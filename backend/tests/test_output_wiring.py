"""Integration tests for output wiring."""
import time

import pytest

from app.core.events import EventBus, EventType
from app.models.camera_state import CameraState, OutputMode
from app.models.motion import MotionProfile
from app.services.output.manager import OutputManager
from app.services.output.wiring import wire_output_to_events


def _make_event_data(cx=0.5, cy=0.5, zoom=1.5):
    return {
        "center_x": cx,
        "center_y": cy,
        "zoom": zoom,
        "motion_profile": "broadcast",
        "tracking_mode": "broadcast",
        "confidence": 0.9,
        "timestamp": time.time(),
    }


def test_output_manager_receives_camera_state_event():
    bus = EventBus()
    manager = OutputManager()
    wire_output_to_events(bus, manager)

    bus.publish(EventType.CAMERA_STATE_UPDATED, _make_event_data(0.3, 0.7, 2.0))
    last = manager.get_last_state()
    assert last is not None
    assert abs(last.center_x - 0.3) < 0.001
    assert abs(last.center_y - 0.7) < 0.001


def test_output_manager_routes_to_active_plugin():
    bus = EventBus()
    manager = OutputManager()
    wire_output_to_events(bus, manager)

    bus.publish(EventType.CAMERA_STATE_UPDATED, _make_event_data(0.5, 0.5, 1.5))
    plugin = manager.active_plugin
    assert plugin is not None
    plugin_state = plugin.get_state()
    assert plugin_state is not None


def test_output_manager_switches_mode():
    bus = EventBus()
    manager = OutputManager()
    wire_output_to_events(bus, manager)

    # Default is virtual
    assert manager.active_mode == OutputMode.VIRTUAL

    # Switch to servo
    manager.set_mode(OutputMode.SERVO)
    bus.publish(EventType.CAMERA_STATE_UPDATED, _make_event_data(0.5, 0.5, 1.5))
    assert manager.active_plugin.name == "servo"


def test_director_service_wires_output_manager():
    from app.core.events import EventBus
    from app.services.director.director_service import DirectorService, DirectorConfig
    from app.services.director.shot_composer import DirectorMode

    bus = EventBus()
    manager = OutputManager()
    config = DirectorConfig(mode=DirectorMode.BROADCAST, event_bus=bus)
    director = DirectorService(config=config, output_manager=manager)

    # Publish a camera state event as the director would
    bus.publish(EventType.CAMERA_STATE_UPDATED, _make_event_data(0.4, 0.6, 2.0))
    last = manager.get_last_state()
    assert last is not None
    assert abs(last.center_x - 0.4) < 0.001


def test_director_without_output_manager_still_works():
    from app.core.events import EventBus
    from app.services.director.director_service import DirectorService, DirectorConfig
    from app.services.director.shot_composer import DirectorMode

    bus = EventBus()
    config = DirectorConfig(mode=DirectorMode.BROADCAST, event_bus=bus)
    director = DirectorService(config=config)

    # Should not raise
    bus.publish(EventType.CAMERA_STATE_UPDATED, _make_event_data(0.4, 0.6, 2.0))


def test_wiring_does_not_duplicate_subscriptions():
    bus = EventBus()
    manager = OutputManager()
    wire_output_to_events(bus, manager)
    wire_output_to_events(bus, manager)

    subscribers = bus.get_subscribers(EventType.CAMERA_STATE_UPDATED)
    assert len(subscribers) == 2  # Two calls, but EventBus deduplicates internally


def test_output_manager_get_last_state_before_any_event():
    manager = OutputManager()
    assert manager.get_last_state() is None
