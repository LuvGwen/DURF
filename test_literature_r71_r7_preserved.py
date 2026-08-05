from literature_stage_r7_analysis import OUTPUT_DIR as R7_OUTPUT_DIR, SOURCE_NOTES_DIR
from literature_stage_r7_data import SOURCES
from literature_stage_r71_analysis import OUTPUT_DIR as R71_OUTPUT_DIR


def test_literature_r71_r7_preserved():
    assert (R7_OUTPUT_DIR / "r7_research_report.md").exists()
    assert (R7_OUTPUT_DIR / "r7_bibliography.bib").exists()
    assert len(list(SOURCE_NOTES_DIR.glob("*.md"))) == len(SOURCES)
    assert R71_OUTPUT_DIR != R7_OUTPUT_DIR


if __name__ == "__main__":
    test_literature_r71_r7_preserved()
    print("test_literature_r71_r7_preserved.py passed")
