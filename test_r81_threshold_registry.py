from r81_test_utils import read_rows


rows = read_rows("r81_threshold_search_registry.csv")
params = {row["parameter"]: row for row in rows}
assert "witch_poison_threshold" in params
assert "0.30" in params["witch_poison_threshold"]["values_tested"]
assert "trust_vote_weight" in params
