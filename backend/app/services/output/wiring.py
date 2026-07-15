"""Event wiring helpers for FieldVision AI."""
from __future__ import annotations

import logging
from typing import Any

from app.core.events import EventBus, EventType
from app.services.output.manager import OutputManager

logger = logging.getLogger(__name__)


def wire_output_to_events(
    event_bus: EventBus,
    output_manager: OutputManager,
) -> None:
    """Wire OutputManager to listen for CAMERA_STATE_UPDATED events.

    This is the main integration point — when the Director publishes
    a CameraState, the OutputManager receives it and applies it to
    the active output plugin.
    """

    def on_camera_state(event: Any) -> None:
        try:
            data = event.data if hasattr(event, "data") else {}
            from app.models.camera_state import CameraState
            from app.models.motion import MotionProfile

            state = CameraState(
                center_x=data.get("center_x", 0.5),
                center_y=data.get("center_y", 0.5),
                zoom=data.get("zoom", 1.5),
                motion_profile=MotionProfile(data.get("motion_profile", "broadcast")),
                tracking_mode=data.get("tracking_mode", "broadcast"),
                confidence=data.get("confidence", 0.5),
                timestamp=data.get("timestamp", 0.0),
            )
            output_manager.apply(state)
        except Exception as exc:
            logger.error("Error wiring camera state to output: %s", exc)

    event_bus.subscribe(EventType.CAMERA_STATE_UPDATED, on_camera_state)
    logger.info("OutputManager wired to CAMERA_STATE_UPDATED events")
