"""Project-wide multiple-testing inventory for R8.1."""

from __future__ import annotations

from r81_common import R81_DIR, build_multiple_testing_rows, write_csv


def generate_multiple_testing_inventory() -> list[dict[str, object]]:
    rows = build_multiple_testing_rows()
    write_csv(R81_DIR / "r81_project_wide_multiple_testing_inventory.csv", rows)
    return rows


if __name__ == "__main__":
    generated = generate_multiple_testing_inventory()
    print(f"Multiple-testing rows: {len(generated)}")
