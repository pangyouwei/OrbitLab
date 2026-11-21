
"""Output helpers for OrbitLab's first version."""

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path

import imageio_ffmpeg
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter, FuncAnimation
import numpy as np

BODY_COLORS = [
    "tab:orange",
    "tab:blue",
    "tab:green",
    "tab:red",
    "tab:purple",
    "tab:brown",
    "tab:pink",
    "tab:gray",
    "tab:olive",
    "tab:cyan",
]


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
    figure, axis = plt.subplots(figsize=(8, 8), dpi=200)
    largest_mass = float(np.max(masses))
    for body_index, name in enumerate(names):
        trajectory = positions[:, body_index, :]
        color = BODY_COLORS[body_index % len(BODY_COLORS)]
        axis.plot(trajectory[:, 0], trajectory[:, 1], color=color, linewidth=2, label=name)
        marker_size = max(
            42.0, 260.0 * (float(masses[body_index]) / largest_mass) ** (1 / 3)
        )
        axis.scatter(
            trajectory[0, 0],
            trajectory[0, 1],
            s=marker_size,
            color=color,
            edgecolors=color,
            linewidths=0.6,
            zorder=3,
        )

    coordinates = positions.reshape(-1, 2)
    lower = coordinates.min(axis=0)
    upper = coordinates.max(axis=0)
    center = (lower + upper) / 2
    half_width = max(float(np.max(upper - lower)) * 0.56, 0.1)
    axis.set_xlim(center[0] - half_width, center[0] + half_width)
    axis.set_ylim(center[1] - half_width, center[1] + half_width)
    axis.set_title("OrbitLab: 2D N-body orbit")
    axis.set_xlabel("x")
    axis.set_ylabel("y")
    axis.set_aspect("equal", adjustable="box")
    axis.grid(True, alpha=0.18)
    axis.legend(frameon=False)
    figure.tight_layout()
    figure.savefig(path)
    figure.savefig(path.with_suffix(".svg"))
    plt.close(figure)


def save_trajectory_animation(
    path: Path,
    times: np.ndarray,
    positions: np.ndarray,
    names: list[str],
    masses: np.ndarray,
    max_frames: int = 180,
    fps: int = 30,
) -> None:
    """Save an AVI animation and a GIF preview of all body trajectories."""
    frame_indices = np.linspace(
        0, len(times) - 1, num=min(max_frames, len(times)), dtype=int
    )
    largest_mass = float(np.max(masses))
    figure, axis = plt.subplots(figsize=(8, 8), dpi=120)
    trails = []
    markers = []
    for body_index, name in enumerate(names):
        color = BODY_COLORS[body_index % len(BODY_COLORS)]
        (trail,) = axis.plot([], [], color=color, linewidth=1.8, alpha=0.7)
        trails.append(trail)
        (marker,) = axis.plot(
            [], [], "o", color=color,
            markersize=12 * (float(masses[body_index]) / largest_mass) ** (1 / 3),
            markeredgecolor=color, markeredgewidth=0.5, label=name,
        )
        markers.append(marker)

    coordinates = positions.reshape(-1, 2)
    lower = coordinates.min(axis=0)
    upper = coordinates.max(axis=0)
    center = (lower + upper) / 2
    half_width = max(float(np.max(upper - lower)) * 0.58, 0.1)
    axis.set_xlim(center[0] - half_width, center[0] + half_width)
    axis.set_ylim(center[1] - half_width, center[1] + half_width)
    axis.set_aspect("equal", adjustable="box")
    axis.set_xlabel("x")
    axis.set_ylabel("y")
    axis.set_title("OrbitLab: 2D N-body motion")
    axis.grid(True, alpha=0.25)
    axis.legend(loc="upper right")
    time_label = axis.text(0.03, 0.96, "", transform=axis.transAxes, va="top")

    def update(frame_index: int):
        step_index = int(frame_indices[frame_index])
        for body_index in range(len(names)):
            trajectory = positions[: step_index + 1, body_index, :]
            trails[body_index].set_data(trajectory[:, 0], trajectory[:, 1])
            markers[body_index].set_data(
                [positions[step_index, body_index, 0]],
                [positions[step_index, body_index, 1]],
            )
        time_label.set_text(f"Simulation time: {times[step_index]:.2f}")
        return (*trails, *markers, time_label)

    animation = FuncAnimation(
        figure, update, frames=len(frame_indices), interval=1000 / fps
    )
    try:
        matplotlib.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()
        animation.save(
            path,
            writer=FFMpegWriter(
                fps=fps,
                codec="mjpeg",
                extra_args=[
                    "-q:v", "3",
                    "-pix_fmt", "yuvj420p",
                    "-vtag", "MJPG",
                ],
            ),
        )
    finally:
        plt.close(figure)

    subprocess.run(
        [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-loglevel", "error",
            "-y",
            "-i", str(path),
            "-filter_complex",
            "[0:v]fps=30,split=2[a][b];"
            "[a]palettegen=stats_mode=full[p];"
            "[b][p]paletteuse=dither=bayer:bayer_scale=5[v]",
            "-map", "[v]",
            "-loop", "0",
            str(path.with_suffix(".gif")),
        ],
        check=True,
    )

def save_summary(path: Path, summary: dict) -> None:
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

