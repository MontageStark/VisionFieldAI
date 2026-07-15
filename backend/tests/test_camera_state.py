"""Tests for CameraState model and output configuration."""
import time

import pytest
from pydantic import ValidationError

from app.models.camera_state import (
    CameraState,
    OutputMode,
    OutputConfig,
    PTZOutputConfig,
    ServoOutputConfig,
    VirtualCameraConfig,
)
from app.models.motion import MotionProfile


class TestOutputMode:
    def test_output_modes(self):
        assert OutputMode.VIRTUAL == "virtual"
        assert OutputMode.SERVO == "servo"
        assert OutputMode.HYBRID == "hybrid"
        assert OutputMode.PTZ == "ptz"

    def test_all_modes_defined(self):
        assert len(OutputMode) == 4


class TestCameraState:
    def test_valid_camera_state(self):
        state = CameraState(
            center_x=0.5,
            center_y=0.5,
            zoom=1.5,
            motion_profile=MotionProfile.BROADCAST,
            confidence=0.85,
            timestamp=1000.0,
        )
        assert state.center_x == 0.5
        assert state.center_y == 0.5
        assert state.zoom == 1.5
        assert state.motion_profile == MotionProfile.BROADCAST
        assert state.tracking_mode == "broadcast"
        assert state.confidence == 0.85
        assert state.timestamp == 1000.0

    def test_camera_state_min_coordinates(self):
        state = CameraState(
            center_x=0.0,
            center_y=0.0,
            zoom=1.0,
            motion_profile=MotionProfile.BROADCAST,
            confidence=0.0,
            timestamp=1.0,
        )
        assert state.center_x == 0.0
        assert state.center_y == 0.0

    def test_camera_state_max_coordinates(self):
        state = CameraState(
            center_x=1.0,
            center_y=1.0,
            zoom=4.0,
            motion_profile=MotionProfile.BROADCAST,
            confidence=1.0,
            timestamp=1.0,
        )
        assert state.center_x == 1.0
        assert state.center_y == 1.0
        assert state.zoom == 4.0

    def test_invalid_center_x_negative(self):
        with pytest.raises(ValidationError):
            CameraState(
                center_x=-0.1,
                center_y=0.5,
                zoom=1.5,
                motion_profile=MotionProfile.BROADCAST,
                confidence=0.85,
                timestamp=1000.0,
            )

    def test_invalid_center_x_above_one(self):
        with pytest.raises(ValidationError):
            CameraState(
                center_x=1.1,
                center_y=0.5,
                zoom=1.5,
                motion_profile=MotionProfile.BROADCAST,
                confidence=0.85,
                timestamp=1000.0,
            )

    def test_invalid_center_y_negative(self):
        with pytest.raises(ValidationError):
            CameraState(
                center_x=0.5,
                center_y=-0.1,
                zoom=1.5,
                motion_profile=MotionProfile.BROADCAST,
                confidence=0.85,
                timestamp=1000.0,
            )

    def test_invalid_center_y_above_one(self):
        with pytest.raises(ValidationError):
            CameraState(
                center_x=0.5,
                center_y=1.1,
                zoom=1.5,
                motion_profile=MotionProfile.BROADCAST,
                confidence=0.85,
                timestamp=1000.0,
            )

    def test_invalid_zoom_too_low(self):
        with pytest.raises(ValidationError):
            CameraState(
                center_x=0.5,
                center_y=0.5,
                zoom=0.5,
                motion_profile=MotionProfile.BROADCAST,
                confidence=0.85,
                timestamp=1000.0,
            )

    def test_invalid_zoom_too_high(self):
        with pytest.raises(ValidationError):
            CameraState(
                center_x=0.5,
                center_y=0.5,
                zoom=5.0,
                motion_profile=MotionProfile.BROADCAST,
                confidence=0.85,
                timestamp=1000.0,
            )

    def test_invalid_confidence_negative(self):
        with pytest.raises(ValidationError):
            CameraState(
                center_x=0.5,
                center_y=0.5,
                zoom=1.5,
                motion_profile=MotionProfile.BROADCAST,
                confidence=-0.1,
                timestamp=1000.0,
            )

    def test_invalid_confidence_above_one(self):
        with pytest.raises(ValidationError):
            CameraState(
                center_x=0.5,
                center_y=0.5,
                zoom=1.5,
                motion_profile=MotionProfile.BROADCAST,
                confidence=1.1,
                timestamp=1000.0,
            )

    def test_invalid_timestamp_zero(self):
        with pytest.raises(ValidationError):
            CameraState(
                center_x=0.5,
                center_y=0.5,
                zoom=1.5,
                motion_profile=MotionProfile.BROADCAST,
                confidence=0.85,
                timestamp=0.0,
            )

    def test_invalid_timestamp_negative(self):
        with pytest.raises(ValidationError):
            CameraState(
                center_x=0.5,
                center_y=0.5,
                zoom=1.5,
                motion_profile=MotionProfile.BROADCAST,
                confidence=0.85,
                timestamp=-1.0,
            )

    def test_coordinates_rounded_to_four_decimals(self):
        state = CameraState(
            center_x=0.123456789,
            center_y=0.987654321,
            zoom=1.5,
            motion_profile=MotionProfile.BROADCAST,
            confidence=0.85,
            timestamp=1000.0,
        )
        assert state.center_x == pytest.approx(0.1235, abs=1e-4)
        assert state.center_y == pytest.approx(0.9877, abs=1e-4)

    def test_to_dict(self):
        state = CameraState(
            center_x=0.5,
            center_y=0.5,
            zoom=1.5,
            motion_profile=MotionProfile.BROADCAST,
            confidence=0.85,
            timestamp=1000.0,
        )
        d = state.to_dict()
        assert d["center_x"] == 0.5
        assert d["center_y"] == 0.5
        assert d["zoom"] == 1.5
        assert d["motion_profile"] == "broadcast"
        assert d["tracking_mode"] == "broadcast"
        assert d["confidence"] == 0.85
        assert d["timestamp"] == 1000.0

    def test_from_normalized_factory(self):
        state = CameraState.from_normalized(
            center_x=0.3,
            center_y=0.7,
            zoom=2.0,
            confidence=0.9,
        )
        assert state.center_x == 0.3
        assert state.center_y == 0.7
        assert state.zoom == 2.0
        assert state.confidence == 0.9
        assert state.motion_profile == MotionProfile.BROADCAST
        assert state.tracking_mode == "broadcast"
        assert state.timestamp > 0.0

    def test_from_normalized_with_custom_values(self):
        state = CameraState.from_normalized(
            center_x=0.6,
            center_y=0.4,
            zoom=3.0,
            confidence=0.75,
            motion_profile=MotionProfile.FAST_BREAK,
            tracking_mode="aggressive",
        )
        assert state.motion_profile == MotionProfile.FAST_BREAK
        assert state.tracking_mode == "aggressive"


