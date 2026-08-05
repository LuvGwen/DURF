from r83_primary_contrast_recalculation import recompute_primary_contrasts
from r83_seer_consistency_audit import build_seer_consistency_audit


corrected = recompute_primary_contrasts()
seer = next(row for row in corrected if row["module"] == "seer")
audit = build_seer_consistency_audit(corrected)
raw_issue = next(row for row in audit if row["statistic"] == "raw_sign_flip_p_value")
holm_issue = next(row for row in audit if row["statistic"] == "Holm_adjusted_p_value")

assert seer["bootstrap_ci_low"] > 0
assert seer["Holm_adjusted_p_value"] <= 0.05
assert raw_issue["issue_detected"] == "True"
assert holm_issue["issue_detected"] == "True"
assert "denominator" in raw_issue["explanation"]
