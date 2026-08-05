"""Literature confirmation-bias audit for R8.1."""

from __future__ import annotations

from r81_common import R81_DIR, build_literature_bias_rows, write_csv


def generate_literature_bias_audit() -> list[dict[str, object]]:
    rows = build_literature_bias_rows()
    write_csv(R81_DIR / "r81_literature_confirmation_bias_audit.csv", rows)
    return rows


if __name__ == "__main__":
    generated = generate_literature_bias_audit()
    print(f"Literature-bias rows: {len(generated)}")
