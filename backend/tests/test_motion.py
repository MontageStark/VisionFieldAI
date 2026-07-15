"""Tests for the motion planner and smoothing utilities."""
from __future__ import annotations

import threading
import time
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

from app.core.events import EventType, Event, EventPriority, EventBus
from app.models.motion import MotionProfile, MotionPlan, ServoCommand
from app.models.safety import SafetyCheck, SafetyViolationType, SafetySeverity
from app.services.motion.smooth import (
    ease_in,
    ease_in_out,
    ease_out,
    ease_out_elastic,
    lerp,
    lerp_angle,
    smoothstep,
    apply_smoothing,
    generate_waypoints,
    trapezoidal_velocity_profile,
    time_between_angles,
)
from app.services.motion.motion_planner import (
    MotionPlanner,
    MotionPlannerConfig,
    SafetyLayer,
    ServoAxis,
    ServoState,
    VelocityLimit,
)


class TestEasingFunctions:
    def test_ease_in_out_boundary(self):
        assert ease_in_out(0.0) == pytest.approx(0.0, abs=1e-6)
        assert ease_in_out(1.0) == pytest.approx(1.0, abs=1e-6)
        assert ease_in_out(0.5) == pytest.approx(0.5, abs=1e-6)

    def test_ease_in_out_monotonic(self):
        vals = [ease_in_out(t / 100.0) for t in range(101)]
        assert vals == sorted(vals)

    def test_ease_in_boundary(self):
        assert ease_in(0.0) == pytest.approx(0.0, abs=1e-6)
        assert ease_in(1.0) == pytest.approx(1.0, abs=1e-6)

    def test_ease_in_accelerates(self):
        d1 = ease_in(0.25) - ease_in(0.0)
        d2 = ease_in(0.50) - ease_in(0.25)
        assert d2 > d1

    def test_ease_out_boundary(self):
        assert ease_out(0.0) == pytest.approx(0.0, abs=1e-6)
        assert ease_out(1.0) == pytest.approx(1.0, abs=1e-6)

    def test_ease_out_decelerates(self):
        d1 = ease_out(0.25) - ease_out(0.0)
        d2 = ease_out(0.50) - ease_out(0.25)
        assert d1 > d2

    def test_ease_out_elastic_boundary(self):
        assert ease_out_elastic(0.0) == pytest.approx(0.0, abs=1e-3)
        assert ease_out_elastic(1.0) == pytest.approx(1.0, abs=1e-3)


class TestLerp:
    def test_lerp_at_boundaries(self):
        assert lerp(10.0, 20.0, 0.0) == pytest.approx(10.0)
        assert lerp(10.0, 20.0, 1.0) == pytest.approx(20.0)

    def test_lerp_at_midpoint(self):
        assert lerp(10.0, 20.0, 0.5) == pytest.approx(15.0)

    def test_lerp_clamps(self):
        assert lerp(10.0, 20.0, -0.5) == pytest.approx(10.0)
        assert lerp(10.0, 20.0, 1.5) == pytest.approx(20.0)

    def test_lerp_angle_wraparound(self):
        assert lerp_angle(350.0, 10.0, 0.5) == pytest.approx(0.0, abs=0.1)
        assert lerp_angle(10.0, 350.0, 0.5) == pytest.approx(0.0, abs=0.1)


class TestSmoothstep:
    def test_smoothstep_at_boundaries(self):
        assert smoothstep(5.0, 10.0, 0.0) == pytest.approx(5.0)
        assert smoothstep(5.0, 10.0, 1.0) == pytest.approx(10.0)

    def test_smoothstep_at_midpoint(self):
        assert smoothstep(0.0, 1.0, 0.5) == pytest.approx(0.5)


class TestApplySmoothing:
    def test_smoothing_factor_bounds(self):
        assert apply_smoothing(0.0, 100.0, 0.001) == pytest.approx(0.1, abs=0.01)
        assert apply_smoothing(0.0, 100.0, 1.0) == pytest.approx(100.0)

    def test_smoothing_no_change_when_equal(self):
        assert apply_smoothing(50.0, 50.0, 0.5) == pytest.approx(50.0)


