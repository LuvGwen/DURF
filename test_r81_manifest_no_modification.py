import csv
from pathlib import Path


BASE = Path("results/project_overfitting_audit_stage_r81")
rows = list(csv.DictReader((BASE / "r81_manifest_hash_forensic_audit.csv").open()))

for manifest_type in ["r4_payoff_manifest", "r5_metric_manifest"]:
    historical_rows = [
        row
        for row in rows
        if row["manifest_type"] == manifest_type
        and row["stage"] not in {"current_manifest_like_inventory"}
        and row["raw_file_sha256"] != "absent"
    ]
    assert historical_rows
    assert {row["changed_from_original"] for row in historical_rows} == {"False"}
