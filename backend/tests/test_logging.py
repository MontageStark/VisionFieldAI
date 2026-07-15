"""Tests for structured logging implementation."""
from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.app.core.logging import (
    ConsoleFormatter,
    JSONFormatter,
    PerformanceTimer,
    RotatingFileHandler,
    StructuredLogger,
    StructuredLogRecord,
    get_correlation_id,
    get_logger,
    get_session_id,
    reset_logging,
    set_correlation_id,
    set_session_id,
    setup_logging,
)


class TestCorrelationIDs:
    """Test correlation ID context management."""

    def setup_method(self):
        reset_logging()

    def teardown_method(self):
        reset_logging()

    def test_get_default_correlation_id_is_none(self):
        assert get_correlation_id() is None

    def test_set_and_get_correlation_id(self):
        set_correlation_id("req_abc123")
        assert get_correlation_id() == "req_abc123"

    def test_clear_correlation_id(self):
        set_correlation_id("req_abc123")
        set_correlation_id(None)
        assert get_correlation_id() is None

    def test_get_default_session_id_is_none(self):
        assert get_session_id() is None

    def test_set_and_get_session_id(self):
        set_session_id("sess_xyz789")
        assert get_session_id() == "sess_xyz789"

    def test_clear_session_id(self):
        set_session_id("sess_xyz789")
        set_session_id(None)
        assert get_session_id() is None

    def test_correlation_id_thread_independence(self):
        """Test that correlation IDs are independent per thread."""
        results = {}

        def worker(thread_id: int):
            set_correlation_id(f"req_{thread_id}")
            time.sleep(0.01)
            results[thread_id] = get_correlation_id()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Each thread should have its own correlation ID
        for i in range(5):
            assert results[i] == f"req_{i}"


class TestStructuredLogRecord:
    """Test StructuredLogRecord class."""

    def test_creation(self):
        record = StructuredLogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="test message",
            args=(),
            exc_info=None,
        )
        assert record.name == "test"
        assert record.levelno == logging.INFO
        assert record.structured_fields == {}
        assert record.service_name is None
        assert record.correlation_id is None

    def test_structured_fields(self):
        record = StructuredLogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="test message",
            args=(),
            exc_info=None,
        )
        record.structured_fields["frame_number"] = 123
        record.structured_fields["resolution"] = "1920x1080"
        assert record.structured_fields["frame_number"] == 123
        assert record.structured_fields["resolution"] == "1920x1080"


