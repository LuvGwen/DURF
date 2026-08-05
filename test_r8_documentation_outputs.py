from r8_test_utils import assert_exists, read_rows


required_reports = [
    "r8_pre_registration.md",
    "r8_schema.md",
    "r8_data_integration_method.md",
    "r8_sample_unit_audit.md",
    "r8_statistical_synthesis_report.md",
    "r8_role_strategy_report.md",
    "r8_payoff_risk_report.md",
    "r8_speech_bow_ml_report.md",
    "r8_validity_report.md",
    "r8_literature_integration_report.md",
    "r8_financial_analogy_report.md",
    "r8_proposal_completion_report.md",
    "r8_limitations.md",
    "r8_overclaiming_audit.md",
    "r8_research_report.md",
    "r8_r9_readiness.md",
]

for report in required_reports:
    assert_exists(f"results/final_integrated_analysis_stage_r8/{report}")
assert len(read_rows("r8_final_table_registry.csv")) == 24
assert len(read_rows("r8_final_figure_registry.csv")) == 18
print("test_r8_documentation_outputs passed")
