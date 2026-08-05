"""Outcome-switching registry for R8.1."""

from __future__ import annotations

from r81_common import R81_DIR, build_outcome_switching_rows, write_csv


def generate_outcome_switching_registry() -> list[dict[str, object]]:
    rows = build_outcome_switching_rows()
    write_csv(R81_DIR / "r81_outcome_switching_registry.csv", rows)
    return rows


if __name__ == "__main__":
    generated = generate_outcome_switching_registry()
    print(f"Outcome-switching rows: {len(generated)}")
