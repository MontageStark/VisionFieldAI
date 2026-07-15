"""MotionPlanner: smooth camera motion with velocity limiting and safety validation."""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.core.events import EventType, EventPriority, Event
from app.models.motion import MotionProfile, MotionPlan, ServoCommand
from app.models.safety import SafetyCheck, SafetyViolationType, SafetySeverity

logger = logging.getLogger(__name__)


class ServoAxis(str, Enum):
    """Servo axis identifiers."""

    PAN = "pan"
    TILT = "tilt"


@dataclass
class VelocityLimit:
    """Velocity limit configuration for a single axis."""

    max_velocity: float = 90.0
    max_acceleration: float = 200.0

    def clamp_velocity(self, velocity: float) -> float:
        return max(-self.max_velocity, min(self.max_velocity, velocity))

    def clamp_acceleration(self, acceleration: float) -> float:
        return max(-self.max_acceleration, min(self.max_acceleration, acceleration))


@dataclass
class ServoState:
    """Current state of a servo axis."""

    current_angle: float = 90.0
    target_angle: float = 90.0
    last_velocity: float = 0.0
    last_update: float = 0.0


class SafetyLayer:
    """Validates servo commands against safety constraints.

    This layer performs pre-command validation to ensure angles
    and velocities are within safe operating limits.
    """

    def __init__(
        self,
        min_angle: float = 0.0,
        max_angle: float = 180.0,
        max_jump_per_update: float = 15.0,
    ) -> None:
        self._min_angle = min_angle
        self._max_angle = max_angle
        self._max_jump_per_update = max_jump_per_update

    def validate_angle(self, angle: float) -> SafetyCheck:
        if self._min_angle <= angle <= self._max_angle:
            return SafetyCheck(passed=True, message="Angle within limits")
        clamped = max(self._min_angle, min(self._max_angle, angle))
        return SafetyCheck(
            passed=False,
            violation_type=SafetyViolationType.ANGLE_EXCEEDED,
            severity=SafetySeverity.ERROR,
            message=f"Angle {angle} outside [{self._min_angle}, {self._max_angle}]",
            original_angle=angle,
            clamped_angle=clamped,
        )

    def validate_jump(self, current_angle: float, target_angle: float) -> SafetyCheck:
        jump = abs(target_angle - current_angle)
        if jump <= self._max_jump_per_update:
            return SafetyCheck(passed=True, message=f"Jump {jump:.1f} deg is safe")
        clamped = current_angle + (
            (target_angle - current_angle) / jump * self._max_jump_per_update
        )
        return SafetyCheck(
            passed=False,
            violation_type=SafetyViolationType.JUMP_LIMIT,
            severity=SafetySeverity.WARNING,
            message=f"Jump {jump:.1f} deg exceeds limit {self._max_jump_per_update} deg",
            original_angle=target_angle,
            clamped_angle=clamped,
        )

    def validate_command(
        self,
        current_angle: float,
        target_angle: float,
        speed: float,
    ) -> SafetyCheck:
        jump_check = self.validate_jump(current_angle, target_angle)
        if not jump_check.passed:
            return jump_check
        angle_check = self.validate_angle(target_angle)
        if not angle_check.passed:
            return angle_check
        if speed > 120.0:
            return SafetyCheck(
                passed=False,
                violation_type=SafetyViolationType.SPEED_LIMIT,
                severity=SafetySeverity.ERROR,
                message=f"Speed {speed} exceeds 120 deg/s",
            )
        return SafetyCheck(passed=True, message="Command validated")


@dataclass
class MotionPlannerConfig:
    """MotionPlanner configuration."""

    event_bus: Any = None
    safety_layer: Optional[SafetyLayer] = None
    max_velocity: float = 90.0
    max_acceleration: float = 200.0
    smoothing_factor: float = 0.3
    default_pan: float = 90.0
    default_tilt: float = 90.0
    sequence_offset: int = 0


