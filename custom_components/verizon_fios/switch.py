"""Switch platform for Verizon FiOS Router."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VerizonRouterCoordinator


def _is_device_blocked(device: dict[str, Any]) -> bool:
    """Infer whether a device is blocked from known-device payload."""
    truthy = {"1", "true", "blocked", "deny", "denied", "off"}
    for key in (
        "blocked",
        "block",
        "internet_blocked",
        "internet_block",
        "allow",
        "deny",
        "acl",
        "access",
    ):
        if key not in device:
            continue
        value = device.get(key)
        if isinstance(value, bool):
            if key in {"allow", "access"}:
                return not value
            return value
        normalized = str(value).strip().lower()
        if key in {"allow", "access"}:
            return normalized not in {"1", "true", "allow", "allowed", "on"}
        return normalized in truthy
    return False


def _device_mac(device: dict[str, Any]) -> str | None:
    """Get device MAC from known-device payload."""
    for key in ("mac_addr", "mac", "sta_mac", "device_mac"):
        value = device.get(key)
        if value:
            return str(value).lower()
    return None


def _device_name(device: dict[str, Any], index: int) -> str:
    """Get display name for a known device."""
    for key in ("device_name", "hostname", "name", "friendly_name"):
        value = device.get(key)
        if value and str(value).strip():
            return str(value)
    mac = _device_mac(device)
    return f"Device {index}" if not mac else f"Device {mac}"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Verizon FiOS switch entities."""
    coordinator: VerizonRouterCoordinator = hass.data[DOMAIN][entry.entry_id]
    known_devices = coordinator.data.get("known_devices", {}).get("known_devices", [])
    switches: list[VerizonDeviceBlockSwitch] = []

    for index, device in enumerate(known_devices):
        mac = _device_mac(device)
        if not mac:
            continue
        switches.append(
            VerizonDeviceBlockSwitch(
                coordinator=coordinator,
                entry=entry,
                mac=mac,
                name=_device_name(device, index + 1),
            )
        )

    async_add_entities(switches)


class VerizonDeviceBlockSwitch(CoordinatorEntity, SwitchEntity):
    """Switch entity that blocks/unblocks internet access for one device."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:lan-disconnect"

    def __init__(
        self,
        coordinator: VerizonRouterCoordinator,
        entry: ConfigEntry,
        mac: str,
        name: str,
    ) -> None:
        """Initialize device switch."""
        super().__init__(coordinator)
        self._entry = entry
        self._mac = mac.lower()
        self._attr_name = f"{name} Internet Block"
        stable = self._mac.replace(":", "")
        self._attr_unique_id = f"verizon_fios_{entry.entry_id}_block_{stable}"

    @property
    def available(self) -> bool:
        """Entity availability."""
        return super().available and self._lookup_device() is not None

    def _lookup_device(self) -> dict[str, Any] | None:
        """Find backing known-device row by MAC."""
        known_devices = self.coordinator.data.get("known_devices", {}).get("known_devices", [])
        for device in known_devices:
            if _device_mac(device) == self._mac:
                return device
        return None

    @property
    def is_on(self) -> bool | None:
        """Return True when internet access is blocked."""
        device = self._lookup_device()
        if not device:
            return None
        return _is_device_blocked(device)

    @property
    def device_info(self) -> DeviceInfo:
        """Attach switch to router device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self.coordinator.data.get("router_name", "Verizon Router"),
            manufacturer="Verizon",
            model=self.coordinator.data.get("hardware_model", "CR1000A"),
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Block internet access for this device."""
        await self.coordinator.async_set_device_blocked(self._mac, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Unblock internet access for this device."""
        await self.coordinator.async_set_device_blocked(self._mac, False)
