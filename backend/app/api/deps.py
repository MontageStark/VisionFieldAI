"""Dependency injection for FastAPI routes."""
from __future__ import annotations

from typing import Optional

from app.core.state import SystemStateMachine, create_default_machine
from app.core.events import EventBus, get_event_bus, reset_event_bus
from app.api.mocks import CameraService, ServoService, DirectorService, StreamService


_state_machine: Optional[SystemStateMachine] = None
_event_bus: Optional[EventBus] = None


def get_state_machine() -> SystemStateMachine:
    global _state_machine
    if _state_machine is None:
        _state_machine = create_default_machine()
    return _state_machine


def get_event_bus_dep() -> EventBus:
    return get_event_bus()


_camera_svc: Optional[CameraService] = None
_servo_svc: Optional[ServoService] = None
_director_svc: Optional[DirectorService] = None
_stream_svc: Optional[StreamService] = None


def get_camera_service() -> CameraService:
    global _camera_svc
    if _camera_svc is None:
        _camera_svc = CameraService()
    return _camera_svc


def get_servo_service() -> ServoService:
    global _servo_svc
    if _servo_svc is None:
        _servo_svc = ServoService()
    return _servo_svc


def get_director_service() -> DirectorService:
    global _director_svc
    if _director_svc is None:
        _director_svc = DirectorService()
    return _director_svc


def get_stream_service() -> StreamService:
    global _stream_svc
    if _stream_svc is None:
        _stream_svc = StreamService()
    return _stream_svc


def reset_services() -> None:
    global _camera_svc, _servo_svc, _director_svc, _stream_svc, _state_machine
    _camera_svc = None
    _servo_svc = None
    _director_svc = None
    _stream_svc = None
    _state_machine = None
    reset_event_bus()
