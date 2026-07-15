"""Tests for the Performance Manager service."""
from __future__ import annotations

import socket
import threading
import time
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

from app.services.monitoring.performance_manager import (
    PerformanceConfig,
    PerformanceManager,
    PerformanceMetric,
    Resolution,
    YoloModelSize,
    find_free_port,
    get_available_port,
)


@pytest.fixture
def mock_event_bus():
    bus = MagicMock()
    bus.publish = MagicMock()
    return bus


@pytest.fixture
def perf_config(mock_event_bus) -> PerformanceConfig:
    return PerformanceConfig(
        max_gpu_mem_gb=2.0,
        max_cpu_cores=2,
        target_fps=30.0,
        min_fps_threshold=20.0,
        critical_fps_threshold=10.0,
        gpu_memory_threshold=0.8,
        event_bus=mock_event_bus,
    )


@pytest.fixture
def perf_manager(perf_config) -> PerformanceManager:
    return PerformanceManager(config=perf_config)


class TestResolution:
    def test_resolution_values(self) -> None:
        assert Resolution.FULL_HD.width == 1920
        assert Resolution.FULL_HD.height == 1080
        assert Resolution.HD.width == 1280
        assert Resolution.SD.width == 640
        assert Resolution.LOW.width == 320

    def test_next_lower_from_full_hd(self) -> None:
        next_res = Resolution.FULL_HD.next_lower()
        assert next_res == Resolution.HD

    def test_next_lower_from_hd(self) -> None:
        next_res = Resolution.HD.next_lower()
        assert next_res == Resolution.SD

    def test_next_lower_from_sd(self) -> None:
        next_res = Resolution.SD.next_lower()
        assert next_res == Resolution.LOW

    def test_next_lower_from_low_returns_none(self) -> None:
        next_res = Resolution.LOW.next_lower()
        assert next_res is None


class TestYoloModelSize:
    def test_model_size_values(self) -> None:
        assert YoloModelSize.NANO.value == "yolo11n.pt"
        assert YoloModelSize.SMALL.value == "yolo11s.pt"
        assert YoloModelSize.MEDIUM.value == "yolo11m.pt"

    def test_next_smaller_from_nano(self) -> None:
        next_model = YoloModelSize.NANO.next_smaller()
        assert next_model == YoloModelSize.SMALL

    def test_next_smaller_from_small(self) -> None:
        next_model = YoloModelSize.SMALL.next_smaller()
        assert next_model == YoloModelSize.MEDIUM

    def test_next_smaller_from_medium_returns_none(self) -> None:
        next_model = YoloModelSize.MEDIUM.next_smaller()
        assert next_model is None


class TestPerformanceConfig:
    def test_defaults(self) -> None:
        config = PerformanceConfig()
        assert config.max_gpu_mem_gb == 2.0
        assert config.max_cpu_cores == 2
        assert config.target_fps == 30.0
        assert config.min_fps_threshold == 20.0
        assert config.critical_fps_threshold == 10.0
        assert config.gpu_memory_threshold == 0.8
        assert config.event_bus is None

    def test_custom_values(self) -> None:
        bus = MagicMock()
        config = PerformanceConfig(
            max_gpu_mem_gb=4.0,
            max_cpu_cores=4,
            target_fps=60.0,
            min_fps_threshold=30.0,
            critical_fps_threshold=15.0,
            gpu_memory_threshold=0.9,
            event_bus=bus,
        )
        assert config.max_gpu_mem_gb == 4.0
        assert config.max_cpu_cores == 4
        assert config.target_fps == 60.0
        assert config.min_fps_threshold == 30.0
        assert config.critical_fps_threshold == 15.0
        assert config.gpu_memory_threshold == 0.9
        assert config.event_bus is bus


class TestPerformanceManagerInit:
    def test_init_with_config(self, perf_config) -> None:
        mgr = PerformanceManager(config=perf_config)
        assert mgr.current_resolution == Resolution.FULL_HD
        assert mgr.current_model_size == YoloModelSize.NANO
        assert mgr.current_fps == 0.0

    def test_init_with_event_bus(self, mock_event_bus) -> None:
        mgr = PerformanceManager(event_bus=mock_event_bus)
        assert mgr._config.event_bus is mock_event_bus

    def test_init_defaults(self) -> None:
        mgr = PerformanceManager()
        assert mgr.current_resolution == Resolution.FULL_HD
        assert mgr.current_model_size == YoloModelSize.NANO


class TestFPSMonitoring:
    def test_initial_fps_zero(self, perf_manager) -> None:
        assert perf_manager.current_fps == 0.0

    def test_fps_average_empty(self, perf_manager) -> None:
        assert perf_manager.fps_average == 0.0

    def test_record_frame_updates_fps(self, perf_manager) -> None:
        now = time.time()
        perf_manager.record_frame(now)
        perf_manager.record_frame(now + 0.1)
        assert perf_manager.current_fps > 0

    def test_fps_calculation(self, perf_manager) -> None:
        now = time.time()
        for i in range(10):
            perf_manager.record_frame(now + i * 0.1)
        perf_manager._update_fps(time.time())
        assert perf_manager.current_fps > 0
        assert perf_manager.fps_average > 0

    def test_fps_history_maintained(self, perf_manager) -> None:
        now = time.time()
        for i in range(35):
            perf_manager.record_frame(now + i * 0.1)
            time.sleep(0.001)
        assert len(perf_manager._fps_history) <= 30


