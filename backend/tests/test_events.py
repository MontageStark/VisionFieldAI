"""Tests for event bus implementation."""
from __future__ import annotations

import asyncio
import threading
from typing import List
from unittest.mock import MagicMock

import pytest

from backend.app.core.events import (
    Event,
    EventBus,
    EventPriority,
    EventType,
    get_event_bus,
    reset_event_bus,
)


class TestEventType:
    """Test EventType enum."""

    def test_system_events(self):
        assert EventType.STATE_CHANGED == "state.changed"
        assert EventType.ERROR_OCCURRED == "error.occurred"
        assert EventType.HEALTH_CHECK == "health.check"

    def test_camera_events(self):
        assert EventType.FRAME_CAPTURED == "camera.frame_captured"
        assert EventType.CAMERA_CONNECTED == "camera.connected"
        assert EventType.CAMERA_DISCONNECTED == "camera.disconnected"

    def test_vision_events(self):
        assert EventType.DETECTIONS_COMPLETE == "vision.detections_complete"
        assert EventType.TRACKING_UPDATED == "tracking.updated"

    def test_director_events(self):
        assert EventType.DIRECTOR_DECISION == "director.decision"
        assert EventType.CAMERA_MOVE == "director.camera_move"

    def test_servo_events(self):
        assert EventType.SERVO_COMMAND == "servo.command"
        assert EventType.SERVO_POSITION == "servo.position"
        assert EventType.SERVO_ERROR == "servo.error"

    def test_streaming_events(self):
        assert EventType.STREAM_STARTED == "stream.started"
        assert EventType.STREAM_STOPPED == "stream.stopped"
        assert EventType.STREAM_ERROR == "stream.error"

    def test_event_type_count(self):
        assert len(EventType) == 18

    def test_camera_state_updated_event_type_exists(self):
        from app.core.events import EventType
        assert hasattr(EventType, "CAMERA_STATE_UPDATED")
        assert EventType.CAMERA_STATE_UPDATED.value == "director.camera_state_updated"

    def test_publish_camera_state_updated(self):
        from app.core.events import EventBus, EventType
        bus = EventBus()
        received = []
        bus.subscribe(EventType.CAMERA_STATE_UPDATED, lambda e: received.append(e))
        bus.publish(EventType.CAMERA_STATE_UPDATED, {"center_x": 0.5})
        assert len(received) == 1
        assert received[0].data["center_x"] == 0.5


class TestEventPriority:
    """Test EventPriority enum."""

    def test_priority_values(self):
        assert EventPriority.NORMAL == 0
        assert EventPriority.HIGH == 1
        assert EventPriority.CRITICAL == 2

    def test_priority_ordering(self):
        assert EventPriority.NORMAL < EventPriority.HIGH < EventPriority.CRITICAL


class TestEvent:
    """Test Event data class."""

    def test_creation_defaults(self):
        event = Event(EventType.STATE_CHANGED)
        assert event.event_type == EventType.STATE_CHANGED
        assert event.data == {}
        assert event.priority == EventPriority.NORMAL
        assert event.source is None
        assert event.timestamp > 0

    def test_creation_with_data(self):
        data = {"old_state": "idle", "new_state": "streaming"}
        event = Event(EventType.STATE_CHANGED, data=data)
        assert event.data == data

    def test_creation_with_priority(self):
        event = Event(EventType.ERROR_OCCURRED, priority=EventPriority.CRITICAL)
        assert event.priority == EventPriority.CRITICAL

    def test_creation_with_source(self):
        event = Event(EventType.FRAME_CAPTURED, source="camera_0")
        assert event.source == "camera_0"

    def test_repr(self):
        event = Event(EventType.CAMERA_MOVE, priority=EventPriority.HIGH, source="director")
        r = repr(event)
        assert "director.camera_move" in r
        assert "HIGH" in r
        assert "director" in r


class TestEventBusInitialization:
    """Test EventBus initialization."""

    def test_default_init(self):
        bus = EventBus()
        assert bus.history == []
        assert bus.subscription_count == 0

    def test_custom_history_size(self):
        bus = EventBus(history_size=50)
        assert bus.history == []

    def test_repr(self):
        bus = EventBus()
        assert "EventBus" in repr(bus)
        assert "subscriptions=0" in repr(bus)


