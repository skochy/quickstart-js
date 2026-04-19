"""Thin wrapper around pyskyq for sending remote-control commands to Sky Q boxes."""
import logging
from pyskyq import SkyRemote, REMOTECOMMANDS

logger = logging.getLogger(__name__)

# Map of normalised voice command → REMOTECOMMANDS enum value
COMMAND_MAP: dict[str, REMOTECOMMANDS] = {
    # Playback
    "play": REMOTECOMMANDS.play,
    "resume": REMOTECOMMANDS.play,
    "pause": REMOTECOMMANDS.pause,
    "stop": REMOTECOMMANDS.stop,
    "record": REMOTECOMMANDS.record,
    "fast forward": REMOTECOMMANDS.fastforward,
    "skip forward": REMOTECOMMANDS.fastforward,
    "rewind": REMOTECOMMANDS.rewind,
    "skip back": REMOTECOMMANDS.rewind,
    # Channels
    "channel up": REMOTECOMMANDS.channelup,
    "next channel": REMOTECOMMANDS.channelup,
    "channel down": REMOTECOMMANDS.channeldown,
    "previous channel": REMOTECOMMANDS.channeldown,
    # Navigation
    "up": REMOTECOMMANDS.up,
    "down": REMOTECOMMANDS.down,
    "left": REMOTECOMMANDS.left,
    "right": REMOTECOMMANDS.right,
    "select": REMOTECOMMANDS.select,
    "ok": REMOTECOMMANDS.select,
    "back": REMOTECOMMANDS.backup,
    "go back": REMOTECOMMANDS.backup,
    "home": REMOTECOMMANDS.home,
    "sky home": REMOTECOMMANDS.home,
    "guide": REMOTECOMMANDS.tvguide,
    "tv guide": REMOTECOMMANDS.tvguide,
    # Power
    "power": REMOTECOMMANDS.power,
    "standby": REMOTECOMMANDS.power,
    "turn on": REMOTECOMMANDS.power,
    "turn off": REMOTECOMMANDS.power,
    # Colour buttons
    "red": REMOTECOMMANDS.red,
    "green": REMOTECOMMANDS.green,
    "yellow": REMOTECOMMANDS.yellow,
    "blue": REMOTECOMMANDS.blue,
    # Misc
    "interactive": REMOTECOMMANDS.interactive,
    "search": REMOTECOMMANDS.search,
    "sky": REMOTECOMMANDS.sky,
    "box office": REMOTECOMMANDS.boxoffice,
    "help": REMOTECOMMANDS.help,
    "services": REMOTECOMMANDS.services,
    "dismiss": REMOTECOMMANDS.dismiss,
}

# Human-readable labels for voice responses
COMMAND_LABELS: dict[str, str] = {
    "play": "Playing",
    "resume": "Resuming",
    "pause": "Pausing",
    "stop": "Stopping",
    "record": "Starting recording",
    "fast forward": "Fast forwarding",
    "skip forward": "Skipping forward",
    "rewind": "Rewinding",
    "skip back": "Skipping back",
    "channel up": "Channel up",
    "next channel": "Going to the next channel",
    "channel down": "Channel down",
    "previous channel": "Going to the previous channel",
    "guide": "Opening the TV guide",
    "tv guide": "Opening the TV guide",
    "home": "Going home",
    "sky home": "Going home",
    "back": "Going back",
    "go back": "Going back",
    "power": "Toggling power",
    "standby": "Putting on standby",
    "turn on": "Turning on",
    "turn off": "Turning off",
}


class SkyController:
    def __init__(self, ip: str, port: int = 49160) -> None:
        self.ip = ip
        self.port = port

    def send_command(self, command: str) -> bool:
        """Send a voice command to the Sky Q box. Returns True on success."""
        cmd = COMMAND_MAP.get(command.lower())
        if cmd is None:
            logger.warning("Unknown command: %r", command)
            return False
        try:
            remote = SkyRemote(self.ip, self.port)
            remote.press(cmd)
            logger.info("Sent %r to %s", command, self.ip)
            return True
        except Exception:
            logger.exception("Failed to send %r to %s", command, self.ip)
            return False

    @staticmethod
    def known_commands() -> list[str]:
        return sorted(COMMAND_MAP.keys())
