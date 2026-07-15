"""Tests for ESP32 WebSocket communication service."""
from __future__ import annotations

import json
import threading
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock

import pytest

from app.services.communication.protocol import (
    CommandType,
    ESP32Command,
    ESP32Response,
    PositionFeedback,
    TransitionType,
    parse_response,
    serialize_command,
)
from app.services.communication.esp32_client import (
    ConnectionState,
    ESP32Client,
    ESP32ClientConfig,
    ESP32ClientError,
)


# ---------------------------------------------------------------------------
# Protocol tests
# ---------------------------------------------------------------------------


class TestCommandSerialization:
    def test_serialize_pan_command(self) -> None:
        cmd = ESP32Command(command_type=CommandType.PAN, pan=45.0)
        data = serialize_command(cmd)
        parsed = json.loads(data)
        assert parsed["type"] == "pan"
        assert parsed["pan"] == 45.0

    def test_serialize_tilt_command(self) -> None:
        cmd = ESP32Command(command_type=CommandType.TILT, tilt=90.0)
        data = serialize_command(cmd)
        parsed = json.loads(data)
        assert parsed["type"] == "tilt"
        assert parsed["tilt"] == 90.0

    def test_serialize_combined_command(self) -> None:
        cmd = ESP32Command(
            command_type=CommandType.PAN_TILT,
            pan=45.0,
            tilt=90.0,
            transition=TransitionType.SMOOTH,
            duration=1.5,
        )
        data = serialize_command(cmd)
        parsed = json.loads(data)
        assert parsed["type"] == "pan_tilt"
        assert parsed["pan"] == 45.0
        assert parsed["tilt"] == 90.0
        assert parsed["transition"] == "smooth"
        assert parsed["duration"] == 1.5

    def test_serialize_zoom_command(self) -> None:
        cmd = ESP32Command(command_type=CommandType.ZOOM, zoom=2.0)
        data = serialize_command(cmd)
        parsed = json.loads(data)
        assert parsed["type"] == "zoom"
        assert parsed["zoom"] == 2.0

    def test_serialize_status_command(self) -> None:
        cmd = ESP32Command(command_type=CommandType.STATUS)
        data = serialize_command(cmd)
        parsed = json.loads(data)
        assert parsed["type"] == "status"

    def test_serialize_home_command(self) -> None:
        cmd = ESP32Command(command_type=CommandType.HOME)
        data = serialize_command(cmd)
        parsed = json.loads(data)
        assert parsed["type"] == "home"

    def test_serialize_unknown_command_type_raises(self) -> None:
        cmd = ESP32Command(command_type=CommandType.UNKNOWN)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            serialize_command(cmd)

    def test_serialize_pan_requires_value(self) -> None:
        cmd = ESP32Command(command_type=CommandType.PAN)
        with pytest.raises(ValueError):
            serialize_command(cmd)


class TestResponseParsing:
    def test_parse_position_feedback(self) -> None:
        data = {
            "type": "position",
            "pan": 45.5,
            "tilt": 90.0,
            "zoom": 1.0,
            "timestamp": 1234567890.123,
        }
        response = parse_response(data)
        assert isinstance(response, PositionFeedback)
        assert response.pan == 45.5
        assert response.tilt == 90.0
        assert response.zoom == 1.0

    def test_parse_acknowledgement(self) -> None:
        data = {"type": "ack", "command_id": "cmd_001", "status": "ok"}
        response = parse_response(data)
        assert isinstance(response, ESP32Response)
        assert response.success is True
        assert response.command_id == "cmd_001"

    def test_parse_error_response(self) -> None:
        data = {"type": "error", "message": "Invalid pan angle", "code": -32001}
        response = parse_response(data)
        assert isinstance(response, ESP32Response)
        assert response.success is False
        assert response.error_message == "Invalid pan angle"

    def test_parse_heartbeat_response(self) -> None:
        data = {"type": "heartbeat", "interval_ms": 5000}
        response = parse_response(data)
        assert response is not None
        assert response.success is True

    def test_parse_unknown_type_returns_generic(self) -> None:
        data = {"type": "custom", "foo": "bar"}
        response = parse_response(data)
        assert isinstance(response, ESP32Response)


# ---------------------------------------------------------------------------
# ESP32ClientConfig tests
# ---------------------------------------------------------------------------


class TestESP32ClientConfig:
    def test_default_config_values(self) -> None:
        config = ESP32ClientConfig()
        assert config.esp32_url == "ws://192.168.1.100:8080"
        assert config.heartbeat_interval == 5.0
        assert config.reconnect_delay == 1.0
        assert config.max_reconnect_delay == 60.0
        assert config.connection_timeout == 10.0

    def test_custom_config_values(self) -> None:
        config = ESP32ClientConfig(
            esp32_url="ws://custom:9999",
            heartbeat_interval=10.0,
            reconnect_delay=2.0,
        )
        assert config.esp32_url == "ws://custom:9999"
        assert config.heartbeat_interval == 10.0
        assert config.reconnect_delay == 2.0