class TestSubscribeUnsubscribe:
    """Test subscribe and unsubscribe operations."""

    def test_subscribe(self):
        bus = EventBus()
        handler = MagicMock()
        bus.subscribe(EventType.STATE_CHANGED, handler)
        assert bus.subscription_count == 1
        assert handler in bus.get_subscribers(EventType.STATE_CHANGED)

    def test_subscribe_wildcard(self):
        bus = EventBus()
        handler = MagicMock()
        bus.subscribe("*", handler)
        assert bus.subscription_count == 1
        assert handler in bus.get_subscribers("*")

    def test_subscribe_string_type(self):
        bus = EventBus()
        handler = MagicMock()
        bus.subscribe("state.changed", handler)
        assert handler in bus.get_subscribers("state.changed")

    def test_subscribe_no_duplicates(self):
        bus = EventBus()
        handler = MagicMock()
        bus.subscribe(EventType.STATE_CHANGED, handler)
        bus.subscribe(EventType.STATE_CHANGED, handler)
        assert bus.subscription_count == 1

    def test_unsubscribe(self):
        bus = EventBus()
        handler = MagicMock()
        bus.subscribe(EventType.STATE_CHANGED, handler)
        result = bus.unsubscribe(EventType.STATE_CHANGED, handler)
        assert result is True
        assert bus.subscription_count == 0

    def test_unsubscribe_not_found(self):
        bus = EventBus()
        handler = MagicMock()
        result = bus.unsubscribe(EventType.STATE_CHANGED, handler)
        assert result is False

    def test_unsubscribe_wrong_type(self):
        bus = EventBus()
        handler = MagicMock()
        bus.subscribe(EventType.STATE_CHANGED, handler)
        result = bus.unsubscribe(EventType.ERROR_OCCURRED, handler)
        assert result is False
        assert bus.subscription_count == 1

    def test_get_subscribers_returns_copy(self):
        bus = EventBus()
        handler = MagicMock()
        bus.subscribe(EventType.STATE_CHANGED, handler)
        subs = bus.get_subscribers(EventType.STATE_CHANGED)
        subs.clear()
        assert bus.subscription_count == 1


class TestPublish:
    """Test event publishing."""

    def test_publish_calls_handler(self):
        bus = EventBus()
        handler = MagicMock()
        bus.subscribe(EventType.STATE_CHANGED, handler)
        bus.publish(EventType.STATE_CHANGED)
        handler.assert_called_once()

    def test_publish_returns_event(self):
        bus = EventBus()
        handler = MagicMock()
        bus.subscribe(EventType.STATE_CHANGED, handler)
        event = bus.publish(EventType.STATE_CHANGED)
        assert isinstance(event, Event)
        assert event.event_type == EventType.STATE_CHANGED

    def test_publish_passes_data(self):
        bus = EventBus()
        handler = MagicMock()
        bus.subscribe(EventType.FRAME_CAPTURED, handler)
        data = {"frame_id": 42, "width": 1920}
        bus.publish(EventType.FRAME_CAPTURED, data=data)
        call_args = handler.call_args[0][0]
        assert call_args.data == data

    def test_publish_passes_priority(self):
        bus = EventBus()
        handler = MagicMock()
        bus.subscribe(EventType.ERROR_OCCURRED, handler)
        bus.publish(EventType.ERROR_OCCURRED, priority=EventPriority.CRITICAL)
        call_args = handler.call_args[0][0]
        assert call_args.priority == EventPriority.CRITICAL

    def test_publish_passes_source(self):
        bus = EventBus()
        handler = MagicMock()
        bus.subscribe(EventType.CAMERA_MOVE, handler)
        bus.publish(EventType.CAMERA_MOVE, source="director")
        call_args = handler.call_args[0][0]
        assert call_args.source == "director"

    def test_publish_no_subscribers(self):
        bus = EventBus()
        # Should not raise
        event = bus.publish(EventType.STATE_CHANGED)
        assert isinstance(event, Event)

    def test_publish_multiple_handlers(self):
        bus = EventBus()
        handler1 = MagicMock()
        handler2 = MagicMock()
        bus.subscribe(EventType.STATE_CHANGED, handler1)
        bus.subscribe(EventType.STATE_CHANGED, handler2)
        bus.publish(EventType.STATE_CHANGED)
        handler1.assert_called_once()
        handler2.assert_called_once()

    def test_publish_wildcard_receives_all(self):
        bus = EventBus()
        handler = MagicMock()
        bus.subscribe("*", handler)
        bus.publish(EventType.STATE_CHANGED)
        bus.publish(EventType.FRAME_CAPTURED)
        assert handler.call_count == 2

    def test_publish_specific_and_wildcard(self):
        bus = EventBus()
        specific = MagicMock()
        wildcard = MagicMock()
        bus.subscribe(EventType.STATE_CHANGED, specific)
        bus.subscribe("*", wildcard)
        bus.publish(EventType.STATE_CHANGED)
        specific.assert_called_once()
        wildcard.assert_called_once()

    def test_publish_records_history(self):
        bus = EventBus()
        bus.publish(EventType.STATE_CHANGED)
        bus.publish(EventType.FRAME_CAPTURED)
        history = bus.history
        assert len(history) == 2
        assert history[0].event_type == EventType.STATE_CHANGED
        assert history[1].event_type == EventType.FRAME_CAPTURED

    def test_publish_history_ordering(self):
        bus = EventBus()
        for i in range(5):
            bus.publish(EventType.STATE_CHANGED, data={"i": i})
        history = bus.history
        assert len(history) == 5
        for i, event in enumerate(history):
            assert event.data["i"] == i


