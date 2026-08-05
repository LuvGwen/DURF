"""Run the R8.3 replication consistency audit.

This stage is analysis-only. It reads frozen R8.2/R8.1/R6.2 outputs, writes
corrected R8.3 reporting layers, and updates cumulative documentation. It
must not regenerate gameplay data.
"""

from __future__ import annotations

from r83_common import (
    R4_AUTHORITATIVE_HASH,
    R5_AUTHORITATIVE_HASH,
    R83_BOOTSTRAP_REPLICATES,
    R83_SIGN_FLIP_REPLICATES,
    RESULTS_DIR,
    fmt,
    r82_action_rows,
    r82_game_rows,
    write_csv,
    write_text,
)
from r83_primary_contrast_recalculation import write_primary_recalculation_outputs
from r83_role_conclusion_freeze import write_role_conclusion_outputs
from r83_r9_input_pack import (
    build_validation_summary,
    update_research_progress,
    write_corrected_layers,
    write_r9_readiness,
)
from r83_seer_consistency_audit import write_seer_consistency_outputs
from r83_seer_evidence_integration import write_seer_evidence_outputs
from r83_witch_risk_benefit import write_witch_risk_benefit_outputs


VALIDATION_FIELDS = ["check", "passed", "detail"]


def write_pre_registration():
    write_text(
        RESULTS_DIR / "r83_pre_registration.md",
        f"""# R8.3 Pre-Registration

R8.3 is a replication statistical consistency audit and final role-conclusion
freeze. It reads only frozen R8.2/R8.1/R6.2 artifacts.

## Frozen Comparisons

- Villager: `trust_weighted` vs `reference`
- Seer: `immediate_reveal` vs `private_only`
- Witch: `aggressive_full` vs `reference`

## Primary Outcome

The primary outcome is actor payoff. The independent inference block is
`matched_set_id`. Holm correction is applied across exactly the three primary
role contrasts.

## Fixed Methods

- Matched-set bootstrap replicates: {R83_BOOTSTRAP_REPLICATES}
- Matched sign-flip replicates: {R83_SIGN_FLIP_REPLICATES}
- No gameplay regeneration
- No threshold tuning
- No post-hoc primary outcome changes
- No reconstruction of unavailable lifecycle metrics

## Frozen Manifest Hashes

- R4 payoff manifest: `{R4_AUTHORITATIVE_HASH}`
- R5 metric manifest: `{R5_AUTHORITATIVE_HASH}`
""",
    )


def write_inference_standard():
    write_text(
        RESULTS_DIR / "r83_inference_interpretation_standard.md",
        """# R8.3 Inference Interpretation Standard

## Primary CI

The primary effect interval is the candidate-minus-reference matched-set
bootstrap confidence interval over actor-payoff differences. The inference
block is `matched_set_id`.

## Multiplicity

The reported CI is not multiplicity-adjusted. The confirmatory decision is
controlled by the Holm-adjusted p-value across exactly three primary tests:
Villager, Seer, and Witch.

## Conflicting CI and P-Value Reporting

If an unadjusted CI excludes zero but the Holm-adjusted p-value is not
confirmatory, the result must be reported as positive-direction but not
confirmatorily replicated. An unadjusted CI must not be described as
overriding the preregistered adjusted test.

## Policy-Level CIs Versus Paired-Effect CIs

Policy-level CIs describe the mean outcome for one policy. Paired-effect CIs
describe the matched candidate-minus-reference contrast and are the relevant
interval for R8.3 primary inference.

## Bootstrap Versus Sign-Flip Inference

The matched bootstrap estimates uncertainty in the paired mean difference.
The sign-flip test estimates a two-sided null distribution under exchangeable
signs for all matched differences, including zero differences. Removing zero
differences while changing the denominator is not valid for the R8.3 primary
test.
""",
    )


