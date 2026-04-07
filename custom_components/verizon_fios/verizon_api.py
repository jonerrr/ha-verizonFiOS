"""Verizon Router API handler."""
import asyncio
import hashlib
import json
import logging
import re
import ssl
from typing import Any
from urllib.parse import urlencode

import aiohttp

_LOGGER = logging.getLogger(__name__)


class VerizonRouterAPI:
    """Handle Verizon Router API communication."""

    def __init__(self, router_url: str, username: str, password: str):
        """Initialize the API handler."""
        self.router_url = router_url
        self.username = username
        self.password = password
        self._session = None
        self._ssl_context = ssl._create_unverified_context()
        self._last_successful_data: dict[str, Any] | None = None

    def _arc_md5(self, text: str) -> str:
        """Verizon's custom ArcMD5 hash: MD5 -> SHA512."""
        md5_hash = hashlib.md5(text.encode()).hexdigest()
        sha512_hash = hashlib.sha512(md5_hash.encode('ascii')).hexdigest()
        return sha512_hash

    def _login_encode(self, password: str, token: str) -> str:
        """Encode password with token: SHA512(token + ArcMD5(password))."""
        arc_md5_result = self._arc_md5(password)
        combined = token + arc_md5_result
        final_hash = hashlib.sha512(combined.encode('ascii')).hexdigest()
        return final_hash

    def _hash_username(self, username: str) -> str:
        """Hash username using ArcMD5."""
        return self._arc_md5(username)

    async def _get_login_status(self) -> dict[str, Any] | None:
        """Get parsed loginStatus payload from router."""
        try:
            async with self._session.get(
                f"{self.router_url}/loginStatus.cgi",
                ssl=self._ssl_context,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    return None
                text = await response.text()
                return json.loads(text)
        except Exception:
            return None

    def _parse_js_value(self, js_content: str, variable_name: str) -> Any:
        """Parse JavaScript variable values from router response."""
        # Pattern for addROD calls
        rod_pattern = rf'addROD\("{variable_name}",\s*(.+?)\s*\);'
        match = re.search(rod_pattern, js_content, re.DOTALL)
        
        if not match:
            return None
        
        try:
            value_str = match.group(1).strip()
            
            # For complex objects/arrays, find matching closing bracket
            if value_str.startswith('{') or value_str.startswith('['):
                bracket_count = 0
                brace_count = 0
                end_pos = 0
                in_string = False
                escape_next = False
                
                for i, char in enumerate(value_str):
                    if escape_next:
                        escape_next = False
                        continue
                    if char == '\\':
                        escape_next = True
                        continue
                    if char in ['"', "'"]:
                        in_string = not in_string
                        continue
                    if in_string:
                        continue
                    
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                    elif char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
                    
                    if brace_count == 0 and bracket_count == 0:
                        end_pos = i + 1
                        break
                
                if end_pos > 0:
                    value_str = value_str[:end_pos]
            
            # Replace single quotes with double quotes
            value_str = re.sub(r"'([^']*)'", r'"\1"', value_str)
            
            # Remove trailing commas (JavaScript allows, JSON doesn't)
            value_str = re.sub(r',(\s*[}\]])', r'\1', value_str)
            
            return json.loads(value_str)
        except Exception as e:
            _LOGGER.debug("Error parsing %s: %s", variable_name, e)
            return None

    def _parse_cfg_table(self, js_content: str, key_prefix: str) -> dict[int, str]:
        """Parse addCfg table values for keys like key_prefix_<index>."""
        pattern = re.compile(
            rf'addCfg\("{re.escape(key_prefix)}_(\d+)",\s*"[^"]*",\s*"([^"]*)"\);'
        )
        result: dict[int, str] = {}
        for match in pattern.finditer(js_content):
            result[int(match.group(1))] = match.group(2).strip().lower()
        return result

    async def _get_login_token(self) -> str | None:
        """Get login token from router."""
        try:
            data = await self._get_login_status()
            if data is None:
                return None
            token = data.get("loginToken")
            if token:
                _LOGGER.debug("Successfully retrieved login token")
            else:
                _LOGGER.error("No loginToken in response: %s", data)
            return token
        except Exception as e:
            _LOGGER.error("Error getting login token: %s", e)
        return None

    async def _login(self, token: str) -> bool:
        """Login to router."""
        try:
            username_hash = self._hash_username(self.username)
            password_hash = self._login_encode(self.password, token)
            
            _LOGGER.debug("Login attempt with username: %s", self.username)
            _LOGGER.debug("Username hash: %s...", username_hash[:20])
            _LOGGER.debug("Password hash: %s...", password_hash[:20])
            
            login_data = {
                "luci_username": username_hash,
                "luci_password": password_hash,
                "luci_view": "Desktop",
                "luci_token": token,
                "luci_keep_login": "0"
            }
            
            headers = {
                "Origin": self.router_url,
                "Referer": f"{self.router_url}/",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            async with self._session.post(
                f"{self.router_url}/login.cgi",
                data=login_data,
                headers=headers,
                ssl=self._ssl_context,
                allow_redirects=False,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                _LOGGER.debug("Login response status: %s", response.status)
                _LOGGER.debug("Login response headers: %s", dict(response.headers))
                
                if response.status not in (200, 302):
                    if response.status == 403:
                        _LOGGER.debug(
                            "Login rejected with 403 (possible transient auth/session lockout)"
                        )
                    else:
                        _LOGGER.error(
                            "Login failed - unexpected status: %s", response.status
                        )
                    text = await response.text()
                    _LOGGER.debug("Response body: %s", text[:200])
                    return False

                # Try Set-Cookie header first (matches PyScript approach)
                if "Set-Cookie" in response.headers:
                    set_cookie = response.headers.get("Set-Cookie", "")
                    _LOGGER.debug("Set-Cookie header: %s...", set_cookie[:100])
                    if "sysauth=" in set_cookie:
                        match = re.search(r"sysauth=([^;]+)", set_cookie)
                        if match and match.group(1):
                            _LOGGER.info("Login successful - found sysauth in Set-Cookie header")
                            return True

                # Fallback: check cookie jar
                cookies = self._session.cookie_jar.filter_cookies(self.router_url)
                _LOGGER.debug("Cookies in jar: %s", len(cookies))
                for cookie in cookies.values():
                    _LOGGER.debug(
                        "Cookie: %s = %s",
                        cookie.key,
                        cookie.value[:20] if cookie.value else "empty",
                    )
                    if cookie.key == "sysauth" and cookie.value:
                        _LOGGER.info("Login successful - got sysauth from cookie jar")
                        return True

                # Some firmware returns 200 with no new cookie but session is still authenticated.
                status = await self._get_login_status()
                if status and str(status.get("islogin")) == "1":
                    _LOGGER.info("Login successful - router reports authenticated session")
                    return True

                _LOGGER.error("Login failed - no authenticated session established")
                    
        except Exception as e:
            _LOGGER.error("Login error: %s", e, exc_info=True)
        return False

    async def _authenticate_session(self) -> tuple[str, str]:
        """Authenticate and return (login_token, form_token)."""
        token = await self._get_login_token()
        if not token:
            raise Exception("Could not get login token")

        if not await self._login(token):
            raise Exception("Login failed")

        form_token = await self._get_form_token(self._session, token)
        return token, form_token

    async def test_connection(self) -> bool:
        """Test if we can connect to the router."""
        _LOGGER.debug("Starting connection test to %s", self.router_url)
        
        connector = aiohttp.TCPConnector(ssl=self._ssl_context)
        cookie_jar = aiohttp.CookieJar(unsafe=True)
        timeout = aiohttp.ClientTimeout(total=30)
        
        try:
            async with aiohttp.ClientSession(
                connector=connector, 
                cookie_jar=cookie_jar,
                timeout=timeout
            ) as session:
                self._session = session
                
                _LOGGER.debug("Getting login token...")
                token = await self._get_login_token()
                if not token:
                    _LOGGER.error("Failed to get login token from router")
                    return False
                
                _LOGGER.debug("Got token: %s..., attempting login...", token[:10])
                login_result = await self._login(token)
                
                if login_result:
                    _LOGGER.info("Login successful")
                else:
                    _LOGGER.error("Login failed - check username and password")
                
                return login_result
        except aiohttp.ClientError as e:
            _LOGGER.error("Connection error: %s", e)
            return False
        except asyncio.TimeoutError:
            _LOGGER.error("Connection timeout - router not responding")
            return False
        except Exception as e:
            _LOGGER.error("Connection test failed with exception: %s", e, exc_info=True)
            return False

    async def fetch_router_data(self) -> dict[str, Any]:
        """Fetch all router data."""
        connector = aiohttp.TCPConnector(ssl=self._ssl_context)
        cookie_jar = aiohttp.CookieJar(unsafe=True)
        
        async with aiohttp.ClientSession(connector=connector, cookie_jar=cookie_jar) as session:
            self._session = session
            
            # Login (retry to reduce transient 403 failures)
            auth_error: Exception | None = None
            for attempt in range(6):
                try:
                    await self._authenticate_session()
                    auth_error = None
                    break
                except Exception as err:
                    auth_error = err
                    if attempt < 5:
                        await asyncio.sleep(min(5.0, 0.6 * (2**attempt)))
            if auth_error:
                if self._last_successful_data is not None:
                    _LOGGER.warning(
                        "Auth failed during refresh (%s); using last successful router data",
                        auth_error,
                    )
                    return self._last_successful_data
                raise auth_error
            
            # Fetch data files
            headers = {"Referer": f"{self.router_url}/"}
            
            # Get cgi_basic.js
            async with session.get(
                f"{self.router_url}/cgi/cgi_basic.js",
                headers=headers,
                ssl=self._ssl_context
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch cgi_basic.js: {response.status}")
                basic_content = await response.text()
            
            # Get cgi_owl.js
            owl_content = None
            try:
                async with session.get(
                    f"{self.router_url}/cgi/cgi_owl.js",
                    headers=headers,
                    ssl=self._ssl_context
                ) as response:
                    if response.status == 200:
                        owl_content = await response.text()
            except:
                pass
            known_devices_content = None
            try:
                async with session.get(
                    f"{self.router_url}/cgi/cgi_known_devices.js",
                    headers=headers,
                    ssl=self._ssl_context
                ) as response:
                    if response.status == 200:
                        known_devices_content = await response.text()
            except:
                pass

            parsed = await self._parse_data(
                basic_content, owl_content, known_devices_content
            )
            self._last_successful_data = parsed
            return parsed

    async def _parse_data(
        self,
        basic_content: str,
        owl_content: str | None,
        known_devices_content: str | None = None,
    ) -> dict[str, Any]:
        """Parse router data into structured format."""
        data = {}
        
        # Parse topology
        topology = self._parse_js_value(basic_content, "dump_toplogy_map_info")
        if topology and 'nodes' in topology:
            data['topology'] = topology
        
        # Parse known devices
        known_devices = self._parse_js_value(basic_content, "known_device_list")
        if not known_devices and owl_content:
            known_devices = self._parse_js_value(owl_content, "known_device_list")
        if not known_devices and known_devices_content:
            known_devices = self._parse_js_value(
                known_devices_content, "known_device_list"
            )

        blocked_macs: set[str] = set()
        if known_devices_content:
            block_mac = self._parse_cfg_table(known_devices_content, "block_mac")
            block_enable = self._parse_cfg_table(known_devices_content, "block_enable")
            for idx, mac in block_mac.items():
                if mac and block_enable.get(idx, "0") == "1":
                    blocked_macs.add(mac.lower())

        if known_devices:
            if blocked_macs and isinstance(known_devices, dict):
                devices = known_devices.get("known_devices", [])
                if isinstance(devices, list):
                    for device in devices:
                        mac = str(device.get("mac", "")).lower()
                        device["internet_blocked"] = mac in blocked_macs
            data['known_devices'] = known_devices
        if blocked_macs:
            data["blocked_macs"] = blocked_macs
        
        # Parse station info
        station_info = self._parse_js_value(basic_content, "dump_toplogy_station_info")
        if not station_info and owl_content:
            station_info = self._parse_js_value(owl_content, "dump_toplogy_station_info")
        if station_info:
            data['station_info'] = station_info
        
        # Parse router name
        router_name = self._parse_js_value(basic_content, "router_name")
        if router_name:
            data['router_name'] = router_name
        
        # Parse hardware model
        hardware_model = self._parse_js_value(basic_content, "hardware_model")
        if hardware_model:
            data['hardware_model'] = hardware_model

        form_token = self._parse_js_value(basic_content, "session:token")
        if not form_token and owl_content:
            form_token = self._parse_js_value(owl_content, "session:token")
        if form_token:
            data["form_token"] = form_token
        
        return data

    async def _create_authenticated_session(self) -> tuple[aiohttp.ClientSession, str]:
        """Create session and return authenticated session + token."""
        connector = aiohttp.TCPConnector(ssl=self._ssl_context)
        cookie_jar = aiohttp.CookieJar(unsafe=True)
        session = aiohttp.ClientSession(connector=connector, cookie_jar=cookie_jar)
        self._session = session

        token = await self._get_login_token()
        if not token:
            await session.close()
            raise Exception("Could not get login token")
        if not await self._login(token):
            await session.close()
            raise Exception("Login failed")

        return session, token

    async def _get_form_token(
        self, session: aiohttp.ClientSession, fallback_token: str
    ) -> str:
        """Get apply token from loginStatus.cgi after login."""
        try:
            self._session = session
            status = await self._get_login_status()
            if not status:
                return fallback_token
            token = status.get("token")
            return token if token else fallback_token
        except Exception:
            return fallback_token

    async def _post_form(
        self,
        session: aiohttp.ClientSession,
        path: str,
        data: dict[str, Any],
    ) -> tuple[int, str]:
        """POST x-www-form-urlencoded data and return status/body."""
        headers = {
            "Origin": self.router_url,
            "Referer": f"{self.router_url}/#/adv/devices/list",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0",
        }
        async with session.post(
            f"{self.router_url}{path}",
            data=urlencode(data),
            headers=headers,
            ssl=self._ssl_context,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as response:
            return response.status, await response.text()

    async def reboot_router(self) -> None:
        """Trigger router reboot."""
        session, login_token = await self._create_authenticated_session()
        try:
            token = await self._get_form_token(session, login_token)
            status, _ = await self._post_form(
                session,
                "/apply_abstract.cgi",
                {"token": token, "action": "ui_reboot_reason", "action_params": "1"},
            )
            if status != 200:
                raise Exception("Router rejected reboot reason pre-check")

            status, _ = await self._post_form(
                session,
                "/apply_abstract.cgi",
                {"token": token, "action": "reboot"},
            )
            if status != 200:
                raise Exception("Router rejected reboot request")
        finally:
            await session.close()

    async def set_device_blocked(self, mac: str, blocked: bool) -> None:
        """Block or unblock a device by MAC."""
        session, login_token = await self._create_authenticated_session()
        try:
            normalized_mac = mac.lower()
            token = await self._get_form_token(session, login_token)

            headers = {"Referer": f"{self.router_url}/#/adv/devices/list"}
            async with session.get(
                f"{self.router_url}/cgi/cgi_known_devices.js",
                headers=headers,
                ssl=self._ssl_context,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    raise Exception("Failed to fetch known-device config")
                cfg_content = await response.text()

            block_mac = self._parse_cfg_table(cfg_content, "block_mac")
            block_enable = self._parse_cfg_table(cfg_content, "block_enable")

            existing_index: int | None = None
            free_index: int | None = None
            max_index = max(
                max(block_mac.keys(), default=-1),
                max(block_enable.keys(), default=-1),
            )
            for idx in range(max_index + 1):
                slot_mac = block_mac.get(idx, "")
                slot_enabled = block_enable.get(idx, "0")
                if slot_mac == normalized_mac:
                    existing_index = idx
                    if slot_enabled == "1" and blocked:
                        return
                    break
                if free_index is None and (slot_mac == "" or slot_enabled == "0"):
                    free_index = idx

            if blocked:
                index = existing_index if existing_index is not None else free_index
                if index is None:
                    raise Exception("No free block list slot available")
                cmd = "ui_block_dev"
                cmdparam = f"{normalized_mac},{index}"
            else:
                if existing_index is None:
                    return
                cmd = "ui_remove_block_dev"
                cmdparam = str(existing_index)

            await self._post_form(
                session,
                "/analysis.cgi",
                {
                    "token": token,
                    "content": f"HA device access toggle {normalized_mac} blocked={blocked}",
                },
            )

            status, _ = await self._post_form(
                session,
                "/apply_abstract.cgi",
                {"token": token, "action": cmd, "action_params": cmdparam},
            )
            if status != 200:
                raise Exception(f"Router rejected device access update for {normalized_mac}")
        finally:
            await session.close()
