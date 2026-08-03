from literature_bibliography_builder import apa_references, author_year_rows, bibtex_entries
from literature_stage_r7_data import SOURCES


def test_literature_bibliography():
    bib = bibtex_entries()
    apa = apa_references()
    rows = author_year_rows()
    for source in SOURCES:
        assert source["citation_key"] in bib
        assert source["title"] in apa
    assert len(rows) == len(SOURCES)
    assert all(row["citation_key"] for row in rows)


if __name__ == "__main__":
    test_literature_bibliography()
    print("test_literature_bibliography.py passed")
