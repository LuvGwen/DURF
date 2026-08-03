from literature_stage_r7_data import SOURCES


def test_literature_no_fake_citations():
    forbidden_statuses = {"fabricated", "unknown", ""}
    assert not [source for source in SOURCES if source["metadata_status"] in forbidden_statuses]
    assert all(source["doi"] or source["url"] for source in SOURCES)
    assert all(source["authors"] and source["title"] and source["year"] for source in SOURCES)


if __name__ == "__main__":
    test_literature_no_fake_citations()
    print("test_literature_no_fake_citations.py passed")
