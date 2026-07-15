"""Shot composition logic with rule-based cinematography."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

import numpy as np


class DirectorMode(str, Enum):
    """Director modes affecting shot composition style."""

    BROADCAST = "broadcast"
    AGGRESSIVE = "aggressive"
    WIDE = "wide"
    TRAINING = "training"
    MANUAL_ASSIST = "manual_assist"


class ShotType(str, Enum):
    """Types of camera shots with varying field of view."""

    CLOSE_UP = "close_up"
    MEDIUM = "medium"
    WIDE = "wide"
    OVER_SHOULDER = "over_shoulder"
    TRACKING = "tracking"
    STATIC = "static"


class CameraAction(str, Enum):
    """Camera movement actions."""

    PAN = "pan"
    TILT = "tilt"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    TRACK = "track"
    HOLD = "hold"


class FieldZone(str, Enum):
    """Field zones for camera targeting."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    DEFENSE = "defense"
    OFFENSE = "offense"
    GOAL = "goal"


CLASS_WEIGHTS = {
    "ball": 2.5,
    "person": 1.0,
    "goalkeeper": 1.3,
    "referee": 0.8,
}

RELEVANT_CLASSES = {"ball", "person", "goalkeeper", "referee"}


@dataclass
class ShotComposition:
    """Result of shot composition -- abstract normalized framing.
    No hardware-specific values (degrees, angles).
    """

    center_x: float = 0.5      # 0.0-1.0, 0=left, 1=right
    center_y: float = 0.5      # 0.0-1.0, 0=top, 1=bottom
    zoom: float = 1.5
    action: CameraAction = CameraAction.HOLD
    shot_type: ShotType = ShotType.STATIC
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "center_x": self.center_x,
            "center_y": self.center_y,
            "zoom": self.zoom,
            "action": self.action.value,
            "shot_type": self.shot_type.value,
            "confidence": self.confidence,
        }


# Backwards compat alias
CameraMove = ShotComposition


