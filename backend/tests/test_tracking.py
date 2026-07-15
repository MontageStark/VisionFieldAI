"""Tests for the tracking service with ByteTrack multi-object tracking."""
from __future__ import annotations

import threading
import time
from typing import Any, Dict, List
from unittest.mock import MagicMock

import numpy as np
import pytest

from app.services.tracking.sorter import (
    ByteTrackSort,
    KalmanBoxTracker,
    Track,
    TrackState,
    iou_distance,
)
from app.services.tracking.tracking_service import TrackingConfig, TrackingService


class FakeKalmanBoxTracker:
    """Test double for KalmanBoxTracker with predictable behavior."""

    _instance_count = 0

    def __init__(self, bbox: tuple = (0.0, 0.0, 100.0, 100.0)) -> None:
        FakeKalmanBoxTracker._instance_count += 1
        self._id = FakeKalmanBoxTracker._instance_count
        self._bbox = bbox
        self._mean = np.zeros(8, dtype=np.float32)
        self._mean[:4] = [50.0, 50.0, 1.0, 100.0]
        self._call_count = 0

    @property
    def id(self) -> int:
        return self._id

    @property
    def mean(self) -> np.ndarray:
        return self._mean.copy()

    @property
    def covariance(self) -> np.ndarray:
        return np.eye(8, dtype=np.float32) * 1e3

    def predict(self) -> tuple:
        self._call_count += 1
        return self._mean.copy(), np.eye(8, dtype=np.float32) * 1e3

    def update(self, bbox: tuple, confidence: float = 1.0) -> None:
        self._bbox = bbox
        self._call_count += 1

    def get_bbox(self) -> tuple:
        return self._bbox

    def get_velocity(self) -> tuple:
        return (0.0, 0.0)

    @property
    def call_count(self) -> int:
        return self._call_count


@pytest.fixture
def mock_event_bus():
    """Create a mock event bus."""
    bus = MagicMock()
    bus.publish = MagicMock()
    bus.subscribe = MagicMock()
    bus.unsubscribe = MagicMock()
    return bus


@pytest.fixture
def tracking_config(mock_event_bus) -> TrackingConfig:
    return TrackingConfig(
        max_time_lost=30,
        min_hits_tentative=3,
        min_hits_confirmed=3,
        iou_threshold=0.3,
        second_iou_threshold=0.5,
        event_bus=mock_event_bus,
    )


@pytest.fixture
def sample_detections() -> List[Dict[str, Any]]:
    return [
        {
            "class_id": 0,
            "class_name": "person",
            "confidence": 0.95,
            "bbox": [10.0, 20.0, 50.0, 80.0],
        },
        {
            "class_id": 0,
            "class_name": "person",
            "confidence": 0.88,
            "bbox": [100.0, 120.0, 150.0, 200.0],
        },
    ]


class TestTrackState:
    def test_track_state_values(self) -> None:
        assert TrackState.TENTATIVE.value == "tentative"
        assert TrackState.CONFIRMED.value == "confirmed"
        assert TrackState.LOST.value == "lost"


class TestTrack:
    def test_creates_track_with_defaults(self) -> None:
        track = Track(track_id=1, class_id=0, class_name="person")
        assert track.track_id == 1
        assert track.state == TrackState.TENTATIVE
        assert track.hits == 0
        assert track.age == 0
        assert track.time_since_update == 0

    def test_creates_track_with_custom_values(self) -> None:
        track = Track(
            track_id=5,
            class_id=2,
            class_name="car",
            state=TrackState.CONFIRMED,
            bbox=(10.0, 20.0, 50.0, 60.0),
            confidence=0.9,
            hits=10,
        )
        assert track.track_id == 5
        assert track.state == TrackState.CONFIRMED
        assert track.bbox == (10.0, 20.0, 50.0, 60.0)
        assert track.confidence == 0.9
        assert track.hits == 10

    def test_to_dict(self) -> None:
        track = Track(
            track_id=1,
            class_id=0,
            class_name="person",
            state=TrackState.CONFIRMED,
            bbox=(10.0, 20.0, 50.0, 80.0),
            confidence=0.95,
            hits=5,
            age=10,
            velocity=(1.0, 2.0),
        )
        d = track.to_dict()
        assert d["track_id"] == 1
        assert d["class_id"] == 0
        assert d["class_name"] == "person"
        assert d["state"] == "confirmed"
        assert d["bbox"] == (10.0, 20.0, 50.0, 80.0)
        assert d["confidence"] == 0.95
        assert d["hits"] == 5
        assert d["age"] == 10
        assert d["velocity"] == (1.0, 2.0)


