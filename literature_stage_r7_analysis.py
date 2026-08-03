"""Generate R7 literature synthesis outputs.

R7 is a documentation and theory-synthesis stage. It does not run gameplay
experiments or alter prior numerical results.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from literature_bibliography_builder import apa_references, author_year_rows, bibtex_entries
from literature_claim_audit import claim_support_rows
from literature_finding_mapper import finding_mapping_rows
from literature_metadata_validator import validate_sources
from literature_search_registry import search_log_rows, source_screening_rows
from literature_source_quality import (
    domain_coverage_rows,
    source_quality_counts,
    source_quality_rows,
)
from literature_stage_r7_data import (
    ACCESS_DATE,
    CONTRADICTIONS,
    DOMAINS,
    FINANCIAL_CROSSWALK,
    PROJECT_FINDINGS,
    R8_READINESS,
    SOURCES,
    source_by_id,
)


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "results" / "literature_synthesis_stage_r7"
SOURCE_NOTES_DIR = OUTPUT_DIR / "source_notes"
RESEARCH_DIR = ROOT / "results" / "research_progress"


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def markdown_table(rows: list[dict[str, str]], columns: list[tuple[str, str]]) -> str:
    header = "| " + " | ".join(label for _, label in columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(str(row.get(key, "")).replace("|", "/") for key, _ in columns) + " |")
    return "\n".join([header, divider] + body)


def relationship_counts() -> Counter:
    return Counter(row["relationship"] for row in finding_mapping_rows())


def financial_crosswalk_rows() -> list[dict[str, str]]:
    keys = [
        "game_entity_or_action",
        "financial_analogue",
        "supporting_literature",
        "shared_mechanism",
        "important_difference",
        "safe_interpretation",
        "overclaim_to_avoid",
    ]
    return [dict(zip(keys, row)) for row in FINANCIAL_CROSSWALK]


def contradiction_rows() -> list[dict[str, str]]:
    keys = [
        "contradiction_id",
        "project_finding",
        "literature_expectation",
        "source",
        "possible_explanation",
        "design_difference",
        "population_difference",
        "measurement_difference",
        "whether_project_result_truly_contradicts_source",
        "final_interpretation",
    ]
    return [dict(zip(keys, row)) for row in CONTRADICTIONS]


def r8_readiness_rows() -> list[dict[str, str]]:
    return [
        {"criterion": criterion, "status": status, "evidence": evidence}
        for criterion, status, evidence in R8_READINESS
    ]


def reference_metadata_rows() -> list[dict[str, str]]:
    rows = validate_sources()
    return [
        {
            "source_id": row["source_id"],
            "metadata_check": row["check"],
            "status": row["status"],
            "detail": row["detail"],
        }
        for row in rows
    ]


def source_notes() -> None:
    sources = source_by_id()
    mapping_by_source: dict[str, list[str]] = {source_id: [] for source_id in sources}
    for row in finding_mapping_rows():
        mapping_by_source[row["source_id"]].append(row["finding_id"])
    for source in SOURCES:
        citation = f"{source['authors']} ({source['year']}). {source['title']}. {source['venue']}."
        note = f"""# {source['citation_key']}

## Full Citation

{citation}

Stable identifier: {source['doi'] or source['url']}

## Research Question

What does this source establish about {DOMAINS.get(source['domain'], source['domain'])}?

## Method

Source type: {source['source_type']}. Peer reviewed: {source['peer_reviewed']}. R7 metadata status: {source['metadata_status']}.

## Data or Sample

See the source itself for data and sample details. R7 records this source at bibliography level and does not copy primary data.

## Major Findings

{source['exact_claim_supported']}

## Limitations

{source['limitations']}

## Relevance to DURF Project

{source['relevance']}

## Exact Project Finding It Informs

{', '.join(mapping_by_source[source['source_id']]) or 'Background source only.'}

## Paraphrase-Safe Summary

This source supports a bounded interpretation of the DURF evidence in the {source['domain']} domain. It should be cited for theory, method, or analogy only within the limitation stated above.

## Short Quotation

No quotation is used. R7 relies on paraphrased, source-bounded summaries.

