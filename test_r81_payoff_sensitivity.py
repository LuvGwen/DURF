from r81_test_utils import read_rows


scenarios = read_rows("r81_payoff_sensitivity_scenarios.csv")
results = read_rows("r81_payoff_sensitivity_results.csv")
ranks = read_rows("r81_policy_rank_under_payoff_variants.csv")
assert len(scenarios) >= 13
assert len(results) == len(scenarios) * 30
assert len(ranks) == len(scenarios) * 30
assert any(row["scenario_name"] == "witch_wrong_poison_harsher" for row in scenarios)
