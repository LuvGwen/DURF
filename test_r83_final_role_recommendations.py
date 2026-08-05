from r83_common import RESULTS_DIR, read_csv


rows = read_csv(RESULTS_DIR / "r83_final_five_role_recommendations.csv")
by_role = {row["role"]: row for row in rows}

assert set(by_role) == {"Villager", "Seer", "Witch", "Hunter", "Werewolf"}
assert by_role["Villager"]["performance_maximizing_policy"] == "trust_weighted"
assert by_role["Seer"]["conservative_default"] == "private_only"
assert by_role["Witch"]["conditional_policy"] == "aggressive_full for risk-tolerant policy use"
assert by_role["Hunter"]["conservative_default"] == "reference"
assert "reference" in by_role["Werewolf"]["performance_maximizing_policy"]
