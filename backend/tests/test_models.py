"""Tests for Pydantic models."""
import pytest
from pydantic import ValidationError

from app.models.detection import BoundingBox, Detection, DetectionResult
from app.models.track import Track, TrackState, TrackHistory
from app.models.director import DirectorDecision, DirectorMode
from app.models.camera_state import CameraState
from app.models.motion import ServoCommand, ServoPosition, MotionPlan, MotionProfile
from app.models.safety import SafetyCheck, SafetyViolation, EmergencyStop, SafetyViolationType, SafetySeverity
from app.models.events import Event, EventType, EventPriority
from app.models.health import HealthStatus, ComponentHealth, SystemHealth


class TestBoundingBox:
    def test_valid_bbox(self):
        bbox = BoundingBox(x1=0.1, y1=0.2, x2=0.8, y2=0.9, confidence=0.95)
        assert bbox.x1 == 0.1
        assert bbox.y2 == 0.9
        assert bbox.width == pytest.approx(0.7)
        assert bbox.height == pytest.approx(0.7)
        assert bbox.center_x == pytest.approx(0.45)
        assert bbox.center_y == pytest.approx(0.55)
        assert bbox.area == pytest.approx(0.49)

    def test_invalid_coordinates_negative(self):
        with pytest.raises(ValidationError):
            BoundingBox(x1=-0.1, y1=0.0, x2=0.5, y2=0.5, confidence=0.9)

    def test_invalid_coordinates_above_one(self):
        with pytest.raises(ValidationError):
            BoundingBox(x1=0.0, y1=0.0, x2=1.5, y2=0.5, confidence=0.9)

    def test_x2_less_than_x1(self):
        with pytest.raises(ValidationError):
            BoundingBox(x1=0.8, y1=0.0, x2=0.2, y2=0.5, confidence=0.9)

    def test_y2_less_than_y1(self):
        with pytest.raises(ValidationError):
            BoundingBox(x1=0.0, y1=0.8, x2=0.5, y2=0.2, confidence=0.9)

    def test_invalid_confidence(self):
        with pytest.raises(ValidationError):
            BoundingBox(x1=0.0, y1=0.0, x2=0.5, y2=0.5, confidence=1.5)


class TestDetection:
    def test_valid_detection(self):
        bbox = BoundingBox(x1=0.1, y1=0.2, x2=0.3, y2=0.4, confidence=0.9)
        det = Detection(label="ball", bbox=bbox, confidence=0.85, timestamp=1000.0, frame_number=1)
        assert det.label == "ball"
        assert det.frame_number == 1

    def test_invalid_label(self):
        bbox = BoundingBox(x1=0.0, y1=0.0, x2=0.5, y2=0.5, confidence=0.9)
        with pytest.raises(ValidationError):
            Detection(label="invalid", bbox=bbox, confidence=0.8, timestamp=1000.0, frame_number=1)

    def test_valid_labels(self):
        bbox = BoundingBox(x1=0.0, y1=0.0, x2=0.5, y2=0.5, confidence=0.9)
        for label in ["ball", "player", "goalkeeper", "referee"]:
            det = Detection(label=label, bbox=bbox, confidence=0.8, timestamp=1000.0, frame_number=1)
            assert det.label == label


class TestDetectionResult:
    def test_empty_result(self):
        result = DetectionResult(frame_number=1, timestamp=1000.0)
        assert result.detection_count == 0
        assert result.ball_detection is None
        assert result.player_detections == []

    def test_with_detections(self):
        bbox = BoundingBox(x1=0.1, y1=0.2, x2=0.3, y2=0.4, confidence=0.9)
        ball = Detection(label="ball", bbox=bbox, confidence=0.9, timestamp=1000.0, frame_number=1)
        player = Detection(label="player", bbox=bbox, confidence=0.8, timestamp=1000.0, frame_number=1)
        result = DetectionResult(frame_number=1, timestamp=1000.0, detections=[ball, player])
        assert result.detection_count == 2
        assert result.ball_detection == ball
        assert len(result.player_detections) == 1


