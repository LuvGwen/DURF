from r81_test_utils import read_rows


rows = read_rows("r81_bow_overfitting_audit.csv")
assert any(row["final_label"] == "statistically_supported_harm" for row in rows)
assert any(row["risk"] == "offline metric overclaiming" for row in rows)