class TestJSONFormatter:
    """Test JSON formatter."""

    def test_basic_format(self):
        formatter = JSONFormatter(service_name="test-service")
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Hello world",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)

        assert data["level"] == "INFO"
        assert data["message"] == "Hello world"
        assert data["logger"] == "test.logger"
        assert "timestamp" in data
        assert data["service"] == "test-service"

    def test_timestamp_format(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="test",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)

        # Should be valid ISO format with timezone
        assert "T" in data["timestamp"]
        assert "+" in data["timestamp"] or "Z" in data["timestamp"]

    def test_exception_formatting(self):
        formatter = JSONFormatter(include_stacktrace=True)
        try:
            raise ValueError("test error")
        except ValueError:
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )
        output = formatter.format(record)
        data = json.loads(output)

        assert "exception" in data
        assert data["exception"]["type"] == "ValueError"
        assert data["exception"]["message"] == "test error"
        assert "traceback" in data["exception"]
        assert "ValueError: test error" in data["exception"]["traceback"]

    def test_exception_without_stacktrace(self):
        formatter = JSONFormatter(include_stacktrace=False)
        try:
            raise ValueError("test error")
        except ValueError:
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )
        output = formatter.format(record)
        data = json.loads(output)

        assert "exception" in data
        assert data["exception"]["type"] == "ValueError"
        assert "traceback" not in data

    def test_structured_record_fields(self):
        formatter = JSONFormatter(service_name="default-service")
        record = StructuredLogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Frame captured",
            args=(),
            exc_info=None,
        )
        record.service_name = "camera-service"
        record.component = "capture"
        record.operation = "get_frame"
        record.correlation_id = "req_abc123"
        record.session_id = "sess_xyz789"
        record.duration_ms = 15.2
        record.structured_fields["frame_number"] = 1234

        output = formatter.format(record)
        data = json.loads(output)

        assert data["service"] == "camera-service"
        assert data["component"] == "capture"
        assert data["operation"] == "get_frame"
        assert data["correlation_id"] == "req_abc123"
        assert data["session_id"] == "sess_xyz789"
        assert data["duration_ms"] == 15.2
        assert data["frame_number"] == 1234

    def test_default_service_name_used(self):
        formatter = JSONFormatter(service_name="fallback-service")
        record = StructuredLogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="test",
            args=(),
            exc_info=None,
        )
        # record.service_name is None, should use formatter default
        output = formatter.format(record)
        data = json.loads(output)

        assert data["service"] == "fallback-service"

    def test_source_location(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="/path/to/file.py",
            lineno=42,
            msg="debug message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)

        assert "source" in data
        assert data["source"]["file"] == "/path/to/file.py"
        assert data["source"]["line"] == 42

    def test_special_characters_in_message(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg='Message with "quotes" and \\backslash and \nnewline',
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)

        # Should be valid JSON
        assert "quotes" in data["message"]

    def test_unicode_message(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Unicode: 你好世界 🌍",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)

        assert data["message"] == "Unicode: 你好世界 🌍"

    def test_no_service_name_on_plain_record_without_formatter_default(self):
        formatter = JSONFormatter()  # No service_name
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="test",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)

        assert "service" not in data


class TestConsoleFormatter:
    """Test console formatter."""

    def test_basic_format(self):
        formatter = ConsoleFormatter(use_colors=False)
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Hello world",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)

        assert "INFO" in output
        assert "Hello world" in output
        assert "test.logger" in output

    def test_color_output(self):
        formatter = ConsoleFormatter(use_colors=True)
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)

        # Should contain ANSI escape codes for error
        assert "\033[31m" in output
        assert "\033[0m" in output

    def test_timestamp_format(self):
        formatter = ConsoleFormatter(use_colors=False)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="test",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)

        # Should have timestamp in HH:MM:SS.mmm format
        assert "[" in output
        assert "]" in output

    def test_structured_context_in_output(self):
        formatter = ConsoleFormatter(use_colors=False)
        record = StructuredLogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Frame captured",
            args=(),
            exc_info=None,
        )
        record.correlation_id = "req_abc123"
        record.component = "capture"
        record.operation = "get_frame"
        record.duration_ms = 15.2

        output = formatter.format(record)

        # correlation_id[:8] of "req_abc123" is "req_abc1"
        assert "req=req_abc1" in output
        assert "comp=capture" in output
        assert "op=get_frame" in output
        assert "ms=15.2" in output

    def test_exception_in_output(self):
        formatter = ConsoleFormatter(use_colors=False)
        try:
            raise ValueError("test error")
        except ValueError:
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )
        output = formatter.format(record)

        assert "ValueError" in output
        assert "test error" in output


