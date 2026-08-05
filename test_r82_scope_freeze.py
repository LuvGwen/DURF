"""Scope-freeze tests for R8.2 targeted independent replication."""

from r82_targeted_replication import (
    FROZEN_MODULES,
    PRIMARY_OUTCOME,
    SECONDARY_OUTCOME,
    frozen_policies_for,
)


def test_frozen_modules_only():
    assert sorted(FROZEN_MODULES) == ["seer", "villager", "witch"]
    assert "hunter" not in FROZEN_MODULES
    assert "wolf" not in FROZEN_MODULES


def test_frozen_policy_pairs_only():
    assert frozen_policies_for("villager") == ["reference", "trust_weighted"]
    assert frozen_policies_for("seer") == ["private_only", "immediate_reveal"]
    assert frozen_policies_for("witch") == ["reference", "aggressive_full"]


def test_primary_outcome_is_not_post_hoc_changed():
    assert PRIMARY_OUTCOME == "actor_payoff"
    assert SECONDARY_OUTCOME == "village_win"


if __name__ == "__main__":
    test_frozen_modules_only()
    test_frozen_policy_pairs_only()
    test_primary_outcome_is_not_post_hoc_changed()
    print("R8.2 scope freeze tests passed.")
