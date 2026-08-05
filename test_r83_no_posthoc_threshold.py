from pathlib import Path


root = Path(__file__).resolve().parent
pre = root / "results" / "replication_consistency_stage_r83" / "r83_pre_registration.md"
validation = root / "results" / "replication_consistency_stage_r83" / "r83_validation_summary.csv"

assert pre.exists()
assert validation.exists()
assert "No threshold tuning" in pre.read_text(encoding="utf-8")
assert "no_posthoc_practical_threshold" in validation.read_text(encoding="utf-8")
