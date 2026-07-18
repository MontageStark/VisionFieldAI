"""CameraService: thread-safe capture loop with auto-reconnect."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

from app.services.camera.video_source import VideoSource


class CameraServiceError(RuntimeError):
    """Raised when the camera service fails to start or operate."""


@dataclass
class Frame:
    """A single captured frame."""

    image: np.ndarray
    sequence: int
    timestamp: float


class CameraService:
    """Capture loop that runs in a background thread.

    Stores only the latest frame in a thread-safe buffer. Auto-reconnects
    to the underlying source on read/open failures.
    """

    def __init__(
        self,
        source: VideoSource,
        buffer_size: int = 1,
        reconnect_interval: float = 0.5,
        event_bus=None,
    ) -> None:
        self._source = source
        self._buffer_size = max(1, int(buffer_size))
        self._reconnect_interval = float(reconnect_interval)
        self._event_bus = event_bus

        self._lock = threading.Lock()
        self._latest: Optional[Frame] = None
        self._sequence = 0

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def resolution(self) -> Tuple[int, int]:
        return self._source.resolution

    @property
    def fps(self) -> float:
        return self._source.fps

    def start(self) -> None:
        if self._running:
            return
        if not self._source.is_opened():
            opened = self._source.open()
            if not opened and not self._source.is_opened():
                # Let capture loop handle reconnection instead of failing immediately
                pass

        self._stop_event.clear()
        self._running = True
        self._thread = threading.Thread(
            target=self._capture_loop, name="CameraService-CaptureLoop", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        if not self._running:
            self._source.release()
            return
        self._stop_event.set()
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        try:
            self._source.release()
        except Exception:
            pass

    def get_frame(self) -> Optional[Frame]:
        with self._lock:
            return self._latest

    def _capture_loop(self) -> None:
        target_period = self._compute_target_period()
        next_deadline = time.monotonic()
        while not self._stop_event.is_set():
            if not self._source.is_opened():
                if not self._try_reconnect():
                    if self._stop_event.wait(self._reconnect_interval):
                        return
                    continue
                target_period = self._compute_target_period()
                next_deadline = time.monotonic()

            ok, image = self._source.read()
            if not ok or image is None:
                if not self._source.is_opened():
                    continue
                if self._stop_event.wait(self._reconnect_interval):
                    return
                self._try_reconnect()
                target_period = self._compute_target_period()
                next_deadline = time.monotonic()
                continue

            with self._lock:
                self._sequence += 1
                frame = Frame(
                    image=image,
                    sequence=self._sequence,
                    timestamp=time.time(),
                )
                self._latest = frame

            if self._event_bus is not None:
                try:
                    self._event_bus.publish(
                        "camera.frame_captured",
                        {
                            "sequence": frame.sequence,
                            "timestamp": frame.timestamp,
                            "shape": list(image.shape),
                        },
                    )
                except Exception:
                    pass

            if target_period > 0:
                next_deadline += target_period
                sleep_for = next_deadline - time.monotonic()
                if sleep_for < 0:
                    next_deadline = time.monotonic()
                    sleep_for = 0
                if self._stop_event.wait(sleep_for):
                    return
            else:
                if self._stop_event.wait(0.001):
                    return

    def _try_reconnect(self) -> bool:
        try:
            try:
                self._source.release()
            except Exception:
                pass
            opened = self._source.open()
            return bool(opened and self._source.is_opened())
        except Exception:
            return False

    def _compute_target_period(self) -> float:
        try:
            fps = float(self._source.fps)
        except Exception:
            fps = 0.0
        if fps <= 0:
            return 0.0
        return 1.0 / fps
