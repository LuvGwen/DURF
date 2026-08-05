import csv
from pathlib import Path


BASE = Path("results/project_overfitting_audit_stage_r81")
rows = list(csv.DictReader((BASE / "r81_manifest_hash_forensic_audit.csv").open()))

for manifest_type in ["r4_payoff_manifest", "r5_metric_manifest"]:
    row = next(item for item in rows if item["manifest_type"] == manifest_type and item["stage"] == "r81")
    assert row["canonical_content_sha256"] == row["expected_historical_hash"]
    assert row["final_authoritative_hash"] == row["expected_historical_hash"]
    assert row["raw_file_sha256"] != row["expected_historical_hash"]
