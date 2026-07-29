"""Tests for R6 remaining-gap analysis."""

from __future__ import annotations

import unittest

from role_strategy_gap_analysis import critical_gap_roles, get_remaining_evidence_gaps


class RoleStrategyGapAnalysisTest(unittest.TestCase):
    def test_critical_gap_roles_include_core_missing_roles(self) -> None:
        roles = critical_gap_roles()
        self.assertIn("Hunter", roles)
        self.assertIn("Seer", roles)
        self.assertIn("Witch", roles)

    def test_every_gap_identifies_required_experiment(self) -> None:
        for row in get_remaining_evidence_gaps():
            self.assertTrue(row["required_experiment"])
            self.assertTrue(row["minimum_scale"])
            self.assertTrue(row["formal_analysis"])


if __name__ == "__main__":
    unittest.main()
