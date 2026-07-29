"""Tests that R6 actor-specific recommendations respect strategy ownership."""

from __future__ import annotations

import unittest

from role_strategy_synthesis import build_decision_matrix, load_evidence


class RoleStrategyActorSpecificOnlyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.matrix = build_decision_matrix(load_evidence())

    def test_actor_specific_rows_owner_matches_role(self) -> None:
        for row in self.matrix:
            if row["actor_specific_or_externality"] == "actor_specific":
                self.assertEqual(row["strategy_owner_role"].lower(), row["role"].lower())

    def test_no_global_configuration_is_actor_specific(self) -> None:
        global_rows = [
            row for row in self.matrix
            if row["strategy_owner_role"] in {"global_village_discussion", "global_configuration"}
        ]
        self.assertTrue(global_rows)
        self.assertTrue(
            all(row["actor_specific_or_externality"] != "actor_specific" for row in global_rows)
        )

    def test_hunter_has_no_recommended_actor_specific_strategy(self) -> None:
        hunter_rows = [row for row in self.matrix if row["role"] == "Hunter"]
        self.assertTrue(hunter_rows)
        self.assertTrue(
            all(row["recommendation_label"] in {"insufficient data", "requires targeted experiment"} for row in hunter_rows)
        )


if __name__ == "__main__":
    unittest.main()
