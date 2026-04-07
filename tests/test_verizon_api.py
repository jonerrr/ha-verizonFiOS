"""Tests for VerizonRouterAPI write/control logic."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import MethodType

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "verizon_fios"
    / "verizon_api.py"
)
SPEC = importlib.util.spec_from_file_location("verizon_api", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(_MODULE)
VerizonRouterAPI = _MODULE.VerizonRouterAPI


class _FakeResponse:
    def __init__(self, status: int, body: str) -> None:
        self.status = status
        self._body = body

    async def __aenter__(self) -> "_FakeResponse":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def text(self) -> str:
        return self._body


class _FakeSession:
    def __init__(self, cfg_body: str) -> None:
        self._cfg_body = cfg_body
        self.closed = False

    def get(self, *_args, **_kwargs) -> _FakeResponse:
        return _FakeResponse(200, self._cfg_body)

    async def close(self) -> None:
        self.closed = True


def _cfg_with_slots(mac_by_index: dict[int, str], enabled_by_index: dict[int, str]) -> str:
    lines: list[str] = []
    max_index = max(max(mac_by_index.keys(), default=0), max(enabled_by_index.keys(), default=0))
    for idx in range(max_index + 1):
        mac = mac_by_index.get(idx, "")
        enabled = enabled_by_index.get(idx, "0")
        lines.append(f'addCfg("block_mac_{idx}", "enc", "{mac}");')
        lines.append(f'addCfg("block_enable_{idx}", "enc", "{enabled}");')
    return "\n".join(lines)


def test_parse_cfg_table() -> None:
    api = VerizonRouterAPI("https://router", "u", "p")
    content = (
        'addCfg("block_mac_0", "enc", "");\n'
        'addCfg("block_mac_1", "enc", "aa:bb:cc:dd:ee:ff");\n'
        'addCfg("block_enable_0", "enc", "0");\n'
    )
    parsed = api._parse_cfg_table(content, "block_mac")
    assert parsed[0] == ""
    assert parsed[1] == "aa:bb:cc:dd:ee:ff"


@pytest.mark.asyncio
async def test_set_device_blocked_uses_ui_block_dev() -> None:
    api = VerizonRouterAPI("https://router", "u", "p")
    target = "ea:a0:e9:f9:e8:45"
    cfg = _cfg_with_slots(mac_by_index={0: "", 1: "74:a6:cd:8a:ed:69"}, enabled_by_index={0: "0", 1: "1"})
    session = _FakeSession(cfg)

    async def fake_create_authenticated_session(self):
        return session, "fallback-login-token"

    async def fake_get_form_token(self, _session, _fallback):
        return "form-token"

    posted: list[tuple[str, dict[str, str]]] = []

    async def fake_post_form(self, _session, path, data):
        posted.append((path, data))
        return 200, "OK"

    api._create_authenticated_session = MethodType(fake_create_authenticated_session, api)
    api._get_form_token = MethodType(fake_get_form_token, api)
    api._post_form = MethodType(fake_post_form, api)

    await api.set_device_blocked(target, True)

    assert posted[0][0] == "/analysis.cgi"
    assert posted[1][0] == "/apply_abstract.cgi"
    assert posted[1][1]["action"] == "ui_block_dev"
    assert posted[1][1]["action_params"] == f"{target},0"


@pytest.mark.asyncio
async def test_set_device_blocked_uses_ui_remove_block_dev() -> None:
    api = VerizonRouterAPI("https://router", "u", "p")
    target = "ea:a0:e9:f9:e8:45"
    cfg = _cfg_with_slots(mac_by_index={10: target}, enabled_by_index={10: "1"})
    session = _FakeSession(cfg)

    async def fake_create_authenticated_session(self):
        return session, "fallback-login-token"

    async def fake_get_form_token(self, _session, _fallback):
        return "form-token"

    posted: list[tuple[str, dict[str, str]]] = []

    async def fake_post_form(self, _session, path, data):
        posted.append((path, data))
        return 200, "OK"

    api._create_authenticated_session = MethodType(fake_create_authenticated_session, api)
    api._get_form_token = MethodType(fake_get_form_token, api)
    api._post_form = MethodType(fake_post_form, api)

    await api.set_device_blocked(target, False)

    assert posted[1][1]["action"] == "ui_remove_block_dev"
    assert posted[1][1]["action_params"] == "10"
