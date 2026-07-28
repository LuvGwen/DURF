import json
from pathlib import Path

from financial_metric_manifest import R4_MANIFEST_HASH, build_metric_manifest


def main():
    path = Path("results/payoff_matrix_stage_r4/r4_payoff_manifest.json")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert manifest["manifest_hash"] == R4_MANIFEST_HASH
    r5_manifest = build_metric_manifest()
    assert r5_manifest["r4_manifest_hash"] == R4_MANIFEST_HASH
    assert r5_manifest["metric_manifest_hash"]
    print("test_financial_manifest_freeze.py passed")


if __name__ == "__main__":
    main()
