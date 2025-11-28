"""Verizon Router API handler."""
import hashlib
import json
import logging
import re
import ssl
from typing import Any

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
                ssl=ssl._create_unverified_context()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('loginToken')
        except Exception as e:
            _LOGGER.error("Error getting login token: %s", e)
        return None

    async def _login(self, token: str) -> bool:
        """Login to router."""
        try:
            username_hash = self._hash_username(self.username)
            password_hash = self._login_encode(self.password, token)
            
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
                "User-Agent": "Mozilla/5.0"
            }
            
            async with self._session.post(
                f"{self.router_url}/login.cgi",
                data=login_data,
                headers=headers,
                ssl=ssl._create_unverified_context(),
                allow_redirects=False
            ) as response:
                if response.status == 302:
                    cookies = self._session.cookie_jar.filter_cookies(self.router_url)
                    for cookie in cookies.values():
                        if cookie.key == 'sysauth' and cookie.value:
                            return True
                    
                    # Try extracting from Set-Cookie header
                    if 'Set-Cookie' in response.headers:
                        set_cookie = response.headers.get('Set-Cookie', '')
                        if 'sysauth=' in set_cookie:
                            match = re.search(r'sysauth=([^;]+)', set_cookie)
                            if match and match.group(1):
                                return True
        except Exception as e:
            _LOGGER.error("Login error: %s", e)
        return False

    async def test_connection(self) -> bool:
        """Test if we can connect to the router."""
        connector = aiohttp.TCPConnector(ssl=ssl._create_unverified_context())
        cookie_jar = aiohttp.CookieJar(unsafe=True)
        
        async with aiohttp.ClientSession(connector=connector, cookie_jar=cookie_jar) as session:
            self._session = session
            token = await self._get_login_token()
            if not token:
                return False
            return await self._login(token)

    async def fetch_router_data(self) -> dict[str, Any]:
        """Fetch all router data."""
        connector = aiohttp.TCPConnector(ssl=ssl._create_unverified_context())
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
                ssl=ssl._create_unverified_context()
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
                    ssl=ssl._create_unverified_context()
                ) as response:
                    if response.status == 200:
                        owl_content = await response.text()
            except:
                pass
            
            return await self._parse_data(basic_content, owl_content)

    async def _parse_data(self, basic_content: str, owl_content: str | None) -> dict[str, Any]:
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
        
        return data
