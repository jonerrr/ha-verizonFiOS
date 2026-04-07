"""Button platform for Verizon FiOS Router."""

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VerizonRouterCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Verizon FiOS router buttons."""
    coordinator: VerizonRouterCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VerizonRouterRebootButton(coordinator, entry)])


class VerizonRouterRebootButton(CoordinatorEntity, ButtonEntity):
    """Representation of a router reboot button."""

    _attr_has_entity_name = True
    _attr_name = "Reboot Router"
    _attr_device_class = ButtonDeviceClass.RESTART
    _attr_icon = "mdi:restart"

    def __init__(self, coordinator: VerizonRouterCoordinator, entry: ConfigEntry) -> None:
        """Initialize the reboot button."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"verizon_fios_{entry.entry_id}_router_reboot"

    @property
    def device_info(self) -> DeviceInfo:
        """Return router device info."""
        topology = self.coordinator.data.get("topology", {})
        nodes = topology.get("nodes") if topology else None
        sw_version = nodes[0].get("sw_ver") if nodes else None
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self.coordinator.data.get("router_name", "Verizon Router"),
            manufacturer="Verizon",
            model=self.coordinator.data.get("hardware_model", "CR1000A"),
            sw_version=sw_version,
        )

    async def async_press(self) -> None:
        """Handle reboot button press."""
        await self.coordinator.async_reboot_router()
