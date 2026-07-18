"""Tests for the camera capture service."""
from __future__ import annotations

import threading
import time
from typing import List, Optional, Tuple

import numpy as np
import pytest

from app.services.camera.video_source import VideoSource
from app.services.camera.opencv_source import OpenCVSource
from app.services.camera.file_source import FileSource
from app.services.camera.camera_service import (
    CameraService,
    Frame,
    CameraServiceError,
)


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


class FakeVideoSource(VideoSource):
    """Test double for VideoSource with configurable behavior."""

    def __init__(
        self,
        fps: float = 30.0,
        resolution: Tuple[int, int] = (640, 480),
        frames: Optional[List[np.ndarray]] = None,
        open_should_fail: bool = False,
        read_should_fail: bool = False,
        loop: bool = False,
    ) -> None:
        self._fps = fps
        self._resolution = resolution
        self._frames: List[np.ndarray] = (
            list(frames) if frames is not None else self._make_frames(resolution, 5)
        )
        self._open_should_fail = open_should_fail
        self._read_should_fail = read_should_fail
        self._loop = loop
        self._opened = False
        self._released = False
        self._index = 0
        self._read_count = 0
        self._open_count = 0
        self._lock = threading.Lock()

    @staticmethod
    def _make_frames(resolution: Tuple[int, int], count: int) -> List[np.ndarray]:
        w, h = resolution
        return [np.zeros((h, w, 3), dtype=np.uint8) for _ in range(count)]

    def open(self) -> bool:
        self._open_count += 1
        if self._open_should_fail:
            self._opened = False
            return False
        self._opened = True
        self._index = 0
        return True

    def read(self):
        if self._read_should_fail:
            return False, None
        if not self._frames:
            return False, None
        with self._lock:
            self._read_count += 1
            if self._loop:
                frame = self._frames[self._index % len(self._frames)]
                self._index += 1
                return True, frame
            if self._index >= len(self._frames):
                return False, None
            frame = self._frames[self._index]
            self._index += 1
            return True, frame

    def release(self) -> None:
        self._released = True
        self._opened = False

    def is_opened(self) -> bool:
        return self._opened

    @property
    def fps(self) -> float:
        return self._fps

    @property
    def resolution(self) -> Tuple[int, int]:
        return self._resolution

    # Test introspection helpers
    @property
    def release_called(self) -> bool:
        return self._released

    @property
    def read_count(self) -> int:
        return self._read_count

    @property
    def open_count(self) -> int:
        return self._open_count


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_source() -> FakeVideoSource:
    return FakeVideoSource(fps=30.0, resolution=(640, 480))


@pytest.fixture
def service(fake_source: FakeVideoSource) -> CameraService:
    svc = CameraService(source=fake_source, buffer_size=4)
    yield svc
    if svc.is_running:
        svc.stop()


# ---------------------------------------------------------------------------
# VideoSource abstract interface
# ---------------------------------------------------------------------------


class TestVideoSourceInterface:
    def test_cannot_instantiate_abstract_class(self) -> None:
        with pytest.raises(TypeError):
            VideoSource()  # type: ignore[abstract]

    def test_subclass_must_implement_methods(self) -> None:
        class IncompleteSource(VideoSource):
            pass

        with pytest.raises(TypeError):
            IncompleteSource()  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# OpenCVSource
# ---------------------------------------------------------------------------


class TestOpenCVSource:
    def test_fps_defaults_to_zero_when_not_yet_read(self) -> None:
        src = OpenCVSource(device_id=0)
        assert src.fps == 0.0
        assert src.resolution == (0, 0)
        assert src.is_opened() is False

    def test_release_is_safe_when_not_open(self) -> None:
        src = OpenCVSource(device_id=0)
        src.release()
        assert src.is_opened() is False


# ---------------------------------------------------------------------------
# FileSource
# ---------------------------------------------------------------------------


class TestFileSource:
    def test_constructs_with_path(self, tmp_path) -> None:
        path = tmp_path / "video.avi"
        # Create a tiny dummy file; FileSource only stores the path
        path.write_bytes(b"")
        src = FileSource(str(path))
        assert src.fps == 0.0
        assert src.resolution == (0, 0)
        assert src.is_opened() is False


# ---------------------------------------------------------------------------
# CameraService lifecycle
# ---------------------------------------------------------------------------


