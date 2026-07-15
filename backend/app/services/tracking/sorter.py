"""ByteTrack SORT tracker wrapper for multi-object tracking."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.optimize import linear_sum_assignment

logger = logging.getLogger(__name__)


class TrackState(str, Enum):
    """Track lifecycle states."""

    TENTATIVE = "tentative"
    CONFIRMED = "confirmed"
    LOST = "lost"


@dataclass
class Track:
    """Single object track with state machine."""

    track_id: int
    class_id: int
    class_name: str
    state: TrackState = TrackState.TENTATIVE
    bbox: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    confidence: float = 0.0
    hits: int = 0
    age: int = 0
    time_since_update: int = 0
    velocity: Tuple[float, float] = (0.0, 0.0)
    features: List[np.ndarray] = field(default_factory=list)
    mean: Optional[np.ndarray] = None
    covariance: Optional[np.ndarray] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize track to dictionary."""
        return {
            "track_id": self.track_id,
            "class_id": self.class_id,
            "class_name": self.class_name,
            "state": self.state.value,
            "bbox": self.bbox,
            "confidence": self.confidence,
            "hits": self.hits,
            "age": self.age,
            "time_since_update": self.time_since_update,
            "velocity": self.velocity,
        }


class KalmanBoxTracker:
    """Kalman filter for bounding box tracking.

    State vector: [x, y, a, h, vx, vy, va, vh]
    where (x, y) is center, a is aspect ratio, h is height,
    and v* are velocities.
    """

    _instance_count: int = 0

    def __init__(self, bbox: Tuple[float, float, float, float]) -> None:
        """Initialize Kalman filter with detection bbox.

        Args:
            bbox: Detection bbox (x1, y1, x2, y2)
        """
        KalmanBoxTracker._instance_count += 1
        self._id = KalmanBoxTracker._instance_count

        self._mean = np.zeros(8, dtype=np.float32)
        self._covariance = np.eye(8, dtype=np.float32) * 1e3

        x1, y1, x2, y2 = bbox
        x = (x1 + x2) / 2
        y = (y1 + y2) / 2
        w = x2 - x1
        h = y2 - y1
        a = w / h if h > 0 else 1.0

        self._mean[:4] = [x, y, a, h]

        self._motion_mat = np.eye(8, dtype=np.float32)
        for i in range(4):
            self._motion_mat[i, i + 4] = 1.0

        self._update_mat = np.eye(4, dtype=np.float32)
        self._observation_mat = np.zeros((4, 8), dtype=np.float32)
        self._observation_mat[0, 0] = 1  # x
        self._observation_mat[1, 1] = 1  # y
        self._observation_mat[2, 2] = 1  # a
        self._observation_mat[3, 3] = 1  # h

        self._std_weight_pos: float = 1.0 / 20
        self._std_weight_vel: float = 1.0 / 160

    @property
    def id(self) -> int:
        return self._id

    @property
    def mean(self) -> np.ndarray:
        return self._mean.copy()

    @property
    def covariance(self) -> np.ndarray:
        return self._covariance.copy()

    def predict(self) -> Tuple[np.ndarray, np.ndarray]:
        """Predict next state using motion model.

        Returns:
            Tuple of (predicted_mean, predicted_covariance)
        """
        dt = 1.0
        for i in range(4):
            self._motion_mat[i, i + 4] = dt

        q_pos = self._std_weight_pos * self._std_weight_pos
        q_vel = self._std_weight_vel * self._std_weight_vel

        self._covariance[
            np.diag_indices(4)
        ] += np.array([q_pos, q_pos, q_pos, q_pos], dtype=np.float32) * dt**4
        self._covariance[
            4:, 4:
        ] += np.eye(4, dtype=np.float32) * q_vel * dt**4

        self._mean = self._motion_mat @ self._mean
        self._covariance = self._motion_mat @ self._covariance @ self._motion_mat.T

        return self._mean, self._covariance

    def update(
        self, bbox: Tuple[float, float, float, float], confidence: float = 1.0
    ) -> None:
        """Update filter with detection.

        Args:
            bbox: Detection bbox (x1, y1, x2, y2)
            confidence: Detection confidence
        """
        x1, y1, x2, y2 = bbox
        x = (x1 + x2) / 2
        y = (y1 + y2) / 2
        w = x2 - x1
        h = y2 - y1
        a = w / h if h > 0 else 1.0

        z = np.array([x, y, a, h], dtype=np.float32)

        self._std_weight_pos = 1.0 / (20 * (confidence + 1e-5))
        self._std_weight_vel = 1.0 / (160 * (confidence + 1e-5))

        r = np.zeros(4, dtype=np.float32)
        r[:2] = self._std_weight_pos**2
        r[2:4] = self._std_weight_pos**2
        r[2] *= w**2 if w > 0 else 1.0
        r[3] *= h**2 if h > 0 else 1.0

        H = self._observation_mat
        P = self._covariance
        R = np.diag(r)

        S = H @ P @ H.T + R
        K = P @ H.T @ np.linalg.inv(S)

        y_diff = z - H @ self._mean

        self._mean = self._mean + K @ y_diff
        self._covariance = (np.eye(8, dtype=np.float32) - K @ H) @ P

    def get_bbox(self) -> Tuple[float, float, float, float]:
        """Get current bbox estimate.

        Returns:
            bbox (x1, y1, x2, y2)
        """
        x, y, a, h = self._mean[:4]
        w = a * h
        x1 = x - w / 2
        y1 = y - h / 2
        x2 = x + w / 2
        y2 = y + h / 2
        return (float(x1), float(y1), float(x2), float(y2))

    def get_velocity(self) -> Tuple[float, float]:
        """Get current velocity estimate.

        Returns:
            Tuple of (vx, vy)
        """
        return (float(self._mean[4]), float(self._mean[5]))


