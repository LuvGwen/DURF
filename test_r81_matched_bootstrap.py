from r81_test_utils import read_rows


rows = read_rows("r81_policy_rank_bootstrap.csv")
assert len(rows) == 150000
assert {row["cluster_unit"] for row in rows} == {"matched_set_id"}
assert max(int(row["bootstrap_replicate"]) for row in rows if row["role"] == "Villager") == 5000
