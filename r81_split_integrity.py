"""Split-integrity registry for R8.1."""

from __future__ import annotations

from r81_common import R81_DIR, build_split_integrity_rows, write_csv


def generate_split_integrity_registry() -> list[dict[str, object]]:
    rows = build_split_integrity_rows()
    write_csv(R81_DIR / "r81_split_integrity_registry.csv", rows)
    return rows


if __name__ == "__main__":
    generated = generate_split_integrity_registry()
    print(f"Split-integrity rows: {len(generated)}")
