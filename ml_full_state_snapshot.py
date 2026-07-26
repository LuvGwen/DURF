import copy
import hashlib
import json
import random

from game import Game
from player import Player
from seat_order_neutral import json_dump


GAME_CONFIG_FIELDS = [
    "use_suspicion_voting",
    "enable_suspicion_update",
    "enable_seer",
    "enable_witch",
    "enable_hunter",
    "enable_speech",
    "enable_herding",
    "herding_alpha",
    "herding_beta",
    "herding_gamma",
    "enable_role_prior",
    "role_prior_alpha",
    "role_prior_beta",
    "role_prior_gamma",
    "role_prior_delta",
    "enable_wolf_strategy",
    "wolf_kill_strategy",
    "wolf_kill_noise_level",
    "enable_wolf_deception",
    "wolf_deception_strategy",
    "enable_deception_credibility",
    "enable_speaker_memory",
    "enable_last_words",
    "enable_risk_preference",
    "risk_preference_mode",
    "speaker_memory_weight",
    "enable_trust_weighted_speech",
    "trust_speech_min_multiplier",
    "trust_speech_max_multiplier",
    "enable_trust_weighted_herding",
    "trust_herding_min_multiplier",
    "trust_herding_max_multiplier",
    "witch_poison_threshold",
    "witch_save_probability",
    "speech_signal_scale",
    "credibility_cost_scale",
    "seer_check_strategy",
    "seer_avoid_repeat_checks",
    "enable_position_model",
    "randomize_seat_roles",
    "seat_order_neutral_mode",
    "neutral_seed",
    "base_game_index",
    "label_condition",
    "rotation_offset",
    "main_game_seed",
    "enable_ml_wolf_kill_policy",
    "ml_wolf_kill_policy_name",
    "ml_wolf_kill_model_manifest_path",
    "ml_wolf_kill_manifest_hash",
    "ml_wolf_kill_epsilon",
    "ml_wolf_kill_hybrid_weight",
]


PLAYER_EXTRA_FIELDS = [
    "actor_uid",
    "physical_seat",
    "displayed_player_id",
    "displayed_seat",
    "displayed_side",
    "displayed_seat_type",
    "physical_side",
    "physical_seat_type",
]


