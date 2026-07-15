"""Tests for the prediction service with Kalman filter."""
from __future__ import annotations

import time
from typing import Any, Dict, List
from unittest.mock import MagicMock

import numpy as np
import pytest

from app.services.prediction.kalman_filter import KalmanFilter2D, motion_compensated_predict
from app.services.prediction.prediction_service import PredictionConfig, PredictionService


@pytest.fixture
def mock_event_bus():
    """Create a mock event bus."""
    bus = MagicMock()
    bus.publish = MagicMock()
    bus.subscribe = MagicMock()
    bus.unsubscribe = MagicMock()
    return bus


@pytest.fixture
def prediction_config(mock_event_bus) -> PredictionConfig:
    return PredictionConfig(
        prediction_horizon=10,
        process_noise=1.0,
        measurement_noise=1.0,
        smoothing_factor=0.5,
        min_confidence=0.3,
        event_bus=mock_event_bus,
    )


@pytest.fixture
def ball_tracks() -> List[Dict[str, Any]]:
    return [
        {
            "track_id": 1,
            "class_id": 32,
            "class_name": "sports_ball",
            "confidence": 0.95,
            "bbox": [100.0, 200.0, 120.0, 220.0],
        },
        {
            "track_id": 2,
            "class_id": 0,
            "class_name": "person",
            "confidence": 0.90,
            "bbox": [50.0, 100.0, 80.0, 200.0],
        },
    ]


class TestKalmanFilter2DInit:
    def test_creates_filter_with_defaults(self) -> None:
        kf = KalmanFilter2D()
        assert kf.is_initialized() is False
        state = kf.get_state()
        assert len(state) == 4
        assert np.all(state == 0)

    def test_creates_filter_with_custom_noise(self) -> None:
        kf = KalmanFilter2D(process_noise=2.0, measurement_noise=0.5)
        assert kf.is_initialized() is False

    def test_creates_filter_with_initial_state(self) -> None:
        initial_state = np.array([10.0, 20.0, 1.0, 2.0], dtype=np.float32)
        kf = KalmanFilter2D(initial_state=initial_state)
        assert kf.is_initialized() is True
        state = kf.get_state()
        assert state[0] == pytest.approx(10.0)
        assert state[1] == pytest.approx(20.0)


class TestKalmanFilter2DInitialize:
    def test_initialize_sets_state(self) -> None:
        kf = KalmanFilter2D()
        kf.initialize(100.0, 200.0, vx=5.0, vy=-3.0)
        assert kf.is_initialized() is True
        pos = kf.get_position()
        assert pos == (100.0, 200.0)
        vel = kf.get_velocity()
        assert vel == (5.0, -3.0)

    def test_initialize_with_zero_velocity(self) -> None:
        kf = KalmanFilter2D()
        kf.initialize(50.0, 75.0)
        vel = kf.get_velocity()
        assert vel == (0.0, 0.0)


class TestKalmanFilter2DPredict:
    def test_predict_returns_state_and_covariance(self) -> None:
        kf = KalmanFilter2D()
        kf.initialize(0.0, 0.0, vx=10.0, vy=5.0)
        state, cov = kf.predict(dt=1.0)
        assert state.shape == (4,)
        assert cov.shape == (4, 4)

    def test_predict_updates_position_with_velocity(self) -> None:
        kf = KalmanFilter2D()
        kf.initialize(0.0, 0.0, vx=10.0, vy=5.0)
        kf.predict(dt=1.0)
        pos = kf.get_position()
        assert pos[0] == pytest.approx(10.0, rel=0.01)
        assert pos[1] == pytest.approx(5.0, rel=0.01)

    def test_predict_preserves_velocity(self) -> None:
        kf = KalmanFilter2D()
        kf.initialize(0.0, 0.0, vx=10.0, vy=5.0)
        kf.predict(dt=1.0)
        vel = kf.get_velocity()
        assert vel == (10.0, 5.0)

    def test_predict_cumulative_with_multiple_steps(self) -> None:
        kf = KalmanFilter2D()
        kf.initialize(0.0, 0.0, vx=10.0, vy=5.0)
        for _ in range(5):
            kf.predict(dt=1.0)
        pos = kf.get_position()
        assert pos[0] == pytest.approx(50.0, rel=0.1)
        assert pos[1] == pytest.approx(25.0, rel=0.1)


