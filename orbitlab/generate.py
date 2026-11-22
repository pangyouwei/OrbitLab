"""Generate reproducible rotating N-body ring configurations."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import numpy as np

from .physics import accelerations, center_of_mass, center_of_mass_velocity


def make_ring_config(
    count: int,
    seed: int,
    dt: float,
    duration: float,
    softening: float,
    position_jitter: float = 0.015,
    velocity_jitter: float = 0.005,
) -> dict:
    """Build a slightly disturbed rotating ring with zero COM and momentum."""
    if count < 2 or dt <= 0 or duration <= 0 or softening < 0:
        raise ValueError("count must be >= 2, dt/duration positive, and softening >= 0")
    if position_jitter < 0 or velocity_jitter < 0:
        raise ValueError("jitter values must be non-negative")

    masses = np.full(count, 1.0 / count)
    angles = 2 * np.pi * np.arange(count) / count
    ring = np.column_stack((np.cos(angles), np.sin(angles)))
    radial_accelerations = accelerations(ring, masses, softening=softening)
    speed = np.sqrt(-np.mean(np.sum(ring * radial_accelerations, axis=1)))
    velocities = speed * np.column_stack((-np.sin(angles), np.cos(angles)))

    random = np.random.default_rng(seed)
    positions = ring + random.normal(scale=position_jitter, size=(count, 2))
    velocities += random.normal(scale=velocity_jitter, size=(count, 2))
    positions -= center_of_mass(positions, masses)
    velocities -= center_of_mass_velocity(velocities, masses)

    steps = round(duration / dt)
    if steps < 1:
        raise ValueError("duration must contain at least one time step")
    return {
        "G": 1.0,
        "dt": dt,
        "steps": steps,
        "softening": softening,
        "bodies": [
            {
                "name": f"body_{index + 1:02d}",
                "mass": float(masses[index]),
                "position": positions[index].tolist(),
                "velocity": velocities[index].tolist(),
            }
            for index in range(count)
        ],
    }


def save_config(path: Path, config: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a rotating N-body ring")
    parser.add_argument("--count", type=int, required=True, help="number of bodies")
    parser.add_argument("--seed", type=int, default=42, help="random seed")
    parser.add_argument("--dt", type=float, default=0.002)
    parser.add_argument("--duration", type=float, default=12.0)
    parser.add_argument("--softening", type=float, default=0.05)
    parser.add_argument("--position-jitter", type=float, default=0.015)
    parser.add_argument("--velocity-jitter", type=float, default=0.005)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--twin-output", type=Path, help="optional nearby initial state")
    parser.add_argument("--twin-delta", type=float, default=1e-5)
    args = parser.parse_args()

    try:
        config = make_ring_config(
            args.count, args.seed, args.dt, args.duration, args.softening,
            args.position_jitter, args.velocity_jitter,
        )
        if args.twin_output is not None and args.twin_delta <= 0:
            raise ValueError("--twin-delta must be positive")
    except ValueError as error:
        parser.error(str(error))

    save_config(args.output, config)
    print(f"Saved {args.count}-body configuration to {args.output}")
    if args.twin_output is not None:
        twin = copy.deepcopy(config)
        twin["bodies"][0]["velocity"][1] += args.twin_delta
        twin["bodies"][1]["velocity"][1] -= args.twin_delta
        save_config(args.twin_output, twin)
        print(f"Saved nearby initial state to {args.twin_output}")


if __name__ == "__main__":
    main()
