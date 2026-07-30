from __future__ import annotations

import re
import unittest
from contextlib import redirect_stdout
from io import StringIO

try:
    from .framework_core import ContinuumSimulation
except ImportError:
    from framework_core import ContinuumSimulation


class CriticalDelayScalingTests(unittest.TestCase):
    @staticmethod
    def _run_and_extract_delay(mu: float) -> float:
        simulation = ContinuumSimulation(
            num_layers=3,
            dt=0.01,
            seed=76,
        )
        output = StringIO()

        with redirect_stdout(output):
            simulation.run_marnov_demolition(
                external_pressure=1.0,
                mu=mu,
                min_coherence=0.0,
                max_tacts=1,
            )

        match = re.search(
            r"t_delay: ([0-9]+(?:\.[0-9]+)?)",
            output.getvalue(),
        )

        if match is None:
            raise AssertionError(
                "Marnov demolition output does not contain t_delay."
            )

        return float(match.group(1))

    def test_fourfold_velocity_halves_delay(self) -> None:
        delay_at_unit_velocity = self._run_and_extract_delay(
            1.0
        )
        delay_at_fourfold_velocity = self._run_and_extract_delay(
            4.0
        )

        self.assertAlmostEqual(
            delay_at_unit_velocity,
            1.0,
            places=5,
        )
        self.assertAlmostEqual(
            delay_at_fourfold_velocity,
            0.5,
            places=5,
        )
        self.assertAlmostEqual(
            delay_at_unit_velocity
            / delay_at_fourfold_velocity,
            2.0,
            places=5,
        )


if __name__ == "__main__":
    unittest.main()
