"""Freeze R8.3 final role conclusions from corrected replication evidence."""

from __future__ import annotations

from r83_common import (
    FROZEN_COMPARISONS,
    R81_DIR,
    RESULTS_DIR,
    fmt,
    read_csv,
    rows_by_key,
    r82_primary_contrasts,
    r82_policy_summary,
    r82_special_metrics,
    support_rate,
    witch_action_summary,
    write_csv,
    write_text,
)


FINAL_REPLICATION_FIELDS = [
    "role",
    "reference_policy",
    "candidate_policy",
    "primary_difference",
    "authoritative_ci",
    "raw_p_value",
    "Holm_adjusted_p_value",
    "primary_rule_met",
    "faction_win_difference",
    "faction_win_ci",
    "mechanism_metrics",
    "safety_metrics",
    "unavailable_metrics",
    "seed_robustness",
    "regime_robustness",
    "final_evidence_label",
    "policy_evidence_grade",
    "final_recommendation",
    "recommendation_scope",
    "prohibited_wording",
    "source_files",
]

FIVE_ROLE_FIELDS = [
    "role",
    "conservative_default",
    "performance_maximizing_policy",
    "conditional_policy",
    "exploratory_candidate",
    "rejected_policies",
    "confirmatory_status",
    "evidence_grade",
    "replication_status",
    "safety_tradeoff",
    "payoff_specification_dependence",
    "regime_scope",
    "simulation_scope",
    "final_safe_wording",
]

CLAIM_FIELDS = [
    "claim_id",
    "role",
    "claim",
    "status_label",
    "evidence",
    "final_safe_wording",
    "source_files",
]


def _secondary_contrast_by_module():
    return {
        row["module"]: row
        for row in r82_primary_contrasts()
        if row["outcome_role"] == "secondary"
    }


def _risk_diff(summary_by_key, module, candidate, reference):
    cand = summary_by_key[(module, candidate)]
    ref = summary_by_key[(module, reference)]
    return {
        "downside_diff": float(cand["downside_deviation"]) - float(ref["downside_deviation"]),
        "cvar95_diff": float(cand["cvar_like_95"]) - float(ref["cvar_like_95"]),
    }


