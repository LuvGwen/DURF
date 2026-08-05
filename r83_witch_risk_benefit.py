"""R8.3 Witch risk-benefit summary from frozen R8.2 outputs."""

from __future__ import annotations

from r83_common import (
    RESULTS_DIR,
    fmt,
    rows_by_key,
    r82_primary_contrasts,
    r82_policy_summary,
    witch_action_summary,
    write_csv,
    write_text,
)


OUTPUT_FIELDS = [
    "metric",
    "reference",
    "aggressive_full",
    "difference",
    "confidence_interval",
    "favorable_or_unfavorable",
    "statistical_status",
    "interpretation",
    "limitation",
]


def build_witch_risk_benefit(corrected_rows):
    summaries = rows_by_key(r82_policy_summary(), "module", "policy")
    contrasts = rows_by_key(r82_primary_contrasts(), "module", "metric")
    actions = witch_action_summary()
    ref = summaries[("witch", "reference")]
    cand = summaries[("witch", "aggressive_full")]
    actor = next(row for row in corrected_rows if row["module"] == "witch")
    win = contrasts[("witch", "village_win")]

    ref_wrong = actions["reference"]["wrong_poison"] / actions["reference"]["witch_poison"]
    cand_wrong = (
        actions["aggressive_full"]["wrong_poison"]
        / actions["aggressive_full"]["witch_poison"]
    )
    ref_slot_use = (
        actions["reference"]["witch_poison"] + actions["reference"]["witch_save"]
    ) / 2000
    cand_slot_use = (
        actions["aggressive_full"]["witch_poison"]
        + actions["aggressive_full"]["witch_save"]
    ) / 2000
    ref_potions_per_game = (
        actions["reference"]["witch_poison"] + actions["reference"]["witch_save"]
    ) / 1000
    cand_potions_per_game = (
        actions["aggressive_full"]["witch_poison"]
        + actions["aggressive_full"]["witch_save"]
    ) / 1000

    rows = [
        {
            "metric": "actor_payoff",
            "reference": ref["mean_actor_payoff"],
            "aggressive_full": cand["mean_actor_payoff"],
            "difference": actor["paired_difference"],
            "confidence_interval": f"[{actor['bootstrap_ci_low']}, {actor['bootstrap_ci_high']}]",
            "favorable_or_unfavorable": "favorable",
            "statistical_status": "corrected Holm-confirmatory primary effect",
            "interpretation": "Aggressive full improves expected Witch actor payoff under the frozen payoff specification.",
            "limitation": "Payoff improvement does not imply safety superiority.",
        },
        {
            "metric": "village_win_rate",
            "reference": ref["village_win_rate"],
            "aggressive_full": cand["village_win_rate"],
            "difference": float(cand["village_win_rate"]) - float(ref["village_win_rate"]),
            "confidence_interval": f"[{win['ci_low']}, {win['ci_high']}]",
            "favorable_or_unfavorable": "favorable",
            "statistical_status": "secondary unadjusted CI positive; Holm secondary p not confirmatory",
            "interpretation": "Aggressive full increases village win rate in the R8.2 replication dataset.",
            "limitation": "Village win is secondary and does not override the primary actor-payoff rule.",
        },
        {
            "metric": "wrong_poison_rate",
            "reference": ref_wrong,
            "aggressive_full": cand_wrong,
            "difference": cand_wrong - ref_wrong,
            "confidence_interval": "not_computed_in_R8.2",
            "favorable_or_unfavorable": "unfavorable",
            "statistical_status": "descriptive action-derived safety metric",
            "interpretation": "Aggressive full substantially increases wrong-poison frequency.",
            "limitation": "Action-derived rate is not a preregistered primary inferential outcome.",
        },
        {
            "metric": "potion_slot_use",
            "reference": ref_slot_use,
            "aggressive_full": cand_slot_use,
            "difference": cand_slot_use - ref_slot_use,
            "confidence_interval": "not_computed_in_R8.2",
            "favorable_or_unfavorable": "mixed",
            "statistical_status": "descriptive action-derived intensity metric",
            "interpretation": "Aggressive full uses many more available potion slots.",
            "limitation": "Higher intervention intensity can be useful or risky depending on context.",
        },
        {
            "metric": "potions_per_game",
            "reference": ref_potions_per_game,
            "aggressive_full": cand_potions_per_game,
            "difference": cand_potions_per_game - ref_potions_per_game,
            "confidence_interval": "not_computed_in_R8.2",
            "favorable_or_unfavorable": "mixed",
            "statistical_status": "descriptive action-derived intensity metric",
            "interpretation": "Aggressive full increases potion use by 0.627 potions per game.",
            "limitation": "Does not distinguish waste from appropriate intervention.",
        },
        {
            "metric": "downside_deviation",
            "reference": ref["downside_deviation"],
            "aggressive_full": cand["downside_deviation"],
            "difference": float(cand["downside_deviation"]) - float(ref["downside_deviation"]),
            "confidence_interval": "not_computed_in_R8.2",
            "favorable_or_unfavorable": "favorable",
            "statistical_status": "descriptive risk metric",
            "interpretation": "Downside deviation is slightly lower for aggressive full.",
            "limitation": "Risk metric was not the R8.2 primary inferential outcome.",
        },
        {
            "metric": "CVaR_like_95",
            "reference": ref["cvar_like_95"],
            "aggressive_full": cand["cvar_like_95"],
            "difference": float(cand["cvar_like_95"]) - float(ref["cvar_like_95"]),
            "confidence_interval": "not_computed_in_R8.2",
            "favorable_or_unfavorable": "unfavorable",
            "statistical_status": "descriptive tail-risk metric",
            "interpretation": "Aggressive full has a more negative CVaR-like 95 value, so tail-risk wording should remain cautious.",
            "limitation": "Tail risk comparison is descriptive.",
        },
        {
            "metric": "primary_waste",
            "reference": "unavailable_from_R8.2_export",
            "aggressive_full": "unavailable_from_R8.2_export",
            "difference": "unavailable_from_R8.2_export",
            "confidence_interval": "unavailable_from_R8.2_export",
            "favorable_or_unfavorable": "unavailable",
            "statistical_status": "unavailable",
            "interpretation": "R8.2 did not export full potion lifecycle state.",
            "limitation": "Do not reconstruct from incomplete action rows.",
        },
        {
            "metric": "extended_waste",
            "reference": "unavailable_from_R8.2_export",
            "aggressive_full": "unavailable_from_R8.2_export",
            "difference": "unavailable_from_R8.2_export",
            "confidence_interval": "unavailable_from_R8.2_export",
            "favorable_or_unfavorable": "unavailable",
            "statistical_status": "unavailable",
            "interpretation": "R8.2 did not export unused-potion and missed-opportunity lifecycle fields.",
            "limitation": "Use R6.2 only as separated historical lifecycle evidence.",
        },
    ]
    return rows


def write_witch_risk_benefit_outputs(corrected_rows):
    rows = build_witch_risk_benefit(corrected_rows)
    write_csv(
        RESULTS_DIR / "r83_witch_risk_benefit_summary.csv",
        rows,
        OUTPUT_FIELDS,
    )
    write_text(
        RESULTS_DIR / "r83_witch_risk_benefit_report.md",
        witch_risk_benefit_report(rows),
    )
    return rows


def witch_risk_benefit_report(rows):
    wrong = next(row for row in rows if row["metric"] == "wrong_poison_rate")
    return f"""# R8.3 Witch Risk-Benefit Report

Aggressive full improves expected payoff and village win rate under the frozen
R8.2 payoff specification, while substantially increasing wrong-poison
frequency and intervention intensity.

- Wrong-poison rate difference: {fmt(wrong['difference'])}
- Primary waste: unavailable from R8.2 export
- Extended waste: unavailable from R8.2 export

The final recommendation is therefore conditional/risk-tolerant, not an
unqualified safety-superiority claim.
"""


if __name__ == "__main__":
    from r83_primary_contrast_recalculation import recompute_primary_contrasts

    for row in write_witch_risk_benefit_outputs(recompute_primary_contrasts()):
        print(row)
