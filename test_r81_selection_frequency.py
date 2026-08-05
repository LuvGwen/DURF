from r81_test_utils import read_rows


rows = read_rows("r81_policy_selection_frequency.csv")
assert len(rows) == 30
lookup = {(row["role"], row["policy"]): float(row["selection_frequency"]) for row in rows}
assert lookup[("Villager", "trust_weighted")] >= 0.99
assert lookup[("Hunter", "reference")] >= 0.80
assert lookup[("Hunter", "highest_suspicion")] >= 0.80