class TestHandlerErrorHandling:
    """Test that failing handlers don't block others."""

    def test_failing_handler_does_not_block_others(self):
        bus = EventBus()
        failing = MagicMock(side_effect=ValueError("boom"))
        success = MagicMock()
        bus.subscribe(EventType.STATE_CHANGED, failing)
        bus.subscribe(EventType.STATE_CHANGED, success)
        bus.publish(EventType.STATE_CHANGED)
        failing.assert_called_once()
        success.assert_called_once()

    def test_multiple_failures_all_others_run(self):
        bus = EventBus()
        fail1 = MagicMock(side_effect=RuntimeError("err1"))
        fail2 = MagicMock(side_effect=TypeError("err2"))
        success = MagicMock()
        bus.subscribe(EventType.STATE_CHANGED, fail1)
        bus.subscribe(EventType.STATE_CHANGED, success)
        bus.subscribe(EventType.STATE_CHANGED, fail2)
        bus.publish(EventType.STATE_CHANGED)
        fail1.assert_called_once()
        fail2.assert_called_once()
        success.assert_called_once()

    def test_publish_still_records_history_on_error(self):
        bus = EventBus()
        bus.subscribe(EventType.ERROR_OCCURRED, MagicMock(side_effect=RuntimeError))
        bus.publish(EventType.ERROR_OCCURRED)
        assert len(bus.history) == 1


class TestHistory:
    """Test event history management."""

    def test_history_respects_size_limit(self):
        bus = EventBus(history_size=5)
        for i in range(10):
            bus.publish(EventType.STATE_CHANGED, data={"i": i})
        history = bus.history
        assert len(history) == 5
        assert history[0].data["i"] == 5
        assert history[4].data["i"] == 9

    def test_clear_history(self):
        bus = EventBus()
        bus.publish(EventType.STATE_CHANGED)
        bus.publish(EventType.FRAME_CAPTURED)
        bus.clear_history()
        assert bus.history == []

    def test_history_returns_copy(self):
        bus = EventBus()
        bus.publish(EventType.STATE_CHANGED)
        history = bus.history
        history.clear()
        assert len(bus.history) == 1


class TestClearSubscriptions:
    """Test clearing all subscriptions."""

    def test_clear_subscriptions(self):
        bus = EventBus()
        bus.subscribe(EventType.STATE_CHANGED, MagicMock())
        bus.subscribe(EventType.FRAME_CAPTURED, MagicMock())
        bus.subscribe("*", MagicMock())
        bus.clear_subscriptions()
        assert bus.subscription_count == 0