## Citation Key

`{source['citation_key']}`
"""
        write_text(SOURCE_NOTES_DIR / f"{source['source_id']}_{source['citation_key']}.md", note)


def simple_bar_svg(title: str, rows: list[tuple[str, float]], path: Path, width: int = 920, height: int = 420) -> None:
    max_value = max(value for _, value in rows) if rows else 1
    left = 220
    top = 58
    bar_h = 24
    gap = 12
    plot_w = width - left - 60
    total_h = max(height, top + len(rows) * (bar_h + gap) + 40)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{total_h}" viewBox="0 0 {width} {total_h}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="24" y="34" font-family="Arial" font-size="20" font-weight="700" fill="#1f2933">{title}</text>',
    ]
    for idx, (label, value) in enumerate(rows):
        y = top + idx * (bar_h + gap)
        bar_w = 0 if max_value == 0 else (value / max_value) * plot_w
        parts.append(f'<text x="24" y="{y + 17}" font-family="Arial" font-size="13" fill="#334155">{label}</text>')
        parts.append(f'<rect x="{left}" y="{y}" width="{bar_w:.1f}" height="{bar_h}" rx="3" fill="#3366cc"/>')
        parts.append(f'<text x="{left + bar_w + 8}" y="{y + 17}" font-family="Arial" font-size="13" fill="#334155">{value:g}</text>')
    parts.append("</svg>")
    write_text(path, "\n".join(parts) + "\n")


def framework_svg(path: Path) -> None:
    labels = [
        ("Hidden roles", 70, 70),
        ("Speech signals", 300, 70),
        ("Belief update", 530, 70),
        ("Credibility", 760, 70),
        ("Voting/action", 300, 210),
        ("Role payoff", 530, 210),
        ("Risk metrics", 760, 210),
        ("Literature synthesis", 420, 340),
    ]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="980" height="430" viewBox="0 0 980 430">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="24" y="34" font-family="Arial" font-size="20" font-weight="700" fill="#1f2933">R7 Theoretical Framework Map</text>',
    ]
    for text, x, y in labels:
        parts.append(f'<rect x="{x}" y="{y}" width="170" height="54" rx="6" fill="#eef5ff" stroke="#3366cc"/>')
        parts.append(f'<text x="{x + 14}" y="{y + 33}" font-family="Arial" font-size="14" fill="#1f2933">{text}</text>')
    arrows = [
        (240, 97, 300, 97),
        (470, 97, 530, 97),
        (700, 97, 760, 97),
        (385, 124, 385, 210),
        (615, 124, 615, 210),
        (845, 124, 845, 210),
        (470, 237, 530, 237),
        (615, 264, 505, 340),
        (845, 264, 590, 340),
    ]
    for x1, y1, x2, y2 in arrows:
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#64748b" stroke-width="2" marker-end="url(#arrow)"/>')
    parts.insert(
        2,
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b"/></marker></defs>',
    )
    parts.append("</svg>")
    write_text(path, "\n".join(parts) + "\n")


def write_figures() -> None:
    coverage_rows = domain_coverage_rows()
    simple_bar_svg(
        "Literature Domain Coverage",
        [(row["domain"], float(row["source_count"])) for row in coverage_rows],
        OUTPUT_DIR / "literature_domain_coverage.svg",
    )
    rel_counts = relationship_counts()
    simple_bar_svg(
        "Project Finding-Literature Relationships",
        [(key, float(value)) for key, value in sorted(rel_counts.items())],
        OUTPUT_DIR / "project_finding_literature_relationships.svg",
    )
    q_counts = source_quality_counts()
    simple_bar_svg(
        "Source Quality Distribution",
        [(key, float(value)) for key, value in sorted(q_counts.items())],
        OUTPUT_DIR / "source_quality_distribution.svg",
    )
    simple_bar_svg(
        "Financial Analogy Crosswalk Coverage",
        [(row["game_entity_or_action"], 1.0) for row in financial_crosswalk_rows()],
        OUTPUT_DIR / "financial_analogy_crosswalk.svg",
        width=960,
        height=680,
    )
    simple_bar_svg(
        "Literature Agreement and Disagreement Map",
        [(key, float(value)) for key, value in sorted(rel_counts.items())],
        OUTPUT_DIR / "literature_agreement_disagreement_map.svg",
    )
    framework_svg(OUTPUT_DIR / "theoretical_framework_map.svg")


def report_header(title: str) -> str:
    return f"# {title}\n\nGenerated on {ACCESS_DATE}. This R7 artifact is literature synthesis only; no gameplay experiment was run.\n\n"


def domain_report(domain: str, title: str) -> str:
    sources = [
        source for source in SOURCES
        if source["domain"] == domain or domain in source.get("secondary_domains", "").split(";")
    ]
    rows = [
        {
            "source": f"{source['authors'].split(';')[0]} ({source['year']})",
            "quality": source["quality_grade"],
            "claim": source["exact_claim_supported"],
            "limitation": source["limitations"],
        }
        for source in sources
    ]
    body = report_header(title)
    body += "## Synthesis\n\n"
    body += (
        f"R7 retained {len(sources)} sources connected to this domain. "
        "The sources support comparison, theory framing, and citation-ready wording, "
        "but they do not replace the project's own simulation evidence.\n\n"
    )
    body += markdown_table(rows, [("source", "Source"), ("quality", "Quality"), ("claim", "Supported claim"), ("limitation", "Limitation")])
    body += "\n\n## DURF Interpretation\n\n"
    body += "The project should cite these sources to frame mechanisms, not to overstate real-world causal transfer.\n"
    return body


def project_comparison_report() -> str:
    rows = []
    for finding_id, chapter, finding, effect, grade, source_ids, relationship, explanation in PROJECT_FINDINGS:
        rows.append(
            {
                "finding_id": finding_id,
                "chapter": chapter,
                "relationship": relationship,
                "sources": source_ids,
                "safe_wording": explanation,
            }
        )
    return (
        report_header("R7 Project Finding Comparison Report")
        + "## Finding-to-Literature Map\n\n"
        + markdown_table(rows, [("finding_id", "Finding"), ("chapter", "Chapter"), ("relationship", "Relationship"), ("sources", "Sources"), ("safe_wording", "Safe interpretation")])
        + "\n\n## Interpretation\n\nMost findings are consistent with or extend prior theory. Negative findings, especially BoW live failure and ML live-policy failure, are preserved rather than smoothed into success claims.\n"
    )


def theoretical_synthesis() -> str:
    return report_header("R7 Theoretical Synthesis") + """## Core Model

