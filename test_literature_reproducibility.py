import hashlib
from pathlib import Path

from literature_stage_r7_analysis import OUTPUT_DIR, write_all_outputs


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_literature_reproducibility():
    write_all_outputs()
    target = OUTPUT_DIR / "r7_finding_literature_comparison_matrix.csv"
    first = digest(target)
    write_all_outputs()
    second = digest(target)
    assert first == second


if __name__ == "__main__":
    test_literature_reproducibility()
    print("test_literature_reproducibility.py passed")
