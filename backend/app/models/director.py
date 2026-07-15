"""Director models for FieldVision AI."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.camera_state import CameraState


class DirectorMode(str, Enum):
    """Director operating modes."""

    BROADCAST = "broadcast"
    AGGRESSIVE = "aggressive"
    WIDE = "wide"
    TRAINING = "training"
    MANUAL_ASSIST = "manual_assist"


class DirectorDecision(BaseModel):
    """Decision output from the Director service."""

    mode: DirectorMode = Field(..., description="Director mode used")
    target: CameraState = Field(..., description="Target camera state")
    reasoning: str = Field(..., min_length=1, description="Decision reasoning")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Decision confidence")
    timestamp: float = Field(..., gt=0.0, description="Decision timestamp")
    tracking_track_id: Optional[int] = Field(
        default=None, ge=0, description="Track ID being followed"
    )

    @field_validator("reasoning")
    @classmethod
    def validate_reasoning_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("reasoning must not be empty")
        return v.strip()
