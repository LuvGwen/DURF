from r83_common import RESULTS_DIR, read_csv


required = [
    "r83_seer_statistical_consistency_audit.csv",
    "r83_primary_contrast_recalculation.csv",
    "r83_final_replication_conclusions.csv",
    "r83_witch_risk_benefit_summary.csv",
    "r83_seer_evidence_integration.csv",
    "r83_final_five_role_recommendations.csv",
    "r83_final_claim_registry.csv",
    "r83_validation_summary.csv",
    "r83_r9_readiness_summary.csv",
    "r83_pre_registration.md",
    "r83_statistical_consistency_method.md",
    "r83_inference_interpretation_standard.md",
    "r83_research_report.md",
    "r83_r9_readiness.md",
]

for file_name in required:
    assert (RESULTS_DIR / file_name).exists(), file_name

validation = read_csv(RESULTS_DIR / "r83_validation_summary.csv")
assert all(row["passed"] == "True" for row in validation), validation
