"""Search-log and screening-registry helpers for R7."""

from __future__ import annotations

from literature_stage_r7_data import ACCESS_DATE, SEARCH_LOGS, SOURCES


def search_log_rows() -> list[dict[str, str]]:
    rows = []
    for search_id, engine, query, domain, screened, retained, notes in SEARCH_LOGS:
        rows.append(
            {
                "search_id": search_id,
                "database_or_engine": engine,
                "search_query": query,
                "search_date": ACCESS_DATE,
                "year_filter": "none",
                "domain": domain,
                "result_count_screened": screened,
                "sources_retained": retained,
                "exclusion_reason": "duplicates, superficial keyword matches, inaccessible metadata, or unrelated domain focus",
                "notes": notes,
            }
        )
    return rows


def source_screening_rows() -> list[dict[str, str]]:
    return [
        {
            "source_id": source["source_id"],
            "title": source["title"],
            "screened": "yes",
            "included": "yes",
            "exclusion_reason": "",
            "duplicate_of": "",
            "quality_rating": source["quality_grade"],
            "notes": source["relevance"],
        }
        for source in SOURCES
    ]


if __name__ == "__main__":
    for row in search_log_rows():
        print(row)
