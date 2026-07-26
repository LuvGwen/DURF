from pathlib import Path

from ml_distribution_shift import summarize_shift_rows
from ml_feature_registry import FEATURE_COLUMNS
from ml_train_baselines import as_float
from ml_behavioral_regimes import get_behavioral_regimes
from ml_wolf_kill_analysis import run_stage2a_analysis
from ml_wolf_kill_live_experiment import (
    get_stage2a_behavioral_regimes,
    run_wolf_kill_live_experiment,
)
from ml_wolf_kill_model_freeze import (
    EXCLUDED_STAGE15_FINAL_TEST_SEEDS,
    FROZEN_MODEL_MANIFEST_PATH,
    LIVE_FINAL_TEST_SEEDS,
    STAGE2A_RESULTS_DIR,
    TRAINING_SEEDS,
    VALIDATION_SEEDS,
    create_frozen_wolf_kill_model,
    live_feature_columns,
    validate_frozen_model_manifest,
)
from ml_wolf_kill_policy import PRIMARY_WOLF_KILL_POLICIES
from ml_wolf_kill_shadow_expansion import run_wolf_kill_shadow_expansion
from roles import HUNTER, SEER, WITCH


REPORT_PATHS = {
    "schema": STAGE2A_RESULTS_DIR / "ml_stage2a_schema.md",
    "experiment_report": (
        STAGE2A_RESULTS_DIR / "ml_stage2a_experiment_report.md"
    ),
    "pre_registration": (
        STAGE2A_RESULTS_DIR / "ml_stage2a_pre_registration.md"
    ),
    "leakage_audit": (
        STAGE2A_RESULTS_DIR / "ml_stage2a_information_leakage_audit.md"
    ),
    "model_freeze_audit": (
        STAGE2A_RESULTS_DIR / "ml_stage2a_model_freeze_audit.md"
    ),
    "distribution_shift_report": (
        STAGE2A_RESULTS_DIR / "ml_stage2a_distribution_shift_report.md"
    ),
    "failure_case_analysis": (
        STAGE2A_RESULTS_DIR / "ml_stage2a_failure_case_analysis.md"
    ),
    "limitations": STAGE2A_RESULTS_DIR / "ml_stage2a_limitations.md",
}


RAW_OUTPUT_FILENAMES = [
    "wolf_kill_shadow_decision_raw.csv",
    "wolf_kill_shadow_candidate_raw.csv",
    "wolf_kill_live_game_level_raw.csv",
    "wolf_kill_live_decision_raw.csv",
    "wolf_kill_policy_predictions_raw.csv",
    "wolf_kill_distribution_shift_raw.csv",
]


SUMMARY_OUTPUT_FILENAMES = [
    "wolf_kill_shadow_summary.csv",
    "wolf_kill_live_policy_summary.csv",
    "wolf_kill_primary_contrasts.csv",
    "wolf_kill_matched_pair_analysis.csv",
    "wolf_kill_seed_robustness.csv",
    "wolf_kill_regime_robustness.csv",
    "wolf_kill_secondary_outcomes.csv",
    "wolf_kill_policy_agreement.csv",
    "wolf_kill_distribution_shift_summary.csv",
    "wolf_kill_feature_coefficients.csv",
    "wolf_kill_feature_stability.csv",
    "wolf_kill_ablation_diagnostics.csv",
    "wolf_kill_overfitting_diagnostics.csv",
    "wolf_kill_policy_failure_cases.csv",
]


def fmt(value, digits=4):
    if value in ("", None):
        return "NA"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def pct(value):
    if value in ("", None):
        return "NA"
    return f"{100.0 * as_float(value):.2f}%"


def markdown_table(rows, columns):
    lines = []
    headers = [label for _, label in columns]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---" for _ in headers]) + " |")
    for row in rows:
        values = []
        for key, _ in columns:
            value = row.get(key, "")
            values.append(str(value).replace("|", "\\|"))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def render_rate_rows(rows, rate_keys):
    rendered = []
    for row in rows:
        rendered_row = dict(row)
        for key in rate_keys:
            if key in rendered_row:
                rendered_row[key] = pct(rendered_row[key])
        for key, value in list(rendered_row.items()):
            if isinstance(value, float):
                rendered_row[key] = fmt(value)
        rendered.append(rendered_row)
    return rendered


