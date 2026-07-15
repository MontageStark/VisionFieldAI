"""ESP32 WebSocket client for camera control."""
from __future__ import annotations

import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    import websockets
except ImportError:
    websockets = None

from app.services.communication.protocol import (
    CommandType,
    ESP32Command,
    PositionFeedback,
    TransitionType,
    parse_response,
    serialize_command,
)

logger = logging.getLogger(__name__)


class ConnectionState(str, Enum):
    """WebSocket connection state."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"


class ESP32ClientError(Exception):
    """ESP32 client error."""

    pass


@dataclass
class ESP32ClientConfig:
    """Configuration for ESP32 client."""

    esp32_url: str = "ws://192.168.1.100:8080"
    heartbeat_interval: float = 5.0
    reconnect_delay: float = 1.0
    max_reconnect_delay: float = 60.0
    connection_timeout: float = 10.0


@dataclass
class ESP32Client:
    """WebSocket client for communicating with ESP32.

    Features:
    - WebSocket connection management
    - JSON command sending (pan/tilt/zoom/transition)
    - Position feedback parsing
    - Heartbeat/keepalive mechanism
    - Auto-reconnect with exponential backoff
    - Connection state management
    - Error handling and logging
    """

    esp32_url: str = field(default="ws://192.168.1.100:8080")
    config: Optional[ESP32ClientConfig] = None
    event_bus: Any = field(default=None, repr=False)

    _ws: Any = field(default=None, init=False, repr=False)
    _state: ConnectionState = field(default=ConnectionState.DISCONNECTED, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)
    _heartbeat_task: Optional[asyncio.Task[None]] = field(default=None, init=False, repr=False)
    _receive_task: Optional[asyncio.Task[None]] = field(default=None, init=False, repr=False)
    _running: bool = field(default=False, init=False)
    _sequence: int = field(default=0, init=False)
    _last_position: Optional[PositionFeedback] = field(default=None, init=False)
    _current_reconnect_delay: float = field(default=1.0, init=False)
    _reconnect_attempts: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if self.config is not None:
            self.esp32_url = self.config.esp32_url
        if websockets is None:
            raise ImportError("websockets library required: pip install websockets")

    @property
    def state(self) -> ConnectionState:
        """Get current connection state."""
        return self._state

    async def connect(self) -> None:
        """Establish WebSocket connection to ESP32."""
        async with self._lock:
            if self._state == ConnectionState.CONNECTED:
                return

            self._state = ConnectionState.CONNECTING
            logger.info("Connecting to ESP32 at %s", self.esp32_url)

            try:
                self._ws = await asyncio.wait_for(
                    websockets.connect(
                        self.esp32_url,
                        ping_interval=None,
                        open_timeout=self.config.connection_timeout if self.config else 10.0,
                    ),
                    timeout=self.config.connection_timeout if self.config else 10.0,
                )
                self._state = ConnectionState.CONNECTED
                self._running = True
                self._current_reconnect_delay = (
                    self.config.reconnect_delay if self.config else 1.0
                )
                self._reconnect_attempts = 0
                logger.info("Connected to ESP32")

                self._receive_task = asyncio.create_task(self._receive_loop())
                self._start_heartbeat()

            except Exception as exc:
                logger.error("Failed to connect to ESP32: %s", exc)
                self._state = ConnectionState.DISCONNECTED
                self._ws = None
                raise ESP32ClientError(f"Connection failed: {exc}") from exc

    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        async with self._lock:
            self._running = False
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                try:
                    await self._heartbeat_task
                except asyncio.CancelledError:
                    pass
                self._heartbeat_task = None

            if self._receive_task:
                self._receive_task.cancel()
                try:
                    await self._receive_task
                except asyncio.CancelledError:
                    pass
                self._receive_task = None

            if self._ws:
                try:
                    await self._ws.close()
                except Exception:
                    pass
                self._ws = None

            self._state = ConnectionState.DISCONNECTED
            logger.info("Disconnected from ESP32")

    async def send_command(
        self,
        command_type: CommandType,
        pan: Optional[float] = None,
        tilt: Optional[float] = None,
        zoom: Optional[float] = None,
        transition: Optional[TransitionType] = None,
        duration: Optional[float] = None,
    ) -> None:
        """Send a command to ESP32.

        Args:
            command_type: Type of command
            pan: Pan angle (for PAN, PAN_TILT)
            tilt: Tilt angle (for TILT, PAN_TILT)
            zoom: Zoom level (for ZOOM)
            transition: Transition type (for PAN_TILT)
            duration: Transition duration (for PAN_TILT)

        Raises:
            ESP32ClientError: If not connected or send fails
        """
        if self._state != ConnectionState.CONNECTED or self._ws is None:
            raise ESP32ClientError("Not connected to ESP32")

        cmd = ESP32Command(
            command_type=command_type,
            pan=pan,
            tilt=tilt,
            zoom=zoom,
            transition=transition,
            duration=duration,
        )

        self._sequence += 1
        cmd.command_id = f"seq_{self._sequence}"

        try:
            data = serialize_command(cmd)
            await self._ws.send(data)
            logger.debug("Sent command: %s", data)
        except Exception as exc:
            logger.error("Failed to send command: %s", exc)
            raise ESP32ClientError(f"Send failed: {exc}") from exc

    def _start_heartbeat(self) -> None:
        """Start heartbeat task."""
        interval = (
            self.config.heartbeat_interval if self.config else 5.0
        )
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop(interval))

    async def _heartbeat_loop(self, interval: float) -> None:
        """Send periodic heartbeat to keep connection alive.

        Args:
            interval: Seconds between heartbeats
        """
        while self._running and self._state == ConnectionState.CONNECTED:
            try:
                await asyncio.sleep(interval)
                if self._ws and self._running:
                    await self._ws.send(json.dumps({"type": "heartbeat"}))
                    logger.debug("Heartbeat sent")
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning("Heartbeat failed: %s", exc)
                break

    async def _receive_loop(self) -> None:
        """Receive and process messages from ESP32."""
        while self._running and self._ws:
            try:
                message = await self._ws.recv()
                await self._handle_message(message)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                if self._running:
                    logger.warning("Receive error: %s", exc)
                    await self._handle_disconnect()
                break

    async def _handle_message(self, message: str) -> None:
        """Process incoming message.

        Args:
            message: Raw JSON message string
        """
        try:
            data = json.loads(message)
            msg_type = data.get("type", "")

            if msg_type == "position":
                feedback = parse_response(data)
                if isinstance(feedback, PositionFeedback):
                    self._last_position = feedback
                    logger.debug(
                        "Position update: pan=%.1f tilt=%.1f zoom=%.1f",
                        feedback.pan,
                        feedback.tilt,
                        feedback.zoom,
                    )
            elif msg_type == "error":
                logger.error("ESP32 error: %s", data.get("message", "Unknown"))

        except json.JSONDecodeError:
            logger.warning("Invalid JSON received: %s", message)
        except Exception as exc:
            logger.error("Error handling message: %s", exc)

    async def _handle_disconnect(self) -> None:
        """Handle unexpected disconnection with reconnect."""
        if not self._running:
            return

        self._state = ConnectionState.RECONNECTING
        delay = self._current_reconnect_delay

        while self._running and self._state == ConnectionState.RECONNECTING:
            logger.info(
                "Reconnecting in %.1f seconds (attempt %d)",
                delay,
                self._reconnect_attempts + 1,
            )
            await asyncio.sleep(delay)

            if not self._running:
                break

            try:
                self._ws = await websockets.connect(
                    self.esp32_url,
                    ping_interval=None,
                )
                self._state = ConnectionState.CONNECTED
                self._reconnect_attempts = 0
                self._current_reconnect_delay = (
                    self.config.reconnect_delay if self.config else 1.0
                )
                logger.info("Reconnected to ESP32")
                self._receive_task = asyncio.create_task(self._receive_loop())
                self._start_heartbeat()
                return

            except Exception as exc:
                logger.warning("Reconnect failed: %s", exc)
                self._reconnect_attempts += 1
                self._current_reconnect_delay = min(
                    delay * 2,
                    self.config.max_reconnect_delay if self.config else 60.0,
                )

        self._state = ConnectionState.DISCONNECTED

    async def get_position(self, timeout: float = 0.5) -> Optional[PositionFeedback]:
        """Get current position with optional timeout.

        Args:
            timeout: Maximum seconds to wait for position

        Returns:
            PositionFeedback or None if timeout
        """
        feedback = self._last_position
        if feedback is None and self._state == ConnectionState.CONNECTED:
            await asyncio.sleep(timeout)
            feedback = self._last_position
        return feedback

    @property
    def is_connected(self) -> bool:
        """Check if connected to ESP32."""
        return self._state == ConnectionState.CONNECTED

    @asynccontextmanager
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        try:
            yield self
        finally:
            await self.disconnect()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()


async def get_esp32_client(
    url: str = "ws://192.168.1.100:8080",
    config: Optional[ESP32ClientConfig] = None,
) -> ESP32Client:
    """Factory function to create and connect ESP32 client.

    Args:
        url: WebSocket URL for ESP32
        config: Optional client configuration

    Returns:
        Connected ESP32Client instance
    """
    if config is None:
        config = ESP32ClientConfig(esp32_url=url)
    client = ESP32Client(config=config)
    await client.connect()
    return client