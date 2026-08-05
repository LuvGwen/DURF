from r8_test_utils import read_rows


rows = read_rows("r8_final_role_strategy_table.csv")
roles = {row["role"] for row in rows}

assert roles == {"Hunter", "Seer", "Witch", "Werewolf", "Villager"}
assert any(row["role"] == "Villager" and row["strongest_tested_policy"] == "trust_weighted" for row in rows)
assert all(row["gap_closed"] == "yes" for row in rows)
print("test_r8_role_strategy_table passed")
