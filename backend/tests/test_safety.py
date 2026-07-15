"""Tests for the safety layer."""
from __future__ import annotations

import threading
import time
from typing import Any, Dict, List
from unittest.mock import MagicMock, call

import pytest

from app.core.events import EventPriority, Event, EventBus
from app.models.events import EventType
from app.models.safety import SafetyCheck, SafetyViolationType, SafetySeverity, SafetyViolation
from app.services.motion.safety import (
    SafetyLayer,
    ServoAxis,
    AxisLimits,
    ServoBounds,
)


class TestSafetyLayerInit:
    def test_init_with_defaults(self):
        sl = SafetyLayer()
        assert sl._watchdog_timeout == 2.0
        assert sl._connected is True
        assert sl._emergency_stopped is False
        assert sl._pan_limits.min_angle == 0.0
        assert sl._pan_limits.max_angle == 180.0
        assert sl._pan_limits.max_jump == 15.0

    def test_init_with_custom_limits(self):
        pan_limits = AxisLimits(min_angle=10.0, max_angle=170.0, max_jump=10.0)
        tilt_limits = AxisLimits(min_angle=20.0, max_angle=160.0, max_jump=8.0)
        sl = SafetyLayer(pan_limits=pan_limits, tilt_limits=tilt_limits)
        assert sl._pan_limits.min_angle == 10.0
        assert sl._pan_limits.max_angle == 170.0
        assert sl._pan_limits.max_jump == 10.0
        assert sl._tilt_limits.min_angle == 20.0
        assert sl._tilt_limits.max_angle == 160.0
        assert sl._tilt_limits.max_jump == 8.0

    def test_init_with_servo_bounds(self):
        bounds = ServoBounds(pan_min=5.0, pan_max=175.0, tilt_min=15.0, tilt_max=165.0)
        sl = SafetyLayer(servo_bounds=bounds)
        assert sl._servo_bounds.pan_min == 5.0
        assert sl._servo_bounds.pan_max == 175.0


class TestAngleValidation:
    def test_validate_angle_pan_within_limits(self):
        sl = SafetyLayer(pan_limits=AxisLimits(min_angle=0.0, max_angle=180.0))
        check = sl.validate_angle(ServoAxis.PAN, 90.0)
        assert check.passed is True

    def test_validate_angle_pan_outside_limits(self):
        sl = SafetyLayer(pan_limits=AxisLimits(min_angle=0.0, max_angle=180.0))
        check = sl.validate_angle(ServoAxis.PAN, 200.0)
        assert check.passed is False
        assert check.violation_type == SafetyViolationType.ANGLE_EXCEEDED
        assert check.clamped_angle == 180.0

    def test_validate_angle_below_minimum(self):
        sl = SafetyLayer(pan_limits=AxisLimits(min_angle=10.0, max_angle=170.0))
        check = sl.validate_angle(ServoAxis.PAN, 5.0)
        assert check.passed is False
        assert check.clamped_angle == 10.0

    def test_validate_angle_tilt_within_limits(self):
        sl = SafetyLayer(tilt_limits=AxisLimits(min_angle=30.0, max_angle=150.0))
        check = sl.validate_angle(ServoAxis.TILT, 90.0)
        assert check.passed is True

    def test_validate_angle_tilt_outside_limits(self):
        sl = SafetyLayer(tilt_limits=AxisLimits(min_angle=30.0, max_angle=150.0))
        check = sl.validate_angle(ServoAxis.TILT, 160.0)
        assert check.passed is False
        assert check.violation_type == SafetyViolationType.ANGLE_EXCEEDED
        assert check.clamped_angle == 150.0


class TestJumpValidation:
    def test_validate_jump_pan_within_limits(self):
        sl = SafetyLayer(pan_limits=AxisLimits(max_jump=15.0))
        check = sl.validate_jump(ServoAxis.PAN, 90.0, 100.0)
        assert check.passed is True

    def test_validate_jump_pan_exceeds_limit(self):
        sl = SafetyLayer(pan_limits=AxisLimits(max_jump=15.0))
        check = sl.validate_jump(ServoAxis.PAN, 90.0, 120.0)
        assert check.passed is False
        assert check.violation_type == SafetyViolationType.JUMP_LIMIT
        assert check.clamped_angle is not None
        assert 90.0 < check.clamped_angle < 120.0

    def test_validate_jump_tilt_within_limits(self):
        sl = SafetyLayer(tilt_limits=AxisLimits(max_jump=10.0))
        check = sl.validate_jump(ServoAxis.TILT, 90.0, 95.0)
        assert check.passed is True

    def test_validate_jump_tilt_exceeds_limit(self):
        sl = SafetyLayer(tilt_limits=AxisLimits(max_jump=10.0))
        check = sl.validate_jump(ServoAxis.TILT, 90.0, 110.0)
        assert check.passed is False
        assert check.violation_type == SafetyViolationType.JUMP_LIMIT

    def test_validate_jump_negative_direction(self):
        sl = SafetyLayer(pan_limits=AxisLimits(max_jump=15.0))
        check = sl.validate_jump(ServoAxis.PAN, 90.0, 70.0)
        assert check.passed is False
        assert check.violation_type == SafetyViolationType.JUMP_LIMIT


