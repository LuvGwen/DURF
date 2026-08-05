"""Replication-priority and R9-readiness decisions for R8.1."""

from __future__ import annotations

from r81_common import (
    R81_DIR,
    build_r9_readiness_rows,
    build_replication_rows,
    read_csv,
    write_csv,
)


def generate_replication_decisions(corrected_rows: list[dict[str, object]] | None = None) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    if corrected_rows is None:
        corrected_rows = read_csv(R81_DIR / "r81_corrected_role_strategy_table.csv")
    replication_rows = build_replication_rows(corrected_rows)
    readiness_rows = build_r9_readiness_rows(corrected_rows)
    write_csv(R81_DIR / "r81_replication_priority_registry.csv", replication_rows)
    write_csv(R81_DIR / "r81_r9_readiness_summary.csv", readiness_rows)
    return replication_rows, readiness_rows


if __name__ == "__main__":
    replication, readiness = generate_replication_decisions()
    print(f"Replication rows: {len(replication)}")
    print(f"Readiness rows: {len(readiness)}")
