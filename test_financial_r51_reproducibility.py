from financial_r51_analysis import build_actor_specific_raw, enrich_player_rows, read_csv


def test_actor_specific_dataset_is_deterministic():
    rows = enrich_player_rows(read_csv("results/payoff_matrix_stage_r4/r4_player_level_payoff_raw.csv"))
    left = build_actor_specific_raw(rows)
    right = build_actor_specific_raw(rows)
    assert left == right
