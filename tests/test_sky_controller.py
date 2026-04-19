import pytest
from unittest.mock import MagicMock, patch
from src.sky_controller import SkyController, COMMAND_MAP


def test_known_commands_not_empty():
    assert len(SkyController.known_commands()) > 0


def test_command_map_contains_basics():
    for cmd in ("play", "pause", "stop", "channel up", "channel down"):
        assert cmd in COMMAND_MAP


@patch("src.sky_controller.SkyRemote")
def test_send_command_success(MockRemote):
    mock_instance = MagicMock()
    MockRemote.return_value = mock_instance

    controller = SkyController("192.168.1.1")
    result = controller.send_command("pause")

    assert result is True
    MockRemote.assert_called_once_with("192.168.1.1", 49160)
    mock_instance.press.assert_called_once()


@patch("src.sky_controller.SkyRemote")
def test_send_unknown_command(MockRemote):
    controller = SkyController("192.168.1.1")
    result = controller.send_command("totally_unknown_command")
    assert result is False
    MockRemote.assert_not_called()


@patch("src.sky_controller.SkyRemote")
def test_send_command_exception_returns_false(MockRemote):
    MockRemote.return_value.press.side_effect = ConnectionError("refused")
    controller = SkyController("192.168.1.1")
    result = controller.send_command("play")
    assert result is False
