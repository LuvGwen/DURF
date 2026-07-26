import csv
import json
from collections import defaultdict

from config import DEFAULT_MAX_ROUNDS
from ml_behavioral_regimes import get_behavioral_regimes, get_continuation_policies
from ml_distribution_shift import calculate_distribution_shift
from ml_full_counterfactual_rollout import add_full_rollout_values
from ml_stage15_experiment import make_wolf_decision
from ml_train_baselines import as_float
from ml_wolf_kill_model_freeze import (
    FROZEN_MODEL_MANIFEST_PATH,
    load_json,
    predict_from_manifest,
    validate_frozen_model_manifest,
)
from ml_wolf_kill_policy import (
    DEFAULT_HYBRID_ML_WEIGHT,
    PRIMARY_WOLF_KILL_POLICIES,
    normalize_scores,
    observation_safe_rule_proxy_score,
)
from seat_order_neutral import stable_seed


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(exist_ok=True, parents=True)
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore",
            restval="",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def collect_shadow_wolf_kill_rows(
    seeds,
    games_per_regime_seed,
    max_candidates,
    rollouts_per_policy,
):
    rows = []
    snapshots = {}
    for regime in get_behavioral_regimes():
        for seed in seeds:
            for base_game_index in range(1, games_per_regime_seed + 1):
                new_rows, new_snapshots = make_wolf_decision(
                    seed=seed,
                    base_game_index=base_game_index,
                    regime=regime,
                    max_candidates=max_candidates,
                )
                rows.extend(new_rows)
                snapshots.update(new_snapshots)
    rows = add_full_rollout_values(
        rows,
        snapshots,
        get_continuation_policies(),
        rollouts_per_policy=rollouts_per_policy,
        rollout_seed=42,
        max_rounds=DEFAULT_MAX_ROUNDS,
    )
    for row in rows:
        row["full_rollout_policy_values_json"] = json.dumps(
            row.get("full_rollout_policy_values", {}),
            sort_keys=True,
        )
    return rows


def add_shadow_policy_scores(rows, manifest):
    by_decision = defaultdict(list)
    scored_rows = []
    for row in rows:
        prediction, detail = predict_from_manifest(manifest, row)
        scored = dict(row)
        scored["ml_predicted_wolf_value"] = prediction
        scored["missing_feature_count"] = detail["missing_feature_count"]
        scored["observation_safe_rule_proxy_score"] = (
            observation_safe_rule_proxy_score(scored)
        )
        by_decision[scored["decision_id"]].append(scored)
        scored_rows.append(scored)

    for decision_rows in by_decision.values():
        ml_scores = {
            row["candidate_uid"]: row["ml_predicted_wolf_value"]
            for row in decision_rows
        }
        rule_scores = {
            row["candidate_uid"]: row["observation_safe_rule_proxy_score"]
            for row in decision_rows
        }
        normalized_ml = normalize_scores(ml_scores)
        normalized_rule = normalize_scores(rule_scores)
        sorted_ml = sorted(
            decision_rows,
            key=lambda row: (
                -row["ml_predicted_wolf_value"],
                str(row["candidate_uid"]),
            ),
        )
        margin = 0.0
        if len(sorted_ml) >= 2:
            margin = (
                sorted_ml[0]["ml_predicted_wolf_value"]
                - sorted_ml[1]["ml_predicted_wolf_value"]
            )
        for row in decision_rows:
            row["normalized_ml_value"] = normalized_ml[row["candidate_uid"]]
            row["normalized_existing_rule_score"] = normalized_rule[
                row["candidate_uid"]
            ]
            row["hybrid_score"] = (
                DEFAULT_HYBRID_ML_WEIGHT * row["normalized_ml_value"]
                + (1.0 - DEFAULT_HYBRID_ML_WEIGHT)
                * row["normalized_existing_rule_score"]
            )
            row.update(calculate_distribution_shift(
                manifest,
                row,
                prediction=row["ml_predicted_wolf_value"],
                margin=margin,
            ))
    return scored_rows


def choose_best(rows, score_field):
    return sorted(
        rows,
        key=lambda row: (-as_float(row[score_field]), str(row["candidate_uid"])),
    )[0]


def choose_shadow_policy_row(decision_rows, policy_name):
    if policy_name == "existing_rule":
        selected = [
            row for row in decision_rows
            if int(row.get("action_selected_by_existing_policy", 0)) == 1
        ]
        return selected[0] if selected else decision_rows[0]
    if policy_name == "frozen_ml":
        return choose_best(decision_rows, "ml_predicted_wolf_value")
    if policy_name == "frozen_hybrid_50_50":
        return choose_best(decision_rows, "hybrid_score")
    if policy_name == "frozen_ml_epsilon_010":
        sorted_rows = sorted(
            decision_rows,
            key=lambda row: (
                -as_float(row["ml_predicted_wolf_value"]),
                str(row["candidate_uid"]),
            ),
        )
        seed = stable_seed(
            "stage2a_shadow_epsilon",
            sorted_rows[0]["decision_id"],
        )
        import random
        rng = random.Random(seed)
        if len(sorted_rows) > 1 and rng.random() < 0.10:
            return sorted_rows[1 + rng.randrange(len(sorted_rows) - 1)]
        return sorted_rows[0]
    raise ValueError(f"Unknown shadow policy: {policy_name}")


