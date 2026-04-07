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

    async def _get_login_token(self) -> str | None:
        """Get login token from router."""
        try:
            async with self._session.get(
                f"{self.router_url}/loginStatus.cgi",
                ssl=self._ssl_context,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                _LOGGER.debug("Token request status: %s", response.status)
                if response.status == 200:
                    # Router returns text/javascript instead of application/json
                    # So we need to get text and parse it manually
                    text = await response.text()
                    _LOGGER.debug("Token response text: %s", text[:200])
                    
                    try:
                        data = json.loads(text)
                    except json.JSONDecodeError as e:
                        _LOGGER.error("Failed to parse token response as JSON: %s", e)
                        _LOGGER.debug("Response text was: %s", text)
                        return None
                    
                    token = data.get('loginToken')
                    if token:
                        _LOGGER.debug("Successfully retrieved login token")
                    else:
                        _LOGGER.error("No loginToken in response: %s", data)
                    return token
                else:
                    _LOGGER.error("Bad status getting token: %s", response.status)
                    text = await response.text()
                    _LOGGER.debug("Response body: %s", text[:200])
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
                
                if response.status == 302:
                    _LOGGER.debug("Got 302 redirect (expected)")
                    
                    # Try Set-Cookie header first (matches PyScript approach)
                    sysauth_cookie = None
                    if 'Set-Cookie' in response.headers:
                        set_cookie = response.headers.get('Set-Cookie', '')
                        _LOGGER.debug("Set-Cookie header: %s...", set_cookie[:100])
                        if 'sysauth=' in set_cookie:
                            match = re.search(r'sysauth=([^;]+)', set_cookie)
                            if match and match.group(1):
                                sysauth_cookie = match.group(1)
                                _LOGGER.info("Login successful - found sysauth in Set-Cookie header")
                                return True
                    
                    # Fallback: check cookie jar
                    if not sysauth_cookie:
                        cookies = self._session.cookie_jar.filter_cookies(self.router_url)
                        _LOGGER.debug("Cookies in jar: %s", len(cookies))
                        
                        for cookie in cookies.values():
                            _LOGGER.debug("Cookie: %s = %s", cookie.key, cookie.value[:20] if cookie.value else "empty")
                            if cookie.key == 'sysauth' and cookie.value:
                                _LOGGER.info("Login successful - got sysauth from cookie jar")
                                return True
                    
                    _LOGGER.error("Login failed - no sysauth cookie found")
                else:
                    _LOGGER.error("Login failed - unexpected status: %s", response.status)
                    text = await response.text()
                    _LOGGER.debug("Response body: %s", text[:200])
                    
        except Exception as e:
            _LOGGER.error("Login error: %s", e, exc_info=True)
        return False

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
            
            # Login
            token = await self._get_login_token()
            if not token:
                raise Exception("Could not get login token")
            
            if not await self._login(token):
                raise Exception("Login failed")
            
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

            return await self._parse_data(
                basic_content, owl_content, known_devices_content
            )

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
        if known_devices:
            data['known_devices'] = known_devices
        
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
        session, token = await self._create_authenticated_session()
        try:
            # The UI uses a generic apply endpoint; command names vary by model/firmware.
            candidates = (
                "ui_system_reboot",
                "ui_reboot",
                "reboot",
            )
            for action in candidates:
                status, _ = await self._post_form(
                    session,
                    "/apply_abstract.cgi",
                    {"token": token, "action": action},
                )
                if status == 200:
                    return
            raise Exception("Router rejected reboot request")
        finally:
            await session.close()

    async def set_device_blocked(self, mac: str, blocked: bool) -> None:
        """Block or unblock a device by MAC."""
        session, token = await self._create_authenticated_session()
        try:
            # Router UI performs POST analysis.cgi followed by apply_abstract.cgi.
            await self._post_form(
                session,
                "/analysis.cgi",
                {"token": token, "content": f"HA device access toggle {mac} blocked={blocked}"},
            )

            action_payloads = [
                {
                    "token": token,
                    "action": "ui_parental_single",
                    "action_params": json.dumps({"mac": mac, "block": int(blocked)}),
                },
                {
                    "token": token,
                    "action": "parental_control",
                    "action_params": json.dumps({"mac": mac, "block": int(blocked)}),
                },
                {
                    "token": token,
                    "action": "device_access",
                    "action_params": json.dumps({"mac": mac, "allow": int(not blocked)}),
                },
            ]

            for payload in action_payloads:
                status, _ = await self._post_form(
                    session, "/apply_abstract.cgi", payload
                )
                if status == 200:
                    return

            raise Exception(f"Router rejected device access update for {mac}")
        finally:
            await session.close()
