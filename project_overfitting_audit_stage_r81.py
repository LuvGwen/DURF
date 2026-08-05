"""Run R8.1 project-wide overfitting and selection-bias audit."""

from __future__ import annotations

from pathlib import Path

from r81_bow_audit import generate_bow_audit
from r81_common import (
    CORRECTED_R8_DIR,
    CORRECTED_R9_PACK_DIR,
    R4_MANIFEST,
    R5_MANIFEST,
    R8_DIR,
    R81_DIR,
    ROOT,
    build_validation_summary,
    ensure_dirs,
    markdown_table,
    read_csv,
    sha256_file,
    update_cumulative_docs,
    write_csv,
    write_md,
)
from r81_decision_history import generate_decision_history
from r81_distribution_sensitivity import generate_distribution_sensitivity
from r81_final_seed_reuse import generate_final_seed_reuse_audit
from r81_literature_bias_audit import generate_literature_bias_audit
from r81_ml_audit import generate_ml_audit
from r81_multiple_testing import generate_multiple_testing_inventory
from r81_outcome_switching import generate_outcome_switching_registry
from r81_payoff_sensitivity import generate_payoff_sensitivity
from r81_post_selection_bootstrap import generate_post_selection_bootstrap
from r81_rank_stability import generate_rank_stability_summary
from r81_recommendation_correction import generate_recommendation_corrections
from r81_replication_decision import generate_replication_decisions
from r81_split_integrity import generate_split_integrity_registry
from r81_strategy_search_audit import generate_strategy_search_registry
from r81_threshold_audit import generate_threshold_registry


REPORT_FILES = [
    "r81_pre_registration.md",
    "r81_audit_methodology.md",
    "r81_project_decision_history_report.md",
    "r81_strategy_search_report.md",
    "r81_outcome_switching_report.md",
    "r81_split_and_seed_integrity_report.md",
    "r81_multiple_testing_report.md",
    "r81_post_selection_bias_report.md",
    "r81_payoff_sensitivity_report.md",
    "r81_distribution_sensitivity_report.md",
    "r81_bow_overfitting_report.md",
    "r81_ml_overfitting_report.md",
    "r81_literature_confirmation_bias_report.md",
    "r81_villager_strategy_development_audit.md",
    "r81_seer_strategy_development_audit.md",
    "r81_witch_strategy_development_audit.md",
    "r81_hunter_strategy_development_audit.md",
    "r81_werewolf_strategy_development_audit.md",
    "r81_corrected_conclusions.md",
    "r81_replication_decision.md",
    "r81_limitations.md",
    "r81_overclaiming_audit.md",
    "r81_research_report.md",
    "r81_r9_readiness.md",
]


def _report(title: str, body: str) -> str:
    return f"# {title}\n\n{body.strip()}\n"


def _role_module(role: str) -> str:
    return {"Hunter": "hunter", "Seer": "seer", "Witch": "witch", "Werewolf": "wolf", "Villager": "villager"}[role]


