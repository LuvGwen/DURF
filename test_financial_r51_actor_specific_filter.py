from financial_r51_analysis import build_actor_specific_raw, enrich_player_rows, read_csv


def test_actor_specific_rows_require_owner_equals_affected_role():
    rows = enrich_player_rows(read_csv("results/payoff_matrix_stage_r4/r4_player_level_payoff_raw.csv"))
    actor_rows = build_actor_specific_raw(rows)
    assert actor_rows
    assert all(row["strategy_owner_role"] == row["affected_role"] for row in actor_rows)
    assert not any(row["strategy_name"] == "reference_strategy_mix" for row in actor_rows)
