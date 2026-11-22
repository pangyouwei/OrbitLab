"""Small numerical checks for generated N-body initial states."""

from __future__ import annotations

import unittest

import numpy as np

from orbitlab.compare import compare_configs
from orbitlab.generate import make_ring_config
from orbitlab.physics import accelerations, center_of_mass, center_of_mass_velocity


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


if __name__ == "__main__":
    unittest.main()