def _write_corrected_r8_layer(
    corrected_rows: list[dict[str, object]],
    conclusion_rows: list[dict[str, object]],
    grade_rows: list[dict[str, object]],
    readiness_rows: list[dict[str, object]],
) -> None:
    add_cols = [
        "original_r8_label",
        "audited_label",
        "changed",
        "change_reason",
        "post_selection_risk",
        "confirmatory_status",
    ]

    def copy_with_audit(source_name: str, target_name: str, default_label: str = "unchanged") -> None:
        rows = read_csv(R8_DIR / source_name)
        out = []
        for row in rows:
            new_row = dict(row)
            mechanism = row.get("mechanism_or_role", row.get("role", ""))
            matching = next((item for item in corrected_rows if item["role"].lower() in mechanism.lower()), None)
            if matching is None:
                new_row.update(
                    {
                        "original_r8_label": row.get("conclusion_status", row.get("recommendation", default_label)),
                        "audited_label": default_label,
                        "changed": "False",
                        "change_reason": "No R8.1 role-strategy downgrade applied to this row.",
                        "post_selection_risk": "low_to_moderate",
                        "confirmatory_status": row.get("conclusion_status", default_label),
                    }
                )
            else:
                new_row.update({col: matching.get(col, "") for col in add_cols})
            out.append(new_row)
        write_csv(CORRECTED_R8_DIR / target_name, out)

    copy_with_audit("r8_supported_findings.csv", "corrected_supported_findings.csv")
    copy_with_audit("r8_negative_results.csv", "corrected_negative_results.csv")
    copy_with_audit("r8_uncertain_findings.csv", "corrected_uncertain_findings.csv")
    copy_with_audit("r8_final_hypothesis_registry.csv", "corrected_final_hypothesis_registry.csv")
    copy_with_audit("r8_final_statistical_evidence_table.csv", "corrected_final_statistical_evidence_table.csv")
    copy_with_audit("r8_proposal_completion_matrix.csv", "corrected_proposal_completion_matrix.csv")

    superseded = read_csv(R8_DIR / "r8_superseded_result_registry.csv")
    for row in conclusion_rows:
        if row["changed"] == "True":
            superseded.append(
                {
                    "superseded_result_id": f"R81_{row['role']}",
                    "superseded_stage": "R8",
                    "superseded_claim": row["original_r8_label"],
                    "superseding_stage": "R8.1",
                    "superseding_evidence": row["audited_label"],
                    "reason": row["change_reason"],
                    "final_reporting_rule": "Use audited labels and require R8.2 replication before changing defaults.",
                    "original_r8_label": row["original_r8_label"],
                    "audited_label": row["audited_label"],
                    "changed": row["changed"],
                    "change_reason": row["change_reason"],
                    "post_selection_risk": row["post_selection_risk"],
                    "confirmatory_status": row["confirmatory_status"],
                }
            )
    write_csv(CORRECTED_R8_DIR / "corrected_superseded_result_registry.csv", superseded)

    write_csv(CORRECTED_R8_DIR / "corrected_policy_evidence_grade_registry.csv", grade_rows)
    write_csv(CORRECTED_R8_DIR / "corrected_r9_readiness_summary.csv", readiness_rows)
    write_md(
        CORRECTED_R9_PACK_DIR / "README.md",
        _report(
            "Corrected R9 Input Pack",
            "This pack preserves original R8 source artifacts where useful and adds R8.1 corrected labels. "
            "The readiness decision is R8.2 TARGETED REPLICATION REQUIRED before adopting Seer immediate_reveal or Witch aggressive_full as defaults.",
        ),
    )
    manifest_rows = []
    for path in sorted(CORRECTED_R9_PACK_DIR.iterdir()):
        if path.is_file():
            manifest_rows.append(
                {
                    "filename": path.name,
                    "path": str(path.relative_to(ROOT)),
                    "status": "included",
                    "r81_note": "Use with R8.1 corrected labels.",
                }
            )
    write_csv(CORRECTED_R8_DIR / "corrected_r9_input_pack_manifest.csv", manifest_rows)


