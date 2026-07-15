"""Motion models for FieldVision AI."""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class MotionProfile(str, Enum):
    """Motion profile types."""

    BROADCAST = "broadcast"
    FAST_BREAK = "fast_break"
    SET_PIECE = "set_piece"
    GOAL_CELEBRATION = "goal_celebration"


class ServoCommand(BaseModel):
    """Command sent to servo controller."""

    target_angle: float = Field(..., ge=0.0, le=180.0, description="Target angle degrees")
    speed: float = Field(default=90.0, gt=0.0, le=120.0, description="Speed deg/s")
    acceleration: float = Field(default=200.0, gt=0.0, le=400.0, description="Acceleration deg/s^2")
    timestamp: float = Field(..., gt=0.0, description="Command timestamp")
    sequence: int = Field(default=0, ge=0, description="Command sequence number")


class ServoPosition(BaseModel):
    """Current servo position reported by ESP32."""

    current_angle: float = Field(..., ge=0.0, le=180.0, description="Current angle degrees")
    target_angle: float = Field(..., ge=0.0, le=180.0, description="Target angle degrees")
    speed: float = Field(default=0.0, ge=0.0, le=120.0, description="Current speed deg/s")
    status: str = Field(default="OK", description="Servo status")
    uptime: float = Field(default=0.0, ge=0.0, description="ESP32 uptime seconds")
    free_heap: int = Field(default=0, ge=0, description="Free heap bytes")
    timestamp: float = Field(..., gt=0.0, description="Report timestamp")


class MotionPlan(BaseModel):
    """Planned motion trajectory from motion planner."""

    profile: MotionProfile = Field(..., description="Motion profile used")
    waypoints: List[float] = Field(..., min_length=1, description="Angle waypoints degrees")
    durations: List[float] = Field(
        ..., min_length=1, description="Duration for each segment seconds"
    )
    total_duration: float = Field(..., gt=0.0, description="Total motion duration seconds")
    max_speed: float = Field(..., gt=0.0, le=120.0, description="Max speed deg/s")
    max_acceleration: float = Field(..., gt=0.0, le=400.0, description="Max acceleration deg/s^2")
    timestamp: float = Field(..., gt=0.0, description="Plan timestamp")

    @property
    def waypoint_count(self) -> int:
        """Number of waypoints."""
        return len(self.waypoints)
