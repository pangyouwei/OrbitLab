"""Time integration methods used by OrbitLab."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

AccelerationFunction = Callable[[np.ndarray], np.ndarray]


def velocity_verlet_step(
    positions: np.ndarray,
    velocities: np.ndarray,
    accelerations: np.ndarray,
    dt: float,
    acceleration_function: AccelerationFunction,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Advance one step with the velocity Verlet method.

    Returns new positions, new velocities, and the newly evaluated
    accelerations. The caller supplies the old accelerations so that each step
    evaluates the force only once after the position update.
    """
    if dt <= 0:
        raise ValueError("dt must be positive")

    next_positions = positions + velocities * dt + 0.5 * accelerations * dt**2
    next_accelerations = acceleration_function(next_positions)
    next_velocities = velocities + 0.5 * (
        accelerations + next_accelerations
    ) * dt
    return next_positions, next_velocities, next_accelerations

