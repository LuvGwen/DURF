from literature_stage_r7_data import SOURCES


def test_literature_no_duplicate_sources():
    source_ids = [source["source_id"] for source in SOURCES]
    keys = [source["citation_key"] for source in SOURCES]
    dois = [source["doi"].lower() for source in SOURCES if source["doi"]]
    title_author_year = [
        (
            source["title"].strip().lower(),
            source["authors"].split(";")[0].strip().lower(),
            source["year"],
        )
        for source in SOURCES
    ]
    assert len(source_ids) == len(set(source_ids))
    assert len(keys) == len(set(keys))
    assert len(dois) == len(set(dois))
    assert len(title_author_year) == len(set(title_author_year))


if __name__ == "__main__":
    test_literature_no_duplicate_sources()
    print("test_literature_no_duplicate_sources.py passed")
