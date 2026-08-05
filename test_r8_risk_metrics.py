from r8_test_utils import read_rows


rows = read_rows("r8_final_role_payoff_table.csv")
hunter = next(row for row in rows if row["role"] == "hunter")

assert float(hunter["cvar95_loss"]) > 2.0
assert all(row["sharpe_like_ratio"] != "not_reported" for row in rows)
assert all(row["sortino_like_ratio"] != "not_reported" for row in rows)
print("test_r8_risk_metrics passed")
