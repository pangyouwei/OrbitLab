"""Conservation diagnostics for 2-D Newtonian N-body simulations."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from .physics import center_of_mass


def total_energy(
    positions: np.ndarray,
    velocities: np.ndarray,
    masses: np.ndarray,
    gravitational_constant: float = 1.0,
    softening: float = 0.0,
) -> float:
    """Return kinetic plus pairwise potential energy."""
    positions = np.asarray(positions, dtype=float)
    velocities = np.asarray(velocities, dtype=float)
    masses = np.asarray(masses, dtype=float)

    kinetic = 0.5 * np.sum(masses * np.sum(velocities**2, axis=1))
    potential = 0.0
    for body_index in range(len(masses) - 1):
        displacement = positions[body_index + 1 :] - positions[body_index]
        distances = np.sqrt(np.sum(displacement**2, axis=1) + softening**2)
        potential -= gravitational_constant * masses[body_index] * np.sum(
            masses[body_index + 1 :] / distances
        )
    return float(kinetic + potential)


def total_momentum(velocities: np.ndarray, masses: np.ndarray) -> np.ndarray:
    """Return the two components of total linear momentum."""
    return np.sum(np.asarray(velocities, dtype=float) * masses[:, None], axis=0)


def angular_momentum_z(
    positions: np.ndarray, velocities: np.ndarray, masses: np.ndarray
) -> float:
    """Return the out-of-plane angular momentum for a 2-D system."""
    positions = np.asarray(positions, dtype=float)
    velocities = np.asarray(velocities, dtype=float)
    return float(
        np.sum(masses * (positions[:, 0] * velocities[:, 1] - positions[:, 1] * velocities[:, 0]))
    )


def compute_diagnostic_history(
    times: np.ndarray,
    positions: np.ndarray,
    velocities: np.ndarray,
    masses: np.ndarray,
    gravitational_constant: float = 1.0,
    softening: float = 0.0,
) -> dict[str, np.ndarray]:
    """Compute conservation quantities and their drift at every time point."""
    energies = np.array(
        [
            total_energy(position, velocity, masses, gravitational_constant, softening)
            for position, velocity in zip(positions, velocities)
        ]
    )
    momenta = np.array([total_momentum(velocity, masses) for velocity in velocities])
    angular_momenta = np.array(
        [angular_momentum_z(position, velocity, masses) for position, velocity in zip(positions, velocities)]
    )
    centers_of_mass = np.array([center_of_mass(position, masses) for position in positions])

    energy_scale = max(abs(float(energies[0])), np.finfo(float).eps)
    relative_energy_error = np.abs((energies - energies[0]) / energy_scale)
    momentum_drift = np.linalg.norm(momenta - momenta[0], axis=1)
    angular_momentum_drift = np.abs(angular_momenta - angular_momenta[0])
    center_of_mass_drift = np.linalg.norm(
        centers_of_mass - centers_of_mass[0], axis=1
    )

    return {
        "times": np.asarray(times, dtype=float),
        "energy": energies,
        "relative_energy_error": relative_energy_error,
        "momentum_x": momenta[:, 0],
        "momentum_y": momenta[:, 1],
        "angular_momentum_z": angular_momenta,
        "center_of_mass_x": centers_of_mass[:, 0],
        "center_of_mass_y": centers_of_mass[:, 1],
        "center_of_mass_drift": center_of_mass_drift,
        "momentum_drift": momentum_drift,
        "angular_momentum_drift": angular_momentum_drift,
    }


def save_diagnostics_csv(path: Path, diagnostics: dict[str, np.ndarray]) -> None:
    """Save the diagnostic history in a spreadsheet-friendly format."""
    columns = [
        "times",
        "energy",
        "relative_energy_error",
        "momentum_x",
        "momentum_y",
        "angular_momentum_z",
        "center_of_mass_x",
        "center_of_mass_y",
        "center_of_mass_drift",
        "momentum_drift",
        "angular_momentum_drift",
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        for row in zip(*(diagnostics[column] for column in columns)):
            writer.writerow(f"{float(value):.12g}" for value in row)
