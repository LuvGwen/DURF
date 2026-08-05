"""Decision-history registry for R8.1."""

from __future__ import annotations

from r81_common import R81_DIR, build_decision_history_rows, write_csv


def generate_decision_history() -> list[dict[str, object]]:
    rows = build_decision_history_rows()
    write_csv(R81_DIR / "r81_experimental_decision_history.csv", rows)
    return rows


if __name__ == "__main__":
    generated = generate_decision_history()
    print(f"Decision-history rows: {len(generated)}")
