from r83_primary_contrast_recalculation import recompute_primary_contrasts
from r83_witch_risk_benefit import build_witch_risk_benefit


rows = {row["metric"]: row for row in build_witch_risk_benefit(recompute_primary_contrasts())}

assert rows["actor_payoff"]["favorable_or_unfavorable"] == "favorable"
assert rows["wrong_poison_rate"]["favorable_or_unfavorable"] == "unfavorable"
assert float(rows["wrong_poison_rate"]["difference"]) > 0
assert rows["primary_waste"]["reference"] == "unavailable_from_R8.2_export"
assert rows["extended_waste"]["difference"] == "unavailable_from_R8.2_export"