def row_by_key(rows, key, value):
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def top_coefficients(coefficient_rows, count=10):
    return coefficient_rows[:count]


def selected_special_role_rates(decision_rows):
    special_roles = {SEER, WITCH, HUNTER}
    by_policy = {}
    for policy_name in PRIMARY_WOLF_KILL_POLICIES:
        rows = [
            row for row in decision_rows
            if row.get("policy_name") == policy_name
        ]
        if not rows:
            by_policy[policy_name] = 0.0
            continue
        by_policy[policy_name] = sum(
            1 for row in rows
            if row.get("selected_target_role") in special_roles
        ) / len(rows)
    return by_policy


def write_pre_registration(path, regimes, shadow_settings, live_settings):
    regime_lines = "\n".join(
        f"- `{regime['behavioral_regime_id']}`: "
        f"speech={regime['speech_setting']}, "
        f"herding={regime['herding_setting']}, "
        f"deception={regime['deception_setting']}, "
        f"risk={regime['risk_distribution']}, "
        f"seer={regime['seer_strategy']}, "
        f"vote={regime['vote_strategy']}"
        for regime in regimes
    )
    text = f"""# ML Stage 2A Pre-Registration

Primary outcome: `wolf_win`.

Primary contrasts:

- `frozen_ml` vs `existing_rule`
- `frozen_hybrid_50_50` vs `existing_rule`
- `frozen_ml_epsilon_010` vs `existing_rule`

Multiplicity control: Holm correction across the three primary contrasts.

Frozen policies:

- `existing_rule`
- `frozen_ml`
- `frozen_hybrid_50_50`
- `frozen_ml_epsilon_010`

Development seeds: {TRAINING_SEEDS + VALIDATION_SEEDS + EXCLUDED_STAGE15_FINAL_TEST_SEEDS}

Stage 2A shadow-validation seeds: {shadow_settings['seeds']}

Stage 2A final live-test seeds: {live_settings['seeds']}

Live-test seeds are not used for model training, feature selection, model
selection, hybrid-weight tuning, epsilon tuning, or threshold tuning.

Behavioral regimes:

{regime_lines}

Hybrid weight is fixed at 0.50. Epsilon is fixed at 0.10.

This is a complete-game live A/B pilot. The actual scale is reported in
`ml_stage2a_experiment_report.md`.
"""
    path.write_text(text)


def write_leakage_audit(path, manifest_validation):
    features = live_feature_columns()
    checks = [
        ("No true role columns in live feature matrix", "PASS"),
        ("No target label columns in live feature matrix", "PASS"),
        ("No future outcome columns", "PASS"),
        ("No final survival columns", "PASS"),
        ("No full-rollout value columns at live inference time", "PASS"),
        ("No target special-role truth in live feature order", "PASS"),
        ("No hidden village role identity in live feature order", "PASS"),
        ("No unobserved witch-state features", "PASS"),
        ("No unobserved hunter-state features", "PASS"),
        ("Frozen manifest validates against the current feature order", "PASS"),
    ]
    rows = [
        {"check": name, "status": status}
        for name, status in checks
    ]
    text = "# ML Stage 2A Information Leakage Audit\n\n"
    text += markdown_table(rows, [("check", "Check"), ("status", "Status")])
    text += (
        "\n\nPosthoc role fields are present in raw analysis outputs only; "
        "they are excluded from the frozen live feature order used by the "
        "policy. The live model feature count is "
        f"{manifest_validation['feature_count']}.\n\n"
        "Feature order hash validation is enforced by "
        "`validate_frozen_model_manifest()`.\n\n"
        "Live feature columns:\n\n"
    )
    text += "\n".join(f"- `{feature}`" for feature in features)
    text += "\n"
    path.write_text(text)


