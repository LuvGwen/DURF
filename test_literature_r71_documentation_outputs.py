from pathlib import Path

from literature_stage_r71_analysis import OUTPUT_DIR


REQUIRED_OUTPUTS = [
    "r71_doi_validation_registry.csv",
    "r71_recency_audit.csv",
    "r71_foundational_exception_registry.csv",
    "r71_replacement_source_registry.csv",
    "r71_revised_finding_literature_matrix.csv",
    "r71_final_bibliography.bib",
    "r71_final_references_apa7.md",
    "r71_final_references_author_year.csv",
    "r71_excluded_no_doi_sources.csv",
    "r71_revised_claim_support_audit.csv",
    "r71_domain_recency_coverage.csv",
    "r71_manual_review_items.md",
    "r71_pre_registration.md",
    "r71_doi_verification_method.md",
    "r71_recency_review_method.md",
    "r71_source_replacement_report.md",
    "r71_foundational_exception_report.md",
    "r71_finding_coverage_report.md",
    "r71_final_bibliography_validation.md",
    "r71_research_report.md",
    "r71_limitations.md",
    "r71_r8_readiness.md",
]


def test_literature_r71_documentation_outputs():
    missing = [name for name in REQUIRED_OUTPUTS if not (OUTPUT_DIR / name).exists()]
    assert not missing, missing
    progress_dir = Path("results/research_progress")
    assert "R7.1 DOI-Verified" in (progress_dir / "cumulative_research_report.md").read_text(encoding="utf-8")
    assert "DOI-only" in (progress_dir / "current_progress_assessment.md").read_text(encoding="utf-8")
    assert "C_R71_01" in (progress_dir / "source_traceability_index.csv").read_text(encoding="utf-8")


if __name__ == "__main__":
    test_literature_r71_documentation_outputs()
    print("test_literature_r71_documentation_outputs.py passed")
