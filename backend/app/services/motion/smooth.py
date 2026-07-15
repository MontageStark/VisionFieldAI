"""Smoothing and easing utilities for camera motion."""
from __future__ import annotations

import math
from typing import Callable, List, Tuple


def ease_in_out(t: float) -> float:
    """Cubic ease-in-out: starts slow, fast in middle, ends slow.

    Args:
        t: Normalized time in [0.0, 1.0]

    Returns:
        Eased value in [0.0, 1.0]
    """
    t = max(0.0, min(1.0, t))
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - math.pow(-2.0 * t + 2.0, 3.0) / 2.0


def ease_in(t: float) -> float:
    """Cubic ease-in: starts slow, accelerates.

    Args:
        t: Normalized time in [0.0, 1.0]

    Returns:
        Eased value in [0.0, 1.0]
    """
    t = max(0.0, min(1.0, t))
    return t * t * t


def ease_out(t: float) -> float:
    """Cubic ease-out: starts fast, decelerates.

    Args:
        t: Normalized time in [0.0, 1.0]

    Returns:
        Eased value in [0.0, 1.0]
    """
    t = max(0.0, min(1.0, t))
    return 1.0 - math.pow(1.0 - t, 3.0)


def ease_out_elastic(t: float) -> float:
    """Elastic ease-out: overshoots slightly then settles.

    Args:
        t: Normalized time in [0.0, 1.0]

    Returns:
        Eased value in [0.0, 1.0]
    """
    t = max(0.0, min(1.0, t))
    if t == 0.0:
        return 0.0
    if t == 1.0:
        return 1.0
    return math.pow(2.0, -10.0 * t) * math.sin((t - 0.075) * (2.0 * math.pi) / 0.3) + 1.0


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between two values.

    Args:
        a: Start value
        b: End value
        t: Interpolation factor in [0.0, 1.0]

    Returns:
        Interpolated value
    """
    t = max(0.0, min(1.0, t))
    return a + (b - a) * t


def lerp_angle(a: float, b: float, t: float) -> float:
    """Linear interpolation between two angles, handling wraparound.

    Args:
        a: Start angle in degrees
        b: End angle in degrees
        t: Interpolation factor in [0.0, 1.0]

    Returns:
        Interpolated angle in degrees in [0.0, 360.0)
    """
    t = max(0.0, min(1.0, t))
    delta = ((b - a) + 180.0) % 360.0 - 180.0
    result = a + delta * t
    return result % 360.0


def smoothstep(a: float, b: float, t: float) -> float:
    """Smoothstep interpolation (ease-in-out equivalent).

    Args:
        a: Start value
        b: End value
        t: Interpolation factor in [0.0, 1.0]

    Returns:
        Interpolated value
    """
    t = max(0.0, min(1.0, t))
    t = t * t * (3.0 - 2.0 * t)
    return a + (b - a) * t


def apply_smoothing(
    current: float,
    target: float,
    factor: float,
) -> float:
    """Apply exponential smoothing to a value.

    Args:
        current: Current value
        target: Target value
        factor: Smoothing factor in (0.0, 1.0]. Higher = more responsive.

    Returns:
        Smoothed value
    """
    factor = max(0.001, min(1.0, factor))
    return current + (target - current) * factor


def generate_waypoints(
    start: float,
    end: float,
    count: int,
    easing: Callable[[float], float] = ease_in_out,
) -> List[float]:
    """Generate evenly-spaced waypoints with easing applied.

    Args:
        start: Start value
        end: End value
        count: Number of waypoints (including start, excluding end)
        easing: Easing function to apply

    Returns:
        List of waypoint values
    """
    if count < 1:
        return []
    if count == 1:
        return [start]

    waypoints = []
    for i in range(count):
        t = i / (count - 1)
        eased_t = easing(t)
        waypoints.append(lerp(start, end, eased_t))
    return waypoints


def trapezoidal_velocity_profile(
    distance: float,
    max_velocity: float,
    acceleration: float,
) -> Tuple[float, float, float]:
    """Calculate trapezoidal velocity profile durations.

    Uses symmetric acceleration and deceleration with peak velocity.

    Args:
        distance: Total distance to travel in degrees
        max_velocity: Peak velocity in deg/s
        acceleration: Acceleration in deg/s^2

    Returns:
        Tuple of (accel_time, cruise_time, decel_time) in seconds
    """
    distance = abs(distance)
    if distance <= 0.0 or max_velocity <= 0.0 or acceleration <= 0.0:
        return (0.0, 0.0, 0.0)

    accel_dist = 0.5 * acceleration * (max_velocity / acceleration) ** 2

    if accel_dist >= distance / 2.0:
        triangle_time = 2.0 * math.sqrt(distance / acceleration)
        half_time = triangle_time / 2.0
        return (half_time, 0.0, half_time)

    cruise_velocity = max_velocity
    accel_time = max_velocity / acceleration
    decel_time = max_velocity / acceleration

    accel_dist = 0.5 * acceleration * accel_time ** 2
    decel_dist = 0.5 * acceleration * decel_time ** 2
    cruise_dist = distance - accel_dist - decel_dist
    cruise_time = cruise_dist / cruise_velocity if cruise_velocity > 0 else 0.0

    return (accel_time, max(0.0, cruise_time), decel_time)


def time_between_angles(
    start_angle: float,
    end_angle: float,
    max_velocity: float,
    acceleration: float,
) -> float:
    """Calculate total time to move between two angles.

    Args:
        start_angle: Start angle in degrees
        end_angle: End angle in degrees
        max_velocity: Maximum velocity in deg/s
        acceleration: Acceleration in deg/s^2

    Returns:
        Total time in seconds
    """
    distance = abs(end_angle - start_angle)
    accel_time, cruise_time, decel_time = trapezoidal_velocity_profile(
        distance, max_velocity, acceleration
    )
    return accel_time + cruise_time + decel_time