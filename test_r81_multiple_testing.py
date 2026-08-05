from r81_test_utils import read_rows


rows = read_rows("r81_project_wide_multiple_testing_inventory.csv")
families = {row["family_id"] for row in rows}
assert {"R61_hunter", "R61_seer", "R61_witch", "R61_wolf", "R61_villager", "R8_MAX_SELECTION"}.issubset(families)
assert any(row["post_selection_risk"] == "high" for row in rows)
