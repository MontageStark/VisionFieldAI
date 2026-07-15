"""Virtual camera output — crop/pan/zoom in software."""
from __future__ import annotations

import math
from typing import Optional

import cv2
import numpy as np

from app.models.camera_state import CameraState, VirtualCameraConfig
from app.services.output.base import OutputPlugin


class VirtualCameraOutput(OutputPlugin):
    """Virtual camera output — applies crop/pan/zoom to frames in software.

    Takes CameraState (center_x, center_y, zoom) and transforms the input
    frame to produce a professionally framed output frame suitable for
    broadcast (e.g., via OBS virtual camera).

    Features:
    - Dead zone to prevent jitter on small movements
    - Safe margin to keep action away from frame edges
    - Smooth zoom transitions
    - Motion-profile-aware framing
    """

    def __init__(self, config: Optional[VirtualCameraConfig] = None) -> None:
        self._config = config or VirtualCameraConfig()
        self._current_state: Optional[CameraState] = None

    @property
    def name(self) -> str:
        return "virtual_camera"

    def apply(self, state: CameraState) -> None:
        """Apply a camera state, with dead zone filtering."""
        if self._current_state is not None:
            dx = state.center_x - self._current_state.center_x
            dy = state.center_y - self._current_state.center_y
            distance = math.sqrt(dx * dx + dy * dy)
            if distance < self._config.dead_zone:
                # Within dead zone — keep current position, only update zoom
                state = CameraState(
                    center_x=self._current_state.center_x,
                    center_y=self._current_state.center_y,
                    zoom=state.zoom,
                    motion_profile=state.motion_profile,
                    tracking_mode=state.tracking_mode,
                    confidence=state.confidence,
                    timestamp=state.timestamp,
                )
        self._current_state = state

    def get_state(self) -> Optional[CameraState]:
        return self._current_state

    def reset(self) -> None:
        if self._current_state is not None:
            self._current_state = CameraState(
                center_x=0.5,
                center_y=0.5,
                zoom=self._config.default_zoom,
                motion_profile=self._current_state.motion_profile,
                tracking_mode=self._current_state.tracking_mode,
                confidence=1.0,
                timestamp=self._current_state.timestamp,
            )

    def apply_frame(self, frame: np.ndarray) -> np.ndarray:
        """Apply current CameraState to a frame and return the transformed frame.

        Args:
            frame: Input BGR frame (H, W, 3)

        Returns:
            Transformed frame matching desired CameraState
        """
        if self._current_state is None:
            return frame

        h, w = frame.shape[:2]
        cx = self._current_state.center_x
        cy = self._current_state.center_y
        zoom = self._current_state.zoom

        # Compute crop window
        crop_w = w / zoom
        crop_h = h / zoom

        # Clamp crop size to frame size
        crop_w = min(crop_w, w)
        crop_h = min(crop_h, h)

        # Compute crop origin centered on target point
        x1 = cx * w - crop_w / 2
        y1 = cy * h - crop_h / 2

        # Clamp to frame boundaries
        x1 = max(0, min(x1, w - crop_w))
        y1 = max(0, min(y1, h - crop_h))
        x2 = x1 + crop_w
        y2 = y1 + crop_h

        # Crop and resize back to original dimensions
        cropped = frame[int(y1):int(y2), int(x1):int(x2)]
        output = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LANCZOS4)

        return output
