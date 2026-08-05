from r8_test_utils import read_rows


rows = read_rows("r8_final_literature_integration_table.csv")

assert len(rows) >= 40
assert all(int(row["doi_verified_source_count"]) == int(row["eligible_source_count"]) for row in rows)
assert all(row["dois"] for row in rows)
print("test_r8_literature_doi_only passed")