def iou_distance(
    boxes1: List[Tuple[float, float, float, float]],
    boxes2: List[Tuple[float, float, float, float]],
) -> np.ndarray:
    """Compute IOU distance matrix between two sets of boxes.

    Args:
        boxes1: First set of bboxes (x1, y1, x2, y2)
        boxes2: Second set of bboxes (x1, y1, x2, y2)

    Returns:
        Distance matrix (1 - IOU)
    """
    n = len(boxes1)
    m = len(boxes2)
    if n == 0 or m == 0:
        return np.zeros((n, m), dtype=np.float32)

    dist = np.zeros((n, m), dtype=np.float32)

    for i, b1 in enumerate(boxes1):
        x1_1, y1_1, x2_1, y2_1 = b1
        area1 = max(0.0, x2_1 - x1_1) * max(0.0, y2_1 - y1_1)

        for j, b2 in enumerate(boxes2):
            x1_2, y1_2, x2_2, y2_2 = b2
            area2 = max(0.0, x2_2 - x1_2) * max(0.0, y2_2 - y1_2)

            xi1 = max(x1_1, x1_2)
            yi1 = max(y1_1, y1_2)
            xi2 = min(x2_1, x2_2)
            yi2 = min(y2_1, y2_2)

            inter_area = max(0.0, xi2 - xi1) * max(0.0, yi2 - yi1)
            union_area = area1 + area2 - inter_area

            iou = inter_area / union_area if union_area > 0 else 0.0
            dist[i, j] = 1.0 - iou

    return dist


