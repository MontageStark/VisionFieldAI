"""Tests for VirtualCameraOutput."""
import numpy as np
import time
import pytest

from app.services.output.virtual_camera import VirtualCameraOutput
from app.models.camera_state import CameraState, VirtualCameraConfig
from app.models.motion import MotionProfile


def _make_state(cx=0.5, cy=0.5, zoom=1.5, ts=None):
    return CameraState(
        center_x=cx, center_y=cy, zoom=zoom,
        motion_profile=MotionProfile.BROADCAST,
        tracking_mode="broadcast", confidence=0.9,
        timestamp=ts or time.time(),
    )


def test_apply_updates_state():
    plugin = VirtualCameraOutput()
    state = _make_state(0.3, 0.7, 2.0)
    plugin.apply(state)
    result = plugin.get_state()
    assert result.center_x == 0.3
    assert result.center_y == 0.7
    assert result.zoom == 2.0


def test_dead_zone_prevents_small_movements():
    cfg = VirtualCameraConfig(dead_zone=0.05)
    plugin = VirtualCameraOutput(cfg)
    plugin.apply(_make_state(0.5, 0.5))
    plugin.apply(_make_state(0.51, 0.51))  # within dead zone
    result = plugin.get_state()
    assert abs(result.center_x - 0.5) < 0.001


def test_dead_zone_allows_large_movements():
    cfg = VirtualCameraConfig(dead_zone=0.05)
    plugin = VirtualCameraOutput(cfg)
    plugin.apply(_make_state(0.5, 0.5))
    plugin.apply(_make_state(0.7, 0.7))  # outside dead zone
    result = plugin.get_state()
    assert abs(result.center_x - 0.7) < 0.001


def test_apply_frame_center():
    plugin = VirtualCameraOutput(VirtualCameraConfig(dead_zone=0.0))
    plugin.apply(_make_state(0.5, 0.5, 2.0))
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    result = plugin.apply_frame(frame)
    assert result.shape == (480, 640, 3)


def test_apply_frame_crop_size():
    plugin = VirtualCameraOutput(VirtualCameraConfig(dead_zone=0.0))
    plugin.apply(_make_state(0.5, 0.5, 2.0))
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    result = plugin.apply_frame(frame)
    assert result.shape[0] == 480
    assert result.shape[1] == 640


def test_apply_frame_returns_input_when_no_state():
    plugin = VirtualCameraOutput()
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    result = plugin.apply_frame(frame)
    np.testing.assert_array_equal(result, frame)


def test_reset_returns_to_center():
    plugin = VirtualCameraOutput()
    plugin.apply(_make_state(0.2, 0.8, 2.5))
    plugin.reset()
    result = plugin.get_state()
    assert result.center_x == 0.5
    assert result.center_y == 0.5
    assert result.zoom == 1.5


def test_name():
    assert VirtualCameraOutput().name == "virtual_camera"
