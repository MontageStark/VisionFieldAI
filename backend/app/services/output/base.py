"""Output plugin system for FieldVision AI."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.models.camera_state import CameraState


class OutputPlugin(ABC):
    """Abstract base class for all output renderers.

    Each plugin translates abstract CameraState into device-specific commands.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin identifier string."""
        ...

    @abstractmethod
    def apply(self, state: CameraState) -> None:
        """Apply a camera state to the output device."""
        ...

    @abstractmethod
    def get_state(self) -> Optional[CameraState]:
        """Get the current rendered camera state."""
        ...

    def reset(self) -> None:
        """Reset output to default position."""
        pass

    def is_available(self) -> bool:
        """Check if the output device is available."""
        return True


class OutputPluginError(RuntimeError):
    """Raised when an output plugin encounters an error."""
