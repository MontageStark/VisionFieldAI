"""Camera API endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import get_camera_service

router = APIRouter(prefix="/api/camera", tags=["camera"])


@router.get("/status")
def camera_status() -> dict:
    svc = get_camera_service()
    return svc.status()


@router.post("/start")
def camera_start() -> dict:
    svc = get_camera_service()
    return svc.start()


@router.post("/stop")
def camera_stop() -> dict:
    svc = get_camera_service()
    return svc.stop()
