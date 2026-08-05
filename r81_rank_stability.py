"""Rank-stability summary for R8.1."""

from __future__ import annotations

from r81_common import R81_DIR, build_selection_stability_rows, read_csv, write_csv


def generate_rank_stability_summary(selection_rows: list[dict[str, object]] | None = None) -> list[dict[str, object]]:
    if selection_rows is None:
        selection_rows = read_csv(R81_DIR / "r81_policy_selection_frequency.csv")
    rows = build_selection_stability_rows(selection_rows)
    write_csv(R81_DIR / "r81_selection_stability_summary.csv", rows)
    return rows


if __name__ == "__main__":
    generated = generate_rank_stability_summary()
    print(f"Rank-stability rows: {len(generated)}")
