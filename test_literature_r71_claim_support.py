import csv

from literature_stage_r71_analysis import OUTPUT_DIR


def test_literature_r71_claim_support():
    with (OUTPUT_DIR / "r71_revised_claim_support_audit.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    assert all(row["doi"] for row in rows)
    assert all(row["recent_companion_present"] == "True" for row in rows)

    finance = [row for row in rows if row["claim_type"] == "financial analogy"]
    bow = [row for row in rows if row["claim_id"] == "R7-C07"]
    offline = [row for row in rows if row["claim_id"] == "R7-C08"]
    assert finance and any(row["recent"] == "True" for row in finance)
    assert bow and all(row["recent"] == "True" for row in bow)
    assert offline and all(row["recent"] == "True" for row in offline)


if __name__ == "__main__":
    test_literature_r71_claim_support()
    print("test_literature_r71_claim_support.py passed")
