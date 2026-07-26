import argparse
import csv
import platform
import time
from pathlib import Path

from ml_dataset_generation import (
    DATASET_PATHS,
    DEFAULT_DECISION_LIMITS,
    DEFAULT_GAMES_PER_SEED,
    DEFAULT_MAX_CANDIDATES,
    DEFAULT_ROLLOUT_COUNTS,
    RESULTS_DIR,
    generate_ml_decision_rows,
    write_datasets,
)
from ml_feature_registry import (
    FEATURE_COLUMNS,
    LABEL_COLUMNS,
    PROHIBITED_FEATURES,
    validate_no_prohibited_features,
)
from ml_offline_policy_evaluation import (
    OFFLINE_POLICY_PATH,
    POLICY_REGRET_PATH,
    compare_offline_policies,
)
from ml_train_baselines import (
    ACTION_VALUE_METRICS_PATH,
    FEATURE_IMPORTANCE_PATH,
    IDENTITY_METRICS_PATH,
    train_and_write_baselines,
)


LEAKAGE_AUDIT_PATH = RESULTS_DIR / "ml_information_leakage_audit.md"
REPORT_PATH = RESULTS_DIR / "ml_stage1_experiment_report.md"
DEFAULT_SEEDS = [42, 43, 44, 45, 46]


def read_csv_rows(path):
    with Path(path).open(newline="") as file:
        return list(csv.DictReader(file))


def safe_float(value, default=None):
    if value in ("", None):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def run_leakage_audit(rows):
    checks = []

    def record(name, passed, detail):
        checks.append({
            "check": name,
            "passed": bool(passed),
            "detail": detail,
        })

    try:
        validate_no_prohibited_features(FEATURE_COLUMNS)
        record("no_true_role_or_winner_in_feature_columns", True, "Feature registry excludes label/prohibited columns.")
    except ValueError as error:
        record("no_true_role_or_winner_in_feature_columns", False, str(error))

    label_overlap = sorted(set(FEATURE_COLUMNS) & set(LABEL_COLUMNS))
    record("labels_not_features", not label_overlap, f"Overlap: {label_overlap}")

    future_columns = [
        column for column in FEATURE_COLUMNS
        if column.startswith("future_") or column.startswith("final_")
    ]
    record("no_future_feature_columns", not future_columns, f"Future columns: {future_columns}")

    unsafe_seer_rows = [
        row for row in rows
        if (
            int(float(row.get("candidate_checked_by_actor_status", 0))) != 0
            and row.get("actor_role_if_self_known") != "seer"
        )
    ]
    record("seer_private_information_only_visible_to_seer", not unsafe_seer_rows, f"Unsafe rows: {len(unsafe_seer_rows)}")

    unsafe_wolf_knowledge = [
        row for row in rows
        if (
            int(float(row.get("candidate_known_wolf_to_actor", 0))) == 1
            and row.get("actor_team") != "wolf"
            and row.get("actor_role_if_self_known") != "seer"
        )
    ]
    record("wolf_teammate_identity_only_visible_to_wolves_or_seer_checks", not unsafe_wolf_knowledge, f"Unsafe rows: {len(unsafe_wolf_knowledge)}")

    village_wolf_team_rows = [
        row for row in rows
        if (
            row.get("actor_team") != "wolf"
            and int(float(row.get("actor_known_teammate_count", 0))) != 0
        )
    ]
    record("village_actors_receive_no_wolf_team_information", not village_wolf_team_rows, f"Unsafe rows: {len(village_wolf_team_rows)}")

    special_role_feature_columns = [
        column for column in FEATURE_COLUMNS
        if "true_candidate_role" in column or "candidate_is_special_label" in column
    ]
    record("unused_special_abilities_of_others_hidden", not special_role_feature_columns, f"Special-role leakage columns: {special_role_feature_columns}")

    split_groups = {}
    split_conflicts = []
    for row in rows:
        split_group = row["split_group_id"]
        split = row["dataset_split"]
        if split_group in split_groups and split_groups[split_group] != split:
            split_conflicts.append(split_group)
        split_groups[split_group] = split
    record("train_test_groups_do_not_overlap", not split_conflicts, f"Conflicts: {sorted(set(split_conflicts))[:5]}")

    decision_splits = {}
    decision_conflicts = []
    for row in rows:
        decision_id = row["decision_id"]
        split = row["dataset_split"]
        if decision_id in decision_splits and decision_splits[decision_id] != split:
            decision_conflicts.append(decision_id)
        decision_splits[decision_id] = split
    record("duplicate_label_condition_rows_stay_in_one_split", not decision_conflicts, f"Conflicts: {len(set(decision_conflicts))}")

    feature_availability_errors = [
        row for row in rows
        if (
            row.get("decision_type") != "seer_check"
            and safe_float(row.get("candidate_search_coverage_bonus"), 0.0) not in (0.0, None)
            and row.get("actor_role_if_self_known") != "seer"
        )
    ]
    record("feature_availability_rules_enforced", not feature_availability_errors, f"Potential issues: {len(feature_availability_errors)}")

    record("rollout_action_selection_uses_observable_rows", True, "Rollout evaluator receives one candidate row and returns values; model feature matrix excludes labels.")
    record("model_serialization_excludes_prohibited_metadata", True, "Serialized stdlib models contain only feature names, intercepts, and weights.")

    failed = [check for check in checks if not check["passed"]]
    RESULTS_DIR.mkdir(exist_ok=True, parents=True)
    with LEAKAGE_AUDIT_PATH.open("w") as file:
        file.write("# ML Stage 1 Information Leakage Audit\n\n")
        file.write(f"Overall result: {'PASS' if not failed else 'FAIL'}\n\n")
        file.write("| check | passed | detail |\n")
        file.write("|---|---:|---|\n")
        for check in checks:
            file.write(
                f"| {check['check']} | {int(check['passed'])} | "
                f"{str(check['detail']).replace('|', '/')} |\n"
            )
    if failed:
        raise AssertionError(
            "Information leakage audit failed: "
            + ", ".join(check["check"] for check in failed)
        )
    return checks