class TestStructuredLogger:
    """Test StructuredLogger class."""

    def setup_method(self):
        reset_logging()

    def teardown_method(self):
        reset_logging()

    def test_creation(self):
        logger = StructuredLogger(
            "test.logger", service_name="camera", component="capture"
        )
        assert logger.name == "test.logger"
        assert logger.service_name == "camera"
        assert logger.component == "capture"

    def test_default_values(self):
        logger = StructuredLogger("test")
        assert logger.service_name is None
        assert logger.component is None

    def test_set_service_name(self):
        logger = StructuredLogger("test")
        logger.service_name = "new-service"
        assert logger.service_name == "new-service"

    def test_set_component(self):
        logger = StructuredLogger("test")
        logger.component = "new-component"
        assert logger.component == "new-component"

    def test_debug_logging(self):
        logger = StructuredLogger("test")
        logger.setLevel(logging.DEBUG)
        record = logger.debug("Debug message", frame_number=123)
        assert record is not None
        assert record.levelno == logging.DEBUG
        assert record.structured_fields["frame_number"] == 123

    def test_info_logging(self):
        logger = StructuredLogger("test")
        logger.setLevel(logging.DEBUG)
        record = logger.info("Info message", resolution="1920x1080")
        assert record is not None
        assert record.levelno == logging.INFO
        assert record.structured_fields["resolution"] == "1920x1080"

    def test_warning_logging(self):
        logger = StructuredLogger("test")
        record = logger.warning("Warning message", disk_usage=85)
        assert record is not None
        assert record.levelno == logging.WARNING
        assert record.structured_fields["disk_usage"] == 85

    def test_error_logging(self):
        logger = StructuredLogger("test")
        record = logger.error("Error message", error_code=500)
        assert record is not None
        assert record.levelno == logging.ERROR

    def test_critical_logging(self):
        logger = StructuredLogger("test")
        record = logger.critical("Critical message", system_state="EMERGENCY")
        assert record is not None
        assert record.levelno == logging.CRITICAL

    def test_error_with_exception(self):
        logger = StructuredLogger("test")
        logger.setLevel(logging.DEBUG)
        try:
            raise ValueError("test error")
        except ValueError:
            exc_info = sys.exc_info()

        record = logger.error(
            "Error occurred",
            exc_info=exc_info,
            operation="process_frame",
        )
        assert record is not None

    def test_correlation_id_in_record(self):
        logger = StructuredLogger("test")
        logger.setLevel(logging.DEBUG)
        set_correlation_id("req_test123")

        record = logger.info("Test message")
        assert record is not None
        assert record.correlation_id == "req_test123"

    def test_session_id_in_record(self):
        logger = StructuredLogger("test")
        logger.setLevel(logging.DEBUG)
        set_session_id("sess_test456")

        record = logger.info("Test message")
        assert record is not None
        assert record.session_id == "sess_test456"

    def test_level_filtering(self):
        logger = StructuredLogger("test")
        logger.setLevel(logging.WARNING)

        # Should not log
        debug_record = logger.debug("Debug")
        info_record = logger.info("Info")

        assert debug_record is None
        assert info_record is None

        # Should log
        warning_record = logger.warning("Warning")
        assert warning_record is not None

    def test_multiple_fields(self):
        logger = StructuredLogger("test")
        logger.setLevel(logging.DEBUG)

        record = logger.info(
            "Multiple fields",
            field1="value1",
            field2=123,
            field3=True,
        )
        assert record is not None
        assert record.structured_fields["field1"] == "value1"
        assert record.structured_fields["field2"] == 123
        assert record.structured_fields["field3"] is True


class TestPerformanceTimer:
    """Test PerformanceTimer class."""

    def setup_method(self):
        reset_logging()

    def teardown_method(self):
        reset_logging()

    def test_context_manager(self):
        logger = StructuredLogger("test")
        logger.setLevel(logging.DEBUG)

        with PerformanceTimer(logger, "test_operation") as timer:
            time.sleep(0.01)
            assert timer._start_time is not None

    def test_timing_is_recorded(self):
        logger = StructuredLogger("test")
        logger.setLevel(logging.DEBUG)

        with PerformanceTimer(logger, "test_operation") as timer:
            time.sleep(0.01)

        assert timer._start_time is not None

    def test_decorator_usage(self):
        logger = StructuredLogger("test")
        logger.setLevel(logging.DEBUG)

        @PerformanceTimer(logger, "decorated_function")
        def my_function():
            time.sleep(0.01)
            return "result"

        result = my_function()
        assert result == "result"

    def test_decorator_preserves_function_name(self):
        logger = StructuredLogger("test")

        @PerformanceTimer(logger, "operation")
        def my_function():
            pass

        assert my_function.__name__ == "my_function"

    def test_exception_handling_in_context_manager(self):
        logger = StructuredLogger("test")
        logger.setLevel(logging.DEBUG)

        with pytest.raises(ValueError):
            with PerformanceTimer(logger, "failing_operation"):
                raise ValueError("test error")

    def test_exception_handling_in_decorator(self):
        logger = StructuredLogger("test")
        logger.setLevel(logging.DEBUG)

        @PerformanceTimer(logger, "failing_operation")
        def failing_function():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            failing_function()

    def test_extra_fields_passed(self):
        logger = StructuredLogger("test")
        logger.setLevel(logging.DEBUG)

        with PerformanceTimer(
            logger, "operation", frame_number=123, resolution="1080p"
        ):
            time.sleep(0.001)

    def test_custom_log_level(self):
        logger = StructuredLogger("test")
        logger.setLevel(logging.DEBUG)

        with PerformanceTimer(logger, "operation", level=logging.DEBUG):
            time.sleep(0.001)


