"""Threshold-search registry for R8.1."""

from __future__ import annotations

from r81_common import R81_DIR, build_threshold_rows, write_csv


def generate_threshold_registry() -> list[dict[str, object]]:
    rows = build_threshold_rows()
    write_csv(R81_DIR / "r81_threshold_search_registry.csv", rows)
    return rows


if __name__ == "__main__":
    generated = generate_threshold_registry()
    print(f"Threshold rows: {len(generated)}")
