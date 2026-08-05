from r81_test_utils import read_rows


rows = read_rows("r81_outcome_switching_registry.csv")
assert any(row["analysis_area"] == "Seer reveal policy" and row["outcome_switching_risk"] == "high" for row in rows)
assert any("BoW" in row["analysis_area"] for row in rows)
assert any("ML" in row["analysis_area"] for row in rows)
