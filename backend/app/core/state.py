"""State machine for FieldVision AI system."""
from __future__ import annotations

import threading
import time
from collections import deque
from enum import IntEnum
from typing import Any, Callable, Dict, List, Optional, Tuple


class SystemState(IntEnum):
    """System states for FieldVision AI."""
    BOOTING = 0
    CONNECTING = 1
    IDLE = 2
    STREAMING = 3
    TRACKING = 4
    MANUAL = 5
    HOMING = 6
    EMERGENCY_STOP = 7
    ERROR = 8


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


# Valid transitions as specified
VALID_TRANSITIONS: Dict[SystemState, List[SystemState]] = {
    SystemState.BOOTING: [SystemState.CONNECTING, SystemState.ERROR],
    SystemState.CONNECTING: [SystemState.IDLE, SystemState.ERROR],
    SystemState.IDLE: [
        SystemState.STREAMING,
        SystemState.MANUAL,
        SystemState.HOMING,
        SystemState.EMERGENCY_STOP,
        SystemState.ERROR,
    ],
    SystemState.STREAMING: [
        SystemState.TRACKING,
        SystemState.IDLE,
        SystemState.EMERGENCY_STOP,
        SystemState.ERROR,
    ],
    SystemState.TRACKING: [
        SystemState.STREAMING,
        SystemState.IDLE,
        SystemState.EMERGENCY_STOP,
        SystemState.ERROR,
    ],
    SystemState.MANUAL: [
        SystemState.IDLE,
        SystemState.EMERGENCY_STOP,
        SystemState.ERROR,
    ],
    SystemState.HOMING: [
        SystemState.IDLE,
        SystemState.EMERGENCY_STOP,
        SystemState.ERROR,
    ],
    SystemState.EMERGENCY_STOP: [SystemState.BOOTING, SystemState.ERROR],
    SystemState.ERROR: [SystemState.BOOTING],
}


class SystemStateMachine:
    """Thread-safe state machine with transition validation, callbacks, and history."""

    def __init__(self, initial_state: SystemState = SystemState.BOOTING) -> None:
        """Initialize the state machine.
        
        Args:
            initial_state: Starting state (default: BOOTING)
        """
        self._state = initial_state
        self._lock = threading.RLock()
        self._history: deque = deque(maxlen=10)
        self._enter_callbacks: Dict[SystemState, List[Callable[..., Any]]] = {
            state: [] for state in SystemState
        }
        self._exit_callbacks: Dict[SystemState, List[Callable[..., Any]]] = {
            state: [] for state in SystemState
        }
        
        # Record initial state in history
        self._history.append({
            "from": None,
            "to": initial_state,
            "timestamp": time.time(),
            "callbacks_executed": True,
        })
    
    @property
    def state(self) -> SystemState:
        """Get current state."""
        return self._state
    
    @property
    def history(self) -> List[dict]:
        """Get state transition history (last 10 transitions)."""
        with self._lock:
            return list(self._history)
    
    def on_enter(self, state: SystemState, callback: Callable[..., Any]) -> None:
        """Register a callback to be called when entering a state.
        
        Args:
            state: State to register callback for
            callback: Function to call when entering the state
        """
        with self._lock:
            self._enter_callbacks[state].append(callback)
    
    def on_exit(self, state: SystemState, callback: Callable[..., Any]) -> None:
        """Register a callback to be called when exiting a state.
        
        Args:
            state: State to register callback for
            callback: Function to call when exiting the state
        """
        with self._lock:
            self._exit_callbacks[state].append(callback)
    
    def transition(self, new_state: SystemState, **kwargs: Any) -> None:
        """Transition to a new state.
        
        Args:
            new_state: Target state to transition to
            **kwargs: Additional data to pass to callbacks
            
        Raises:
            InvalidTransitionError: If transition is not allowed
        """
        with self._lock:
            old_state = self._state
            
            # Validate transition
            if new_state not in VALID_TRANSITIONS.get(old_state, []):
                raise InvalidTransitionError(
                    f"Invalid transition from {old_state.name} to {new_state.name}"
                )
            
            # Execute exit callbacks
            for callback in self._exit_callbacks[old_state]:
                callback(old_state, new_state, **kwargs)
            
            # Update state
            self._state = new_state
            
            # Execute enter callbacks
            for callback in self._enter_callbacks[new_state]:
                callback(old_state, new_state, **kwargs)
            
            # Record history
            self._history.append({
                "from": old_state,
                "to": new_state,
                "timestamp": time.time(),
                "callbacks_executed": True,
            })
    
    def get_valid_transitions(self) -> List[SystemState]:
        """Get list of valid transitions from current state.
        
        Returns:
            List of valid target states
        """
        with self._lock:
            return VALID_TRANSITIONS.get(self._state, []).copy()
    
    def can_transition(self, target_state: SystemState) -> bool:
        """Check if transition to target state is valid.
        
        Args:
            target_state: State to check
            
        Returns:
            True if transition is valid
        """
        with self._lock:
            return target_state in VALID_TRANSITIONS.get(self._state, [])
    
    def clear_history(self) -> None:
        """Clear state transition history."""
        with self._lock:
            self._history.clear()
            # Add current state as first entry
            self._history.append({
                "from": None,
                "to": self._state,
                "timestamp": time.time(),
                "callbacks_executed": True,
            })
    
    def __repr__(self) -> str:
        """String representation of state machine."""
        return f"SystemStateMachine(state={self._state.name})"


def create_default_machine() -> SystemStateMachine:
    """Create a state machine with default configuration.
    
    Returns:
        SystemStateMachine initialized to BOOTING state
    """
    return SystemStateMachine(SystemState.BOOTING)