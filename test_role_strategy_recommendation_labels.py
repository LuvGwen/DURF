"""Tests for R6 recommendation label validity."""

from __future__ import annotations

import unittest

from role_strategy_evidence_registry import RECOMMENDATION_LABELS
from role_strategy_synthesis import build_decision_matrix, build_default_registry, load_evidence


class RoleStrategyRecommendationLabelsTest(unittest.TestCase):
    def test_all_matrix_labels_allowed(self) -> None:
        matrix = build_decision_matrix(load_evidence())
        bad = [
            row["recommendation_label"]
            for row in matrix
            if row["recommendation_label"] not in RECOMMENDATION_LABELS
        ]
        self.assertEqual(bad, [])

    def test_every_role_has_current_default_status(self) -> None:
        matrix = build_decision_matrix(load_evidence())
        defaults = build_default_registry(matrix)
        self.assertEqual(
            {row["role"] for row in defaults},
            {"Villager", "Seer", "Witch", "Hunter", "Werewolf"},
        )


if __name__ == "__main__":
    unittest.main()
