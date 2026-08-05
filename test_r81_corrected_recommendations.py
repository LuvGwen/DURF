from r81_test_utils import read_rows


rows = read_rows("r81_corrected_role_strategy_table.csv")
lookup = {row["role"]: row for row in rows}
assert lookup["Seer"]["changed"] == "True"
assert lookup["Seer"]["audited_recommended_policy"] == "private_only"
assert lookup["Witch"]["changed"] == "True"
assert lookup["Villager"]["confirmatory_status"] == "confirmatory_supported"