class ShotComposer:
    """Rule-based cinematography engine for shot composition.

    Computes weighted centroids from tracked objects, determines
    appropriate shot types based on director mode, and generates
    camera movement commands.
    """

    def __init__(self, mode: DirectorMode = DirectorMode.BROADCAST) -> None:
        """Initialize the shot composer.

        Args:
            mode: Director mode affecting composition rules
        """
        self.mode = mode
        self._last_centroid: Optional[Tuple[float, float]] = None

    def set_mode(self, mode: DirectorMode) -> None:
        """Set the director mode.

        Args:
            mode: New director mode
        """
        self.mode = mode

    def compute_weighted_centroid(
        self, tracks: List[dict]
    ) -> Optional[Tuple[float, float]]:
        """Compute weighted centroid from tracked objects.

        Ball has highest weight (2.5x), then goalkeeper (1.3x),
        then players (1.0x), then referee (0.8x).

        Args:
            tracks: List of track dictionaries with bbox and class_name

        Returns:
            Tuple of (x, y) centroid coordinates, or None if no relevant tracks
        """
        if not tracks:
            return None

        total_weight = 0.0
        weighted_x = 0.0
        weighted_y = 0.0

        for track in tracks:
            class_name = track.get("class_name", "")
            if class_name not in RELEVANT_CLASSES:
                continue

            bbox = track.get("bbox", [0, 0, 0, 0])
            if len(bbox) < 4:
                continue

            x1, y1, x2, y2 = bbox
            center_x = (x1 + x2) / 2.0
            center_y = (y1 + y2) / 2.0
            confidence = track.get("confidence", 1.0)
            weight = CLASS_WEIGHTS.get(class_name, 1.0) * confidence

            weighted_x += center_x * weight
            weighted_y += center_y * weight
            total_weight += weight

        if total_weight <= 0:
            return None

        centroid = (weighted_x / total_weight, weighted_y / total_weight)
        self._last_centroid = centroid
        return centroid

    def get_field_zone(
        self, x: float, y: float, frame_width: int, frame_height: int
    ) -> FieldZone:
        """Determine field zone from coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels

        Returns:
            FieldZone enum value
        """
        left_third = frame_width / 3
        right_third = 2 * frame_width / 3

        zone_h = FieldZone.CENTER
        if x < left_third:
            zone_h = FieldZone.LEFT
        elif x > right_third:
            zone_h = FieldZone.RIGHT

        fifth_h = frame_height / 5
        zone_v = FieldZone.CENTER
        if y < fifth_h:
            zone_v = FieldZone.OFFENSE
        elif y > 4 * fifth_h:
            zone_v = FieldZone.DEFENSE

        if zone_v == FieldZone.DEFENSE and zone_h == FieldZone.CENTER:
            if y > frame_height * 0.92:
                return FieldZone.GOAL
            return FieldZone.DEFENSE

        if zone_v != FieldZone.CENTER:
            return zone_v
        return zone_h

    def get_zoom_level(
        self, zone: FieldZone, player_count: int
    ) -> float:
        """Calculate zoom level based on field zone and player count.

        Args:
            zone: Current field zone
            player_count: Number of relevant players in frame

        Returns:
            Zoom factor (1.0 = wide, higher = more zoomed)
        """
        base_zoom = 1.0

        if self.mode == DirectorMode.WIDE:
            base_zoom = 1.2
        elif self.mode == DirectorMode.AGGRESSIVE:
            base_zoom = 2.0
        elif self.mode == DirectorMode.BROADCAST:
            base_zoom = 1.5
        elif self.mode == DirectorMode.TRAINING:
            base_zoom = 1.8
        elif self.mode == DirectorMode.MANUAL_ASSIST:
            base_zoom = 1.5

        if zone == FieldZone.GOAL:
            base_zoom *= 1.5
        elif zone == FieldZone.CENTER:
            base_zoom *= 1.0
        else:
            base_zoom *= 0.9

        player_factor = max(0.5, 1.0 - (player_count - 2) * 0.05)
        base_zoom *= player_factor

        return max(1.0, min(4.0, base_zoom))

    def _get_shot_type_for_mode(
        self,
        zone: FieldZone,
        player_count: int,
        has_ball: bool,
    ) -> ShotType:
        """Determine shot type based on director mode and scene analysis.

        Args:
            zone: Current field zone
            player_count: Number of players in frame
            has_ball: Whether ball is present in frame

        Returns:
            ShotType enum value
        """
        if self.mode == DirectorMode.BROADCAST:
            if player_count <= 3:
                return ShotType.MEDIUM
            elif player_count <= 6:
                return ShotType.OVER_SHOULDER
            return ShotType.WIDE

        elif self.mode == DirectorMode.AGGRESSIVE:
            if has_ball:
                return ShotType.CLOSE_UP
            return ShotType.TRACKING

        elif self.mode == DirectorMode.WIDE:
            return ShotType.WIDE

        elif self.mode == DirectorMode.TRAINING:
            if player_count <= 4:
                return ShotType.MEDIUM
            return ShotType.OVER_SHOULDER

        elif self.mode == DirectorMode.MANUAL_ASSIST:
            if player_count <= 5:
                return ShotType.MEDIUM
            return ShotType.WIDE

        return ShotType.STATIC

    def compose_shot(
        self,
        tracks: List[dict],
        frame_width: int,
        frame_height: int,
        prev_move: Optional[ShotComposition] = None,
    ) -> ShotComposition:
        """Compose a shot based on tracked objects and director mode.

        Args:
            tracks: List of track dictionaries
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels
            prev_move: Previous shot composition for smoothing

        Returns:
            ShotComposition with normalized center_x, center_y, zoom
        """
        if not tracks:
            return ShotComposition()

        centroid = self.compute_weighted_centroid(tracks)
        if centroid is None:
            return ShotComposition()

        target_x, target_y = centroid

        has_ball = any(t.get("class_name") == "ball" for t in tracks)
        player_count = sum(
            1 for t in tracks if t.get("class_name") in ("person", "goalkeeper")
        )

        zone = self.get_field_zone(target_x, target_y, frame_width, frame_height)
        zoom = self.get_zoom_level(zone, player_count)
        shot_type = self._get_shot_type_for_mode(zone, player_count, has_ball)

        center_x = target_x / frame_width   # 0-1 normalized
        center_y = target_y / frame_height  # 0-1 normalized

        if prev_move is not None:
            center_x = prev_move.center_x * 0.7 + center_x * 0.3
            center_y = prev_move.center_y * 0.7 + center_y * 0.3

        confidence = min(1.0, sum(t.get("confidence", 0) for t in tracks) / len(tracks))

        return ShotComposition(
            center_x=center_x,
            center_y=center_y,
            zoom=zoom,
            action=CameraAction.TRACK if abs(center_x - 0.5) > 0.1 or abs(center_y - 0.5) > 0.1 else CameraAction.HOLD,
            shot_type=shot_type,
            confidence=confidence,
        )

    def generate_camera_actions(
        self,
        delta_x: float,
        delta_y: float,
        player_count: int,
    ) -> List[CameraAction]:
        """Generate list of camera actions based on movement deltas.

        Args:
            delta_x: Horizontal movement in pixels
            delta_y: Vertical movement in pixels
            player_count: Number of players in frame

        Returns:
            List of CameraAction enums
        """
        actions: List[CameraAction] = []
        threshold_x = 20.0
        threshold_y = 15.0

        if abs(delta_x) > threshold_x:
            actions.append(CameraAction.PAN)
        if abs(delta_y) > threshold_y:
            actions.append(CameraAction.TILT)

        if player_count < 3:
            actions.append(CameraAction.ZOOM_IN)
        elif player_count > 8:
            actions.append(CameraAction.ZOOM_OUT)

        if len(actions) == 0:
            actions.append(CameraAction.HOLD)
        else:
            actions.append(CameraAction.TRACK)

        return actions

    def smooth_composition(
        self,
        prev_move: Optional[ShotComposition],
        target_center_x: float,
        target_center_y: float,
        target_zoom: float,
    ) -> ShotComposition:
        """Smooth shot composition with interpolation.

        Args:
            prev_move: Previous shot composition (None for first move)
            target_center_x: Target center X (0-1)
            target_center_y: Target center Y (0-1)
            target_zoom: Target zoom level

        Returns:
            Smoothed ShotComposition
        """
        if prev_move is None:
            return ShotComposition(
                center_x=target_center_x,
                center_y=target_center_y,
                zoom=target_zoom,
                action=CameraAction.HOLD,
                shot_type=ShotType.STATIC,
                confidence=1.0,
            )

        smoothing_factor = 0.3
        smoothed_cx = prev_move.center_x + (target_center_x - prev_move.center_x) * smoothing_factor
        smoothed_cy = prev_move.center_y + (target_center_y - prev_move.center_y) * smoothing_factor
        smoothed_zoom = prev_move.zoom + (target_zoom - prev_move.zoom) * smoothing_factor

        delta_cx = abs(target_center_x - prev_move.center_x)
        delta_cy = abs(target_center_y - prev_move.center_y)

        if delta_cx > 0.15 or delta_cy > 0.15:
            action = CameraAction.TRACK
        elif delta_cx > 0.1:
            action = CameraAction.PAN
        elif delta_cy > 0.08:
            action = CameraAction.TILT
        else:
            action = CameraAction.HOLD

        return ShotComposition(
            center_x=smoothed_cx,
            center_y=smoothed_cy,
            zoom=smoothed_zoom,
            action=action,
            shot_type=prev_move.shot_type,
            confidence=prev_move.confidence,
        )

    # Keep old name as alias
    smooth_camera_move = smooth_composition