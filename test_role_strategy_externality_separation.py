"""Tests for R6 externality separation."""

from __future__ import annotations

import unittest

from role_strategy_externality_synthesis import get_cross_role_externality_matrix
from role_strategy_synthesis import build_decision_matrix, load_evidence


class RoleStrategyExternalitySeparationTest(unittest.TestCase):
    def test_externality_rows_have_different_owner_and_affected_role(self) -> None:
        rows = get_cross_role_externality_matrix()
        self.assertGreater(len(rows), 0)
        self.assertTrue(
            all(row["strategy_owner_role"] != row["affected_role"] for row in rows)
        )

    def test_decision_matrix_keeps_externalities_out(self) -> None:
        matrix = build_decision_matrix(load_evidence())
        self.assertTrue(
            all(row["actor_specific_or_externality"] != "externality" for row in matrix)
        )


if __name__ == "__main__":
    unittest.main()
