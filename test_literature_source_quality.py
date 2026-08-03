from literature_source_quality import domain_coverage_rows, source_quality_counts


def test_literature_source_quality():
    coverage = domain_coverage_rows()
    assert all(row["meets_minimum"] == "True" for row in coverage), coverage
    counts = source_quality_counts()
    assert counts["A"] + counts["B"] >= 45
    assert counts["A"] >= counts["C"]


if __name__ == "__main__":
    test_literature_source_quality()
    print("test_literature_source_quality.py passed")