# ---------------------------------------------------------------------------
# ConnectionState tests
# ---------------------------------------------------------------------------


class TestConnectionState:
    def test_connection_state_values(self) -> None:
        assert ConnectionState.DISCONNECTED.value == "disconnected"
        assert ConnectionState.CONNECTING.value == "connecting"
        assert ConnectionState.CONNECTED.value == "connected"
        assert ConnectionState.RECONNECTING.value == "reconnecting"


# ---------------------------------------------------------------------------
# ESP32Client lifecycle
# ---------------------------------------------------------------------------


class TestESP32ClientInit:
    def test_init_with_defaults(self) -> None:
        client = ESP32Client()
        assert client.state == ConnectionState.DISCONNECTED
        assert client.esp32_url == "ws://192.168.1.100:8080"

    def test_init_with_custom_url(self) -> None:
        client = ESP32Client(esp32_url="ws://test:1234")
        assert client.esp32_url == "ws://test:1234"

    def test_init_with_config_object(self) -> None:
        config = ESP32ClientConfig(esp32_url="ws://config:5555")
        client = ESP32Client(config=config)
        assert client.esp32_url == "ws://config:5555"

    def test_init_with_different_url_than_default(self) -> None:
        client = ESP32Client(esp32_url="ws://esp32:9000")
        assert client.esp32_url == "ws://esp32:9000"
        assert client.state == ConnectionState.DISCONNECTED

    def test_is_connected_false_initially(self) -> None:
        client = ESP32Client()
        assert client.is_connected is False


# ---------------------------------------------------------------------------
# Command serialization via client
# ---------------------------------------------------------------------------


class TestESP32ClientCommandBuilding:
    def test_command_type_values(self) -> None:
        assert CommandType.PAN.value == "pan"
        assert CommandType.TILT.value == "tilt"
        assert CommandType.PAN_TILT.value == "pan_tilt"
        assert CommandType.ZOOM.value == "zoom"
        assert CommandType.STATUS.value == "status"

    def test_transition_type_values(self) -> None:
        assert TransitionType.INSTANT.value == "instant"
        assert TransitionType.SMOOTH.value == "smooth"
        assert TransitionType.LINEAR.value == "linear"

    def test_esp32_command_with_all_params(self) -> None:
        cmd = ESP32Command(
            command_type=CommandType.PAN_TILT,
            pan=45.0,
            tilt=90.0,
            transition=TransitionType.SMOOTH,
            duration=2.0,
            command_id="test_123",
        )
        assert cmd.pan == 45.0
        assert cmd.tilt == 90.0
        assert cmd.transition == TransitionType.SMOOTH
        assert cmd.duration == 2.0
        assert cmd.command_id == "test_123"


# ---------------------------------------------------------------------------
# PositionFeedback tests
# ---------------------------------------------------------------------------


class TestPositionFeedback:
    def test_from_dict(self) -> None:
        data = {
            "pan": 45.5,
            "tilt": 90.0,
            "zoom": 2.0,
            "timestamp": 1234567890.0,
        }
        feedback = PositionFeedback.from_dict(data)
        assert feedback.pan == 45.5
        assert feedback.tilt == 90.0
        assert feedback.zoom == 2.0
        assert feedback.timestamp == 1234567890.0

    def test_from_dict_with_defaults(self) -> None:
        data = {"pan": 0.0, "tilt": 0.0}
        feedback = PositionFeedback.from_dict(data)
        assert feedback.pan == 0.0
        assert feedback.tilt == 0.0
        assert feedback.zoom == 1.0
        assert feedback.timestamp == 0.0


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestESP32ClientErrorHandling:
    def test_client_error_is_exception(self) -> None:
        error = ESP32ClientError("test error")
        assert isinstance(error, Exception)
        assert str(error) == "test error"

    def test_error_message_preserved(self) -> None:
        error = ESP32ClientError("connection failed")
        assert "connection failed" in str(error)


# ---------------------------------------------------------------------------
# ESP32Response tests
# ---------------------------------------------------------------------------


class TestESP32Response:
    def test_default_response_is_success(self) -> None:
        response = ESP32Response()
        assert response.success is True

    def test_error_response_fields(self) -> None:
        response = ESP32Response(
            success=False,
            error_code=-32001,
            error_message="Invalid parameter",
        )
        assert response.success is False
        assert response.error_code == -32001
        assert response.error_message == "Invalid parameter"


# ---------------------------------------------------------------------------
# State transitions
# ---------------------------------------------------------------------------


class TestConnectionStateTransitions:
    def test_state_is_enum(self) -> None:
        assert isinstance(ConnectionState.DISCONNECTED, ConnectionState)
        assert isinstance(ConnectionState.CONNECTED, ConnectionState)

    def test_state_string_values(self) -> None:
        assert str(ConnectionState.DISCONNECTED) == "ConnectionState.DISCONNECTED"
        assert ConnectionState.DISCONNECTED.value == "disconnected"