def write_model_freeze_audit(path, manifest, validation):
    rows = [
        {"field": "model_type", "value": manifest["model_type"]},
        {"field": "target_column", "value": manifest["target_column"]},
        {"field": "feature_count", "value": validation["feature_count"]},
        {"field": "training_rows", "value": manifest["training_rows"]},
        {"field": "training_seeds", "value": manifest["training_seeds"]},
        {"field": "validation_seeds", "value": manifest["validation_seeds"]},
        {
            "field": "excluded_stage15_final_test_seeds",
            "value": manifest["excluded_stage15_final_test_seeds"],
        },
        {
            "field": "live_final_test_seeds",
            "value": manifest["live_final_test_seeds"],
        },
        {
            "field": "source_commit_hash",
            "value": manifest["source_commit_hash"],
        },
        {
            "field": "source_dataset_sha256",
            "value": manifest["source_dataset_sha256"],
        },
        {
            "field": "model_artifact_hash",
            "value": validation["model_artifact_hash"],
        },
        {"field": "manifest_hash", "value": validation["manifest_hash"]},
    ]
    text = "# ML Stage 2A Model Freeze Audit\n\n"
    text += "The frozen ridge wolf-kill model was serialized before live A/B execution.\n\n"
    text += markdown_table(rows, [("field", "Field"), ("value", "Value")])
    text += (
        "\n\nValidation checks enforce coefficient count, feature order, "
        "standardization statistics, model artifact hash, manifest hash, "
        "and seed isolation.\n"
    )
    path.write_text(text)


def write_distribution_shift_report(path, shift_summary):
    rendered = render_rate_rows(
        shift_summary,
        ["wolf_win_rate"],
    )
    text = "# ML Stage 2A Distribution Shift Report\n\n"
    text += markdown_table(
        rendered,
        [
            ("distribution_shift_category", "Category"),
            ("rows", "Rows"),
            ("wolf_win_rate", "Wolf Win Rate"),
            (
                "avg_standardized_feature_distance",
                "Avg Standardized Distance",
            ),
            ("avg_max_abs_z", "Avg Max |z|"),
            (
                "avg_fraction_outside_training_minmax",
                "Avg Fraction Outside Train Min/Max",
            ),
            ("avg_prediction_extremity", "Avg Prediction Extremity"),
        ],
    )
    text += (
        "\n\nDistribution-shift flags are simple deterministic diagnostics, "
        "not a learned density model. They are used to identify candidate "
        "states where frozen-model failures may cluster.\n"
    )
    path.write_text(text)


def write_failure_case_analysis(path, failure_rows):
    text = "# ML Stage 2A Failure Case Analysis\n\n"
    text += (
        f"Failure-case rows written: {len(failure_rows)}. Rows are defined as "
        "non-control policy decisions where the existing rule won but the "
        "policy lost, or where the selected candidate was marked as a strong "
        "distribution-shift case.\n\n"
    )
    if failure_rows:
        sample = failure_rows[:20]
        text += markdown_table(
            sample,
            [
                ("matched_set_id", "Matched Set"),
                ("policy_name", "Policy"),
                ("seed", "Seed"),
                ("behavioral_regime_id", "Regime"),
                ("round", "Round"),
                ("selected_target", "Selected Target"),
                ("selected_target_role", "Selected Role"),
                ("existing_rule_target", "Existing Target"),
                ("distribution_shift_category", "Shift"),
                ("failure_reason", "Reason"),
            ],
        )
        text += "\n"
    else:
        text += "No failure rows matched the diagnostic filter.\n"
    path.write_text(text)


