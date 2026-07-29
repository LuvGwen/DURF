"""Tests that R6 leaves simulator default behavior available."""

from __future__ import annotations

import unittest

from simulation import run_simulation, summarize_results


class RoleStrategyDefaultBehaviorTest(unittest.TestCase):
    def test_default_simulation_still_runs(self) -> None:
        results = run_simulation(num_games=1, max_rounds=20, seed=42)
        summary = summarize_results(results)
        self.assertEqual(summary["total_games"], 1)
        self.assertEqual(
            summary["wolf_wins"] + summary["village_wins"] + summary["draws"],
            1,
        )


if __name__ == "__main__":
    unittest.main()
