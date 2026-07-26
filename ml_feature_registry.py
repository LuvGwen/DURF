from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureDefinition:
    name: str
    description: str
    data_type: str
    actor_types_allowed: str
    earliest_phase: str
    visibility: str
    source_function: str
    missing_value_policy: str


FEATURE_REGISTRY = [
    FeatureDefinition(
        "round_number",
        "Current game round at the decision point.",
        "integer",
        "all",
        "night",
        "public",
        "build_actor_observation",
        "0",
    ),
    FeatureDefinition(
        "phase_is_night",
        "Indicator that the decision occurs at night.",
        "integer",
        "seer,wolf_team",
        "night",
        "public",
        "build_actor_observation",
        "0",
    ),
    FeatureDefinition(
        "phase_is_day",
        "Indicator that the decision occurs during day discussion/voting.",
        "integer",
        "all",
        "day",
        "public",
        "build_actor_observation",
        "0",
    ),
    FeatureDefinition(
        "decision_type_is_seer_check",
        "Indicator for seer check candidate rows.",
        "integer",
        "seer",
        "night",
        "public",
        "build_candidate_feature_row",
        "0",
    ),
    FeatureDefinition(
        "decision_type_is_wolf_kill",
        "Indicator for wolf kill candidate rows.",
        "integer",
        "wolf_team",
        "night",
        "team-private",
        "build_candidate_feature_row",
        "0",
    ),
    FeatureDefinition(
        "decision_type_is_day_vote",
        "Indicator for day vote candidate rows.",
        "integer",
        "all",
        "day",
        "public",
        "build_candidate_feature_row",
        "0",
    ),
    FeatureDefinition(
        "actor_team_is_wolf",
        "Whether the acting player is known to self as wolf team.",
        "integer",
        "self",
        "night",
        "role-private",
        "build_actor_observation",
        "0",
    ),
    FeatureDefinition(
        "actor_team_is_village",
        "Whether the acting player is known to self as village team.",
        "integer",
        "self",
        "night",
        "role-private",
        "build_actor_observation",
        "0",
    ),
    FeatureDefinition(
        "alive_count",
        "Number of alive players before this decision.",
        "integer",
        "all",
        "night",
        "public",
        "build_actor_observation",
        "0",
    ),
    FeatureDefinition(
        "dead_count",
        "Number of dead players before this decision.",
        "integer",
        "all",
        "night",
        "public",
        "build_actor_observation",
        "0",
    ),
    FeatureDefinition(
        "public_revealed_role_count",
        "Number of players whose roles have been publicly revealed by death.",
        "integer",
        "all",
        "day",
        "public",
        "build_actor_observation",
        "0",
    ),
    FeatureDefinition(
        "public_information_entropy_proxy",
        "Average p_wolf uncertainty proxy from decision-time belief scores.",
        "float",
        "all",
        "night",
        "public",
        "compute_score_state",
        "0.5",
    ),
    FeatureDefinition(
        "number_of_public_check_results",
        "Public seer results. Current engine treats checks as private, so this remains 0.",
        "integer",
        "all",
        "night",
        "public",
        "build_actor_observation",
        "0",
    ),
    FeatureDefinition(
        "number_of_previous_eliminations",
        "Count of previous public deaths before the decision.",
        "integer",
        "all",
        "day",
        "public",
        "build_actor_observation",
        "0",
    ),
    FeatureDefinition(
        "actor_suspicion_score",
        "Decision-time suspicion score for the actor.",
        "float",
        "all",
        "night",
        "public",
        "compute_score_state",
        "0.0",
    ),
    FeatureDefinition(
        "actor_p_wolf",
        "Decision-time p_wolf score for the actor.",
        "float",
        "all",
        "night",
        "public",
        "compute_score_state",
        "initial_p_wolf",
    ),
    FeatureDefinition(
        "actor_risk_conservative",
        "Actor risk preference indicator.",
        "integer",
        "all",
        "night",
        "role-private",
        "build_actor_observation",
        "0",
    ),
    FeatureDefinition(
        "actor_risk_aggressive",
        "Actor risk preference indicator.",
        "integer",
        "all",
        "night",
        "role-private",
        "build_actor_observation",
        "0",
    ),
    FeatureDefinition(
        "actor_previous_votes_made",
        "Number of votes made by the actor before this decision.",
        "integer",
        "all",
        "day",
        "public",
        "event_history_counts",
        "0",
    ),
    FeatureDefinition(
        "actor_previous_speeches_made",
        "Number of speech acts made by the actor before this decision.",
        "integer",
        "all",
        "day",
        "public",
        "event_history_counts",
        "0",
    ),
    FeatureDefinition(
        "actor_known_teammate_count",
        "Number of known alive wolf teammates, visible only to wolf actors.",
        "integer",
        "wolf_team",
        "night",
        "team-private",
        "build_actor_observation",
        "0",
    ),
    FeatureDefinition(
        "candidate_alive",
        "Candidate is alive and legal at the decision point.",
        "integer",
        "all",
        "night",
        "public",
        "build_candidate_feature_row",
        "0",
    ),
    FeatureDefinition(
        "candidate_checked_by_actor_status",
        "Private seer-known status: 1 known wolf, -1 known village, 0 unknown.",
        "integer",
        "seer",
        "night",
        "role-private",
        "seer_private_check_memory",
        "0",
    ),
    FeatureDefinition(
        "candidate_public_role_known",
        "Whether the candidate's role is publicly revealed before the decision.",
        "integer",
        "all",
        "day",
        "public",
        "revealed_role_memory",
        "0",
    ),
    FeatureDefinition(
        "candidate_suspicion_score",
        "Candidate suspicion score reconstructed from past events only.",
        "float",
        "all",
        "night",
        "public",
        "compute_score_state",
        "0.0",
    ),
    FeatureDefinition(
        "candidate_p_wolf",
        "Candidate p_wolf reconstructed from past events only.",
        "float",
        "all",
        "night",
        "public",
        "compute_score_state",
        "initial_p_wolf",
    ),
    FeatureDefinition(
        "candidate_received_accusations",
        "Past accusation-like speeches targeting the candidate.",
        "integer",
        "all",
        "day",
        "public",
        "event_history_counts",
        "0",
    ),
    FeatureDefinition(
        "candidate_made_accusations",
        "Past accusation-like speeches made by the candidate.",
        "integer",
        "all",
        "day",
        "public",
        "event_history_counts",
        "0",
    ),
    FeatureDefinition(
        "candidate_wrong_accusation_count",
        "Visible wrong-accusation penalties attributed to the candidate as speaker.",
        "integer",
        "all",
        "day",
        "public",
        "event_history_counts",
        "0",
    ),
    FeatureDefinition(
        "candidate_vote_received_count",
        "Votes previously received by the candidate.",
        "integer",
        "all",
        "day",
        "public",
        "event_history_counts",
        "0",
    ),
    FeatureDefinition(
        "candidate_vote_made_count",
        "Votes previously cast by the candidate.",
        "integer",
        "all",
        "day",
        "public",
        "event_history_counts",
        "0",
    ),
    FeatureDefinition(
        "candidate_vote_switch_count",
        "How often the candidate changed vote targets across previous days.",
        "integer",
        "all",
        "day",
        "public",
        "event_history_counts",
        "0",
    ),
    FeatureDefinition(
        "candidate_speech_count",
        "Total past speeches by candidate.",
        "integer",
        "all",
        "day",
        "public",
        "event_history_counts",
        "0",
    ),
    FeatureDefinition(
        "candidate_defense_count",
        "Past defend/deny/deflect speeches by candidate.",
        "integer",
        "all",
        "day",
        "public",
        "event_history_counts",
        "0",
    ),
    FeatureDefinition(
        "candidate_role_claim_count",
        "Past role-claim speeches by candidate.",
        "integer",
        "all",
        "day",
        "public",
        "event_history_counts",
        "0",
    ),
    FeatureDefinition(
        "candidate_special_role_claim_count",
        "Past role-claim speeches by candidate, separated for role-prior use.",
        "integer",
        "all",
        "day",
        "public",
        "event_history_counts",
        "0",
    ),
    FeatureDefinition(
        "candidate_trust_from_actor",
        "Actor-specific trust score for the candidate as a speaker.",
        "float",
        "all",
        "day",
        "role-private",
        "speaker_trust_from_past_events",
        "0.5",
    ),
    FeatureDefinition(
        "candidate_conflict_with_actor",
        "Past candidate accusations against actor or actor accusations against candidate.",
        "integer",
        "all",
        "day",
        "public",
        "event_history_counts",
        "0",
    ),
    FeatureDefinition(
        "candidate_support_from_actor",
        "Past trust/defense relation between actor and candidate.",
        "integer",
        "all",
        "day",
        "public",
        "event_history_counts",
        "0",
    ),
    FeatureDefinition(
        "candidate_public_influence_proxy",
        "Speech plus vote influence proxy based on past observable activity.",
        "float",
        "all",
        "day",
        "public",
        "event_history_counts",
        "0.0",
    ),
    FeatureDefinition(
        "candidate_physical_seat_numeric",
        "Physical seat index when position information is public by design.",
        "integer",
        "all",
        "night",
        "public",
        "position_model",
        "displayed seat if physical seat unavailable",
    ),
    FeatureDefinition(
        "candidate_seat_is_edge",
        "Position-model edge-seat indicator.",
        "integer",
        "all",
        "night",
        "public",
        "position_model",
        "0",
    ),
    FeatureDefinition(
        "candidate_side_is_left",
        "Position-model left-side indicator.",
        "integer",
        "all",
        "night",
        "public",
        "position_model",
        "0",
    ),
    FeatureDefinition(
        "candidate_distance_from_actor",
        "Circular seat distance from actor to candidate.",
        "integer",
        "all",
        "night",
        "public",
        "position_model",
        "0",
    ),
    FeatureDefinition(
        "candidate_search_coverage_bonus",
        "Distance from previously checked seats for seer search diversity.",
        "float",
        "seer",
        "night",
        "role-private",
        "seer_private_check_memory",
        "0.0",
    ),
    FeatureDefinition(
        "candidate_was_previously_targeted_by_actor",
        "Whether this actor previously checked, killed, voted, or accused candidate.",
        "integer",
        "all",
        "day",
        "public/role-private",
        "event_history_counts",
        "0",
    ),
    FeatureDefinition(
        "candidate_known_wolf_to_actor",
        "Legally known wolf marker from seer private result or wolf teammate knowledge.",
        "integer",
        "seer,wolf_team",
        "night",
        "role-private/team-private",
        "known_information_for_actor",
        "0",
    ),
    FeatureDefinition(
        "candidate_known_village_to_actor",
        "Legally known village marker from seer private result.",
        "integer",
        "seer",
        "night",
        "role-private",
        "known_information_for_actor",
        "0",
    ),
    FeatureDefinition(
        "candidate_current_vote_count",
        "Votes already recorded in the current voting state, if available.",
        "integer",
        "all",
        "day",
        "public",
        "current_vote_state",
        "0",
    ),
    FeatureDefinition(
        "current_vote_total",
        "Total votes already recorded in current voting state, if available.",
        "integer",
        "all",
        "day",
        "public",
        "current_vote_state",
        "0",
    ),
    FeatureDefinition(
        "candidate_uncertainty_proxy",
        "min(p_wolf, 1 - p_wolf) at decision time.",
        "float",
        "all",
        "night",
        "public",
        "compute_score_state",
        "0.5",
    ),
    FeatureDefinition(
        "candidate_survival_proxy",
        "Public proxy for candidate persistence: 1 if alive, plus low suspicion/p_wolf.",
        "float",
        "all",
        "night",
        "public",
        "build_candidate_feature_row",
        "0.0",
    ),
]


