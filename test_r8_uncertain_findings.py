from r8_test_utils import read_rows


rows = read_rows("r8_uncertain_findings.csv")
texts = " ".join(row["final_safe_wording"] for row in rows)

assert len(rows) >= 4
assert "promising" in texts or "diagnostic" in texts
assert all(row["finding_type"] == "uncertain_or_diagnostic" for row in rows)
print("test_r8_uncertain_findings passed")