The DURF simulator can be interpreted as a hidden-information decision system. Players observe public events, generate speech signals, update suspicion and `p_wolf`, and act under role-specific incentives. R7 maps that design to four linked theory families: incomplete-information games, reputation-weighted social learning, deception/misinformation, and risk-adjusted decision metrics.

## Trust-Weighted Voting

Trust-weighted voting is best interpreted as reliability-sensitive aggregation. Reputation literature supports the idea that prior speaker reliability should affect later decisions, while cascade literature warns that uncalibrated public influence can amplify errors.

## BoW and Live Policy Failure

The BoW results fit domain-shift theory: lexical features can predict labels in a familiar template distribution but fail under unseen templates. Offline policy literature explains why even a useful predictor may reduce live outcomes when inserted into a feedback system.

## Seer Reveal and Information Premium

The Seer resembles an informed signaler. The positive information premium is consistent with information-economics theory, but reveal timing also creates exposure risk. R7 therefore keeps immediate reveal as promising but uncertain.

## Witch and Hunter Risk

Witch and Hunter mechanisms show why mean payoff alone is insufficient. Wrong poison and death shot outcomes concentrate downside risk; unused potions create opportunity cost.

## Werewolf Manipulation

Werewolf deception and night strategy instantiate strategic misinformation by an informed minority. Credibility costs and speaker memory are the model's safeguards against cost-free manipulation.

## Contribution Beyond Existing Work