PROHIBITED_FEATURES = {
    "true_candidate_role_label",
    "candidate_is_wolf_label",
    "eventual_winner_label",
    "actor_team_win_label",
    "rollout_team_win_rate",
    "rollout_best_action",
    "final_survival_label",
    "future_votes",
    "future_speech",
    "future_deaths",
}


LABEL_COLUMNS = {
    "true_candidate_role_label",
    "candidate_is_wolf_label",
    "eventual_winner_label",
    "actor_team_win_label",
    "check_target_is_wolf",
    "candidate_is_special_label",
    "vote_target_is_wolf_label",
    "rollout_team_win_rate",
    "rollout_team_win_standard_error",
    "rollout_immediate_success_rate",
    "rollout_secondary_reward_mean",
    "rollout_value_rank_within_decision",
    "rollout_best_action",
    "rollout_existing_policy_regret",
}


ID_COLUMNS = {
    "observation_id",
    "decision_id",
    "game_id",
    "seed",
    "base_game_index",
    "round",
    "round_number",
    "phase",
    "decision_type",
    "actor_uid",
    "actor_team",
    "actor_role_if_self_known",
    "candidate_uid",
    "selected_candidate_uid",
    "existing_policy_name",
    "dataset_split",
    "split_group_id",
}


FEATURE_COLUMNS = [feature.name for feature in FEATURE_REGISTRY]