def _write_reports(
    decision_rows: list[dict[str, object]],
    strategy_rows: list[dict[str, object]],
    threshold_rows: list[dict[str, object]],
    outcome_rows: list[dict[str, object]],
    split_rows: list[dict[str, object]],
    seed_rows: list[dict[str, object]],
    testing_rows: list[dict[str, object]],
    selection_rows: list[dict[str, object]],
    curse_rows: list[dict[str, object]],
    stability_rows: list[dict[str, object]],
    corrected_rows: list[dict[str, object]],
    grade_rows: list[dict[str, object]],
    payoff_scenarios: list[dict[str, object]],
    payoff_rank_rows: list[dict[str, object]],
    coverage_rows: list[dict[str, object]],
    distribution_rows: list[dict[str, object]],
    bow_rows: list[dict[str, object]],
    ml_rows: list[dict[str, object]],
    literature_rows: list[dict[str, object]],
    replication_rows: list[dict[str, object]],
    conclusion_rows: list[dict[str, object]],
    readiness_rows: list[dict[str, object]],
) -> None:
    write_md(
        R81_DIR / "r81_pre_registration.md",
        _report(
            "R8.1 Retrospective Pre-Registration",
            (
                "R8.1 is a retrospective audit, not a new strategy search. The fixed audit questions are: "
                "which decisions were exploratory, which strategy/threshold families were searched, whether final seeds were reused for R8 selection, "
                "whether multiple testing and winner's-curse risks alter conclusions, whether payoff/risk variants change rankings, and whether R9 can begin. "
                "No historical raw datasets, R4 manifest, R5 manifest, or game mechanisms are modified."
            ),
        ),
    )
    write_md(
        R81_DIR / "r81_audit_methodology.md",
        _report(
            "R8.1 Audit Methodology",
            (
                "The audit combines registry review, static strategy-family counts, matched-set bootstrap resampling, payoff-sensitivity perturbation, "
                "distribution-shift risk scoring, BoW/ML/literature bias review, and corrected recommendation labeling. "
                "Matched-set bootstrap uses 5,000 replicates per role module and resamples R6.1 matched_set_id clusters."
            ),
        ),
    )
    write_md(
        R81_DIR / "r81_project_decision_history_report.md",
        _report(
            "Project Decision History",
            "The decision history distinguishes exploratory pilot choices from confirmatory or validation stages.\n\n"
            + markdown_table(decision_rows, [("stage_id", "Stage"), ("decision_id", "Decision"), ("hypothesis_timing", "Timing"), ("post_selection_risk", "Risk")]),
        ),
    )
    write_md(
        R81_DIR / "r81_strategy_search_report.md",
        _report(
            "Strategy Search Audit",
            "The registry shows substantial researcher degrees of freedom across policy, threshold, BoW, ML, and payoff variants.\n\n"
            + markdown_table(strategy_rows, [("mechanism_family", "Mechanism"), ("variant_count", "Variants"), ("selection_bias_risk", "Risk"), ("source_stage", "Source")]),
        ),
    )
    write_md(
        R81_DIR / "r81_outcome_switching_report.md",
        _report(
            "Outcome Switching Audit",
            markdown_table(outcome_rows, [("analysis_area", "Area"), ("final_or_selected_outcome", "Selected Outcome"), ("outcome_switching_risk", "Risk"), ("audit_action", "Action")]),
        ),
    )
    write_md(
        R81_DIR / "r81_split_and_seed_integrity_report.md",
        _report(
            "Split and Seed Integrity",
            "Final-seed reuse is classified as post-test model/policy selection rather than raw gameplay leakage.\n\n"
            + markdown_table(split_rows, [("split_unit", "Unit"), ("status", "Status"), ("leakage_or_bias_risk", "Risk")])
            + "\n\n"
            + markdown_table(seed_rows[:10], [("seed", "Seed"), ("seed_split", "Split"), ("reuse_classification", "Reuse")]),
        ),
    )
    write_md(
        R81_DIR / "r81_multiple_testing_report.md",
        _report(
            "Multiple Testing Inventory",
            markdown_table(testing_rows, [("analysis_family", "Family"), ("test_count", "Tests"), ("correction_used", "Correction"), ("post_selection_risk", "Risk")]),
        ),
    )
    write_md(
        R81_DIR / "r81_post_selection_bias_report.md",
        _report(
            "Post-Selection Bias and Winner's Curse",
            "Bootstrap selection frequencies are used to separate stable defaults from descriptive winners.\n\n"
            + markdown_table(stability_rows, [("role", "Role"), ("bootstrap_top_policy", "Bootstrap Top"), ("bootstrap_top_selection_frequency", "Frequency"), ("selection_stability_label", "Stability")])
            + "\n\n"
            + markdown_table(curse_rows, [("role", "Role"), ("policy", "Policy"), ("selection_frequency", "Selection Freq"), ("winner_curse_estimate", "Winner's Curse")], max_rows=12),
        ),
    )
    write_md(
        R81_DIR / "r81_payoff_sensitivity_report.md",
        _report(
            "Payoff Sensitivity",
            "R8.1 performs a summary-level perturbation audit only; R4 and R5 manifests are unchanged.\n\n"
            + markdown_table(payoff_scenarios, [("scenario_name", "Scenario"), ("description", "Description")])
            + "\n\n"
            + markdown_table([row for row in payoff_rank_rows if row["rank"] == 1], [("scenario_name", "Scenario"), ("role", "Role"), ("policy", "Winner"), ("adjusted_mean_actor_payoff", "Adjusted Mean")], max_rows=35),
        ),
    )
    write_md(
        R81_DIR / "r81_distribution_sensitivity_report.md",
        _report(
            "Distribution Sensitivity",
            markdown_table(coverage_rows, [("distribution_axis", "Axis"), ("status", "Status"), ("risk", "Risk")])
            + "\n\n"
            + markdown_table(distribution_rows, [("domain", "Domain"), ("severity", "Severity"), ("mitigation", "Mitigation")]),
        ),
    )
    write_md(R81_DIR / "r81_bow_overfitting_report.md", _report("BoW Overfitting Audit", markdown_table(bow_rows, [("stage", "Stage"), ("risk", "Risk"), ("status", "Status"), ("final_label", "Label")])))
    write_md(R81_DIR / "r81_ml_overfitting_report.md", _report("ML Overfitting Audit", markdown_table(ml_rows, [("stage", "Stage"), ("risk", "Risk"), ("status", "Status"), ("final_label", "Label")])))
    write_md(R81_DIR / "r81_literature_confirmation_bias_report.md", _report("Literature Confirmation-Bias Audit", markdown_table(literature_rows, [("risk", "Risk"), ("status", "Status"), ("evidence", "Evidence")])))

    for role in ["Villager", "Seer", "Witch", "Hunter", "Werewolf"]:
        module = _role_module(role)
        role_grades = [row for row in grade_rows if row["role"] == role]
        role_corrected = [row for row in corrected_rows if row["role"] == role][0]
        write_md(
            R81_DIR / f"r81_{module if module != 'wolf' else 'werewolf'}_strategy_development_audit.md",
            _report(
                f"{role} Strategy Development Audit",
                f"Audited recommendation: `{role_corrected['audited_recommended_policy']}`. "
                f"R8 strongest tested policy: `{role_corrected['strongest_tested_policy']}`. "
                f"Confirmatory status: `{role_corrected['confirmatory_status']}`.\n\n"
                + markdown_table(role_grades, [("policy", "Policy"), ("mean_actor_payoff", "Mean Payoff"), ("bootstrap_selection_frequency", "Selection Freq"), ("evidence_grade", "Evidence Grade")]),
            ),
        )

    write_md(
        R81_DIR / "r81_corrected_conclusions.md",
        _report(
            "Corrected Conclusions",
            "R8.1 does not overturn validated negative findings or the Villager trust-weighted result. It does downgrade Seer immediate_reveal and Witch aggressive_full from default-like language to replication-required experimental candidates.\n\n"
            + markdown_table(conclusion_rows, [("role", "Role"), ("audited_label", "Audited Label"), ("changed", "Changed"), ("post_selection_risk", "Risk")]),
        ),
    )
    write_md(
        R81_DIR / "r81_replication_decision.md",
        _report(
            "Replication Decision",
            "Exact decision: R8.2 TARGETED REPLICATION REQUIRED before R9 final recommendation claims.\n\n"
            + markdown_table(replication_rows, [("role", "Role"), ("audited_recommended_policy", "Audited Recommendation"), ("replication_priority", "Priority"), ("exact_next_action", "Next Action")]),
        ),
    )
    write_md(
        R81_DIR / "r81_limitations.md",
        _report(
            "R8.1 Limitations",
            "- R8.1 is retrospective and cannot convert exploratory stages into preregistered evidence.\n"
            "- Payoff sensitivity is summary-level and does not replace the frozen R4/R5 manifest calculations.\n"
            "- Corrected R8 labels reduce overclaiming but fresh-seed replication is still required for load-bearing changed recommendations.\n"
            "- Speech and ML conclusions remain template-bound or diagnostic unless validated in live game-level tests.",
        ),
    )
    write_md(
        R81_DIR / "r81_overclaiming_audit.md",
        _report(
            "Overclaiming Audit",
            "Final-report language must avoid global-optimum claims. Safe wording: `strongest tested within validated configuration space`, `descriptive candidate`, `requires targeted replication`, or `statistically supported harm` as appropriate.",
        ),
    )
    write_md(
        R81_DIR / "r81_r9_readiness.md",
        _report(
            "R9 Readiness",
            markdown_table(readiness_rows, [("criterion", "Criterion"), ("status", "Status"), ("evidence", "Evidence")])
            + "\n\nExact next stage: **R8.2 - Targeted Independent Replication of Load-Bearing Role Recommendations**.",
        ),
    )
    write_md(
        R81_DIR / "r81_research_report.md",
        _report(
            "R8.1 Project-Wide Overfitting and Selection-Bias Audit",
            (
                "R8.1 audited the entire DURF Werewolf research pipeline for researcher degrees of freedom, multiple testing, outcome switching, seed reuse, post-selection winner's curse, payoff sensitivity, distribution shift, BoW/ML overfitting, literature confirmation bias, and overclaiming risk.\n\n"
                f"R4 manifest hash: `{sha256_file(R4_MANIFEST)}`\n\n"
                f"R5 metric manifest hash: `{sha256_file(R5_MANIFEST)}`\n\n"
                "Main result: R4/R5 frozen manifests are unchanged and no raw gameplay leakage was found. However, R8 reused the R6.1 final seeds for maximum-payoff recommendation selection. This is classified as post-test policy selection, so Seer immediate_reveal and Witch aggressive_full are downgraded to replication-required experimental candidates. Villager trust_weighted remains the strongest supported positive policy; Hunter and Werewolf retain reference/default policies.\n\n"
                "Readiness decision: **R8.2 TARGETED REPLICATION REQUIRED** before final R9 default-recommendation claims."
            ),
        ),
    )


