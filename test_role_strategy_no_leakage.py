"""Tests for R6 leakage and association-language safeguards."""

from __future__ import annotations

import unittest

from role_strategy_synthesis import build_data_analysis_summary, build_decision_matrix, load_evidence


class RoleStrategyNoLeakageTest(unittest.TestCase):
    def test_information_premium_is_associative(self) -> None:
        matrix = build_decision_matrix(load_evidence())
        info = next(row for row in matrix if row["strategy"] == "early_wolf_discovery_signal")
        self.assertIn("association", str(info["formal_inference_status"]))
        self.assertIn("outcome-dependent", str(info["main_risk"]))

    def test_summary_mentions_no_hidden_information_claim(self) -> None:
        evidence = load_evidence()
        summary = build_data_analysis_summary(evidence, build_decision_matrix(evidence))
        self.assertTrue(
            all("hidden-information" in row["leakage_status"] for row in summary)
        )


if __name__ == "__main__":
    unittest.main()