class TestKalmanFilter2DUpdate:
    def test_update_modifies_state(self) -> None:
        kf = KalmanFilter2D()
        kf.initialize(0.0, 0.0, vx=0.0, vy=0.0)
        measurement = np.array([100.0, 200.0])
        kf.predict(dt=1.0)
        kf.update(measurement)
        pos = kf.get_position()
        assert pos[0] > 0.0
        assert pos[1] > 0.0

    def test_update_with_noisy_measurement_smooths(self) -> None:
        kf = KalmanFilter2D(process_noise=1.0, measurement_noise=10.0)
        kf.initialize(0.0, 0.0, vx=10.0, vy=0.0)

        noisy_measurements = [
            np.array([12.0, 0.5]),
            np.array([18.0, -0.3]),
            np.array([25.0, 0.8]),
            np.array([31.0, -0.2]),
        ]

        for z in noisy_measurements:
            kf.predict(dt=1.0)
            kf.update(z)

        final_pos = kf.get_position()
        assert final_pos[0] > 20.0
        assert abs(final_pos[1]) < 5.0

    def test_update_with_confidence_weights(self) -> None:
        kf = KalmanFilter2D()
        kf.initialize(0.0, 0.0, vx=0.0, vy=0.0)
        kf.predict(dt=1.0)

        kf.update_with_noise(np.array([100.0, 100.0]), confidence=0.1)
        pos_low = kf.get_position()

        kf.reset()
        kf.initialize(0.0, 0.0, vx=0.0, vy=0.0)
        kf.predict(dt=1.0)
        kf.update_with_noise(np.array([100.0, 100.0]), confidence=1.0)
        pos_high = kf.get_position()

        assert pos_high[0] > pos_low[0]

    def test_update_preserves_covariance_shape(self) -> None:
        kf = KalmanFilter2D()
        kf.initialize(50.0, 50.0)
        kf.predict(dt=1.0)
        _, cov = kf.update(np.array([55.0, 52.0]))
        assert cov.shape == (4, 4)


class TestKalmanFilter2DFuturePrediction:
    def test_predict_future_returns_positions(self) -> None:
        kf = KalmanFilter2D()
        kf.initialize(0.0, 0.0, vx=10.0, vy=5.0)
        future = kf.predict_future(steps=5)
        assert len(future) == 5
        assert all(isinstance(p, tuple) and len(p) == 2 for p in future)

    def test_predict_future_linear_motion(self) -> None:
        kf = KalmanFilter2D()
        kf.initialize(0.0, 0.0, vx=10.0, vy=5.0)
        future = kf.predict_future(steps=3, dt=1.0)
        assert future[0] == pytest.approx((10.0, 5.0), rel=0.01)
        assert future[1] == pytest.approx((20.0, 10.0), rel=0.01)
        assert future[2] == pytest.approx((30.0, 15.0), rel=0.01)

    def test_predict_future_zero_velocity(self) -> None:
        kf = KalmanFilter2D()
        kf.initialize(100.0, 200.0, vx=0.0, vy=0.0)
        future = kf.predict_future(steps=5)
        for pos in future:
            assert pos == (100.0, 200.0)

    def test_predict_future_with_custom_dt(self) -> None:
        kf = KalmanFilter2D()
        kf.initialize(0.0, 0.0, vx=10.0, vy=5.0)
        future = kf.predict_future(steps=2, dt=2.0)
        assert future[0] == pytest.approx((20.0, 10.0), rel=0.01)
        assert future[1] == pytest.approx((40.0, 20.0), rel=0.01)


class TestKalmanFilter2DGetPosition:
    def test_get_position_returns_tuple(self) -> None:
        kf = KalmanFilter2D()
        kf.initialize(123.0, 456.0)
        pos = kf.get_position()
        assert pos == (123.0, 456.0)

    def test_get_position_returns_floats(self) -> None:
        kf = KalmanFilter2D()
        kf.initialize(100, 200)
        pos = kf.get_position()
        assert isinstance(pos[0], float)
        assert isinstance(pos[1], float)


class TestKalmanFilter2DGetVelocity:
    def test_get_velocity_returns_tuple(self) -> None:
        kf = KalmanFilter2D()
        kf.initialize(0.0, 0.0, vx=7.5, vy=-2.3)
        vel = kf.get_velocity()
        assert vel[0] == pytest.approx(7.5)
        assert vel[1] == pytest.approx(-2.3)


class TestKalmanFilter2DReset:
    def test_reset_clears_state(self) -> None:
        kf = KalmanFilter2D()
        kf.initialize(100.0, 200.0, vx=10.0, vy=5.0)
        kf.reset()
        assert kf.is_initialized() is False
        state = kf.get_state()
        assert np.all(state == 0)


