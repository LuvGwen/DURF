from r81_test_utils import read_rows


rows = read_rows("r81_split_integrity_registry.csv")
assert any(row["split_unit"] == "policy_final_selection" and row["status"] == "selection_risk_found" for row in rows)
assert any(row["split_unit"] == "matched_set" and row["status"] == "pass" for row in rows)