class TestGenerateWaypoints:
    def test_waypoint_count(self):
        wp = generate_waypoints(0.0, 100.0, 5)
        assert len(wp) == 5

    def test_waypoint_endpoints(self):
        wp = generate_waypoints(0.0, 100.0, 5)
        assert wp[0] == pytest.approx(0.0)
        assert wp[-1] == pytest.approx(100.0)

    def test_empty_count(self):
        assert generate_waypoints(0.0, 100.0, 0) == []
        assert generate_waypoints(0.0, 100.0, 1) == [0.0]


class TestVelocityProfile:
    def test_zero_distance(self):
        accel, cruise, decel = trapezoidal_velocity_profile(0.0, 90.0, 200.0)
        assert accel == 0.0
        assert cruise == 0.0
        assert decel == 0.0

    def test_triangle_profile(self):
        accel, cruise, decel = trapezoidal_velocity_profile(1.0, 90.0, 200.0)
        assert cruise == pytest.approx(0.0, abs=1e-6)
        assert accel > 0.0
        assert decel > 0.0

    def test_trapezoidal_profile(self):
        accel, cruise, decel = trapezoidal_velocity_profile(50.0, 90.0, 200.0)
        total = accel + cruise + decel
        assert total > 0.0
        assert cruise >= 0.0

    def test_time_between_angles(self):
        t = time_between_angles(0.0, 90.0, 90.0, 200.0)
        assert t > 0.0


class TestSafetyLayer:
    def test_validate_angle_within_limits(self):
        sl = SafetyLayer(min_angle=0.0, max_angle=180.0)
        check = sl.validate_angle(90.0)
        assert check.passed is True

    def test_validate_angle_outside_limits(self):
        sl = SafetyLayer(min_angle=0.0, max_angle=180.0)
        check = sl.validate_angle(200.0)
        assert check.passed is False
        assert check.violation_type == SafetyViolationType.ANGLE_EXCEEDED
        assert check.clamped_angle == 180.0

    def test_validate_jump_within_limits(self):
        sl = SafetyLayer(max_jump_per_update=15.0)
        check = sl.validate_jump(90.0, 100.0)
        assert check.passed is True

    def test_validate_jump_exceeds_limit(self):
        sl = SafetyLayer(max_jump_per_update=15.0)
        check = sl.validate_jump(90.0, 120.0)
        assert check.passed is False
        assert check.violation_type == SafetyViolationType.JUMP_LIMIT

    def test_validate_command_passes(self):
        sl = SafetyLayer()
        check = sl.validate_command(90.0, 100.0, 90.0)
        assert check.passed is True

    def test_validate_command_speed_exceeded(self):
        sl = SafetyLayer()
        check = sl.validate_command(90.0, 100.0, 150.0)
        assert check.passed is False
        assert check.violation_type == SafetyViolationType.SPEED_LIMIT


class TestVelocityLimit:
    def test_clamp_velocity(self):
        vl = VelocityLimit(max_velocity=90.0)
        assert vl.clamp_velocity(50.0) == 50.0
        assert vl.clamp_velocity(150.0) == 90.0
        assert vl.clamp_velocity(-150.0) == -90.0

    def test_clamp_acceleration(self):
        vl = VelocityLimit(max_acceleration=200.0)
        assert vl.clamp_acceleration(100.0) == 100.0
        assert vl.clamp_acceleration(300.0) == 200.0


class TestServoState:
    def test_servo_state_defaults(self):
        state = ServoState()
        assert state.current_angle == 90.0
        assert state.target_angle == 90.0
        assert state.last_velocity == 0.0


class TestMotionPlannerInit:
    def test_init_with_defaults(self):
        mp = MotionPlanner()
        assert mp._event_bus is None
        assert mp._running is False
        assert mp.stats["camera_moves_received"] == 0
        assert mp.stats["servo_commands_published"] == 0

    def test_init_with_config(self):
        config = MotionPlannerConfig(
            max_velocity=45.0,
            max_acceleration=100.0,
            default_pan=45.0,
            default_tilt=135.0,
        )
        mp = MotionPlanner(config=config)
        assert mp._config.max_velocity == 45.0
        assert mp._config.default_pan == 45.0
        assert mp._config.default_tilt == 135.0

    def test_init_with_mock_event_bus(self):
        mock_bus = MagicMock(spec=EventBus)
        config = MotionPlannerConfig(event_bus=mock_bus)
        mp = MotionPlanner(config=config)
        assert mp._event_bus is mock_bus
        mock_bus.subscribe.assert_any_call(EventType.CAMERA_MOVE, mp._on_camera_move)
        mock_bus.subscribe.assert_any_call(EventType.SERVO_POSITION, mp._on_servo_position)