class ByteTrackSort:
    """ByteTrack SORT multi-object tracker.

    Implements a simplified ByteTrack algorithm with:
    - Kalman filter for motion prediction
    - Two-stage association (high confidence then low confidence)
    - Track state machine (tentative -> confirmed -> lost)
    """

    def __init__(
        self,
        max_time_lost: int = 30,
        min_hits_tentative: int = 3,
        min_hits_confirmed: int = 3,
        iou_threshold: float = 0.3,
        second_iou_threshold: float = 0.5,
    ) -> None:
        """Initialize ByteTrack SORT tracker.

        Args:
            max_time_lost: Max frames without update before track is lost
            min_hits_tentative: Min hits to transition tentative -> confirmed
            min_hits_confirmed: Min hits to confirm track
            iou_threshold: IOU threshold for first association
            second_iou_threshold: IOU threshold for second association
        """
        self._max_time_lost = max_time_lost
        self._min_hits_tentative = min_hits_tentative
        self._min_hits_confirmed = min_hits_confirmed
        self._iou_threshold = iou_threshold
        self._second_iou_threshold = second_iou_threshold

        self._tracks: List[Track] = []
        self._trackers: List[KalmanBoxTracker] = []
        self._next_id: int = 1

        self._frame_count: int = 0

    @property
    def tracks(self) -> List[Track]:
        """Get list of active tracks."""
        return list(self._tracks)

    @property
    def frame_count(self) -> int:
        return self._frame_count

    def update(
        self,
        detections: List[Tuple[Tuple[float, float, float, float], int, str, float]],
    ) -> List[Track]:
        """Update tracker with new detections.

        Args:
            detections: List of (bbox, class_id, class_name, confidence)

        Returns:
            List of updated tracks
        """
        self._frame_count += 1

        for track in self._tracks:
            track.age += 1
            track.time_since_update += 1

        self._predict()

        matched, unmatched_dets, unmatched_tracks = self._associate(detections)

        for det_idx, track_idx in matched:
            self._tracks[track_idx].time_since_update = 0
            bbox, class_id, class_name, confidence = detections[det_idx]
            self._trackers[track_idx].update(bbox, confidence)
            self._tracks[track_idx].hits += 1
            self._tracks[track_idx].bbox = bbox
            self._tracks[track_idx].confidence = confidence
            self._tracks[track_idx].velocity = self._trackers[track_idx].get_velocity()

            if (
                self._tracks[track_idx].state == TrackState.TENTATIVE
                and self._tracks[track_idx].hits >= self._min_hits_tentative
            ):
                self._tracks[track_idx].state = TrackState.CONFIRMED

        unmatched_dets_high: List[int] = []
        unmatched_dets_low: List[int] = []

        for det_idx in unmatched_dets:
            _, _, _, conf = detections[det_idx]
            if conf >= 0.5:
                unmatched_dets_high.append(det_idx)
            else:
                unmatched_dets_low.append(det_idx)

        if unmatched_tracks and unmatched_dets_low:
            second_matches, second_unmatched_dets, second_unmatched_tracks = self._associate_single(
                detections, unmatched_tracks, unmatched_dets_low, self._second_iou_threshold
            )

            for det_idx, track_idx in second_matches:
                unmatched_dets_low.remove(det_idx)
                unmatched_tracks.remove(track_idx)

            for track_idx in second_unmatched_tracks:
                if self._tracks[track_idx].state == TrackState.TENTATIVE:
                    self._tracks[track_idx].state = TrackState.LOST

        for det_idx in unmatched_dets_high:
            bbox, class_id, class_name, confidence = detections[det_idx]
            self._create_track(bbox, class_id, class_name, confidence)

        for track_idx in unmatched_tracks:
            if self._tracks[track_idx].state != TrackState.LOST:
                self._tracks[track_idx].state = TrackState.LOST

        self._tracks = [t for t in self._tracks if t.state != TrackState.LOST]
        self._trackers = [
            self._trackers[i]
            for i, t in enumerate(self._tracks)
            if t.state != TrackState.LOST
        ]

        active_tracks = [t for t in self._tracks if t.time_since_update <= self._max_time_lost]

        return active_tracks

    def _predict(self) -> None:
        """Predict next state for all trackers."""
        for tracker in self._trackers:
            tracker.predict()

    def _associate(
        self,
        detections: List[Tuple[Tuple[float, float, float, float], int, str, float]],
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """First stage association.

        Returns:
            Tuple of (matched_indices, unmatched_det_indices, unmatched_track_indices)
        """
        if not self._tracks or not detections:
            return [], list(range(len(detections))), list(range(len(self._tracks)))

        det_boxes = [d[0] for d in detections]
        track_boxes = [t.bbox for t in self._tracks]

        cost_matrix = iou_distance(det_boxes, track_boxes)

        det_indices = list(range(len(detections)))
        track_indices = list(range(len(self._tracks)))

        matched_indices: List[Tuple[int, int]] = []
        unmatched_det_indices: List[int] = []
        unmatched_track_indices: List[int] = []

        if cost_matrix.size > 0:
            det_ind, track_ind = linear_sum_assignment(cost_matrix)

            for d, t in zip(det_ind, track_ind):
                if cost_matrix[d, t] <= self._iou_threshold:
                    matched_indices.append((d, t))
                    det_indices.remove(d)
                    track_indices.remove(t)

        unmatched_det_indices = det_indices
        unmatched_track_indices = track_indices

        return matched_indices, unmatched_det_indices, unmatched_track_indices

    def _associate_single(
        self,
        detections: List[Tuple[Tuple[float, float, float, float], int, str, float]],
        unmatched_tracks: List[int],
        unmatched_dets: List[int],
        threshold: float,
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """Second stage association for unmatched tracks and detections.

        Returns:
            Tuple of (matched_indices, unmatched_det_indices, unmatched_track_indices)
        """
        if not unmatched_tracks or not unmatched_dets:
            return [], unmatched_dets, unmatched_tracks

        det_boxes = [detections[i][0] for i in unmatched_dets]
        track_boxes = [self._tracks[i].bbox for i in unmatched_tracks]

        cost_matrix = iou_distance(det_boxes, track_boxes)

        matched_indices: List[Tuple[int, int]] = []
        remaining_dets = list(unmatched_dets)
        remaining_tracks = list(unmatched_tracks)

        if cost_matrix.size > 0:
            det_ind, track_ind = linear_sum_assignment(cost_matrix)

            for d, t in zip(det_ind, track_ind):
                if cost_matrix[d, t] <= threshold:
                    matched_indices.append((unmatched_dets[d], unmatched_tracks[t]))
                    if unmatched_dets[d] in remaining_dets:
                        remaining_dets.remove(unmatched_dets[d])
                    if unmatched_tracks[t] in remaining_tracks:
                        remaining_tracks.remove(unmatched_tracks[t])

        return matched_indices, remaining_dets, remaining_tracks

    def _create_track(
        self,
        bbox: Tuple[float, float, float, float],
        class_id: int,
        class_name: str,
        confidence: float,
    ) -> None:
        """Create new track for unmatched detection.

        Args:
            bbox: Detection bbox
            class_id: Class ID
            class_name: Class name
            confidence: Detection confidence
        """
        tracker = KalmanBoxTracker(bbox)
        track = Track(
            track_id=self._next_id,
            class_id=class_id,
            class_name=class_name,
            state=TrackState.TENTATIVE,
            bbox=bbox,
            confidence=confidence,
            hits=1,
            age=0,
            time_since_update=0,
            velocity=(0.0, 0.0),
        )
        self._next_id += 1
        self._tracks.append(track)
        self._trackers.append(tracker)

    def reset(self) -> None:
        """Reset tracker state."""
        self._tracks.clear()
        self._trackers.clear()
        self._frame_count = 0
        KalmanBoxTracker._instance_count = 0
        self._next_id = 1