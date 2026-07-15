"""Video file source for simulation/testing."""
from __future__ import annotations

import threading
from typing import Optional, Tuple

import cv2
import numpy as np

from app.services.camera.video_source import VideoSource


class FileSource(VideoSource):
    """VideoSource backed by a video file on disk.

    Useful for simulation mode where no physical camera is available.
    """

    def __init__(self, path: str, loop: bool = False) -> None:
        self._path = path
        self._loop = loop
        self._cap: Optional[cv2.VideoCapture] = None
        self._lock = threading.Lock()
        self._fps_value: float = 0.0
        self._resolution_value: Tuple[int, int] = (0, 0)
        self._frame_count: int = 0

    def open(self) -> bool:
        with self._lock:
            if self._cap is not None and self._cap.isOpened():
                return True
            self._cap = cv2.VideoCapture(self._path)
            if not self._cap.isOpened():
                self._cap.release()
                self._cap = None
                return False

            width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = float(self._cap.get(cv2.CAP_PROP_FPS))
            self._resolution_value = (width, height)
            self._fps_value = fps if fps > 0 else 0.0
            self._frame_count = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
            return True

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        with self._lock:
            if self._cap is None or not self._cap.isOpened():
                return False, None
            ok, frame = self._cap.read()
        if not ok or frame is None:
            if self._loop and self._cap is not None:
                with self._lock:
                    self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ok2, frame2 = self._cap.read()
                if ok2 and frame2 is not None:
                    return True, frame2
            return False, None
        return True, frame

    def release(self) -> None:
        with self._lock:
            if self._cap is not None:
                try:
                    self._cap.release()
                except Exception:  # noqa: BLE001
                    pass
                self._cap = None

    def is_opened(self) -> bool:
        with self._lock:
            return self._cap is not None and self._cap.isOpened()

    @property
    def fps(self) -> float:
        return self._fps_value

    @property
    def resolution(self) -> Tuple[int, int]:
        return self._resolution_value
