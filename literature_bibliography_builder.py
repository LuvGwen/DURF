"""Bibliography formatting helpers for R7."""

from __future__ import annotations

import re

from literature_stage_r7_data import SOURCES


def _entry_type(source: dict[str, str]) -> str:
    if source["source_type"] in {"journal article"}:
        return "article"
    if source["source_type"] in {"conference paper", "workshop paper"}:
        return "inproceedings"
    if source["source_type"] in {"book", "textbook"}:
        return "book"
    if source["source_type"] == "book chapter":
        return "incollection"
    return "misc"


def _bib_escape(value: str) -> str:
    return value.replace("&", "\\&")


def bibtex_entries(sources=None) -> str:
    entries = []
    for source in sources or SOURCES:
        fields = {
            "title": source["title"],
            "author": " and ".join(part.strip() for part in source["authors"].split(";")),
            "year": source["year"],
            "url": source["url"],
            "note": f"Source type: {source['source_type']}; R7 quality grade: {source['quality_grade']}",
        }
        if _entry_type(source) == "article":
            fields["journal"] = source["venue"]
        elif _entry_type(source) == "inproceedings":
            fields["booktitle"] = source["venue"]
        elif _entry_type(source) == "book":
            fields["publisher"] = source["venue"]
        else:
            fields["howpublished"] = source["venue"]
        if source.get("doi"):
            fields["doi"] = source["doi"]
        body = ",\n".join(
            f"  {key} = {{{_bib_escape(value)}}}" for key, value in fields.items() if value
        )
        entries.append(f"@{_entry_type(source)}{{{source['citation_key']},\n{body}\n}}")
    return "\n\n".join(entries) + "\n"


def apa_reference(source: dict[str, str]) -> str:
    authors = source["authors"].replace(";", ",")
    title = source["title"]
    venue = source["venue"]
    tail = source["doi"] if source["doi"] else source["url"]
    return f"{authors}. ({source['year']}). {title}. {venue}. {tail}"


def apa_references(sources=None) -> str:
    rows = ["# R7 References (APA 7 Draft)", ""]
    for source in sorted(sources or SOURCES, key=lambda item: item["citation_key"]):
        rows.append(f"- {apa_reference(source)}")
    rows.append("")
    rows.append("Note: Entries marked in metadata validation as manual-review items require final human bibliography cleanup before submission.")
    return "\n".join(rows) + "\n"


def author_year_rows(sources=None) -> list[dict[str, str]]:
    rows = []
    for source in sources or SOURCES:
        first_author = re.split(r";|,", source["authors"])[0].strip()
        rows.append(
            {
                "source_id": source["source_id"],
                "citation_key": source["citation_key"],
                "author_year": f"{first_author} ({source['year']})",
                "title": source["title"],
                "doi": source["doi"],
                "url": source["url"],
                "metadata_status": source["metadata_status"],
            }
        )
    return rows


if __name__ == "__main__":
    print(bibtex_entries())