class TestCameraServiceLifecycle:
    def test_starts_and_stops_capture_loop(self, fake_source: FakeVideoSource) -> None:
        svc = CameraService(source=fake_source, buffer_size=4)
        assert not svc.is_running
        svc.start()
        assert svc.is_running
        svc.stop()
        assert not svc.is_running

    def test_start_opens_underlying_source(self, fake_source: FakeVideoSource) -> None:
        svc = CameraService(source=fake_source, buffer_size=4)
        svc.start()
        try:
            assert fake_source.is_opened()
        finally:
            svc.stop()

    def test_stop_releases_underlying_source(self, fake_source: FakeVideoSource) -> None:
        svc = CameraService(source=fake_source, buffer_size=4)
        svc.start()
        svc.stop()
        assert fake_source.release_called

    def test_start_when_source_fails_to_open_continues(self) -> None:
        bad = FakeVideoSource(open_should_fail=True)
        svc = CameraService(source=bad, buffer_size=4, reconnect_interval=0.05)
        svc.start()
        assert svc.is_running
        svc.stop()

    def test_double_start_is_idempotent(self, fake_source: FakeVideoSource) -> None:
        svc = CameraService(source=fake_source, buffer_size=4)
        svc.start()
        try:
            open_count_before = fake_source.open_count
            svc.start()
            assert fake_source.open_count == open_count_before
        finally:
            svc.stop()

    def test_stop_when_not_running_is_safe(self, fake_source: FakeVideoSource) -> None:
        svc = CameraService(source=fake_source, buffer_size=4)
        svc.stop()
        assert not svc.is_running


# ---------------------------------------------------------------------------
# Frame retrieval and properties
# ---------------------------------------------------------------------------


class TestCameraServiceFrames:
    def test_get_frame_returns_none_initially(self, service: CameraService) -> None:
        assert service.get_frame() is None

    def test_capture_loop_produces_frames(self, service: CameraService) -> None:
        service.start()
        deadline = time.monotonic() + 2.0
        frame = None
        while time.monotonic() < deadline:
            frame = service.get_frame()
            if frame is not None:
                break
            time.sleep(0.01)
        assert frame is not None
        assert isinstance(frame.image, np.ndarray)
        assert frame.image.shape == (480, 640, 3)
        service.stop()

    def test_frame_has_sequence_and_timestamp(self, service: CameraService) -> None:
        service.start()
        deadline = time.monotonic() + 2.0
        frame: Optional[Frame] = None
        while time.monotonic() < deadline:
            frame = service.get_frame()
            if frame is not None and frame.sequence > 0:
                break
            time.sleep(0.01)
        assert frame is not None
        assert frame.sequence > 0
        assert frame.timestamp > 0.0
        service.stop()

    def test_frame_sequence_is_monotonic(self, service: CameraService) -> None:
        service.start()
        # Allow buffer to fill
        time.sleep(0.1)
        frames: List[Frame] = []
        for _ in range(3):
            f = service.get_frame()
            if f is not None:
                frames.append(f)
            time.sleep(0.02)
        service.stop()
        assert len(frames) >= 2
        for prev, curr in zip(frames, frames[1:]):
            assert curr.sequence >= prev.sequence

    def test_resolution_and_fps_reflect_source(self, service: CameraService) -> None:
        assert service.resolution == (640, 480)
        assert service.fps == pytest.approx(30.0)

    def test_get_frame_is_thread_safe(
        self, service: CameraService
    ) -> None:
        service.start()
        errors: List[Exception] = []

        def reader() -> None:
            try:
                for _ in range(50):
                    service.get_frame()
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=reader) for _ in range(4)]
        try:
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        finally:
            service.stop()
        assert errors == []


# ---------------------------------------------------------------------------
# Auto-reconnect
# ---------------------------------------------------------------------------


class TestCameraServiceAutoReconnect:
    def test_reconnects_after_read_failure(self, fake_source: FakeVideoSource) -> None:
        # Source that fails first, then succeeds
        original_read = fake_source.read
        call_state = {"calls": 0}

        def flaky_read():
            call_state["calls"] += 1
            if call_state["calls"] == 1:
                return False, None
            return original_read()

        fake_source.read = flaky_read  # type: ignore[method-assign]
        svc = CameraService(
            source=fake_source, buffer_size=4, reconnect_interval=0.05
        )
        svc.start()
        try:
            # Give the loop enough time to recover
            time.sleep(0.2)
            frame = service_get_frame_with_timeout(svc, timeout=1.0)
            assert frame is not None
            assert call_state["calls"] >= 2
        finally:
            svc.stop()

    def test_reconnect_after_open_failure(
        self, fake_source: FakeVideoSource
    ) -> None:
        # First open fails, second open succeeds
        open_state = {"calls": 0}
        original_open = fake_source.open

        def flaky_open() -> bool:
            open_state["calls"] += 1
            if open_state["calls"] == 1:
                return False
            return original_open()

        fake_source.open = flaky_open  # type: ignore[method-assign]
        svc = CameraService(
            source=fake_source, buffer_size=4, reconnect_interval=0.05
        )
        svc.start()
        try:
            time.sleep(0.3)
            assert open_state["calls"] >= 2
            assert svc.is_running
        finally:
            svc.stop()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def service_get_frame_with_timeout(
    service: CameraService, timeout: float
) -> Optional[Frame]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        frame = service.get_frame()
        if frame is not None:
            return frame
        time.sleep(0.01)
    return None