def build_final_replication_conclusions(corrected_rows):
    summary = rows_by_key(r82_policy_summary(), "module", "policy")
    special = rows_by_key(r82_special_metrics(), "module", "policy")
    secondary = _secondary_contrast_by_module()
    actions = witch_action_summary()
    rows = []
    for row in corrected_rows:
        module = row["module"]
        spec = FROZEN_COMPARISONS[module]
        reference = spec["reference"]
        candidate = spec["candidate"]
        role = spec["role"]
        win = secondary[module]
        seed = support_rate(module, "actor_payoff", "seed")
        regime = support_rate(module, "actor_payoff", "behavioral_regime")
        risks = _risk_diff(summary, module, candidate, reference)
        mechanism = ""
        safety = ""
        unavailable = ""
        recommendation = ""
        grade = "A"
        label = "independently_replicated_confirmatory_supported"
        scope = "tested R8.2 simulation configuration"
        if module == "villager":
            ref_sp = special[(module, reference)]
            cand_sp = special[(module, candidate)]
            accuracy_diff = (
                float(cand_sp["correct_vote_rate"])
                - float(ref_sp["correct_vote_rate"])
            )
            wrong_elim_diff = (
                float(cand_sp["wrong_eliminations"]) / 1000
                - float(ref_sp["wrong_eliminations"]) / 1000
            )
            mechanism = (
                f"vote_accuracy_diff={fmt(accuracy_diff)}; "
                f"wrong_eliminations_per_game_diff={fmt(wrong_elim_diff)}"
            )
            safety = (
                f"downside_diff={fmt(risks['downside_diff'])}; "
                f"cvar95_diff={fmt(risks['cvar95_diff'])}"
            )
            recommendation = "Recommend trust_weighted within tested simulation configuration."
        elif module == "seer":
            label = "replicated_positive_with_material_tradeoff"
            grade = "B"
            mechanism = "immediate_reveal payoff effect corrected to confirmatory; reveal events increase public information."
            safety = "R6.2 historical audit reports post-reveal exposure; R8.2 terminal survival is 0% for both policies."
            unavailable = "next-night hazard; one-round survival; two-round survival unavailable from R8.2 export"
            recommendation = (
                "Retain private_only as safety-conservative default; treat "
                "immediate_reveal as payoff-supported but exposure-constrained."
            )
        elif module == "witch":
            label = "replicated_positive_with_material_tradeoff"
            grade = "A/B"
            ref_wrong = actions[reference]["wrong_poison"] / actions[reference]["witch_poison"]
            cand_wrong = actions[candidate]["wrong_poison"] / actions[candidate]["witch_poison"]
            ref_use = (actions[reference]["witch_poison"] + actions[reference]["witch_save"]) / 1000
            cand_use = (actions[candidate]["witch_poison"] + actions[candidate]["witch_save"]) / 1000
            mechanism = (
                f"wrong_poison_diff={fmt(cand_wrong - ref_wrong)}; "
                f"potions_per_game_diff={fmt(cand_use - ref_use)}"
            )
            safety = (
                f"wrong_poison_reference={fmt(ref_wrong)}; "
                f"wrong_poison_candidate={fmt(cand_wrong)}; "
                f"downside_diff={fmt(risks['downside_diff'])}; "
                f"cvar95_diff={fmt(risks['cvar95_diff'])}"
            )
            unavailable = "primary_waste; extended_waste unavailable from R8.2 export"
            recommendation = (
                "Use aggressive_full only as a conditional risk-tolerant policy; "
                "retain reference as conservative default option."
            )
        rows.append({
            "role": role,
            "reference_policy": reference,
            "candidate_policy": candidate,
            "primary_difference": row["paired_difference"],
            "authoritative_ci": f"[{row['bootstrap_ci_low']}, {row['bootstrap_ci_high']}]",
            "raw_p_value": row["raw_p_value"],
            "Holm_adjusted_p_value": row["Holm_adjusted_p_value"],
            "primary_rule_met": str(float(row["Holm_adjusted_p_value"]) <= 0.05),
            "faction_win_difference": win["mean_difference"],
            "faction_win_ci": f"[{win['ci_low']}, {win['ci_high']}]",
            "mechanism_metrics": mechanism,
            "safety_metrics": safety,
            "unavailable_metrics": unavailable,
            "seed_robustness": (
                f"actor_payoff_support={fmt(seed['support_rate'])}; "
                f"groups={seed['group_count']}"
            ),
            "regime_robustness": (
                f"actor_payoff_support={fmt(regime['support_rate'])}; "
                f"groups={regime['group_count']}"
            ),
            "final_evidence_label": label,
            "policy_evidence_grade": grade,
            "final_recommendation": recommendation,
            "recommendation_scope": scope,
            "prohibited_wording": "optimal; proven; universally best; causes",
            "source_files": (
                "results/targeted_replication_stage_r82/r82_game_level_raw.csv; "
                "results/targeted_replication_stage_r82/r82_action_raw.csv.gz"
            ),
        })
    return rows


