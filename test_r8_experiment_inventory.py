from r8_test_utils import assert_exists, read_rows


rows = read_rows("r8_experiment_inventory.csv")
stage_ids = {row["stage_id"] for row in rows}

assert_exists("results/final_integrated_analysis_stage_r8/r8_experiment_inventory.csv")
assert len(rows) >= 20
assert "structured_seer_search" in stage_ids
assert "r6_role_strategy_synthesis" in stage_ids
assert "r7_literature" in stage_ids
assert all(row["included_in_final_analysis"] for row in rows)
print("test_r8_experiment_inventory passed")
