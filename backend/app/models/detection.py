"""Detection models for FieldVision AI."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class BoundingBox(BaseModel):
    """Normalized bounding box for object detection."""

    x1: float = Field(..., ge=0.0, le=1.0, description="Top-left x (0-1 normalized)")
    y1: float = Field(..., ge=0.0, le=1.0, description="Top-left y (0-1 normalized)")
    x2: float = Field(..., ge=0.0, le=1.0, description="Bottom-right x (0-1 normalized)")
    y2: float = Field(..., ge=0.0, le=1.0, description="Bottom-right y (0-1 normalized)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence 0-1")

    @field_validator("x2")
    @classmethod
    def x2_must_be_greater_than_x1(cls, v: float, info) -> float:
        if "x1" in info.data and v < info.data["x1"]:
            raise ValueError("x2 must be greater than or equal to x1")
        return v

    @field_validator("y2")
    @classmethod
    def y2_must_be_greater_than_y1(cls, v: float, info) -> float:
        if "y1" in info.data and v < info.data["y1"]:
            raise ValueError("y2 must be greater than or equal to y1")
        return v

    @property
    def width(self) -> float:
        """Width of bounding box."""
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        """Height of bounding box."""
        return self.y2 - self.y1

    @property
    def center_x(self) -> float:
        """Center x coordinate."""
        return (self.x1 + self.x2) / 2.0

    @property
    def center_y(self) -> float:
        """Center y coordinate."""
        return (self.y1 + self.y2) / 2.0

    @property
    def area(self) -> float:
        """Area of bounding box."""
        return self.width * self.height


class Detection(BaseModel):
    """Single object detection from vision service."""

    label: str = Field(
        ..., min_length=1, description="Object label: ball, player, goalkeeper, referee"
    )
    bbox: BoundingBox = Field(..., description="Bounding box")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    timestamp: float = Field(..., gt=0.0, description="Detection timestamp")
    frame_number: int = Field(..., gt=0, description="Frame number")

    @field_validator("label")
    @classmethod
    def validate_label(cls, v: str) -> str:
        valid_labels = {"ball", "player", "goalkeeper", "referee"}
        if v not in valid_labels:
            raise ValueError(f"label must be one of {valid_labels}")
        return v


class DetectionResult(BaseModel):
    """Collection of detections for a single frame."""

    frame_number: int = Field(..., gt=0, description="Frame number")
    timestamp: float = Field(..., gt=0.0, description="Frame timestamp")
    detections: List[Detection] = Field(default_factory=list, description="List of detections")
    inference_time_ms: float = Field(
        default=0.0, ge=0.0, description="Vision inference time in ms"
    )
    frame_width: int = Field(default=1920, gt=0, description="Frame width in pixels")
    frame_height: int = Field(default=1080, gt=0, description="Frame height in pixels")

    @property
    def detection_count(self) -> int:
        """Number of detections in this frame."""
        return len(self.detections)

    @property
    def ball_detection(self) -> Optional[Detection]:
        """Get ball detection if present."""
        for det in self.detections:
            if det.label == "ball":
                return det
        return None

    @property
    def player_detections(self) -> List[Detection]:
        """Get all player detections."""
        return [det for det in self.detections if det.label == "player"]
