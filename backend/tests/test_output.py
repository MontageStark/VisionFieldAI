"""Tests for output plugin system."""
from __future__ import annotations

import pytest
from typing import Optional

from app.models.camera_state import CameraState, OutputConfig, OutputMode
from app.services.output.base import OutputPlugin, OutputPluginError
from app.services.output.manager import OutputManager
from app.services.output.virtual_camera import VirtualCameraOutput
from app.services.output.servo import ServoOutput
from app.services.output.ptz import PTZOutput


def _make_state() -> CameraState:
    """Create a test CameraState."""
    return CameraState.from_normalized(
        center_x=0.5,
        center_y=0.5,
        zoom=2.0,
        confidence=0.9,
    )


class TestOutputPlugin:
    """Tests for OutputPlugin abstract base class."""

    def test_cannot_instantiate_directly(self):
        """OutputPlugin is abstract and cannot be instantiated."""
        with pytest.raises(TypeError):
            OutputPlugin()

    def test_subclass_must_implement_name(self):
        """Subclass without name property raises TypeError."""
        class IncompletePlugin(OutputPlugin):
            def apply(self, state: CameraState) -> None:
                pass
            def get_state(self) -> Optional[CameraState]:
                return None
        with pytest.raises(TypeError):
            IncompletePlugin()

    def test_subclass_must_implement_apply(self):
        """Subclass without apply method raises TypeError."""
        class IncompletePlugin(OutputPlugin):
            @property
            def name(self) -> str:
                return "incomplete"
            def get_state(self) -> Optional[CameraState]:
                return None
        with pytest.raises(TypeError):
            IncompletePlugin()

    def test_subclass_must_implement_get_state(self):
        """Subclass without get_state method raises TypeError."""
        class IncompletePlugin(OutputPlugin):
            @property
            def name(self) -> str:
                return "incomplete"
            def apply(self, state: CameraState) -> None:
                pass
        with pytest.raises(TypeError):
            IncompletePlugin()

    def test_default_reset(self):
        """Default reset method does nothing."""
        class MinimalPlugin(OutputPlugin):
            @property
            def name(self) -> str:
                return "minimal"
            def apply(self, state: CameraState) -> None:
                pass
            def get_state(self) -> Optional[CameraState]:
                return None
        plugin = MinimalPlugin()
        plugin.reset()

    def test_default_is_available(self):
        """Default is_available returns True."""
        class MinimalPlugin(OutputPlugin):
            @property
            def name(self) -> str:
                return "minimal"
            def apply(self, state: CameraState) -> None:
                pass
            def get_state(self) -> Optional[CameraState]:
                return None
        plugin = MinimalPlugin()
        assert plugin.is_available() is True


class TestVirtualCameraOutput:
    """Tests for VirtualCameraOutput."""

    def test_name(self):
        plugin = VirtualCameraOutput()
        assert plugin.name == "virtual_camera"

    def test_apply_stores_state(self):
        plugin = VirtualCameraOutput()
        state = _make_state()
        plugin.apply(state)
        assert plugin.get_state() == state

    def test_get_state_initially_none(self):
        plugin = VirtualCameraOutput()
        assert plugin.get_state() is None

    def test_reset_clears_state(self):
        plugin = VirtualCameraOutput()
        state = _make_state()
        plugin.apply(state)
        plugin.reset()
        assert plugin.get_state() is None

    def test_is_available(self):
        plugin = VirtualCameraOutput()
        assert plugin.is_available() is True


class TestServoOutput:
    """Tests for ServoOutput."""

    def test_name(self):
        plugin = ServoOutput()
        assert plugin.name == "servo"

    def test_apply_stores_state(self):
        plugin = ServoOutput()
        state = _make_state()
        plugin.apply(state)
        assert plugin.get_state() == state

    def test_get_state_initially_none(self):
        plugin = ServoOutput()
        assert plugin.get_state() is None

    def test_reset_clears_state(self):
        plugin = ServoOutput()
        state = _make_state()
        plugin.apply(state)
        plugin.reset()
        assert plugin.get_state() is None

    def test_is_available(self):
        plugin = ServoOutput()
        assert plugin.is_available() is True


class TestPTZOutput:
    """Tests for PTZOutput."""

    def test_name(self):
        plugin = PTZOutput()
        assert plugin.name == "ptz"

    def test_apply_stores_state(self):
        plugin = PTZOutput()
        state = _make_state()
        plugin.apply(state)
        assert plugin.get_state() == state

    def test_get_state_initially_none(self):
        plugin = PTZOutput()
        assert plugin.get_state() is None

    def test_is_not_available(self):
        plugin = PTZOutput()
        assert plugin.is_available() is False


class TestOutputManager:
    """Tests for OutputManager."""

    def setup_method(self):
        """Reset singleton before each test."""
        OutputManager.reset_instance()

    def test_instantiation(self):
        manager = OutputManager()
        assert manager is not None

    def test_default_mode_is_virtual(self):
        manager = OutputManager()
        assert manager.active_mode == OutputMode.VIRTUAL

    def test_active_plugin_is_virtual_by_default(self):
        manager = OutputManager()
        assert manager.active_plugin is not None
        assert manager.active_plugin.name == "virtual_camera"

    def test_switch_to_servo_mode(self):
        manager = OutputManager()
        manager.set_mode(OutputMode.SERVO)
        assert manager.active_mode == OutputMode.SERVO
        assert manager.active_plugin.name == "servo"

    def test_switch_to_ptz_mode(self):
        manager = OutputManager()
        manager.set_mode(OutputMode.PTZ)
        assert manager.active_mode == OutputMode.PTZ
        assert manager.active_plugin.name == "ptz"

    def test_switch_to_hybrid_mode(self):
        manager = OutputManager()
        manager.set_mode(OutputMode.HYBRID)
        assert manager.active_mode == OutputMode.HYBRID
        assert manager.active_plugin.name == "servo"

    def test_invalid_mode_raises_error(self):
        manager = OutputManager()
        with pytest.raises(OutputPluginError):
            manager.set_mode("invalid_mode")

    def test_apply_routes_to_active_plugin(self):
        manager = OutputManager()
        state = _make_state()
        manager.apply(state)
        assert manager.active_plugin.get_state() == state

    def test_get_last_state(self):
        manager = OutputManager()
        state = _make_state()
        manager.apply(state)
        assert manager.get_last_state() == state

    def test_get_last_state_initially_none(self):
        manager = OutputManager()
        assert manager.get_last_state() is None

    def test_apply_after_mode_switch(self):
        manager = OutputManager()
        state = _make_state()
        manager.set_mode(OutputMode.SERVO)
        manager.apply(state)
        assert manager.active_plugin.get_state() == state

    def test_reset_resets_all_plugins(self):
        manager = OutputManager()
        state = _make_state()
        manager.apply(state)
        manager.reset()
        assert manager.get_last_state() == state
        for plugin in manager._plugins.values():
            assert plugin.get_state() is None

    def test_singleton_pattern(self):
        manager1 = OutputManager.get_instance()
        manager2 = OutputManager.get_instance()
        assert manager1 is manager2

    def test_reset_instance(self):
        manager1 = OutputManager.get_instance()
        OutputManager.reset_instance()
        manager2 = OutputManager.get_instance()
        assert manager1 is not manager2
