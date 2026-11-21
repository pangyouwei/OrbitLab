"""Newtonian physics for a small collection of point masses."""

from __future__ import annotations

import numpy as np


def accelerations(
    positions: np.ndarray,
    masses: np.ndarray,
    gravitational_constant: float = 1.0,
    softening: float = 0.0,
) -> np.ndarray:
    """Return the acceleration of every body in a 2-D N-body state.

    ``softening`` prevents a numerical singularity when two bodies become
    extremely close. It is zero for the ideal point-mass formula.
    """
    positions = np.asarray(positions, dtype=float)
    masses = np.asarray(masses, dtype=float)

    if positions.ndim != 2 or positions.shape[1] != 2:
        raise ValueError("positions must have shape (number_of_bodies, 2)")
    if masses.ndim != 1 or len(masses) != len(positions):
        raise ValueError("masses must have one value for each body")
    if np.any(masses <= 0):
        raise ValueError("all masses must be positive")
    if gravitational_constant <= 0:
        raise ValueError("gravitational_constant must be positive")
    if softening < 0:
        raise ValueError("softening must be non-negative")

    # displacement[i, j] points from body i to body j.
    displacement = positions[None, :, :] - positions[:, None, :]
    distance_squared = np.sum(displacement * displacement, axis=2) + softening**2

    # Remove self-interaction. The diagonal displacement is zero, but its
    # contribution must be explicitly excluded when softening is nonzero.
    np.fill_diagonal(distance_squared, np.inf)
    inverse_distance_cubed = distance_squared ** (-1.5)
    weighted_displacement = displacement * inverse_distance_cubed[:, :, None]
    return gravitational_constant * np.sum(
        weighted_displacement * masses[None, :, None], axis=1
    )