class TestCommandValidation:
    def test_validate_command_passes(self):
        sl = SafetyLayer()
        check = sl.validate_command(ServoAxis.PAN, 90.0, 100.0, 90.0)
        assert check.passed is True

    def test_validate_command_jump_failure(self):
        sl = SafetyLayer(pan_limits=AxisLimits(max_jump=5.0))
        check = sl.validate_command(ServoAxis.PAN, 90.0, 120.0, 90.0)
        assert check.passed is False
        assert check.violation_type == SafetyViolationType.JUMP_LIMIT

    def test_validate_command_angle_failure(self):
        sl = SafetyLayer(pan_limits=AxisLimits(min_angle=0.0, max_angle=180.0, max_jump=200.0))
        check = sl.validate_command(ServoAxis.PAN, 90.0, 200.0, 90.0)
        assert check.passed is False
        assert check.violation_type == SafetyViolationType.ANGLE_EXCEEDED

    def test_validate_command_speed_failure(self):
        sl = SafetyLayer()
        check = sl.validate_command(ServoAxis.PAN, 90.0, 100.0, 150.0)
        assert check.passed is False
        assert check.violation_type == SafetyViolationType.SPEED_LIMIT


class TestPositionBounds:
    def test_validate_position_bounds_both_valid(self):
        sl = SafetyLayer()
        valid, checks = sl.validate_position_bounds(90.0, 90.0)
        assert valid is True
        assert len(checks) == 2
        assert all(c.passed for c in checks)

    def test_validate_position_bounds_pan_invalid(self):
        sl = SafetyLayer(pan_limits=AxisLimits(min_angle=10.0, max_angle=170.0))
        valid, checks = sl.validate_position_bounds(5.0, 90.0)
        assert valid is False
        assert not checks[0].passed

    def test_validate_position_bounds_tilt_invalid(self):
        sl = SafetyLayer(tilt_limits=AxisLimits(min_angle=30.0, max_angle=150.0))
        valid, checks = sl.validate_position_bounds(90.0, 160.0)
        assert valid is False
        assert not checks[1].passed

    def test_validate_position_bounds_both_invalid(self):
        sl = SafetyLayer(
            pan_limits=AxisLimits(min_angle=10.0, max_angle=170.0),
            tilt_limits=AxisLimits(min_angle=30.0, max_angle=150.0),
        )
        valid, checks = sl.validate_position_bounds(200.0, 10.0)
        assert valid is False
        assert not checks[0].passed
        assert not checks[1].passed


class TestWatchdog:
    def test_watchdog_creates_timer(self):
        sl = SafetyLayer(watchdog_timeout=1.0)
        assert sl._watchdog_timer is None

    def test_watchdog_expires_without_reset(self):
        sl = SafetyLayer(watchdog_timeout=0.1)
        sl.update_position(pan=90.0)
        time.sleep(0.3)
        assert sl.watchdog_expired is True

    def test_watchdog_reset_on_position_update(self):
        sl = SafetyLayer(watchdog_timeout=0.5)
        sl._reset_watchdog()
        time.sleep(0.1)
        assert sl.watchdog_expired is False
        sl.update_position(pan=90.0)
        time.sleep(0.1)
        assert sl.watchdog_expired is False


class TestEmergencyStop:
    def test_emergency_stop_sets_flag(self):
        sl = SafetyLayer()
        sl.emergency_stop("Test stop")
        assert sl.is_emergency_stopped() is True
        assert sl.get_emergency_stop_reason() == "Test stop"

    def test_emergency_stop_publishes_event(self):
        mock_bus = MagicMock(spec=EventBus)
        sl = SafetyLayer(event_bus=mock_bus)
        sl.emergency_stop("Test stop")
        mock_bus.publish.assert_called()
        call_args = mock_bus.publish.call_args
        assert call_args[0][0] == EventType.EMERGENCY_STOP

    def test_emergency_stop_publishes_violation(self):
        mock_bus = MagicMock(spec=EventBus)
        sl = SafetyLayer(event_bus=mock_bus)
        sl.emergency_stop("Test stop")

        safety_violation_calls = [
            c for c in mock_bus.publish.call_args_list
            if c[0][0] == EventType.SAFETY_VIOLATION
        ]
        assert len(safety_violation_calls) >= 1

    def test_emergency_stop_callback(self):
        callback_called = threading.Event()

        def callback(reason: str) -> None:
            callback_called.set()

        sl = SafetyLayer(on_emergency_stop=callback)
        sl.emergency_stop("Test callback")
        assert callback_called.wait(timeout=1.0) is True

    def test_reset_emergency_stop(self):
        sl = SafetyLayer()
        sl.emergency_stop("Test stop")
        sl.reset_emergency_stop()
        assert sl.is_emergency_stopped() is False
        assert sl.get_emergency_stop_reason() is None

    def test_emergency_stop_prevents_further_stops(self):
        sl = SafetyLayer()
        sl.emergency_stop("First stop")
        sl.emergency_stop("Second stop")
        assert sl.get_emergency_stop_reason() == "First stop"


