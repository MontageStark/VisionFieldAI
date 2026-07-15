"""Prediction service with Kalman filter for ball trajectory prediction."""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np

from app.services.prediction.kalman_filter import KalmanFilter2D

logger = logging.getLogger(__name__)


@dataclass
class PredictionConfig:
    """Prediction service configuration."""

    prediction_horizon: int = 10
    process_noise: float = 1.0
    measurement_noise: float = 1.0
    smoothing_factor: float = 0.5
    min_confidence: float = 0.3
    event_bus: Any = None


class PredictionService:
    """Ball trajectory prediction service using Kalman filter.

    Subscribes to TRACKING_UPDATED events, applies Kalman filtering
    to ball tracks, and publishes PREDICTION_UPDATED events with
    predicted future positions.

    Features:
    - 2D position tracking with velocity estimation
    - Configurable prediction horizon
    - Smoothing of noisy detections
    - Gap filling when detections are missing
    """

    def __init__(
        self,
        config: Optional[PredictionConfig] = None,
    ) -> None:
        """Initialize the prediction service.

        Args:
            config: PredictionConfig with service parameters
        """
        if config is not None:
            self._config = config
        else:
            self._config = PredictionConfig()

        self._filters: Dict[str, KalmanFilter2D] = {}
        self._last_positions: Dict[str, tuple[float, float]] = {}
        self._velocities: Dict[str, tuple[float, float]] = {}

        self._event_bus = self._config.event_bus
        self._running = False
        self._lock = threading.Lock()

        self._stats = {
            "predictions_published": 0,
            "filters_created": 0,
            "filters_updated": 0,
            "missed_detections": 0,
            "errors": 0,
        }

        if self._event_bus is not None:
            self._subscribe_to_events()

    def _subscribe_to_events(self) -> None:
        """Subscribe to tracking events."""
        if self._event_bus is None:
            return
        try:
            from app.core.events import EventType

            self._event_bus.subscribe(
                EventType.TRACKING_UPDATED,
                self._on_tracking_updated,
            )
            logger.info("Subscribed to %s", EventType.TRACKING_UPDATED.value)
        except Exception as exc:
            logger.error("Failed to subscribe to events: %s", exc)

    def _on_tracking_updated(self, event: Any) -> None:
        """Handle tracking updated event.

        Args:
            event: Event with track data
        """
        try:
            data = event.data if hasattr(event, "data") else {}
            sequence = data.get("sequence", 0)
            tracks = data.get("tracks", [])

            if self._event_bus is None:
                return

            predictions = self.process_tracks(tracks, sequence)
            self.publish_predictions(predictions, sequence)

        except Exception as exc:
            logger.error("Error processing tracking event: %s", exc)
            self._stats["errors"] += 1

    def process_tracks(
        self,
        tracks: List[Dict[str, Any]],
        sequence: int = 0,
    ) -> List[Dict[str, Any]]:
        """Process tracks and generate predictions.

        Args:
            tracks: List of track dictionaries with ball detections
            sequence: Frame sequence number

        Returns:
            List of prediction dictionaries
        """
        with self._lock:
            predictions = []

            ball_tracks = [t for t in tracks if t.get("class_name") == "sports_ball"]

            if not ball_tracks:
                for track_id in list(self._filters.keys()):
                    pred = self._get_prediction_for_track(track_id, sequence)
                    if pred:
                        predictions.append(pred)

                return predictions

            for track in ball_tracks:
                track_id = str(track.get("track_id", 0))
                bbox = track.get("bbox", (0, 0, 0, 0))
                confidence = track.get("confidence", 1.0)

                cx = (bbox[0] + bbox[2]) / 2.0
                cy = (bbox[1] + bbox[3]) / 2.0

                if track_id not in self._filters:
                    kf = KalmanFilter2D(
                        process_noise=self._config.process_noise,
                        measurement_noise=self._config.measurement_noise,
                    )
                    kf.initialize(cx, cy, vx=0.0, vy=0.0)
                    self._filters[track_id] = kf
                    self._last_positions[track_id] = (cx, cy)
                    self._velocities[track_id] = (0.0, 0.0)
                    self._stats["filters_created"] += 1
                else:
                    kf = self._filters[track_id]
                    prev_pos = self._last_positions.get(track_id, (cx, cy))

                    dt = 1.0 / 30.0
                    kf.predict(dt=dt)

                    kf.update_with_noise(np.array([cx, cy]), confidence=confidence)

                    vx, vy = kf.get_velocity()
                    self._velocities[track_id] = (vx, vy)
                    self._last_positions[track_id] = (cx, cy)

                    self._stats["filters_updated"] += 1

                pred = self._get_prediction_for_track(track_id, sequence)
                if pred:
                    predictions.append(pred)

            return predictions

    def _get_prediction_for_track(self, track_id: str, sequence: int) -> Optional[Dict[str, Any]]:
        """Get prediction for a specific track.

        Args:
            track_id: Track identifier
            sequence: Current sequence number

        Returns:
            Prediction dictionary or None
        """
        if track_id not in self._filters:
            return None

        kf = self._filters[track_id]

        future_positions = kf.predict_future(steps=self._config.prediction_horizon)

        position = kf.get_position()
        velocity = kf.get_velocity()

        confidence = self._estimate_confidence(kf)

        return {
            "track_id": track_id,
            "current_position": position,
            "velocity": velocity,
            "future_positions": future_positions,
            "prediction_horizon": self._config.prediction_horizon,
            "confidence": confidence,
            "sequence": sequence,
        }

    def _estimate_confidence(self, kf: KalmanFilter2D) -> float:
        """Estimate prediction confidence from filter covariance.

        Args:
            kf: Kalman filter

        Returns:
            Confidence score (0-1)
        """
        P = kf.get_covariance()
        pos_var = (P[0, 0] + P[1, 1]) / 2.0

        max_var = 10000.0
        confidence = max(0.0, min(1.0, 1.0 - (pos_var / max_var)))

        return confidence

    def publish_predictions(
        self,
        predictions: List[Dict[str, Any]],
        sequence: int = 0,
    ) -> None:
        """Publish prediction results to event bus.

        Args:
            predictions: List of prediction dictionaries
            sequence: Frame sequence number
        """
        if self._event_bus is None:
            return

        try:
            from app.core.events import EventType

            self._event_bus.publish(
                EventType.PREDICTION_UPDATED,
                data={
                    "sequence": sequence,
                    "predictions": predictions,
                    "prediction_count": len(predictions),
                    "timestamp": time.time(),
                },
                source="prediction",
            )

            self._stats["predictions_published"] += 1

        except Exception as exc:
            logger.error("Error publishing predictions: %s", exc)
            self._stats["errors"] += 1

    def predict_future_positions(
        self,
        track_id: str,
        steps: int | None = None,
    ) -> List[tuple[float, float]]:
        """Get future position predictions for a track.

        Args:
            track_id: Track identifier
            steps: Number of steps. If None, uses configured horizon.

        Returns:
            List of (x, y) position predictions
        """
        with self._lock:
            if track_id not in self._filters:
                return []

            kf = self._filters[track_id]
            if steps is None:
                steps = self._config.prediction_horizon

            return kf.predict_future(steps=steps)

    def get_track_state(self, track_id: str) -> Optional[Dict[str, Any]]:
        """Get current state for a track.

        Args:
            track_id: Track identifier

        Returns:
            Dictionary with position, velocity, or None if not found
        """
        with self._lock:
            if track_id not in self._filters:
                return None

            kf = self._filters[track_id]
            pos = kf.get_position()
            vel = kf.get_velocity()

            return {
                "track_id": track_id,
                "position": pos,
                "velocity": vel,
                "is_initialized": kf.is_initialized(),
            }

    def remove_track(self, track_id: str) -> bool:
        """Remove a track and its filter.

        Args:
            track_id: Track identifier

        Returns:
            True if track was removed
        """
        with self._lock:
            if track_id in self._filters:
                del self._filters[track_id]
                self._last_positions.pop(track_id, None)
                self._velocities.pop(track_id, None)
                return True
            return False

    def clear_all_tracks(self) -> None:
        """Clear all tracked objects and filters."""
        with self._lock:
            self._filters.clear()
            self._last_positions.clear()
            self._velocities.clear()

    def start(self) -> None:
        """Start the prediction service."""
        with self._lock:
            self._running = True
            logger.info("PredictionService started")

    def stop(self) -> None:
        """Stop the prediction service."""
        with self._lock:
            self._running = False
            logger.info("PredictionService stopped")

    @property
    def is_running(self) -> bool:
        """Check if service is running."""
        return self._running

    @property
    def stats(self) -> Dict[str, int]:
        """Get service statistics."""
        with self._lock:
            return dict(self._stats)

    @property
    def active_track_count(self) -> int:
        """Get number of active tracked objects."""
        with self._lock:
            return len(self._filters)

    def get_config(self) -> PredictionConfig:
        """Get service configuration."""
        return self._config

    def reset(self) -> None:
        """Reset service state."""
        with self._lock:
            self._filters.clear()
            self._last_positions.clear()
            self._velocities.clear()
            self._stats = {
                "predictions_published": 0,
                "filters_created": 0,
                "filters_updated": 0,
                "missed_detections": 0,
                "errors": 0,
            }