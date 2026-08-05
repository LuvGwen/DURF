"""Matched-set post-selection bootstrap for R8.1."""

from __future__ import annotations

from r81_common import R81_DIR, build_bootstrap_outputs, write_csv


def generate_post_selection_bootstrap(replicates: int = 5000) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    rank_rows, frequency_rows, curse_rows = build_bootstrap_outputs(replicates=replicates)
    write_csv(R81_DIR / "r81_policy_rank_bootstrap.csv", rank_rows)
    write_csv(R81_DIR / "r81_policy_selection_frequency.csv", frequency_rows)
    write_csv(R81_DIR / "r81_winners_curse_estimates.csv", curse_rows)
    return rank_rows, frequency_rows, curse_rows


if __name__ == "__main__":
    ranks, frequencies, curses = generate_post_selection_bootstrap()
    print(f"Bootstrap rank rows: {len(ranks)}")
    print(f"Selection-frequency rows: {len(frequencies)}")
    print(f"Winners-curse rows: {len(curses)}")