class TestHasSubscribers:
    """Test has_subscribers method."""

    def test_has_subscribers_true(self):
        bus = EventBus()
        bus.subscribe(EventType.STATE_CHANGED, MagicMock())
        assert bus.has_subscribers(EventType.STATE_CHANGED) is True

    def test_has_subscribers_false(self):
        bus = EventBus()
        assert bus.has_subscribers(EventType.STATE_CHANGED) is False

    def test_has_subscribers_wildcard(self):
        bus = EventBus()
        bus.subscribe("*", MagicMock())
        assert bus.has_subscribers(EventType.STATE_CHANGED) is True


class TestSingleton:
    """Test global event bus singleton."""

    def setup_method(self):
        reset_event_bus()

    def teardown_method(self):
        reset_event_bus()

    def test_singleton_returns_same_instance(self):
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2

    def test_reset_creates_new_instance(self):
        bus1 = get_event_bus()
        reset_event_bus()
        bus2 = get_event_bus()
        assert bus1 is not bus2


class TestThreadSafety:
    """Test thread safety of event bus."""

    def test_concurrent_subscribe(self):
        bus = EventBus()
        errors = []

        def subscriber():
            try:
                for _ in range(100):
                    handler = MagicMock()
                    bus.subscribe(EventType.STATE_CHANGED, handler)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=subscriber) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert bus.subscription_count == 1000

    def test_concurrent_publish(self):
        bus = EventBus()
        received = []
        lock = threading.Lock()

        def handler(event: Event) -> None:
            with lock:
                received.append(event.data["id"])

        bus.subscribe(EventType.STATE_CHANGED, handler)
        errors = []

        def publisher(start: int) -> None:
            try:
                for i in range(100):
                    bus.publish(EventType.STATE_CHANGED, data={"id": start + i})
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=publisher, args=(i * 100,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(received) == 500

    def test_concurrent_subscribe_and_publish(self):
        bus = EventBus()
        errors = []
        publish_count = [0]

        def handler(event: Event) -> None:
            publish_count[0] += 1

        def subscriber():
            try:
                for _ in range(50):
                    bus.subscribe(EventType.FRAME_CAPTURED, handler)
            except Exception as e:
                errors.append(e)

        def publisher():
            try:
                for _ in range(50):
                    bus.publish(EventType.FRAME_CAPTURED)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=subscriber),
            threading.Thread(target=subscriber),
            threading.Thread(target=publisher),
            threading.Thread(target=publisher),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestAsyncPublish:
    """Test async event publishing."""

    def test_publish_async_calls_sync_handler(self):
        bus = EventBus()
        handler = MagicMock()
        bus.subscribe(EventType.STATE_CHANGED, handler)
        bus.publish_async(EventType.STATE_CHANGED)
        handler.assert_called_once()

    def test_publish_async_records_history(self):
        bus = EventBus()
        bus.subscribe(EventType.STATE_CHANGED, MagicMock())
        bus.publish_async(EventType.STATE_CHANGED)
        assert len(bus.history) == 1

    def test_publish_async_failing_handler(self):
        bus = EventBus()
        failing = MagicMock(side_effect=RuntimeError("boom"))
        success = MagicMock()
        bus.subscribe(EventType.STATE_CHANGED, failing)
        bus.subscribe(EventType.STATE_CHANGED, success)
        bus.publish_async(EventType.STATE_CHANGED)
        failing.assert_called_once()
        success.assert_called_once()


class TestWaitFor:
    """Test async wait_for method."""

    def test_wait_for_receives_event(self):
        bus = EventBus()
        result = []

        async def runner():
            async def publish_later():
                await asyncio.sleep(0.01)
                bus.publish(EventType.STATE_CHANGED, data={"ready": True})

            asyncio.create_task(publish_later())
            event = await bus.wait_for(EventType.STATE_CHANGED, timeout=1.0)
            result.append(event)

        asyncio.run(runner())
        assert len(result) == 1
        assert result[0].data["ready"] is True

    def test_wait_for_timeout(self):
        bus = EventBus()

        async def runner():
            with pytest.raises(asyncio.TimeoutError):
                await bus.wait_for(EventType.STATE_CHANGED, timeout=0.01)

        asyncio.run(runner())


