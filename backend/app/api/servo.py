"""Servo API endpoints."""
from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.api.deps import get_servo_service

router = APIRouter(prefix="/api/servo", tags=["servo"])


class ServoCommandRequest(BaseModel):
    pan: float = Field(..., ge=0.0, le=180.0, description="Pan angle degrees")
    tilt: float = Field(..., ge=0.0, le=180.0, description="Tilt angle degrees")


@router.get("/status")
def servo_status() -> dict:
    svc = get_servo_service()
    return svc.status()


@router.post("/command")
def servo_command(req: ServoCommandRequest) -> dict:
    svc = get_servo_service()
    result = svc.command(req.pan, req.tilt)
    if result["status"] == "emergency_active":
        raise HTTPException(status_code=409, detail="Emergency stop is active")
    return result


@router.post("/home")
def servo_home() -> dict:
    svc = get_servo_service()
    return svc.home()


@router.post("/emergency")
def servo_emergency() -> dict:
    svc = get_servo_service()
    return svc.emergency_stop()
