"""Tests for state machine implementation."""
from __future__ import annotations

import threading
import time
from typing import List
from unittest.mock import MagicMock

import pytest

from backend.app.core.state import (
    SystemState,
    SystemStateMachine,
    InvalidTransitionError,
    VALID_TRANSITIONS,
    create_default_machine,
)


class TestSystemState:
    """Test SystemState enum."""
    
    def test_state_values(self):
        """Verify state values match specification."""
        assert SystemState.BOOTING == 0
        assert SystemState.CONNECTING == 1
        assert SystemState.IDLE == 2
        assert SystemState.STREAMING == 3
        assert SystemState.TRACKING == 4
        assert SystemState.MANUAL == 5
        assert SystemState.HOMING == 6
        assert SystemState.EMERGENCY_STOP == 7
        assert SystemState.ERROR == 8
    
    def test_state_count(self):
        """Verify we have exactly 9 states."""
        assert len(SystemState) == 9
    
    def test_valid_transitions_defined(self):
        """Verify all states have transition definitions."""
        for state in SystemState:
            assert state in VALID_TRANSITIONS
    
    def test_transition_targets_are_states(self):
        """Verify all transition targets are valid states."""
        for source, targets in VALID_TRANSITIONS.items():
            assert isinstance(source, SystemState)
            for target in targets:
                assert isinstance(target, SystemState)


class TestStateMachineInitialization:
    """Test state machine initialization."""
    
    def test_default_initial_state(self):
        """Test default initial state is BOOTING."""
        sm = SystemStateMachine()
        assert sm.state == SystemState.BOOTING
    
    def test_custom_initial_state(self):
        """Test custom initial state."""
        sm = SystemStateMachine(SystemState.IDLE)
        assert sm.state == SystemState.IDLE
    
    def test_initial_history(self):
        """Test initial history contains one entry."""
        sm = SystemStateMachine()
        history = sm.history
        assert len(history) == 1
        assert history[0]["from"] is None
        assert history[0]["to"] == SystemState.BOOTING
    
    def test_create_default_machine(self):
        """Test factory function."""
        sm = create_default_machine()
        assert sm.state == SystemState.BOOTING


class TestStateTransitions:
    """Test valid state transitions."""
    
    def test_booting_to_connecting(self):
        """Test BOOTING → CONNECTING transition."""
        sm = SystemStateMachine()
        sm.transition(SystemState.CONNECTING)
        assert sm.state == SystemState.CONNECTING
    
    def test_connecting_to_idle(self):
        """Test CONNECTING → IDLE transition."""
        sm = SystemStateMachine(SystemState.CONNECTING)
        sm.transition(SystemState.IDLE)
        assert sm.state == SystemState.IDLE
    
    def test_idle_to_streaming(self):
        """Test IDLE → STREAMING transition."""
        sm = SystemStateMachine(SystemState.IDLE)
        sm.transition(SystemState.STREAMING)
        assert sm.state == SystemState.STREAMING
    
    def test_streaming_to_tracking(self):
        """Test STREAMING → TRACKING transition."""
        sm = SystemStateMachine(SystemState.STREAMING)
        sm.transition(SystemState.TRACKING)
        assert sm.state == SystemState.TRACKING
    
    def test_tracking_to_streaming(self):
        """Test TRACKING → STREAMING transition."""
        sm = SystemStateMachine(SystemState.TRACKING)
        sm.transition(SystemState.STREAMING)
        assert sm.state == SystemState.STREAMING
    
    def test_idle_to_manual(self):
        """Test IDLE → MANUAL transition."""
        sm = SystemStateMachine(SystemState.IDLE)
        sm.transition(SystemState.MANUAL)
        assert sm.state == SystemState.MANUAL
    
    def test_idle_to_homing(self):
        """Test IDLE → HOMING transition."""
        sm = SystemStateMachine(SystemState.IDLE)
        sm.transition(SystemState.HOMING)
        assert sm.state == SystemState.HOMING
    
    def test_homing_to_idle(self):
        """Test HOMING → IDLE transition."""
        sm = SystemStateMachine(SystemState.HOMING)
        sm.transition(SystemState.IDLE)
        assert sm.state == SystemState.IDLE
    
    def test_manual_to_idle(self):
        """Test MANUAL → IDLE transition."""
        sm = SystemStateMachine(SystemState.MANUAL)
        sm.transition(SystemState.IDLE)
        assert sm.state == SystemState.IDLE
    
    def test_emergency_stop_from_idle(self):
        """Test IDLE → EMERGENCY_STOP transition."""
        sm = SystemStateMachine(SystemState.IDLE)
        sm.transition(SystemState.EMERGENCY_STOP)
        assert sm.state == SystemState.EMERGENCY_STOP
    
    def test_emergency_stop_from_streaming(self):
        """Test STREAMING → EMERGENCY_STOP transition."""
        sm = SystemStateMachine(SystemState.STREAMING)
        sm.transition(SystemState.EMERGENCY_STOP)
        assert sm.state == SystemState.EMERGENCY_STOP
    
    def test_emergency_stop_from_tracking(self):
        """Test TRACKING → EMERGENCY_STOP transition."""
        sm = SystemStateMachine(SystemState.TRACKING)
        sm.transition(SystemState.EMERGENCY_STOP)
        assert sm.state == SystemState.EMERGENCY_STOP
    
    def test_emergency_stop_to_booting(self):
        """Test EMERGENCY_STOP → BOOTING transition."""
        sm = SystemStateMachine(SystemState.EMERGENCY_STOP)
        sm.transition(SystemState.BOOTING)
        assert sm.state == SystemState.BOOTING
    
    def test_error_to_booting(self):
        """Test ERROR → BOOTING transition."""
        sm = SystemStateMachine(SystemState.ERROR)
        sm.transition(SystemState.BOOTING)
        assert sm.state == SystemState.BOOTING
    
    def test_error_from_any_state(self):
        """Test ERROR transition from all states."""
        for state in SystemState:
            if state == SystemState.ERROR:
                continue
            sm = SystemStateMachine(state)
            sm.transition(SystemState.ERROR)
            assert sm.state == SystemState.ERROR