class TestRepr:
    """Test string representation."""

    def test_repr_no_subscriptions(self):
        bus = EventBus()
        assert "subscriptions=0" in repr(bus)

    def test_repr_with_subscriptions(self):
        bus = EventBus()
        bus.subscribe(EventType.STATE_CHANGED, MagicMock())
        bus.subscribe("*", MagicMock())
        assert "subscriptions=2" in repr(bus)

    def test_repr_with_history(self):
        bus = EventBus()
        bus.publish(EventType.STATE_CHANGED)
        assert "history=1" in repr(bus)


class TestRealWorldScenarios:
    """Test realistic usage patterns."""

    def test_camera_to_vision_pipeline(self):
        bus = EventBus()
        frame_events = []
        detection_events = []

        def on_frame(event: Event) -> None:
            frame_events.append(event)
            # Vision service detects objects
            bus.publish(
                EventType.DETECTIONS_COMPLETE,
                data={"detections": [{"class": "ball", "confidence": 0.95}]},
                source="vision",
            )

        def on_detection(event: Event) -> None:
            detection_events.append(event)

        bus.subscribe(EventType.FRAME_CAPTURED, on_frame)
        bus.subscribe(EventType.DETECTIONS_COMPLETE, on_detection)

        bus.publish(EventType.FRAME_CAPTURED, data={"frame_id": 1}, source="camera")

        assert len(frame_events) == 1
        assert len(detection_events) == 1
        assert detection_events[0].data["detections"][0]["class"] == "ball"

    def test_director_decision_flow(self):
        bus = EventBus()
        decisions = []
        moves = []

        def on_detection(event: Event) -> None:
            bus.publish(
                EventType.DIRECTOR_DECISION,
                data={"action": "track", "target": "ball"},
                source="director",
            )

        def on_decision(event: Event) -> None:
            decisions.append(event)
            bus.publish(
                EventType.CAMERA_MOVE,
                data={"pan": 45.0, "tilt": 30.0},
                source="director",
            )

        def on_move(event: Event) -> None:
            moves.append(event)

        bus.subscribe(EventType.DETECTIONS_COMPLETE, on_detection)
        bus.subscribe(EventType.DIRECTOR_DECISION, on_decision)
        bus.subscribe(EventType.CAMERA_MOVE, on_move)

        bus.publish(EventType.DETECTIONS_COMPLETE, source="vision")

        assert len(decisions) == 1
        assert len(moves) == 1
        assert moves[0].data["pan"] == 45.0

    def test_emergency_stop_broadcast(self):
        bus = EventBus()
        handlers_called = []

        def on_servo_stop(event: Event) -> None:
            handlers_called.append("servo")

        def on_stream_stop(event: Event) -> None:
            handlers_called.append("stream")

        def on_state_change(event: Event) -> None:
            handlers_called.append("state")

        bus.subscribe(EventType.SERVO_COMMAND, on_servo_stop)
        bus.subscribe(EventType.STREAM_STOPPED, on_stream_stop)
        bus.subscribe(EventType.STATE_CHANGED, on_state_change)

        # Emergency stop broadcasts to all relevant services
        bus.publish(EventType.SERVO_COMMAND, data={"action": "stop"})
        bus.publish(EventType.STREAM_STOPPED, data={"reason": "emergency"})
        bus.publish(EventType.STATE_CHANGED, data={"new_state": "emergency_stop"})

        assert "servo" in handlers_called
        assert "stream" in handlers_called
        assert "state" in handlers_called

    def test_dashboard_wildcard_subscription(self):
        bus = EventBus()
        dashboard_events = []

        def dashboard_handler(event: Event) -> None:
            dashboard_events.append(event.event_type)

        bus.subscribe("*", dashboard_handler)

        bus.publish(EventType.FRAME_CAPTURED)
        bus.publish(EventType.DETECTIONS_COMPLETE)
        bus.publish(EventType.CAMERA_MOVE)
        bus.publish(EventType.SERVO_POSITION)

        assert len(dashboard_events) == 4
        assert EventType.FRAME_CAPTURED in dashboard_events
        assert EventType.DETECTIONS_COMPLETE in dashboard_events
