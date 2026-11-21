"""Output helpers for OrbitLab's first version."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def save_trajectory_csv(
    path: Path,
    times: np.ndarray,
    positions: np.ndarray,
    velocities: np.ndarray,
    names: list[str],
) -> None:
    """Save one row per body and time step."""
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["time", "body", "x", "y", "vx", "vy"])
        for time, position_row, velocity_row in zip(times, positions, velocities):
            for body_index, name in enumerate(names):
                writer.writerow(
                    [
                        f"{time:.10g}",
                        name,
                        f"{position_row[body_index, 0]:.10g}",
                        f"{position_row[body_index, 1]:.10g}",
                        f"{velocity_row[body_index, 0]:.10g}",
                        f"{velocity_row[body_index, 1]:.10g}",
                    ]
                )


def save_trajectory_plot(
    path: Path,
    positions: np.ndarray,
    names: list[str],
    masses: np.ndarray,
) -> None:
    """Save an equal-aspect plot of all body trajectories."""
    figure, axis = plt.subplots(figsize=(8, 8), dpi=150)
    colors = ["tab:orange", "tab:blue"]
    for body_index, name in enumerate(names):
        trajectory = positions[:, body_index, :]
        color = colors[body_index % len(colors)]
        axis.plot(trajectory[:, 0], trajectory[:, 1], color=color, linewidth=1.2, label=name)
        axis.scatter(
            trajectory[0, 0], trajectory[0, 1], color=color, marker="o", s=28,
            edgecolors="black", linewidths=0.4,
        )
        axis.scatter(
            trajectory[-1, 0], trajectory[-1, 1], color=color, marker="x", s=36,
            linewidths=1.2,
        )
        axis.scatter(
            trajectory[0, 0], trajectory[0, 1], color=color,
            s=max(25.0, 55.0 * float(masses[body_index]) ** (1 / 3)),
            alpha=0.35,
        )

    axis.set_title("OrbitLab: 2D two-body gravitational motion")
    axis.set_xlabel("x")
    axis.set_ylabel("y")
    axis.set_aspect("equal", adjustable="box")
    axis.grid(True, alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(path)
    plt.close(figure)


def save_summary(path: Path, summary: dict) -> None:
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

