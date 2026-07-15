"""Kalman filter for 2D ball trajectory prediction."""
from __future__ import annotations

import numpy as np


class KalmanFilter2D:
    """2D Kalman filter for ball tracking with linear motion model.

    State vector: [x, y, vx, vy] (position and velocity in 2D)
    Measurement vector: [x, y] (position only)

    Uses a constant velocity motion model with configurable process
    and measurement noise.
    """

    def __init__(
        self,
        process_noise: float = 1.0,
        measurement_noise: float = 1.0,
        initial_state: np.ndarray | None = None,
        initial_covariance: np.ndarray | None = None,
    ) -> None:
        """Initialize the Kalman filter.

        Args:
            process_noise: Process noise standard deviation (Q diagonal value)
            measurement_noise: Measurement noise standard deviation (R diagonal value)
            initial_state: Initial state vector [x, y, vx, vy]. If None, uses zeros.
            initial_covariance: Initial covariance matrix. If None, uses identity * 1e3.
        """
        self._dt = 1.0

        self._state_dim = 4
        self._meas_dim = 2

        self._F = np.array([
            [1.0, 0.0, 1.0, 0.0],
            [0.0, 1.0, 0.0, 1.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ], dtype=np.float32)

        self._H = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
        ], dtype=np.float32)

        self._Q_base = np.array([
            [0.25, 0.00, 0.50, 0.00],
            [0.00, 0.25, 0.00, 0.50],
            [0.50, 0.00, 1.00, 0.00],
            [0.00, 0.50, 0.00, 1.00],
        ], dtype=np.float32) * (process_noise ** 2)

        self._R = np.eye(self._meas_dim, dtype=np.float32) * (measurement_noise ** 2)

        if initial_state is not None:
            self._state = initial_state.astype(np.float32)
        else:
            self._state = np.zeros(self._state_dim, dtype=np.float32)

        if initial_covariance is not None:
            self._P = initial_covariance.astype(np.float32)
        else:
            self._P = np.eye(self._state_dim, dtype=np.float32) * 1e3

        self._initialized = np.any(self._state != 0) or np.any(self._P != np.eye(self._state_dim) * 1e3)

    def initialize(self, x: float, y: float, vx: float = 0.0, vy: float = 0.0) -> None:
        """Initialize filter with first measurement.

        Args:
            x: Initial x position
            y: Initial y position
            vx: Initial x velocity (default 0)
            vy: Initial y velocity (default 0)
        """
        self._state = np.array([x, y, vx, vy], dtype=np.float32)
        self._P = np.eye(self._state_dim, dtype=np.float32) * 1e3
        self._initialized = True

    def predict(self, dt: float | None = None) -> tuple[np.ndarray, np.ndarray]:
        """Predict next state.

        Args:
            dt: Time step. If None, uses stored dt. If provided, updates F matrix.

        Returns:
            Tuple of (predicted_state, predicted_covariance)
        """
        if dt is not None and dt != self._dt:
            self._dt = dt
            self._F = np.array([
                [1.0, 0.0, dt, 0.0],
                [0.0, 1.0, 0.0, dt],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ], dtype=np.float32)

        Q = self._Q_base * (self._dt ** 2)

        self._state = self._F @ self._state
        self._P = self._F @ self._P @ self._F.T + Q

        return self._state.copy(), self._P.copy()

    def update(self, measurement: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Update state with measurement.

        Args:
            measurement: Measurement vector [x, y]

        Returns:
            Tuple of (updated_state, updated_covariance)
        """
        z = np.asarray(measurement, dtype=np.float32).reshape(-1)

        if z.shape[0] != self._meas_dim:
            raise ValueError(f"Measurement dimension must be {self._meas_dim}, got {z.shape[0]}")

        y = z - self._H @ self._state

        S = self._H @ self._P @ self._H.T + self._R
        K = self._P @ self._H.T @ np.linalg.inv(S)

        self._state = self._state + K @ y
        self._P = (np.eye(self._state_dim, dtype=np.float32) - K @ self._H) @ self._P

        return self._state.copy(), self._P.copy()

    def update_with_noise(self, measurement: np.ndarray, confidence: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
        """Update state with measurement and confidence weighting.

        Args:
            measurement: Measurement vector [x, y]
            confidence: Measurement confidence (0-1). Lower = more noise.

        Returns:
            Tuple of (updated_state, updated_covariance)
        """
        if confidence <= 0:
            return self._state.copy(), self._P.copy()

        measurement_array = np.asarray(measurement, dtype=np.float32)
        R_adaptive = self._R / max(confidence, 0.01)

        z = measurement_array.reshape(-1)

        y = z - self._H @ self._state

        S = self._H @ self._P @ self._H.T + R_adaptive
        K = self._P @ self._H.T @ np.linalg.inv(S)

        self._state = self._state + K @ y
        self._P = (np.eye(self._state_dim, dtype=np.float32) - K @ self._H) @ self._P

        return self._state.copy(), self._P.copy()

    def get_position(self) -> tuple[float, float]:
        """Get current position estimate.

        Returns:
            Tuple of (x, y)
        """
        return float(self._state[0]), float(self._state[1])

    def get_velocity(self) -> tuple[float, float]:
        """Get current velocity estimate.

        Returns:
            Tuple of (vx, vy)
        """
        return float(self._state[2]), float(self._state[3])

    def get_state(self) -> np.ndarray:
        """Get full state vector.

        Returns:
            State vector [x, y, vx, vy]
        """
        return self._state.copy()

    def get_covariance(self) -> np.ndarray:
        """Get state covariance matrix.

        Returns:
            Covariance matrix (4x4)
        """
        return self._P.copy()

    def predict_future(self, steps: int, dt: float | None = None) -> list[tuple[float, float]]:
        """Predict future positions.

        Args:
            steps: Number of future steps to predict
            dt: Time step for each prediction. If None, uses stored dt.

        Returns:
            List of (x, y) position predictions
        """
        if dt is None:
            dt = self._dt

        F_step = np.array([
            [1.0, 0.0, dt, 0.0],
            [0.0, 1.0, 0.0, dt],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ], dtype=np.float32)

        Q_step = self._Q_base * (dt ** 2)

        state = self._state.copy()
        P = self._P.copy()

        predictions = []
        for _ in range(steps):
            state = F_step @ state
            P = F_step @ P @ F_step.T + Q_step
            predictions.append((float(state[0]), float(state[1])))

        return predictions

    def is_initialized(self) -> bool:
        """Check if filter has been initialized with a measurement.

        Returns:
            True if initialized
        """
        return bool(self._initialized)

    def reset(self) -> None:
        """Reset filter to uninitialized state."""
        self._state = np.zeros(self._state_dim, dtype=np.float32)
        self._P = np.eye(self._state_dim, dtype=np.float32) * 1e3
        self._initialized = False


def motion_compensated_predict(
    current_state: np.ndarray,
    velocity: np.ndarray,
    steps: int,
    dt: float,
) -> list[tuple[float, float]]:
    """Simple motion-compensated prediction without Kalman filtering.

    Args:
        current_state: Current position (x, y)
        velocity: Velocity (vx, vy)
        steps: Number of steps to predict
        dt: Time step

    Returns:
        List of (x, y) position predictions
    """
    predictions = []
    x, y = current_state
    vx, vy = velocity

    for i in range(1, steps + 1):
        t = i * dt
        pred_x = x + vx * t
        pred_y = y + vy * t
        predictions.append((pred_x, pred_y))

    return predictions