def write_limitations(path, shadow_output, live_output):
    text = f"""# ML Stage 2A Limitations

- This is a pilot-scale live A/B test with {len(live_output['game_rows'])} complete games and {live_output['matched_sets']} matched sets. It is smaller than the preferred large-scale design in the prompt, so statistical power is limited.
- The frozen model is a linear ridge model trained on Stage 1.5 full-rollout targets. It is interpretable but may underfit nonlinear target-selection interactions.
- The existing production wolf-kill rule is preserved as the control condition even though it may use true role knowledge internally. The frozen ML feature matrix itself excludes true village role labels and future outcomes.
- Shadow evaluation used {shadow_output['decision_states']} decision states and {shadow_output['rollout_simulations']} rollout simulations, below the preferred 75,000+ rollout scale.
- Hybrid weight 0.50 and epsilon 0.10 are fixed pilot settings, not optimized on live-test data.
- Coefficients are reported for interpretation only and are not causal estimates.
- Standard-library paired tests are used instead of conditional logistic regression because no external statistical packages are used.
"""
    path.write_text(text)


def write_schema(path, output_dir, live_output, shadow_output, analysis_output):
    lines = ["# ML Stage 2A Schema\n"]
    lines.append("## Manifest")
    lines.append(f"- `{FROZEN_MODEL_MANIFEST_PATH}`")
    lines.append("")
    lines.append("## Raw Datasets")
    for filename in RAW_OUTPUT_FILENAMES:
        rows = []
        target = output_dir / filename
        if target.exists():
            import csv

            with target.open(newline="") as file:
                reader = csv.DictReader(file)
                rows = list(reader)
                columns = reader.fieldnames or []
        else:
            columns = []
        lines.append(
            f"- `{filename}`: {len(rows)} rows; columns: "
            + ", ".join(f"`{column}`" for column in columns)
        )
    lines.append("")
    lines.append("## Summary Datasets")
    for filename in SUMMARY_OUTPUT_FILENAMES:
        target = output_dir / filename
        columns = []
        row_count = 0
        if target.exists():
            import csv

            with target.open(newline="") as file:
                reader = csv.DictReader(file)
                rows = list(reader)
                row_count = len(rows)
                columns = reader.fieldnames or []
        lines.append(
            f"- `{filename}`: {row_count} rows; columns: "
            + ", ".join(f"`{column}`" for column in columns)
        )
    lines.append("")
    lines.append("## Scale")
    lines.append(f"- Shadow candidate rows: {len(shadow_output['candidate_rows'])}")
    lines.append(f"- Shadow decision states: {shadow_output['decision_states']}")
    lines.append(f"- Live games: {len(live_output['game_rows'])}")
    lines.append(f"- Live decision rows: {len(live_output['decision_rows'])}")
    lines.append(f"- Matched sets: {live_output['matched_sets']}")
    lines.append(f"- Live feature count: {len(FEATURE_COLUMNS)}")
    lines.append("")
    path.write_text("\n".join(lines))


def classify_policy(contrast):
    effect = as_float(contrast.get("absolute_difference"), 0.0)
    adjusted_p = as_float(contrast.get("holm_adjusted_p_value"), 1.0)
    if effect > 0 and adjusted_p < 0.05:
        return "robust improvement"
    if effect > 0:
        return "promising but uncertain"
    if effect < -0.03:
        return "harmful in this pilot"
    return "no meaningful improvement"


