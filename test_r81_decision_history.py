from r81_test_utils import read_rows


rows = read_rows("r81_experimental_decision_history.csv")
assert len(rows) >= 20
assert any(row["stage_id"] == "r61" for row in rows)
assert any(row["stage_id"] == "r8" and row["post_selection_risk"] == "high" for row in rows)
