from r8_test_utils import read_rows


rows = read_rows("r8_supported_findings.csv")
texts = " ".join(row["final_safe_wording"] for row in rows)

assert len(rows) >= 3
assert "Trust-weighted voting" in texts
assert "Financial-risk metrics" in texts
assert all(row["finding_type"] == "supported" for row in rows)
print("test_r8_supported_findings passed")