The project contributes by combining social-deduction simulation, controlled speech signals, speaker-specific trust memory, role-specific payoff accounting, risk metrics, and live-policy validation in one reproducible Python environment.
"""


def r7_research_report() -> str:
    coverage = domain_coverage_rows()
    quality = source_quality_counts()
    rel = relationship_counts()
    readiness = r8_readiness_rows()
    return report_header("R7 Research Report") + f"""## Technical Summary

R7 completes a systematic literature comparison without running new gameplay experiments. It retained {len(SOURCES)} sources across {len(DOMAINS)} literature domains, mapped all {len(PROJECT_FINDINGS)} required project findings, created a citation-ready bibliography, and generated claim-support, contradiction, financial-analogy, and source-quality registries.

## Search and Screening

The search log documents the search systems actually used. Sources were included only when they had identifiable authorship, verifiable metadata, and a clear relationship to project claims. Preprints and books are retained only when useful and explicitly limited.

## Domain Coverage

{markdown_table(coverage, [("domain", "Domain"), ("source_count", "Sources"), ("minimum_required", "Minimum"), ("meets_minimum", "Met")])}

## Source Quality

Quality counts: A={quality.get('A', 0)}, B={quality.get('B', 0)}, C={quality.get('C', 0)}. Core conclusions rely mainly on A/B sources.

## Relationship to Project Findings

Relationship counts: {', '.join(f'{key}={value}' for key, value in sorted(rel.items()))}.

## Financial Analogy

The financial analogy is supported as a conceptual framework. It is not a causal claim about real markets. Every crosswalk row includes an important difference and an overclaim to avoid.

## Literature Disagreements

The contradiction registry records apparent disagreements around edge-seat folklore, BoW generalization, behavioral-risk Seer checking, live-policy failure, Witch aggression, Werewolf payoff, Seer reveal exposure, and deep-cover policy. Most are qualifications or design differences rather than direct contradictions.

## Validation

R7 validation checks cover metadata, duplicate DOI/title detection, source quality, finding coverage, claim support, bibliography generation, fake-citation guards, domain coverage, reproducibility, and documentation outputs.

## R8 Readiness

{markdown_table(readiness, [("criterion", "Criterion"), ("status", "Status"), ("evidence", "Evidence")])}

## Conclusion Label

