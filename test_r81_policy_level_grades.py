from r81_test_utils import read_rows


rows = read_rows("r81_policy_evidence_grade_registry.csv")
lookup = {(row["role"], row["policy"]): row for row in rows}
assert lookup[("Villager", "trust_weighted")]["evidence_grade"] == "A"
assert lookup[("Witch", "conservative_full")]["evidence_grade"] == "rejected"
assert lookup[("Seer", "private_only")]["evidence_grade"] == "B"