def generate_all() -> dict[str, object]:
    ensure_dirs()
    decision_rows = generate_decision_history()
    strategy_rows = generate_strategy_search_registry()
    threshold_rows = generate_threshold_registry()
    outcome_rows = generate_outcome_switching_registry()
    split_rows = generate_split_integrity_registry()
    seed_rows = generate_final_seed_reuse_audit()
    testing_rows = generate_multiple_testing_inventory()
    rank_rows, selection_rows, curse_rows = generate_post_selection_bootstrap()
    stability_rows = generate_rank_stability_summary(selection_rows)
    corrected_rows, grade_rows, conclusion_rows = generate_recommendation_corrections(selection_rows)
    replication_rows, readiness_rows = generate_replication_decisions(corrected_rows)
    payoff_scenarios, payoff_results, payoff_rank_rows = generate_payoff_sensitivity()
    coverage_rows, distribution_rows = generate_distribution_sensitivity()
    bow_rows = generate_bow_audit()
    ml_rows = generate_ml_audit()
    literature_rows = generate_literature_bias_audit()

    _write_corrected_r8_layer(corrected_rows, conclusion_rows, grade_rows, readiness_rows)
    _write_reports(
        decision_rows,
        strategy_rows,
        threshold_rows,
        outcome_rows,
        split_rows,
        seed_rows,
        testing_rows,
        selection_rows,
        curse_rows,
        stability_rows,
        corrected_rows,
        grade_rows,
        payoff_scenarios,
        payoff_rank_rows,
        coverage_rows,
        distribution_rows,
        bow_rows,
        ml_rows,
        literature_rows,
        replication_rows,
        conclusion_rows,
        readiness_rows,
    )

    output_files = [
        R81_DIR / "r81_experimental_decision_history.csv",
        R81_DIR / "r81_strategy_search_registry.csv",
        R81_DIR / "r81_threshold_search_registry.csv",
        R81_DIR / "r81_outcome_switching_registry.csv",
        R81_DIR / "r81_split_integrity_registry.csv",
        R81_DIR / "r81_final_seed_reuse_audit.csv",
        R81_DIR / "r81_project_wide_multiple_testing_inventory.csv",
        R81_DIR / "r81_policy_rank_bootstrap.csv",
        R81_DIR / "r81_policy_selection_frequency.csv",
        R81_DIR / "r81_winners_curse_estimates.csv",
        R81_DIR / "r81_selection_stability_summary.csv",
        R81_DIR / "r81_corrected_role_strategy_table.csv",
        R81_DIR / "r81_policy_evidence_grade_registry.csv",
        R81_DIR / "r81_payoff_sensitivity_scenarios.csv",
        R81_DIR / "r81_payoff_sensitivity_results.csv",
        R81_DIR / "r81_policy_rank_under_payoff_variants.csv",
        R81_DIR / "r81_regime_coverage_audit.csv",
        R81_DIR / "r81_distribution_shift_risk_registry.csv",
        R81_DIR / "r81_bow_overfitting_audit.csv",
        R81_DIR / "r81_ml_overfitting_audit.csv",
        R81_DIR / "r81_literature_confirmation_bias_audit.csv",
        R81_DIR / "r81_replication_priority_registry.csv",
        R81_DIR / "r81_conclusion_change_registry.csv",
        R81_DIR / "r81_r9_readiness_summary.csv",
        *[R81_DIR / name for name in REPORT_FILES],
        CORRECTED_R8_DIR / "corrected_role_strategy_table.csv",
        CORRECTED_R8_DIR / "corrected_supported_findings.csv",
        CORRECTED_R8_DIR / "corrected_negative_results.csv",
        CORRECTED_R8_DIR / "corrected_uncertain_findings.csv",
        CORRECTED_R8_DIR / "corrected_superseded_result_registry.csv",
        CORRECTED_R8_DIR / "corrected_final_hypothesis_registry.csv",
        CORRECTED_R8_DIR / "corrected_final_statistical_evidence_table.csv",
        CORRECTED_R8_DIR / "corrected_proposal_completion_matrix.csv",
        CORRECTED_R8_DIR / "corrected_r9_input_pack_manifest.csv",
    ]
    validation_rows = build_validation_summary(output_files)
    write_csv(R81_DIR / "r81_validation_summary.csv", validation_rows)

    update_cumulative_docs(R81_DIR / "r81_validation_summary.csv")

    return {
        "decision_rows": len(decision_rows),
        "strategy_rows": len(strategy_rows),
        "threshold_rows": len(threshold_rows),
        "rank_rows": len(rank_rows),
        "selection_rows": len(selection_rows),
        "corrected_rows": len(corrected_rows),
        "readiness": readiness_rows[-1]["status"],
    }


if __name__ == "__main__":
    summary = generate_all()
    print("R8.1 project-wide overfitting audit complete")
    for key, value in summary.items():
        print(f"{key}: {value}")
