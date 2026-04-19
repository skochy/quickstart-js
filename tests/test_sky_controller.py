from unittest.mock import patch
from src.sky_controller import SkyController, COMMAND_MAP


def test_known_commands_not_empty():
    assert len(SkyController.known_commands()) > 0


def test_command_map_contains_basics():
    for cmd in ("play", "pause", "stop", "channel up", "channel down"):
        assert cmd in COMMAND_MAP


@patch("src.sky_controller.press_remote")
def test_send_command_success(mock_press):
    controller = SkyController("192.168.1.1")
    result = controller.send_command("pause")

    assert result is True
    mock_press.assert_called_once()
    args, kwargs = mock_press.call_args
    assert args[0] == "192.168.1.1"


@patch("src.sky_controller.press_remote")
def test_send_unknown_command(mock_press):
    controller = SkyController("192.168.1.1")
    result = controller.send_command("totally_unknown_command")
    assert result is False
    mock_press.assert_not_called()


@patch("src.sky_controller.press_remote")
def test_send_command_exception_returns_false(mock_press):
    mock_press.side_effect = ConnectionError("refused")
    controller = SkyController("192.168.1.1")
    result = controller.send_command("play")
    assert result is False
