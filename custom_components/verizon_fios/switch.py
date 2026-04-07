"""Switch platform for Verizon FiOS Router."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VerizonRouterCoordinator


def _is_device_blocked(device: dict[str, Any]) -> bool:
    """Infer whether a device is blocked from known-device payload."""
    if "internet_blocked" in device:
        return bool(device["internet_blocked"])

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
    """Switch entity that controls internet access for one device."""

    _attr_has_entity_name = True
    _attr_name = "Internet Access"
    _attr_icon = "mdi:lan-connect"

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
        self._device_name = name
        stable = self._mac.replace(":", "")
        self._attr_unique_id = f"verizon_fios_{entry.entry_id}_internet_{stable}"

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
        """Return True when internet is enabled."""
        device = self._lookup_device()
        if not device:
            return None
        return not _is_device_blocked(device)

    @property
    def device_info(self) -> DeviceInfo:
        """Attach switch to a dedicated per-client device."""
        device = self._lookup_device() or {}
        stable = self._mac.replace(":", "")
        model = device.get("device_model") or device.get("device") or "Network Device"
        manufacturer = device.get("device_manufacturer") or device.get("mac_vendor") or "Unknown"
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._entry.entry_id}_{stable}")},
            connections={(CONNECTION_NETWORK_MAC, self._mac)},
            name=self._device_name,
            manufacturer=manufacturer,
            model=model,
            via_device=(DOMAIN, self._entry.entry_id),
            configuration_url=f"{self._entry.data.get('router_url', 'https://192.168.1.1')}/#/adv/devices/list/settings/{self._mac}",
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable internet access for this device."""
        await self.coordinator.async_set_device_blocked(self._mac, False)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable internet access for this device."""
        await self.coordinator.async_set_device_blocked(self._mac, True)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose useful per-device details from router inventory."""
        device = self._lookup_device() or {}
        attrs: dict[str, Any] = {
            "mac": self._mac,
            "ip": device.get("ip"),
            "hostname": device.get("hostname"),
            "name": device.get("name"),
            "device_type": device.get("device") or device.get("dev_class"),
            "manufacturer": device.get("device_manufacturer") or device.get("mac_vendor"),
            "model": device.get("device_model"),
            "os": device.get("device_os") or device.get("os"),
            "port": device.get("port"),
            "activity": device.get("activity"),
            "time_last_active": device.get("time_last_active"),
            "time_first_seen": device.get("time_first_seen"),
        }
        return {k: v for k, v in attrs.items() if v not in (None, "")}