def stable_sha256(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


def serialize_player(player):
    data = player.to_dict()
    for field in PLAYER_EXTRA_FIELDS:
        if hasattr(player, field):
            data[field] = getattr(player, field)
    data["team"] = player.team
    return copy.deepcopy(data)


def restore_player(data):
    player = Player(player_id=int(data["player_id"]), role=data["role"])
    player.alive = bool(data.get("alive", True))
    player.suspicion_score = float(data.get("suspicion_score", 0.0))
    player.p_wolf = float(data.get("p_wolf", 0.0))
    player.risk_preference = data.get("risk_preference", "neutral")
    player.side = data.get("side")
    player.seat_type = data.get("seat_type")
    player.has_antidote = bool(data.get("has_antidote", True))
    player.has_poison = bool(data.get("has_poison", True))
    player.has_given_last_words = bool(
        data.get("has_given_last_words", False)
    )
    player.vote_target = data.get("vote_target")
    player.night_target = data.get("night_target")
    player.memory = copy.deepcopy(data.get("memory", []))
    for field in PLAYER_EXTRA_FIELDS:
        if field in data:
            setattr(player, field, data[field])
    return player


def canonical_snapshot_state(snapshot):
    return {
        "players": sorted(
            snapshot["players"],
            key=lambda player: (
                str(player.get("actor_uid", player["player_id"])),
                player["player_id"],
            ),
        ),
        "state": snapshot["state"],
        "event_log": snapshot["event_log"],
        "payoffs": snapshot.get("payoffs", {}),
        "config": snapshot["config"],
        "metadata": snapshot.get("metadata", {}),
    }


def capture_full_game_snapshot(game, snapshot_id=None, metadata=None):
    if metadata is None:
        metadata = {}
    snapshot = {
        "snapshot_id": snapshot_id or stable_sha256({
            "round": game.state.round_number,
            "phase": game.state.phase,
            "events": len(game.event_log),
            "metadata": metadata,
        }),
        "players": [
            serialize_player(player)
            for player in game.state.players
        ],
        "state": {
            "round_number": game.state.round_number,
            "phase": game.state.phase,
            "game_over": game.state.game_over,
            "winner": game.state.winner,
            "seat_order_neutral_mode": getattr(
                game.state,
                "seat_order_neutral_mode",
                False,
            ),
            "neutral_seed": getattr(game.state, "neutral_seed", None),
            "base_game_index": getattr(game.state, "base_game_index", None),
            "label_condition": getattr(game.state, "label_condition", None),
            "rotation_offset": getattr(game.state, "rotation_offset", 0),
            "main_game_seed": getattr(game.state, "main_game_seed", None),
            "neutral_actor_iteration_order": copy.deepcopy(
                getattr(game.state, "neutral_actor_iteration_order", [])
            ),
            "physical_to_displayed_mapping": copy.deepcopy(
                getattr(game.state, "physical_to_displayed_mapping", None)
            ),
            "displayed_to_physical_mapping": copy.deepcopy(
                getattr(game.state, "displayed_to_physical_mapping", None)
            ),
        },
        "event_log": copy.deepcopy(game.event_log),
        "payoffs": copy.deepcopy(getattr(game, "payoffs", {})),
        "config": {
            field: copy.deepcopy(getattr(game, field))
            for field in GAME_CONFIG_FIELDS
            if hasattr(game, field)
        },
        "metadata": copy.deepcopy(metadata),
        "rng_state_repr": repr(random.getstate()),
    }
    snapshot["canonical_hash"] = stable_sha256(
        canonical_snapshot_state(snapshot)
    )
    return snapshot


def restore_full_game_snapshot(snapshot):
    players = [
        restore_player(player_data)
        for player_data in snapshot["players"]
    ]
    config = copy.deepcopy(snapshot["config"])
    init_config = copy.deepcopy(config)
    init_config["randomize_seat_roles"] = False
    game = Game(players, **init_config)
    state_data = snapshot["state"]
    game.state.players = players
    game.state.round_number = int(state_data["round_number"])
    game.state.phase = state_data["phase"]
    game.state.game_over = bool(state_data["game_over"])
    game.state.winner = state_data["winner"]
    for field in [
        "seat_order_neutral_mode",
        "neutral_seed",
        "base_game_index",
        "label_condition",
        "rotation_offset",
        "main_game_seed",
        "neutral_actor_iteration_order",
        "physical_to_displayed_mapping",
        "displayed_to_physical_mapping",
    ]:
        setattr(game.state, field, copy.deepcopy(state_data.get(field)))
    for field, value in config.items():
        setattr(game, field, copy.deepcopy(value))
    game.event_log = copy.deepcopy(snapshot["event_log"])
    game.payoffs = copy.deepcopy(snapshot.get("payoffs", {}))
    return game


def clone_game_from_snapshot(snapshot):
    return restore_full_game_snapshot(copy.deepcopy(snapshot))


def validate_snapshot_equivalence(snapshot):
    restored_game = restore_full_game_snapshot(snapshot)
    restored_snapshot = capture_full_game_snapshot(
        restored_game,
        snapshot_id=snapshot.get("snapshot_id"),
        metadata=snapshot.get("metadata", {}),
    )
    return {
        "snapshot_id": snapshot.get("snapshot_id"),
        "original_hash": snapshot["canonical_hash"],
        "restored_hash": restored_snapshot["canonical_hash"],
        "equivalent": (
            snapshot["canonical_hash"] == restored_snapshot["canonical_hash"]
        ),
    }


def snapshot_to_json(snapshot):
    return json_dump(snapshot)
