"""Tests for the vision service with YOLO11 object detection."""
from __future__ import annotations

import threading
import time
from typing import List
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from backend.app.config.settings import AISettings
from app.services.vision.detector import Detection, YOLO11Detector
from app.services.vision.vision_service import VisionConfig, VisionService


class FakeYOLO11Detector:
    """Test double for YOLO11Detector with deterministic fake detections."""

    def __init__(
        self,
        simulation_mode: bool = False,
        device: str = "cpu",
        confidence_threshold: float = 0.5,
        detect_count: int = 2,
    ) -> None:
        self._simulation_mode = simulation_mode
        self._device = device
        self._confidence_threshold = confidence_threshold
        self._detect_count = detect_count
        self._call_count = 0
        self._calls: List[np.ndarray] = []

    def detect(self, image: np.ndarray) -> List[Detection]:
        self._call_count += 1
        self._calls.append(image.copy())
        if self._simulation_mode:
            return []
        return [
            Detection(
                class_id=i % 80,
                class_name=f"class_{i}",
                confidence=0.5 + (i * 0.1),
                bbox=(10.0 + i, 20.0 + i, 50.0 + i, 60.0 + i),
            )
            for i in range(self._detect_count)
        ]

    @property
    def simulation_mode(self) -> bool:
        return self._simulation_mode

    @property
    def device(self) -> str:
        return self._device

    @property
    def confidence_threshold(self) -> float:
        return self._confidence_threshold

    def update_confidence(self, threshold: float) -> None:
        self._confidence_threshold = threshold

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
def ai_settings() -> AISettings:
    return AISettings(
        model_name="yolo11n.pt",
        confidence_threshold=0.5,
        device="cpu",
        max_detections=100,
    )


@pytest.fixture
def vision_config(mock_event_bus) -> VisionConfig:
    return VisionConfig(
        model_name="yolo11n.pt",
        confidence_threshold=0.5,
        device="cpu",
        max_detections=100,
        simulation_mode=True,
        event_bus=mock_event_bus,
    )


@pytest.fixture
def fake_detector() -> FakeYOLO11Detector:
    return FakeYOLO11Detector(simulation_mode=False, detect_count=2)


@pytest.fixture
def sample_frame() -> np.ndarray:
    return np.zeros((480, 640, 3), dtype=np.uint8)


class TestYOLO11Detector:
    def test_constructs_with_defaults(self) -> None:
        det = YOLO11Detector()
        assert det.simulation_mode is True
        assert det.device == "cuda"
        assert det.confidence_threshold == 0.5

    def test_constructs_with_custom_params(self) -> None:
        det = YOLO11Detector(
            model_name="yolo11s.pt",
            confidence_threshold=0.7,
            device="cpu",
            simulation_mode=True,
            max_detections=50,
        )
        assert det.device == "cpu"
        assert det.confidence_threshold == 0.7

    def test_detect_in_simulation_mode_returns_empty(self) -> None:
        det = YOLO11Detector(simulation_mode=True)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = det.detect(frame)
        assert result == []

    def test_update_confidence_clamped_to_valid_range(self) -> None:
        det = YOLO11Detector(confidence_threshold=0.5)
        det.update_confidence(1.5)
        assert det.confidence_threshold == 1.0
        det.update_confidence(-0.5)
        assert det.confidence_threshold == 0.0
        det.update_confidence(0.75)
        assert det.confidence_threshold == 0.75

    def test_preprocess_returns_array_and_meta(self) -> None:
        det = YOLO11Detector(simulation_mode=True)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        processed, meta = det.preprocess(frame)
        assert processed.ndim == 4
        assert "original_shape" in meta or "shape" in meta
        assert "scale" in meta or "original_shape" in meta


class TestDetection:
    def test_creates_detection(self) -> None:
        det = Detection(
            class_id=0,
            class_name="ball",
            confidence=0.95,
            bbox=(10.0, 20.0, 50.0, 60.0),
        )
        assert det.class_id == 0
        assert det.class_name == "ball"
        assert det.confidence == 0.95
        assert det.bbox == (10.0, 20.0, 50.0, 60.0)
        assert det.track_id is None

    def test_detection_with_track_id(self) -> None:
        det = Detection(
            class_id=1,
            class_name="person",
            confidence=0.88,
            bbox=(15.0, 25.0, 55.0, 65.0),
            track_id=42,
        )
        assert det.track_id == 42


class TestVisionServiceInit:
    def test_init_from_ai_settings(self, ai_settings, mock_event_bus) -> None:
        svc = VisionService(ai_settings=ai_settings)
        assert svc.detector.device == "cpu"
        assert svc.detector.confidence_threshold == 0.5

    def test_init_from_explicit_config(self, vision_config) -> None:
        svc = VisionService(config=vision_config)
        assert svc.detector.device == "cpu"
        assert svc.detector.simulation_mode is True

    def test_init_defaults_to_simulation(self) -> None:
        svc = VisionService()
        assert svc.detector.simulation_mode is True
        assert svc.detector.device == "cuda"

    def test_start_stop(self) -> None:
        svc = VisionService()
        assert not svc.is_running
        svc.start()
        assert svc.is_running
        svc.stop()
        assert not svc.is_running

    def test_double_start_is_idempotent(self) -> None:
        svc = VisionService()
        svc.start()
        svc.start()
        assert svc.is_running
        svc.stop()

    def test_stats_initialized(self, vision_config) -> None:
        svc = VisionService(config=vision_config)
        stats = svc.stats
        assert stats["frames_processed"] == 0
        assert stats["detections_published"] == 0
        assert stats["errors"] == 0