def write_research_report(corrected_rows, final_rows, five_role_rows, witch_rows, seer_rows, readiness_decision):
    lines = [
        "# R8.3 Replication Consistency Audit and Final Role Freeze",
        "",
        "## Summary",
        "",
        "R8.3 found that the R8.2 Seer CI/p-value inconsistency was caused by "
        "a reporting/calculation error in the sign-flip p-value denominator. "
        "The R8.2 paired actor-payoff differences and CIs were reproducible, "
        "but the raw p-values were recomputed using all matched-set differences.",
        "",
        "## Corrected Primary Contrasts",
        "",
        "| Module | Candidate | Difference | 95% CI | Raw p | Holm p | Result |",
        "|---|---|---:|---|---:|---:|---|",
    ]
    for row in corrected_rows:
        lines.append(
            f"| {row['module']} | {row['candidate']} | "
            f"{fmt(row['paired_difference'])} | "
            f"[{fmt(row['bootstrap_ci_low'])}, {fmt(row['bootstrap_ci_high'])}] | "
            f"{fmt(row['raw_p_value'])} | {fmt(row['Holm_adjusted_p_value'])} | "
            f"{row['final_authoritative_result']} |"
        )

    lines.extend([
        "",
        "## Final Role Conclusions",
        "",
        "| Role | Final Evidence Label | Recommendation |",
        "|---|---|---|",
    ])
    for row in final_rows:
        lines.append(
            f"| {row['role']} | {row['final_evidence_label']} | "
            f"{row['final_recommendation']} |"
        )

    lines.extend([
        "",
        "## Five-Role Recommendation Freeze",
        "",
        "| Role | Conservative Default | Performance Policy | Evidence Grade |",
        "|---|---|---|---|",
    ])
    for row in five_role_rows:
        lines.append(
            f"| {row['role']} | {row['conservative_default']} | "
            f"{row['performance_maximizing_policy']} | {row['evidence_grade']} |"
        )

    wrong_poison = next(row for row in witch_rows if row["metric"] == "wrong_poison_rate")
    lines.extend([
        "",
        "## Witch Tradeoff",
        "",
        "Aggressive full improves expected Witch actor payoff and village win "
        "rate under the frozen payoff specification, while increasing "
        f"wrong-poison rate by {fmt(wrong_poison['difference'])}. Primary and "
        "extended potion waste remain unavailable from the R8.2 export.",
        "",
        "## Seer Safety Evidence",
        "",
        "R8.3 separates corrected R8.2 payoff replication from historical R6.2 "
        "lifecycle safety evidence. R8.2 did not export next-night hazard or "
        "short-horizon survival fields, so immediate reveal is payoff-supported "
        "but exposure-constrained rather than a safety-superior default.",
        "",
        "## R9 Readiness",
        "",
        f"Decision: **{readiness_decision}**.",
    ])
    write_text(RESULTS_DIR / "r83_research_report.md", "\n".join(lines))


def run_documentation_validation():
    from validate_research_documentation import main as validate_documentation

    return validate_documentation() == 0


def write_validation_outputs(corrected_rows, documentation_passed):
    rows = build_validation_summary(corrected_rows)
    rows.append({
        "check": "documentation_validation_passed",
        "passed": str(bool(documentation_passed)),
        "detail": "validate_research_documentation.py",
    })
    write_csv(RESULTS_DIR / "r83_validation_summary.csv", rows, VALIDATION_FIELDS)
    return rows


def run_r83():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    corrected_rows = write_primary_recalculation_outputs()
    seer_audit_rows = write_seer_consistency_outputs(corrected_rows)
    final_rows, five_role_rows, claim_rows = write_role_conclusion_outputs(corrected_rows)
    witch_rows = write_witch_risk_benefit_outputs(corrected_rows)
    seer_rows = write_seer_evidence_outputs(corrected_rows)
    write_pre_registration()
    write_inference_standard()
    write_corrected_layers(
        corrected_rows,
        final_rows,
        five_role_rows,
        claim_rows,
        witch_rows,
        seer_rows,
    )

    provisional_validation = build_validation_summary(corrected_rows)
    provisional_validation.append({
        "check": "documentation_validation_passed",
        "passed": "True",
        "detail": "pre-validation placeholder; overwritten after validation run",
    })
    write_csv(RESULTS_DIR / "r83_validation_summary.csv", provisional_validation, VALIDATION_FIELDS)
    readiness_rows, readiness_decision = write_r9_readiness(provisional_validation)
    update_research_progress(corrected_rows, final_rows, five_role_rows, readiness_decision)
    write_research_report(
        corrected_rows,
        final_rows,
        five_role_rows,
        witch_rows,
        seer_rows,
        readiness_decision,
    )

    documentation_passed = run_documentation_validation()
    validation_rows = write_validation_outputs(corrected_rows, documentation_passed)
    readiness_rows, readiness_decision = write_r9_readiness(validation_rows)
    update_research_progress(corrected_rows, final_rows, five_role_rows, readiness_decision)
    write_research_report(
        corrected_rows,
        final_rows,
        five_role_rows,
        witch_rows,
        seer_rows,
        readiness_decision,
    )

    return {
        "corrected_rows": corrected_rows,
        "seer_audit_rows": seer_audit_rows,
        "final_rows": final_rows,
        "five_role_rows": five_role_rows,
        "claim_rows": claim_rows,
        "witch_rows": witch_rows,
        "seer_rows": seer_rows,
        "validation_rows": validation_rows,
        "readiness_rows": readiness_rows,
        "readiness_decision": readiness_decision,
        "game_rows_read": len(r82_game_rows()),
        "action_rows_read": len(r82_action_rows()),
    }


if __name__ == "__main__":
    result = run_r83()
    print("R8.3 replication consistency audit complete.")
    print(f"Game rows read: {result['game_rows_read']}")
    print(f"Action rows read: {result['action_rows_read']}")
    print(f"Readiness: {result['readiness_decision']}")