class TestTrackState:
    def test_states(self):
        assert TrackState.TENTATIVE == "tentative"
        assert TrackState.CONFIRMED == "confirmed"
        assert TrackState.LOST == "lost"


class TestTrack:
    def test_valid_track(self):
        bbox = BoundingBox(x1=0.1, y1=0.2, x2=0.3, y2=0.4, confidence=0.9)
        track = Track(
            track_id=1, label="player", state=TrackState.CONFIRMED,
            bbox=bbox, age=10, hits=8, time_since_update=0
        )
        assert track.track_id == 1
        assert track.is_active is True
        assert track.speed is None

    def test_with_velocity(self):
        bbox = BoundingBox(x1=0.1, y1=0.2, x2=0.3, y2=0.4, confidence=0.9)
        track = Track(
            track_id=2, label="ball", state=TrackState.CONFIRMED,
            bbox=bbox, age=5, hits=5, time_since_update=1,
            velocity=(2.0, 3.0)
        )
        assert track.speed == pytest.approx(3.605551275463989)

    def test_inactive_tentative(self):
        bbox = BoundingBox(x1=0.1, y1=0.2, x2=0.3, y2=0.4, confidence=0.9)
        track = Track(
            track_id=3, label="player", state=TrackState.TENTATIVE,
            bbox=bbox, age=1, hits=1, time_since_update=0
        )
        assert track.is_active is False


class TestTrackHistory:
    def test_valid_history(self):
        history = TrackHistory(
            track_id=1, label="ball",
            positions=[(0.1, 0.2), (0.3, 0.4)],
            timestamps=[1000.0, 1001.0]
        )
        assert history.length == 2
        assert history.last_position == (0.3, 0.4)

    def test_unsorted_timestamps(self):
        with pytest.raises(ValidationError):
            TrackHistory(
                track_id=1, label="ball",
                positions=[(0.1, 0.2)],
                timestamps=[1002.0, 1001.0]
            )


class TestDirectorMode:
    def test_modes(self):
        assert DirectorMode.BROADCAST == "broadcast"
        assert DirectorMode.AGGRESSIVE == "aggressive"
        assert DirectorMode.WIDE == "wide"
        assert DirectorMode.TRAINING == "training"
        assert DirectorMode.MANUAL_ASSIST == "manual_assist"


class TestDirectorDecision:
    def test_valid_decision(self):
        target = CameraState(
            center_x=0.5, center_y=0.5, zoom=1.5,
            motion_profile=MotionProfile.BROADCAST,
            confidence=0.85, timestamp=1000.0,
        )
        decision = DirectorDecision(
            mode=DirectorMode.BROADCAST, target=target,
            reasoning="Tracking ball", confidence=0.85, timestamp=1000.0
        )
        assert decision.mode == DirectorMode.BROADCAST
        assert decision.tracking_track_id is None

    def test_empty_reasoning(self):
        target = CameraState(
            center_x=0.5, center_y=0.5, zoom=1.5,
            motion_profile=MotionProfile.BROADCAST,
            confidence=0.85, timestamp=1000.0,
        )
        with pytest.raises(ValidationError):
            DirectorDecision(
                mode=DirectorMode.BROADCAST, target=target,
                reasoning="  ", confidence=0.85, timestamp=1000.0
            )


class TestServoCommand:
    def test_valid_command(self):
        cmd = ServoCommand(target_angle=90.0, timestamp=1000.0)
        assert cmd.target_angle == 90.0
        assert cmd.speed == 90.0

    def test_invalid_angle(self):
        with pytest.raises(ValidationError):
            ServoCommand(target_angle=200.0, timestamp=1000.0)


class TestServoPosition:
    def test_valid_position(self):
        pos = ServoPosition(current_angle=90.0, target_angle=90.0, timestamp=1000.0)
        assert pos.current_angle == 90.0
        assert pos.status == "OK"


