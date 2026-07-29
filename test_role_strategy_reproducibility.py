"""Tests that R6 synthesis is deterministic."""

from __future__ import annotations

import json
import unittest

from role_strategy_synthesis import (
    build_contradiction_audit,
    build_decision_matrix,
    build_remaining_gaps,
    load_evidence,
)


class RoleStrategyReproducibilityTest(unittest.TestCase):
    def test_synthesis_tables_are_deterministic(self) -> None:
        evidence = load_evidence()
        first = {
            "matrix": build_decision_matrix(evidence),
            "contradictions": build_contradiction_audit(evidence),
            "gaps": build_remaining_gaps(),
        }
        second = {
            "matrix": build_decision_matrix(evidence),
            "contradictions": build_contradiction_audit(evidence),
            "gaps": build_remaining_gaps(),
        }
        self.assertEqual(
            json.dumps(first, sort_keys=True),
            json.dumps(second, sort_keys=True),
        )


if __name__ == "__main__":
    unittest.main()