class TestMotionCompensatedPredict:
    def test_returns_list_of_positions(self) -> None:
        result = motion_compensated_predict(
            current_state=np.array([0.0, 0.0]),
            velocity=np.array([10.0, 5.0]),
            steps=5,
            dt=1.0,
        )
        assert len(result) == 5

    def test_linear_motion_prediction(self) -> None:
        result = motion_compensated_predict(
            current_state=np.array([0.0, 0.0]),
            velocity=np.array([10.0, 5.0]),
            steps=3,
            dt=1.0,
        )
        assert result[0] == (10.0, 5.0)
        assert result[1] == (20.0, 10.0)
        assert result[2] == (30.0, 15.0)

    def test_zero_velocity_gives_same_position(self) -> None:
        result = motion_compensated_predict(
            current_state=np.array([100.0, 200.0]),
            velocity=np.array([0.0, 0.0]),
            steps=3,
            dt=1.0,
        )
        for pos in result:
            assert pos == (100.0, 200.0)


class TestPredictionServiceInit:
    def test_init_from_explicit_config(self, prediction_config) -> None:
        svc = PredictionService(config=prediction_config)
        assert svc.is_running is False
        assert svc.get_config().prediction_horizon == 10

    def test_init_defaults(self) -> None:
        svc = PredictionService()
        assert svc.is_running is False
        config = svc.get_config()
        assert config.prediction_horizon == 10
        assert config.process_noise == 1.0

    def test_start_stop(self) -> None:
        svc = PredictionService()
        assert not svc.is_running
        svc.start()
        assert svc.is_running
        svc.stop()
        assert not svc.is_running

    def test_stats_initialized(self, prediction_config) -> None:
        svc = PredictionService(config=prediction_config)
        stats = svc.stats
        assert stats["predictions_published"] == 0
        assert stats["filters_created"] == 0


class TestPredictionServiceProcess:
    def test_process_empty_tracks(self, prediction_config) -> None:
        svc = PredictionService(config=prediction_config)
        predictions = svc.process_tracks([], sequence=1)
        assert predictions == []

    def test_process_extracts_ball_tracks(self, prediction_config, ball_tracks) -> None:
        svc = PredictionService(config=prediction_config)
        predictions = svc.process_tracks(ball_tracks, sequence=1)
        assert len(predictions) == 1
        assert predictions[0]["track_id"] == "1"

    def test_process_creates_filter_for_new_track(self, prediction_config, ball_tracks) -> None:
        svc = PredictionService(config=prediction_config)
        svc.process_tracks(ball_tracks, sequence=1)
        assert svc.active_track_count == 1

    def test_process_updates_existing_filter(self, prediction_config, ball_tracks) -> None:
        svc = PredictionService(config=prediction_config)
        svc.process_tracks(ball_tracks, sequence=1)
        svc.process_tracks(ball_tracks, sequence=2)
        svc.process_tracks(ball_tracks, sequence=3)
        assert svc.active_track_count == 1
        assert svc.stats["filters_created"] == 1
        assert svc.stats["filters_updated"] == 2

    def test_process_ignores_non_ball_tracks(self, prediction_config, ball_tracks) -> None:
        svc = PredictionService(config=prediction_config)
        person_track = {
            "track_id": 99,
            "class_id": 0,
            "class_name": "person",
            "confidence": 0.9,
            "bbox": [50.0, 100.0, 80.0, 200.0],
        }
        svc.process_tracks([person_track], sequence=1)
        assert svc.active_track_count == 0

    def test_process_multiple_ball_tracks(self, prediction_config) -> None:
        svc = PredictionService(config=prediction_config)
        tracks = [
            {
                "track_id": 1,
                "class_name": "sports_ball",
                "confidence": 0.9,
                "bbox": [100.0, 200.0, 120.0, 220.0],
            },
            {
                "track_id": 2,
                "class_name": "sports_ball",
                "confidence": 0.9,
                "bbox": [300.0, 400.0, 320.0, 420.0],
            },
        ]
        svc.process_tracks(tracks, sequence=1)
        assert svc.active_track_count == 2

    def test_process_increments_stats(self, prediction_config, ball_tracks) -> None:
        svc = PredictionService(config=prediction_config)
        svc.process_tracks(ball_tracks, sequence=1)
        svc.process_tracks(ball_tracks, sequence=2)
        assert svc.stats["filters_created"] == 1
        assert svc.stats["filters_updated"] == 1