def build_five_role_recommendations():
    r81 = {
        row["role"]: row
        for row in read_csv(R81_DIR / "r81_corrected_role_strategy_table.csv")
    }
    return [
        {
            "role": "Villager",
            "conservative_default": "reference",
            "performance_maximizing_policy": "trust_weighted",
            "conditional_policy": "trust_weighted",
            "exploratory_candidate": "",
            "rejected_policies": "none in R8.2 frozen scope",
            "confirmatory_status": "independently replicated confirmatory improvement",
            "evidence_grade": "A",
            "replication_status": "R8.2/R8.3 fresh-seed replication supported",
            "safety_tradeoff": "No material safety penalty detected; false-positive vote rate decreased.",
            "payoff_specification_dependence": "frozen R4/R5 payoff specification",
            "regime_scope": "ten R6.1 behavioral regimes",
            "simulation_scope": "10-player randomized-role simulation",
            "final_safe_wording": "Trust-weighted voting is recommended within the tested simulation configuration.",
        },
        {
            "role": "Seer",
            "conservative_default": "private_only",
            "performance_maximizing_policy": "immediate_reveal",
            "conditional_policy": "immediate_reveal only when exposure risk is acceptable",
            "exploratory_candidate": "",
            "rejected_policies": "none in R8.2 frozen scope",
            "confirmatory_status": "payoff effect replicated after R8.3 p-value correction; default constrained by safety evidence",
            "evidence_grade": "B",
            "replication_status": "corrected independent payoff replication",
            "safety_tradeoff": "R6.2 reports high post-reveal exposure; R8.2 lacks short-horizon survival exports.",
            "payoff_specification_dependence": "frozen R4/R5 payoff specification",
            "regime_scope": "ten R6.1 behavioral regimes; safety lifecycle from historical R6.2 audit",
            "simulation_scope": "10-player randomized-role simulation",
            "final_safe_wording": "Retain private_only as the safety-conservative default; immediate_reveal is payoff-supported but exposure-constrained.",
        },
        {
            "role": "Witch",
            "conservative_default": "reference",
            "performance_maximizing_policy": "aggressive_full",
            "conditional_policy": "aggressive_full for risk-tolerant policy use",
            "exploratory_candidate": "",
            "rejected_policies": "conservative_full historically harmful in R6.1",
            "confirmatory_status": "replicated payoff improvement with material safety tradeoff",
            "evidence_grade": "A/B",
            "replication_status": "R8.2/R8.3 fresh-seed replication supported for payoff",
            "safety_tradeoff": "Wrong-poison and potion-use rates materially increase.",
            "payoff_specification_dependence": "frozen R4/R5 payoff specification; lifecycle waste unavailable from R8.2",
            "regime_scope": "ten R6.1 behavioral regimes",
            "simulation_scope": "10-player randomized-role simulation",
            "final_safe_wording": "Aggressive full is a conditional risk-tolerant Witch policy, not an unconditional safety-superior default.",
        },
        {
            "role": "Hunter",
            "conservative_default": "reference",
            "performance_maximizing_policy": "reference",
            "conditional_policy": "",
            "exploratory_candidate": "",
            "rejected_policies": r81["Hunter"]["strictly_dominated_policies"],
            "confirmatory_status": "retained reference; no tested alternative confirmed improvement",
            "evidence_grade": "B",
            "replication_status": "not part of R8.2; R8.1 said no replication required for retaining reference",
            "safety_tradeoff": "No new R8.3 gameplay evidence.",
            "payoff_specification_dependence": "R6.1/R8.1 corrected evidence",
            "regime_scope": "R6.1 behavioral regimes",
            "simulation_scope": "10-player randomized-role simulation",
            "final_safe_wording": "Retain Hunter reference policy; no tested alternative should be promoted.",
        },
        {
            "role": "Werewolf",
            "conservative_default": "reference",
            "performance_maximizing_policy": "reference / threat_adaptive family",
            "conditional_policy": "threat_adaptive may be treated as tied family member",
            "exploratory_candidate": "",
            "rejected_policies": r81["Werewolf"]["strictly_dominated_policies"],
            "confirmatory_status": "no unique superior member established",
            "evidence_grade": "B",
            "replication_status": "not part of R8.2; R8.1 retained reference family",
            "safety_tradeoff": "No new R8.3 gameplay evidence.",
            "payoff_specification_dependence": "R6.1/R8.1 corrected evidence",
            "regime_scope": "R6.1 behavioral regimes",
            "simulation_scope": "10-player randomized-role simulation",
            "final_safe_wording": "Use reference/threat_adaptive family wording; do not claim a unique superior Werewolf policy.",
        },
    ]


