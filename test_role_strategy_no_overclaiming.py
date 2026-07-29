"""Tests for R6 overclaiming constraints."""

from __future__ import annotations

import unittest

from role_strategy_synthesis import build_decision_matrix, load_evidence


class RoleStrategyNoOverclaimingTest(unittest.TestCase):
    def test_no_strategy_label_claims_global_optimum(self) -> None:
        matrix = build_decision_matrix(load_evidence())
        forbidden = {"globally optimal", "optimal", "proven", "guarantees"}
        labels = " ".join(str(row["recommendation_label"]) for row in matrix).lower()
        recommendations = " ".join(str(row["current_recommendation"]) for row in matrix).lower()
        for word in forbidden:
            self.assertNotIn(word, labels)
            self.assertNotIn(word, recommendations)

    def test_positive_mean_without_significance_is_uncertain(self) -> None:
        matrix = build_decision_matrix(load_evidence())
        witch = next(row for row in matrix if row["strategy"] == "witch_conservative_poison")
        self.assertEqual(witch["recommendation_label"], "promising but uncertain")
        self.assertEqual(witch["evidence_grade"], "C")


if __name__ == "__main__":
    unittest.main()
