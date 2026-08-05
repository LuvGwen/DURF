from r81_test_utils import read_rows


rows = read_rows("r81_winners_curse_estimates.csv")
assert len(rows) == 30
assert any(row["winner_curse_estimate"] not in ("", "0") for row in rows)
assert all("selection_frequency" in row for row in rows)
