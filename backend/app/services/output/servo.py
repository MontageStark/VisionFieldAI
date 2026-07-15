"""Servo output plugin — translates CameraState to servo angles."""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Optional

from app.models.camera_state import CameraState, ServoOutputConfig
from app.models.motion import MotionProfile, MotionPlan
from app.services.output.base import OutputPlugin
from app.services.motion.safety import SafetyLayer, ServoAxis, AxisLimits
from app.services.motion.smooth import trapezoidal_velocity_profile, lerp, ease_in_out

logger = logging.getLogger(__name__)


@dataclass
class ServoAxisState:
    current: float = 90.0
    target: float = 90.0


class ServoMotionPlanner:
    """Internal motion planner for servo output.

    Generates smooth waypoint trajectories between servo positions,
    respecting velocity and acceleration limits.
    """

    def __init__(self, config: ServoOutputConfig) -> None:
        self._config = config
        self._safety = SafetyLayer(
            pan_limits=AxisLimits(
                min_angle=config.pan_min,
                max_angle=config.pan_max,
                max_jump=15.0,
            ),
            tilt_limits=AxisLimits(
                min_angle=config.tilt_min,
                max_angle=config.tilt_max,
                max_jump=15.0,
            ),
        )
        self._pan = ServoAxisState(current=config.default_pan, target=config.default_pan)
        self._tilt = ServoAxisState(current=config.default_tilt, target=config.default_tilt)

    def plan(self, pan_angle: float, tilt_angle: float) -> Optional[MotionPlan]:
        """Plan motion from current position to target pan/tilt."""
        # Safety check pan
        pan_jump = self._safety.validate_jump(
            ServoAxis.PAN, self._pan.current, pan_angle
        )
        if not pan_jump.passed and pan_jump.clamped_angle is None:
            return None
        clamped_pan = pan_jump.clamped_angle if not pan_jump.passed else pan_angle

        # Safety check tilt
        tilt_jump = self._safety.validate_jump(
            ServoAxis.TILT, self._tilt.current, tilt_angle
        )
        if not tilt_jump.passed and tilt_jump.clamped_angle is None:
            return None
        clamped_tilt = tilt_jump.clamped_angle if not tilt_jump.passed else tilt_angle

        # Compute motion profile
        pan_dist = abs(clamped_pan - self._pan.current)
        tilt_dist = abs(clamped_tilt - self._tilt.current)
        total_dist = max(pan_dist, tilt_dist)

        if total_dist < 1e-6:
            return None

        accel, cruise, decel = trapezoidal_velocity_profile(
            total_dist, self._config.max_velocity, self._config.max_acceleration
        )
        total_duration = accel + cruise + decel

        # Generate waypoints
        waypoint_count = max(2, int(total_duration / 0.1))
        waypoints = []
        for i in range(waypoint_count):
            t = i / (waypoint_count - 1)
            eased = ease_in_out(t)
            waypoints.append(lerp(self._pan.current, clamped_pan, eased))

        segment = total_duration / max(1, waypoint_count - 1)
        durations = [segment] * (waypoint_count - 1)

        self._pan.target = clamped_pan
        self._tilt.target = clamped_tilt

        return MotionPlan(
            profile=MotionProfile.BROADCAST,
            waypoints=waypoints,
            durations=durations,
            total_duration=total_duration,
            max_speed=self._config.max_velocity,
            max_acceleration=self._config.max_acceleration,
            timestamp=time.time(),
        )

    @property
    def current_pan(self) -> float:
        return self._pan.current

    @property
    def current_tilt(self) -> float:
        return self._tilt.current


class ServoOutput(OutputPlugin):
    """Servo output — translates CameraState to pan/tilt angles for ESP32."""

    def __init__(self, config: Optional[ServoOutputConfig] = None) -> None:
        self._config = config or ServoOutputConfig()
        self._current_state: Optional[CameraState] = None
        self._motion_planner = ServoMotionPlanner(self._config)
        self._pan_angle = self._config.default_pan
        self._tilt_angle = self._config.default_tilt
        self._zoom = 1.0
        self._motion_plan: Optional[MotionPlan] = None
        self._lock = threading.Lock()

    @property
    def name(self) -> str:
        return "servo"

    def apply(self, state: CameraState) -> None:
        with self._lock:
            self._current_state = state
            self._pan_angle = (
                self._config.pan_min
                + state.center_x * (self._config.pan_max - self._config.pan_min)
            )
            self._tilt_angle = (
                self._config.tilt_min
                + state.center_y * (self._config.tilt_max - self._config.tilt_min)
            )
            self._zoom = state.zoom
            self._motion_plan = self._motion_planner.plan(self._pan_angle, self._tilt_angle)

    def get_state(self) -> Optional[CameraState]:
        return self._current_state

    def reset(self) -> None:
        with self._lock:
            self._pan_angle = self._config.default_pan
            self._tilt_angle = self._config.default_tilt
            self._zoom = 1.0
            self._motion_plan = None
            self._current_state = None

    @property
    def pan_angle(self) -> float:
        return self._pan_angle

    @property
    def tilt_angle(self) -> float:
        return self._tilt_angle

    @property
    def motion_plan(self) -> Optional[MotionPlan]:
        return self._motion_plan