class TestVirtualCameraConfig:
    def test_default_values(self):
        config = VirtualCameraConfig()
        assert config.dead_zone == 0.05
        assert config.safe_margin == 0.1
        assert config.max_velocity == 1.0
        assert config.smoothing_factor == 0.3
        assert config.default_zoom == 1.5

    def test_custom_values(self):
        config = VirtualCameraConfig(
            dead_zone=0.1,
            safe_margin=0.2,
            max_velocity=2.0,
            smoothing_factor=0.5,
            default_zoom=2.5,
        )
        assert config.dead_zone == 0.1
        assert config.safe_margin == 0.2

    def test_invalid_dead_zone_negative(self):
        with pytest.raises(ValidationError):
            VirtualCameraConfig(dead_zone=-0.1)

    def test_invalid_dead_zone_too_high(self):
        with pytest.raises(ValidationError):
            VirtualCameraConfig(dead_zone=0.3)

    def test_invalid_smoothing_factor_negative(self):
        with pytest.raises(ValidationError):
            VirtualCameraConfig(smoothing_factor=-0.1)

    def test_invalid_smoothing_factor_above_one(self):
        with pytest.raises(ValidationError):
            VirtualCameraConfig(smoothing_factor=1.1)


class TestServoOutputConfig:
    def test_default_values(self):
        config = ServoOutputConfig()
        assert config.pan_min == 0.0
        assert config.pan_max == 180.0
        assert config.tilt_min == 0.0
        assert config.tilt_max == 180.0
        assert config.default_pan == 90.0
        assert config.default_tilt == 90.0
        assert config.max_velocity == 90.0
        assert config.max_acceleration == 200.0

    def test_invalid_pan_min_negative(self):
        with pytest.raises(ValidationError):
            ServoOutputConfig(pan_min=-1.0)

    def test_invalid_pan_max_above_180(self):
        with pytest.raises(ValidationError):
            ServoOutputConfig(pan_max=200.0)

    def test_invalid_max_velocity_zero(self):
        with pytest.raises(ValidationError):
            ServoOutputConfig(max_velocity=0.0)

    def test_invalid_max_acceleration_negative(self):
        with pytest.raises(ValidationError):
            ServoOutputConfig(max_acceleration=-1.0)


class TestPTZOutputConfig:
    def test_default_values(self):
        config = PTZOutputConfig()
        assert config.host == "192.168.1.100"
        assert config.port == 80
        assert config.username is None
        assert config.password is None

    def test_custom_values(self):
        config = PTZOutputConfig(
            host="10.0.0.1",
            port=8080,
            username="admin",
            password="secret",
        )
        assert config.host == "10.0.0.1"
        assert config.port == 8080
        assert config.username == "admin"
        assert config.password == "secret"


class TestOutputConfig:
    def test_default_mode(self):
        config = OutputConfig()
        assert config.mode == OutputMode.VIRTUAL
        assert isinstance(config.virtual_camera, VirtualCameraConfig)
        assert isinstance(config.servo, ServoOutputConfig)
        assert isinstance(config.ptz, PTZOutputConfig)

    def test_custom_mode(self):
        config = OutputConfig(mode=OutputMode.SERVO)
        assert config.mode == OutputMode.SERVO

    def test_invalid_port_zero(self):
        with pytest.raises(ValidationError):
            OutputConfig(ptz=PTZOutputConfig(port=0))

    def test_invalid_port_above_65535(self):
        with pytest.raises(ValidationError):
            OutputConfig(ptz=PTZOutputConfig(port=70000))
