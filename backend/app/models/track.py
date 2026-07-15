"""Tracking models for FieldVision AI."""
from __future__ import annotations

from enum import Enum
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field, field_validator

from app.models.detection import BoundingBox


class TrackState(str, Enum):
    """Track lifecycle state."""

    TENTATIVE = "tentative"
    CONFIRMED = "confirmed"
    LOST = "lost"


class Track(BaseModel):
    """Single tracked object across frames."""

    track_id: int = Field(..., ge=0, description="Unique track identifier")
    label: str = Field(..., min_length=1, description="Object label")
    state: TrackState = Field(..., description="Track state")
    bbox: BoundingBox = Field(..., description="Current bounding box")
    age: int = Field(..., ge=0, description="Frames since first detection")
    hits: int = Field(..., ge=0, description="Total detections matched")
    time_since_update: int = Field(..., ge=0, description="Frames since last update")
    velocity: Optional[Tuple[float, float]] = Field(
        default=None, description="Velocity (vx, vy) in pixels/frame"
    )

    @field_validator("label")
    @classmethod
    def validate_label(cls, v: str) -> str:
        valid_labels = {"ball", "player", "goalkeeper", "referee"}
        if v not in valid_labels:
            raise ValueError(f"label must be one of {valid_labels}")
        return v

    @property
    def is_active(self) -> bool:
        """Track is active if confirmed and recently updated."""
        return self.state == TrackState.CONFIRMED and self.time_since_update <= 3

    @property
    def speed(self) -> Optional[float]:
        """Speed magnitude if velocity is available."""
        if self.velocity is None:
            return None
        vx, vy = self.velocity
        return (vx**2 + vy**2) ** 0.5


class TrackHistory(BaseModel):
    """Historical positions for a track."""

    track_id: int = Field(..., ge=0, description="Track identifier")
    label: str = Field(..., min_length=1, description="Object label")
    positions: List[Tuple[float, float]] = Field(
        default_factory=list, description="History of (center_x, center_y) positions"
    )
    timestamps: List[float] = Field(
        default_factory=list, description="Timestamps for each position"
    )
    bboxes: List[BoundingBox] = Field(
        default_factory=list, description="History of bounding boxes"
    )

    @field_validator("timestamps")
    @classmethod
    def validate_timestamps_sorted(cls, v: List[float]) -> List[float]:
        if v and any(v[i] > v[i + 1] for i in range(len(v) - 1)):
            raise ValueError("timestamps must be in ascending order")
        return v

    @property
    def length(self) -> int:
        """Number of recorded positions."""
        return len(self.positions)

    @property
    def last_position(self) -> Optional[Tuple[float, float]]:
        """Most recent position."""
        return self.positions[-1] if self.positions else None
