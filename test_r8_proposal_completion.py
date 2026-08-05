from r8_test_utils import read_rows


rows = read_rows("r8_proposal_completion_matrix.csv")
readiness = read_rows("r8_r9_readiness_summary.csv")

assert len(rows) >= 60
assert not any(row["blocking_final_report"] == "Yes" for row in rows)
assert all(row["status"] == "ready" for row in readiness)
print("test_r8_proposal_completion passed")
