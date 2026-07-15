"""DirectorService - Cinematic decision engine for autonomous camera control."""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.core.events import EventType, EventPriority
from app.models.camera_state import CameraState
from app.models.motion import MotionProfile
from app.services.director.shot_composer import (
    ShotComposer,
    DirectorMode,
    ShotType,
    CameraAction,
    ShotComposition,
)


logger = logging.getLogger(__name__)


@dataclass
class DirectorConfig:
    """Director service configuration."""

    mode: DirectorMode = DirectorMode.BROADCAST
    event_bus: Any = None
    frame_width: int = 640
    frame_height: int = 480
    smoothing_factor: float = 0.3


class DirectorService:
    """Cinematic decision engine for autonomous camera control.

    Subscribes to TRACKING_UPDATED events, processes tracking data
    to compose shots using ShotComposer, and publishes DIRECTOR_DECISION
    and CAMERA_STATE_UPDATED events to control the camera.

    Director Modes:
        - broadcast: Professional broadcast-style coverage
        - aggressive: Tight shots on ball carrier
        - wide: Full field overview
        - training: Educational view showing formations
        - manual_assist: Semi-automatic with human override capability
    """

    def __init__(
        self,
        config: Optional[DirectorConfig] = None,
        mode: Optional[DirectorMode] = None,
        output_manager: Optional[Any] = None,
    ) -> None:
        """Initialize the director service.

        Args:
            config: Explicit DirectorConfig (takes precedence)
            mode: Director mode (used if config is None)
            output_manager: Optional OutputManager for forwarding camera states
        """
        if config is not None:
            self._config = config
        else:
            self._config = DirectorConfig(mode=mode or DirectorMode.BROADCAST)

        self._composer = ShotComposer(mode=self._config.mode)
        self._event_bus = self._config.event_bus
        self._output_manager = output_manager
        self._running = False
        self._lock = threading.Lock()

        self._last_composition: Optional[ShotComposition] = None
        self._last_sequence: int = 0

        self._stats = {
            "frames_processed": 0,
            "decisions_published": 0,
            "camera_moves_published": 0,
            "errors": 0,
            "last_sequence": 0,
        }

        if self._event_bus is not None:
            self._subscribe_to_events()
            if self._output_manager is not None:
                self._subscribe_to_output_events()

    def _subscribe_to_events(self) -> None:
        """Subscribe to tracking events."""
        if self._event_bus is None:
            return
        try:
            self._event_bus.subscribe(
                EventType.TRACKING_UPDATED,
                self._on_tracking_updated,
            )
            logger.info("Subscribed to %s", EventType.TRACKING_UPDATED.value)
        except Exception as exc:
            logger.error("Failed to subscribe to events: %s", exc)

    def _subscribe_to_output_events(self) -> None:
        """Subscribe to CAMERA_STATE_UPDATED to forward to OutputManager."""
        if self._event_bus is None or self._output_manager is None:
            return
        try:
            self._event_bus.subscribe(
                EventType.CAMERA_STATE_UPDATED,
                self._on_camera_state_for_output,
            )
            logger.info(
                "Subscribed to %s for output forwarding",
                EventType.CAMERA_STATE_UPDATED.value,
            )
        except Exception as exc:
            logger.error("Failed to subscribe to output events: %s", exc)

    def _on_camera_state_for_output(self, event: Any) -> None:
        """Forward CAMERA_STATE_UPDATED to OutputManager."""
        if self._output_manager is None:
            return
        try:
            data = event.data if hasattr(event, "data") else {}
            state = CameraState(
                center_x=data.get("center_x", 0.5),
                center_y=data.get("center_y", 0.5),
                zoom=data.get("zoom", 1.5),
                motion_profile=MotionProfile(data.get("motion_profile", "broadcast")),
                tracking_mode=data.get("tracking_mode", "broadcast"),
                confidence=data.get("confidence", 0.5),
                timestamp=data.get("timestamp", 0.0),
            )
            self._output_manager.apply(state)
        except Exception as exc:
            logger.error("Error forwarding camera state to output: %s", exc)

    def _on_tracking_updated(self, event: Any) -> None:
        """Handle tracking updated event from tracking service.

        Args:
            event: Event with data containing track results
        """
        try:
            data = event.data if hasattr(event, "data") else {}
            sequence = data.get("sequence", 0)
            tracks = data.get("tracks", [])

            if self._event_bus is None:
                return

            composition = self.process_tracks(tracks, sequence)
            self.publish_decision(tracks, composition, sequence)
            self.publish_camera_state(composition, sequence)

        except Exception as exc:
            logger.error("Error processing tracking event: %s", exc)
            with self._lock:
                self._stats["errors"] += 1

    def process_tracks(
        self,
        tracks: List[Dict[str, Any]],
        sequence: int = 0,
    ) -> ShotComposition:
        """Process tracks and compose a shot.

        Args:
            tracks: List of track dictionaries
            sequence: Frame sequence number

        Returns:
            ShotComposition with composition decisions
        """
        with self._lock:
            try:
                composition = self._composer.compose_shot(
                    tracks,
                    self._config.frame_width,
                    self._config.frame_height,
                    self._last_composition,
                )

                smoothed = self._composer.smooth_camera_move(
                    self._last_composition,
                    composition.center_x,
                    composition.center_y,
                    composition.zoom,
                )
                self._last_composition = smoothed

                self._stats["frames_processed"] += 1
                self._stats["last_sequence"] = sequence
                self._last_sequence = sequence

                return smoothed

            except Exception as exc:
                logger.error("Error processing tracks: %s", exc)
                self._stats["errors"] += 1
                return ShotComposition()

    def publish_decision(
        self,
        tracks: List[Dict[str, Any]],
        composition: ShotComposition,
        sequence: int = 0,
    ) -> None:
        """Publish director decision event.

        Args:
            tracks: List of track dictionaries
            composition: Composed shot composition
            sequence: Frame sequence number
        """
        if self._event_bus is None:
            return

        try:
            centroid = self._composer.compute_weighted_centroid(tracks)
            zone = None
            if centroid:
                zone = self._composer.get_field_zone(
                    centroid[0],
                    centroid[1],
                    self._config.frame_width,
                    self._config.frame_height,
                )

            player_count = sum(
                1 for t in tracks if t.get("class_name") in ("person", "goalkeeper")
            )
            has_ball = any(t.get("class_name") == "ball" for t in tracks)

            self._event_bus.publish(
                EventType.DIRECTOR_DECISION,
                data={
                    "sequence": sequence,
                    "mode": self._config.mode.value,
                    "camera_move": composition.to_dict(),
                    "zone": zone.value if zone else None,
                    "player_count": player_count,
                    "has_ball": has_ball,
                    "centroid": list(centroid) if centroid else None,
                    "timestamp": time.time(),
                },
                priority=EventPriority.NORMAL,
                source="director",
            )

            self._stats["decisions_published"] += 1

        except Exception as exc:
            logger.error("Error publishing director decision: %s", exc)
            self._stats["errors"] += 1

    def publish_camera_state(
        self,
        composition: ShotComposition,
        sequence: int = 0,
    ) -> None:
        """Publish CameraState to the event bus.

        Args:
            composition: Composed shot composition
            sequence: Frame sequence number
        """
        if self._event_bus is None:
            return
        try:
            camera_state = CameraState(
                center_x=composition.center_x,
                center_y=composition.center_y,
                zoom=composition.zoom,
                motion_profile=MotionProfile.BROADCAST,
                tracking_mode=self._config.mode.value,
                confidence=composition.confidence,
                timestamp=time.time(),
            )
            self._event_bus.publish(
                EventType.CAMERA_STATE_UPDATED,
                data={
                    "sequence": sequence,
                    **camera_state.to_dict(),
                },
                priority=EventPriority.HIGH,
                source="director",
            )
            self._stats["camera_moves_published"] += 1
        except Exception as exc:
            logger.error("Error publishing camera state: %s", exc)
            self._stats["errors"] += 1

    def process_frame(
        self,
        tracks: List[Dict[str, Any]],
        sequence: int = 0,
    ) -> ShotComposition:
        """Process a single frame and generate camera commands.

        Convenience method that combines process_tracks and publishing.

        Args:
            tracks: List of track dictionaries
            sequence: Frame sequence number

        Returns:
            ShotComposition with composition decisions
        """
        composition = self.process_tracks(tracks, sequence)

        if self._event_bus is not None:
            self.publish_decision(tracks, composition, sequence)
            self.publish_camera_state(composition, sequence)

        return composition

    def start(self) -> None:
        """Start the director service."""
        with self._lock:
            self._running = True
            logger.info("DirectorService started in %s mode", self._config.mode.value)

    def stop(self) -> None:
        """Stop the director service."""
        with self._lock:
            self._running = False
            logger.info("DirectorService stopped")

    @property
    def is_running(self) -> bool:
        """Check if service is running."""
        return self._running

    @property
    def composer(self) -> ShotComposer:
        """Get the shot composer instance."""
        return self._composer

    @property
    def stats(self) -> Dict[str, int]:
        """Get processing statistics."""
        with self._lock:
            return dict(self._stats)

    def get_mode(self) -> DirectorMode:
        """Get current director mode."""
        return self._config.mode

    def set_mode(self, mode: DirectorMode) -> None:
        """Set director mode.

        Args:
            mode: New director mode
        """
        with self._lock:
            self._config.mode = mode
            self._composer.set_mode(mode)
            logger.info("Director mode changed to %s", mode.value)

    def get_config(self) -> DirectorConfig:
        """Get current director configuration."""
        return self._config

    def reset(self) -> None:
        """Reset director state."""
        with self._lock:
            self._last_composition = None
            self._last_sequence = 0
            self._stats = {
                "frames_processed": 0,
                "decisions_published": 0,
                "camera_moves_published": 0,
                "errors": 0,
                "last_sequence": 0,
            }