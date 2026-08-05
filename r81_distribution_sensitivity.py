"""Distribution-sensitivity audit for R8.1."""

from __future__ import annotations

from r81_common import R81_DIR, build_distribution_rows, write_csv


def generate_distribution_sensitivity() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    coverage, risks = build_distribution_rows()
    write_csv(R81_DIR / "r81_regime_coverage_audit.csv", coverage)
    write_csv(R81_DIR / "r81_distribution_shift_risk_registry.csv", risks)
    return coverage, risks


if __name__ == "__main__":
    coverage_rows, risk_rows = generate_distribution_sensitivity()
    print(f"Coverage rows: {len(coverage_rows)}")
    print(f"Distribution-risk rows: {len(risk_rows)}")
