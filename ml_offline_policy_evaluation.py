from collections import defaultdict
from pathlib import Path

from ml_dataset_generation import DATASET_PATHS, RESULTS_DIR
from ml_decision_logger import write_csv_rows
from ml_train_baselines import (
    as_float,
    load_model,
    predict_logistic,
    predict_ridge,
    read_csv_rows,
)


OFFLINE_POLICY_PATH = RESULTS_DIR / "ml_offline_policy_comparison.csv"
POLICY_REGRET_PATH = RESULTS_DIR / "ml_policy_regret_summary.csv"


def group_by_decision(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["decision_id"]].append(row)
    return grouped


def choose_max(rows, score_function):
    return sorted(
        rows,
        key=lambda row: (
            score_function(row),
            str(row["candidate_uid"]),
        ),
        reverse=True,
    )[0]


def add_identity_predictions(rows):
    rows = [dict(row) for row in rows]
    model_paths = {
        "seer_candidate_states": (
            "identity_seer_candidate_states_logistic_stdlib.json"
        ),
        "village_vote_candidate_states": (
            "identity_village_vote_candidate_states_logistic_stdlib.json"
        ),
        "wolf_kill_candidate_states": (
            "identity_wolf_kill_candidate_states_logistic_stdlib.json"
        ),
    }
    context_rows = {
        "seer_candidate_states": [
            row for row in rows if row["decision_type"] == "seer_check"
        ],
        "village_vote_candidate_states": [
            row for row in rows
            if row["decision_type"] == "day_vote"
            and row["actor_team"] != "wolf"
        ],
        "wolf_kill_candidate_states": [
            row for row in rows if row["decision_type"] == "wolf_kill"
        ],
    }
    for context, subset in context_rows.items():
        path = RESULTS_DIR / "models" / model_paths[context]
        if not subset or not path.exists():
            for row in subset:
                row["ml_wolf_probability"] = as_float(
                    row.get("candidate_p_wolf"),
                    0.3,
                )
            continue
        model = load_model(path)
        predictions = predict_logistic(model, subset)
        for row, prediction in zip(subset, predictions):
            row["ml_wolf_probability"] = prediction
    for row in rows:
        row.setdefault(
            "ml_wolf_probability",
            as_float(row.get("candidate_p_wolf"), 0.3),
        )
    return rows


def add_action_value_predictions(rows):
    rows = [dict(row) for row in rows]
    for decision_type in ["seer_check", "wolf_kill", "day_vote"]:
        subset = [
            row for row in rows
            if row["decision_type"] == decision_type
        ]
        path = RESULTS_DIR / "models" / (
            f"action_value_{decision_type}_ridge_stdlib.json"
        )
        if not subset or not path.exists():
            for row in subset:
                row["ml_action_value"] = as_float(
                    row.get("rollout_team_win_rate"),
                    0.0,
                )
            continue
        model = load_model(path)
        predictions = predict_ridge(model, subset)
        for row, prediction in zip(subset, predictions):
            row["ml_action_value"] = prediction
    return rows


def policy_candidates_for_decision_type(decision_type):
    if decision_type == "seer_check":
        return {
            "existing_rule": lambda rows: [
                row for row in rows
                if int(row["action_selected_by_existing_policy"]) == 1
            ][0],
            "highest_existing_p_wolf": lambda rows: choose_max(
                rows,
                lambda row: as_float(row["candidate_p_wolf"], 0.0),
            ),
            "highest_existing_suspicion": lambda rows: choose_max(
                rows,
                lambda row: as_float(row["candidate_suspicion_score"], 0.0),
            ),
            "ml_highest_wolf_probability": lambda rows: choose_max(
                rows,
                lambda row: as_float(row["ml_wolf_probability"], 0.0),
            ),
            "ml_highest_action_value": lambda rows: choose_max(
                rows,
                lambda row: as_float(row["ml_action_value"], 0.0),
            ),
            "ml_action_value_plus_exploration_bonus": lambda rows: choose_max(
                rows,
                lambda row: (
                    as_float(row["ml_action_value"], 0.0)
                    + 0.10 * as_float(row["candidate_uncertainty_proxy"], 0.0)
                    + 0.10 * as_float(row["candidate_search_coverage_bonus"], 0.0)
                ),
            ),
            "epsilon_greedy_0_10_offline_expected": None,
        }
    if decision_type == "wolf_kill":
        return {
            "existing_wolf_strategy": lambda rows: [
                row for row in rows
                if int(row["action_selected_by_existing_policy"]) == 1
            ][0],
            "highest_threat_proxy": lambda rows: choose_max(
                rows,
                lambda row: (
                    as_float(row["candidate_survival_proxy"], 0.0)
                    + as_float(row["candidate_public_influence_proxy"], 0.0)
                    - as_float(row["candidate_suspicion_score"], 0.0)
                ),
            ),
            "highest_predicted_special_role_proxy": lambda rows: choose_max(
                rows,
                lambda row: (
                    as_float(row["candidate_role_claim_count"], 0.0)
                    + as_float(row["candidate_public_influence_proxy"], 0.0)
                ),
            ),
            "ml_highest_wolf_team_action_value": lambda rows: choose_max(
                rows,
                lambda row: as_float(row["ml_action_value"], 0.0),
            ),
        }
    return {
        "existing_voting_rule": lambda rows: [
            row for row in rows
            if int(row["action_selected_by_existing_policy"]) == 1
        ][0],
        "highest_suspicion": lambda rows: choose_max(
            rows,
            lambda row: as_float(row["candidate_suspicion_score"], 0.0),
        ),
        "highest_ml_wolf_probability_for_village": lambda rows: choose_max(
            rows,
            lambda row: as_float(row["ml_wolf_probability"], 0.0),
        ),
        "ml_highest_action_value": lambda rows: choose_max(
            rows,
            lambda row: as_float(row["ml_action_value"], 0.0),
        ),
        "wolf_team_ml_vote_value": lambda rows: choose_max(
            rows,
            lambda row: as_float(row["ml_action_value"], 0.0),
        ),
    }