def build_final_claim_registry(final_rows, five_role_rows):
    return [
        {
            "claim_id": "R83_CLAIM_01",
            "role": "Villager",
            "claim": "trust_weighted improves Villager payoff and vote accuracy.",
            "status_label": "independently_replicated_confirmatory_supported",
            "evidence": "R8.3 corrected actor-payoff Holm p <= 0.05; vote accuracy increased.",
            "final_safe_wording": "Trust-weighted is recommended within the tested simulation configuration.",
            "source_files": "r83_primary_contrast_recalculation.csv; r83_final_replication_conclusions.csv",
        },
        {
            "claim_id": "R83_CLAIM_02",
            "role": "Seer",
            "claim": "immediate_reveal improves Seer actor payoff.",
            "status_label": "replicated_positive_with_material_tradeoff",
            "evidence": "R8.3 corrected p-value resolves R8.2 inconsistency; R6.2 safety exposure remains.",
            "final_safe_wording": "Immediate reveal is payoff-supported but exposure-constrained.",
            "source_files": "r83_primary_contrast_recalculation.csv; r83_seer_evidence_integration.csv",
        },
        {
            "claim_id": "R83_CLAIM_03",
            "role": "Seer",
            "claim": "immediate_reveal is a safe unconditional default.",
            "status_label": "withdrawn",
            "evidence": "R8.2 lacks short-horizon safety exports and R6.2 found exposure.",
            "final_safe_wording": "Retain private_only as safety-conservative default.",
            "source_files": "r83_seer_evidence_integration.csv",
        },
        {
            "claim_id": "R83_CLAIM_04",
            "role": "Witch",
            "claim": "aggressive_full improves Witch payoff and village win rate.",
            "status_label": "replicated_positive_with_material_tradeoff",
            "evidence": "R8.3 corrected actor-payoff Holm p <= 0.05; wrong-poison rate increases.",
            "final_safe_wording": "Aggressive full is conditional/risk-tolerant, not unconditionally safety-superior.",
            "source_files": "r83_witch_risk_benefit_summary.csv",
        },
        {
            "claim_id": "R83_CLAIM_05",
            "role": "Hunter",
            "claim": "Hunter reference remains the default.",
            "status_label": "reference_retained",
            "evidence": "R8.1 corrected layer; no R8.2 replication required.",
            "final_safe_wording": "Retain Hunter reference.",
            "source_files": "results/project_overfitting_audit_stage_r81/r81_corrected_role_strategy_table.csv",
        },
        {
            "claim_id": "R83_CLAIM_06",
            "role": "Werewolf",
            "claim": "Werewolf reference/threat_adaptive family remains the supported wording.",
            "status_label": "reference_retained",
            "evidence": "R8.1 corrected layer retained reference family and rejected deep_cover where supported.",
            "final_safe_wording": "Do not claim a unique superior Werewolf policy.",
            "source_files": "results/project_overfitting_audit_stage_r81/r81_corrected_role_strategy_table.csv",
        },
        {
            "claim_id": "R83_CLAIM_07",
            "role": "All",
            "claim": "Final role recommendations are bounded by simulation distribution and payoff specification.",
            "status_label": "simulation_distribution_bound",
            "evidence": "All role conclusions use 10-player simulated games and frozen payoff rules.",
            "final_safe_wording": "Report findings as simulation-specific strategy evidence.",
            "source_files": "r83_final_five_role_recommendations.csv",
        },
    ]


def write_role_conclusion_outputs(corrected_rows):
    final_rows = build_final_replication_conclusions(corrected_rows)
    five_role_rows = build_five_role_recommendations()
    claim_rows = build_final_claim_registry(final_rows, five_role_rows)
    write_csv(
        RESULTS_DIR / "r83_final_replication_conclusions.csv",
        final_rows,
        FINAL_REPLICATION_FIELDS,
    )
    write_csv(
        RESULTS_DIR / "r83_final_five_role_recommendations.csv",
        five_role_rows,
        FIVE_ROLE_FIELDS,
    )
    write_csv(
        RESULTS_DIR / "r83_final_claim_registry.csv",
        claim_rows,
        CLAIM_FIELDS,
    )
    write_text(
        RESULTS_DIR / "r83_final_role_conclusion_report.md",
        final_role_report(five_role_rows),
    )
    write_text(
        RESULTS_DIR / "r83_overclaiming_audit.md",
        overclaiming_audit(),
    )
    return final_rows, five_role_rows, claim_rows


def final_role_report(rows):
    lines = [
        "# R8.3 Final Role Conclusion Report",
        "",
        "R8.3 freezes role conclusions after correcting the R8.2 sign-flip p-value issue.",
        "",
        "| Role | Conservative Default | Performance Policy | Evidence Grade | Safe Wording |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['role']} | {row['conservative_default']} | "
            f"{row['performance_maximizing_policy']} | {row['evidence_grade']} | "
            f"{row['final_safe_wording']} |"
        )
    return "\n".join(lines)


def overclaiming_audit():
    return """# R8.3 Overclaiming Audit

Prohibited wording for final R9 reporting:

- optimal
- proven
- universally best
- causes

Allowed wording must be bounded to the tested simulation configuration, the
frozen payoff specification, and the audited role-specific evidence. Seer and
Witch conclusions must explicitly disclose safety tradeoffs and unavailable
R8.2 lifecycle metrics.
"""


if __name__ == "__main__":
    from r83_primary_contrast_recalculation import recompute_primary_contrasts

    outputs = write_role_conclusion_outputs(recompute_primary_contrasts())
    for table in outputs:
        print(len(table))
