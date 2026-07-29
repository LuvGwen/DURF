"""Tests for R6 contradiction priority rules."""

from __future__ import annotations

import unittest

from role_strategy_contradiction_audit import get_cross_stage_contradictions


class RoleStrategyContradictionPriorityTest(unittest.TestCase):
    def test_required_contradictions_present(self) -> None:
        topics = " ".join(row["research_topic"] for row in get_cross_stage_contradictions())
        self.assertIn("BoW", topics)
        self.assertIn("ML", topics)
        self.assertIn("strategy frontier", topics)
        self.assertIn("Edge-seat", topics)

    def test_priority_sources_are_later_validation_sources(self) -> None:
        priorities = {
            row["contradiction_id"]: row["which_result_has_priority"]
            for row in get_cross_stage_contradictions()
        }
        self.assertIn("R3 matched live policy outcomes", priorities["R6-X01"])
        self.assertIn("Stage 2A/2B complete live policy contrasts", priorities["R6-X02"])
        self.assertIn("R5.1 actor-specific attribution audit", priorities["R6-X03"])


if __name__ == "__main__":
    unittest.main()
