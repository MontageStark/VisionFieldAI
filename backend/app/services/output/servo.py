"""Servo output plugin — stub."""
from __future__ import annotations

from typing import Optional

from app.models.camera_state import CameraState, ServoOutputConfig
from app.services.output.base import OutputPlugin


class ServoOutput(OutputPlugin):
    """Servo output — stub for now."""

    def __init__(self, config: Optional[ServoOutputConfig] = None) -> None:
        self._config = config or ServoOutputConfig()
        self._current_state: Optional[CameraState] = None

    @property
    def name(self) -> str:
        return "servo"

    def apply(self, state: CameraState) -> None:
        self._current_state = state

    def get_state(self) -> Optional[CameraState]:
        return self._current_state

    def reset(self) -> None:
        self._current_state = None
