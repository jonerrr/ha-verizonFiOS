"""DataUpdateCoordinator for Verizon Router."""
from datetime import timedelta
import logging
from typing import Any
import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_ROUTER_URL, DOMAIN, UPDATE_INTERVAL
from .verizon_api import VerizonRouterAPI

_LOGGER = logging.getLogger(__name__)


class VerizonRouterCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Verizon Router data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.api = VerizonRouterAPI(
            entry.data[CONF_ROUTER_URL],
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
        )
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self._write_lock = asyncio.Lock()

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            return await self.api.fetch_router_data()
        except Exception as err:
            raise UpdateFailed(f"Error communicating with router: {err}") from err

    async def async_reboot_router(self) -> None:
        """Reboot the router and refresh data."""
        async with self._write_lock:
            try:
                await self.api.reboot_router()
                await self.async_request_refresh()
            except Exception as err:
                raise HomeAssistantError(f"Router reboot failed: {err}") from err

    async def async_set_device_blocked(self, mac: str, blocked: bool) -> None:
        """Set device blocked/unblocked and refresh data."""
        async with self._write_lock:
            try:
                await self.api.set_device_blocked(mac, blocked)
                await self.async_request_refresh()
            except Exception as err:
                raise HomeAssistantError(
                    f"Failed to update device access for {mac}: {err}"
                ) from err
