"""Tests for R6 evidence grading helpers."""

from __future__ import annotations

import unittest

from role_strategy_evidence_grading import (
    evidence_grade_rank,
    is_valid_evidence_grade,
    is_valid_recommendation_label,
    label_for_adjusted_p_value,
)


class RoleStrategyEvidenceGradingTest(unittest.TestCase):
    def test_grade_validation(self) -> None:
        self.assertTrue(is_valid_evidence_grade("A"))
        self.assertTrue(is_valid_evidence_grade("U"))
        self.assertFalse(is_valid_evidence_grade("Z"))

    def test_grade_order(self) -> None:
        self.assertGreater(evidence_grade_rank("A"), evidence_grade_rank("C"))
        self.assertGreater(evidence_grade_rank("D"), evidence_grade_rank("U"))

    def test_label_validation(self) -> None:
        self.assertTrue(is_valid_recommendation_label("no supported improvement"))
        self.assertFalse(is_valid_recommendation_label("globally optimal"))

    def test_non_significant_positive_is_not_supported(self) -> None:
        label = label_for_adjusted_p_value("0.37", "positive")
        self.assertEqual(label, "promising but uncertain")

    def test_significant_harm_is_harmful(self) -> None:
        label = label_for_adjusted_p_value("0.001", "negative", harmful_context=True)
        self.assertEqual(label, "statistically supported harmful")


if __name__ == "__main__":
    unittest.main()
