"""Strategy-search registry for R8.1."""

from __future__ import annotations

from r81_common import R81_DIR, build_strategy_search_rows, write_csv


def generate_strategy_search_registry() -> list[dict[str, object]]:
    rows = build_strategy_search_rows()
    write_csv(R81_DIR / "r81_strategy_search_registry.csv", rows)
    return rows


if __name__ == "__main__":
    generated = generate_strategy_search_registry()
    print(f"Strategy-search rows: {len(generated)}")
