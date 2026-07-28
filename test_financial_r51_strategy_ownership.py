from financial_r51_strategy_attribution import (
    corrected_strategy_registry_rows,
    is_actor_specific_for_role,
    strategy_owner_role,
)


def test_strategy_owner_roles_are_explicit():
    rows = corrected_strategy_registry_rows()
    assert len(rows) == 5
    assert all(row["strategy_owner_role"] for row in rows)
    assert strategy_owner_role("wolf_random_kill") == "werewolf"
    assert strategy_owner_role("seer_highest_suspicion") == "seer"


def test_invalid_actor_specific_pairs_are_rejected():
    assert not is_actor_specific_for_role("wolf_random_kill", "hunter")
    assert not is_actor_specific_for_role("witch_conservative_poison", "seer")
    assert not is_actor_specific_for_role("villager_random_vote", "werewolf")
    assert is_actor_specific_for_role("wolf_random_kill", "werewolf")
