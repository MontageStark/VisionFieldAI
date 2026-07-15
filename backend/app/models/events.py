"""Event models for FieldVision AI."""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Event types for the FieldVision AI system."""

    # System events
    STATE_CHANGED = "state.changed"
    ERROR_OCCURRED = "error.occurred"
    HEALTH_CHECK = "health.check"

    # Camera events
    FRAME_CAPTURED = "camera.frame_captured"
    CAMERA_CONNECTED = "camera.connected"
    CAMERA_DISCONNECTED = "camera.disconnected"

    # Vision events
    DETECTIONS_COMPLETE = "vision.detections_complete"
    TRACKING_UPDATED = "tracking.updated"

    # Director events
    DIRECTOR_DECISION = "director.decision"
    CAMERA_MOVE = "director.camera_move"

    # Servo events
    SERVO_COMMAND = "servo.command"
    SERVO_POSITION = "servo.position"
    SERVO_ERROR = "servo.error"

    # Streaming events
    STREAM_STARTED = "stream.started"
    STREAM_STOPPED = "stream.stopped"
    STREAM_ERROR = "stream.error"

    # Safety events
    SAFETY_VIOLATION = "safety.violation"
    EMERGENCY_STOP = "safety.emergency_stop"


class EventPriority(int, Enum):
    """Event priority levels."""

    NORMAL = 0
    HIGH = 1
    CRITICAL = 2


class Event(BaseModel):
    """Event published to the event bus."""

    event_type: EventType = Field(..., description="Event type")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event payload")
    priority: EventPriority = Field(default=EventPriority.NORMAL, description="Priority level")
    timestamp: float = Field(..., gt=0.0, description="Event timestamp")
    source: Optional[str] = Field(default=None, description="Source component")