class TestMotionPlannerLifecycle:
    def test_start_stop(self):
        mp = MotionPlanner()
        mp.start()
        assert mp.is_running is True
        mp.stop()
        assert mp.is_running is False


class TestMotionPlannerHoming:
    def test_homing_sets_default_angles(self):
        mock_bus = MagicMock(spec=EventBus)
        config = MotionPlannerConfig(
            event_bus=mock_bus,
            default_pan=45.0,
            default_tilt=135.0,
        )
        mp = MotionPlanner(config=config)
        mp._pan_state.current_angle = 50.0
        mp._tilt_state.current_angle = 130.0

        commands = mp.execute_homing()
        assert len(commands) == 2
        mock_bus.publish.assert_called()


class TestMotionPlannerCameraMove:
    def test_on_camera_move_updates_state(self):
        mock_bus = MagicMock(spec=EventBus)
        config = MotionPlannerConfig(event_bus=mock_bus)
        mp = MotionPlanner(config=config)
        mp.start()

        event = MagicMock()
        event.data = {"pan": 60.0, "tilt": 120.0, "sequence": 1}
        mp._on_camera_move(event)

        assert mp.stats["camera_moves_received"] == 1


class TestMotionPlannerMotionProfile:
    def test_generate_motion_profile(self):
        mp = MotionPlanner()
        plan = mp.generate_motion_profile(
            45.0, 135.0, MotionProfile.BROADCAST
        )
        assert isinstance(plan, MotionPlan)
        assert len(plan.waypoints) >= 2
        assert plan.waypoints[0] == pytest.approx(45.0)
        assert plan.waypoints[-1] == pytest.approx(135.0)
        assert plan.total_duration > 0.0

    def test_generate_motion_profile_fast_break(self):
        mp = MotionPlanner()
        plan = mp.generate_motion_profile(
            0.0, 180.0, MotionProfile.FAST_BREAK
        )
        assert plan.profile == MotionProfile.FAST_BREAK
        assert len(plan.waypoints) >= 2


class TestMotionPlannerSafetyIntegration:
    def test_safety_layer_blocks_invalid_jump(self):
        mock_bus = MagicMock(spec=EventBus)
        safety = SafetyLayer(max_jump_per_update=5.0)
        config = MotionPlannerConfig(
            event_bus=mock_bus,
            safety_layer=safety,
            default_pan=90.0,
            default_tilt=90.0,
        )
        mp = MotionPlanner(config=config)
        mp._pan_state.current_angle = 90.0

        event = MagicMock()
        event.data = {"pan": 150.0, "tilt": 90.0, "sequence": 1}
        mp._on_camera_move(event)

        assert mp.stats["safety_violations_blocked"] >= 0


class TestMotionPlannerServoPosition:
    def test_on_servo_position_updates_pan(self):
        mock_bus = MagicMock(spec=EventBus)
        config = MotionPlannerConfig(event_bus=mock_bus)
        mp = MotionPlanner(config=config)

        event = MagicMock()
        event.data = {"pan_angle": 75.0}
        mp._on_servo_position(event)

        assert mp.pan_state.current_angle == 75.0


class TestMotionPlannerReset:
    def test_reset_clears_stats(self):
        mock_bus = MagicMock(spec=EventBus)
        config = MotionPlannerConfig(event_bus=mock_bus)
        mp = MotionPlanner(config=config)
        mp._stats["camera_moves_received"] = 10

        mp.reset()
        assert mp.stats["camera_moves_received"] == 0


class TestMotionPlannerCurrentAngles:
    def test_get_current_angles(self):
        mp = MotionPlanner()
        mp._pan_state.current_angle = 100.0
        mp._tilt_state.current_angle = 60.0
        pan, tilt = mp.get_current_angles()
        assert pan == 100.0
        assert tilt == 60.0


class TestMotionPlannerSetSafetyLayer:
    def test_set_safety_layer(self):
        mp = MotionPlanner()
        new_safety = SafetyLayer(max_jump_per_update=30.0)
        mp.set_safety_layer(new_safety)
        assert mp._safety is new_safety