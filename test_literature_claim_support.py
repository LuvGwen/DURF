from literature_claim_audit import claim_support_rows


ALLOWED = {
    "fully_supported",
    "partially_supported",
    "project_only",
    "literature_only",
    "unsupported",
    "requires_qualification",
}


def test_literature_claim_support():
    rows = claim_support_rows()
    assert rows
    assert all(row["support_status"] in ALLOWED for row in rows)
    assert all(row["literature_source"] for row in rows)
    assert all(row["final_safe_wording"] for row in rows)
    assert not any(
        row["support_status"] == "unsupported" and row["overclaim_risk"] == "low"
        for row in rows
    )


if __name__ == "__main__":
    test_literature_claim_support()
    print("test_literature_claim_support.py passed")