def summarize_policy(decision_type, policy_name, selected_rows, all_decisions):
    if not selected_rows:
        return {
            "decision_type": decision_type,
            "policy": policy_name,
            "test_decision_states": 0,
            "estimated_policy_value": "",
            "average_regret": "",
            "existing_policy_agreement_rate": "",
        }
    values = [as_float(row["rollout_team_win_rate"]) for row in selected_rows]
    regrets = []
    agreements = []
    for row in selected_rows:
        decision_rows = all_decisions[row["decision_id"]]
        best_value = max(
            as_float(candidate["rollout_team_win_rate"])
            for candidate in decision_rows
        )
        regrets.append(best_value - as_float(row["rollout_team_win_rate"]))
        agreements.append(int(row["action_selected_by_existing_policy"]))
    return {
        "decision_type": decision_type,
        "policy": policy_name,
        "test_decision_states": len(selected_rows),
        "estimated_policy_value": sum(values) / len(values),
        "average_regret": sum(regrets) / len(regrets),
        "existing_policy_agreement_rate": sum(agreements) / len(agreements),
    }


def compare_offline_policies(rows=None):
    if rows is None:
        rows = read_csv_rows(DATASET_PATHS["identity"])
    test_rows = [
        row for row in rows
        if row["dataset_split"] == "test"
    ]
    test_rows = add_identity_predictions(test_rows)
    test_rows = add_action_value_predictions(test_rows)
    grouped = group_by_decision(test_rows)
    policy_rows = []

    for decision_type in ["seer_check", "wolf_kill", "day_vote"]:
        decisions = {
            decision_id: rows_for_decision
            for decision_id, rows_for_decision in grouped.items()
            if rows_for_decision[0]["decision_type"] == decision_type
        }
        policies = policy_candidates_for_decision_type(decision_type)
        for policy_name, selector in policies.items():
            selected = []
            if selector is None:
                for decision_rows in decisions.values():
                    best = choose_max(
                        decision_rows,
                        lambda row: as_float(row["ml_action_value"], 0.0),
                    )
                    random_mean = sum(
                        as_float(row["rollout_team_win_rate"], 0.0)
                        for row in decision_rows
                    ) / len(decision_rows)
                    row = dict(best)
                    row["rollout_team_win_rate"] = (
                        0.90 * as_float(best["rollout_team_win_rate"], 0.0)
                        + 0.10 * random_mean
                    )
                    selected.append(row)
            else:
                for decision_rows in decisions.values():
                    if (
                        decision_type == "day_vote"
                        and policy_name == "wolf_team_ml_vote_value"
                        and decision_rows[0]["actor_team"] != "wolf"
                    ):
                        continue
                    if (
                        decision_type == "day_vote"
                        and policy_name == "highest_ml_wolf_probability_for_village"
                        and decision_rows[0]["actor_team"] == "wolf"
                    ):
                        continue
                    selected.append(selector(decision_rows))
            policy_rows.append(summarize_policy(
                decision_type,
                policy_name,
                selected,
                grouped,
            ))

    write_csv_rows(
        OFFLINE_POLICY_PATH,
        policy_rows,
        [
            "decision_type",
            "policy",
            "test_decision_states",
            "estimated_policy_value",
            "average_regret",
            "existing_policy_agreement_rate",
        ],
    )
    write_csv_rows(
        POLICY_REGRET_PATH,
        [
            row for row in policy_rows
            if row["policy"] in {
                "existing_rule",
                "existing_wolf_strategy",
                "existing_voting_rule",
                "ml_highest_action_value",
                "ml_highest_wolf_team_action_value",
            }
        ],
        [
            "decision_type",
            "policy",
            "test_decision_states",
            "estimated_policy_value",
            "average_regret",
            "existing_policy_agreement_rate",
        ],
    )
    return policy_rows


if __name__ == "__main__":
    rows = compare_offline_policies()
    print("Offline policy comparison complete")
    print(f"Policy rows: {len(rows)}")
    print(f"Output: {OFFLINE_POLICY_PATH}")
