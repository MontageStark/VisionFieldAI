"""Output manager that routes CameraState to the active output plugin."""
from __future__ import annotations

import logging
import threading
from typing import Dict, Optional

from app.models.camera_state import CameraState, OutputConfig, OutputMode
from app.services.output.base import OutputPlugin, OutputPluginError

logger = logging.getLogger(__name__)


class OutputManager:
    """Manages the active output plugin and routes CameraState to it."""

    _instance: Optional[OutputManager] = None
    _instance_lock = threading.Lock()

    def __init__(self, config: Optional[OutputConfig] = None) -> None:
        self._config = config or OutputConfig()
        self._plugins: Dict[OutputMode, OutputPlugin] = {}
        self._active_mode: OutputMode = self._config.mode
        self._active_plugin: Optional[OutputPlugin] = None
        self._last_state: Optional[CameraState] = None
        self._lock = threading.Lock()

        self._register_plugins()

    def _register_plugins(self) -> None:
        from app.services.output.virtual_camera import VirtualCameraOutput
        from app.services.output.servo import ServoOutput
        from app.services.output.ptz import PTZOutput

        self._plugins = {
            OutputMode.VIRTUAL: VirtualCameraOutput(self._config.virtual_camera),
            OutputMode.SERVO: ServoOutput(self._config.servo),
            OutputMode.HYBRID: ServoOutput(self._config.servo),
            OutputMode.PTZ: PTZOutput(self._config.ptz),
        }

        self._active_plugin = self._plugins.get(self._active_mode)

    @property
    def active_plugin(self) -> Optional[OutputPlugin]:
        return self._active_plugin

    @property
    def active_mode(self) -> OutputMode:
        return self._active_mode

    def set_mode(self, mode: OutputMode) -> None:
        with self._lock:
            if mode not in self._plugins:
                mode_name = mode.value if hasattr(mode, 'value') else str(mode)
                raise OutputPluginError(f"No plugin registered for mode: {mode_name}")
            self._active_mode = mode
            self._active_plugin = self._plugins[mode]
            logger.info("Output mode switched to %s", mode.value)

    def apply(self, state: CameraState) -> None:
        with self._lock:
            self._last_state = state
            if self._active_plugin is None:
                logger.warning("No active output plugin, cannot apply state")
                return
            try:
                self._active_plugin.apply(state)
            except OutputPluginError:
                raise

    def get_last_state(self) -> Optional[CameraState]:
        with self._lock:
            return self._last_state

    def reset(self) -> None:
        with self._lock:
            for plugin in self._plugins.values():
                try:
                    plugin.reset()
                except Exception:
                    pass

    @classmethod
    def get_instance(cls, config: Optional[OutputConfig] = None) -> OutputManager:
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls(config)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        with cls._instance_lock:
            cls._instance = None
