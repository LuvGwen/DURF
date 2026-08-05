from r83_primary_contrast_recalculation import recompute_primary_contrasts


rows = {row["module"]: row for row in recompute_primary_contrasts()}

assert set(rows) == {"villager", "seer", "witch"}
assert all(int(row["matched_sets"]) == 1000 for row in rows.values())
assert abs(rows["villager"]["paired_difference"] - 0.1529) < 1e-12
assert abs(rows["seer"]["paired_difference"] - 0.06735) < 1e-12
assert abs(rows["witch"]["paired_difference"] - 0.1651) < 1e-12
assert all(row["final_authoritative_result"] == "replicated_positive_primary_effect" for row in rows.values())