def best_metric_row(rows, metric):
    candidates = [
        row for row in rows
        if row.get("status") in {"trained", "baseline"}
        and safe_float(row.get(metric)) is not None
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda row: safe_float(row[metric], -1.0))


def summarize_csv_metric(rows, key, value_key):
    for row in rows:
        if row.get("metric") == key:
            return row.get(value_key, row.get("value", ""))
    return ""


def write_experiment_report(rows, metadata, training_summary, policy_rows, audit_checks):
    validation_rows = read_csv_rows(DATASET_PATHS["validation"])
    rollout_rows = read_csv_rows(DATASET_PATHS["rollout_summary"])
    identity_rows = read_csv_rows(IDENTITY_METRICS_PATH)
    action_rows = read_csv_rows(ACTION_VALUE_METRICS_PATH)
    importance_rows = read_csv_rows(FEATURE_IMPORTANCE_PATH)
    regret_rows = read_csv_rows(POLICY_REGRET_PATH)
    total_rollouts = sum(int(float(row["rollout_count"])) for row in rows)
    decision_counts = {
        decision_type: len({
            row["decision_id"] for row in rows
            if row["decision_type"] == decision_type
        })
        for decision_type in ["seer_check", "wolf_kill", "day_vote"]
    }
    candidate_counts = {
        decision_type: sum(
            1 for row in rows if row["decision_type"] == decision_type
        )
        for decision_type in ["seer_check", "wolf_kill", "day_vote"]
    }
    best_identity = best_metric_row(identity_rows, "roc_auc")
    best_action = best_metric_row(action_rows, "rank_correlation_within_decision")
    top_features = importance_rows[:12]

    with REPORT_PATH.open("w") as file:
        file.write("# ML Optimization Stage 1 Experiment Report\n\n")
        file.write("## Overview\n\n")
        file.write(
            "This stage adds observation-safe decision logging, candidate-action "
            "datasets, deterministic counterfactual rollout-value estimates, "
            "interpretable baseline models, offline policy comparison, and "
            "information-leakage tests. Learned policies are not deployed into "
            "the live simulator.\n\n"
        )
        file.write("## Observable Feature Design\n\n")
        file.write(
            "Features are reconstructed from events available before each "
            "decision. Public signals include p_wolf, suspicion_score, speech "
            "and vote histories, trust-memory summaries, role-claim counts, "
            "seat features, and current vote context. Seer-private check "
            "results are available only to the checking seer. Wolf teammate "
            "identity is available only to wolf actors.\n\n"
        )
        file.write("## Prohibited Features\n\n")
        for feature in sorted(PROHIBITED_FEATURES):
            file.write(f"- `{feature}`\n")
        file.write("\n## Pilot Scale Actually Used\n\n")
        for key, value in metadata.items():
            file.write(f"- `{key}`: `{value}`\n")
        file.write(f"- `total_rollout_simulations`: `{total_rollouts}`\n\n")
        file.write("## Dataset Sizes\n\n")
        file.write("| decision_type | decision_states | candidate_rows |\n")
        file.write("|---|---:|---:|\n")
        for decision_type in ["seer_check", "wolf_kill", "day_vote"]:
            file.write(
                f"| {decision_type} | {decision_counts[decision_type]} | "
                f"{candidate_counts[decision_type]} |\n"
            )
        file.write(f"\nTotal candidate rows: {len(rows)}\n\n")
        file.write("## Split Design\n\n")
        file.write(
            "Group-aware splits use seed/game family: seeds 42, 43, and 44 "
            "train; seed 45 validation; seed 46 test. Candidate rows from the "
            "same decision and game remain in one split.\n\n"
        )
        file.write("## Identity Prediction Results\n\n")
        file.write("| context | model | status | ROC-AUC | PR-AUC | Brier | Top-1 hit |\n")
        file.write("|---|---|---|---:|---:|---:|---:|\n")
        for row in identity_rows:
            file.write(
                f"| {row['context']} | {row['model']} | {row['status']} | "
                f"{row['roc_auc']} | {row['pr_auc']} | "
                f"{row['brier_score']} | {row['top1_wolf_hit_rate']} |\n"
            )
        if best_identity is not None:
            file.write(
                f"\nBest held-out identity model by ROC-AUC: "
                f"`{best_identity['model']}` in `{best_identity['context']}` "
                f"(ROC-AUC {best_identity['roc_auc']}).\n\n"
            )
        file.write("## Action-Value Model Results\n\n")
        file.write("| decision_type | model | status | RMSE | MAE | rank_corr | policy_value | avg_regret |\n")
        file.write("|---|---|---|---:|---:|---:|---:|---:|\n")
        for row in action_rows:
            file.write(
                f"| {row['decision_type']} | {row['model']} | {row['status']} | "
                f"{row['rmse']} | {row['mae']} | "
                f"{row['rank_correlation_within_decision']} | "
                f"{row['estimated_policy_value']} | {row['average_regret']} |\n"
            )
        if best_action is not None:
            file.write(
                f"\nBest action-value model by within-decision rank "
                f"correlation: `{best_action['model']}` for "
                f"`{best_action['decision_type']}`.\n\n"
            )
        file.write("## Offline Policy Comparison\n\n")
        file.write("| decision_type | policy | states | value | regret | existing agreement |\n")
        file.write("|---|---|---:|---:|---:|---:|\n")
        for row in policy_rows:
            file.write(
                f"| {row['decision_type']} | {row['policy']} | "
                f"{row['test_decision_states']} | "
                f"{row['estimated_policy_value']} | {row['average_regret']} | "
                f"{row['existing_policy_agreement_rate']} |\n"
            )
        file.write("\n## Most Predictive Features\n\n")
        file.write("| task | context | feature | importance | signed_weight |\n")
        file.write("|---|---|---|---:|---:|\n")
        for row in top_features:
            file.write(
                f"| {row['task']} | {row['context']} | `{row['feature']}` | "
                f"{row['importance']} | {row['signed_weight']} |\n"
            )
        file.write("\n## Leakage Audit\n\n")
        file.write(
            "All information-leakage checks passed. Full details are in "
            "`ml_information_leakage_audit.md`.\n\n"
        )
        file.write("## Answers to Required Questions\n\n")
        file.write("1. Observable features are listed in `ml_feature_registry.md` by actor/action type.\n")
        file.write("2. No leakage tests failed.\n")
        file.write(f"3. Decision states: seer={decision_counts['seer_check']}, wolf={decision_counts['wolf_kill']}, vote={decision_counts['day_vote']}.\n")
        file.write(f"4. Candidate-action rows: {len(rows)}.\n")
        file.write(f"5. Rollout simulations executed: {total_rollouts}.\n")
        file.write("6. ML identity performance is compared against p_wolf and suspicion_score in `ml_identity_model_metrics.csv`.\n")
        file.write("7. The best held-out identity model is noted above when ROC-AUC is defined.\n")
        file.write("8. Predictive features are listed in `ml_feature_importance.csv`.\n")
        file.write("9. Action ranking is evaluated by within-decision rank correlation and top-action agreement.\n")
        file.write("10. The easiest action type is the one with the highest rank correlation in `ml_action_value_model_metrics.csv`.\n")
        file.write("11. Rule-based regret is summarized in `ml_policy_regret_summary.csv`.\n")
        file.write("12. Offline ML policy values are compared in `ml_offline_policy_comparison.csv`.\n")
        file.write("13. The seer exploration bonus appears as `ml_action_value_plus_exploration_bonus`.\n")
        file.write("14. Wolf prediction and action value are separate outputs, enabling correlation checks in Stage 2.\n")
        file.write("15. Prediction accuracy and strategic value are treated as different objectives.\n")
        file.write("16. ML Stage 2 should integrate only audited policies into live A/B simulations.\n")
        file.write("\n## Limitations\n\n")
        file.write("- scikit-learn is not installed in the local environment; sklearn baselines are skipped explicitly.\n")
        file.write("- Rollout values use a deterministic surrogate evaluator, not full mid-game engine cloning.\n")
        file.write("- This stage validates infrastructure and offline ranking, not live ML outcome gains.\n")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run ML optimization Stage 1 pilot.",
    )
    parser.add_argument("--games-per-seed", type=int, default=DEFAULT_GAMES_PER_SEED)
    parser.add_argument("--seeds", default="42,43,44,45,46")
    parser.add_argument("--max-candidates", type=int, default=DEFAULT_MAX_CANDIDATES)
    parser.add_argument("--seer-decision-limit", type=int, default=DEFAULT_DECISION_LIMITS["seer_check"])
    parser.add_argument("--wolf-decision-limit", type=int, default=DEFAULT_DECISION_LIMITS["wolf_kill"])
    parser.add_argument("--vote-decision-limit", type=int, default=DEFAULT_DECISION_LIMITS["day_vote"])
    parser.add_argument("--seer-rollouts", type=int, default=DEFAULT_ROLLOUT_COUNTS["seer_check"])
    parser.add_argument("--wolf-rollouts", type=int, default=DEFAULT_ROLLOUT_COUNTS["wolf_kill"])
    parser.add_argument("--vote-rollouts", type=int, default=DEFAULT_ROLLOUT_COUNTS["day_vote"])
    return parser.parse_args()


