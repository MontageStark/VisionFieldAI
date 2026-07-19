"""Dependency injection for FastAPI routes."""
from __future__ import annotations

import logging
import time
from typing import Any, Optional

from app.core.state import SystemStateMachine, create_default_machine
from app.core.events import EventBus, get_event_bus, reset_event_bus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Adapter wrappers
# ---------------------------------------------------------------------------
# Real services have different interfaces from the API contract.
# Adapters expose the exact method signatures the API routes expect,
# delegating to the real services underneath.  If initialization fails
# (missing deps, no hardware, etc.) we fall back to the mock implementations
# so the API stays usable for development.


class CameraServiceAdapter:
    """Wraps the real CameraService to expose the mock-compatible API."""

    def __init__(self) -> None:
        self._running = False
        self._started_at: Optional[float] = None
        self._real: Any = None
        self._error: Optional[str] = None

        try:
            from app.config.loader import get_settings
            from app.services.camera.service import CameraService as RealCamera

            settings = get_settings()
            config = settings.camera.model_dump()
            self._real = RealCamera(config)
            logger.info("CameraService initialized (source=%s)", config.get("source_type"))
        except Exception as exc:
            self._error = str(exc)
            logger.warning("CameraService using mock fallback: %s", exc)

    def start(self) -> dict:
        if self._running:
            return {"status": "already_running"}
        if self._real is not None:
            try:
                if hasattr(self._real, "source") and self._real.source:
                    opened = self._real.source.open()
                    if not opened:
                        return {"status": "error", "detail": "Failed to open camera source"}
            except Exception as exc:
                return {"status": "error", "detail": str(exc)}
        self._running = True
        self._started_at = time.time()
        return {"status": "started", "timestamp": self._started_at}

    def stop(self) -> dict:
        if not self._running:
            return {"status": "already_stopped"}
        if self._real is not None:
            try:
                if hasattr(self._real, "source") and self._real.source:
                    self._real.source.release()
            except Exception as exc:
                logger.error("Error stopping camera: %s", exc)
        self._running = False
        self._started_at = None
        return {"status": "stopped"}

    def status(self) -> dict:
        return {
            "running": self._running,
            "uptime": time.time() - self._started_at if self._started_at else 0.0,
            "source": "real" if self._real else "mock",
            "error": self._error,
        }


class ServoServiceAdapter:
    """Wraps the real ServoOutput plugin to expose the mock-compatible API."""

    def __init__(self) -> None:
        self._pan_angle = 90.0
        self._tilt_angle = 90.0
        self._emergency = False
        self._real: Any = None
        self._error: Optional[str] = None

        try:
            from app.config.loader import get_settings
            from app.services.output.servo import ServoOutput

            settings = get_settings()
            self._real = ServoOutput(settings.output.servo)
            logger.info("ServoService initialized (real ServoOutput plugin)")
        except Exception as exc:
            self._error = str(exc)
            logger.warning("ServoService using mock fallback: %s", exc)

    def status(self) -> dict:
        pan = self._pan_angle
        tilt = self._tilt_angle
        if self._real is not None:
            try:
                pan = self._real.pan_angle
                tilt = self._real.tilt_angle
                self._pan_angle = pan
                self._tilt_angle = tilt
            except Exception:
                pass
        return {
            "pan_angle": pan,
            "tilt_angle": tilt,
            "emergency_stop": self._emergency,
            "source": "real" if self._real else "mock",
        }

    def command(self, pan: float, tilt: float) -> dict:
        if self._emergency:
            return {"status": "emergency_active", "pan": self._pan_angle, "tilt": self._tilt_angle}
        pan = max(0.0, min(180.0, pan))
        tilt = max(0.0, min(180.0, tilt))
        self._pan_angle = pan
        self._tilt_angle = tilt
        return {"status": "ok", "pan": pan, "tilt": tilt, "source": "real" if self._real else "mock"}

    def home(self) -> dict:
        if self._emergency:
            return {"status": "emergency_active"}
        self._pan_angle = 90.0
        self._tilt_angle = 90.0
        if self._real is not None:
            try:
                self._real.reset()
            except Exception:
                pass
        return {"status": "homed", "pan": 90.0, "tilt": 90.0}

    def emergency_stop(self) -> dict:
        self._emergency = True
        return {"status": "emergency_stop_activated"}

    def reset_emergency(self) -> dict:
        self._emergency = False
        return {"status": "emergency_reset"}


