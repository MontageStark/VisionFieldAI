"""ESP32 communication protocol - command and response types."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Union


class CommandType(str, Enum):
    """ESP32 command types."""

    PAN = "pan"
    TILT = "tilt"
    PAN_TILT = "pan_tilt"
    ZOOM = "zoom"
    STATUS = "status"
    HEARTBEAT = "heartbeat"
    HOME = "home"
    UNKNOWN = "unknown"


class TransitionType(str, Enum):
    """Motion transition types."""

    INSTANT = "instant"
    SMOOTH = "smooth"
    LINEAR = "linear"


@dataclass
class ESP32Command:
    """Represents a command to send to the ESP32."""

    command_type: CommandType
    pan: Optional[float] = None
    tilt: Optional[float] = None
    zoom: Optional[float] = None
    transition: Optional[TransitionType] = None
    duration: Optional[float] = None
    command_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.command_id is None:
            self.command_id = f"cmd_{id(self)}"


@dataclass
class ESP32Response:
    """Generic ESP32 response."""

    success: bool = True
    command_id: Optional[str] = None
    error_code: Optional[int] = None
    error_message: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class PositionFeedback:
    """Position feedback from ESP32."""

    pan: float
    tilt: float
    zoom: float = 1.0
    timestamp: float = 0.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PositionFeedback:
        return cls(
            pan=float(data.get("pan", 0.0)),
            tilt=float(data.get("tilt", 0.0)),
            zoom=float(data.get("zoom", 1.0)),
            timestamp=float(data.get("timestamp", 0.0)),
        )


def serialize_command(cmd: ESP32Command) -> str:
    """Serialize an ESP32Command to JSON string.

    Args:
        cmd: Command to serialize

    Returns:
        JSON string representation

    Raises:
        ValueError: If command type is unknown
    """
    data: Dict[str, Any] = {"command_id": cmd.command_id}

    if cmd.command_type == CommandType.PAN:
        if cmd.pan is None:
            raise ValueError("PAN command requires pan value")
        data["type"] = "pan"
        data["pan"] = cmd.pan
    elif cmd.command_type == CommandType.TILT:
        if cmd.tilt is None:
            raise ValueError("TILT command requires tilt value")
        data["type"] = "tilt"
        data["tilt"] = cmd.tilt
    elif cmd.command_type == CommandType.PAN_TILT:
        if cmd.pan is None or cmd.tilt is None:
            raise ValueError("PAN_TILT command requires pan and tilt values")
        data["type"] = "pan_tilt"
        data["pan"] = cmd.pan
        data["tilt"] = cmd.tilt
        if cmd.transition is not None:
            data["transition"] = cmd.transition.value
        if cmd.duration is not None:
            data["duration"] = cmd.duration
    elif cmd.command_type == CommandType.ZOOM:
        if cmd.zoom is None:
            raise ValueError("ZOOM command requires zoom value")
        data["type"] = "zoom"
        data["zoom"] = cmd.zoom
    elif cmd.command_type == CommandType.STATUS:
        data["type"] = "status"
    elif cmd.command_type == CommandType.HEARTBEAT:
        data["type"] = "heartbeat"
    elif cmd.command_type == CommandType.HOME:
        data["type"] = "home"
    elif cmd.command_type == CommandType.UNKNOWN:
        raise ValueError("Cannot serialize UNKNOWN command type")
    else:
        raise ValueError(f"Unknown command type: {cmd.command_type}")

    return json.dumps(data)


def parse_response(data: Dict[str, Any]) -> Union[PositionFeedback, ESP32Response]:
    """Parse a response from ESP32.

    Args:
        data: Parsed JSON dictionary from ESP32

    Returns:
        PositionFeedback if type is 'position', ESP32Response otherwise
    """
    msg_type = data.get("type", "")

    if msg_type == "position":
        return PositionFeedback.from_dict(data)

    response = ESP32Response()
    response.raw_data = data

    if msg_type == "ack":
        response.success = True
        response.command_id = data.get("command_id")
    elif msg_type == "error":
        response.success = False
        response.error_message = data.get("message", "Unknown error")
        response.error_code = data.get("code")
    elif msg_type == "heartbeat":
        response.success = True
    else:
        response.success = True

    return response