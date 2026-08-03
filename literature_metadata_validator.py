"""Validation helpers for R7 literature metadata."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from literature_stage_r7_data import SOURCES


DOI_RE = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$")


def valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_sources(sources=None) -> list[dict[str, str]]:
    rows = []
    seen_doi = {}
    seen_title_author_year = {}
    for source in sources or SOURCES:
        source_id = source["source_id"]
        title_key = (
            source["title"].strip().lower(),
            source["authors"].split(";")[0].strip().lower(),
            source["year"],
        )
        duplicate_key = seen_title_author_year.get(title_key)
        if duplicate_key:
            rows.append(
                {
                    "source_id": source_id,
                    "check": "duplicate_title_author_year",
                    "status": "FAIL",
                    "detail": duplicate_key,
                }
            )
        else:
            seen_title_author_year[title_key] = source_id

        doi = source.get("doi", "").strip()
        if doi:
            rows.append(
                {
                    "source_id": source_id,
                    "check": "doi_format",
                    "status": "PASS" if DOI_RE.match(doi) else "FAIL",
                    "detail": doi,
                }
            )
            if doi.lower() in seen_doi:
                rows.append(
                    {
                        "source_id": source_id,
                        "check": "duplicate_doi",
                        "status": "FAIL",
                        "detail": seen_doi[doi.lower()],
                    }
                )
            else:
                seen_doi[doi.lower()] = source_id
        else:
            rows.append(
                {
                    "source_id": source_id,
                    "check": "doi_absent_flagged",
                    "status": "PASS",
                    "detail": source.get("metadata_status", ""),
                }
            )

        required = ["citation_key", "title", "authors", "year", "venue", "url"]
        missing = [field for field in required if not source.get(field)]
        rows.append(
            {
                "source_id": source_id,
                "check": "required_metadata_present",
                "status": "PASS" if not missing else "FAIL",
                "detail": ",".join(missing) if missing else "complete",
            }
        )
        rows.append(
            {
                "source_id": source_id,
                "check": "url_syntax",
                "status": "PASS" if valid_url(source.get("url", "")) else "FAIL",
                "detail": source.get("url", ""),
            }
        )
        rows.append(
            {
                "source_id": source_id,
                "check": "fabrication_flag_absent",
                "status": "PASS"
                if source.get("metadata_status") not in {"fabricated", "unknown"}
                else "FAIL",
                "detail": source.get("metadata_status", ""),
            }
        )
    return rows


def validation_passed(rows=None) -> bool:
    rows = rows if rows is not None else validate_sources()
    return all(row["status"] == "PASS" for row in rows)


if __name__ == "__main__":
    checks = validate_sources()
    failed = [row for row in checks if row["status"] != "PASS"]
    print(f"Literature metadata validation checks: {len(checks)}")
    print(f"Failed: {len(failed)}")
    for row in failed:
        print(row)
    raise SystemExit(1 if failed else 0)