class TestMotionPlan:
    def test_valid_plan(self):
        plan = MotionPlan(
            profile=MotionProfile.BROADCAST,
            waypoints=[90.0, 95.0, 93.0],
            durations=[0.1, 0.1],
            total_duration=0.2, max_speed=120.0, max_acceleration=200.0,
            timestamp=1000.0
        )
        assert plan.waypoint_count == 3

    def test_empty_waypoints(self):
        with pytest.raises(ValidationError):
            MotionPlan(
                profile=MotionProfile.BROADCAST,
                waypoints=[], durations=[],
                total_duration=0.0, max_speed=120.0, max_acceleration=200.0,
                timestamp=1000.0
            )


class TestSafetyCheck:
    def test_passed_check(self):
        check = SafetyCheck(passed=True, message="OK")
        assert check.passed is True
        assert check.violation_type is None

    def test_failed_check(self):
        check = SafetyCheck(
            passed=False, violation_type=SafetyViolationType.ANGLE_EXCEEDED,
            severity=SafetySeverity.WARNING, message="Angle clamped",
            original_angle=200.0, clamped_angle=180.0
        )
        assert check.passed is False
        assert check.clamped_angle == 180.0


class TestSafetyViolation:
    def test_valid_violation(self):
        violation = SafetyViolation(
            violation_type=SafetyViolationType.WATCHDOG,
            severity=SafetySeverity.CRITICAL,
            message="Watchdog timeout", timestamp=1000.0,
            action_taken="emergency_stop"
        )
        assert violation.severity == SafetySeverity.CRITICAL


class TestEmergencyStop:
    def test_valid_stop(self):
        stop = EmergencyStop(reason="Button pressed", timestamp=1000.0)
        assert stop.servo_locked is True
        assert stop.requires_manual_reset is True


class TestEventType:
    def test_event_types(self):
        assert EventType.STATE_CHANGED == "state.changed"
        assert EventType.DETECTIONS_COMPLETE == "vision.detections_complete"
        assert EventType.EMERGENCY_STOP == "safety.emergency_stop"


class TestEventPriority:
    def test_priorities(self):
        assert EventPriority.NORMAL < EventPriority.HIGH < EventPriority.CRITICAL


class TestEvent:
    def test_valid_event(self):
        event = Event(
            event_type=EventType.STATE_CHANGED,
            data={"old": "idle", "new": "tracking"},
            timestamp=1000.0, source="state_machine"
        )
        assert event.event_type == EventType.STATE_CHANGED
        assert event.priority == EventPriority.NORMAL

    def test_critical_event(self):
        event = Event(
            event_type=EventType.EMERGENCY_STOP,
            priority=EventPriority.CRITICAL,
            timestamp=1000.0
        )
        assert event.priority == EventPriority.CRITICAL


class TestHealthStatus:
    def test_statuses(self):
        assert HealthStatus.GREEN == "green"
        assert HealthStatus.YELLOW == "yellow"
        assert HealthStatus.RED == "red"


class TestComponentHealth:
    def test_healthy_component(self):
        comp = ComponentHealth(name="gpu", status=HealthStatus.GREEN, timestamp=1000.0)
        assert comp.is_healthy is True

    def test_unhealthy_component(self):
        comp = ComponentHealth(name="gpu", status=HealthStatus.RED, timestamp=1000.0, message="Overheated")
        assert comp.is_healthy is False


class TestSystemHealth:
    def test_healthy_system(self):
        comp1 = ComponentHealth(name="gpu", status=HealthStatus.GREEN, timestamp=1000.0)
        comp2 = ComponentHealth(name="cpu", status=HealthStatus.GREEN, timestamp=1000.0)
        health = SystemHealth(
            status=HealthStatus.GREEN, components={"gpu": comp1, "cpu": comp2},
            timestamp=1000.0
        )
        assert health.unhealthy_components == []
        assert health.critical_components == []

    def test_system_with_issues(self):
        comp1 = ComponentHealth(name="gpu", status=HealthStatus.YELLOW, timestamp=1000.0)
        comp2 = ComponentHealth(name="cpu", status=HealthStatus.RED, timestamp=1000.0)
        health = SystemHealth(
            status=HealthStatus.RED, components={"gpu": comp1, "cpu": comp2},
            timestamp=1000.0
        )
        assert "gpu" in health.unhealthy_components
        assert "cpu" in health.critical_components
