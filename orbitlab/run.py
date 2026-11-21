"""Command-line entry point for OrbitLab's 2-D N-body simulation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .diagnostics import compute_diagnostic_history, save_diagnostics_csv
from .integrators import velocity_verlet_step
from .physics import accelerations, center_of_mass, center_of_mass_velocity
from .visualize import (
    save_summary,
    save_trajectory_animation,
    save_trajectory_csv,
    save_trajectory_plot,
)


def load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        config = json.load(file)

    bodies = config.get("bodies")
    if not isinstance(bodies, list) or len(bodies) < 2:
        raise ValueError("the configuration requires at least two bodies")
    for body in bodies:
        for key in ("name", "mass", "position", "velocity"):
            if key not in body:
                raise ValueError(f"each body must contain {key!r}")
        if len(body["position"]) != 2 or len(body["velocity"]) != 2:
            raise ValueError("position and velocity must each have two values")
        if float(body["mass"]) <= 0:
            raise ValueError("body masses must be positive")
    if config.get("steps", 0) <= 0:
        raise ValueError("steps must be positive")
    if config.get("dt", 0) <= 0:
        raise ValueError("dt must be positive")
    if float(config.get("G", 1.0)) <= 0:
        raise ValueError("G must be positive")
    if float(config.get("softening", 0.0)) < 0:
        raise ValueError("softening must be non-negative")
    return config


def simulate(
    config: dict,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str], np.ndarray]:
    bodies = config["bodies"]
    names = [str(body["name"]) for body in bodies]
    masses = np.array([body["mass"] for body in bodies], dtype=float)
    positions = np.array([body["position"] for body in bodies], dtype=float)
    velocities = np.array([body["velocity"] for body in bodies], dtype=float)
    steps = int(config["steps"])
    dt = float(config["dt"])
    gravitational_constant = float(config.get("G", 1.0))
    softening = float(config.get("softening", 0.0))

    def acceleration_function(current_positions: np.ndarray) -> np.ndarray:
        return accelerations(
            current_positions, masses, gravitational_constant, softening
        )

    times = np.arange(steps + 1, dtype=float) * dt
    number_of_bodies = len(bodies)
    position_history = np.empty((steps + 1, number_of_bodies, 2), dtype=float)
    velocity_history = np.empty((steps + 1, number_of_bodies, 2), dtype=float)
    position_history[0] = positions
    velocity_history[0] = velocities
    current_accelerations = acceleration_function(positions)

    for step_index in range(steps):
        positions, velocities, current_accelerations = velocity_verlet_step(
            positions,
            velocities,
            current_accelerations,
            dt,
            acceleration_function,
        )
        position_history[step_index + 1] = positions
        velocity_history[step_index + 1] = velocities

    return times, position_history, velocity_history, names, masses


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate a 2D Newtonian N-body system")
    parser.add_argument("config", type=Path, help="path to a JSON configuration")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="base directory; a subdirectory named after the config is created",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    times, positions, velocities, names, masses = simulate(config)
    gravitational_constant = float(config.get("G", 1.0))
    softening = float(config.get("softening", 0.0))
    stem = args.config.stem
    output_dir = args.output_dir / stem
    output_dir.mkdir(parents=True, exist_ok=True)
    save_trajectory_csv(
        output_dir / f"{stem}_trajectory.csv", times, positions, velocities, names
    )
    save_trajectory_plot(
        output_dir / f"{stem}_trajectory.png", positions, names, masses
    )
    save_trajectory_animation(
        output_dir / f"{stem}_animation.avi", times, positions, names, masses
    )
    diagnostic_history = compute_diagnostic_history(
        times,
        positions,
        velocities,
        masses,
        gravitational_constant,
        softening,
    )
    save_diagnostics_csv(
        output_dir / f"{stem}_diagnostics.csv", diagnostic_history
    )
    summary = {
        "config": str(args.config),
        "bodies": names,
        "steps": int(config["steps"]),
        "dt": float(config["dt"]),
        "final_time": float(times[-1]),
        "integrator": "velocity_verlet",
        "final_positions": positions[-1].tolist(),
        "final_velocities": velocities[-1].tolist(),
        "initial_center_of_mass": center_of_mass(positions[0], masses).tolist(),
        "final_center_of_mass": center_of_mass(positions[-1], masses).tolist(),
        "initial_center_of_mass_velocity": center_of_mass_velocity(
            velocities[0], masses
        ).tolist(),
        "final_center_of_mass_velocity": center_of_mass_velocity(
            velocities[-1], masses
        ).tolist(),
        "initial_total_energy": float(diagnostic_history["energy"][0]),
        "final_total_energy": float(diagnostic_history["energy"][-1]),
        "maximum_relative_energy_error": float(
            np.max(diagnostic_history["relative_energy_error"])
        ),
        "initial_total_momentum": [
            float(diagnostic_history["momentum_x"][0]),
            float(diagnostic_history["momentum_y"][0]),
        ],
        "final_total_momentum": [
            float(diagnostic_history["momentum_x"][-1]),
            float(diagnostic_history["momentum_y"][-1]),
        ],
        "maximum_momentum_drift": float(np.max(diagnostic_history["momentum_drift"])),
        "initial_angular_momentum_z": float(
            diagnostic_history["angular_momentum_z"][0]
        ),
        "final_angular_momentum_z": float(
            diagnostic_history["angular_momentum_z"][-1]
        ),
        "maximum_angular_momentum_drift": float(
            np.max(diagnostic_history["angular_momentum_drift"])
        ),
        "maximum_center_of_mass_drift": float(
            np.max(diagnostic_history["center_of_mass_drift"])
        ),
    }
    save_summary(output_dir / f"{stem}_summary.json", summary)
    print(f"Simulated {len(times)} time points through t={times[-1]:.6g}.")
    print(f"Saved results to {output_dir.resolve()}")


if __name__ == "__main__":
    main()

