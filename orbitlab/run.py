"""Command-line entry point for the first OrbitLab simulation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .integrators import velocity_verlet_step
from .physics import accelerations
from .visualize import save_summary, save_trajectory_csv, save_trajectory_plot


def load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        config = json.load(file)

    bodies = config.get("bodies")
    if not isinstance(bodies, list) or len(bodies) != 2:
        raise ValueError("the first version requires exactly two bodies")
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
    position_history = np.empty((steps + 1, 2, 2), dtype=float)
    velocity_history = np.empty((steps + 1, 2, 2), dtype=float)
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
    parser = argparse.ArgumentParser(description="Simulate a 2D two-body orbit")
    parser.add_argument("config", type=Path, help="path to a JSON configuration")
    parser.add_argument(
        "--output-dir", type=Path, default=Path("outputs"), help="directory for results"
    )
    args = parser.parse_args()

    config = load_config(args.config)
    times, positions, velocities, names, masses = simulate(config)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = args.config.stem
    save_trajectory_csv(
        args.output_dir / f"{stem}_trajectory.csv", times, positions, velocities, names
    )
    save_trajectory_plot(
        args.output_dir / f"{stem}_trajectory.png", positions, names, masses
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
    }
    save_summary(args.output_dir / f"{stem}_summary.json", summary)
    print(f"Simulated {len(times)} time points through t={times[-1]:.6g}.")
    print(f"Saved results to {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()

