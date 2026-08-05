from pathlib import Path


root = Path(__file__).resolve().parent
witch = (root / "results" / "replication_consistency_stage_r83" / "r83_witch_risk_benefit_summary.csv").read_text(encoding="utf-8")
seer = (root / "results" / "replication_consistency_stage_r83" / "r83_seer_evidence_integration.csv").read_text(encoding="utf-8")

assert "primary_waste,unavailable_from_R8.2_export" in witch
assert "extended_waste,unavailable_from_R8.2_export" in witch
assert "next_night_hazard" in seer
assert "do not pool" in seer.lower()