class TestKalmanBoxTracker:
    def test_constructs_with_bbox(self) -> None:
        tracker = KalmanBoxTracker((10.0, 20.0, 50.0, 60.0))
        assert tracker.id == 1
        mean = tracker.mean
        assert len(mean) == 8
        assert mean[0] == pytest.approx(30.0)
        assert mean[1] == pytest.approx(40.0)

    def test_predict_returns_mean_and_covariance(self) -> None:
        tracker = KalmanBoxTracker((10.0, 20.0, 50.0, 60.0))
        mean, cov = tracker.predict()
        assert mean.shape == (8,)
        assert cov.shape == (8, 8)

    def test_update_modifies_state(self) -> None:
        tracker = KalmanBoxTracker((10.0, 20.0, 50.0, 60.0))
        tracker.update((15.0, 25.0, 55.0, 65.0), confidence=0.9)
        bbox = tracker.get_bbox()
        assert bbox[0] == pytest.approx(15.0, abs=5.0)

    def test_instance_count_increments(self) -> None:
        KalmanBoxTracker._instance_count = 0
        t1 = KalmanBoxTracker((0, 0, 10, 10))
        t2 = KalmanBoxTracker((0, 0, 20, 20))
        assert t1.id == 1
        assert t2.id == 2


class TestIOUDistance:
    def test_iou_identical_boxes(self) -> None:
        boxes = [(10.0, 10.0, 50.0, 50.0), (10.0, 10.0, 50.0, 50.0)]
        dist = iou_distance(boxes, boxes)
        assert dist[0, 1] == pytest.approx(0.0, abs=0.01)

    def test_iou_no_overlap(self) -> None:
        boxes1 = [(0.0, 0.0, 10.0, 10.0)]
        boxes2 = [(100.0, 100.0, 110.0, 110.0)]
        dist = iou_distance(boxes1, boxes2)
        assert dist[0, 0] == pytest.approx(1.0, abs=0.01)

    def test_iou_partial_overlap(self) -> None:
        boxes1 = [(0.0, 0.0, 50.0, 50.0)]
        boxes2 = [(25.0, 25.0, 75.0, 75.0)]
        dist = iou_distance(boxes1, boxes2)
        assert dist[0, 0] > 0.0
        assert dist[0, 0] < 1.0

    def test_iou_empty_inputs(self) -> None:
        dist = iou_distance([], [])
        assert dist.shape == (0, 0)


