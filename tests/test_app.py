import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


os.environ.setdefault("SKY_DEVICES", "living_room:192.168.1.100")


@pytest.fixture
def client():
    from src.app import app
    return TestClient(app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_devices(client):
    resp = client.get("/devices")
    assert resp.status_code == 200
    assert "living room" in resp.json()["devices"]


def test_commands_list(client):
    resp = client.get("/commands")
    assert resp.status_code == 200
    assert "pause" in resp.json()["commands"]


def _webhook_payload(handler: str, command: str, device: str | None = None) -> dict:
    params: dict = {
        "SkyCommand": {"resolved": command, "original": command}
    }
    if device:
        params["SkyDevice"] = {"resolved": device, "original": device}
    return {
        "handler": {"name": handler},
        "intent": {"name": handler, "params": params},
    }


@patch("src.sky_controller.SkyRemote")
def test_webhook_pause(MockRemote, client):
    MockRemote.return_value = MagicMock()
    payload = _webhook_payload("SkyControl", "pause")
    resp = client.post("/webhook", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert "Pausing" in body["prompt"]["firstSimple"]["speech"]


@patch("src.sky_controller.SkyRemote")
def test_webhook_channel_up(MockRemote, client):
    MockRemote.return_value = MagicMock()
    payload = _webhook_payload("SkyControl", "channel up")
    resp = client.post("/webhook", json=payload)
    assert resp.status_code == 200


def test_webhook_list_devices(client):
    payload = {"handler": {"name": "ListDevices"}, "intent": {"name": "ListDevices", "params": {}}}
    resp = client.post("/webhook", json=payload)
    assert resp.status_code == 200
    assert "living room" in resp.json()["prompt"]["firstSimple"]["speech"].lower()


def test_webhook_bad_json(client):
    resp = client.post("/webhook", content=b"not json", headers={"content-type": "application/json"})
    assert resp.status_code == 400
