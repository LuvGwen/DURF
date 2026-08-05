"""BoW overfitting audit for R8.1."""

from __future__ import annotations

from r81_common import R81_DIR, build_bow_audit_rows, write_csv


def generate_bow_audit() -> list[dict[str, object]]:
    rows = build_bow_audit_rows()
    write_csv(R81_DIR / "r81_bow_overfitting_audit.csv", rows)
    return rows


if __name__ == "__main__":
    generated = generate_bow_audit()
    print(f"BoW audit rows: {len(generated)}")