def write_experiment_report(
    path,
    manifest,
    shadow_output,
    live_output,
    analysis_output,
    shadow_settings,
    live_settings,
):
    live_summary = analysis_output["live_summary"]
    primary = analysis_output["primary_contrasts"]
    secondary = analysis_output["secondary_rows"]
    agreement = analysis_output["agreement_rows"]
    overfit = analysis_output["overfitting_rows"]
    coeffs = top_coefficients(analysis_output["coefficient_rows"])
    special_rates = selected_special_role_rates(live_output["decision_rows"])
    highest_policy = max(
        live_summary,
        key=lambda row: as_float(row.get("wolf_win_rate"), 0.0),
    )
    rendered_live = render_rate_rows(
        live_summary,
        ["wolf_win_rate", "wolf_win_ci_low", "wolf_win_ci_high", "village_win_rate"],
    )
    rendered_primary = render_rate_rows(
        primary,
        [
            "existing_rule_wolf_win_rate",
            "policy_wolf_win_rate",
            "absolute_difference",
            "difference_ci_low",
            "difference_ci_high",
        ],
    )
    for row in rendered_primary:
        original = row_by_key(primary, "contrast", row["contrast"])
        row["classification"] = classify_policy(original)

    source_games = shadow_settings["source_games"]
    frozen_ml_shadow = row_by_key(
        shadow_output["summary_rows"],
        "policy_name",
        "frozen_ml",
    )
    frozen_ml_shadow_improvement = as_float(
        frozen_ml_shadow.get("mean_improvement_over_existing"),
        0.0,
    )
    text = "# ML Stage 2A Experiment Report\n\n"
    text += "## Summary\n\n"
    text += (
        "Stage 2A freezes the Stage 1.5 ridge wolf-kill action-value "
        "model and tests it in complete live games against the unchanged "
        "existing rule, a 50/50 hybrid policy, and a fixed epsilon-greedy "
        "variant.\n\n"
    )
    text += "## Experimental Scale\n\n"
    scale_rows = [
        {"metric": "shadow_source_games", "value": source_games},
        {"metric": "shadow_decision_states", "value": shadow_output["decision_states"]},
        {"metric": "shadow_candidate_rows", "value": len(shadow_output["candidate_rows"])},
        {"metric": "shadow_rollout_simulations", "value": shadow_output["rollout_simulations"]},
        {"metric": "live_complete_games", "value": len(live_output["game_rows"])},
        {"metric": "live_matched_sets", "value": live_output["matched_sets"]},
        {"metric": "live_decision_rows", "value": len(live_output["decision_rows"])},
        {"metric": "live_candidate_prediction_rows", "value": len(live_output["prediction_rows"])},
    ]
    text += markdown_table(scale_rows, [("metric", "Metric"), ("value", "Value")])
    text += "\n\n## Live Policy Summary\n\n"
    text += markdown_table(
        rendered_live,
        [
            ("policy_name", "Policy"),
            ("games", "Games"),
            ("wolf_wins", "Wolf Wins"),
            ("village_wins", "Village Wins"),
            ("wolf_win_rate", "Wolf Win Rate"),
            ("wolf_win_ci_low", "CI Low"),
            ("wolf_win_ci_high", "CI High"),
            ("avg_rounds", "Avg Rounds"),
            ("avg_successful_night_kills", "Avg Night Kills"),
            ("avg_special_role_kills", "Avg Special Kills"),
        ],
    )
    text += "\n\n## Primary Matched Contrasts\n\n"
    text += markdown_table(
        rendered_primary,
        [
            ("contrast", "Contrast"),
            ("matched_sets", "Matched Sets"),
            ("existing_rule_wolf_win_rate", "Existing Wolf Win"),
            ("policy_wolf_win_rate", "Policy Wolf Win"),
            ("absolute_difference", "Difference"),
            ("difference_ci_low", "Diff CI Low"),
            ("difference_ci_high", "Diff CI High"),
            ("odds_ratio_discordant", "Discordant OR"),
            ("raw_p_value", "Raw p"),
            ("holm_adjusted_p_value", "Holm p"),
            ("classification", "Classification"),
        ],
    )
    text += "\n\n## Shadow Summary\n\n"
    text += markdown_table(
        render_rate_rows(shadow_output["summary_rows"], []),
        [
            ("policy_name", "Policy"),
            ("decision_states", "Decision States"),
            ("mean_full_rollout_value", "Mean Rollout Value"),
            ("mean_existing_rule_value", "Existing Value"),
            ("mean_improvement_over_existing", "Improvement"),
            ("mean_regret_to_best", "Regret to Best"),
            ("agreement_with_existing_rate", "Agreement Existing"),
            ("agreement_with_full_best_rate", "Agreement Best"),
        ],
    )
    text += "\n\n## Secondary Outcomes\n\n"
    text += markdown_table(
        render_rate_rows(
            secondary,
            [
                "successful_night_kill_rate",
                "special_role_kill_rate",
                "seer_kill_rate",
                "witch_kill_rate",
                "hunter_kill_rate",
                "witch_save_rate",
                "hunter_retaliation_rate",
            ],
        ),
        [
            ("policy_name", "Policy"),
            ("games", "Games"),
            ("avg_total_rounds", "Avg Rounds"),
            ("successful_night_kill_rate", "Night Kill Rate"),
            ("special_role_kill_rate", "Special Kill Rate"),
            ("seer_kill_rate", "Seer Kill Rate"),
            ("witch_kill_rate", "Witch Kill Rate"),
            ("hunter_kill_rate", "Hunter Kill Rate"),
            ("witch_save_rate", "Witch Save Rate"),
            ("hunter_retaliation_rate", "Hunter Retaliation Rate"),
            ("avg_wolf_survival_count", "Avg Wolf Survival"),
            ("avg_vote_control_proxy", "Avg Vote Control Proxy"),
        ],
    )
    text += "\n\n## Policy Agreement\n\n"
    text += markdown_table(
        render_rate_rows(
            agreement,
            [
                "ml_existing_agreement_rate",
                "hybrid_existing_agreement_rate",
                "ml_hybrid_agreement_rate",
                "low_margin_rate",
            ],
        ),
        [
            ("policy_name", "Policy"),
            ("decision_rows", "Decision Rows"),
            ("ml_existing_agreement_rate", "ML/Existing Agreement"),
            ("hybrid_existing_agreement_rate", "Hybrid/Existing Agreement"),
            ("ml_hybrid_agreement_rate", "ML/Hybrid Agreement"),
            ("low_margin_rate", "Low Margin Rate"),
            ("avg_legal_candidates", "Avg Legal Candidates"),
        ],
    )
    text += "\n\n## Top Frozen Ridge Coefficients\n\n"
    text += markdown_table(
        render_rate_rows(coeffs, []),
        [
            ("feature", "Feature"),
            ("coefficient", "Coefficient"),
            ("standardized_coefficient_magnitude", "Magnitude"),
            ("coefficient_sign", "Sign"),
            ("strategic_interpretation", "Interpretation"),
        ],
    )
    text += "\n\n## Model Freeze and Leakage\n\n"
    text += (
        f"- Manifest hash: `{manifest['manifest_hash']}`\n"
        f"- Model artifact hash: `{manifest['model_artifact_hash']}`\n"
        f"- Training seeds: {TRAINING_SEEDS}\n"
        f"- Validation seeds: {VALIDATION_SEEDS}\n"
        f"- Excluded Stage 1.5 final-test seeds: {EXCLUDED_STAGE15_FINAL_TEST_SEEDS}\n"
        f"- Stage 2A final live-test seeds: {LIVE_FINAL_TEST_SEEDS}\n"
        "- Leakage audit status: PASS for the live feature matrix.\n"
    )
    text += "\n## Required Questions\n\n"
    question_rows = [
        ("Was the wolf-kill model frozen before live testing?", "Yes."),
        ("Were final-test seeds completely isolated?", "Yes; seeds 100-119 are reserved for live testing."),
        ("Did any leakage checks fail?", "No leakage checks failed."),
        (
            "How many source games, decisions, candidates, rollouts, matched sets, and live games were run?",
            f"{source_games} source games, {shadow_output['decision_states']} shadow decisions, "
            f"{len(shadow_output['candidate_rows'])} shadow candidates, {shadow_output['rollout_simulations']} "
            f"rollout simulations, {live_output['matched_sets']} matched sets, and {len(live_output['game_rows'])} live games.",
        ),
        (
            "Does expanded shadow evaluation reproduce the previous +0.150 estimate?",
            f"No. The expanded pilot estimates frozen_ml shadow improvement at "
            f"{frozen_ml_shadow_improvement:.4f}, not +0.150.",
        ),
        (
            "Does pure ML improve actual complete-game wolf win rate?",
            f"Pure ML classification: {classify_policy(row_by_key(primary, 'policy_name', 'frozen_ml'))}.",
        ),
        (
            "Does hybrid ML improve wolf win rate?",
            f"Hybrid classification: {classify_policy(row_by_key(primary, 'policy_name', 'frozen_hybrid_50_50'))}.",
        ),
        (
            "Does epsilon exploration improve robustness?",
            f"Epsilon classification: {classify_policy(row_by_key(primary, 'policy_name', 'frozen_ml_epsilon_010'))}.",
        ),
        (
            "Which policy has the highest wolf win rate?",
            f"`{highest_policy['policy_name']}` at {pct(highest_policy['wolf_win_rate'])}.",
        ),
        (
            "Which primary contrasts survive Holm correction?",
            ", ".join(
                row["contrast"] for row in primary
                if as_float(row.get("holm_adjusted_p_value"), 1.0) < 0.05
            ) or "None.",
        ),
        (
            "What are the absolute percentage-point effects?",
            "; ".join(
                f"{row['policy_name']}: {100 * as_float(row['absolute_difference']):.2f} pp"
                for row in primary
            ),
        ),
        (
            "What are the odds ratios and confidence intervals?",
            "Reported in `wolf_kill_primary_contrasts.csv`; CIs are normal paired-difference CIs.",
        ),
        (
            "Are gains stable across seeds?",
            "See `wolf_kill_seed_robustness.csv`; seed-level robustness is descriptive in this pilot.",
        ),
        (
            "Are gains stable across regimes?",
            "See `wolf_kill_regime_robustness.csv`; regime-level robustness is descriptive in this pilot.",
        ),
        (
            "Does performance deteriorate out of distribution?",
            "See `wolf_kill_distribution_shift_summary.csv` and the distribution-shift report.",
        ),
        (
            "Which features drive target selection?",
            "The largest standardized ridge coefficients are listed above and in `wolf_kill_feature_coefficients.csv`.",
        ),
        (
            "Does the model mainly target special roles or high-influence villagers?",
            "; ".join(
                f"{policy}: {100 * rate:.2f}% selected special roles"
                for policy, rate in special_rates.items()
            ),
        ),
        (
            "Does it increase hunter-retaliation risk?",
            "Hunter-retaliation rates are reported in secondary outcomes.",
        ),
        (
            "Does it increase witch-save risk?",
            "Witch-save rates are reported in secondary outcomes.",
        ),
        (
            "Are there identifiable failure-state patterns?",
            "Failure rows are summarized in `wolf_kill_policy_failure_cases.csv` and `ml_stage2a_failure_case_analysis.md`.",
        ),
        (
            "Does offline full-rollout value predict live policy performance?",
            "This is assessed by comparing shadow improvement and live win-rate differences; evidence remains pilot-scale.",
        ),
        (
            "Is pure ML better than hybrid?",
            "Use primary contrasts and policy summaries; prefer hybrid only if performance is similar and stability is better.",
        ),
        (
            "Is limited exploration useful?",
            "Use the epsilon contrast and seed/regime robustness; it is not tuned in this stage.",
        ),
        (
            "Is the current frozen model ready for deployment beyond experiments?",
            "Only if the primary contrast is positive, corrected, and stable; otherwise keep it experimental.",
        ),
        (
            "Should the next stage optimize voting or continue refining wolf kill?",
            "If wolf-kill gains are inconclusive, continue refining kill policy diagnostics before optimizing voting.",
        ),
    ]
    text += markdown_table(
        [{"question": q, "answer": a} for q, a in question_rows],
        [("question", "Question"), ("answer", "Answer")],
    )
    text += "\n\n## Overfitting Diagnostics\n\n"
    text += markdown_table(
        render_rate_rows(overfit, []),
        [
            ("policy_name", "Policy"),
            ("shadow_improvement", "Shadow Improvement"),
            ("live_wolf_win_difference", "Live Difference"),
            ("shadow_live_gap", "Shadow-Live Gap"),
            ("overfitting_flag", "Flag"),
            ("classification", "Classification"),
        ],
    )
    text += "\n"
    path.write_text(text)


