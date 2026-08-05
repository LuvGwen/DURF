from pathlib import Path

from r81_test_utils import R81_DIR, read_rows


required_reports = [
    "r81_pre_registration.md",
    "r81_audit_methodology.md",
    "r81_research_report.md",
    "r81_r9_readiness.md",
    "r81_corrected_conclusions.md",
]
for report in required_reports:
    assert (R81_DIR / report).exists(), report
assert (R81_DIR / "corrected_r8" / "corrected_role_strategy_table.csv").exists()
assert (R81_DIR / "corrected_r8" / "r9_input_pack" / "README.md").exists()
validation = read_rows("r81_validation_summary.csv")
assert len(validation) >= 60
