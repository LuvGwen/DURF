"""Validate the explicit R6.2 recommended research configuration."""

from r62_analysis import RESULTS_DIR, run_configuration_validation, write_csv


def run_r62_configuration_validation():
    rows, summary = run_configuration_validation()
    write_csv(
        RESULTS_DIR / "r62_configuration_validation_raw.csv",
        rows,
        list(rows[0]),
    )
    write_csv(
        RESULTS_DIR / "r62_configuration_validation_summary.csv",
        summary,
        list(summary[0]),
    )
    return rows, summary


if __name__ == "__main__":
    _, summary_rows = run_r62_configuration_validation()
    for row in summary_rows:
        print(row)
