from financial_r51_analysis import build_cross_role_externality_raw, enrich_player_rows, read_csv


def test_externality_rows_require_owner_differs_from_affected_role():
    rows = enrich_player_rows(read_csv("results/payoff_matrix_stage_r4/r4_player_level_payoff_raw.csv"))
    external_rows = build_cross_role_externality_raw(rows)
    assert external_rows
    assert all(row["external_strategy_owner_role"] != row["affected_role"] for row in external_rows)
    assert all(row["interpretation_limit"].startswith("cross-role") for row in external_rows)
