from r83_primary_contrast_recalculation import recompute_primary_contrasts
from r83_role_conclusion_freeze import (
    build_final_replication_conclusions,
    build_five_role_recommendations,
)


corrected = recompute_primary_contrasts()
final = {row["role"]: row for row in build_final_replication_conclusions(corrected)}
five = {row["role"]: row for row in build_five_role_recommendations()}

assert final["Seer"]["final_evidence_label"] == "replicated_positive_with_material_tradeoff"
assert final["Seer"]["primary_rule_met"] == "True"
assert "next-night hazard" in final["Seer"]["unavailable_metrics"]
assert five["Seer"]["conservative_default"] == "private_only"
assert "exposure-constrained" in five["Seer"]["final_safe_wording"]
