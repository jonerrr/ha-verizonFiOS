"""Helpers for per-device status mapping."""

from __future__ import annotations

from typing import Any


def _as_active(value: Any) -> bool:
    """Return True when router activity value indicates online."""
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "online", "active", "yes"}:
        return True
    if text in {"0", "false", "offline", "inactive", "no", ""}:
        return False
    # Unknown values are treated as active so we don't hide status accidentally.
    return True


def infer_connection_status(
    device: dict[str, Any], station_info: dict[str, Any] | None
) -> str:
    """Map router connection details into a friendly status string."""
    if not _as_active(device.get("activity", 0)):
        return "Offline"

    for key in ("wlconn_type", "connection_type", "connect_type"):
        value = str(device.get(key, "")).strip()
        if value:
            return value

    port = str(device.get("port", "")).lower()
    if "eth" in port:
        return "Ethernet"

    # Match router UI connection labels from devices list.
    if "wds2" in port or "wl0" in port or "2g" in port or "24g" in port:
        return "2.4 GHz"
    if "wl1" in port:
        return "5 GHz 1"
    if "wl2" in port:
        return "5 GHz 2"
    if "wds5" in port or "5g" in port:
        return "5 GHz"
    if "wds6" in port or "6g" in port:
        return "6 GHz"

    # Fallback for firmwares that provide station MAC.
    mac = str(device.get("mac_addr") or device.get("mac") or "").lower()
    stations = station_info.get("stations", []) if station_info else []
    if mac:
        for station in stations:
            station_mac = str(station.get("mac") or station.get("sta_mac") or "").lower()
            if station_mac != mac:
                continue
            connect_type = str(station.get("connect_type", "")).strip()
            if connect_type == "2.4G":
                return "2.4 GHz"
            if connect_type.startswith("5G"):
                # Router UI distinguishes 5 GHz 1/2 by interface.
                intf = str(station.get("connect_intf", "")).lower()
                if "wl1" in intf:
                    return "5 GHz 1"
                if "wl2" in intf:
                    return "5 GHz 2"
                return "5 GHz"
            if connect_type.startswith("6G"):
                return "6 GHz"
            if connect_type == "Ether":
                return "Ethernet"

    if port:
        return f"connected ({port})"
    return "Connected"
