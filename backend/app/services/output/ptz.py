"""PTZ output plugin — stub."""
from __future__ import annotations

from typing import Optional

from app.models.camera_state import CameraState, PTZOutputConfig
from app.services.output.base import OutputPlugin


class PTZOutput(OutputPlugin):
    """PTZ output — stub, not yet implemented."""

    def __init__(self, config: Optional[PTZOutputConfig] = None) -> None:
        self._config = config or PTZOutputConfig()
        self._current_state: Optional[CameraState] = None

    @property
    def name(self) -> str:
        return "ptz"

    def apply(self, state: CameraState) -> None:
        self._current_state = state

    def get_state(self) -> Optional[CameraState]:
        return self._current_state

    def is_available(self) -> bool:
        return False