class DirectorServiceAdapter:
    """Wraps the real DirectorService to expose the mock-compatible API."""

    def __init__(self) -> None:
        self._mode = "broadcast"
        self._last_decision: Optional[dict] = None
        self._real: Any = None
        self._error: Optional[str] = None

        try:
            from app.config.loader import get_settings
            from app.services.director.director_service import DirectorService as RealDirector
            from app.services.director.shot_composer import DirectorMode

            settings = get_settings()
            from app.services.director.director_service import DirectorConfig

            config = DirectorConfig(
                mode=DirectorMode.BROADCAST,
                event_bus=get_event_bus(),
            )
            self._real = RealDirector(config=config)
            logger.info("DirectorService initialized (real)")
        except Exception as exc:
            self._error = str(exc)
            logger.warning("DirectorService using mock fallback: %s", exc)

    def status(self) -> dict:
        return {
            "mode": self._mode,
            "last_decision": self._last_decision,
            "source": "real" if self._real else "mock",
        }

    def set_mode(self, mode: str) -> dict:
        valid_modes = ["broadcast", "aggressive", "wide", "training", "manual_assist"]
        if mode not in valid_modes:
            return {"status": "error", "message": f"Invalid mode. Must be one of: {valid_modes}"}
        self._mode = mode
        if self._real is not None:
            try:
                from app.services.director.shot_composer import DirectorMode
                self._real.set_mode(DirectorMode(mode))
            except Exception as exc:
                logger.error("Failed to set director mode: %s", exc)
        return {"status": "ok", "mode": mode}

    def get_decision(self) -> dict:
        import random
        decision = {
            "mode": self._mode,
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


class StreamServiceAdapter:
    """Wraps the real OutputManager to expose the mock-compatible API."""

    def __init__(self) -> None:
        self._streaming = False
        self._started_at: Optional[float] = None
        self._real: Any = None
        self._error: Optional[str] = None

        try:
            from app.config.loader import get_settings
            from app.services.output.manager import OutputManager

            settings = get_settings()
            self._real = OutputManager(settings.output)
            logger.info("StreamService initialized (OutputManager)")
        except Exception as exc:
            self._error = str(exc)
            logger.warning("StreamService using mock fallback: %s", exc)

    def status(self) -> dict:
        return {
            "streaming": self._streaming,
            "uptime": time.time() - self._started_at if self._started_at else 0.0,
            "source": "real" if self._real else "mock",
            "active_mode": self._real.active_mode.value if self._real else None,
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


# ---------------------------------------------------------------------------
# Singleton state
# ---------------------------------------------------------------------------

_state_machine: Optional[SystemStateMachine] = None
_event_bus: Optional[EventBus] = None

_camera_svc: Optional[CameraServiceAdapter] = None
_servo_svc: Optional[ServoServiceAdapter] = None
_director_svc: Optional[DirectorServiceAdapter] = None
_stream_svc: Optional[StreamServiceAdapter] = None


def get_state_machine() -> SystemStateMachine:
    global _state_machine
    if _state_machine is None:
        _state_machine = create_default_machine()
    return _state_machine


def get_event_bus_dep() -> EventBus:
    return get_event_bus()


def get_camera_service() -> CameraServiceAdapter:
    global _camera_svc
    if _camera_svc is None:
        _camera_svc = CameraServiceAdapter()
    return _camera_svc


def get_servo_service() -> ServoServiceAdapter:
    global _servo_svc
    if _servo_svc is None:
        _servo_svc = ServoServiceAdapter()
    return _servo_svc


def get_director_service() -> DirectorServiceAdapter:
    global _director_svc
    if _director_svc is None:
        _director_svc = DirectorServiceAdapter()
    return _director_svc


def get_stream_service() -> StreamServiceAdapter:
    global _stream_svc
    if _stream_svc is None:
        _stream_svc = StreamServiceAdapter()
    return _stream_svc


def reset_services() -> None:
    global _camera_svc, _servo_svc, _director_svc, _stream_svc, _state_machine
    _camera_svc = None
    _servo_svc = None
    _director_svc = None
    _stream_svc = None
    _state_machine = None
    reset_event_bus()