class TestVisionServiceProcessFrame:
    def test_process_frame_returns_detections(
        self, vision_config, fake_detector, sample_frame
    ) -> None:
        svc = VisionService(config=vision_config)
        svc._detector = fake_detector

        detections = svc.process_frame(sample_frame, sequence=1)

        assert len(detections) == 2
        assert fake_detector.call_count == 1
        assert detections[0].class_name == "class_0"

    def test_process_frame_increments_stats(
        self, vision_config, fake_detector, sample_frame
    ) -> None:
        svc = VisionService(config=vision_config)
        svc._detector = fake_detector

        svc.process_frame(sample_frame, sequence=1)
        svc.process_frame(sample_frame, sequence=2)

        stats = svc.stats
        assert stats["frames_processed"] == 2
        assert stats["last_sequence"] == 2

    def test_process_frame_handles_exception(
        self, vision_config, sample_frame
    ) -> None:
        svc = VisionService(config=vision_config)
        svc._detector = None

        detections = svc.process_frame(sample_frame, sequence=1)

        assert detections == []
        assert svc.stats["errors"] == 1


class TestVisionServicePublish:
    def test_publish_detections_calls_event_bus(
        self, vision_config, mock_event_bus
    ) -> None:
        svc = VisionService(config=vision_config)

        detections = [
            Detection(
                class_id=0,
                class_name="ball",
                confidence=0.95,
                bbox=(10.0, 20.0, 50.0, 60.0),
            ),
        ]

        svc.publish_detections(detections, sequence=1)

        mock_event_bus.publish.assert_called_once()
        call_kwargs = mock_event_bus.publish.call_args[1]
        assert "data" in call_kwargs
        published_data = call_kwargs["data"]
        assert "detections" in published_data
        assert len(published_data["detections"]) == 1
        assert published_data["detections"][0]["class_name"] == "ball"

    def test_publish_detections_no_event_bus(self, vision_config) -> None:
        vision_config.event_bus = None
        svc = VisionService(config=vision_config)

        detections = [
            Detection(
                class_id=0,
                class_name="ball",
                confidence=0.95,
                bbox=(10.0, 20.0, 50.0, 60.0),
            ),
        ]

        svc.publish_detections(detections, sequence=1)
        assert svc.stats["detections_published"] == 0


class TestVisionServiceEvents:
    def test_subscribes_to_frame_captured(self, vision_config, mock_event_bus) -> None:
        svc = VisionService(config=vision_config)

        mock_event_bus.subscribe.assert_called()
        subscribe_calls = mock_event_bus.subscribe.call_args_list
        assert len(subscribe_calls) > 0

    def test_updates_confidence_at_runtime(self, vision_config) -> None:
        svc = VisionService(config=vision_config)
        assert svc.detector.confidence_threshold == 0.5

        svc.update_confidence(0.8)
        assert svc.detector.confidence_threshold == 0.8


class TestVisionServiceGetConfig:
    def test_get_config_returns_current_config(self, vision_config) -> None:
        svc = VisionService(config=vision_config)
        config = svc.get_config()
        assert config.model_name == "yolo11n.pt"
        assert config.device == "cpu"
        assert config.confidence_threshold == 0.5
        assert config.simulation_mode is True


class TestFakeDetector:
    def test_fake_detector_returns_deterministic_detections(self) -> None:
        det = FakeYOLO11Detector(detect_count=3, simulation_mode=False)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        results = det.detect(frame)

        assert len(results) == 3
        assert results[0].class_name == "class_0"
        assert results[1].class_name == "class_1"
        assert results[2].confidence == pytest.approx(0.7, abs=0.01)

    def test_fake_detector_simulation_returns_empty(self) -> None:
        det = FakeYOLO11Detector(simulation_mode=True)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        results = det.detect(frame)

        assert results == []

    def test_fake_detector_tracks_calls(self) -> None:
        det = FakeYOLO11Detector(simulation_mode=False)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        det.detect(frame)
        det.detect(frame)

        assert det.call_count == 2


class TestVisionConfig:
    def test_config_constructs_with_defaults(self) -> None:
        config = VisionConfig(
            model_name="yolo11n.pt",
            confidence_threshold=0.5,
            device="cuda",
            max_detections=100,
        )
        assert config.simulation_mode is False
        assert config.max_vram_gb == 2.0
        assert config.event_bus is None

    def test_config_constructs_with_all_params(self) -> None:
        bus = MagicMock()
        config = VisionConfig(
            model_name="yolo11s.pt",
            confidence_threshold=0.7,
            device="cpu",
            max_detections=50,
            simulation_mode=True,
            max_vram_gb=4.0,
            event_bus=bus,
        )
        assert config.model_name == "yolo11s.pt"
        assert config.device == "cpu"
        assert config.simulation_mode is True
        assert config.max_vram_gb == 4.0
        assert config.event_bus is bus