class TestPredictionServiceFuturePositions:
    def test_predict_future_positions_unknown_track(self, prediction_config) -> None:
        svc = PredictionService(config=prediction_config)
        future = svc.predict_future_positions("unknown_track")
        assert future == []

    def test_predict_future_positions_after_processing(self, prediction_config, ball_tracks) -> None:
        svc = PredictionService(config=prediction_config)
        svc.process_tracks(ball_tracks, sequence=1)
        future = svc.predict_future_positions("1")
        assert len(future) == 10

    def test_predict_future_with_custom_steps(self, prediction_config, ball_tracks) -> None:
        svc = PredictionService(config=prediction_config)
        svc.process_tracks(ball_tracks, sequence=1)
        future = svc.predict_future_positions("1", steps=5)
        assert len(future) == 5


class TestPredictionServiceTrackState:
    def test_get_track_state_unknown_track(self, prediction_config) -> None:
        svc = PredictionService(config=prediction_config)
        state = svc.get_track_state("unknown")
        assert state is None

    def test_get_track_state_after_processing(self, prediction_config, ball_tracks) -> None:
        svc = PredictionService(config=prediction_config)
        svc.process_tracks(ball_tracks, sequence=1)
        state = svc.get_track_state("1")
        assert state is not None
        assert "position" in state
        assert "velocity" in state


class TestPredictionServiceRemoveTrack:
    def test_remove_existing_track(self, prediction_config, ball_tracks) -> None:
        svc = PredictionService(config=prediction_config)
        svc.process_tracks(ball_tracks, sequence=1)
        assert svc.active_track_count == 1
        result = svc.remove_track("1")
        assert result is True
        assert svc.active_track_count == 0

    def test_remove_unknown_track(self, prediction_config) -> None:
        svc = PredictionService(config=prediction_config)
        result = svc.remove_track("unknown")
        assert result is False


class TestPredictionServiceClearAll:
    def test_clear_all_tracks(self, prediction_config, ball_tracks) -> None:
        svc = PredictionService(config=prediction_config)
        svc.process_tracks(ball_tracks, sequence=1)
        assert svc.active_track_count == 1
        svc.clear_all_tracks()
        assert svc.active_track_count == 0


class TestPredictionServicePublish:
    def test_publish_calls_event_bus(self, prediction_config, mock_event_bus, ball_tracks) -> None:
        svc = PredictionService(config=prediction_config)
        svc.process_tracks(ball_tracks, sequence=1)
        predictions = svc.process_tracks(ball_tracks, sequence=2)
        svc.publish_predictions(predictions, sequence=2)
        mock_event_bus.publish.assert_called()

    def test_publish_format(self, prediction_config, mock_event_bus, ball_tracks) -> None:
        svc = PredictionService(config=prediction_config)
        svc.process_tracks(ball_tracks, sequence=1)
        predictions = svc.process_tracks(ball_tracks, sequence=2)
        svc.publish_predictions(predictions, sequence=2)
        call_kwargs = mock_event_bus.publish.call_args[1]
        assert "data" in call_kwargs
        published_data = call_kwargs["data"]
        assert "predictions" in published_data
        assert published_data["prediction_count"] == 1

    def test_publish_no_event_bus(self, mock_event_bus) -> None:
        config = PredictionConfig(event_bus=None)
        svc = PredictionService(config=config)
        svc.publish_predictions([], sequence=1)
        assert svc.stats["predictions_published"] == 0


class TestPredictionServiceReset:
    def test_reset_clears_state(self, prediction_config, ball_tracks) -> None:
        svc = PredictionService(config=prediction_config)
        svc.process_tracks(ball_tracks, sequence=1)
        assert svc.active_track_count == 1
        svc.reset()
        assert svc.active_track_count == 0
        stats = svc.stats
        assert stats["filters_created"] == 0
        assert stats["predictions_published"] == 0


class TestPredictionConfig:
    def test_config_constructs_with_defaults(self) -> None:
        config = PredictionConfig()
        assert config.prediction_horizon == 10
        assert config.process_noise == 1.0
        assert config.measurement_noise == 1.0
        assert config.min_confidence == 0.3

    def test_config_constructs_with_all_params(self) -> None:
        bus = MagicMock()
        config = PredictionConfig(
            prediction_horizon=20,
            process_noise=2.0,
            measurement_noise=0.5,
            smoothing_factor=0.7,
            min_confidence=0.5,
            event_bus=bus,
        )
        assert config.prediction_horizon == 20
        assert config.process_noise == 2.0
        assert config.measurement_noise == 0.5
        assert config.smoothing_factor == 0.7
        assert config.min_confidence == 0.5
        assert config.event_bus is bus