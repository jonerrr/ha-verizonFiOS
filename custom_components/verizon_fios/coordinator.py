"""DataUpdateCoordinator for Verizon Router."""
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
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

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            return await self.api.fetch_router_data()
        except Exception as err:
            raise UpdateFailed(f"Error communicating with router: {err}") from err
