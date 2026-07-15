"""Camera state model for FieldVision AI output abstraction."""
from __future__ import annotations

import time
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.motion import MotionProfile


class OutputMode(str, Enum):
    """Output rendering mode."""
    VIRTUAL = "virtual"
    SERVO = "servo"
    HYBRID = "hybrid"
    PTZ = "ptz"


class CameraState(BaseModel):
    """Abstract camera state output from the AI Director.

    Represents desired framing as normalized coordinates — no hardware knowledge.
    Renderers (VirtualCamera, Servo, PTZ) translate this to device-specific commands.
    """

    center_x: float = Field(..., ge=0.0, le=1.0, description="Target center X (0=left, 1=right)")
    center_y: float = Field(..., ge=0.0, le=1.0, description="Target center Y (0=top, 1=bottom)")
    zoom: float = Field(..., ge=1.0, le=4.0, description="Zoom level (1.0=wide, 4.0=close)")
    motion_profile: MotionProfile = Field(..., description="Motion profile for this move")
    tracking_mode: str = Field(default="broadcast", description="Director tracking mode")
    confidence: float = Field(..., ge=0.0, le=1.0, description="AI confidence in this state")
    timestamp: float = Field(..., gt=0.0, description="State timestamp")

    @field_validator("center_x", "center_y")
    @classmethod
    def normalize_coordinates(cls, v: float) -> float:
        return round(v, 4)

    def to_dict(self) -> dict:
        return {
            "center_x": self.center_x,
            "center_y": self.center_y,
            "zoom": self.zoom,
            "motion_profile": self.motion_profile.value,
            "tracking_mode": self.tracking_mode,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_normalized(
        cls,
        center_x: float,
        center_y: float,
        zoom: float,
        confidence: float,
        motion_profile: MotionProfile = MotionProfile.BROADCAST,
        tracking_mode: str = "broadcast",
    ) -> CameraState:
        """Factory to create CameraState from normalized values."""
        return cls(
            center_x=center_x,
            center_y=center_y,
            zoom=zoom,
            motion_profile=motion_profile,
            tracking_mode=tracking_mode,
            confidence=confidence,
            timestamp=time.time(),
        )


class VirtualCameraConfig(BaseModel):
    """Configuration for virtual camera output."""
    dead_zone: float = Field(default=0.05, ge=0.0, le=0.2, description="Dead zone radius (0-1)")
    safe_margin: float = Field(default=0.1, ge=0.0, le=0.3, description="Safe margin (0-1)")
    max_velocity: float = Field(default=1.0, ge=0.1, le=5.0, description="Max velocity (normalized/s)")
    smoothing_factor: float = Field(default=0.3, ge=0.0, le=1.0, description="Smoothing 0-1")
    default_zoom: float = Field(default=1.5, ge=1.0, le=4.0, description="Default zoom level")


class ServoOutputConfig(BaseModel):
    """Configuration for servo output."""
    pan_min: float = Field(default=0.0, ge=0.0, le=180.0)
    pan_max: float = Field(default=180.0, ge=0.0, le=180.0)
    tilt_min: float = Field(default=0.0, ge=0.0, le=180.0)
    tilt_max: float = Field(default=180.0, ge=0.0, le=180.0)
    default_pan: float = Field(default=90.0, ge=0.0, le=180.0)
    default_tilt: float = Field(default=90.0, ge=0.0, le=180.0)
    max_velocity: float = Field(default=90.0, gt=0.0, le=120.0)
    max_acceleration: float = Field(default=200.0, gt=0.0, le=400.0)


class PTZOutputConfig(BaseModel):
    """Configuration for PTZ output."""
    host: str = Field(default="192.168.1.100")
    port: int = Field(default=80, ge=1, le=65535)
    username: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)


class OutputConfig(BaseModel):
    """Top-level output configuration."""
    mode: OutputMode = Field(default=OutputMode.VIRTUAL, description="Active output mode")
    virtual_camera: VirtualCameraConfig = Field(default_factory=VirtualCameraConfig)
    servo: ServoOutputConfig = Field(default_factory=ServoOutputConfig)
    ptz: PTZOutputConfig = Field(default_factory=PTZOutputConfig)
