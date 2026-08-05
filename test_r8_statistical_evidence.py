from r8_test_utils import read_rows


rows = read_rows("r8_final_statistical_evidence_table.csv")
statuses = {row["conclusion_status"] for row in rows}

assert len(rows) >= 14
assert "statistically_supported_harm" in statuses
assert "statistically_supported_improvement" in statuses
assert all(row["independent_unit"] for row in rows)
assert all(row["source_data"] for row in rows)
print("test_r8_statistical_evidence passed")
