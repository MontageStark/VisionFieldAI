"""Abstract video source interface for camera capture."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Tuple

import numpy as np


class VideoSource(ABC):
    """Abstract interface for any video frame source.

    Implementations must be thread-safe for ``release()`` being called from
    a different thread than the capture loop.
    """

    @abstractmethod
    def open(self) -> bool:
        """Open the underlying device/file. Returns True on success."""

    @abstractmethod
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read the next frame.

        Returns:
            (success, frame) tuple. On failure ``frame`` is None.
        """

    @abstractmethod
    def release(self) -> None:
        """Release the underlying resource. Safe to call when closed."""

    @abstractmethod
    def is_opened(self) -> bool:
        """Return True if the source is currently open."""

    @property
    @abstractmethod
    def fps(self) -> float:
        """Reported frames per second."""

    @property
    @abstractmethod
    def resolution(self) -> Tuple[int, int]:
        """Reported (width, height) of the source."""
