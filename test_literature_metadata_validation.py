from literature_metadata_validator import validate_sources


def test_literature_metadata_validation():
    rows = validate_sources()
    failed = [row for row in rows if row["status"] != "PASS"]
    assert not failed, failed[:5]


if __name__ == "__main__":
    test_literature_metadata_validation()
    print("test_literature_metadata_validation.py passed")
