from literature_finding_mapper import finding_mapping_rows, unmapped_findings
from literature_stage_r7_data import PROJECT_FINDINGS


def test_literature_finding_mapping():
    rows = finding_mapping_rows()
    assert len(rows) >= len(PROJECT_FINDINGS)
    assert not unmapped_findings()
    assert all(row["source_id"] for row in rows)
    assert all(row["relationship"] for row in rows)


if __name__ == "__main__":
    test_literature_finding_mapping()
    print("test_literature_finding_mapping.py passed")