class TestInvalidTransitions:
    """Test invalid state transitions."""
    
    def test_invalid_transition_raises_error(self):
        """Test that invalid transition raises InvalidTransitionError."""
        sm = SystemStateMachine()
        with pytest.raises(InvalidTransitionError):
            sm.transition(SystemState.IDLE)  # BOOTING → IDLE is invalid
    
    def test_invalid_transition_message(self):
        """Test error message contains state names."""
        sm = SystemState.BOOTING
        sm_machine = SystemStateMachine()
        with pytest.raises(InvalidTransitionError) as exc_info:
            sm_machine.transition(SystemState.IDLE)
        assert "BOOTING" in str(exc_info.value)
        assert "IDLE" in str(exc_info.value)
    
    def test_booting_to_streaming_invalid(self):
        """Test BOOTING → STREAMING is invalid."""
        sm = SystemStateMachine()
        with pytest.raises(InvalidTransitionError):
            sm.transition(SystemState.STREAMING)
    
    def test_booting_to_idle_invalid(self):
        """Test BOOTING → IDLE is invalid."""
        sm = SystemStateMachine()
        with pytest.raises(InvalidTransitionError):
            sm.transition(SystemState.IDLE)
    
    def test_connecting_to_streaming_invalid(self):
        """Test CONNECTING → STREAMING is invalid."""
        sm = SystemStateMachine(SystemState.CONNECTING)
        with pytest.raises(InvalidTransitionError):
            sm.transition(SystemState.STREAMING)
    
    def test_idle_to_booting_invalid(self):
        """Test IDLE → BOOTING is invalid."""
        sm = SystemStateMachine(SystemState.IDLE)
        with pytest.raises(InvalidTransitionError):
            sm.transition(SystemState.BOOTING)
    
    def test_streaming_to_idle_invalid(self):
        """Test STREAMING → IDLE is invalid (spec shows IDLE as valid)."""
        # Actually, STREAMING → IDLE IS valid per spec
        sm = SystemStateMachine(SystemState.STREAMING)
        sm.transition(SystemState.IDLE)
        assert sm.state == SystemState.IDLE
    
    def test_manual_to_streaming_invalid(self):
        """Test MANUAL → STREAMING is invalid."""
        sm = SystemStateMachine(SystemState.MANUAL)
        with pytest.raises(InvalidTransitionError):
            sm.transition(SystemState.STREAMING)
    
    def test_homing_to_streaming_invalid(self):
        """Test HOMING → STREAMING is invalid."""
        sm = SystemStateMachine(SystemState.HOMING)
        with pytest.raises(InvalidTransitionError):
            sm.transition(SystemState.STREAMING)
    
    def test_error_to_idle_invalid(self):
        """Test ERROR → IDLE is invalid."""
        sm = SystemStateMachine(SystemState.ERROR)
        with pytest.raises(InvalidTransitionError):
            sm.transition(SystemState.IDLE)


