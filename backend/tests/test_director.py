"""Tests for the Director Service - cinematic decision engine."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

import pytest

from app.core.events import EventType
from app.services.director.shot_composer import (
    CameraAction,
    CameraMove,
    DirectorMode,
    FieldZone,
    ShotComposer,
    ShotComposition,
    ShotType,
)


class TestDirectorMode:
    def test_director_mode_values(self) -> None:
        assert DirectorMode.BROADCAST.value == "broadcast"
        assert DirectorMode.AGGRESSIVE.value == "aggressive"
        assert DirectorMode.WIDE.value == "wide"
        assert DirectorMode.TRAINING.value == "training"
        assert DirectorMode.MANUAL_ASSIST.value == "manual_assist"

    def test_all_modes_defined(self) -> None:
        assert len(DirectorMode) == 5


class TestShotType:
    def test_shot_type_values(self) -> None:
        assert ShotType.CLOSE_UP.value == "close_up"
        assert ShotType.MEDIUM.value == "medium"
        assert ShotType.WIDE.value == "wide"
        assert ShotType.OVER_SHOULDER.value == "over_shoulder"
        assert ShotType.TRACKING.value == "tracking"
        assert ShotType.STATIC.value == "static"

    def test_all_shot_types_defined(self) -> None:
        assert len(ShotType) == 6


class TestFieldZone:
    def test_field_zone_values(self) -> None:
        assert FieldZone.LEFT.value == "left"
        assert FieldZone.CENTER.value == "center"
        assert FieldZone.RIGHT.value == "right"
        assert FieldZone.DEFENSE.value == "defense"
        assert FieldZone.OFFENSE.value == "offense"
        assert FieldZone.GOAL.value == "goal"

    def test_all_zones_defined(self) -> None:
        assert len(FieldZone) == 6


class TestCameraAction:
    def test_camera_action_values(self) -> None:
        assert CameraAction.PAN.value == "pan"
        assert CameraAction.TILT.value == "tilt"
        assert CameraAction.ZOOM_IN.value == "zoom_in"
        assert CameraAction.ZOOM_OUT.value == "zoom_out"
        assert CameraAction.TRACK.value == "track"
        assert CameraAction.HOLD.value == "hold"

    def test_all_actions_defined(self) -> None:
        assert len(CameraAction) == 6


class TestCameraMove:
    def test_camera_move_constructs(self) -> None:
        move = ShotComposition(
            center_x=0.5,
            center_y=0.5,
            zoom=1.5,
            action=CameraAction.PAN,
            shot_type=ShotType.TRACKING,
            confidence=0.9,
        )
        assert move.center_x == 0.5
        assert move.center_y == 0.5
        assert move.zoom == 1.5
        assert move.action == CameraAction.PAN
        assert move.shot_type == ShotType.TRACKING
        assert move.confidence == 0.9

    def test_camera_move_defaults(self) -> None:
        move = ShotComposition()
        assert move.center_x == 0.5
        assert move.center_y == 0.5
        assert move.zoom == 1.5
        assert move.action == CameraAction.HOLD
        assert move.shot_type == ShotType.STATIC
        assert move.confidence == 0.0

    def test_camera_move_to_dict(self) -> None:
        move = ShotComposition(
            center_x=0.6,
            center_y=0.4,
            zoom=1.2,
            action=CameraAction.TILT,
            shot_type=ShotType.MEDIUM,
            confidence=0.85,
        )
        d = move.to_dict()
        assert d["center_x"] == 0.6
        assert d["center_y"] == 0.4
        assert d["zoom"] == 1.2
        assert d["action"] == "tilt"
        assert d["shot_type"] == "medium"
        assert d["confidence"] == 0.85


class TestShotComposer:
    def test_shot_composer_initialization(self) -> None:
        composer = ShotComposer()
        assert composer.mode == DirectorMode.BROADCAST

    def test_shot_composer_with_mode(self) -> None:
        composer = ShotComposer(mode=DirectorMode.AGGRESSIVE)
        assert composer.mode == DirectorMode.AGGRESSIVE

    def test_set_mode(self) -> None:
        composer = ShotComposer()
        composer.set_mode(DirectorMode.WIDE)
        assert composer.mode == DirectorMode.WIDE

    def test_compute_weighted_centroid_single_player(self) -> None:
        composer = ShotComposer()
        tracks = [
            {"track_id": 1, "class_name": "person", "bbox": [100, 100, 150, 200], "confidence": 0.9},
        ]
        centroid = composer.compute_weighted_centroid(tracks)
        assert centroid is not None
        assert len(centroid) == 2

    def test_compute_weighted_centroid_multiple_players(self) -> None:
        composer = ShotComposer()
        tracks = [
            {"track_id": 1, "class_name": "person", "bbox": [100, 100, 150, 200], "confidence": 0.9},
            {"track_id": 2, "class_name": "person", "bbox": [200, 100, 250, 200], "confidence": 0.8},
        ]
        centroid = composer.compute_weighted_centroid(tracks)
        assert centroid is not None

    def test_compute_weighted_centroid_with_ball(self) -> None:
        composer = ShotComposer()
        tracks = [
            {"track_id": 1, "class_name": "person", "bbox": [100, 100, 150, 200], "confidence": 0.9},
            {"track_id": 2, "class_name": "ball", "bbox": [175, 150, 185, 160], "confidence": 0.95},
        ]
        centroid = composer.compute_weighted_centroid(tracks)
        assert centroid is not None
        ball_x = (175 + 185) / 2
        ball_y = (150 + 160) / 2
        assert abs(centroid[0] - ball_x) < abs(centroid[0] - 125)

    def test_compute_weighted_centroid_empty_tracks(self) -> None:
        composer = ShotComposer()
        centroid = composer.compute_weighted_centroid([])
        assert centroid is None

    def test_compute_weighted_centroid_excludes_irrelevant_classes(self) -> None:
        composer = ShotComposer()
        tracks = [
            {"track_id": 1, "class_name": "person", "bbox": [100, 100, 150, 200], "confidence": 0.9},
            {"track_id": 2, "class_name": "ball", "bbox": [175, 150, 185, 160], "confidence": 0.95},
            {"track_id": 3, "class_name": "goalkeeper", "bbox": [50, 100, 100, 200], "confidence": 0.85},
            {"track_id": 4, "class_name": "referee", "bbox": [300, 100, 350, 200], "confidence": 0.8},
        ]
        centroid = composer.compute_weighted_centroid(tracks)
        assert centroid is not None

    def test_get_field_zone_center(self) -> None:
        composer = ShotComposer()
        zone = composer.get_field_zone(320, 240, 640, 480)
        assert zone == FieldZone.CENTER

    def test_get_field_zone_left(self) -> None:
        composer = ShotComposer()
        zone = composer.get_field_zone(100, 240, 640, 480)
        assert zone == FieldZone.LEFT

    def test_get_field_zone_right(self) -> None:
        composer = ShotComposer()
        zone = composer.get_field_zone(540, 240, 640, 480)
        assert zone == FieldZone.RIGHT

    def test_get_field_zone_defense(self) -> None:
        composer = ShotComposer()
        zone = composer.get_field_zone(320, 400, 640, 480)
        assert zone == FieldZone.DEFENSE

    def test_get_field_zone_offense(self) -> None:
        composer = ShotComposer()
        zone = composer.get_field_zone(320, 80, 640, 480)
        assert zone == FieldZone.OFFENSE

    def test_get_zoom_level_wide_mode(self) -> None:
        composer = ShotComposer(mode=DirectorMode.WIDE)
        zoom = composer.get_zoom_level(FieldZone.CENTER, 2)
        assert zoom > 1.0

    def test_get_zoom_level_aggressive_mode(self) -> None:
        aggressive_composer = ShotComposer(mode=DirectorMode.AGGRESSIVE)
        broadcast_composer = ShotComposer(mode=DirectorMode.BROADCAST)
        aggressive_zoom = aggressive_composer.get_zoom_level(FieldZone.CENTER, 2)
        broadcast_zoom = broadcast_composer.get_zoom_level(FieldZone.CENTER, 2)
        assert aggressive_zoom > broadcast_zoom

    def test_get_zoom_level_broadcast_mode(self) -> None:
        composer = ShotComposer(mode=DirectorMode.BROADCAST)
        zoom = composer.get_zoom_level(FieldZone.CENTER, 2)
        assert 1.0 <= zoom <= 3.0

    def test_get_zoom_level_more_players_closer(self) -> None:
        composer = ShotComposer()
        zoom_few = composer.get_zoom_level(FieldZone.CENTER, 2)
        zoom_many = composer.get_zoom_level(FieldZone.CENTER, 11)
        assert zoom_many < zoom_few

    def test_compose_shot_returns_camera_move(self) -> None:
        composer = ShotComposer()
        tracks = [
            {"track_id": 1, "class_name": "person", "bbox": [100, 100, 150, 200], "confidence": 0.9},
        ]
        move = composer.compose_shot(tracks, 640, 480)
        assert isinstance(move, CameraMove)
        assert move.zoom >= 1.0

    def test_compose_shot_broadcast_mode(self) -> None:
        composer = ShotComposer(mode=DirectorMode.BROADCAST)
        tracks = [
            {"track_id": 1, "class_name": "person", "bbox": [100, 100, 150, 200], "confidence": 0.9},
        ]
        move = composer.compose_shot(tracks, 640, 480)
        assert move.shot_type in [ShotType.MEDIUM, ShotType.WIDE, ShotType.OVER_SHOULDER]

    def test_compose_shot_aggressive_mode(self) -> None:
        composer = ShotComposer(mode=DirectorMode.AGGRESSIVE)
        tracks = [
            {"track_id": 1, "class_name": "person", "bbox": [100, 100, 150, 200], "confidence": 0.9},
        ]
        move = composer.compose_shot(tracks, 640, 480)
        assert move.shot_type in [ShotType.CLOSE_UP, ShotType.TRACKING]

    def test_compose_shot_wide_mode(self) -> None:
        composer = ShotComposer(mode=DirectorMode.WIDE)
        tracks = [
            {"track_id": 1, "class_name": "person", "bbox": [100, 100, 150, 200], "confidence": 0.9},
        ]
        move = composer.compose_shot(tracks, 640, 480)
        assert move.shot_type == ShotType.WIDE
        assert move.zoom >= 1.0

    def test_compose_shot_training_mode(self) -> None:
        composer = ShotComposer(mode=DirectorMode.TRAINING)
        tracks = [
            {"track_id": 1, "class_name": "person", "bbox": [100, 100, 150, 200], "confidence": 0.9},
        ]
        move = composer.compose_shot(tracks, 640, 480)
        assert move.shot_type in [ShotType.MEDIUM, ShotType.OVER_SHOULDER, ShotType.WIDE]

    def test_compose_shot_manual_assist_mode(self) -> None:
        composer = ShotComposer(mode=DirectorMode.MANUAL_ASSIST)
        tracks = [
            {"track_id": 1, "class_name": "person", "bbox": [100, 100, 150, 200], "confidence": 0.9},
        ]
        move = composer.compose_shot(tracks, 640, 480)
        assert isinstance(move, CameraMove)

    def test_compose_shot_empty_tracks(self) -> None:
        composer = ShotComposer()
        move = composer.compose_shot([], 640, 480)
        assert isinstance(move, CameraMove)
        assert move.action == CameraAction.HOLD

    def test_generate_camera_actions_pan(self) -> None:
        composer = ShotComposer()
        actions = composer.generate_camera_actions(50, 0, 640)
        assert CameraAction.PAN in actions

    def test_generate_camera_actions_tilt(self) -> None:
        composer = ShotComposer()
        actions = composer.generate_camera_actions(0, 30, 480)
        assert CameraAction.TILT in actions

    def test_generate_camera_actions_zoom_in(self) -> None:
        composer = ShotComposer()
        actions = composer.generate_camera_actions(0, 0, 2)
        assert CameraAction.ZOOM_IN in actions

    def test_generate_camera_actions_zoom_out(self) -> None:
        composer = ShotComposer()
        actions = composer.generate_camera_actions(0, 0, 10)
        assert CameraAction.ZOOM_OUT in actions

    def test_generate_camera_actions_track(self) -> None:
        composer = ShotComposer()
        actions = composer.generate_camera_actions(50, 10, 400)
        assert CameraAction.TRACK in actions

    def test_generate_camera_actions_hold_small_movement(self) -> None:
        composer = ShotComposer()
        actions = composer.generate_camera_actions(5, 3, 5)
        assert CameraAction.HOLD in actions

    def test_smooth_camera_move_first_move(self) -> None:
        composer = ShotComposer()
        smoothed = composer.smooth_camera_move(None, 0.6, 0.4, 1.5)
        assert smoothed.center_x == 0.6
        assert smoothed.center_y == 0.4
        assert smoothed.zoom == 1.5

    def test_smooth_camera_move_subsequent_moves(self) -> None:
        composer = ShotComposer()
        prev = ShotComposition(center_x=0.5, center_y=0.5, zoom=1.5)
        smoothed = composer.smooth_camera_move(prev, 0.7, 0.6, 1.8)
        assert smoothed.center_x <= 0.7
        assert smoothed.center_y <= 0.6


class TestDirectorServiceIntegration:
    """Tests for DirectorService with event bus integration."""

    @pytest.fixture
    def mock_event_bus(self):
        bus = MagicMock()
        bus.publish = MagicMock()
        bus.subscribe = MagicMock()
        bus.unsubscribe = MagicMock()
        return bus

    @pytest.fixture
    def sample_tracks(self):
        return [
            {
                "track_id": 1,
                "class_name": "person",
                "bbox": [100.0, 100.0, 150.0, 200.0],
                "confidence": 0.95,
            },
            {
                "track_id": 2,
                "class_name": "ball",
                "bbox": [175.0, 150.0, 185.0, 160.0],
                "confidence": 0.9,
            },
        ]

    def test_director_service_init(self, mock_event_bus) -> None:
        from app.services.director.director_service import DirectorConfig, DirectorService

        config = DirectorConfig(event_bus=mock_event_bus)
        svc = DirectorService(config=config)
        assert svc.is_running is False
        mock_event_bus.subscribe.assert_called()

    def test_director_service_subscribes_to_tracking_updated(self, mock_event_bus) -> None:
        from app.services.director.director_service import DirectorConfig, DirectorService

        config = DirectorConfig(event_bus=mock_event_bus)
        svc = DirectorService(config=config)
        subscribe_calls = mock_event_bus.subscribe.call_args_list
        event_types = [call[0][0].value for call in subscribe_calls]
        assert EventType.TRACKING_UPDATED.value in event_types

    def test_director_service_publishes_decision(self, mock_event_bus, sample_tracks) -> None:
        from app.services.director.director_service import DirectorConfig, DirectorService

        config = DirectorConfig(event_bus=mock_event_bus)
        svc = DirectorService(config=config)
        event = MagicMock()
        event.data = {"tracks": sample_tracks, "sequence": 1}
        svc._on_tracking_updated(event)
        mock_event_bus.publish.assert_called()

    def test_director_service_publishes_camera_move(self, mock_event_bus, sample_tracks) -> None:
        from app.services.director.director_service import DirectorConfig, DirectorService

        config = DirectorConfig(event_bus=mock_event_bus)
        svc = DirectorService(config=config)
        event = MagicMock()
        event.data = {"tracks": sample_tracks, "sequence": 1}
        svc._on_tracking_updated(event)
        publish_calls = mock_event_bus.publish.call_args_list
        event_types = [call[0][0].value for call in publish_calls]
        assert EventType.CAMERA_STATE_UPDATED.value in event_types

    def test_director_service_respects_mode(self, mock_event_bus) -> None:
        from app.services.director.director_service import DirectorConfig, DirectorService

        config = DirectorConfig(
            event_bus=mock_event_bus, mode=DirectorMode.AGGRESSIVE
        )
        svc = DirectorService(config=config)
        assert svc.get_mode() == DirectorMode.AGGRESSIVE

    def test_director_service_set_mode(self, mock_event_bus) -> None:
        from app.services.director.director_service import DirectorConfig, DirectorService

        config = DirectorConfig(event_bus=mock_event_bus)
        svc = DirectorService(config=config)
        svc.set_mode(DirectorMode.WIDE)
        assert svc.get_mode() == DirectorMode.WIDE

    def test_director_service_process_frame(self, mock_event_bus, sample_tracks) -> None:
        from app.services.director.director_service import DirectorConfig, DirectorService

        config = DirectorConfig(event_bus=mock_event_bus)
        svc = DirectorService(config=config)
        svc.process_frame(sample_tracks, sequence=1)
        assert mock_event_bus.publish.called

    def test_director_service_publishes_director_decision_event(
        self, mock_event_bus, sample_tracks
    ) -> None:
        from app.services.director.director_service import DirectorConfig, DirectorService

        config = DirectorConfig(event_bus=mock_event_bus)
        svc = DirectorService(config=config)
        svc.process_frame(sample_tracks, sequence=1)
        publish_calls = mock_event_bus.publish.call_args_list
        event_types = [call[0][0].value for call in publish_calls]
        assert EventType.DIRECTOR_DECISION.value in event_types

    def test_director_service_empty_tracks(self, mock_event_bus) -> None:
        from app.services.director.director_service import DirectorConfig, DirectorService

        config = DirectorConfig(event_bus=mock_event_bus)
        svc = DirectorService(config=config)
        svc.process_frame([], sequence=1)
        assert mock_event_bus.publish.called

    def test_director_service_start_stop(self, mock_event_bus) -> None:
        from app.services.director.director_service import DirectorConfig, DirectorService

        config = DirectorConfig(event_bus=mock_event_bus)
        svc = DirectorService(config=config)
        assert not svc.is_running
        svc.start()
        assert svc.is_running
        svc.stop()
        assert not svc.is_running

    def test_director_service_stats(self, mock_event_bus, sample_tracks) -> None:
        from app.services.director.director_service import DirectorConfig, DirectorService

        config = DirectorConfig(event_bus=mock_event_bus)
        svc = DirectorService(config=config)
        svc.process_frame(sample_tracks, sequence=1)
        stats = svc.stats
        assert "frames_processed" in stats
        assert stats["frames_processed"] == 1

    def test_director_service_reset(self, mock_event_bus, sample_tracks) -> None:
        from app.services.director.director_service import DirectorConfig, DirectorService

        config = DirectorConfig(event_bus=mock_event_bus)
        svc = DirectorService(config=config)
        svc.process_frame(sample_tracks, sequence=1)
        svc.reset()
        stats = svc.stats
        assert stats["frames_processed"] == 0

    def test_director_config_defaults(self) -> None:
        from app.services.director.director_service import DirectorConfig

        config = DirectorConfig()
        assert config.mode == DirectorMode.BROADCAST
        assert config.event_bus is None

    def test_director_config_full(self, mock_event_bus) -> None:
        from app.services.director.director_service import DirectorConfig

        config = DirectorConfig(
            mode=DirectorMode.WIDE,
            event_bus=mock_event_bus,
            frame_width=1920,
            frame_height=1080,
        )
        assert config.mode == DirectorMode.WIDE
        assert config.event_bus is mock_event_bus
        assert config.frame_width == 1920
        assert config.frame_height == 1080