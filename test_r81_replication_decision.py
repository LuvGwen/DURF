from r81_test_utils import read_rows


replication = read_rows("r81_replication_priority_registry.csv")
readiness = read_rows("r81_r9_readiness_summary.csv")
assert any(row["role"] == "Seer" and row["replication_priority"] == "required_before_default_change" for row in replication)
assert readiness[-1]["status"] == "R8.2 TARGETED REPLICATION REQUIRED"