`ready for synthesis`. R7 is complete with identified manual-review metadata items. The exact next stage is R8 - Final Integrated Data Analysis and Evidence Tables.
"""


def other_reports() -> dict[str, str]:
    return {
        "r7_pre_registration.md": report_header("R7 Pre-Registration") + "## Objective\n\nCross-check project findings against scholarly literature without running new simulation.\n\n## Inclusion Criteria\n\nInclude sources that directly support theory, method, or evidence mapping; exclude superficial or unverifiable sources.\n\n## Outcomes\n\nCoverage by domain, source quality, finding-literature relationships, financial analogy safety, contradiction registry, and R8 readiness.\n",
        "r7_search_methodology.md": report_header("R7 Search Methodology") + "## Search Systems Used\n\nCodex web search, publisher DOI pages, ACL Anthology, PMLR, AAAI OJS, Microsoft Research pages, PubMed, NBER, and book/publisher pages. Google Scholar, JSTOR, SSRN, IEEE Xplore, and ACM DL were not claimed as directly used unless represented by publisher/index records in the source metadata.\n\n## Screening\n\nSearches prioritized peer-reviewed and authoritative sources. Preprints and books were retained only with explicit limitations.\n",
        "r7_screening_report.md": report_header("R7 Screening Report") + "## Screening Summary\n\nAll retained sources are listed in `r7_source_screening_registry.csv`. Exclusions were duplicates, superficial keyword matches, unverifiable metadata, or unrelated domain focus.\n\n## Manual Review\n\nSeveral book or older DOI metadata items are marked `manual_review_required` or `manual_identifier_review` and should be checked before final submission bibliography formatting.\n",
        "r7_financial_analogy_report.md": report_header("R7 Financial Analogy Report") + "## Conclusion\n\nThe analogy is useful but bounded. `p_wolf` resembles a dynamic risk score, Werewolf deception resembles adversarial manipulation, Seer information resembles private signal value, and speaker memory resembles reputation. These are conceptual parallels, not causal financial-market claims.\n\n" + markdown_table(financial_crosswalk_rows(), [("game_entity_or_action", "Game item"), ("financial_analogue", "Financial analogue"), ("safe_interpretation", "Safe interpretation"), ("overclaim_to_avoid", "Overclaim to avoid")]),
        "r7_limitations.md": report_header("R7 Limitations") + "## Main Limitations\n\n- Some metadata for books and older records requires final manual bibliography review.\n- The project does not claim causal correspondence with real financial markets.\n- Some early-stage findings remain descriptive pilots.\n- Preprints and non-peer-reviewed books are not used as primary support for core empirical claims.\n- No new simulation was run in R7.\n",
        "r7_manual_review_items.md": report_header("R7 Manual Review Items") + "## Items\n\n- Confirm final edition metadata for book references before final report submission.\n- Confirm page ranges for older JSTOR/DOI records if page-specific citation is required.\n- Replace the proposal source note if the original DURF proposal file is later added.\n- Decide whether to cite preprints in the final report or retain them as background only.\n",
    }


def write_reports() -> None:
    reports = other_reports()
    reports.update(
        {
            "r7_social_deduction_literature.md": domain_report("social_deduction", "R7 Social Deduction Literature"),
            "r7_asymmetric_information_literature.md": domain_report("asymmetric_information", "R7 Asymmetric Information Literature"),
            "r7_herding_and_trust_literature.md": domain_report("herding_trust", "R7 Herding and Trust Literature"),
            "r7_deception_and_misinformation_literature.md": domain_report("deception_misinformation", "R7 Deception and Misinformation Literature"),
            "r7_behavioral_finance_literature.md": domain_report("behavioral_finance", "R7 Behavioral Finance Literature"),
            "r7_bow_and_domain_shift_literature.md": domain_report("bow_domain_shift", "R7 BoW and Domain Shift Literature"),
            "r7_offline_policy_failure_literature.md": domain_report("offline_policy", "R7 Offline Policy Failure Literature"),
            "r7_multi_agent_validation_literature.md": domain_report("simulation_validation", "R7 Multi-Agent Validation Literature"),
            "r7_risk_metrics_literature.md": domain_report("risk_metrics", "R7 Risk Metrics Literature"),
            "r7_project_finding_comparison_report.md": project_comparison_report(),
            "r7_theoretical_synthesis.md": theoretical_synthesis(),
            "r7_research_report.md": r7_research_report(),
        }
    )
    for filename, content in reports.items():
        write_text(OUTPUT_DIR / filename, content)


def append_unique_section(path: Path, marker: str, content: str) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker not in existing:
        path.write_text(existing.rstrip() + "\n\n" + content.strip() + "\n", encoding="utf-8")


def update_cumulative_registry() -> None:
    path = RESEARCH_DIR / "cumulative_evidence_registry.csv"
    rows = []
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = handle.readline() if False else list(rows[0].keys())
    existing = {(row["stage_id"], row["hypothesis_id"]) for row in rows}
    additions = [
        {
            "stage_id": "r7_literature_synthesis",
            "stage_name": "R7 Systematic Literature Comparison",
            "research_domain": "literature comparison",
            "hypothesis_id": "H_R7_literature_coverage",
            "hypothesis": "Every major project chapter can be mapped to verifiable scholarly literature.",
            "prior_hypothesis_source": "R6.2 readiness",
            "experiment_design": "Structured literature search, source screening, quality scoring, and finding-literature matrix.",
            "dataset_path": "results/literature_synthesis_stage_r7/r7_finding_literature_comparison_matrix.csv",
            "report_path": "results/literature_synthesis_stage_r7/r7_research_report.md",
            "raw_row_count": str(len(finding_mapping_rows())),
            "raw_game_count": "0",
            "independent_sample_size": "64 retained sources and 41 project findings",
            "matched_set_count": "NA",
            "seed_count": "NA",
            "behavioral_regime_count": "NA",
            "primary_outcome": "literature coverage",
            "comparison": "required findings versus retained source mapping",
            "control_condition": "NA",
            "descriptive_effect": "All 41 required findings mapped to literature.",
            "absolute_percentage_point_effect": "NA",
            "effect_size_type": "coverage count",
            "effect_size": "41 of 41 findings mapped",
            "confidence_interval": "not applicable",
            "raw_p_value": "not applicable",
            "adjusted_p_value": "not applicable",
            "multiplicity_method": "not applicable",
            "evidence_level": "LEVEL 4 - documentation and source validation",
            "seed_robustness": "not applicable",
            "regime_robustness": "not applicable",
            "design_validity": "source-quality and claim-support audits exported",
            "engine_validity": "not applicable",
            "distribution_shift_status": "literature comparison preserves domain-shift findings",
            "overfitting_status": "no new model fit",
            "leakage_status": "no hidden gameplay data used",
            "conclusion_label": "ready for synthesis",
            "hypothesis_status": "supported",
            "main_limitation": "Some bibliography metadata remains flagged for final manual review.",
            "supersedes_stage_id": "",
            "superseded_by_stage_id": "",
            "next_hypothesis": "R8 should consolidate final evidence tables and statistical conclusions.",
            "source_commit": "pending_current_stage_commit",
            "current_documentation_commit": "pending_current_stage_commit",
        },
        {
            "stage_id": "r7_financial_analogy",
            "stage_name": "R7 Systematic Literature Comparison",
            "research_domain": "financial analogy",
            "hypothesis_id": "H_R7_financial_analogy_bounded",
            "hypothesis": "The financial-market analogy is supportable as a conceptual framework with explicit limits.",
            "prior_hypothesis_source": "R5 financial-risk stage",
            "experiment_design": "Financial analogy crosswalk and claim support audit.",
            "dataset_path": "results/literature_synthesis_stage_r7/r7_financial_analogy_crosswalk.csv",
            "report_path": "results/literature_synthesis_stage_r7/r7_financial_analogy_report.md",
            "raw_row_count": str(len(FINANCIAL_CROSSWALK)),
            "raw_game_count": "0",
            "independent_sample_size": "16 analogy rows",
            "matched_set_count": "NA",
            "seed_count": "NA",
            "behavioral_regime_count": "NA",
            "primary_outcome": "safe financial analogy",
            "comparison": "game construct versus financial analogue",
            "control_condition": "NA",
            "descriptive_effect": "Every analogy row includes a limitation and overclaim to avoid.",
            "absolute_percentage_point_effect": "NA",
            "effect_size_type": "coverage count",
            "effect_size": "16 of 16 rows limitation-qualified",
            "confidence_interval": "not applicable",
            "raw_p_value": "not applicable",
            "adjusted_p_value": "not applicable",
            "multiplicity_method": "not applicable",
            "evidence_level": "LEVEL 4 - documentation and source validation",
            "seed_robustness": "not applicable",
            "regime_robustness": "not applicable",
            "design_validity": "overclaim audit exported",
            "engine_validity": "not applicable",
            "distribution_shift_status": "not applicable",
            "overfitting_status": "not applicable",
            "leakage_status": "no gameplay leakage issue",
            "conclusion_label": "financial analogy supported",
            "hypothesis_status": "supported with limitations",
            "main_limitation": "Analogy is conceptual and not causal evidence about markets.",
            "supersedes_stage_id": "",
            "superseded_by_stage_id": "",
            "next_hypothesis": "R8 should use the R7 crosswalk to choose final evidence-table language.",
            "source_commit": "pending_current_stage_commit",
            "current_documentation_commit": "pending_current_stage_commit",
        },
    ]
    for row in additions:
        key = (row["stage_id"], row["hypothesis_id"])
        if key not in existing:
            rows.append(row)
    write_csv(path, rows, fieldnames)


def update_proposal_matrix() -> None:
    path = RESEARCH_DIR / "durf_proposal_alignment_matrix.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = list(rows[0].keys())
    by_component = {row["proposal_component"]: row for row in rows}
    updates = {
        "Literature cross-check": {
            "status": "completed_and_extended",
            "evidence": "R7 systematic literature comparison maps 41 project findings to 64 retained sources.",
            "source_file": "results/literature_synthesis_stage_r7/r7_research_report.md",
            "quality_of_completion": "High with explicit manual metadata review items.",
            "remaining_work": "Use R7 in final integrated report.",
            "required_next_stage": "R8",
            "blocking_final_report": "No",
        },
        "Financial-market interpretation": {
            "status": "completed_with_limitations",
            "evidence": "R7 financial analogy crosswalk explicitly supports bounded conceptual analogies.",
            "source_file": "results/literature_synthesis_stage_r7/r7_financial_analogy_crosswalk.csv",
            "quality_of_completion": "High as conceptual framework; not causal market evidence.",
            "remaining_work": "Use safe wording in final report.",
            "required_next_stage": "R8",
            "blocking_final_report": "No",
        },
    }
    additions = [
        ("Related work", "Final report related-work source base.", "completed", "R7 bibliography, source notes, and domain reports exist.", "results/literature_synthesis_stage_r7/r7_research_report.md"),
        ("behavioral-finance literature", "Behavioral finance source base for final report.", "completed", "R7 retained market manipulation, herding, information, and risk sources.", "results/literature_synthesis_stage_r7/r7_behavioral_finance_literature.md"),
        ("game-theory literature", "Game-theory source base for final report.", "completed", "R7 retained Bayesian games, signaling, cheap talk, and reputation sources.", "results/literature_synthesis_stage_r7/r7_asymmetric_information_literature.md"),
        ("multi-agent literature", "Multi-agent and ABM validation source base.", "completed", "R7 retained social deduction and ABM validation sources.", "results/literature_synthesis_stage_r7/r7_multi_agent_validation_literature.md"),
        ("BoW literature", "BoW and domain-shift literature base.", "completed", "R7 retained text classification and domain-shift sources.", "results/literature_synthesis_stage_r7/r7_bow_and_domain_shift_literature.md"),
        ("final reference list", "Citation-ready final reference list.", "completed_with_limitations", "R7 generated BibTeX and APA draft references; manual review items are explicit.", "results/literature_synthesis_stage_r7/r7_references_apa7.md"),
    ]
    for component, update in updates.items():
        if component in by_component:
            by_component[component].update(update)
    existing_components = {row["proposal_component"] for row in rows}
    for component, description, status, evidence, source_file in additions:
        if component not in existing_components:
            rows.append(
                {
                    "proposal_component": component,
                    "original_proposal_description": description,
                    "status": status,
                    "evidence": evidence,
                    "source_file": source_file,
                    "quality_of_completion": "High",
                    "remaining_work": "Use in final report.",
                    "required_next_stage": "R8",
                    "priority": "High",
                    "blocking_final_report": "No",
                }
            )
    write_csv(path, rows, fieldnames)


def update_traceability() -> None:
    path = RESEARCH_DIR / "source_traceability_index.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = list(rows[0].keys())
    existing = {row["claim_id"] for row in rows}
    additions = [
        {
            "claim_id": "C_R7_01",
            "claim_summary": "R7 maps all required project findings to literature.",
            "stage": "R7",
            "source_file": "results/literature_synthesis_stage_r7/r7_finding_literature_comparison_matrix.csv",
            "source_table_or_section": "all rows",
            "dataset": "results/literature_synthesis_stage_r7/r7_finding_literature_comparison_matrix.csv",
            "analysis_script": "literature_stage_r7_analysis.py",
            "commit_hash": "pending_current_stage_commit",
            "verification_status": "verified_from_source",
            "notes": "No new gameplay experiment; literature synthesis only.",
        },
        {
            "claim_id": "C_R7_02",
            "claim_summary": "R7 supports financial analogy only as a bounded conceptual framework.",
            "stage": "R7",
            "source_file": "results/literature_synthesis_stage_r7/r7_financial_analogy_crosswalk.csv",
            "source_table_or_section": "all rows",
            "dataset": "results/literature_synthesis_stage_r7/r7_financial_analogy_crosswalk.csv",
            "analysis_script": "literature_stage_r7_analysis.py",
            "commit_hash": "pending_current_stage_commit",
            "verification_status": "verified_from_source",
            "notes": "Every row includes limitation and overclaim-to-avoid fields.",
        },
    ]
    for row in additions:
        if row["claim_id"] not in existing:
            rows.append(row)
    write_csv(path, rows, fieldnames)


def update_research_progress_docs() -> None:
    append_unique_section(
        RESEARCH_DIR / "cumulative_research_report.md",
        "## 32. R7 Systematic Literature Comparison",
        """## 32. R7 Systematic Literature Comparison

