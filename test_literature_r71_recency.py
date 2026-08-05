import csv

from literature_stage_r71_analysis import OUTPUT_DIR
from literature_stage_r71_data import (
    FOUNDATIONAL_EXCEPTIONS,
    RECENT_START_YEAR,
    RECENT_END_YEAR,
    all_sources_by_id,
    final_sources,
)


def test_literature_r71_recency():
    lookup = all_sources_by_id()
    sources = final_sources()
    recent = [
        source
        for source in sources
        if RECENT_START_YEAR <= int(source["year"]) <= RECENT_END_YEAR
    ]
    assert len(recent) / len(sources) >= 0.75

    old_sources = [
        source
        for source in sources
        if not (RECENT_START_YEAR <= int(source["year"]) <= RECENT_END_YEAR)
    ]
    assert {source["source_id"] for source in old_sources} <= set(FOUNDATIONAL_EXCEPTIONS)
    for source in old_sources:
        companions = FOUNDATIONAL_EXCEPTIONS[source["source_id"]][2].split(";")
        assert any(
            RECENT_START_YEAR <= int(lookup[companion_id]["year"]) <= RECENT_END_YEAR
            for companion_id in companions
        )

    with (OUTPUT_DIR / "r71_domain_recency_coverage.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    assert all(row["recent_2016_2026_percent"] for row in rows)


if __name__ == "__main__":
    test_literature_r71_recency()
    print("test_literature_r71_recency.py passed")
