from r8_test_utils import read_rows


rows = read_rows("r8_financial_analogy_final_table.csv")
limits = " ".join(row["unsupported_or_limited_use"] for row in rows)

assert len(rows) >= 5
assert "not" in limits.lower()
assert any(row["analogy_component"] == "p_wolf" for row in rows)
print("test_r8_financial_analogy_limits passed")