def summarize_shadow_policies(rows):
    decision_groups = defaultdict(list)
    for row in rows:
        decision_groups[row["decision_id"]].append(row)

    decision_raw = []
    for decision_id, decision_rows in decision_groups.items():
        existing = choose_shadow_policy_row(decision_rows, "existing_rule")
        best = choose_best(decision_rows, "full_rollout_mean_team_win_rate")
        for policy_name in PRIMARY_WOLF_KILL_POLICIES:
            selected = choose_shadow_policy_row(decision_rows, policy_name)
            decision_raw.append({
                "decision_id": decision_id,
                "game_id": selected["game_id"],
                "seed": selected["seed"],
                "base_game_index": selected["base_game_index"],
                "behavioral_regime_id": selected["behavioral_regime_id"],
                "policy_name": policy_name,
                "selected_candidate_uid": selected["candidate_uid"],
                "existing_rule_candidate_uid": existing["candidate_uid"],
                "full_rollout_best_candidate_uid": best["candidate_uid"],
                "selected_full_rollout_value": selected[
                    "full_rollout_mean_team_win_rate"
                ],
                "existing_rule_full_rollout_value": existing[
                    "full_rollout_mean_team_win_rate"
                ],
                "best_full_rollout_value": best[
                    "full_rollout_mean_team_win_rate"
                ],
                "improvement_over_existing": (
                    as_float(selected["full_rollout_mean_team_win_rate"])
                    - as_float(existing["full_rollout_mean_team_win_rate"])
                ),
                "regret_to_best": (
                    as_float(best["full_rollout_mean_team_win_rate"])
                    - as_float(selected["full_rollout_mean_team_win_rate"])
                ),
                "agrees_with_existing": (
                    1 if selected["candidate_uid"] == existing["candidate_uid"] else 0
                ),
                "agrees_with_full_best": (
                    1 if selected["candidate_uid"] == best["candidate_uid"] else 0
                ),
                "distribution_shift_category": selected[
                    "distribution_shift_category"
                ],
                "ml_prediction_margin": selected[
                    "candidate_ranking_margin"
                ],
            })

    summary_rows = []
    grouped = defaultdict(list)
    for row in decision_raw:
        grouped[row["policy_name"]].append(row)
    for policy_name, policy_rows in grouped.items():
        summary_rows.append({
            "policy_name": policy_name,
            "decision_states": len(policy_rows),
            "mean_full_rollout_value": mean(
                row["selected_full_rollout_value"]
                for row in policy_rows
            ),
            "mean_existing_rule_value": mean(
                row["existing_rule_full_rollout_value"]
                for row in policy_rows
            ),
            "mean_improvement_over_existing": mean(
                row["improvement_over_existing"]
                for row in policy_rows
            ),
            "mean_regret_to_best": mean(
                row["regret_to_best"] for row in policy_rows
            ),
            "agreement_with_existing_rate": mean(
                row["agrees_with_existing"] for row in policy_rows
            ),
            "agreement_with_full_best_rate": mean(
                row["agrees_with_full_best"] for row in policy_rows
            ),
        })
    return decision_raw, summary_rows


def mean(values):
    numeric = [as_float(value) for value in values]
    return sum(numeric) / len(numeric) if numeric else 0.0


def run_wolf_kill_shadow_expansion(
    output_dir,
    manifest_path=FROZEN_MODEL_MANIFEST_PATH,
    seeds=None,
    games_per_regime_seed=3,
    max_candidates=4,
    rollouts_per_policy=1,
):
    if seeds is None:
        seeds = list(range(60, 65))
    manifest = load_json(manifest_path)
    validate_frozen_model_manifest(manifest)
    rows = collect_shadow_wolf_kill_rows(
        seeds,
        games_per_regime_seed,
        max_candidates,
        rollouts_per_policy,
    )
    rows = add_shadow_policy_scores(rows, manifest)
    decision_raw, summary_rows = summarize_shadow_policies(rows)
    candidate_raw = []
    for row in rows:
        candidate_raw.append({
            key: value for key, value in row.items()
            if key != "_full_rollout_detail_rows"
        })
    write_csv(
        output_dir / "wolf_kill_shadow_candidate_raw.csv",
        candidate_raw,
        sorted({key for row in candidate_raw for key in row}),
    )
    write_csv(
        output_dir / "wolf_kill_shadow_decision_raw.csv",
        decision_raw,
        sorted({key for row in decision_raw for key in row}),
    )
    write_csv(
        output_dir / "wolf_kill_shadow_summary.csv",
        summary_rows,
        [
            "policy_name",
            "decision_states",
            "mean_full_rollout_value",
            "mean_existing_rule_value",
            "mean_improvement_over_existing",
            "mean_regret_to_best",
            "agreement_with_existing_rate",
            "agreement_with_full_best_rate",
        ],
    )
    return {
        "candidate_rows": candidate_raw,
        "decision_rows": decision_raw,
        "summary_rows": summary_rows,
        "source_seeds": seeds,
        "decision_states": len({row["decision_id"] for row in rows}),
        "rollout_simulations": sum(
            int(row.get("full_rollout_count", 0)) for row in rows
        ),
    }


if __name__ == "__main__":
    from pathlib import Path

    output = run_wolf_kill_shadow_expansion(
        Path("results") / "ml_optimization_stage2a"
    )
    print("Wolf-kill shadow expansion complete")
    print("Decision states:", output["decision_states"])
    print("Candidate rows:", len(output["candidate_rows"]))
