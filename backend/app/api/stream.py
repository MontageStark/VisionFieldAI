"""Streaming API endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import get_stream_service

router = APIRouter(prefix="/api/stream", tags=["stream"])


@router.get("/status")
def stream_status() -> dict:
    svc = get_stream_service()
    return svc.status()


@router.post("/start")
def stream_start() -> dict:
    svc = get_stream_service()
    return svc.start()


@router.post("/stop")
def stream_stop() -> dict:
    svc = get_stream_service()
    return svc.stop()
