import os
import pytest
from src.device_registry import DeviceRegistry


def make_registry(sky_devices: str) -> DeviceRegistry:
    os.environ["SKY_DEVICES"] = sky_devices
    return DeviceRegistry()


def test_single_device_auto_selected():
    registry = make_registry("living_room:192.168.1.100")
    name, ip = registry.resolve(None)
    assert name == "living room"
    assert ip == "192.168.1.100"


def test_multi_device_no_name_returns_none():
    registry = make_registry("living_room:192.168.1.100,bedroom:192.168.1.101")
    name, ip = registry.resolve(None)
    assert name is None
    assert ip is None


def test_exact_match():
    registry = make_registry("living_room:192.168.1.100,bedroom:192.168.1.101")
    name, ip = registry.resolve("bedroom")
    assert name == "bedroom"
    assert ip == "192.168.1.101"


def test_partial_match():
    registry = make_registry("living_room:192.168.1.100")
    name, ip = registry.resolve("living")
    assert ip == "192.168.1.100"


def test_no_match_returns_none():
    registry = make_registry("living_room:192.168.1.100")
    name, ip = registry.resolve("kitchen")
    assert name is None
    assert ip is None


def test_underscore_normalised():
    registry = make_registry("living_room:10.0.0.1")
    assert "living room" in registry.devices


def test_empty_env_var():
    os.environ["SKY_DEVICES"] = ""
    registry = DeviceRegistry()
    assert registry.devices == {}
