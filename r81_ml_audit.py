"""ML overfitting audit for R8.1."""

from __future__ import annotations

from r81_common import R81_DIR, build_ml_audit_rows, write_csv


def generate_ml_audit() -> list[dict[str, object]]:
    rows = build_ml_audit_rows()
    write_csv(R81_DIR / "r81_ml_overfitting_audit.csv", rows)
    return rows


if __name__ == "__main__":
    generated = generate_ml_audit()
    print(f"ML audit rows: {len(generated)}")