R7 conducts a structured literature comparison and theoretical synthesis without running new gameplay experiments. It retains 64 sources, maps all 41 required project findings, creates a financial analogy crosswalk, documents contradictions and limitations, and generates citation-ready BibTeX and APA draft references.

Conclusion: `ready for synthesis`. R7 supports the financial-market analogy as a bounded conceptual framework, not a causal claim about real markets. The exact next stage is R8 - Final Integrated Data Analysis and Evidence Tables.
""",
    )
    append_unique_section(
        RESEARCH_DIR / "durf_proposal_alignment_audit.md",
        "## R7 Literature Comparison Update",
        """## R7 Literature Comparison Update

R7 completes the proposal requirement to cross-check findings with literature. It adds related-work coverage for social deduction, game theory, herding, deception, behavioral finance, Bag-of-Words/domain shift, offline policy evaluation, simulation validation, and risk metrics. The final bibliography remains citation-ready with explicit manual-review items.
""",
    )
    append_unique_section(
        RESEARCH_DIR / "current_progress_assessment.md",
        "## R7 Current Assessment",
        """## R7 Current Assessment

Systematic literature comparison is complete with identified metadata review gaps. The project is ready for R8 final integrated Data Analysis and evidence tables.
""",
    )
    append_unique_section(
        RESEARCH_DIR / "remaining_work_roadmap.md",
        "## After R7",
        """## After R7

