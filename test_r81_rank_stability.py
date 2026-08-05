from r81_test_utils import read_rows


rows = read_rows("r81_selection_stability_summary.csv")
assert len(rows) == 5
assert any(row["role"] == "Seer" and row["bootstrap_top_policy"] == "immediate_reveal" for row in rows)
assert any(row["role"] == "Witch" and row["bootstrap_top_policy"] == "aggressive_full" for row in rows)
