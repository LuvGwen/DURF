import csv
from pathlib import Path


BASE = Path("results/project_overfitting_audit_stage_r81")
rows = list(csv.DictReader((BASE / "r81_manifest_hash_forensic_audit.csv").open()))
paths = {row["repository_path"] for row in rows}

assert "results/payoff_matrix_stage_r4/r4_payoff_manifest.json" in paths
assert "results/financial_risk_stage_r5/r5_metric_definition_manifest.json" in paths
assert any(row["manifest_type"] == "r4_payoff_manifest" for row in rows)
assert any(row["manifest_type"] == "r5_metric_manifest" for row in rows)
