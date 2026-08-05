"""Final-seed reuse audit for R8.1."""

from __future__ import annotations

from r81_common import R81_DIR, build_final_seed_reuse_rows, write_csv


def generate_final_seed_reuse_audit() -> list[dict[str, object]]:
    rows = build_final_seed_reuse_rows()
    write_csv(R81_DIR / "r81_final_seed_reuse_audit.csv", rows)
    return rows


if __name__ == "__main__":
    generated = generate_final_seed_reuse_audit()
    print(f"Final-seed rows: {len(generated)}")
