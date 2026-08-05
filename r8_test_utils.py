"""Shared test helpers for R8 output validation."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent
R8_DIR = ROOT / "results" / "final_integrated_analysis_stage_r8"


def read_rows(name: str) -> list[dict[str, str]]:
    path = R8_DIR / name
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def assert_exists(path: str) -> Path:
    actual = ROOT / path
    assert actual.exists(), f"Missing expected path: {path}"
    return actual


def digest(path: str) -> str:
    actual = ROOT / path
    return hashlib.sha256(actual.read_bytes()).hexdigest()
