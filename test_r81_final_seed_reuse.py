from r81_test_utils import read_rows


rows = read_rows("r81_final_seed_reuse_audit.csv")
final_rows = [row for row in rows if row["seed_split"] in {"final_test", "final_evaluation"}]
assert final_rows
assert all(row["reuse_classification"] == "post_test_model_or_policy_selection" for row in final_rows)
assert all(row["raw_gameplay_leakage"] == "False" for row in rows)