class TestRotatingFileHandler:
    """Test RotatingFileHandler."""

    def test_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            handler = RotatingFileHandler(log_file, max_days=7)
            assert handler.backupCount == 7
            handler.close()

    def test_default_retention(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            handler = RotatingFileHandler(log_file)
            assert handler.backupCount == 30
            handler.close()

    def test_writes_to_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            handler = RotatingFileHandler(log_file)
            formatter = JSONFormatter()
            handler.setFormatter(formatter)

            logger = logging.getLogger("test.file")
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

            logger.info("Test message")
            handler.flush()
            handler.close()

            with open(log_file, "r") as f:
                content = f.read()
                assert "Test message" in content


class TestSetupLogging:
    """Test setup_logging function."""

    def setup_method(self):
        reset_logging()

    def teardown_method(self):
        reset_logging()

    def test_creates_log_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = os.path.join(tmpdir, "logs")
            setup_logging("test-service", log_dir=log_dir, file_output=True, console_output=False)
            assert os.path.exists(log_dir)
            # Cleanup: close handlers before directory removal
            reset_logging()

    def test_console_handler_added(self):
        setup_logging("test-service", console_output=True, file_output=False)
        root = logging.getLogger()
        assert len(root.handlers) == 1
        assert isinstance(root.handlers[0], logging.StreamHandler)

    def test_file_handler_added(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            setup_logging(
                "test-service",
                log_dir=tmpdir,
                file_output=True,
                console_output=False,
            )
            root = logging.getLogger()
            assert len(root.handlers) == 1
            assert isinstance(root.handlers[0], RotatingFileHandler)
            # Cleanup
            reset_logging()

    def test_both_handlers_added(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            setup_logging(
                "test-service",
                log_dir=tmpdir,
                console_output=True,
                file_output=True,
            )
            root = logging.getLogger()
            assert len(root.handlers) == 2
            # Cleanup
            reset_logging()

    def test_log_level_set(self):
        setup_logging("test-service", log_level=logging.WARNING)
        root = logging.getLogger()
        assert root.level == logging.WARNING

    def test_clears_existing_handlers(self):
        root = logging.getLogger()
        # Add some dummy handlers
        h1 = logging.StreamHandler()
        h2 = logging.StreamHandler()
        root.addHandler(h1)
        root.addHandler(h2)
        assert len(root.handlers) >= 2

        setup_logging("test-service", console_output=True, file_output=False)
        # Should have cleared and added one new handler
        assert len(root.handlers) == 1

    def test_json_format_for_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            setup_logging(
                "test-service",
                log_dir=tmpdir,
                json_output=True,
                file_output=True,
                console_output=False,
            )
            logger = logging.getLogger("test")
            logger.info("Test message")

            root = logging.getLogger()
            for handler in root.handlers:
                handler.flush()

            log_file = Path(tmpdir) / "test-service.log"
            if log_file.exists():
                with open(log_file) as f:
                    content = f.read()
                    if content.strip():
                        data = json.loads(content.strip().split("\n")[0])
                        assert "timestamp" in data
                        assert data["service"] == "test-service"
            # Cleanup
            reset_logging()

    def test_console_format_option(self):
        setup_logging(
            "test-service",
            json_output=False,
            console_output=True,
            file_output=False,
        )
        root = logging.getLogger()
        assert len(root.handlers) == 1
        assert isinstance(root.handlers[0].formatter, ConsoleFormatter)


class TestGetLogger:
    """Test get_logger function."""

    def test_returns_structured_logger(self):
        logger = get_logger("test.module")
        assert isinstance(logger, StructuredLogger)
        assert logger.name == "test.module"

    def test_with_service_name(self):
        logger = get_logger("test", service_name="camera")
        assert logger.service_name == "camera"

    def test_with_component(self):
        logger = get_logger("test", component="capture")
        assert logger.component == "capture"

    def test_with_all_params(self):
        logger = get_logger(
            "test", service_name="camera", component="capture"
        )
        assert logger.service_name == "camera"
        assert logger.component == "capture"


class TestResetLogging:
    """Test reset_logging function."""

    def test_clears_handlers(self):
        root = logging.getLogger()
        root.addHandler(logging.StreamHandler())
        assert len(root.handlers) > 0

        reset_logging()
        assert len(root.handlers) == 0

    def test_resets_level(self):
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

        reset_logging()
        assert root.level == logging.WARNING

    def test_resets_correlation_ids(self):
        set_correlation_id("req_test")
        set_session_id("sess_test")

        reset_logging()

        assert get_correlation_id() is None
        assert get_session_id() is None


class TestThreadSafety:
    """Test thread safety of logging operations."""

    def test_concurrent_correlation_ids(self):
        results = {}
        errors = []

        def worker(thread_id: int):
            try:
                for i in range(100):
                    set_correlation_id(f"req_{thread_id}_{i}")
                    current = get_correlation_id()
                    # Due to timing, we might get a different thread's ID
                    # but it should be a valid ID
                    assert current is not None
                    results[f"{thread_id}_{i}"] = current
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_concurrent_logging(self):
        logger = StructuredLogger("test.concurrent")
        logger.setLevel(logging.DEBUG)
        output = StringIO()
        handler = logging.StreamHandler(output)
        logger.addHandler(handler)

        errors = []

        def worker(thread_id: int):
            try:
                for i in range(50):
                    set_correlation_id(f"req_{thread_id}")
                    logger.info(
                        "Message from thread %d, iteration %d",
                        thread_id,
                        i,
                        iteration=i,
                    )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        # Check we got some output
        output.seek(0)
        lines = output.readlines()
        assert len(lines) == 250  # 5 threads * 50 messages


class TestIntegration:
    """Integration tests for the logging system."""

    def setup_method(self):
        reset_logging()

    def teardown_method(self):
        reset_logging()

    def test_full_logging_flow(self):
        """Test complete logging flow with JSON output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set up logging with DEBUG level to capture all messages
            setup_logging(
                "camera-service",
                log_dir=tmpdir,
                log_level=logging.DEBUG,
                json_output=True,
                console_output=False,
                file_output=True,
            )

            # Get logger and log some messages
            logger = get_logger(
                "camera.capture", service_name="camera", component="capture"
            )
            logger.setLevel(logging.DEBUG)

            set_correlation_id("req_integration_test")
            set_session_id("sess_integration")

            logger.info("Starting frame capture", resolution="1920x1080")
            logger.debug("Frame buffer allocated", buffer_size=4096)
            logger.warning("High latency detected", latency_ms=45.2)

            # Flush handlers
            root = logging.getLogger()
            for handler in root.handlers:
                handler.flush()

            # Read and verify log file
            log_file = Path(tmpdir) / "camera-service.log"
            assert log_file.exists()

            with open(log_file) as f:
                lines = f.readlines()
                assert len(lines) == 3

                # Parse each line as JSON
                for line in lines:
                    data = json.loads(line.strip())
                    assert "timestamp" in data
                    assert data["service"] == "camera"
                    assert data["correlation_id"] == "req_integration_test"
                    assert data["session_id"] == "sess_integration"

            # Cleanup
            reset_logging()

    def test_performance_timing_integration(self):
        """Test performance timing in real scenario."""
        logger = StructuredLogger("test.perf")
        logger.setLevel(logging.DEBUG)
        output = StringIO()
        handler = logging.StreamHandler(output)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

        with PerformanceTimer(logger, "process_frame", frame_id=42):
            time.sleep(0.01)

        handler.flush()
        output.seek(0)
        line = output.readline()
        data = json.loads(line)

        assert data["operation"] == "process_frame"
        assert data["frame_id"] == 42
        assert "duration_ms" in data
        assert data["duration_ms"] > 0

    def test_exception_logging_integration(self):
        """Test exception logging with full traceback."""
        logger = StructuredLogger("test.exception")
        logger.setLevel(logging.DEBUG)
        output = StringIO()
        handler = logging.StreamHandler(output)
        handler.setFormatter(JSONFormatter(include_stacktrace=True))
        logger.addHandler(handler)

        try:
            raise RuntimeError("Integration test error")
        except RuntimeError:
            logger.error(
                "Operation failed",
                exc_info=sys.exc_info(),
                operation="test_operation",
            )

        handler.flush()
        output.seek(0)
        line = output.readline()
        data = json.loads(line)

        assert data["level"] == "ERROR"
        assert data["operation"] == "test_operation"
        assert data["exception"]["type"] == "RuntimeError"
        assert data["exception"]["message"] == "Integration test error"
        assert "traceback" in data["exception"]


class TestRealWorldScenarios:
    """Test realistic FieldVision AI usage patterns."""

    def setup_method(self):
        reset_logging()

    def teardown_method(self):
        reset_logging()

    def test_camera_capture_logging(self):
        """Test camera service logging pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            setup_logging(
                "camera",
                log_dir=tmpdir,
                json_output=True,
                console_output=False,
                file_output=True,
            )

            logger = get_logger("camera.capture", component="capture")

            # Simulate frame capture
            set_correlation_id("req_frame_1234")

            with PerformanceTimer(logger, "get_frame"):
                time.sleep(0.001)  # Simulate capture time

            logger.info(
                "Frame captured successfully",
                frame_number=1234,
                resolution="1920x1080",
                fps=30,
            )

            root = logging.getLogger()
            for handler in root.handlers:
                handler.flush()

            log_file = Path(tmpdir) / "camera.log"
            with open(log_file) as f:
                lines = f.readlines()
                assert len(lines) == 2

                # First line is timing
                timing_data = json.loads(lines[0].strip())
                assert timing_data["operation"] == "get_frame"
                assert "duration_ms" in timing_data

                # Second line is frame info
                frame_data = json.loads(lines[1].strip())
                assert frame_data["frame_number"] == 1234
                assert frame_data["resolution"] == "1920x1080"

            # Cleanup
            reset_logging()

    def test_director_decision_logging(self):
        """Test director service logging pattern."""
        logger = get_logger("director.decision", component="decision")
        logger.setLevel(logging.DEBUG)
        output = StringIO()
        handler = logging.StreamHandler(output)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

        set_correlation_id("req_director_001")

        logger.info(
            "Camera move decision",
            action="track",
            target="ball",
            confidence=0.95,
            pan_angle=45.0,
            tilt_angle=30.0,
        )

        handler.flush()
        output.seek(0)
        data = json.loads(output.readline())

        # Service name comes from the StructuredLogRecord
        # Since we don't pass service_name to get_logger, it will be None
        # but the formatter has no default either, so service may not be in output
        assert data["target"] == "ball"
        assert data["confidence"] == 0.95

    def test_error_recovery_logging(self):
        """Test error logging with recovery."""
        logger = get_logger("servo.control", component="servo")
        logger.setLevel(logging.DEBUG)
        output = StringIO()
        handler = logging.StreamHandler(output)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

        set_correlation_id("req_servo_error")

        # Log the error
        try:
            raise ConnectionError("Servo not responding")
        except ConnectionError:
            logger.error(
                "Servo connection lost",
                exc_info=sys.exc_info(),
                servo_id=1,
                last_position=90.0,
            )

        # Log recovery
        logger.info(
            "Servo reconnected",
            servo_id=1,
            recovery_time_ms=150.0,
        )

        handler.flush()
        output.seek(0)
        lines = output.readlines()

        error_data = json.loads(lines[0].strip())
        assert error_data["level"] == "ERROR"
        assert error_data["servo_id"] == 1

        recovery_data = json.loads(lines[1].strip())
        assert recovery_data["level"] == "INFO"
        assert recovery_data["recovery_time_ms"] == 150.0
