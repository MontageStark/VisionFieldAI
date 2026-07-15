"""Mock services for development."""
from __future__ import annotations

import time
from typing import Optional

from app.models.director import DirectorMode


class CameraService:
    """Mock camera service for development."""

    def __init__(self) -> None:
        self._running = False
        self._started_at: Optional[float] = None

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> dict:
        if self._running:
            return {"status": "already_running"}
        self._running = True
        self._started_at = time.time()
        return {"status": "started", "timestamp": self._started_at}

    def stop(self) -> dict:
        if not self._running:
            return {"status": "already_stopped"}
        self._running = False
        self._started_at = None
        return {"status": "stopped"}

    def status(self) -> dict:
        return {
            "running": self._running,
            "uptime": time.time() - self._started_at if self._started_at else 0.0,
        }


class ServoService:
    """Mock servo service for development."""

    def __init__(self) -> None:
        self._pan_angle = 90.0
        self._tilt_angle = 90.0
        self._emergency = False

    @property
    def is_emergency(self) -> bool:
        return self._emergency

    def status(self) -> dict:
        return {
            "pan_angle": self._pan_angle,
            "tilt_angle": self._tilt_angle,
            "emergency_stop": self._emergency,
        }

    def command(self, pan: float, tilt: float) -> dict:
        if self._emergency:
            return {"status": "emergency_active", "pan": self._pan_angle, "tilt": self._tilt_angle}
        self._pan_angle = max(0.0, min(180.0, pan))
        self._tilt_angle = max(0.0, min(180.0, tilt))
        return {"status": "ok", "pan": self._pan_angle, "tilt": self._tilt_angle}

    def home(self) -> dict:
        if self._emergency:
            return {"status": "emergency_active"}
        self._pan_angle = 90.0
        self._tilt_angle = 90.0
        return {"status": "homed", "pan": 90.0, "tilt": 90.0}

    def emergency_stop(self) -> dict:
        self._emergency = True
        return {"status": "emergency_stop_activated"}

    def reset_emergency(self) -> dict:
        self._emergency = False
        return {"status": "emergency_reset"}


class DirectorService:
    """Mock director service for development."""

    def __init__(self) -> None:
        self._mode = DirectorMode.BROADCAST
        self._last_decision: Optional[dict] = None

    def status(self) -> dict:
        return {
            "mode": self._mode.value,
            "last_decision": self._last_decision,
        }

    def set_mode(self, mode: str) -> dict:
        valid_modes = [m.value for m in DirectorMode]
        if mode not in valid_modes:
            return {"status": "error", "message": f"Invalid mode. Must be one of: {valid_modes}"}
        self._mode = DirectorMode(mode)
        return {"status": "ok", "mode": self._mode.value}

    def get_decision(self) -> dict:
        import random
        decision = {
            "mode": self._mode.value,
            "target": {
                "pan_angle": 90.0 + random.uniform(-20, 20),
                "tilt_angle": 90.0 + random.uniform(-20, 20),
                "zoom": 2.0 + random.uniform(-1, 1),
                "transition_time": 0.5,
            },
            "reasoning": "Mock decision for development",
            "confidence": 0.85,
            "timestamp": time.time(),
        }
        self._last_decision = decision
        return decision


class StreamService:
    """Mock stream service for development."""

    def __init__(self) -> None:
        self._streaming = False
        self._started_at: Optional[float] = None

    @property
    def is_streaming(self) -> bool:
        return self._streaming

    def status(self) -> dict:
        return {
            "streaming": self._streaming,
            "uptime": time.time() - self._started_at if self._started_at else 0.0,
        }

    def start(self) -> dict:
        if self._streaming:
            return {"status": "already_streaming"}
        self._streaming = True
        self._started_at = time.time()
        return {"status": "started", "timestamp": self._started_at}

    def stop(self) -> dict:
        if not self._streaming:
            return {"status": "already_stopped"}
        self._streaming = False
        self._started_at = None
        return {"status": "stopped"}
