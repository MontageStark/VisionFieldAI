"""Performance Manager for FieldVision AI - monitors FPS, GPU memory, auto-scales."""
from __future__ import annotations

import logging
import socket
import threading
import time
from collections import deque
from enum import Enum
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None


class Resolution(Enum):
    FULL_HD = (1920, 1080)
    HD = (1280, 720)
    SD = (640, 480)
    LOW = (320, 240)

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    def next_lower(self) -> Optional[Resolution]:
        steps = [Resolution.FULL_HD, Resolution.HD, Resolution.SD, Resolution.LOW]
        idx = steps.index(self)
        if idx + 1 < len(steps):
            return steps[idx + 1]
        return None

    def __repr__(self) -> str:
        return f"{self.name}({self.width}x{self.height})"


class YoloModelSize(Enum):
    NANO = "yolo11n.pt"
    SMALL = "yolo11s.pt"
    MEDIUM = "yolo11m.pt"

    def next_smaller(self) -> Optional[YoloModelSize]:
        steps = [YoloModelSize.NANO, YoloModelSize.SMALL, YoloModelSize.MEDIUM]
        idx = steps.index(self)
        if idx + 1 < len(steps):
            return steps[idx + 1]
        return None

    def __repr__(self) -> str:
        return self.value


class PerformanceMetric(Enum):
    FPS_LOW = "performance.fps_low"
    FPS_CRITICAL = "performance.fps_critical"
    GPU_MEMORY_HIGH = "performance.gpu_memory_high"
    GPU_MEMORY_CRITICAL = "performance.gpu_memory_critical"
    AUTO_SCALE_DOWN = "performance.auto_scale_down"
    AUTO_SCALE_UP = "performance.auto_scale_up"
    THROTTLING_APPLIED = "performance.throttling_applied"


class PerformanceConfig:
    def __init__(
        self,
        max_gpu_mem_gb: float = 2.0,
        max_cpu_cores: int = 2,
        target_fps: float = 30.0,
        min_fps_threshold: float = 20.0,
        critical_fps_threshold: float = 10.0,
        gpu_memory_threshold: float = 0.8,
        event_bus: Optional[Any] = None,
    ) -> None:
        self.max_gpu_mem_gb = max_gpu_mem_gb
        self.max_cpu_cores = max_cpu_cores
        self.target_fps = target_fps
        self.min_fps_threshold = min_fps_threshold
        self.critical_fps_threshold = critical_fps_threshold
        self.gpu_memory_threshold = gpu_memory_threshold
        self.event_bus = event_bus