class TestTransitionCallbacks:
    """Test transition callbacks (on_enter, on_exit)."""
    
    def test_on_enter_callback_called(self):
        """Test on_enter callback is called when entering a state."""
        sm = SystemStateMachine()
        callback = MagicMock()
        sm.on_enter(SystemState.CONNECTING, callback)
        sm.transition(SystemState.CONNECTING)
        callback.assert_called_once()
        args = callback.call_args[0]
        assert args[0] == SystemState.BOOTING
        assert args[1] == SystemState.CONNECTING
    
    def test_on_exit_callback_called(self):
        """Test on_exit callback is called when exiting a state."""
        sm = SystemStateMachine()
        callback = MagicMock()
        sm.on_exit(SystemState.BOOTING, callback)
        sm.transition(SystemState.CONNECTING)
        callback.assert_called_once()
        args = callback.call_args[0]
        assert args[0] == SystemState.BOOTING
        assert args[1] == SystemState.CONNECTING
    
    def test_callback_execution_order(self):
        """Test that exit callbacks are called before enter callbacks."""
        sm = SystemStateMachine()
        call_order = []
        
        def exit_callback(old_state, new_state):
            call_order.append("exit")
        
        def enter_callback(old_state, new_state):
            call_order.append("enter")
        
        sm.on_exit(SystemState.BOOTING, exit_callback)
        sm.on_enter(SystemState.CONNECTING, enter_callback)
        sm.transition(SystemState.CONNECTING)
        assert call_order == ["exit", "enter"]
    
    def test_multiple_callbacks(self):
        """Test multiple callbacks for same state."""
        sm = SystemStateMachine()
        callback1 = MagicMock()
        callback2 = MagicMock()
        sm.on_enter(SystemState.CONNECTING, callback1)
        sm.on_enter(SystemState.CONNECTING, callback2)
        sm.transition(SystemState.CONNECTING)
        callback1.assert_called_once()
        callback2.assert_called_once()
    
    def test_callbacks_receive_kwargs(self):
        """Test callbacks receive additional keyword arguments."""
        sm = SystemStateMachine()
        callback = MagicMock()
        sm.on_enter(SystemState.CONNECTING, callback)
        sm.transition(SystemState.CONNECTING, reason="startup")
        callback.assert_called_once()
        args, kwargs = callback.call_args
        assert kwargs.get("reason") == "startup"
    
    def test_callbacks_on_error_transition(self):
        """Test callbacks work for error transitions."""
        sm = SystemStateMachine()
        enter_callback = MagicMock()
        exit_callback = MagicMock()
        sm.on_exit(SystemState.BOOTING, exit_callback)
        sm.on_enter(SystemState.ERROR, enter_callback)
        sm.transition(SystemState.ERROR)
        exit_callback.assert_called_once()
        enter_callback.assert_called_once()


