"""Run the R6.2 Seer survival audit."""

from r62_analysis import (
    RESULTS_DIR,
    build_seer_life_history,
    seer_bootstrap,
    seer_hazard_summary,
    seer_survival_summary,
    write_csv,
)
from r62_seer_life_history import SEER_LIFE_HISTORY_FIELDS


def run_seer_survival_audit():
    rows = build_seer_life_history()
    summary = seer_survival_summary(rows)
    hazard = seer_hazard_summary(rows)
    bootstrap = seer_bootstrap(rows)
    write_csv(RESULTS_DIR / "r62_seer_life_history_raw.csv", rows, SEER_LIFE_HISTORY_FIELDS)
    write_csv(RESULTS_DIR / "r62_seer_survival_summary.csv", summary, list(summary[0]))
    write_csv(RESULTS_DIR / "r62_seer_post_reveal_hazard_summary.csv", hazard, list(hazard[0]))
    write_csv(
        RESULTS_DIR / "r62_seer_survival_bootstrap_ci.csv",
        bootstrap,
        list(bootstrap[0]),
    )
    return rows, summary, hazard


if __name__ == "__main__":
    histories, _, _ = run_seer_survival_audit()
    print(f"Seer life histories reconstructed: {len(histories)}")
