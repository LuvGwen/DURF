"""Prepare the R9 input pack from R8 outputs."""

from __future__ import annotations

import shutil
from pathlib import Path

from r8_common import OUTPUT_DIR, R9_PACK_DIR, ROOT, write_text


R9_PACK_FILES = [
    "r8_research_report.md",
    "r8_statistical_synthesis_report.md",
    "r8_role_strategy_report.md",
    "r8_payoff_risk_report.md",
    "r8_speech_bow_ml_report.md",
    "r8_literature_integration_report.md",
    "r8_financial_analogy_report.md",
    "r8_proposal_completion_report.md",
    "r8_limitations.md",
    "r8_final_statistical_evidence_table.csv",
    "r8_final_role_strategy_table.csv",
    "r8_final_role_payoff_table.csv",
    "r8_speech_bow_final_table.csv",
    "r8_ml_final_table.csv",
    "r8_final_literature_integration_table.csv",
]


def build_r9_input_pack() -> list[dict[str, str]]:
    R9_PACK_DIR.mkdir(parents=True, exist_ok=True)
    manifest_rows = []
    for filename in R9_PACK_FILES:
        src = OUTPUT_DIR / filename
        dest = R9_PACK_DIR / filename
        if src.exists():
            shutil.copy2(src, dest)
            status = "included"
        else:
            status = "missing"
        manifest_rows.append(
            {
                "filename": filename,
                "source_path": str(src.relative_to(ROOT)),
                "r9_pack_path": str(dest.relative_to(ROOT)),
                "status": status,
            }
        )
    write_text(
        R9_PACK_DIR / "README.md",
        "# R9 Input Pack\n\n"
        "This directory contains the R8 final integrated analysis artifacts selected for R9 final report, presentation, "
        "and reproducibility packaging. It is generated from existing result files and does not include new gameplay "
        "simulation runs.\n",
    )
    return manifest_rows