class TestTransitionHistory:
    """Test state transition history tracking."""
    
    def test_history_records_transition(self):
        """Test history records state transitions."""
        sm = SystemStateMachine()
        sm.transition(SystemState.CONNECTING)
        history = sm.history
        assert len(history) == 2
        assert history[0]["from"] is None
        assert history[0]["to"] == SystemState.BOOTING
        assert history[1]["from"] == SystemState.BOOTING
        assert history[1]["to"] == SystemState.CONNECTING
    
    def test_history_timestamps(self):
        """Test history entries have timestamps."""
        sm = SystemStateMachine()
        sm.transition(SystemState.CONNECTING)
        history = sm.history
        assert "timestamp" in history[0]
        assert "timestamp" in history[1]
        assert history[1]["timestamp"] >= history[0]["timestamp"]
    
    def test_history_max_length(self):
        """Test history is limited to 10 entries."""
        sm = SystemStateMachine()
        # Perform 15 transitions
        states = [
            SystemState.CONNECTING,
            SystemState.IDLE,
            SystemState.STREAMING,
            SystemState.TRACKING,
            SystemState.STREAMING,
            SystemState.IDLE,
            SystemState.MANUAL,
            SystemState.IDLE,
            SystemState.HOMING,
            SystemState.IDLE,
            SystemState.STREAMING,
            SystemState.TRACKING,
            SystemState.EMERGENCY_STOP,
            SystemState.BOOTING,
            SystemState.CONNECTING,
        ]
        for state in states:
            sm.transition(state)
        history = sm.history
        assert len(history) == 10
        # Check last 10 entries
        assert history[-1]["to"] == SystemState.CONNECTING
        assert history[-2]["to"] == SystemState.BOOTING
    
    def test_clear_history(self):
        """Test clearing history."""
        sm = SystemStateMachine()
        sm.transition(SystemState.CONNECTING)
        sm.clear_history()
        history = sm.history
        assert len(history) == 1
        assert history[0]["from"] is None
        assert history[0]["to"] == SystemState.CONNECTING
    
    def test_invalid_transition_not_recorded(self):
        """Test invalid transitions are not recorded in history."""
        sm = SystemStateMachine()
        initial_length = len(sm.history)
        with pytest.raises(InvalidTransitionError):
            sm.transition(SystemState.IDLE)
        assert len(sm.history) == initial_length


class TestThreadSafety:
    """Test thread safety of state machine."""
    
    def test_concurrent_transitions(self):
        """Test concurrent transitions are handled safely."""
        sm = SystemStateMachine()
        errors = []
        
        def transition_worker():
            try:
                for _ in range(100):
                    current = sm.state
                    if current == SystemState.BOOTING:
                        sm.transition(SystemState.CONNECTING)
                    elif current == SystemState.CONNECTING:
                        sm.transition(SystemState.IDLE)
                    elif current == SystemState.IDLE:
                        sm.transition(SystemState.ERROR)
                    elif current == SystemState.ERROR:
                        sm.transition(SystemState.BOOTING)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=transition_worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # No errors should have occurred
        assert len(errors) == 0
        # State should be valid
        assert isinstance(sm.state, SystemState)
    
    def test_concurrent_history_access(self):
        """Test concurrent history access is safe."""
        sm = SystemStateMachine()
        errors = []
        
        def history_reader():
            try:
                for _ in range(100):
                    _ = sm.history
            except Exception as e:
                errors.append(e)
        
        def state_reader():
            try:
                for _ in range(100):
                    _ = sm.state
            except Exception as e:
                errors.append(e)
        
        threads = [
            threading.Thread(target=history_reader),
            threading.Thread(target=history_reader),
            threading.Thread(target=state_reader),
            threading.Thread(target=state_reader),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
    
    def test_concurrent_callback_registration(self):
        """Test concurrent callback registration is safe."""
        sm = SystemStateMachine()
        errors = []
        
        def register_callbacks():
            try:
                for _ in range(100):
                    sm.on_enter(SystemState.CONNECTING, lambda *args: None)
                    sm.on_exit(SystemState.BOOTING, lambda *args: None)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=register_callbacks) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0


class TestCanTransition:
    """Test can_transition method."""
    
    def test_can_transition_valid(self):
        """Test can_transition returns True for valid transitions."""
        sm = SystemStateMachine()
        assert sm.can_transition(SystemState.CONNECTING) is True
        assert sm.can_transition(SystemState.ERROR) is True
    
    def test_can_transition_invalid(self):
        """Test can_transition returns False for invalid transitions."""
        sm = SystemStateMachine()
        assert sm.can_transition(SystemState.IDLE) is False
        assert sm.can_transition(SystemState.STREAMING) is False
    
    def test_get_valid_transitions(self):
        """Test get_valid_transitions returns correct list."""
        sm = SystemStateMachine()
        valid = sm.get_valid_transitions()
        assert SystemState.CONNECTING in valid
        assert SystemState.ERROR in valid
        assert len(valid) == 2
    
    def test_valid_transitions_idempotent(self):
        """Test get_valid_transitions returns independent list."""
        sm = SystemStateMachine()
        valid1 = sm.get_valid_transitions()
        valid2 = sm.get_valid_transitions()
        assert valid1 == valid2
        valid1.append(SystemState.IDLE)
        assert valid2 != valid1


