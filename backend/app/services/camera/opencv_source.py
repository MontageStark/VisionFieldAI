"""OpenCV-based physical camera source."""
from __future__ import annotations

import threading
from typing import Optional, Tuple

import cv2
import numpy as np

from app.services.camera.video_source import VideoSource


class OpenCVSource(VideoSource):
    """VideoSource backed by ``cv2.VideoCapture`` for physical cameras."""

    def __init__(
        self,
        device_id: int = 0,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
        backend: Optional[int] = None,
    ) -> None:
        self._device_id = device_id
        self._requested_width = width
        self._requested_height = height
        self._requested_fps = fps
        self._backend = backend
        self._cap: Optional[cv2.VideoCapture] = None
        self._lock = threading.Lock()
        self._fps_value: float = 0.0
        self._resolution_value: Tuple[int, int] = (0, 0)

    def open(self) -> bool:
        with self._lock:
            if self._cap is not None and self._cap.isOpened():
                return True
            if self._backend is not None:
                self._cap = cv2.VideoCapture(self._device_id, self._backend)
            else:
                self._cap = cv2.VideoCapture(self._device_id)

            if not self._cap.isOpened():
                self._cap.release()
                self._cap = None
                return False

            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, float(self._requested_width))
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, float(self._requested_height))
            self._cap.set(cv2.CAP_PROP_FPS, float(self._requested_fps))

            width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = float(self._cap.get(cv2.CAP_PROP_FPS)) or float(self._requested_fps)
            self._resolution_value = (width, height)
            self._fps_value = fps if fps > 0 else 0.0
            return True

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        with self._lock:
            if self._cap is None or not self._cap.isOpened():
                return False, None
            ok, frame = self._cap.read()
        if not ok or frame is None:
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