class TestGPUMemoryMonitoring:
    def test_gpu_memory_no_cuda(self, perf_manager) -> None:
        used = perf_manager.gpu_memory_used_gb
        ratio = perf_manager.gpu_memory_usage_ratio
        assert used >= 0.0
        assert ratio >= 0.0


class TestAutoScaling:
    def test_auto_scale_down_resolution(self, perf_manager) -> None:
        perf_manager._current_resolution = Resolution.FULL_HD
        perf_manager._auto_scale_down()
        assert perf_manager.current_resolution == Resolution.HD

    def test_auto_scale_down_hd_to_sd(self, perf_manager) -> None:
        perf_manager._current_resolution = Resolution.HD
        perf_manager._auto_scale_down()
        assert perf_manager.current_resolution == Resolution.SD

    def test_auto_scale_down_sd_to_low(self, perf_manager) -> None:
        perf_manager._current_resolution = Resolution.SD
        perf_manager._auto_scale_down()
        assert perf_manager.current_resolution == Resolution.LOW

    def test_auto_scale_down_low_stays(self, perf_manager) -> None:
        perf_manager._current_resolution = Resolution.LOW
        perf_manager._auto_scale_down()
        assert perf_manager.current_resolution == Resolution.LOW

    def test_reduce_model_nano_to_small(self, perf_manager) -> None:
        perf_manager._current_model_size = YoloModelSize.NANO
        perf_manager._maybe_reduce_model()
        assert perf_manager.current_model_size == YoloModelSize.SMALL

    def test_reduce_model_small_to_medium(self, perf_manager) -> None:
        perf_manager._current_model_size = YoloModelSize.SMALL
        perf_manager._maybe_reduce_model()
        assert perf_manager.current_model_size == YoloModelSize.MEDIUM

    def test_reduce_model_medium_stays(self, perf_manager) -> None:
        perf_manager._current_model_size = YoloModelSize.MEDIUM
        perf_manager._maybe_reduce_model()
        assert perf_manager.current_model_size == YoloModelSize.MEDIUM


class TestCPUCoreLimiting:
    def test_limit_cpu_cores(self, perf_manager) -> None:
        perf_manager.limit_cpu_cores(2)
        assert perf_manager._cpu_limited is True

    def test_restore_cpu_cores(self, perf_manager) -> None:
        perf_manager.limit_cpu_cores(2)
        perf_manager.restore_cpu_cores()
        assert perf_manager._cpu_limited is False


class TestCheckPerformance:
    def test_check_performance_returns_dict(self, perf_manager) -> None:
        result = perf_manager.check_performance()
        assert isinstance(result, dict)
        assert "fps" in result
        assert "fps_average" in result
        assert "gpu_memory_gb" in result
        assert "gpu_memory_ratio" in result
        assert "resolution" in result
        assert "model_size" in result
        assert "warnings" in result
        assert "actions_taken" in result

    def test_check_performance_publishes_warning(self, perf_manager, mock_event_bus) -> None:
        perf_manager._config.min_fps_threshold = 100.0
        for i in range(10):
            perf_manager.record_frame()
            time.sleep(0.01)
        perf_manager._config.event_bus = mock_event_bus
        perf_manager.check_performance()
        assert mock_event_bus.publish.called


class TestGetStats:
    def test_get_stats_returns_dict(self, perf_manager) -> None:
        stats = perf_manager.get_stats()
        assert isinstance(stats, dict)
        assert "fps" in stats
        assert "fps_average" in stats
        assert "resolution" in stats
        assert "model_size" in stats
        assert "cpu_limited" in stats


class TestResetStats:
    def test_reset_clears_history(self, perf_manager) -> None:
        now = time.time()
        for i in range(10):
            perf_manager.record_frame(now + i * 0.1)
        perf_manager.reset_stats()
        assert len(perf_manager._fps_history) == 0
        assert perf_manager.current_fps == 0.0


class TestPortDiscovery:
    def test_find_free_port_returns_int(self) -> None:
        port = find_free_port(start_port=18000)
        assert isinstance(port, int)
        assert 18000 <= port < 18100

    def test_find_free_port_specific(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 19000))
        sock.listen(1)
        try:
            port = find_free_port(start_port=19000, max_attempts=10)
            assert port > 19000
        finally:
            sock.close()

    def test_get_available_port(self) -> None:
        port = get_available_port(start_port=20000)
        assert isinstance(port, int)
        assert port >= 20000

    def test_find_free_port_raises_on_failure(self) -> None:
        with pytest.raises(RuntimeError, match="Could not find free port"):
            bound_ports = []
            try:
                for port in range(21000, 21100):
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        s.bind(("127.0.0.1", port))
                        s.listen(1)
                        bound_ports.append(s)
                    except OSError:
                        continue
                find_free_port(start_port=21000, max_attempts=100)
            finally:
                for s in bound_ports:
                    s.close()


class TestPerformanceMetric:
    def test_metric_values(self) -> None:
        assert PerformanceMetric.FPS_LOW.value == "performance.fps_low"
        assert PerformanceMetric.FPS_CRITICAL.value == "performance.fps_critical"
        assert PerformanceMetric.GPU_MEMORY_HIGH.value == "performance.gpu_memory_high"
        assert PerformanceMetric.GPU_MEMORY_CRITICAL.value == "performance.gpu_memory_critical"
        assert PerformanceMetric.AUTO_SCALE_DOWN.value == "performance.auto_scale_down"
        assert PerformanceMetric.AUTO_SCALE_UP.value == "performance.auto_scale_up"
        assert PerformanceMetric.THROTTLING_APPLIED.value == "performance.throttling_applied"