class MotionPlanner:
    """Smooth camera motion planner with velocity limiting and safety validation.

    Subscribes to CAMERA_MOVE events from the DirectorService, generates
    smooth motion profiles with waypoints and timing, validates commands
    through SafetyLayer, and publishes SERVO_COMMAND events to drive servos.

    Features:
    - Easing functions for smooth acceleration/deceleration
    - Per-axis velocity limiting
    - Motion profile generation with waypoints and timing
    - Safety validation before each command
    - Homing sequence to return to default position
    """

    def __init__(
        self,
        config: Optional[MotionPlannerConfig] = None,
    ) -> None:
        if config is not None:
            self._config = config
        else:
            self._config = MotionPlannerConfig()

        self._event_bus = self._config.event_bus
        self._safety = self._config.safety_layer or SafetyLayer()

        self._pan_state = ServoState(
            current_angle=self._config.default_pan,
            target_angle=self._config.default_pan,
            last_update=time.time(),
        )
        self._tilt_state = ServoState(
            current_angle=self._config.default_tilt,
            target_angle=self._config.default_tilt,
            last_update=time.time(),
        )

        self._pan_limit = VelocityLimit(
            max_velocity=self._config.max_velocity,
            max_acceleration=self._config.max_acceleration,
        )
        self._tilt_limit = VelocityLimit(
            max_velocity=self._config.max_velocity,
            max_acceleration=self._config.max_acceleration,
        )

        self._sequence: int = self._config.sequence_offset
        self._running = False
        self._lock = threading.Lock()
        self._homing = False
        self._pending_commands: List[ServoCommand] = []

        self._stats = {
            "camera_moves_received": 0,
            "servo_commands_published": 0,
            "safety_violations_blocked": 0,
            "homing_executions": 0,
            "errors": 0,
        }

        if self._event_bus is not None:
            self._subscribe_to_events()

    def _subscribe_to_events(self) -> None:
        if self._event_bus is None:
            return
        try:
            self._event_bus.subscribe(
                EventType.CAMERA_MOVE,
                self._on_camera_move,
            )
            self._event_bus.subscribe(
                EventType.SERVO_POSITION,
                self._on_servo_position,
            )
            logger.info("MotionPlanner subscribed to %s and %s",
                       EventType.CAMERA_MOVE.value, EventType.SERVO_POSITION.value)
        except Exception as exc:
            logger.error("Failed to subscribe to events: %s", exc)

    def _on_camera_move(self, event: Event) -> None:
        try:
            data = event.data if hasattr(event, "data") else {}
            pan = float(data.get("pan", 90.0))
            tilt = float(data.get("tilt", 90.0))
            sequence = int(data.get("sequence", 0))

            self._stats["camera_moves_received"] += 1
            self.plan_and_execute(pan, tilt, sequence)

        except Exception as exc:
            logger.error("Error processing camera move: %s", exc)
            self._stats["errors"] += 1

    def _on_servo_position(self, event: Event) -> None:
        try:
            data = event.data if hasattr(event, "data") else {}
            pan_angle = data.get("pan_angle", data.get("current_angle"))
            tilt_angle = data.get("tilt_angle")
            if pan_angle is not None:
                self._update_servo_position(ServoAxis.PAN, float(pan_angle))
            if tilt_angle is not None:
                self._update_servo_position(ServoAxis.TILT, float(tilt_angle))
        except Exception as exc:
            logger.debug("Error processing servo position: %s", exc)

    def _update_servo_position(self, axis: ServoAxis, angle: float) -> None:
        with self._lock:
            if axis == ServoAxis.PAN:
                self._pan_state.current_angle = angle
                self._pan_state.last_update = time.time()
            else:
                self._tilt_state.current_angle = angle
                self._tilt_state.last_update = time.time()

    def plan_and_execute(
        self,
        target_pan: float,
        target_tilt: float,
        sequence: int = 0,
    ) -> Optional[MotionPlan]:
        with self._lock:
            return self._plan_and_execute_internal(target_pan, target_tilt, sequence)

    def _plan_and_execute_internal(
        self,
        target_pan: float,
        target_tilt: float,
        sequence: int,
    ) -> Optional[MotionPlan]:
        profile = MotionProfile.BROADCAST
        timestamp = time.time()

        pan_plan = self._plan_axis_motion(
            self._pan_state.current_angle,
            target_pan,
            self._pan_limit,
        )
        tilt_plan = self._plan_axis_motion(
            self._tilt_state.current_angle,
            target_tilt,
            self._tilt_limit,
        )

        waypoints = [target_pan, target_tilt]
        durations = [max(pan_plan, tilt_plan)]

        motion_plan = MotionPlan(
            profile=profile,
            waypoints=waypoints,
            durations=durations,
            total_duration=max(pan_plan, tilt_plan),
            max_speed=self._config.max_velocity,
            max_acceleration=self._config.max_acceleration,
            timestamp=timestamp,
        )

        pan_cmd = self._build_servo_command(
            self._pan_state.current_angle,
            target_pan,
            self._pan_limit,
            timestamp,
        )
        tilt_cmd = self._build_servo_command(
            self._tilt_state.current_angle,
            target_tilt,
            self._tilt_limit,
            timestamp,
        )

        if pan_cmd is not None:
            self._publish_servo_command(ServoAxis.PAN, pan_cmd)
        if tilt_cmd is not None:
            self._publish_servo_command(ServoAxis.TILT, tilt_cmd)

        self._pan_state.target_angle = target_pan
        self._tilt_state.target_angle = target_tilt

        return motion_plan

    def _plan_axis_motion(
        self,
        current: float,
        target: float,
        limit: VelocityLimit,
    ) -> float:
        from app.services.motion.smooth import time_between_angles
        distance = abs(target - current)
        return time_between_angles(
            current, target,
            limit.max_velocity,
            limit.max_acceleration,
        )

    def _build_servo_command(
        self,
        current_angle: float,
        target_angle: float,
        limit: VelocityLimit,
        timestamp: float,
    ) -> Optional[ServoCommand]:
        safety_check = self._safety.validate_command(
            current_angle, target_angle, limit.max_velocity
        )
        if not safety_check.passed:
            logger.warning(
                "Safety check failed for angle %.1f: %s",
                target_angle, safety_check.message
            )
            self._stats["safety_violations_blocked"] += 1
            clamped = safety_check.clamped_angle
            if clamped is None:
                return None
            target_angle = clamped

        self._sequence += 1
        return ServoCommand(
            target_angle=target_angle,
            speed=limit.max_velocity,
            acceleration=limit.max_acceleration,
            timestamp=timestamp,
            sequence=self._sequence,
        )

    def _publish_servo_command(
        self,
        axis: ServoAxis,
        command: ServoCommand,
    ) -> None:
        if self._event_bus is None:
            return
        try:
            axis_key = "pan" if axis == ServoAxis.PAN else "tilt"
            self._event_bus.publish(
                EventType.SERVO_COMMAND,
                data={
                    "axis": axis_key,
                    "target_angle": command.target_angle,
                    "speed": command.speed,
                    "acceleration": command.acceleration,
                    "timestamp": command.timestamp,
                    "sequence": command.sequence,
                },
                priority=EventPriority.HIGH,
                source="motion_planner",
            )
            self._stats["servo_commands_published"] += 1
        except Exception as exc:
            logger.error("Error publishing servo command: %s", exc)
            self._stats["errors"] += 1

    def execute_homing(self) -> List[ServoCommand]:
        with self._lock:
            if self._homing:
                logger.warning("Homing already in progress")
                return []
            self._homing = True

        commands: List[ServoCommand] = []
        timestamp = time.time()

        pan_cmd = self._build_servo_command(
            self._pan_state.current_angle,
            self._config.default_pan,
            self._pan_limit,
            timestamp,
        )
        tilt_cmd = self._build_servo_command(
            self._tilt_state.current_angle,
            self._config.default_tilt,
            self._tilt_limit,
            timestamp,
        )

        if pan_cmd is not None:
            commands.append(pan_cmd)
            self._publish_servo_command(ServoAxis.PAN, pan_cmd)
        if tilt_cmd is not None:
            commands.append(tilt_cmd)
            self._publish_servo_command(ServoAxis.TILT, tilt_cmd)

        with self._lock:
            self._pan_state.target_angle = self._config.default_pan
            self._tilt_state.target_angle = self._config.default_tilt
            self._homing = False
            self._stats["homing_executions"] += 1

        return commands

    def get_current_angles(self) -> Tuple[float, float]:
        with self._lock:
            return (self._pan_state.current_angle, self._tilt_state.current_angle)

    def set_safety_layer(self, safety_layer: SafetyLayer) -> None:
        with self._lock:
            self._safety = safety_layer

    def start(self) -> None:
        with self._lock:
            self._running = True
        logger.info("MotionPlanner started")

    def stop(self) -> None:
        with self._lock:
            self._running = False
        logger.info("MotionPlanner stopped")

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def stats(self) -> Dict[str, int]:
        with self._lock:
            return dict(self._stats)

    @property
    def pan_state(self) -> ServoState:
        with self._lock:
            return self._pan_state

    @property
    def tilt_state(self) -> ServoState:
        with self._lock:
            return self._tilt_state

    def generate_motion_profile(
        self,
        start_angle: float,
        end_angle: float,
        profile: MotionProfile = MotionProfile.BROADCAST,
    ) -> MotionPlan:
        from app.services.motion.smooth import trapezoidal_velocity_profile, lerp, ease_in_out
        import math

        distance = abs(end_angle - start_angle)
        accel, cruise, decel = trapezoidal_velocity_profile(
            distance,
            self._config.max_velocity,
            self._config.max_acceleration,
        )
        total = accel + cruise + decel

        waypoint_count = max(2, int(math.ceil(total / 0.1)))

        waypoints = []
        for i in range(waypoint_count):
            t = i / (waypoint_count - 1)
            eased = ease_in_out(t)
            waypoints.append(lerp(start_angle, end_angle, eased))

        segment = total / max(1, waypoint_count - 1)
        durations = [segment] * (waypoint_count - 1)

        return MotionPlan(
            profile=profile,
            waypoints=waypoints,
            durations=durations,
            total_duration=total,
            max_speed=self._config.max_velocity,
            max_acceleration=self._config.max_acceleration,
            timestamp=time.time(),
        )

    def reset(self) -> None:
        with self._lock:
            self._pan_state = ServoState(
                current_angle=self._config.default_pan,
                target_angle=self._config.default_pan,
            )
            self._tilt_state = ServoState(
                current_angle=self._config.default_tilt,
                target_angle=self._config.default_tilt,
            )
            self._stats = {
                "camera_moves_received": 0,
                "servo_commands_published": 0,
                "safety_violations_blocked": 0,
                "homing_executions": 0,
                "errors": 0,
            }