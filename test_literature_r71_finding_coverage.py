import csv
from collections import defaultdict

from literature_stage_r7_data import PROJECT_FINDINGS
from literature_stage_r71_analysis import OUTPUT_DIR


def test_literature_r71_finding_coverage():
    with (OUTPUT_DIR / "r71_revised_finding_literature_matrix.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    by_finding = defaultdict(list)
    for row in rows:
        by_finding[row["finding_id"]].append(row)
    assert set(by_finding) == {finding[0] for finding in PROJECT_FINDINGS}
    assert all(row["doi_verified"] == "True" for row in rows)
    assert all(row["final_citation_eligible"] == "True" for row in rows)
    assert all(row["coverage_status"] != "manual_review_required" for row in rows)
    for finding_id, finding_rows in by_finding.items():
        assert any(row["recent_source"] == "True" for row in finding_rows), finding_id


if __name__ == "__main__":
    test_literature_r71_finding_coverage()
    print("test_literature_r71_finding_coverage.py passed")
