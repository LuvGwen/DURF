from r83_common import FROZEN_COMPARISONS, paired_differences, r82_game_rows


for module in FROZEN_COMPARISONS:
    diffs = paired_differences(module)
    matched_ids = [row["matched_set_id"] for row in diffs]
    assert len(diffs) == 1000
    assert len(matched_ids) == len(set(matched_ids))

game_rows = r82_game_rows()
assert len(game_rows) == 6000
assert {"matched_set_id", "module", "policy", "actor_payoff"}.issubset(game_rows[0])
