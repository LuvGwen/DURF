from r81_test_utils import read_rows


rows = read_rows("r81_strategy_search_registry.csv")
assert len(rows) >= 17
assert sum(int(row["variant_count"]) for row in rows) >= 100
assert any(row["mechanism_family"] == "Witch poison threshold" for row in rows)
