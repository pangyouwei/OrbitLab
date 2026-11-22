"""Compare nearby N-body initial states over the same simulation interval."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .run import load_config, simulate


def compare_configs(first: dict, second: dict) -> tuple[np.ndarray, np.ndarray]:
    """Return time and RMS position separation of matching bodies."""
    if first["dt"] != second["dt"] or first["steps"] != second["steps"]:
        raise ValueError("both configurations must use the same dt and steps")
    if first.get("G", 1.0) != second.get("G", 1.0) or first.get(
        "softening", 0.0
    ) != second.get("softening", 0.0):
        raise ValueError("both configurations must use the same G and softening")
    if [body["name"] for body in first["bodies"]] != [
        body["name"] for body in second["bodies"]
    ] or [body["mass"] for body in first["bodies"]] != [
        body["mass"] for body in second["bodies"]
    ]:
        raise ValueError("both configurations must have matching bodies and masses")

    times, first_positions, _, _, _ = simulate(first)
    _, second_positions, _, _, _ = simulate(second)
    differences = first_positions - second_positions
    rms_separation = np.sqrt(np.mean(np.sum(differences**2, axis=2), axis=1))
    return times, rms_separation


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare nearby N-body states")
    parser.add_argument("first", type=Path)
    parser.add_argument("second", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/nbody_comparison"))
    args = parser.parse_args()

    try:
        times, separation = compare_configs(
            load_config(args.first), load_config(args.second)
        )
    except ValueError as error:
        parser.error(str(error))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / "separation.csv").open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.writer(file)
        writer.writerow(["time", "rms_position_separation"])
        writer.writerows(zip(times, separation))

    figure, axis = plt.subplots(figsize=(8, 5), dpi=180)
    axis.semilogy(times[1:], separation[1:], color="tab:blue", linewidth=1.8)
    axis.set_xlabel("Simulation time")
    axis.set_ylabel("RMS position separation")
    axis.set_title("Nearby N-body trajectories diverge")
    axis.grid(True, alpha=0.25, which="both")
    figure.tight_layout()
    figure.savefig(args.output_dir / "separation.png")
    plt.close(figure)

    summary = {
        "first": str(args.first),
        "second": str(args.second),
        "final_time": float(times[-1]),
        "final_rms_position_separation": float(separation[-1]),
        "maximum_rms_position_separation": float(np.max(separation)),
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Saved comparison to {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