class TestByteTrackSort:
    def test_initialization(self) -> None:
        tracker = ByteTrackSort()
        assert tracker.frame_count == 0
        assert tracker.tracks == []

    def test_update_with_empty_detections(self) -> None:
        tracker = ByteTrackSort()
        tracks = tracker.update([])
        assert tracks == []

    def test_update_creates_tentative_tracks(self) -> None:
        tracker = ByteTrackSort(
            max_time_lost=30,
            min_hits_tentative=3,
            min_hits_confirmed=3,
        )
        detections = [
            ((10.0, 20.0, 50.0, 80.0), 0, "person", 0.95),
        ]
        tracks = tracker.update(detections)
        assert len(tracks) == 1
        assert tracks[0].state == TrackState.TENTATIVE
        assert tracks[0].track_id == 1

    def test_multiple_updates_confirm_track(self) -> None:
        tracker = ByteTrackSort(
            max_time_lost=30,
            min_hits_tentative=2,
            min_hits_confirmed=2,
        )
        detections = [
            ((10.0, 20.0, 50.0, 80.0), 0, "person", 0.95),
        ]
        tracker.update(detections)
        tracker.update(detections)
        tracks = tracker.update(detections)
        assert len(tracks) == 1
        assert tracks[0].state == TrackState.CONFIRMED

    def test_track_continuity_same_object(self) -> None:
        tracker = ByteTrackSort(
            iou_threshold=0.5,
            min_hits_tentative=1,
        )
        detections = [
            ((10.0, 20.0, 50.0, 80.0), 0, "person", 0.95),
        ]
        for _ in range(5):
            tracks = tracker.update(detections)
        assert len(tracks) == 1
        assert tracks[0].track_id == 1
        assert tracks[0].hits == 5

    def test_different_objects_get_different_ids(self) -> None:
        tracker = ByteTrackSort(
            min_hits_tentative=1,
        )
        dets1 = [((10.0, 20.0, 50.0, 80.0), 0, "person", 0.95)]
        dets2 = [((100.0, 120.0, 150.0, 200.0), 0, "person", 0.95)]
        tracks1 = tracker.update(dets1)
        tracks2 = tracker.update(dets2)
        assert tracks1[0].track_id == 1
        assert tracks2[0].track_id == 2

    def test_tracking_catches_lost_tracks(self) -> None:
        tracker = ByteTrackSort(
            max_time_lost=2,
            min_hits_tentative=1,
        )
        detections = [((10.0, 20.0, 50.0, 80.0), 0, "person", 0.95)]
        tracker.update(detections)
        tracker.update(detections)
        tracks = tracker.update([])
        assert tracks == []

    def test_reset_clears_state(self) -> None:
        tracker = ByteTrackSort()
        detections = [((10.0, 20.0, 50.0, 80.0), 0, "person", 0.95)]
        tracker.update(detections)
        assert len(tracker.tracks) == 1
        tracker.reset()
        assert tracker.tracks == []
        assert tracker.frame_count == 0

    def test_velocity_estimation(self) -> None:
        tracker = ByteTrackSort(min_hits_tentative=1)
        dets1 = [((10.0, 20.0, 50.0, 80.0), 0, "person", 0.95)]
        dets2 = [((15.0, 25.0, 55.0, 85.0), 0, "person", 0.95)]
        tracker.update(dets1)
        tracks = tracker.update(dets2)
        assert len(tracks) == 1


class TestTrackingServiceInit:
    def test_init_from_explicit_config(self, tracking_config) -> None:
        svc = TrackingService(config=tracking_config)
        assert svc.is_running is False
        assert svc.tracker is not None

    def test_init_defaults(self) -> None:
        svc = TrackingService()
        assert svc.is_running is False
        config = svc.get_config()
        assert config.max_time_lost == 30

    def test_start_stop(self) -> None:
        svc = TrackingService()
        assert not svc.is_running
        svc.start()
        assert svc.is_running
        svc.stop()
        assert not svc.is_running

    def test_stats_initialized(self, tracking_config) -> None:
        svc = TrackingService(config=tracking_config)
        stats = svc.stats
        assert stats["frames_processed"] == 0
        assert stats["tracks_updated"] == 0
        assert stats["events_published"] == 0
        assert stats["errors"] == 0


