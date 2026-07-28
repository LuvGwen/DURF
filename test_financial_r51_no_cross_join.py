from financial_r51_analysis import build_mapping_audit, read_csv


def test_mapping_audit_preserves_r5_row_count_without_cross_join():
    rows = read_csv("results/financial_risk_stage_r5/r5_strategy_risk_return_summary.csv")
    audit = build_mapping_audit(rows)
    assert len(audit) == len(rows)
    assert sum(1 for row in audit if row["suspected_cross_join"]) == 0
    assert sum(1 for row in audit if row["suspected_label_propagation"]) == 32
