"""System API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.deps import get_state_machine, get_event_bus_dep
from app.core.state import SystemState, InvalidTransitionError

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/status")
def system_status() -> dict:
    sm = get_state_machine()
    return {
        "state": sm.state.name,
        "valid_transitions": [s.name for s in sm.get_valid_transitions()],
        "history": sm.history[-5:],
    }


@router.get("/state")
def get_state() -> dict:
    sm = get_state_machine()
    return {
        "state": sm.state.name,
        "state_value": int(sm.state),
    }


@router.post("/state/{state_name}")
def set_state(state_name: str) -> dict:
    sm = get_state_machine()
    try:
        new_state = SystemState[state_name.upper()]
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid state: {state_name}. Valid states: {[s.name for s in SystemState]}",
        )
    try:
        sm.transition(new_state)
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))
    prev = sm.history[-1]["from"] if len(sm.history) >= 1 else None
    return {
        "state": sm.state.name,
        "previous_state": prev.name if prev is not None else None,
    }