class TestTrackingServiceProcess:
    def test_process_empty_detections(self, tracking_config) -> None:
        svc = TrackingService(config=tracking_config)
        tracks = svc.process_detections([], sequence=1)
        assert tracks == []

    def test_process_creates_tracks(self, tracking_config, sample_detections) -> None:
        svc = TrackingService(config=tracking_config)
        tracks = svc.process_detections(sample_detections, sequence=1)
        assert len(tracks) == 2
        assert tracks[0].track_id == 1
        assert tracks[1].track_id == 2

    def test_process_increments_stats(self, tracking_config, sample_detections) -> None:
        svc = TrackingService(config=tracking_config)
        svc.process_detections(sample_detections, sequence=1)
        svc.process_detections(sample_detections, sequence=2)
        stats = svc.stats
        assert stats["frames_processed"] == 2
        assert stats["last_sequence"] == 2

    def test_process_tracks_same_object(self, tracking_config) -> None:
        svc = TrackingService(config=tracking_config)
        detections = [
            {"class_id": 0, "class_name": "person", "confidence": 0.95, "bbox": [10, 20, 50, 80]},
        ]
        for i in range(3):
            tracks = svc.process_detections(detections, sequence=i)
        assert len(tracks) == 1
        assert tracks[0].track_id == 1

    def test_get_active_tracks(self, tracking_config, sample_detections) -> None:
        svc = TrackingService(config=tracking_config)
        svc.process_detections(sample_detections, sequence=1)
        active = svc.get_active_tracks()
        assert len(active) == 2
        assert active[0]["track_id"] == 1


class TestTrackingServicePublish:
    def test_publish_tracks_calls_event_bus(self, tracking_config, mock_event_bus, sample_detections) -> None:
        svc = TrackingService(config=tracking_config)
        tracks = svc.process_detections(sample_detections, sequence=1)
        svc.publish_tracks(tracks, sequence=1)
        mock_event_bus.publish.assert_called_once()

    def test_publish_format(self, tracking_config, mock_event_bus, sample_detections) -> None:
        svc = TrackingService(config=tracking_config)
        tracks = svc.process_detections(sample_detections, sequence=1)
        svc.publish_tracks(tracks, sequence=1)
        call_kwargs = mock_event_bus.publish.call_args[1]
        assert "data" in call_kwargs
        published_data = call_kwargs["data"]
        assert "tracks" in published_data
        assert "track_count" in published_data
        assert published_data["track_count"] == 2
        assert published_data["tracks"][0]["class_name"] == "person"

    def test_publish_no_event_bus(self, mock_event_bus) -> None:
        config = TrackingConfig(event_bus=None)
        svc = TrackingService(config=config)
        detections = [
            {"class_id": 0, "class_name": "person", "confidence": 0.95, "bbox": [10, 20, 50, 80]},
        ]
        tracks = svc.process_detections(detections, sequence=1)
        svc.publish_tracks(tracks, sequence=1)
        assert svc.stats["events_published"] == 0


class TestTrackingServiceEvents:
    def test_subscribes_to_detections_complete(self, tracking_config, mock_event_bus) -> None:
        svc = TrackingService(config=tracking_config)
        mock_event_bus.subscribe.assert_called()
        subscribe_calls = mock_event_bus.subscribe.call_args_list
        event_types = [call[0][0].value for call in subscribe_calls]
        assert "vision.detections_complete" in event_types


class TestTrackingServiceReset:
    def test_reset_clears_tracker(self, tracking_config, sample_detections) -> None:
        svc = TrackingService(config=tracking_config)
        svc.process_detections(sample_detections, sequence=1)
        assert len(svc.get_active_tracks()) == 2
        svc.reset()
        assert svc.get_active_tracks() == []
        stats = svc.stats
        assert stats["frames_processed"] == 0


class TestTrackingConfig:
    def test_config_constructs_with_defaults(self) -> None:
        config = TrackingConfig()
        assert config.max_time_lost == 30
        assert config.min_hits_tentative == 3
        assert config.iou_threshold == 0.3
        assert config.event_bus is None

    def test_config_constructs_with_all_params(self) -> None:
        bus = MagicMock()
        config = TrackingConfig(
            max_time_lost=60,
            min_hits_tentative=5,
            min_hits_confirmed=5,
            iou_threshold=0.4,
            second_iou_threshold=0.6,
            event_bus=bus,
        )
        assert config.max_time_lost == 60
        assert config.min_hits_tentative == 5
        assert config.iou_threshold == 0.4
        assert config.second_iou_threshold == 0.6
        assert config.event_bus is bus