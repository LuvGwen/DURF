from r83_primary_contrast_recalculation import recompute_primary_contrasts
from r83_role_conclusion_freeze import build_final_replication_conclusions


final = {row["role"]: row for row in build_final_replication_conclusions(recompute_primary_contrasts())}
villager = final["Villager"]

assert villager["candidate_policy"] == "trust_weighted"
assert villager["primary_rule_met"] == "True"
assert villager["policy_evidence_grade"] == "A"
assert "vote_accuracy_diff" in villager["mechanism_metrics"]
