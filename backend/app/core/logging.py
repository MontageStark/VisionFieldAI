"""Structured logging for FieldVision AI system."""
from __future__ import annotations

import contextvars
import functools
import inspect
import json
import logging
import logging.handlers
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar, cast

# Context variable for correlation IDs - thread-safe and async-safe
_correlation_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "correlation_id", default=None
)
_session_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "session_id", default=None
)

F = TypeVar("F", bound=Callable[..., Any])


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID.

    Returns:
        Current correlation ID or None
    """
    return _correlation_id.get()


def set_correlation_id(correlation_id: Optional[str]) -> None:
    """Set the correlation ID for the current context.

    Args:
        correlation_id: Correlation ID to set (None to clear)
    """
    _correlation_id.set(correlation_id)


def get_session_id() -> Optional[str]:
    """Get the current session ID.

    Returns:
        Current session ID or None
    """
    return _session_id.get()


def set_session_id(session_id: Optional[str]) -> None:
    """Set the session ID for the current context.

    Args:
        session_id: Session ID to set (None to clear)
    """
    _session_id.set(session_id)


class StructuredLogRecord(logging.LogRecord):
    """Extended LogRecord with structured fields."""

    __slots__ = (
        "structured_fields",
        "service_name",
        "component",
        "operation",
        "correlation_id",
        "session_id",
        "duration_ms",
    )

    def __init__(
        self,
        name: str,
        level: int,
        pathname: str,
        lineno: int,
        msg: str,
        args: tuple,
        exc_info: Any,
        func: Optional[str] = None,
        sinfo: Optional[str] = None,
    ) -> None:
        super().__init__(name, level, pathname, lineno, msg, args, exc_info, func, sinfo)
        self.structured_fields: Dict[str, Any] = {}
        self.service_name: Optional[str] = None
        self.component: Optional[str] = None
        self.operation: Optional[str] = None
        self.correlation_id: Optional[str] = None
        self.session_id: Optional[str] = None
        self.duration_ms: Optional[float] = None


class JSONFormatter(logging.Formatter):
    """Formats log records as JSON output."""

    def __init__(
        self,
        service_name: Optional[str] = None,
        include_stacktrace: bool = True,
    ) -> None:
        """Initialize JSON formatter.

        Args:
            service_name: Default service name for all log entries
            include_stacktrace: Whether to include stack traces for exceptions
        """
        super().__init__()
        self._service_name = service_name
        self._include_stacktrace = include_stacktrace

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON string representation
        """
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add service name (from StructuredLogRecord or formatter default)
        if isinstance(record, StructuredLogRecord):
            if record.service_name or self._service_name:
                log_entry["service"] = record.service_name or self._service_name
            if record.component:
                log_entry["component"] = record.component
            if record.operation:
                log_entry["operation"] = record.operation
            if record.correlation_id:
                log_entry["correlation_id"] = record.correlation_id
            if record.session_id:
                log_entry["session_id"] = record.session_id
            if record.duration_ms is not None:
                log_entry["duration_ms"] = record.duration_ms
            # Add any extra structured fields
            log_entry.update(record.structured_fields)
        elif self._service_name:
            # For standard LogRecords, still include service name
            log_entry["service"] = self._service_name

        # Add source location for debug and above
        if record.levelno >= logging.DEBUG:
            log_entry["source"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            }

        # Add exception info if present
        if record.exc_info and record.exc_info[1] is not None:
            if self._include_stacktrace:
                log_entry["exception"] = {
                    "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                    "message": str(record.exc_info[1]),
                    "traceback": self.formatException(record.exc_info),
                }
            else:
                log_entry["exception"] = {
                    "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                    "message": str(record.exc_info[1]),
                }

        return json.dumps(log_entry, default=str, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """Human-readable formatter for console output with color coding."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def __init__(self, use_colors: Optional[bool] = None) -> None:
        """Initialize console formatter.

        Args:
            use_colors: Whether to use ANSI color codes. None = auto-detect.
        """
        super().__init__()
        if use_colors is None:
            self._use_colors = sys.stderr.isatty()
        else:
            self._use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        """Format log record for console output.

        Args:
            record: Log record to format

        Returns:
            Formatted string
        """
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S.%f")[:-3]
        level = record.levelname.ljust(8)

        if self._use_colors:
            color = self.COLORS.get(record.levelname, "")
            level = f"{color}{level}{self.RESET}"

        parts = [f"[{timestamp}] {level} {record.name}: {record.getMessage()}"]

        # Add structured context if available
        if isinstance(record, StructuredLogRecord):
            context_parts = []
            if record.correlation_id:
                context_parts.append(f"req={record.correlation_id[:8]}")
            if record.component:
                context_parts.append(f"comp={record.component}")
            if record.operation:
                context_parts.append(f"op={record.operation}")
            if record.duration_ms is not None:
                context_parts.append(f"ms={record.duration_ms:.1f}")
            if context_parts:
                parts.append(f" ({' '.join(context_parts)})")

        # Add exception info if present
        if record.exc_info and record.exc_info[1] is not None:
            parts.append(f"\n{self.formatException(record.exc_info)}")

        return "".join(parts)


class StructuredLogger:
    """Logger with structured fields and correlation ID support.

    Wraps a standard logging.Logger and adds methods for structured logging
    and performance timing.
    """

    def __init__(
        self,
        name: str,
        service_name: Optional[str] = None,
        component: Optional[str] = None,
    ) -> None:
        """Initialize structured logger.

        Args:
            name: Logger name
            service_name: Service name for log entries
            component: Component name for log entries
        """
        self._logger = logging.getLogger(name)
        self._service_name = service_name
        self._component = component

    @property
    def name(self) -> str:
        """Get logger name."""
        return self._logger.name

    @property
    def propagate(self) -> bool:
        """Get propagation setting."""
        return self._logger.propagate

    @propagate.setter
    def propagate(self, value: bool) -> None:
        """Set propagation setting."""
        self._logger.propagate = value

    @property
    def handlers(self) -> list:
        """Get logger handlers."""
        return self._logger.handlers

    def setLevel(self, level: int) -> None:
        """Set the logging level."""
        self._logger.setLevel(level)

    def addHandler(self, handler: logging.Handler) -> None:
        """Add a handler."""
        self._logger.addHandler(handler)

    def isEnabledFor(self, level: int) -> bool:
        """Check if level is enabled."""
        return self._logger.isEnabledFor(level)

    def _log_structured(
        self,
        level: int,
        msg: str,
        args: tuple,
        exc_info: Any = None,
        extra: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        **kwargs: Any,
    ) -> Optional[StructuredLogRecord]:
        """Create and log a structured record.

        Args:
            level: Log level
            msg: Message format string
            args: Message format args
            exc_info: Exception info tuple
            extra: Extra fields to include
            duration_ms: Optional duration in milliseconds
            **kwargs: Additional structured fields

        Returns:
            The created log record
        """
        if not self.isEnabledFor(level):
            return None

        # Get caller info
        frame = inspect.currentframe()
        if frame and frame.f_back and frame.f_back.f_back:
            caller_frame = frame.f_back.f_back
            pathname = caller_frame.f_code.co_filename
            lineno = caller_frame.f_lineno
            func = caller_frame.f_code.co_name
        else:
            pathname = ""
            lineno = 0
            func = ""

        # Create structured record
        record = StructuredLogRecord(
            name=self.name,
            level=level,
            pathname=pathname,
            lineno=lineno,
            msg=msg,
            args=args,
            exc_info=exc_info,
            func=func,
        )

        # Set structured fields
        record.service_name = self._service_name
        record.component = self._component
        record.correlation_id = get_correlation_id()
        record.session_id = get_session_id()

        # Apply extra and kwargs
        if extra:
            record.structured_fields.update(extra)
        if kwargs:
            record.structured_fields.update(kwargs)

        # Set duration_ms before emitting
        if duration_ms is not None:
            record.duration_ms = duration_ms

        # Use the wrapped logger's handle() to pass our StructuredLogRecord
        # This properly propagates to parent loggers (e.g., root)
        self._logger.handle(record)

        return record

    def debug(
        self, msg: str, *args: Any, extra: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Optional[StructuredLogRecord]:
        """Log at DEBUG level with structured fields.

        Args:
            msg: Message format string
            *args: Message format args
            extra: Extra fields to include
            **kwargs: Additional structured fields

        Returns:
            StructuredLogRecord or None if level not enabled
        """
        return self._log_structured(logging.DEBUG, msg, args, extra=extra, **kwargs)

    def info(
        self, msg: str, *args: Any, extra: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Optional[StructuredLogRecord]:
        """Log at INFO level with structured fields.

        Args:
            msg: Message format string
            *args: Message format args
            extra: Extra fields to include
            **kwargs: Additional structured fields

        Returns:
            StructuredLogRecord or None if level not enabled
        """
        return self._log_structured(logging.INFO, msg, args, extra=extra, **kwargs)

    def warning(
        self, msg: str, *args: Any, extra: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Optional[StructuredLogRecord]:
        """Log at WARNING level with structured fields.

        Args:
            msg: Message format string
            *args: Message format args
            extra: Extra fields to include
            **kwargs: Additional structured fields

        Returns:
            StructuredLogRecord or None if level not enabled
        """
        return self._log_structured(logging.WARNING, msg, args, extra=extra, **kwargs)

    def error(
        self,
        msg: str,
        *args: Any,
        exc_info: Any = None,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Optional[StructuredLogRecord]:
        """Log at ERROR level with structured fields.

        Args:
            msg: Message format string
            *args: Message format args
            exc_info: Exception info tuple
            extra: Extra fields to include
            **kwargs: Additional structured fields

        Returns:
            StructuredLogRecord or None if level not enabled
        """
        return self._log_structured(
            logging.ERROR, msg, args, exc_info=exc_info, extra=extra, **kwargs
        )

    def critical(
        self,
        msg: str,
        *args: Any,
        exc_info: Any = None,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Optional[StructuredLogRecord]:
        """Log at CRITICAL level with structured fields.

        Args:
            msg: Message format string
            *args: Message format args
            exc_info: Exception info tuple
            extra: Extra fields to include
            **kwargs: Additional structured fields

        Returns:
            StructuredLogRecord or None if level not enabled
        """
        return self._log_structured(
            logging.CRITICAL, msg, args, exc_info=exc_info, extra=extra, **kwargs
        )

    def log_with_duration(
        self,
        level: int,
        msg: str,
        duration_ms: float,
        *args: Any,
        **kwargs: Any,
    ) -> Optional[StructuredLogRecord]:
        """Log with performance timing information.

        Args:
            level: Log level
            msg: Message format string
            duration_ms: Duration in milliseconds
            *args: Message format args
            **kwargs: Additional structured fields

        Returns:
            StructuredLogRecord or None if level not enabled
        """
        return self._log_structured(level, msg, args, duration_ms=duration_ms, **kwargs)

    @property
    def service_name(self) -> Optional[str]:
        """Get the service name."""
        return self._service_name

    @service_name.setter
    def service_name(self, value: Optional[str]) -> None:
        """Set the service name."""
        self._service_name = value

    @property
    def component(self) -> Optional[str]:
        """Get the component name."""
        return self._component

    @component.setter
    def component(self, value: Optional[str]) -> None:
        """Set the component name."""
        self._component = value


class PerformanceTimer:
    """Context manager and decorator for timing operations.

    Usage as context manager:
        with PerformanceTimer(logger, "capture_frame", frame_number=123):
            # do work
            pass

    Usage as decorator:
        @PerformanceTimer(logger, "capture_frame")
        def capture_frame():
            # do work
            pass
    """

    def __init__(
        self,
        logger: StructuredLogger,
        operation: str,
        level: int = logging.INFO,
        **extra_fields: Any,
    ) -> None:
        """Initialize performance timer.

        Args:
            logger: StructuredLogger instance
            operation: Operation name
            level: Log level for timing message
            **extra_fields: Additional fields to include in log
        """
        self._logger = logger
        self._operation = operation
        self._level = level
        self._extra_fields = extra_fields
        self._start_time: Optional[float] = None

    def __enter__(self) -> "PerformanceTimer":
        """Start timing."""
        self._start_time = time.perf_counter()
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[Exception],
        exc_tb: Any,
    ) -> None:
        """End timing and log duration."""
        if self._start_time is None:
            return

        duration_ms = (time.perf_counter() - self._start_time) * 1000

        # Build extra fields with operation included
        extra = dict(self._extra_fields)
        extra["operation"] = self._operation

        if exc_type is not None:
            self._logger.error(
                "Operation failed: %s",
                self._operation,
                exc_info=(exc_type, exc_val, exc_tb),
                duration_ms=duration_ms,
                **extra,
            )
        else:
            self._logger.log_with_duration(
                self._level,
                "Operation completed: %s",
                duration_ms=duration_ms,
                **extra,
            )

    def __call__(self, func: F) -> F:
        """Use as decorator."""

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with PerformanceTimer(
                self._logger, self._operation, self._level, **self._extra_fields
            ):
                return func(*args, **kwargs)

        return cast(F, wrapper)


class RotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    """File handler with daily rotation and max retention."""

    def __init__(
        self,
        filename: str,
        max_days: int = 30,
        encoding: str = "utf-8",
    ) -> None:
        """Initialize rotating file handler.

        Args:
            filename: Log file path
            max_days: Maximum days to retain (default: 30)
            encoding: File encoding
        """
        super().__init__(
            filename,
            when="midnight",
            interval=1,
            backupCount=max_days,
            encoding=encoding,
        )


def setup_logging(
    service_name: str,
    log_dir: str = "logs",
    log_level: int = logging.INFO,
    json_output: bool = True,
    console_output: bool = True,
    file_output: bool = True,
    max_days: int = 30,
    include_stacktrace: bool = True,
) -> logging.Logger:
    """Set up structured logging for a service.

    Args:
        service_name: Name of the service
        log_dir: Directory for log files
        log_level: Minimum log level
        json_output: Whether to output JSON format
        console_output: Whether to output to console
        file_output: Whether to output to file
        max_days: Maximum days to retain log files
        include_stacktrace: Whether to include stack traces

    Returns:
        Configured root logger for the service
    """
    # Create log directory if needed
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear existing handlers
    logger.handlers.clear()

    # JSON formatter
    json_formatter = JSONFormatter(
        service_name=service_name,
        include_stacktrace=include_stacktrace,
    )

    # Console formatter
    console_formatter = ConsoleFormatter(use_colors=False)

    # Add console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(log_level)
        if json_output:
            console_handler.setFormatter(json_formatter)
        else:
            console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # Add file handler
    if file_output:
        log_file = log_path / f"{service_name}.log"
        file_handler = RotatingFileHandler(
            str(log_file),
            max_days=max_days,
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(json_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(
    name: str,
    service_name: Optional[str] = None,
    component: Optional[str] = None,
) -> StructuredLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name
        service_name: Service name (optional, overrides module name)
        component: Component name (optional)

    Returns:
        StructuredLogger instance
    """
    logger = StructuredLogger(name, service_name=service_name, component=component)
    return logger


# Module-level lock for thread safety
_init_lock = threading.Lock()


def reset_logging() -> None:
    """Reset logging configuration. Useful for testing."""
    with _init_lock:
        root = logging.getLogger()
        # Close all handlers to release file handles
        for handler in root.handlers[:]:
            try:
                handler.close()
            except Exception:
                pass
        root.handlers.clear()
        root.setLevel(logging.WARNING)

        # Reset correlation IDs
        set_correlation_id(None)
        set_session_id(None)
