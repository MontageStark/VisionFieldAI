"""Director API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.deps import get_director_service

router = APIRouter(prefix="/api/director", tags=["director"])


@router.get("/status")
def director_status() -> dict:
    svc = get_director_service()
    return svc.status()


@router.post("/mode/{mode}")
def director_set_mode(mode: str) -> dict:
    svc = get_director_service()
    result = svc.set_mode(mode)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/decision")
def director_decision() -> dict:
    svc = get_director_service()
    return svc.get_decision()
