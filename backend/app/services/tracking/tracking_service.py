"""Tracking service with ByteTrack multi-object tracking."""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np

from app.config.settings import AISettings
from app.services.tracking.sorter import ByteTrackSort, Track

logger = logging.getLogger(__name__)


@dataclass
class TrackingConfig:
    """Tracking service configuration."""

    max_time_lost: int = 30
    min_hits_tentative: int = 3
    min_hits_confirmed: int = 3
    iou_threshold: float = 0.3
    second_iou_threshold: float = 0.5
    event_bus: Any = None


class TrackingService:
    """ByteTrack multi-object tracking service.

    Subscribes to DETECTIONS_COMPLETE events, runs object tracking,
    and publishes TRACKING_UPDATED events with track results.

    Track lifecycle:
        tentative -> confirmed -> lost
    """

    def __init__(
        self,
        config: Optional[TrackingConfig] = None,
        ai_settings: Optional[AISettings] = None,
    ) -> None:
        """Initialize the tracking service.

        Args:
            config: Explicit TrackingConfig (takes precedence)
            ai_settings: AISettings loaded from config (used if config is None)
        """
        if config is not None:
            self._config = config
        elif ai_settings is not None:
            self._config = TrackingConfig(
                max_time_lost=30,
                min_hits_tentative=3,
                min_hits_confirmed=3,
                iou_threshold=0.3,
                second_iou_threshold=0.5,
            )
        else:
            self._config = TrackingConfig()

        self._tracker = ByteTrackSort(
            max_time_lost=self._config.max_time_lost,
            min_hits_tentative=self._config.min_hits_tentative,
            min_hits_confirmed=self._config.min_hits_confirmed,
            iou_threshold=self._config.iou_threshold,
            second_iou_threshold=self._config.second_iou_threshold,
        )

        self._event_bus = self._config.event_bus
        self._running = False
        self._lock = threading.Lock()

        self._stats = {
            "frames_processed": 0,
            "tracks_created": 0,
            "tracks_updated": 0,
            "events_published": 0,
            "errors": 0,
            "last_sequence": 0,
            "active_tracks": 0,
            "total_tracks": 0,
        }

        if self._event_bus is not None:
            self._subscribe_to_events()

    def _subscribe_to_events(self) -> None:
        """Subscribe to detection events."""
        if self._event_bus is None:
            return
        try:
            from app.core.events import EventType

            self._event_bus.subscribe(
                EventType.DETECTIONS_COMPLETE,
                self._on_detections_complete,
            )
            logger.info("Subscribed to %s", EventType.DETECTIONS_COMPLETE.value)
        except Exception as exc:
            logger.error("Failed to subscribe to events: %s", exc)

    def _on_detections_complete(self, event: Any) -> None:
        """Handle detections complete event from vision service.

        Args:
            event: Event with data containing detection results
        """
        try:
            data = event.data if hasattr(event, "data") else {}
            sequence = data.get("sequence", 0)
            detections = data.get("detections", [])

            if self._event_bus is None:
                return

            tracks = self.process_detections(detections, sequence)
            self.publish_tracks(tracks, sequence)

        except Exception as exc:
            logger.error("Error processing detections event: %s", exc)

    def process_detections(
        self,
        detections: List[Dict[str, Any]],
        sequence: int = 0,
    ) -> List[Track]:
        """Process detections and update tracks.

        Args:
            detections: List of detection dicts with bbox, class_id, etc.
            sequence: Frame sequence number

        Returns:
            List of active Track objects
        """
        with self._lock:
            try:
                dets = []
                for d in detections:
                    bbox = tuple(d.get("bbox", (0, 0, 0, 0)))
                    class_id = d.get("class_id", 0)
                    class_name = d.get("class_name", "unknown")
                    confidence = d.get("confidence", 1.0)
                    dets.append((bbox, class_id, class_name, confidence))

                tracks = self._tracker.update(dets)
                self._stats["frames_processed"] += 1
                self._stats["last_sequence"] = sequence
                self._stats["active_tracks"] = len(tracks)
                self._stats["total_tracks"] = self._tracker._next_id - 1

                return tracks
            except Exception as exc:
                logger.error("Error processing detections: %s", exc)
                self._stats["errors"] += 1
                return []

    def publish_tracks(
        self,
        tracks: List[Track],
        sequence: int = 0,
    ) -> None:
        """Publish track results to the event bus.

        Args:
            tracks: List of Track objects
            sequence: Frame sequence number
        """
        if self._event_bus is None:
            return

        try:
            from app.core.events import EventType

            track_data = [
                {
                    "track_id": t.track_id,
                    "class_id": t.class_id,
                    "class_name": t.class_name,
                    "bbox": t.bbox,
                    "confidence": t.confidence,
                    "state": t.state.value,
                    "age": t.age,
                    "hits": t.hits,
                    "velocity": t.velocity,
                }
                for t in tracks
            ]

            self._event_bus.publish(
                EventType.TRACKING_UPDATED,
                data={
                    "sequence": sequence,
                    "tracks": track_data,
                    "track_count": len(tracks),
                    "timestamp": time.time(),
                    "frame_count": self._stats["frames_processed"],
                },
                source="tracking",
            )

            self._stats["events_published"] += 1
            self._stats["tracks_updated"] = len(tracks)

        except Exception as exc:
            logger.error("Error publishing tracks: %s", exc)
            self._stats["errors"] += 1

    def start(self) -> None:
        """Start the tracking service."""
        with self._lock:
            self._running = True
            logger.info("TrackingService started")

    def stop(self) -> None:
        """Stop the tracking service."""
        with self._lock:
            self._running = False
            logger.info("TrackingService stopped")

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def tracker(self) -> ByteTrackSort:
        return self._tracker

    @property
    def stats(self) -> Dict[str, int]:
        """Get processing statistics."""
        with self._lock:
            return dict(self._stats)

    def get_active_tracks(self) -> List[Dict[str, Any]]:
        """Get list of active tracks as dictionaries.

        Returns:
            List of track dictionaries
        """
        with self._lock:
            return [t.to_dict() for t in self._tracker.tracks]

    def get_config(self) -> TrackingConfig:
        """Get the current tracking service configuration."""
        return self._config

    def reset(self) -> None:
        """Reset tracker state."""
        with self._lock:
            self._tracker.reset()
            self._stats = {
                "frames_processed": 0,
                "tracks_created": 0,
                "tracks_updated": 0,
                "events_published": 0,
                "errors": 0,
                "last_sequence": 0,
                "active_tracks": 0,
                "total_tracks": 0,
            }