class TestStateMachineRepr:
    """Test string representation."""
    
    def test_repr(self):
        """Test __repr__ method."""
        sm = SystemStateMachine()
        assert repr(sm) == "SystemStateMachine(state=BOOTING)"
    
    def test_repr_after_transition(self):
        """Test __repr__ after transition."""
        sm = SystemStateMachine()
        sm.transition(SystemState.CONNECTING)
        assert repr(sm) == "SystemStateMachine(state=CONNECTING)"


class TestRealWorldScenarios:
    """Test realistic usage scenarios."""
    
    def test_camera_service_workflow(self):
        """Test Camera Service: IDLE → STREAMING."""
        sm = SystemStateMachine(SystemState.IDLE)
        sm.transition(SystemState.STREAMING)
        assert sm.state == SystemState.STREAMING
    
    def test_director_service_workflow(self):
        """Test Director Service: STREAMING → TRACKING."""
        sm = SystemStateMachine(SystemState.STREAMING)
        sm.transition(SystemState.TRACKING)
        assert sm.state == SystemState.TRACKING
    
    def test_servo_controller_workflow(self):
        """Test Servo Controller: IDLE → HOMING → IDLE."""
        sm = SystemStateMachine(SystemState.IDLE)
        sm.transition(SystemState.HOMING)
        assert sm.state == SystemState.HOMING
        sm.transition(SystemState.IDLE)
        assert sm.state == SystemState.IDLE
    
    def test_safety_layer_workflow(self):
        """Test Safety Layer: any → EMERGENCY_STOP."""
        states_to_test = [
            SystemState.IDLE,
            SystemState.STREAMING,
            SystemState.TRACKING,
            SystemState.MANUAL,
            SystemState.HOMING,
        ]
        for initial_state in states_to_test:
            sm = SystemStateMachine(initial_state)
            sm.transition(SystemState.EMERGENCY_STOP)
            assert sm.state == SystemState.EMERGENCY_STOP
    
    def test_error_handler_workflow(self):
        """Test Error Handler: any → ERROR."""
        states_to_test = [
            SystemState.BOOTING,
            SystemState.CONNECTING,
            SystemState.IDLE,
            SystemState.STREAMING,
            SystemState.TRACKING,
            SystemState.MANUAL,
            SystemState.HOMING,
            SystemState.EMERGENCY_STOP,
        ]
        for initial_state in states_to_test:
            sm = SystemStateMachine(initial_state)
            sm.transition(SystemState.ERROR)
            assert sm.state == SystemState.ERROR
    
    def test_full_boot_sequence(self):
        """Test complete boot sequence."""
        sm = SystemStateMachine()
        sm.transition(SystemState.CONNECTING)
        sm.transition(SystemState.IDLE)
        assert sm.state == SystemState.IDLE
    
    def test_recovery_from_emergency_stop(self):
        """Test recovery from emergency stop."""
        sm = SystemStateMachine(SystemState.EMERGENCY_STOP)
        sm.transition(SystemState.BOOTING)
        sm.transition(SystemState.CONNECTING)
        sm.transition(SystemState.IDLE)
        assert sm.state == SystemState.IDLE
    
    def test_recovery_from_error(self):
        """Test recovery from error."""
        sm = SystemStateMachine(SystemState.ERROR)
        sm.transition(SystemState.BOOTING)
        sm.transition(SystemState.CONNECTING)
        sm.transition(SystemState.IDLE)
        assert sm.state == SystemState.IDLE
    
    def test_tracking_to_idle(self):
        """Test TRACKING → IDLE transition."""
        sm = SystemStateMachine(SystemState.TRACKING)
        sm.transition(SystemState.IDLE)
        assert sm.state == SystemState.IDLE
    
    def test_streaming_to_idle(self):
        """Test STREAMING → IDLE transition."""
        sm = SystemStateMachine(SystemState.STREAMING)
        sm.transition(SystemState.IDLE)
        assert sm.state == SystemState.IDLE