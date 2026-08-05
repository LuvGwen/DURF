"""Small helpers for R8.1 tests."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
R81_DIR = ROOT / "results" / "project_overfitting_audit_stage_r81"


def read_rows(name: str) -> list[dict[str, str]]:
    path = R81_DIR / name
    assert path.exists(), f"missing {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_text(name: str) -> str:
    path = R81_DIR / name
    assert path.exists(), f"missing {path}"
    return path.read_text(encoding="utf-8")