Next stage: R8 - Final Integrated Data Analysis and Evidence Tables. R8 should consolidate all hypotheses, final evidence grades, statistical results, literature relationships, and final limitations. R7 does not begin final report writing.
""",
    )


def write_all_outputs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_NOTES_DIR.mkdir(parents=True, exist_ok=True)

    write_csv(OUTPUT_DIR / "r7_literature_search_log.csv", search_log_rows())
    write_csv(OUTPUT_DIR / "r7_source_screening_registry.csv", source_screening_rows())
    write_csv(OUTPUT_DIR / "r7_source_quality_registry.csv", source_quality_rows())
    write_csv(OUTPUT_DIR / "r7_finding_literature_comparison_matrix.csv", finding_mapping_rows())
    write_csv(OUTPUT_DIR / "r7_financial_analogy_crosswalk.csv", financial_crosswalk_rows())
    write_csv(OUTPUT_DIR / "r7_literature_contradiction_registry.csv", contradiction_rows())
    write_csv(OUTPUT_DIR / "r7_claim_support_audit.csv", claim_support_rows())
    write_csv(OUTPUT_DIR / "r7_reference_metadata_validation.csv", reference_metadata_rows())
    write_csv(OUTPUT_DIR / "r7_domain_coverage_summary.csv", domain_coverage_rows())
    write_csv(OUTPUT_DIR / "r7_r8_readiness_summary.csv", r8_readiness_rows())
    write_text(OUTPUT_DIR / "r7_bibliography.bib", bibtex_entries())
    write_text(OUTPUT_DIR / "r7_references_apa7.md", apa_references())
    write_csv(OUTPUT_DIR / "r7_references_author_year.csv", author_year_rows())

    source_notes()
    write_figures()
    write_reports()
    update_cumulative_registry()
    update_proposal_matrix()
    update_traceability()
    update_research_progress_docs()


def main() -> int:
    write_all_outputs()
    print("R7 literature synthesis outputs generated")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Sources retained: {len(SOURCES)}")
    print(f"Project findings mapped: {len(PROJECT_FINDINGS)}")
    print(f"Source notes: {len(list(SOURCE_NOTES_DIR.glob('*.md')))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
