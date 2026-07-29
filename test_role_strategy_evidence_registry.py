"""Tests for R6 evidence registry definitions."""

from __future__ import annotations

import unittest
from pathlib import Path

from role_strategy_evidence_registry import (
    EVIDENCE_GRADES,
    SOURCE_EVIDENCE_FILES,
    get_evidence_grade_definitions,
)


class RoleStrategyEvidenceRegistryTest(unittest.TestCase):
    def test_all_required_grades_exist(self) -> None:
        self.assertEqual(set(EVIDENCE_GRADES), {"A", "B", "C", "D", "E", "F", "U"})

    def test_grade_rows_are_exportable(self) -> None:
        rows = get_evidence_grade_definitions()
        self.assertEqual(len(rows), 7)
        self.assertTrue(all(row["grade"] and row["definition"] for row in rows))

    def test_source_files_exist(self) -> None:
        missing = [path for path in SOURCE_EVIDENCE_FILES if not Path(path).exists()]
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
