"""Builds a map of device name → IP address from the SKY_DEVICES env var.

SKY_DEVICES format:  "living_room:192.168.1.100,bedroom:192.168.1.101"
"""
import os
import re
import logging

logger = logging.getLogger(__name__)


def _normalise(name: str) -> str:
    """Lowercase, replace underscores/hyphens with spaces."""
    return re.sub(r"[_\-]+", " ", name.strip().lower())


class DeviceRegistry:
    def __init__(self) -> None:
        self._devices: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        raw = os.environ.get("SKY_DEVICES", "").strip()
        if not raw:
            logger.warning("SKY_DEVICES is not set — no Sky Q boxes registered")
            return
        for entry in raw.split(","):
            entry = entry.strip()
            if ":" not in entry:
                logger.warning("Skipping invalid SKY_DEVICES entry: %r", entry)
                continue
            name, _, ip = entry.partition(":")
            name = _normalise(name)
            ip = ip.strip()
            self._devices[name] = ip
            logger.info("Registered Sky Q box %r → %s", name, ip)

    @property
    def devices(self) -> dict[str, str]:
        return dict(self._devices)

    def resolve(self, name: str | None) -> tuple[str | None, str | None]:
        """Return (canonical_name, ip) for a device name, or (None, None)."""
        if not self._devices:
            return None, None

        if name is None:
            if len(self._devices) == 1:
                canonical, ip = next(iter(self._devices.items()))
                return canonical, ip
            return None, None

        key = _normalise(name)
        # Exact match
        if key in self._devices:
            return key, self._devices[key]
        # Partial / substring match
        for canonical, ip in self._devices.items():
            if key in canonical or canonical in key:
                return canonical, ip
        return None, None

    def default(self) -> tuple[str | None, str | None]:
        if len(self._devices) == 1:
            canonical, ip = next(iter(self._devices.items()))
            return canonical, ip
        return None, None
