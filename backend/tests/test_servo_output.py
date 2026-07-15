"""Tests for ServoOutput."""
import time
import pytest
from app.services.output.servo import ServoOutput, ServoMotionPlanner
from app.models.camera_state import CameraState, ServoOutputConfig
from app.models.motion import MotionProfile


def _make_state(cx=0.5, cy=0.5, zoom=1.5):
    return CameraState(
        center_x=cx, center_y=cy, zoom=zoom,
        motion_profile=MotionProfile.BROADCAST,
        tracking_mode="broadcast", confidence=0.9, timestamp=time.time(),
    )


def test_center_maps_to_default_angles():
    output = ServoOutput()
    output.apply(_make_state(0.5, 0.5))
    assert output.pan_angle == 90.0
    assert output.tilt_angle == 90.0


def test_left_edge_maps_to_pan_min():
    cfg = ServoOutputConfig(pan_min=0.0, pan_max=180.0)
    output = ServoOutput(cfg)
    output.apply(_make_state(0.0, 0.0))
    assert output.pan_angle == 0.0
    assert output.tilt_angle == 0.0


def test_right_edge_maps_to_pan_max():
    cfg = ServoOutputConfig(pan_min=0.0, pan_max=180.0)
    output = ServoOutput(cfg)
    output.apply(_make_state(1.0, 1.0))
    assert output.pan_angle == 180.0
    assert output.tilt_angle == 180.0


def test_motion_plan_generated():
    output = ServoOutput()
    output.apply(_make_state(0.0, 0.0))
    output.apply(_make_state(1.0, 1.0))
    assert output.motion_plan is not None
    assert len(output.motion_plan.waypoints) > 0


def test_reset_returns_to_defaults():
    output = ServoOutput()
    output.apply(_make_state(0.0, 0.0))
    output.reset()
    assert output.pan_angle == 90.0
    assert output.tilt_angle == 90.0
    assert output.motion_plan is None


def test_name():
    assert ServoOutput().name == "servo"


def test_custom_ranges():
    cfg = ServoOutputConfig(pan_min=30.0, pan_max=150.0, tilt_min=45.0, tilt_max=135.0)
    output = ServoOutput(cfg)
    output.apply(_make_state(0.5, 0.5))
    assert output.pan_angle == 90.0
    assert output.tilt_angle == 90.0
    output.apply(_make_state(0.0, 0.0))
    assert output.pan_angle == 30.0
    assert output.tilt_angle == 45.0
