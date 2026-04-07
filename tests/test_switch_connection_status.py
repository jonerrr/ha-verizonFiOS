"""Tests for connection status mapping helper."""

from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "verizon_fios"
    / "device_status.py"
)
SPEC = importlib.util.spec_from_file_location("device_status", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(_MODULE)
infer_connection_status = _MODULE.infer_connection_status


def test_connection_status_offline() -> None:
    device = {"activity": 0, "port": "wds5.1.0"}
    assert infer_connection_status(device, None) == "Offline"


def test_connection_status_from_port_24g() -> None:
    device = {"activity": 1, "port": "wds2.2.1.0"}
    assert infer_connection_status(device, None) == "2.4 GHz"


def test_connection_status_from_port_5g() -> None:
    device = {"activity": 1, "port": "wl1"}
    assert infer_connection_status(device, None) == "5 GHz 1"


def test_connection_status_from_port_5g2() -> None:
    device = {"activity": 1, "port": "wl2"}
    assert infer_connection_status(device, None) == "5 GHz 2"