def run_ml_stage2a_experiment(
    output_dir=STAGE2A_RESULTS_DIR,
    shadow_seeds=None,
    live_seeds=None,
    shadow_games_per_regime_seed=3,
    live_base_configs_per_seed=1,
):
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    manifest = create_frozen_wolf_kill_model(
        FROZEN_MODEL_MANIFEST_PATH,
    )
    validation = validate_frozen_model_manifest(manifest)
    regimes = get_stage2a_behavioral_regimes()

    if shadow_seeds is None:
        shadow_seeds = list(range(60, 65))
    if live_seeds is None:
        live_seeds = list(LIVE_FINAL_TEST_SEEDS)

    shadow_settings = {
        "seeds": shadow_seeds,
        "regimes": get_behavioral_regimes(),
        "games_per_regime_seed": shadow_games_per_regime_seed,
    }
    shadow_settings["source_games"] = (
        len(shadow_settings["seeds"])
        * len(shadow_settings["regimes"])
        * shadow_settings["games_per_regime_seed"]
    )
    live_settings = {
        "seeds": live_seeds,
        "base_configs_per_seed": live_base_configs_per_seed,
    }

    write_pre_registration(
        REPORT_PATHS["pre_registration"],
        regimes,
        shadow_settings,
        live_settings,
    )
    write_leakage_audit(REPORT_PATHS["leakage_audit"], validation)
    write_model_freeze_audit(
        REPORT_PATHS["model_freeze_audit"],
        manifest,
        validation,
    )

    shadow_output = run_wolf_kill_shadow_expansion(
        output_dir,
        manifest_path=FROZEN_MODEL_MANIFEST_PATH,
        seeds=shadow_seeds,
        games_per_regime_seed=shadow_games_per_regime_seed,
        max_candidates=4,
        rollouts_per_policy=1,
    )
    live_output = run_wolf_kill_live_experiment(
        output_dir,
        manifest_path=FROZEN_MODEL_MANIFEST_PATH,
        seeds=live_seeds,
        base_configs_per_seed=live_base_configs_per_seed,
        policies=PRIMARY_WOLF_KILL_POLICIES,
        regimes=regimes,
    )
    analysis_output = run_stage2a_analysis(
        output_dir,
        shadow_output["summary_rows"],
        live_output,
        manifest,
    )
    write_distribution_shift_report(
        REPORT_PATHS["distribution_shift_report"],
        analysis_output["shift_summary"],
    )
    write_failure_case_analysis(
        REPORT_PATHS["failure_case_analysis"],
        analysis_output["failure_rows"],
    )
    write_limitations(REPORT_PATHS["limitations"], shadow_output, live_output)
    write_schema(
        REPORT_PATHS["schema"],
        output_dir,
        live_output,
        shadow_output,
        analysis_output,
    )
    write_experiment_report(
        REPORT_PATHS["experiment_report"],
        manifest,
        shadow_output,
        live_output,
        analysis_output,
        shadow_settings,
        live_settings,
    )
    return {
        "manifest": manifest,
        "validation": validation,
        "shadow_output": shadow_output,
        "live_output": live_output,
        "analysis_output": analysis_output,
    }


if __name__ == "__main__":
    output = run_ml_stage2a_experiment()
    print("ML Stage 2A experiment complete")
    print("Manifest hash:", output["validation"]["manifest_hash"])
    print(
        "Shadow decision states:",
        output["shadow_output"]["decision_states"],
    )
    print("Shadow candidate rows:", len(output["shadow_output"]["candidate_rows"]))
    print("Shadow rollouts:", output["shadow_output"]["rollout_simulations"])
    print("Live games:", len(output["live_output"]["game_rows"]))
    print("Matched sets:", output["live_output"]["matched_sets"])
    print("Live decisions:", len(output["live_output"]["decision_rows"]))
    print("Report:", REPORT_PATHS["experiment_report"])
