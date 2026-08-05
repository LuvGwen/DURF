from r8_test_utils import read_rows


rows = read_rows("r8_final_role_payoff_table.csv")
werewolf = next(row for row in rows if row["role"] == "werewolf")

assert len(rows) == 5
assert float(werewolf["mean_payoff"]) > 0
assert werewolf["rank_mean_payoff"] == "1"
assert all(row["mean_payoff_bootstrap_ci"].startswith("[") for row in rows)
print("test_r8_payoff_metrics passed")
