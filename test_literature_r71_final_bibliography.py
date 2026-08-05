import re
from literature_metadata_validator import DOI_RE
from literature_stage_r71_analysis import OUTPUT_DIR
from literature_stage_r71_data import final_sources


def test_literature_r71_final_bibliography():
    sources = final_sources()
    assert sources
    assert all(source["doi"] for source in sources)
    assert all(DOI_RE.match(source["doi"]) for source in sources)
    assert all("arxiv.org" not in source["url"].lower() for source in sources)

    doi_values = [source["doi"].lower() for source in sources]
    assert len(doi_values) == len(set(doi_values))

    bib = (OUTPUT_DIR / "r71_final_bibliography.bib").read_text(encoding="utf-8")
    apa = (OUTPUT_DIR / "r71_final_references_apa7.md").read_text(encoding="utf-8")
    bib_keys = set(re.findall(r"@[A-Za-z]+\{([^,]+),", bib))
    assert bib_keys == {source["citation_key"] for source in sources}
    for source in sources:
        assert source["title"] in apa
        assert f"https://doi.org/{source['doi']}" in apa


if __name__ == "__main__":
    test_literature_r71_final_bibliography()
    print("test_literature_r71_final_bibliography.py passed")
