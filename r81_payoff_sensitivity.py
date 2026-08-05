"""Payoff-sensitivity audit for R8.1."""

from __future__ import annotations

from r81_common import R81_DIR, build_payoff_scenarios, build_payoff_sensitivity_results, write_csv


def generate_payoff_sensitivity() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    scenarios = build_payoff_scenarios()
    results, rank_rows = build_payoff_sensitivity_results()
    write_csv(R81_DIR / "r81_payoff_sensitivity_scenarios.csv", scenarios)
    write_csv(R81_DIR / "r81_payoff_sensitivity_results.csv", results)
    write_csv(R81_DIR / "r81_policy_rank_under_payoff_variants.csv", rank_rows)
    return scenarios, results, rank_rows


if __name__ == "__main__":
    scenarios, results, ranks = generate_payoff_sensitivity()
    print(f"Payoff scenarios: {len(scenarios)}")
    print(f"Payoff sensitivity rows: {len(results)}")
    print(f"Payoff rank rows: {len(ranks)}")
