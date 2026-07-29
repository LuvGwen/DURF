"""Tests for R6 source traceability."""

from __future__ import annotations

import unittest
from pathlib import Path

from role_strategy_synthesis import build_decision_matrix, build_source_index, load_evidence


class RoleStrategySourceTraceabilityTest(unittest.TestCase):
    def test_source_index_paths_exist(self) -> None:
        missing = [row["source_path"] for row in build_source_index() if row["status"] != "verified_from_source"]
        self.assertEqual(missing, [])

    def test_each_matrix_source_path_exists(self) -> None:
        matrix = build_decision_matrix(load_evidence())
        missing = []
        for row in matrix:
            for item in str(row["source_report"]).split(";"):
                path = item.strip()
                if path and path != "not reported" and not Path(path).exists():
                    missing.append(path)
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
