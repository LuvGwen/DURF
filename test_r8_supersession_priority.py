from r8_test_utils import read_rows


rows = read_rows("r8_superseded_result_registry.csv")
claims = " ".join(row["superseded_claim"] + " " + row["superseding_evidence"] for row in rows)

assert len(rows) >= 8
assert "BoW" in claims
assert "ML" in claims
assert "matched" in claims or "complete game" in claims or "live games" in claims
assert all(row["final_reporting_rule"] for row in rows)
print("test_r8_supersession_priority passed")
