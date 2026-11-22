
"""Output helpers for OrbitLab simulations."""

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

BODY_COLORS = ["tab:orange", "tab:blue", "tab:green"]


def body_colors(count: int) -> list:
    """Give small systems familiar colors and larger systems a wider palette."""
    if count <= len(BODY_COLORS):
        return BODY_COLORS[:count]
    if count <= 20:
        return list(plt.get_cmap("tab20").colors[:count])
    return [plt.get_cmap("hsv")(index / count) for index in range(count)]


def camera_limits(positions: np.ndarray, frame_indices: np.ndarray) -> np.ndarray:
    """Return one fixed viewport based only on the initial body positions."""
    initial_positions = positions[0]
    lower = initial_positions.min(axis=0)
    upper = initial_positions.max(axis=0)
    center = (lower + upper) / 2
    initial_radius = float(np.max(np.abs(initial_positions - center)))
    half_width = max(float(np.max(upper - lower)) * 0.15, initial_radius * 1.15, 0.1)
    fixed = np.array(
        [
            center[0] - half_width,
            center[0] + half_width,
            center[1] - half_width,
            center[1] + half_width,
        ]
    )
    return np.repeat(fixed[None, :], len(frame_indices), axis=0)


def animation_frame_indices(positions: np.ndarray, max_frames: int) -> np.ndarray:
    """For larger systems, finish when most bodies first leave the fixed view."""
    last_step = len(positions) - 1
    if positions.shape[1] >= 4:
        left, right, bottom, top = camera_limits(positions, np.array([0]))[0]
        outside = (
            (positions[:, :, 0] < left)
            | (positions[:, :, 0] > right)
            | (positions[:, :, 1] < bottom)
            | (positions[:, :, 1] > top)
        )
        majority = np.flatnonzero(outside.sum(axis=1) > positions.shape[1] // 2)
        if len(majority):
            last_step = int(majority[0])
    return np.linspace(0, last_step, num=min(max_frames, last_step + 1), dtype=int)


def apply_dark_theme(figure, axis) -> None:
    """Use a black canvas with light labels and subtle grid lines."""
    figure.patch.set_facecolor("black")
    axis.set_facecolor("black")
    for spine in axis.spines.values():
        spine.set_color("white")
    axis.tick_params(colors="white")
    axis.xaxis.label.set_color("white")
    axis.yaxis.label.set_color("white")
    axis.title.set_color("white")


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
    apply_dark_theme(figure, axis)
    largest_mass = float(np.max(masses))
    colors = body_colors(len(names))
    density_scale = min(1.0, 3.0 / len(names))
    for body_index, name in enumerate(names):
        trajectory = positions[:, body_index, :]
        color = colors[body_index]
        axis.plot(
            trajectory[:, 0], trajectory[:, 1], color=color,
            linewidth=max(0.65, 2 * density_scale**0.5), label=name,
        )
        marker_size = max(
            12.0,
            260.0 * (float(masses[body_index]) / largest_mass) ** (1 / 3)
            * density_scale,
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
    axis.grid(True, color="white", alpha=0.18)
    if len(names) <= 10:
        legend = axis.legend(frameon=False)
        for text in legend.get_texts():
            text.set_color("white")
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
    max_frames: int = 240,
    fps: int = 20,
) -> None:
    """Save an AVI animation and a GIF preview of all body trajectories."""
    frame_indices = animation_frame_indices(positions, max_frames)
    limits = camera_limits(positions, frame_indices)
    largest_mass = float(np.max(masses))
    colors = body_colors(len(names))
    density_scale = min(1.0, 3.0 / len(names))
    figure, axis = plt.subplots(figsize=(8, 8), dpi=120)
    apply_dark_theme(figure, axis)
    trails = []
    markers = []
    for body_index, name in enumerate(names):
        color = colors[body_index]
        (trail,) = axis.plot(
            [], [], color=color, linewidth=max(0.65, 1.8 * density_scale**0.5),
            alpha=0.7,
        )
        trails.append(trail)
        (marker,) = axis.plot(
            [], [], "o", color=color,
            markersize=max(
                3.0,
                12 * (float(masses[body_index]) / largest_mass) ** (1 / 3)
                * density_scale**0.5,
            ),
            markeredgecolor=color, markeredgewidth=0.5, label=name,
        )
        markers.append(marker)

    axis.set_xlim(limits[0, 0], limits[0, 1])
    axis.set_ylim(limits[0, 2], limits[0, 3])
    axis.set_aspect("equal", adjustable="box")
    axis.set_xlabel("x")
    axis.set_ylabel("y")
    axis.set_title("OrbitLab: 2D N-body motion")
    axis.grid(True, color="white", alpha=0.25)
    if len(names) <= 10:
        legend = axis.legend(loc="upper right", facecolor="black", edgecolor="white")
        for text in legend.get_texts():
            text.set_color("white")
    time_label = axis.text(
        0.03, 0.96, "", transform=axis.transAxes, va="top", color="white"
    )

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
            f"[0:v]fps={fps},split=2[a][b];"
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

