from pathlib import Path

from literature_stage_r7_analysis import OUTPUT_DIR, SOURCE_NOTES_DIR
from literature_stage_r7_data import SOURCES


REQUIRED_OUTPUTS = [
    "r7_literature_search_log.csv",
    "r7_source_screening_registry.csv",
    "r7_source_quality_registry.csv",
    "r7_finding_literature_comparison_matrix.csv",
    "r7_financial_analogy_crosswalk.csv",
    "r7_literature_contradiction_registry.csv",
    "r7_claim_support_audit.csv",
    "r7_reference_metadata_validation.csv",
    "r7_domain_coverage_summary.csv",
    "r7_r8_readiness_summary.csv",
    "r7_bibliography.bib",
    "r7_references_apa7.md",
    "r7_references_author_year.csv",
    "r7_pre_registration.md",
    "r7_search_methodology.md",
    "r7_screening_report.md",
    "r7_social_deduction_literature.md",
    "r7_asymmetric_information_literature.md",
    "r7_herding_and_trust_literature.md",
    "r7_deception_and_misinformation_literature.md",
    "r7_behavioral_finance_literature.md",
    "r7_bow_and_domain_shift_literature.md",
    "r7_offline_policy_failure_literature.md",
    "r7_multi_agent_validation_literature.md",
    "r7_risk_metrics_literature.md",
    "r7_financial_analogy_report.md",
    "r7_project_finding_comparison_report.md",
    "r7_theoretical_synthesis.md",
    "r7_research_report.md",
    "r7_limitations.md",
    "r7_manual_review_items.md",
    "literature_domain_coverage.svg",
    "project_finding_literature_relationships.svg",
    "source_quality_distribution.svg",
    "theoretical_framework_map.svg",
    "financial_analogy_crosswalk.svg",
    "literature_agreement_disagreement_map.svg",
]


def test_literature_documentation_outputs():
    missing = [name for name in REQUIRED_OUTPUTS if not (OUTPUT_DIR / name).exists()]
    assert not missing, missing
    notes = list(SOURCE_NOTES_DIR.glob("*.md"))
    assert len(notes) == len(SOURCES)
    report = (OUTPUT_DIR / "r7_research_report.md").read_text(encoding="utf-8")
    assert "R8 - Final Integrated Data Analysis and Evidence Tables" in report


if __name__ == "__main__":
    test_literature_documentation_outputs()
    print("test_literature_documentation_outputs.py passed")
