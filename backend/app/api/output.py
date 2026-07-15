"""Output mode control API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.models.camera_state import OutputMode
from app.services.output.manager import OutputManager

router = APIRouter(prefix="/api/output", tags=["output"])


def get_output_manager() -> OutputManager:
    return OutputManager.get_instance()


class OutputModeResponse(BaseModel):
    mode: str


class OutputModeRequest(BaseModel):
    mode: str


@router.get("/mode", response_model=OutputModeResponse)
def get_mode(manager: OutputManager = Depends(get_output_manager)) -> OutputModeResponse:
    return OutputModeResponse(mode=manager.active_mode.value)


@router.post("/mode", response_model=OutputModeResponse)
def set_mode(
    req: OutputModeRequest,
    manager: OutputManager = Depends(get_output_manager),
) -> OutputModeResponse:
    try:
        mode = OutputMode(req.mode)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {req.mode}")
    manager.set_mode(mode)
    return OutputModeResponse(mode=mode.value)


@router.get("/state")
def get_state(manager: OutputManager = Depends(get_output_manager)):
    last = manager.get_last_state()
    if last is None:
        return {
            "center_x": 0.5,
            "center_y": 0.5,
            "zoom": 1.5,
            "mode": manager.active_mode.value,
        }
    return {**last.to_dict(), "mode": manager.active_mode.value}


@router.post("/reset")
def reset_output(manager: OutputManager = Depends(get_output_manager)):
    manager.reset()
    return {"status": "ok"}
