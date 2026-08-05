import csv

from literature_stage_r7_data import SOURCES
from literature_stage_r71_analysis import OUTPUT_DIR


def test_literature_r71_doi_metadata():
    path = OUTPUT_DIR / "r71_doi_validation_registry.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == len(SOURCES)

    doi_rows = [row for row in rows if row["doi_present"] == "True"]
    assert doi_rows
    assert all(row["doi_syntax_valid"] == "True" for row in doi_rows)
    assert all(row["doi_resolves"] == "True" for row in doi_rows)
    assert all(row["doi_title_match"] == "True" for row in doi_rows)
    assert all(row["doi_author_match"] == "True" for row in doi_rows)
    assert all(row["doi_year_match"] == "True" for row in doi_rows)
    assert all(row["doi_venue_match"] == "True" for row in doi_rows)

    unresolved = [
        row
        for row in rows
        if row["final_doi_status"] in {"unresolved", "incorrect_doi", "replacement_required"}
    ]
    assert not unresolved


if __name__ == "__main__":
    test_literature_r71_doi_metadata()
    print("test_literature_r71_doi_metadata.py passed")
