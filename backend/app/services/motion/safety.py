"""Safety layer for motion control with watchdog, disconnect detection, and emergency stop."""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.core.events import EventPriority, Event
from app.models.events import EventType
from app.models.safety import SafetyCheck, SafetyViolationType, SafetySeverity, SafetyViolation, EmergencyStop

logger = logging.getLogger(__name__)


class ServoAxis(str, Enum):
    PAN = "pan"
    TILT = "tilt"


@dataclass
class AxisLimits:
    min_angle: float = 0.0
    max_angle: float = 180.0
    max_jump: float = 15.0


@dataclass
class ServoBounds:
    pan_min: float = 0.0
    pan_max: float = 180.0
    tilt_min: float = 0.0
    tilt_max: float = 180.0


class SafetyLayer:
    """Comprehensive safety layer for motion control.

    Features:
    - Per-axis angle validation (min/max limits)
    - Jump limiting (max angle change per command)
    - Watchdog timer (triggers emergency stop if no heartbeat)
    - Disconnect safety (stops motion if ESP32 disconnects)
    - Emergency stop handling
    - Servo position bounds checking
    - Publishes SAFETY_VIOLATION events on rule breach
    """

    def __init__(
        self,
        event_bus: Optional[Any] = None,
        watchdog_timeout: float = 2.0,
        servo_bounds: Optional[ServoBounds] = None,
        pan_limits: Optional[AxisLimits] = None,
        tilt_limits: Optional[AxisLimits] = None,
        on_emergency_stop: Optional[Callable[[str], None]] = None,
    ) -> None:
        self._event_bus = event_bus
        self._watchdog_timeout = watchdog_timeout
        self._on_emergency_stop = on_emergency_stop

        self._pan_limits = pan_limits or AxisLimits()
        self._tilt_limits = tilt_limits or AxisLimits()

        self._servo_bounds = servo_bounds or ServoBounds()

        self._connected = True
        self._emergency_stopped = False
        self._emergency_stop_reason: Optional[str] = None
        self._lock = threading.Lock()

        self._watchdog_timer: Optional[threading.Timer] = None
        self._watchdog_expired = False

        self._violation_count = 0
        self._last_violation: Optional[SafetyViolation] = None

        self._current_pan = 90.0
        self._current_tilt = 90.0

        if self._event_bus is not None:
            self._subscribe_to_events()

    def _subscribe_to_events(self) -> None:
        if self._event_bus is None:
            return
        try:
            self._event_bus.subscribe(
                EventType.SERVO_POSITION,
                self._on_servo_position,
            )
            self._event_bus.subscribe(
                EventType.CAMERA_DISCONNECTED,
                self._on_camera_disconnected,
            )
            logger.debug("SafetyLayer subscribed to events")
        except Exception as exc:
            logger.error("Failed to subscribe SafetyLayer to events: %s", exc)

    def _on_servo_position(self, event: Event) -> None:
        data = event.data if hasattr(event, "data") else {}
        pan_angle = data.get("pan_angle", data.get("current_angle"))
        tilt_angle = data.get("tilt_angle")

        with self._lock:
            if pan_angle is not None:
                self._current_pan = float(pan_angle)
            if tilt_angle is not None:
                self._current_tilt = float(tilt_angle)

        self._reset_watchdog()

    def _on_camera_disconnected(self, event: Event) -> None:
        with self._lock:
            self._connected = False
        logger.warning("ESP32 disconnected - safety layer notified")
        self._trigger_emergency_stop("ESP32 disconnect detected")

    def _reset_watchdog(self) -> None:
        with self._lock:
            self._watchdog_expired = False
            if self._watchdog_timer is not None:
                self._watchdog_timer.cancel()

            if self._watchdog_timeout > 0:
                self._watchdog_timer = threading.Timer(
                    self._watchdog_timeout,
                    self._on_watchdog_expired,
                )
                self._watchdog_timer.daemon = True
                self._watchdog_timer.start()

    def _on_watchdog_expired(self) -> None:
        with self._lock:
            if self._watchdog_expired:
                return
            self._watchdog_expired = True

        logger.error("Watchdog expired - no heartbeat from ESP32")
        self._trigger_emergency_stop("Watchdog timeout - no heartbeat")

    def _trigger_emergency_stop(self, reason: str) -> None:
        with self._lock:
            if self._emergency_stopped:
                return
            self._emergency_stopped = True
            self._emergency_stop_reason = reason

        violation = SafetyViolation(
            violation_type=SafetyViolationType.WATCHDOG,
            severity=SafetySeverity.CRITICAL,
            message=reason,
            timestamp=time.time(),
            source="safety_layer",
            action_taken="Emergency stop triggered",
        )
        self._last_violation = violation
        self._violation_count += 1

        self._publish_violation(violation)

        if self._on_emergency_stop:
            try:
                self._on_emergency_stop(reason)
            except Exception as exc:
                logger.error("Error in emergency stop callback: %s", exc)

        if self._event_bus is not None:
            self._event_bus.publish(
                EventType.EMERGENCY_STOP,
                data={
                    "reason": reason,
                    "timestamp": time.time(),
                    "source": "safety_layer",
                },
                priority=EventPriority.CRITICAL,
                source="safety_layer",
            )

        logger.critical("EMERGENCY STOP triggered: %s", reason)

    def _publish_violation(self, violation: SafetyViolation) -> None:
        if self._event_bus is None:
            return
        try:
            self._event_bus.publish(
                EventType.SAFETY_VIOLATION,
                data={
                    "violation_type": violation.violation_type.value,
                    "severity": violation.severity.value,
                    "message": violation.message,
                    "timestamp": violation.timestamp,
                    "source": violation.source,
                    "action_taken": violation.action_taken,
                },
                priority=EventPriority.HIGH,
                source="safety_layer",
            )
        except Exception as exc:
            logger.error("Failed to publish safety violation: %s", exc)

    def validate_angle(self, axis: ServoAxis, angle: float) -> SafetyCheck:
        limits = self._pan_limits if axis == ServoAxis.PAN else self._tilt_limits

        if limits.min_angle <= angle <= limits.max_angle:
            return SafetyCheck(passed=True, message=f"{axis.value} angle {angle} is within limits")

        clamped = max(limits.min_angle, min(limits.max_angle, angle))
        return SafetyCheck(
            passed=False,
            violation_type=SafetyViolationType.ANGLE_EXCEEDED,
            severity=SafetySeverity.ERROR,
            message=f"{axis.value} angle {angle} outside [{limits.min_angle}, {limits.max_angle}]",
            original_angle=angle,
            clamped_angle=clamped,
        )

    def validate_jump(self, axis: ServoAxis, current_angle: float, target_angle: float) -> SafetyCheck:
        limits = self._pan_limits if axis == ServoAxis.PAN else self._tilt_limits
        jump = abs(target_angle - current_angle)

        if jump <= limits.max_jump:
            return SafetyCheck(passed=True, message=f"{axis.value} jump {jump:.1f} deg is safe")

        clamped = current_angle + (target_angle - current_angle) / jump * limits.max_jump
        clamped = max(limits.min_angle, min(limits.max_angle, clamped))

        return SafetyCheck(
            passed=False,
            violation_type=SafetyViolationType.JUMP_LIMIT,
            severity=SafetySeverity.WARNING,
            message=f"{axis.value} jump {jump:.1f} deg exceeds limit {limits.max_jump} deg",
            original_angle=target_angle,
            clamped_angle=clamped,
        )

    def validate_command(
        self,
        axis: ServoAxis,
        current_angle: float,
        target_angle: float,
        speed: float,
    ) -> SafetyCheck:
        jump_check = self.validate_jump(axis, current_angle, target_angle)
        if not jump_check.passed:
            return jump_check

        angle_check = self.validate_angle(axis, target_angle)
        if not angle_check.passed:
            return angle_check

        if speed > 120.0:
            return SafetyCheck(
                passed=False,
                violation_type=SafetyViolationType.SPEED_LIMIT,
                severity=SafetySeverity.ERROR,
                message=f"{axis.value} speed {speed} exceeds 120 deg/s",
            )

        return SafetyCheck(passed=True, message=f"{axis.value} command validated")

    def validate_position_bounds(self, pan_angle: float, tilt_angle: float) -> Tuple[bool, List[SafetyCheck]]:
        checks = []
        all_passed = True

        pan_check = self.validate_angle(ServoAxis.PAN, pan_angle)
        checks.append(pan_check)
        if not pan_check.passed:
            all_passed = False

        tilt_check = self.validate_angle(ServoAxis.TILT, tilt_angle)
        checks.append(tilt_check)
        if not tilt_check.passed:
            all_passed = False

        return all_passed, checks

    def record_violation(self, violation: SafetyViolation) -> None:
        with self._lock:
            self._last_violation = violation
            self._violation_count += 1
        self._publish_violation(violation)

    def set_connected(self, connected: bool) -> None:
        with self._lock:
            was_connected = self._connected
            self._connected = connected

        if was_connected and not connected:
            logger.warning("ESP32 connection lost")
            self._trigger_emergency_stop("ESP32 disconnected")

    def is_connected(self) -> bool:
        with self._lock:
            return self._connected

    def emergency_stop(self, reason: str = "Manual emergency stop") -> None:
        self._trigger_emergency_stop(reason)

    def reset_emergency_stop(self) -> None:
        with self._lock:
            self._emergency_stopped = False
            self._emergency_stop_reason = None
            self._watchdog_expired = False
        logger.info("Safety layer emergency stop reset")

    def is_emergency_stopped(self) -> bool:
        with self._lock:
            return self._emergency_stopped

    def get_emergency_stop_reason(self) -> Optional[str]:
        with self._lock:
            return self._emergency_stop_reason

    def get_current_position(self) -> Tuple[float, float]:
        with self._lock:
            return (self._current_pan, self._current_tilt)

    def update_position(self, pan: Optional[float] = None, tilt: Optional[float] = None) -> None:
        with self._lock:
            if pan is not None:
                self._current_pan = pan
            if tilt is not None:
                self._current_tilt = tilt
        if pan is not None or tilt is not None:
            self._reset_watchdog()

    @property
    def violation_count(self) -> int:
        with self._lock:
            return self._violation_count

    @property
    def last_violation(self) -> Optional[SafetyViolation]:
        with self._lock:
            return self._last_violation

    @property
    def watchdog_expired(self) -> bool:
        with self._lock:
            return self._watchdog_expired

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "violation_count": self._violation_count,
                "emergency_stopped": self._emergency_stopped,
                "connected": self._connected,
                "watchdog_expired": self._watchdog_expired,
                "current_pan": self._current_pan,
                "current_tilt": self._current_tilt,
            }

    def set_limits(
        self,
        axis: ServoAxis,
        min_angle: Optional[float] = None,
        max_angle: Optional[float] = None,
        max_jump: Optional[float] = None,
    ) -> None:
        limits = self._pan_limits if axis == ServoAxis.PAN else self._tilt_limits
        with self._lock:
            if min_angle is not None:
                limits.min_angle = min_angle
            if max_angle is not None:
                limits.max_angle = max_angle
            if max_jump is not None:
                limits.max_jump = max_jump

    def get_limits(self, axis: ServoAxis) -> AxisLimits:
        with self._lock:
            return (
                AxisLimits(
                    min_angle=self._pan_limits.min_angle,
                    max_angle=self._pan_limits.max_angle,
                    max_jump=self._pan_limits.max_jump,
                )
                if axis == ServoAxis.PAN
                else AxisLimits(
                    min_angle=self._tilt_limits.min_angle,
                    max_angle=self._tilt_limits.max_angle,
                    max_jump=self._tilt_limits.max_jump,
                )
            )

    def __del__(self) -> None:
        if self._watchdog_timer is not None:
            self._watchdog_timer.cancel()