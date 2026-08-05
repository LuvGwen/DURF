from r8_test_utils import digest


assert digest("results/payoff_matrix_stage_r4/r4_payoff_manifest.json")
assert digest("results/financial_risk_stage_r5/r5_metric_definition_manifest.json")
assert digest("results/metrics_integrity_stage_r62/recommended_research_configuration.json")
print("test_r8_reproducibility passed")