class TestDisconnect:
    def test_set_connected_false_triggers_estop(self):
        sl = SafetyLayer(watchdog_timeout=0.0)
        sl.set_connected(False)
        assert sl.is_emergency_stopped() is True
        assert "disconnected" in sl.get_emergency_stop_reason().lower()

    def test_is_connected(self):
        sl = SafetyLayer()
        assert sl.is_connected() is True
        sl.set_connected(False)
        assert sl.is_connected() is False


class TestSafetyLayerWithEventBus:
    def test_subscribes_to_servo_position(self):
        mock_bus = MagicMock(spec=EventBus)
        sl = SafetyLayer(event_bus=mock_bus)
        mock_bus.subscribe.assert_any_call(EventType.SERVO_POSITION, sl._on_servo_position)

    def test_subscribes_to_camera_disconnect(self):
        mock_bus = MagicMock(spec=EventBus)
        sl = SafetyLayer(event_bus=mock_bus)
        mock_bus.subscribe.assert_any_call(EventType.CAMERA_DISCONNECTED, sl._on_camera_disconnected)

    def test_on_servo_position_updates_position(self):
        mock_bus = MagicMock(spec=EventBus)
        sl = SafetyLayer(event_bus=mock_bus)
        event = MagicMock()
        event.data = {"pan_angle": 75.0, "tilt_angle": 120.0}
        sl._on_servo_position(event)
        pan, tilt = sl.get_current_position()
        assert pan == 75.0
        assert tilt == 120.0

    def test_on_servo_position_partial_update(self):
        mock_bus = MagicMock(spec=EventBus)
        sl = SafetyLayer(event_bus=mock_bus)
        sl.update_position(pan=90.0, tilt=90.0)
        event = MagicMock()
        event.data = {"pan_angle": 45.0}
        sl._on_servo_position(event)
        pan, tilt = sl.get_current_position()
        assert pan == 45.0
        assert tilt == 90.0


class TestViolationTracking:
    def test_violation_count_increments(self):
        sl = SafetyLayer()
        sl.emergency_stop("Test")
        assert sl.violation_count == 1

    def test_last_violation_recorded(self):
        sl = SafetyLayer()
        sl.emergency_stop("Test violation")
        violation = sl.last_violation
        assert violation is not None
        assert violation.severity == SafetySeverity.CRITICAL

    def test_record_violation_increments_count(self):
        mock_bus = MagicMock(spec=EventBus)
        sl = SafetyLayer(event_bus=mock_bus)
        violation = SafetyViolation(
            violation_type=SafetyViolationType.JUMP_LIMIT,
            severity=SafetySeverity.WARNING,
            message="Test violation",
            timestamp=time.time(),
            source="test",
            action_taken="clamped",
        )
        sl.record_violation(violation)
        assert sl.violation_count == 1


class TestLimitsManagement:
    def test_set_limits(self):
        sl = SafetyLayer()
        sl.set_limits(ServoAxis.PAN, min_angle=10.0, max_angle=170.0, max_jump=20.0)
        limits = sl.get_limits(ServoAxis.PAN)
        assert limits.min_angle == 10.0
        assert limits.max_angle == 170.0
        assert limits.max_jump == 20.0

    def test_set_limits_tilt(self):
        sl = SafetyLayer()
        sl.set_limits(ServoAxis.TILT, min_angle=20.0, max_angle=160.0, max_jump=12.0)
        limits = sl.get_limits(ServoAxis.TILT)
        assert limits.min_angle == 20.0
        assert limits.max_angle == 160.0
        assert limits.max_jump == 12.0


class TestStats:
    def test_get_stats(self):
        sl = SafetyLayer()
        stats = sl.get_stats()
        assert "violation_count" in stats
        assert "emergency_stopped" in stats
        assert "connected" in stats
        assert "watchdog_expired" in stats
        assert "current_pan" in stats
        assert "current_tilt" in stats

    def test_stats_reflect_emergency_stop(self):
        sl = SafetyLayer()
        sl.emergency_stop("Test")
        stats = sl.get_stats()
        assert stats["emergency_stopped"] is True
        assert stats["violation_count"] == 1


class TestUpdatePosition:
    def test_update_position_both(self):
        sl = SafetyLayer()
        sl.update_position(pan=45.0, tilt=135.0)
        pan, tilt = sl.get_current_position()
        assert pan == 45.0
        assert tilt == 135.0

    def test_update_position_pan_only(self):
        sl = SafetyLayer()
        sl.update_position(pan=45.0)
        pan, tilt = sl.get_current_position()
        assert pan == 45.0
        assert tilt == 90.0

    def test_update_position_tilt_only(self):
        sl = SafetyLayer()
        sl.update_position(tilt=135.0)
        pan, tilt = sl.get_current_position()
        assert pan == 90.0
        assert tilt == 135.0