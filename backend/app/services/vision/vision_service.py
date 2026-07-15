"""Vision service with YOLO11 object detection."""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np

from app.config.settings import AISettings
from app.services.vision.detector import Detection, YOLO11Detector

logger = logging.getLogger(__name__)


@dataclass
class VisionConfig:
    """Vision service configuration."""

    model_name: str
    confidence_threshold: float
    device: str
    max_detections: int
    simulation_mode: bool = False
    max_vram_gb: float = 2.0
    event_bus: Any = None


class VisionService:
    """YOLO11 object detection service.

    Subscribes to camera FRAME_CAPTURED events, runs object detection,
    and publishes DETECTIONS_COMPLETE events with results.

    Can run in simulation mode for video file input without a physical camera.
    """

    def __init__(
        self,
        config: Optional[VisionConfig] = None,
        ai_settings: Optional[AISettings] = None,
        camera_service: Any = None,
    ) -> None:
        """Initialize the vision service.

        Args:
            config: Explicit VisionConfig (takes precedence)
            ai_settings: AISettings loaded from config (used if config is None)
            camera_service: CameraService instance for frame retrieval
        """
        if config is not None:
            self._config = config
        elif ai_settings is not None:
            self._config = VisionConfig(
                model_name=ai_settings.model_name,
                confidence_threshold=ai_settings.confidence_threshold,
                device=ai_settings.device,
                max_detections=ai_settings.max_detections,
                simulation_mode=False,
            )
        else:
            self._config = VisionConfig(
                model_name="yolo11n.pt",
                confidence_threshold=0.5,
                device="cuda",
                max_detections=100,
                simulation_mode=True,
            )

        self._detector = YOLO11Detector(
            model_name=self._config.model_name,
            confidence_threshold=self._config.confidence_threshold,
            device=self._config.device,
            max_detections=self._config.max_detections,
            simulation_mode=self._config.simulation_mode,
            max_vram_gb=self._config.max_vram_gb,
        )

        self._event_bus = self._config.event_bus
        self._camera_service = camera_service
        self._running = False
        self._lock = threading.Lock()

        self._stats = {
            "frames_processed": 0,
            "detections_published": 0,
            "errors": 0,
            "last_sequence": 0,
        }

        if self._event_bus is not None:
            self._subscribe_to_events()

    def _subscribe_to_events(self) -> None:
        """Subscribe to camera frame captured events."""
        if self._event_bus is None:
            return
        try:
            from app.core.events import EventType

            self._event_bus.subscribe(
                EventType.FRAME_CAPTURED,
                self._on_frame_captured,
            )
            logger.info("Subscribed to %s", EventType.FRAME_CAPTURED.value)
        except Exception as exc:
            logger.error("Failed to subscribe to events: %s", exc)

    def _on_frame_captured(self, event: Any) -> None:
        """Handle a frame captured event from the camera service.

        Args:
            event: Event with data containing frame metadata
        """
        try:
            data = event.data if hasattr(event, "data") else {}
            sequence = data.get("sequence", 0)
            shape = data.get("shape", None)

            if self._event_bus is None:
                return

            if shape is None:
                return

            h, w = shape[0], shape[1]
            frame = self._get_frame_for_sequence(sequence, (h, w))

            if frame is None:
                return

            detections = self.process_frame(frame, sequence)
            self.publish_detections(detections, sequence)

        except Exception as exc:
            logger.error("Error processing frame event: %s", exc)

    def _get_frame_for_sequence(
        self, sequence: int, shape: tuple[int, int]
    ) -> Optional[np.ndarray]:
        """Get frame from camera service buffer for given sequence.

        Args:
            sequence: Frame sequence number
            shape: Frame (height, width)

        Returns:
            Frame as numpy array or None if not available
        """
        if self._camera_service is not None:
            try:
                frame = self._camera_service.get_frame()
                if frame is not None and hasattr(frame, "image"):
                    return frame.image
            except Exception:
                pass
        return None

    def process_frame(self, image: np.ndarray, sequence: int = 0) -> List[Detection]:
        """Process a single frame and return detections.

        Args:
            image: Frame as RGB uint8 numpy array (H, W, 3)
            sequence: Frame sequence number

        Returns:
            List of Detection objects
        """
        with self._lock:
            try:
                detections = self._detector.detect(image)
                self._stats["frames_processed"] += 1
                self._stats["last_sequence"] = sequence
                return detections
            except Exception as exc:
                logger.error("Error processing frame: %s", exc)
                self._stats["errors"] += 1
                return []

    def publish_detections(
        self,
        detections: List[Detection],
        sequence: int = 0,
    ) -> None:
        """Publish detection results to the event bus.

        Args:
            detections: List of Detection objects
            sequence: Frame sequence number
        """
        if self._event_bus is None:
            return

        try:
            from app.core.events import EventType

            detection_data = [
                {
                    "class_id": d.class_id,
                    "class_name": d.class_name,
                    "confidence": d.confidence,
                    "bbox": d.bbox,
                    "track_id": d.track_id,
                }
                for d in detections
            ]

            self._event_bus.publish(
                EventType.DETECTIONS_COMPLETE,
                data={
                    "sequence": sequence,
                    "detections": detection_data,
                    "timestamp": time.time(),
                    "frame_count": self._stats["frames_processed"],
                },
                source="vision",
            )

            self._stats["detections_published"] += 1

        except Exception as exc:
            logger.error("Error publishing detections: %s", exc)
            self._stats["errors"] += 1

    def start(self) -> None:
        """Start the vision service."""
        with self._lock:
            self._running = True
            logger.info(
                "VisionService started (simulation=%s, device=%s)",
                self._detector.simulation_mode,
                self._detector.device,
            )

    def stop(self) -> None:
        """Stop the vision service."""
        with self._lock:
            self._running = False
            logger.info("VisionService stopped")

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def detector(self) -> YOLO11Detector:
        return self._detector

    @property
    def stats(self) -> Dict[str, int]:
        """Get processing statistics."""
        with self._lock:
            return dict(self._stats)

    def update_confidence(self, threshold: float) -> None:
        """Update the confidence threshold at runtime.

        Args:
            threshold: New confidence threshold (0.0 to 1.0)
        """
        self._detector.update_confidence(threshold)
        logger.info("Confidence threshold updated to %.2f", threshold)

    def get_config(self) -> VisionConfig:
        """Get the current vision service configuration."""
        return self._config