def registry_as_rows():
    return [
        {
            "name": feature.name,
            "description": feature.description,
            "data_type": feature.data_type,
            "actor_types_allowed": feature.actor_types_allowed,
            "earliest_phase": feature.earliest_phase,
            "visibility": feature.visibility,
            "source_function": feature.source_function,
            "missing_value_policy": feature.missing_value_policy,
        }
        for feature in FEATURE_REGISTRY
    ]


def get_feature_columns():
    return list(FEATURE_COLUMNS)


def get_model_feature_columns(columns):
    allowed = set(FEATURE_COLUMNS)
    return [column for column in columns if column in allowed]


def validate_no_prohibited_features(feature_columns):
    prohibited = sorted(set(feature_columns) & PROHIBITED_FEATURES)
    if prohibited:
        raise ValueError(
            "Prohibited feature columns found: " + ", ".join(prohibited)
        )
    return True


def write_feature_registry_markdown(path):
    rows = registry_as_rows()
    with path.open("w") as file:
        file.write("# ML Stage 1 Feature Registry\n\n")
        file.write(
            "This registry defines observation-safe feature columns for the "
            "first machine-learning optimization stage. True hidden roles, "
            "future outcomes, and final winner fields are labels only and "
            "must not be used as model features.\n\n"
        )
        file.write("## Prohibited Inputs\n\n")
        for value in sorted(PROHIBITED_FEATURES):
            file.write(f"- `{value}`\n")
        file.write("\n## Feature Definitions\n\n")
        file.write(
            "| name | type | actors | earliest_phase | visibility | source | missing |\n"
        )
        file.write("|---|---|---|---|---|---|---|\n")
        for row in rows:
            file.write(
                f"| `{row['name']}` | {row['data_type']} | "
                f"{row['actor_types_allowed']} | {row['earliest_phase']} | "
                f"{row['visibility']} | `{row['source_function']}` | "
                f"{row['missing_value_policy']} |\n"
            )
