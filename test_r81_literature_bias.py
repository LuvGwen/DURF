from r81_test_utils import read_rows


rows = read_rows("r81_literature_confirmation_bias_audit.csv")
assert len(rows) >= 4
assert any("DOI" in row["evidence"] for row in rows)
