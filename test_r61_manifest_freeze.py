import json
from pathlib import Path

from r61_common_experiment import R4_MANIFEST_HASH, R5_METRIC_MANIFEST_HASH


def main():
    r4 = json.loads(Path("results/payoff_matrix_stage_r4/r4_payoff_manifest.json").read_text())
    r5 = json.loads(Path("results/financial_risk_stage_r5/r5_metric_definition_manifest.json").read_text())
    assert r4["manifest_hash"] == R4_MANIFEST_HASH
    assert r5["metric_manifest_hash"] == R5_METRIC_MANIFEST_HASH
    assert r5["r4_manifest_hash"] == R4_MANIFEST_HASH
    print("test_r61_manifest_freeze.py passed")


if __name__ == "__main__":
    main()
