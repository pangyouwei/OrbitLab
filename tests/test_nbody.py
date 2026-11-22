"""Small numerical checks for generated N-body initial states."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

from orbitlab.compare import compare_configs
from orbitlab.generate import make_ring_config
from orbitlab.physics import accelerations, center_of_mass, center_of_mass_velocity
from orbitlab.visualize import camera_limits


class NBodyTests(unittest.TestCase):
    def test_generated_state_has_stationary_center_of_mass(self) -> None:
        config = make_ring_config(12, 42, 0.002, 1.0, 0.05)
        bodies = config["bodies"]
        positions = np.array([body["position"] for body in bodies])
        velocities = np.array([body["velocity"] for body in bodies])
        masses = np.array([body["mass"] for body in bodies])
        np.testing.assert_allclose(center_of_mass(positions, masses), 0, atol=1e-14)
        np.testing.assert_allclose(
            center_of_mass_velocity(velocities, masses), 0, atol=1e-14
        )
        forces = masses[:, None] * accelerations(
            positions, masses, softening=config["softening"]
        )
        np.testing.assert_allclose(np.sum(forces, axis=0), 0, atol=1e-14)

    def test_nearby_states_separate(self) -> None:
        first = make_ring_config(12, 42, 0.002, 12.0, 0.05)
        second = make_ring_config(12, 42, 0.002, 12.0, 0.05)
        second["bodies"][0]["velocity"][1] += 1e-5
        second["bodies"][1]["velocity"][1] -= 1e-5
        times, separation = compare_configs(first, second)
        self.assertEqual(len(times), 6001)
        self.assertEqual(separation[0], 0)
        self.assertGreater(separation[-1], 0.1)

    def test_camera_contains_all_bodies_and_trails(self) -> None:
        positions = np.array(
            [
                [[-1.0, 0.0], [1.0, 0.0]],
                [[-3.0, 2.0], [2.0, -1.0]],
                [[-2.0, 1.0], [8.0, 4.0]],
            ]
        )
        frame_indices = np.array([0, 1, 2])
        limits = camera_limits(positions, frame_indices)
        for frame, (left, right, bottom, top) in enumerate(limits):
            history = positions[: frame + 1]
            self.assertLess(left, float(history[:, :, 0].min()))
            self.assertGreater(right, float(history[:, :, 0].max()))
            self.assertLess(bottom, float(history[:, :, 1].min()))
            self.assertGreater(top, float(history[:, :, 1].max()))

    def test_duration_option_overrides_json_steps(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(
                [
                    sys.executable, "-m", "orbitlab.run",
                    str(project_root / "examples/two_body_2.json"),
                    "--duration", "0.01", "--skip-animation",
                    "--output-dir", directory,
                ],
                cwd=project_root,
                check=True,
                capture_output=True,
                text=True,
            )
            summary_path = Path(directory) / "two_body_2/two_body_2_summary.json"
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["steps"], 5)
            self.assertAlmostEqual(summary["final_time"], 0.01)


if __name__ == "__main__":
    unittest.main()