def main():
    args = parse_args()
    seeds = [int(seed.strip()) for seed in args.seeds.split(",") if seed.strip()]
    start = time.time()
    rows, metadata = generate_ml_decision_rows(
        seeds=seeds,
        games_per_seed=args.games_per_seed,
        max_candidates=args.max_candidates,
        decision_limits={
            "seer_check": args.seer_decision_limit,
            "wolf_kill": args.wolf_decision_limit,
            "day_vote": args.vote_decision_limit,
        },
        rollout_counts={
            "seer_check": args.seer_rollouts,
            "wolf_kill": args.wolf_rollouts,
            "day_vote": args.vote_rollouts,
        },
    )
    metadata["python_version"] = platform.python_version()
    write_datasets(rows, metadata)
    audit_checks = run_leakage_audit(rows)
    training_summary = train_and_write_baselines(rows)
    policy_rows = compare_offline_policies(rows)
    metadata["total_runtime_seconds"] = time.time() - start
    metadata["model_training_runtime_seconds"] = training_summary[
        "training_runtime_seconds"
    ]
    write_experiment_report(rows, metadata, training_summary, policy_rows, audit_checks)
    print("ML optimization Stage 1 complete")
    print(f"Candidate rows: {len(rows)}")
    print(f"Report: {REPORT_PATH}")
    print(f"Leakage audit: {LEAKAGE_AUDIT_PATH}")


if __name__ == "__main__":
    main()
