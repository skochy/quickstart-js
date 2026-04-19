"""Intent handlers: parse Google Actions webhook payloads and route to Sky Q."""
import logging
from .device_registry import DeviceRegistry
from .sky_controller import SkyController, COMMAND_LABELS

logger = logging.getLogger(__name__)


def _extract_param(params: dict, key: str) -> str | None:
    entry = params.get(key)
    if not entry:
        return None
    return entry.get("resolved") or entry.get("original")


def handle_sky_control(payload: dict, registry: DeviceRegistry) -> dict:
    """Handle the SkyControl intent. Returns a Google Actions webhook response."""
    params = payload.get("intent", {}).get("params", {})
    command = _extract_param(params, "SkyCommand")
    device_name = _extract_param(params, "SkyDevice")

    if not command:
        return _response("Sorry, I didn't catch the command. Try saying pause, play, or channel up.")

    canonical, ip = registry.resolve(device_name)
    if ip is None:
        if device_name:
            return _response(
                f"I couldn't find a Sky box called {device_name!r}. "
                f"Known boxes: {', '.join(registry.devices) or 'none configured'}."
            )
        return _response(
            "You have multiple Sky boxes. Please say which one, for example: "
            "pause in the living room."
        )

    controller = SkyController(ip)
    success = controller.send_command(command)

    label = COMMAND_LABELS.get(command.lower(), command.capitalize())
    device_label = canonical.replace("_", " ").title() if canonical else "your Sky box"

    if success:
        speech = f"{label} on {device_label}."
    else:
        speech = f"Sorry, I couldn't send that command to {device_label}."

    return _response(speech)


def handle_list_devices(registry: DeviceRegistry) -> dict:
    devices = registry.devices
    if not devices:
        return _response("No Sky boxes are configured.")
    names = ", ".join(k.replace("_", " ").title() for k in devices)
    return _response(f"I know about {len(devices)} Sky box{'es' if len(devices) != 1 else ''}: {names}.")


def handle_help() -> dict:
    return _response(
        "You can say things like: pause, play, stop, channel up, channel down, "
        "rewind, fast forward, guide, home, record, or turn off. "
        "Add 'in the living room' to target a specific box."
    )


def _response(speech: str, end_conversation: bool = True) -> dict:
    resp: dict = {
        "prompt": {
            "override": False,
            "firstSimple": {
                "speech": speech,
                "text": speech,
            },
        }
    }
    if end_conversation:
        resp["scene"] = {
            "next": {"name": "actions.scene.END_CONVERSATION"}
        }
    return resp
