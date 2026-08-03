"""Run the R6.2 Witch potion lifecycle audit."""

from r62_analysis import (
    RESULTS_DIR,
    build_witch_lifecycle,
    witch_bootstrap,
    witch_summary,
    write_csv,
)
from r62_witch_payoff_reconciliation import (
    WITCH_RECONCILIATION_FIELDS,
    reconciliation_rows,
)
from r62_witch_potion_lifecycle import WITCH_LIFECYCLE_FIELDS


def run_witch_potion_audit():
    rows = build_witch_lifecycle()
    summary = witch_summary(rows)
    reconciliation = reconciliation_rows(rows)
    bootstrap = witch_bootstrap(rows)
    write_csv(RESULTS_DIR / "r62_witch_potion_lifecycle_raw.csv", rows, WITCH_LIFECYCLE_FIELDS)
    write_csv(RESULTS_DIR / "r62_witch_potion_waste_summary.csv", summary, list(summary[0]))
    write_csv(
        RESULTS_DIR / "r62_witch_payoff_reconciliation.csv",
        reconciliation,
        WITCH_RECONCILIATION_FIELDS,
    )
    write_csv(
        RESULTS_DIR / "r62_witch_potion_bootstrap_ci.csv",
        bootstrap,
        list(bootstrap[0]),
    )
    return rows, summary, reconciliation


if __name__ == "__main__":
    lifecycles, _, _ = run_witch_potion_audit()
    print(f"Witch potion lifecycles reconstructed: {len(lifecycles)}")
