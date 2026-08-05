import csv
import subprocess
from pathlib import Path


BASE = Path("results/project_overfitting_audit_stage_r81")
rows = list(csv.DictReader((BASE / "r81_manifest_hash_forensic_audit.csv").open()))

for manifest_type, path in [
    ("r4_payoff_manifest", "results/payoff_matrix_stage_r4/r4_payoff_manifest.json"),
    ("r5_metric_manifest", "results/financial_risk_stage_r5/r5_metric_definition_manifest.json"),
]:
    row = next(
        item
        for item in rows
        if item["manifest_type"] == manifest_type
        and item["repository_path"] == path
        and item["stage"] == "current_manifest_like_inventory"
    )
    shasum = subprocess.check_output(["shasum", "-a", "256", path], text=True).split()[0]
    assert row["raw_file_sha256"] == shasum
