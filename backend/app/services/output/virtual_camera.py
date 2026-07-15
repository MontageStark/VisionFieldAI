"""Virtual camera output plugin — stub."""
from __future__ import annotations

from typing import Optional

from app.models.camera_state import CameraState, VirtualCameraConfig
from app.services.output.base import OutputPlugin


class VirtualCameraOutput(OutputPlugin):
    """Virtual camera output — stub for now."""

    def __init__(self, config: Optional[VirtualCameraConfig] = None) -> None:
        self._config = config or VirtualCameraConfig()
        self._current_state: Optional[CameraState] = None

    @property
    def name(self) -> str:
        return "virtual_camera"

    def apply(self, state: CameraState) -> None:
        self._current_state = state

    def get_state(self) -> Optional[CameraState]:
        return self._current_state

    def reset(self) -> None:
        self._current_state = None