class PerformanceManager:
    def __init__(
        self,
        config: Optional[PerformanceConfig] = None,
        event_bus: Optional[Any] = None,
    ) -> None:
        self._config = config or PerformanceConfig()
        if event_bus is not None:
            self._config.event_bus = event_bus
        self._fps_history: Deque[float] = deque(maxlen=30)
        self._gpu_history: Deque[float] = deque(maxlen=30)
        self._frame_timestamps: Deque[float] = deque(maxlen=60)
        self._current_resolution = Resolution.FULL_HD
        self._current_model_size = YoloModelSize.NANO
        self._last_fps_update = time.time()
        self._current_fps = 0.0
        self._is_monitoring = False
        self._monitor_lock = threading.Lock()
        self._cpu_limited = False
        self._original_thread_count: Optional[int] = None

    @property
    def current_fps(self) -> float:
        return self._current_fps

    @property
    def current_resolution(self) -> Resolution:
        return self._current_resolution

    @property
    def current_model_size(self) -> YoloModelSize:
        return self._current_model_size

    @property
    def fps_average(self) -> float:
        if not self._fps_history:
            return 0.0
        return sum(self._fps_history) / len(self._fps_history)

    @property
    def gpu_memory_used_gb(self) -> float:
        if not TORCH_AVAILABLE or not torch.cuda.is_available():
            return 0.0
        return torch.cuda.memory_allocated() / (1024**3)

    @property
    def gpu_memory_total_gb(self) -> float:
        if not TORCH_AVAILABLE or not torch.cuda.is_available():
            return 0.0
        return torch.cuda.get_device_properties(0).total_memory / (1024**3)

    @property
    def gpu_memory_usage_ratio(self) -> float:
        if not TORCH_AVAILABLE or not torch.cuda.is_available():
            return 0.0
        used = torch.cuda.memory_allocated()
        total = torch.cuda.get_device_properties(0).total_memory
        return used / total if total > 0 else 0.0

    def record_frame(self, timestamp: Optional[float] = None) -> None:
        now = timestamp or time.time()
        self._frame_timestamps.append(now)
        self._update_fps(now)

    def _update_fps(self, now: float) -> None:
        if len(self._frame_timestamps) < 2:
            return
        elapsed = now - self._frame_timestamps[0]
        if elapsed > 0:
            self._current_fps = (len(self._frame_timestamps) - 1) / elapsed
            self._fps_history.append(self._current_fps)

    def check_performance(self) -> Dict[str, Any]:
        warnings: List[PerformanceMetric] = []
        actions: List[str] = []

        if self.fps_average > 0 and self.fps_average < self._config.critical_fps_threshold:
            warnings.append(PerformanceMetric.FPS_CRITICAL)
            self._auto_scale_down()
            actions.append("reduced_resolution")
            self._maybe_reduce_model()
            actions.append("reduced_model")
        elif self.fps_average > 0 and self.fps_average < self._config.min_fps_threshold:
            warnings.append(PerformanceMetric.FPS_LOW)
            self._auto_scale_down()
            actions.append("reduced_resolution")

        gpu_ratio = self.gpu_memory_usage_ratio
        if gpu_ratio > 0:
            self._gpu_history.append(gpu_ratio)
        if gpu_ratio > self._config.gpu_memory_threshold:
            warnings.append(PerformanceMetric.GPU_MEMORY_HIGH)
        if gpu_ratio > 0.95:
            warnings.append(PerformanceMetric.GPU_MEMORY_CRITICAL)
            self._maybe_reduce_model()
            actions.append("reduced_model")

        if warnings and self._config.event_bus:
            for warning in warnings:
                self._publish_warning(warning, actions)

        return {
            "fps": self._current_fps,
            "fps_average": self.fps_average,
            "gpu_memory_gb": self.gpu_memory_used_gb,
            "gpu_memory_ratio": gpu_ratio,
            "resolution": self._current_resolution,
            "model_size": self._current_model_size,
            "warnings": [w.value for w in warnings],
            "actions_taken": actions,
        }

    def _auto_scale_down(self) -> None:
        next_res = self._current_resolution.next_lower()
        if next_res:
            logger.info("Auto-scaling resolution from %s to %s", self._current_resolution, next_res)
            self._current_resolution = next_res

    def _maybe_reduce_model(self) -> None:
        next_model = self._current_model_size.next_smaller()
        if next_model:
            logger.info("Auto-scaling model from %s to %s", self._current_model_size, next_model)
            self._current_model_size = next_model

    def _publish_warning(self, warning: PerformanceMetric, actions: List[str]) -> None:
        from app.core.events import EventPriority

        event_type = warning.value
        self._config.event_bus.publish(
            event_type,
            data={
                "fps": self._current_fps,
                "fps_average": self.fps_average,
                "gpu_memory_ratio": self.gpu_memory_usage_ratio,
                "resolution": str(self._current_resolution),
                "model_size": str(self._current_model_size),
                "actions_taken": actions,
            },
            priority=EventPriority.HIGH,
            source="performance_manager",
        )

    def limit_cpu_cores(self, max_cores: Optional[int] = None) -> None:
        cores = max_cores or self._config.max_cpu_cores
        if cores < 1:
            cores = 1
        self._original_thread_count = threading.active_count()
        self._cpu_limited = True
        logger.info("Limiting CPU cores to %d", cores)

    def restore_cpu_cores(self) -> None:
        if self._cpu_limited and self._original_thread_count is not None:
            self._cpu_limited = False
            self._original_thread_count = None
            logger.info("Restored CPU core usage")

    def get_stats(self) -> Dict[str, Any]:
        return {
            "fps": self._current_fps,
            "fps_average": self.fps_average,
            "fps_history_size": len(self._fps_history),
            "gpu_memory_used_gb": self.gpu_memory_used_gb,
            "gpu_memory_total_gb": self.gpu_memory_total_gb,
            "gpu_memory_usage_ratio": self.gpu_memory_usage_ratio,
            "resolution": self._current_resolution,
            "model_size": self._current_model_size,
            "cpu_limited": self._cpu_limited,
        }

    def reset_stats(self) -> None:
        self._fps_history.clear()
        self._gpu_history.clear()
        self._frame_timestamps.clear()
        self._current_fps = 0.0


def find_free_port(start_port: int = 8000, max_attempts: int = 100) -> int:
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find free port in range {start_port}-{start_port + max_attempts}")


def get_available_port(host: str = "127.0.0.1", start_port: int = 8000, max_attempts: int = 100) -> int:
    return find_free_port(start_port, max_attempts)