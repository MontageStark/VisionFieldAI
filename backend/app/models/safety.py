"""Safety models for FieldVision AI."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SafetyViolationType(str, Enum):
    """Types of safety violations."""

    ANGLE_EXCEEDED = "angle_exceeded"
    JUMP_LIMIT = "jump_limit"
    SPEED_LIMIT = "speed_limit"
    DISCONNECT = "disconnect"
    WATCHDOG = "watchdog"
    EMERGENCY_BUTTON = "emergency_button"
    OVERCURRENT = "overcurrent"
    OVERTEMPERATURE = "overtemperature"


class SafetySeverity(str, Enum):
    """Safety event severity levels."""

    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SafetyCheck(BaseModel):
    """Result of a safety validation check."""

    passed: bool = Field(..., description="Whether check passed")
    violation_type: Optional[SafetyViolationType] = Field(
        default=None, description="Violation type if failed"
    )
    severity: SafetySeverity = Field(default=SafetySeverity.WARNING, description="Severity")
    message: str = Field(default="", description="Check result message")
    original_angle: Optional[float] = Field(
        default=None, description="Original commanded angle"
    )
    clamped_angle: Optional[float] = Field(
        default=None, description="Angle after clamping"
    )


class SafetyViolation(BaseModel):
    """Record of a safety violation event."""

    violation_type: SafetyViolationType = Field(..., description="Violation type")
    severity: SafetySeverity = Field(..., description="Severity level")
    message: str = Field(..., min_length=1, description="Violation description")
    timestamp: float = Field(..., gt=0.0, description="Violation timestamp")
    source: str = Field(default="safety_layer", description="Source component")
    action_taken: str = Field(..., description="Action taken in response")


class EmergencyStop(BaseModel):
    """Emergency stop event."""

    reason: str = Field(..., min_length=1, description="Stop reason")
    timestamp: float = Field(..., gt=0.0, description="Stop timestamp")
    source: str = Field(default="emergency_button", description="Trigger source")
    servo_locked: bool = Field(default=True, description="Whether servo is locked")
    requires_manual_reset: bool = Field(
        default=True, description="Requires manual reset to resume"
    )
