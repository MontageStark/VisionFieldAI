"""Event bus for FieldVision AI system."""
from __future__ import annotations

import asyncio
import logging
import threading
import time
from collections import deque
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Event types for the FieldVision AI system."""

    # System events
    STATE_CHANGED = "state.changed"
    ERROR_OCCURRED = "error.occurred"
    HEALTH_CHECK = "health.check"

    # Camera events
    FRAME_CAPTURED = "camera.frame_captured"
    CAMERA_CONNECTED = "camera.connected"
    CAMERA_DISCONNECTED = "camera.disconnected"

    # Vision events
    DETECTIONS_COMPLETE = "vision.detections_complete"
    TRACKING_UPDATED = "tracking.updated"
    PREDICTION_UPDATED = "prediction.prediction_updated"

    # Director events
    DIRECTOR_DECISION = "director.decision"
    CAMERA_STATE_UPDATED = "director.camera_state_updated"
    # CAMERA_MOVE deprecated — kept for compat during transition
    CAMERA_MOVE = "director.camera_move"

    # Servo events
    SERVO_COMMAND = "servo.command"
    SERVO_POSITION = "servo.position"
    SERVO_ERROR = "servo.error"

    # Streaming events
    STREAM_STARTED = "stream.started"
    STREAM_STOPPED = "stream.stopped"
    STREAM_ERROR = "stream.error"


class EventPriority(int, Enum):
    """Event priority levels."""

    NORMAL = 0
    HIGH = 1
    CRITICAL = 2


class Event:
    """Represents an event published to the bus."""

    __slots__ = ("event_type", "data", "priority", "timestamp", "source")

    def __init__(
        self,
        event_type: EventType,
        data: Optional[Dict[str, Any]] = None,
        priority: EventPriority = EventPriority.NORMAL,
        source: Optional[str] = None,
    ) -> None:
        """Initialize an event.

        Args:
            event_type: Type of event
            data: Optional event payload
            priority: Event priority level
            source: Optional source identifier
        """
        self.event_type = event_type
        self.data = data or {}
        self.priority = priority
        self.timestamp = time.time()
        self.source = source

    def __repr__(self) -> str:
        return (
            f"Event(type={self.event_type.value}, priority={self.priority.name}, "
            f"source={self.source})"
        )


# Handler type: can be sync or async
HandlerFunc = Callable[..., Any]
AsyncHandlerFunc = Callable[..., Coroutine[Any, Any, Any]]


class EventBus:
    """Async event bus with publish/subscribe pattern.

    Features:
    - Event type filtering
    - Wildcard subscriptions ("*")
    - Event history (last 100 events)
    - Thread-safe publish/subscribe
    - Event priority (normal, high, critical)
    """

    def __init__(self, history_size: int = 100) -> None:
        """Initialize the event bus.

        Args:
            history_size: Maximum number of events to keep in history
        """
        self._lock = threading.RLock()
        self._subscriptions: Dict[str, List[HandlerFunc]] = {}
        self._history: deque[Event] = deque(maxlen=history_size)
        self._running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._tasks: List[asyncio.Task[None]] = []

    def subscribe(
        self, event_type: Union[EventType, str], handler: HandlerFunc
    ) -> None:
        """Subscribe to an event type.

        Args:
            event_type: Event type to subscribe to, or "*" for all events
            handler: Callback function to invoke when event is published
        """
        with self._lock:
            key = event_type if isinstance(event_type, str) else event_type.value
            if key not in self._subscriptions:
                self._subscriptions[key] = []
            if handler not in self._subscriptions[key]:
                self._subscriptions[key].append(handler)

    def unsubscribe(
        self, event_type: Union[EventType, str], handler: HandlerFunc
    ) -> bool:
        """Unsubscribe from an event type.

        Args:
            event_type: Event type to unsubscribe from
            handler: Handler to remove

        Returns:
            True if handler was found and removed
        """
        with self._lock:
            key = event_type if isinstance(event_type, str) else event_type.value
            if key in self._subscriptions:
                try:
                    self._subscriptions[key].remove(handler)
                    return True
                except ValueError:
                    pass
            return False

    def publish(
        self,
        event_type: EventType,
        data: Optional[Dict[str, Any]] = None,
        priority: EventPriority = EventPriority.NORMAL,
        source: Optional[str] = None,
    ) -> Event:
        """Publish an event synchronously.

        All matching handlers are called immediately in the calling thread.
        One failing handler does not prevent others from running.

        Args:
            event_type: Type of event to publish
            data: Optional event payload
            priority: Event priority level
            source: Optional source identifier

        Returns:
            The published Event object
        """
        event = Event(event_type, data, priority, source)

        with self._lock:
            self._history.append(event)

        # Collect handlers: specific type + wildcard
        handlers = self._get_handlers(event_type)

        # Sort by priority (critical first)
        # We don't sort handlers here — priority is on the event, not handler.
        # Handlers are invoked in registration order.

        for handler in handlers:
            try:
                handler(event)
            except Exception:
                logger.exception(
                    "Error in handler %s for event %s",
                    handler.__name__ if hasattr(handler, "__name__") else str(handler),
                    event_type.value,
                )

        return event

    def publish_async(
        self,
        event_type: EventType,
        data: Optional[Dict[str, Any]] = None,
        priority: EventPriority = EventPriority.NORMAL,
        source: Optional[str] = None,
    ) -> Event:
        """Publish an event asynchronously via fire-and-forget tasks.

        Matching handlers are scheduled as async tasks on the running event loop.
        If no loop is running, falls back to synchronous publish.

        Args:
            event_type: Type of event to publish
            data: Optional event payload
            priority: Event priority level
            source: Optional source identifier

        Returns:
            The published Event object
        """
        event = Event(event_type, data, priority, source)

        with self._lock:
            self._history.append(event)

        handlers = self._get_handlers(event_type)

        # Try to schedule async tasks
        loop = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            pass

        if loop and loop.is_running():
            for handler in handlers:
                if asyncio.iscoroutinefunction(handler):
                    task = loop.create_task(self._safe_async_call(handler, event))
                    self._tasks.append(task)
                else:
                    # Sync handler in async context — run in executor
                    loop.run_in_executor(None, self._safe_sync_call, handler, event)
        else:
            # No running loop — call synchronously
            for handler in handlers:
                self._safe_sync_call(handler, event)

        return event

    async def _safe_async_call(
        self, handler: AsyncHandlerFunc, event: Event
    ) -> None:
        """Safely call an async handler, catching exceptions."""
        try:
            await handler(event)
        except Exception:
            logger.exception(
                "Error in async handler %s for event %s",
                handler.__name__ if hasattr(handler, "__name__") else str(handler),
                event.event_type.value,
            )

    @staticmethod
    def _safe_sync_call(handler: HandlerFunc, event: Event) -> None:
        """Safely call a sync handler, catching exceptions."""
        try:
            handler(event)
        except Exception:
            logger.exception(
                "Error in handler %s for event %s",
                handler.__name__ if hasattr(handler, "__name__") else str(handler),
                event.event_type.value,
            )

    def _get_handlers(self, event_type: EventType) -> List[HandlerFunc]:
        """Get all handlers for an event type, including wildcards.

        Args:
            event_type: Event type to get handlers for

        Returns:
            Combined list of specific and wildcard handlers
        """
        with self._lock:
            handlers: List[HandlerFunc] = []
            # Specific handlers first
            if event_type.value in self._subscriptions:
                handlers.extend(self._subscriptions[event_type.value])
            # Wildcard handlers
            if "*" in self._subscriptions:
                handlers.extend(self._subscriptions["*"])
            return handlers

    @property
    def history(self) -> List[Event]:
        """Get event history (last N events)."""
        with self._lock:
            return list(self._history)

    @property
    def subscription_count(self) -> int:
        """Get total number of subscriptions across all event types."""
        with self._lock:
            return sum(len(handlers) for handlers in self._subscriptions.values())

    def get_subscribers(self, event_type: Union[EventType, str]) -> List[HandlerFunc]:
        """Get list of subscribers for a specific event type.

        Args:
            event_type: Event type to check

        Returns:
            List of subscribed handlers
        """
        key = event_type if isinstance(event_type, str) else event_type.value
        with self._lock:
            return list(self._subscriptions.get(key, []))

    def clear_history(self) -> None:
        """Clear event history."""
        with self._lock:
            self._history.clear()

    def clear_subscriptions(self) -> None:
        """Remove all subscriptions."""
        with self._lock:
            self._subscriptions.clear()

    def has_subscribers(self, event_type: EventType) -> bool:
        """Check if an event type has any subscribers (including wildcard).

        Args:
            event_type: Event type to check

        Returns:
            True if there are subscribers
        """
        with self._lock:
            return (
                event_type.value in self._subscriptions
                or "*" in self._subscriptions
            )

    async def wait_for(
        self,
        event_type: EventType,
        timeout: Optional[float] = None,
    ) -> Event:
        """Wait for a specific event type.

        Args:
            event_type: Event type to wait for
            timeout: Maximum seconds to wait (None = forever)

        Returns:
            The received Event

        Raises:
            asyncio.TimeoutError: If timeout is reached
        """
        future: asyncio.Future[Event] = asyncio.get_event_loop().create_future()

        def on_event(event: Event) -> None:
            if not future.done():
                future.set_result(event)

        self.subscribe(event_type, on_event)
        try:
            return await asyncio.wait_for(future, timeout)
        finally:
            self.unsubscribe(event_type, on_event)

    def __repr__(self) -> str:
        return (
            f"EventBus(subscriptions={self.subscription_count}, "
            f"history={len(self._history)})"
        )


# Module-level singleton
_bus: Optional[EventBus] = None
_bus_lock = threading.Lock()


def get_event_bus(history_size: int = 100) -> EventBus:
    """Get the global event bus instance.

    Args:
        history_size: History size (only used on first call)

    Returns:
        Global EventBus instance
    """
    global _bus
    if _bus is None:
        with _bus_lock:
            if _bus is None:
                _bus = EventBus(history_size=history_size)
    return _bus


def reset_event_bus() -> None:
    """Reset the global event bus instance."""
    global _bus
    with _bus_lock:
        _bus = None
