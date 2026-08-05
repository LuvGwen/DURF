from r8_test_utils import read_rows


rows = read_rows("r8_negative_results.csv")
texts = " ".join(row["final_safe_wording"] for row in rows)

assert len(rows) >= 5
assert "BoW" in texts
assert "ML" in texts
assert all(row["finding_type"] == "negative_or_harmful" for row in rows)
print("test_r8_negative_findings passed")
