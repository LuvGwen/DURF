from r81_test_utils import read_rows


coverage = read_rows("r81_regime_coverage_audit.csv")
risks = read_rows("r81_distribution_shift_risk_registry.csv")
assert any(row["distribution_axis"] == "behavioral_regime" for row in coverage)
assert any(row["severity"] == "high" for row in risks)
