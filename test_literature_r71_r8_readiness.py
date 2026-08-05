from literature_stage_r71_analysis import OUTPUT_DIR


def test_literature_r71_r8_readiness():
    readiness = (OUTPUT_DIR / "r71_r8_readiness.md").read_text(encoding="utf-8")
    validation = (OUTPUT_DIR / "r71_final_bibliography_validation.md").read_text(encoding="utf-8")
    manual = (OUTPUT_DIR / "r71_manual_review_items.md").read_text(encoding="utf-8")
    assert "Status: READY FOR R8" in readiness
    assert "Validation status: PASS" in validation
    assert "No unresolved manual review items" in manual


if __name__ == "__main__":
    test_literature_r71_r8_readiness()
    print("test_literature_r71_r8_readiness.py passed")
