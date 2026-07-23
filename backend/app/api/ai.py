"""AI pipeline endpoints — detections, tracking, director decisions."""
from __future__ import annotations

import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["ai"])

# Singleton pipeline — initialized on first request
_pipeline = None


def get_pipeline():
    global _pipeline
    if _pipeline is None:
        from app.services.pipeline import PipelineService
        from app.core.events import get_event_bus
        _pipeline = PipelineService(
            phone_ip="192.168.0.187",
            port=8080,
            event_bus=get_event_bus(),
        )
        _pipeline.start()
        logger.info("Pipeline auto-started")
    return _pipeline


@router.get("/status")
def ai_status() -> dict:
    p = get_pipeline()
    return {
        "running": p.is_running,
        "tracking": p.get_tracking(),
        "decision": p.get_decision(),
    }


@router.get("/tracking")
def ai_tracking() -> dict:
    p = get_pipeline()
    return p.get_tracking()


@router.get("/detections")
def ai_detections() -> dict:
    p = get_pipeline()
    t = p.get_tracking()
    return {
        "count": t["detection_count"],
        "detections": [
            {
                "label": d.label,
                "confidence": round(d.confidence, 2),
                "x": round(d.x, 3),
                "y": round(d.y, 3),
                "w": round(d.w, 3),
                "h": round(d.h, 3),
            }
            for d in p._tracking.detections
        ],
    }


@router.get("/decision")
def ai_decision() -> dict:
    p = get_pipeline()
    return p.get_decision()


@router.post("/start")
def ai_start() -> dict:
    p = get_pipeline()
    p.start()
    return {"status": "started"}


@router.post("/stop")
def ai_stop() -> dict:
    p = get_pipeline()
    p.stop()
    return {"status": "stopped"}
