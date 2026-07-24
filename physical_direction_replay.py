import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from player import Player
from position_model import get_seat_type, get_side
from roles import HUNTER, SEER, WEREWOLF, WITCH, get_team
from seat_order_neutral import (
    NORMAL_MAPPING,
    PHYSICAL_SEATS,
    clockwise_distance_physical,
    counterclockwise_distance_physical,
    get_actor_uid,
    get_physical_seat,
    json_dump,
)


TOTAL_SEATS = 10
PHASE_ORDER = {"night": 0, "day": 1}
PHASE_TRANSITIONS = {
    ("night", "day"): "same_round",
    ("day", "night"): "next_round",
}
ACTION_PRIORITY = {
    "seer_check": 10,
    "witch_save": 20,
    "wolf_kill": 30,
    "witch_poison": 40,
    "speech_action": 50,
    "vote": 60,
    "abstain": 60,
    "day_vote_resolution": 70,
    "hunter_shot": 80,
    "skip_action": 90,
}
CHECK_SUSPICION_INCREASE = 0.25
CHECK_SUSPICION_DECREASE = 0.10


class ReplayError(ValueError):
    """Raised when a supplied action is illegal for the replay state."""


@dataclass
class SuppliedAction:
    round_number: int
    phase: str
    subphase: str
    actor_uid: object
    action_type: str
    physical_target_uid: object = None
    physical_target_seat: int = None
    payload: dict = field(default_factory=dict)
    action_sequence_index: int = 0
    event_log_index: int = None
    pre_state_hash: str = ""
    post_state_hash: str = ""
    rng_stream_id: str = ""

    def to_dict(self):
        return {
            "round_number": self.round_number,
            "phase": self.phase,
            "subphase": self.subphase,
            "actor_uid": self.actor_uid,
            "action_type": self.action_type,
            "physical_target_uid": self.physical_target_uid,
            "physical_target_seat": self.physical_target_seat,
            "payload": self.payload,
            "action_sequence_index": self.action_sequence_index,
            "event_log_index": self.event_log_index,
            "pre_state_hash": self.pre_state_hash,
            "post_state_hash": self.post_state_hash,
            "rng_stream_id": self.rng_stream_id,
        }

    @classmethod
    def from_dict(cls, row):
        return cls(
            round_number=row["round_number"],
            phase=row["phase"],
            subphase=row["subphase"],
            actor_uid=row["actor_uid"],
            action_type=row["action_type"],
            physical_target_uid=row.get("physical_target_uid"),
            physical_target_seat=row.get("physical_target_seat"),
            payload=dict(row.get("payload", {})),
            action_sequence_index=row.get("action_sequence_index", 0),
            event_log_index=row.get("event_log_index"),
            pre_state_hash=row.get("pre_state_hash", ""),
            post_state_hash=row.get("post_state_hash", ""),
            rng_stream_id=row.get("rng_stream_id", ""),
        )


@dataclass
class ReplayActionLog:
    action_log_id: str
    role_by_actor_uid: dict
    physical_seat_by_actor_uid: dict
    actions: list
    metadata: dict = field(default_factory=dict)
    initial_p_wolf: float = 0.3

    def to_dict(self):
        return {
            "action_log_id": self.action_log_id,
            "role_by_actor_uid": self.role_by_actor_uid,
            "physical_seat_by_actor_uid": self.physical_seat_by_actor_uid,
            "actions": [action.to_dict() for action in self.actions],
            "metadata": self.metadata,
            "initial_p_wolf": self.initial_p_wolf,
        }

    def to_json(self):
        return json_dump(self.to_dict())

    @classmethod
    def from_dict(cls, value):
        return cls(
            action_log_id=value["action_log_id"],
            role_by_actor_uid={
                normalize_actor_uid(key): role
                for key, role in value["role_by_actor_uid"].items()
            },
            physical_seat_by_actor_uid={
                normalize_actor_uid(key): int(seat)
                for key, seat in value["physical_seat_by_actor_uid"].items()
            },
            actions=[
                SuppliedAction.from_dict(action)
                for action in value.get("actions", [])
            ],
            metadata=dict(value.get("metadata", {})),
            initial_p_wolf=value.get("initial_p_wolf", 0.3),
        )


@dataclass
class ReplayValidationResult:
    action_log_id: str
    action_count: int
    action_sequence_exact_match: bool
    state_sequence_exact_match: bool
    winner_match: bool
    total_rounds_match: bool
    final_alive_set_match: bool
    first_divergence_event_index: object = ""
    first_divergence_round: object = ""
    first_divergence_phase: object = ""
    first_divergence_type: str = "none"
    error: str = ""

    def to_dict(self):
        return {
            "action_log_id": self.action_log_id,
            "action_count": self.action_count,
            "action_sequence_exact_match": int(
                self.action_sequence_exact_match
            ),
            "state_sequence_exact_match": int(
                self.state_sequence_exact_match
            ),
            "winner_match": int(self.winner_match),
            "total_rounds_match": int(self.total_rounds_match),
            "final_alive_set_match": int(self.final_alive_set_match),
            "first_divergence_event_index": self.first_divergence_event_index,
            "first_divergence_round": self.first_divergence_round,
            "first_divergence_phase": self.first_divergence_phase,
            "first_divergence_type": self.first_divergence_type,
            "error": self.error,
        }


@dataclass
class ReplayActorState:
    actor_uid: object
    physical_seat: int
    role: str
    alive: bool = True
    suspicion_score: float = 0.0
    p_wolf: float = 0.3
    has_antidote: bool = True
    has_poison: bool = True
    has_given_last_words: bool = False

    @property
    def team(self):
        return get_team(self.role)

    def is_wolf(self):
        return self.role == WEREWOLF


def normalize_actor_uid(value):
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return value


def stable_state_sha256(value):
    text = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def mirror_physical_seat(physical_seat, total_seats=TOTAL_SEATS):
    return total_seats + 1 - int(physical_seat)


def reverse_physical_direction(direction):
    if direction == "physical_clockwise":
        return "physical_counterclockwise"
    if direction == "physical_counterclockwise":
        return "physical_clockwise"
    if direction == "clockwise":
        return "counterclockwise"
    if direction == "counterclockwise":
        return "clockwise"
    return direction


def mirror_physical_role_assignment(role_by_physical_seat):
    return {
        mirror_physical_seat(physical_seat): role
        for physical_seat, role in role_by_physical_seat.items()
    }


def mirror_actor_physical_seats(physical_seat_by_actor_uid):
    return {
        normalize_actor_uid(actor_uid): mirror_physical_seat(physical_seat)
        for actor_uid, physical_seat in physical_seat_by_actor_uid.items()
    }


def mirror_supplied_action(action):
    payload = dict(action.payload)
    if "physical_direction" in payload:
        payload["physical_direction"] = reverse_physical_direction(
            payload["physical_direction"]
        )
    if "strategy" in payload:
        payload["strategy"] = reverse_physical_direction(payload["strategy"])

    return SuppliedAction(
        round_number=action.round_number,
        phase=action.phase,
        subphase=action.subphase,
        actor_uid=action.actor_uid,
        action_type=action.action_type,
        physical_target_uid=action.physical_target_uid,
        physical_target_seat=(
            mirror_physical_seat(action.physical_target_seat)
            if action.physical_target_seat is not None
            else None
        ),
        payload=payload,
        action_sequence_index=action.action_sequence_index,
        event_log_index=action.event_log_index,
        pre_state_hash="",
        post_state_hash="",
        rng_stream_id=action.rng_stream_id,
    )


def mirror_action_log(action_log):
    mirrored = ReplayActionLog(
        action_log_id=f"{action_log.action_log_id}_mirrored",
        role_by_actor_uid=dict(action_log.role_by_actor_uid),
        physical_seat_by_actor_uid=mirror_actor_physical_seats(
            action_log.physical_seat_by_actor_uid
        ),
        actions=[mirror_supplied_action(action) for action in action_log.actions],
        metadata={
            **action_log.metadata,
            "mirrored_from": action_log.action_log_id,
        },
        initial_p_wolf=action_log.initial_p_wolf,
    )
    annotate_action_log_checkpoints(mirrored)
    return mirrored


def create_players_from_actor_layout(
    role_by_actor_uid,
    physical_seat_by_actor_uid,
    physical_to_displayed_mapping=None,
    initial_p_wolf=0.3,
):
    if physical_to_displayed_mapping is None:
        physical_to_displayed_mapping = dict(NORMAL_MAPPING)

    players = []
    for actor_uid in sorted(role_by_actor_uid, key=lambda value: str(value)):
        physical_seat = physical_seat_by_actor_uid[actor_uid]
        displayed_id = physical_to_displayed_mapping[physical_seat]
        player = Player(displayed_id, role_by_actor_uid[actor_uid])
        player.actor_uid = actor_uid
        player.physical_seat = physical_seat
        player.displayed_player_id = displayed_id
        player.displayed_seat = displayed_id
        player.displayed_side = get_side(displayed_id)
        player.displayed_seat_type = get_seat_type(displayed_id)
        player.physical_side = get_side(physical_seat)
        player.physical_seat_type = get_seat_type(physical_seat)
        player.side = player.physical_side
        player.seat_type = player.physical_seat_type
        player.p_wolf = initial_p_wolf
        players.append(player)

    return sorted(players, key=lambda player: player.player_id)


def role_by_actor_from_physical_roles(role_by_physical_seat):
    return {
        physical_seat: role
        for physical_seat, role in role_by_physical_seat.items()
    }


def physical_seats_by_actor_from_physical_roles(role_by_physical_seat):
    return {
        physical_seat: physical_seat
        for physical_seat in role_by_physical_seat
    }


class ReplayController:
    def __init__(
        self,
        role_by_actor_uid,
        physical_seat_by_actor_uid,
        initial_p_wolf=0.3,
    ):
        self.actors = {
            normalize_actor_uid(actor_uid): ReplayActorState(
                actor_uid=normalize_actor_uid(actor_uid),
                physical_seat=int(physical_seat_by_actor_uid[actor_uid]),
                role=role,
                p_wolf=initial_p_wolf,
            )
            for actor_uid, role in role_by_actor_uid.items()
        }
        self.round_number = 1
        self.phase = "night"
        self.game_over = False
        self.winner = None
        self.votes = {}
        self.checked_targets_by_seer = defaultdict(set)
        self.witch_antidote_used_rounds = set()
        self.event_trace = []
        self.state_hash_sequence = [self.state_hash()]

    def state_hash(self, mirror_back=False):
        return stable_state_sha256(
            canonical_physical_state(self, mirror_back=mirror_back)
        )

    def get_actor(self, actor_uid):
        actor_uid = normalize_actor_uid(actor_uid)
        if actor_uid not in self.actors:
            raise ReplayError(f"Unknown actor_uid: {actor_uid}")
        return self.actors[actor_uid]

    def _advance_to_action_phase(self, action):
        action_round = int(action.round_number)
        action_phase = action.phase

        if action_phase not in PHASE_ORDER:
            raise ReplayError(f"Unknown phase: {action_phase}")

        if action_round == self.round_number and action_phase == self.phase:
            return

        transition = PHASE_TRANSITIONS.get((self.phase, action_phase))
        if (
            transition == "same_round"
            and action_round == self.round_number
        ):
            self.phase = action_phase
            return

        if (
            transition == "next_round"
            and action_round == self.round_number + 1
        ):
            self.round_number = action_round
            self.phase = action_phase
            self.votes = {}
            self.witch_antidote_used_rounds = set()
            return

        raise ReplayError(
            "Action order does not match replay phase: "
            f"state round={self.round_number} phase={self.phase}, "
            f"action round={action_round} phase={action_phase}."
        )

    def _require_alive(self, actor, action):
        if not actor.alive:
            raise ReplayError(
                f"{action.action_type} actor {actor.actor_uid} is not alive."
            )

    def _require_target_alive(self, target, action):
        if not target.alive:
            raise ReplayError(
                f"{action.action_type} target {target.actor_uid} is not alive."
            )

    def _kill(self, actor_uid):
        actor = self.get_actor(actor_uid)
        actor.alive = False
        self.check_win_condition()

    def check_win_condition(self):
        alive_wolves = sum(
            1 for actor in self.actors.values()
            if actor.alive and actor.is_wolf()
        )
        alive_villagers = sum(
            1 for actor in self.actors.values()
            if actor.alive and not actor.is_wolf()
        )
        if alive_wolves == 0:
            self.game_over = True
            self.winner = "village"
            return True
        if alive_wolves >= alive_villagers:
            self.game_over = True
            self.winner = "wolf"
            return True
        self.game_over = False
        self.winner = None
        return False

    def apply_action(self, action):
        self._advance_to_action_phase(action)
        pre_hash = self.state_hash()

        if action.action_type == "skip_action":
            pass
        elif action.action_type == "speech_action":
            self._apply_speech(action)
        elif action.action_type == "seer_check":
            self._apply_seer_check(action)
        elif action.action_type == "wolf_kill":
            self._apply_wolf_kill(action)
        elif action.action_type == "witch_save":
            self._apply_witch_save(action)
        elif action.action_type == "witch_poison":
            self._apply_witch_poison(action)
        elif action.action_type == "hunter_shot":
            self._apply_hunter_shot(action)
        elif action.action_type == "vote":
            self._apply_vote(action)
        elif action.action_type == "abstain":
            self._apply_abstain(action)
        elif action.action_type == "day_vote_resolution":
            self._apply_day_vote_resolution(action)
        else:
            raise ReplayError(f"Unsupported replay action: {action.action_type}")

        post_hash = self.state_hash()
        self.state_hash_sequence.append(post_hash)
        self.event_trace.append(action_signature(action))
        return pre_hash, post_hash

    def _apply_speech(self, action):
        actor = self.get_actor(action.actor_uid)
        if action.subphase != "last_words":
            self._require_alive(actor, action)
        if action.physical_target_uid is not None:
            self.get_actor(action.physical_target_uid)

    def _apply_seer_check(self, action):
        if action.phase != "night":
            raise ReplayError("seer_check is only legal at night.")
        seer = self.get_actor(action.actor_uid)
        target = self.get_actor(action.physical_target_uid)
        self._require_alive(seer, action)
        self._require_target_alive(target, action)
        if seer.role != SEER:
            raise ReplayError(f"Actor {seer.actor_uid} is not the seer.")
        if seer.actor_uid == target.actor_uid:
            raise ReplayError("Seer cannot check themselves.")
        if target.actor_uid in self.checked_targets_by_seer[seer.actor_uid]:
            raise ReplayError(
                f"Duplicate seer check of actor {target.actor_uid}."
            )
        self.checked_targets_by_seer[seer.actor_uid].add(target.actor_uid)
        if target.is_wolf():
            target.suspicion_score = min(
                1.0,
                target.suspicion_score + CHECK_SUSPICION_INCREASE,
            )
        else:
            target.suspicion_score = max(
                0.0,
                target.suspicion_score - CHECK_SUSPICION_DECREASE,
            )
        if "target_suspicion_after" in action.payload:
            target.suspicion_score = float(
                action.payload["target_suspicion_after"]
            )

    def _apply_wolf_kill(self, action):
        if action.phase != "night":
            raise ReplayError("wolf_kill is only legal at night.")
        target = self.get_actor(action.physical_target_uid)
        self._require_target_alive(target, action)
        if target.is_wolf():
            raise ReplayError("Wolves cannot night-kill a wolf target.")
        if action.payload.get("prevented") is True:
            return
        self._kill(target.actor_uid)

    def _apply_witch_save(self, action):
        if action.phase != "night":
            raise ReplayError("witch_save is only legal at night.")
        witch = self.get_actor(action.actor_uid)
        target = self.get_actor(action.physical_target_uid)
        self._require_alive(witch, action)
        self._require_target_alive(target, action)
        if witch.role != WITCH:
            raise ReplayError(f"Actor {witch.actor_uid} is not a witch.")
        if not witch.has_antidote:
            raise ReplayError("Witch antidote has already been used.")
        if (self.round_number, witch.actor_uid) in self.witch_antidote_used_rounds:
            raise ReplayError("Witch cannot save twice in the same night.")
        witch.has_antidote = False
        self.witch_antidote_used_rounds.add(
            (self.round_number, witch.actor_uid)
        )

    def _apply_witch_poison(self, action):
        if action.phase != "night":
            raise ReplayError("witch_poison is only legal at night.")
        witch = self.get_actor(action.actor_uid)
        target = self.get_actor(action.physical_target_uid)
        self._require_alive(witch, action)
        self._require_target_alive(target, action)
        if witch.role != WITCH:
            raise ReplayError(f"Actor {witch.actor_uid} is not a witch.")
        if not witch.has_poison:
            raise ReplayError("Witch poison has already been used.")
        if (self.round_number, witch.actor_uid) in self.witch_antidote_used_rounds:
            raise ReplayError(
                "Witch cannot use antidote and poison in the same night."
            )
        if witch.actor_uid == target.actor_uid:
            raise ReplayError("Witch cannot poison themselves.")
        witch.has_poison = False
        self._kill(target.actor_uid)

    def _apply_hunter_shot(self, action):
        hunter = self.get_actor(action.actor_uid)
        target = self.get_actor(action.physical_target_uid)
        if hunter.role != HUNTER:
            raise ReplayError(f"Actor {hunter.actor_uid} is not a hunter.")
        if hunter.alive:
            raise ReplayError("Hunter shot is only legal after hunter death.")
        self._require_target_alive(target, action)
        if hunter.actor_uid == target.actor_uid:
            raise ReplayError("Hunter cannot shoot themselves.")
        self._kill(target.actor_uid)

    def _apply_vote(self, action):
        if action.phase != "day":
            raise ReplayError("vote is only legal during the day.")
        voter = self.get_actor(action.actor_uid)
        target = self.get_actor(action.physical_target_uid)
        self._require_alive(voter, action)
        self._require_target_alive(target, action)
        if voter.actor_uid == target.actor_uid:
            raise ReplayError("Player cannot vote for themselves.")
        self.votes[voter.actor_uid] = target.actor_uid

    def _apply_abstain(self, action):
        if action.phase != "day":
            raise ReplayError("abstain is only legal during the day.")
        voter = self.get_actor(action.actor_uid)
        self._require_alive(voter, action)
        self.votes.pop(voter.actor_uid, None)

    def _apply_day_vote_resolution(self, action):
        if action.phase != "day":
            raise ReplayError("day_vote_resolution is only legal by day.")
        target = self.get_actor(action.physical_target_uid)
        self._require_target_alive(target, action)
        if not self.votes:
            raise ReplayError("Cannot resolve day vote without supplied votes.")
        vote_counts = Counter(self.votes.values())
        highest_vote_count = max(vote_counts.values())
        legal_eliminations = {
            actor_uid
            for actor_uid, vote_count in vote_counts.items()
            if vote_count == highest_vote_count
        }
        if target.actor_uid not in legal_eliminations:
            raise ReplayError(
                "Supplied eliminated target does not have highest vote count."
            )
        self._kill(target.actor_uid)

    def run(self, action_log, compare_expected_hashes=False):
        if action_log.action_log_id:
            pass
        for action in action_log.actions:
            try:
                pre_hash, post_hash = self.apply_action(action)
            except ReplayError as error:
                return ReplayValidationResult(
                    action_log_id=action_log.action_log_id,
                    action_count=len(action_log.actions),
                    action_sequence_exact_match=False,
                    state_sequence_exact_match=False,
                    winner_match=False,
                    total_rounds_match=False,
                    final_alive_set_match=False,
                    first_divergence_event_index=(
                        action.action_sequence_index
                    ),
                    first_divergence_round=action.round_number,
                    first_divergence_phase=action.phase,
                    first_divergence_type=action.action_type,
                    error=str(error),
                )
            if compare_expected_hashes:
                if action.pre_state_hash and action.pre_state_hash != pre_hash:
                    return ReplayValidationResult(
                        action_log_id=action_log.action_log_id,
                        action_count=len(action_log.actions),
                        action_sequence_exact_match=True,
                        state_sequence_exact_match=False,
                        winner_match=False,
                        total_rounds_match=False,
                        final_alive_set_match=False,
                        first_divergence_event_index=(
                            action.action_sequence_index
                        ),
                        first_divergence_round=action.round_number,
                        first_divergence_phase=action.phase,
                        first_divergence_type="pre_state_hash",
                        error="pre-state hash mismatch",
                    )
                if action.post_state_hash and action.post_state_hash != post_hash:
                    return ReplayValidationResult(
                        action_log_id=action_log.action_log_id,
                        action_count=len(action_log.actions),
                        action_sequence_exact_match=True,
                        state_sequence_exact_match=False,
                        winner_match=False,
                        total_rounds_match=False,
                        final_alive_set_match=False,
                        first_divergence_event_index=(
                            action.action_sequence_index
                        ),
                        first_divergence_round=action.round_number,
                        first_divergence_phase=action.phase,
                        first_divergence_type="post_state_hash",
                        error="post-state hash mismatch",
                    )

        return ReplayValidationResult(
            action_log_id=action_log.action_log_id,
            action_count=len(action_log.actions),
            action_sequence_exact_match=True,
            state_sequence_exact_match=True,
            winner_match=True,
            total_rounds_match=True,
            final_alive_set_match=True,
        )

    def final_alive_actor_uids(self):
        return sorted(
            actor.actor_uid
            for actor in self.actors.values()
            if actor.alive
        )


def canonical_physical_state(source, mirror_back=False):
    if isinstance(source, ReplayController):
        actors = source.actors.values()
        checked = {
            str(seer_uid): sorted(targets)
            for seer_uid, targets in source.checked_targets_by_seer.items()
        }
        votes = {
            str(voter): target
            for voter, target in sorted(source.votes.items())
        }
        return {
            "round": source.round_number,
            "phase": source.phase,
            "game_over": source.game_over,
            "winner": source.winner,
            "actors": [
                {
                    "actor_uid": actor.actor_uid,
                    "physical_seat": (
                        mirror_physical_seat(actor.physical_seat)
                        if mirror_back
                        else actor.physical_seat
                    ),
                    "role": actor.role,
                    "alive": actor.alive,
                    "suspicion_score": round(actor.suspicion_score, 6),
                    "p_wolf": round(actor.p_wolf, 6),
                    "has_antidote": actor.has_antidote,
                    "has_poison": actor.has_poison,
                    "has_given_last_words": actor.has_given_last_words,
                }
                for actor in sorted(actors, key=lambda value: str(value.actor_uid))
            ],
            "checked_targets_by_seer": checked,
            "votes": votes,
        }

    players = getattr(source, "players", source)
    return {
        "actors": [
            {
                "actor_uid": get_actor_uid(player),
                "physical_seat": (
                    mirror_physical_seat(get_physical_seat(player))
                    if mirror_back
                    else get_physical_seat(player)
                ),
                "role": player.role,
                "alive": player.alive,
                "suspicion_score": round(player.suspicion_score, 6),
                "p_wolf": round(player.p_wolf, 6),
                "has_antidote": getattr(player, "has_antidote", None),
                "has_poison": getattr(player, "has_poison", None),
                "has_given_last_words": getattr(
                    player,
                    "has_given_last_words",
                    None,
                ),
            }
            for player in sorted(players, key=lambda value: str(get_actor_uid(value)))
        ]
    }


def canonical_mirrored_state(source):
    return canonical_physical_state(source, mirror_back=True)


def action_signature(action, mirror_back=False):
    target_seat = action.physical_target_seat
    if target_seat is not None and mirror_back:
        target_seat = mirror_physical_seat(target_seat)
    return {
        "round": action.round_number,
        "phase": action.phase,
        "subphase": action.subphase,
        "actor_uid": action.actor_uid,
        "action_type": action.action_type,
        "target_uid": action.physical_target_uid,
        "target_seat": target_seat,
        "speech_type": action.payload.get("speech_type"),
        "deception_type": action.payload.get("deception_type"),
        "target_is_wolf": action.payload.get("target_is_wolf"),
        "prevented": action.payload.get("prevented"),
    }


def action_sequence_signature(actions, mirror_back=False):
    return [
        action_signature(action, mirror_back=mirror_back)
        for action in actions
    ]


def first_divergence(reference_items, observed_items):
    max_length = max(len(reference_items), len(observed_items))
    for index in range(max_length):
        reference_item = (
            reference_items[index] if index < len(reference_items) else None
        )
        observed_item = (
            observed_items[index] if index < len(observed_items) else None
        )
        if reference_item == observed_item:
            continue
        item = observed_item or reference_item or {}
        return {
            "index": index,
            "round": item.get("round", ""),
            "phase": item.get("phase", ""),
            "type": item.get("action_type", "trace_length"),
            "expected": reference_item,
            "observed": observed_item,
        }
    return {
        "index": "",
        "round": "",
        "phase": "none",
        "type": "none",
        "expected": None,
        "observed": None,
    }


def get_actor_maps_from_game(game):
    displayed_to_actor = {}
    displayed_to_physical = {}
    actor_to_physical = {}
    role_by_actor = {}
    for player in game.state.players:
        displayed_to_actor[player.player_id] = get_actor_uid(player)
        displayed_to_physical[player.player_id] = get_physical_seat(player)
        actor_to_physical[get_actor_uid(player)] = get_physical_seat(player)
        role_by_actor[get_actor_uid(player)] = player.role
    return displayed_to_actor, displayed_to_physical, actor_to_physical, role_by_actor


def displayed_to_actor_uid(displayed_to_actor, displayed_id):
    if displayed_id is None:
        return None
    return displayed_to_actor.get(int(displayed_id))


def displayed_to_physical_seat(displayed_to_physical, displayed_id):
    if displayed_id is None:
        return None
    return displayed_to_physical.get(int(displayed_id))


def make_action(
    event,
    event_log_index,
    subphase,
    actor_uid,
    action_type,
    physical_target_uid=None,
    physical_target_seat=None,
    payload=None,
):
    if payload is None:
        payload = {}
    return SuppliedAction(
        round_number=event.get("round"),
        phase=event.get("phase"),
        subphase=subphase,
        actor_uid=actor_uid,
        action_type=action_type,
        physical_target_uid=physical_target_uid,
        physical_target_seat=physical_target_seat,
        payload=payload,
        event_log_index=event_log_index,
    )


def capture_actions_from_event_log(game):
    displayed_to_actor, displayed_to_physical, _, _ = get_actor_maps_from_game(
        game
    )
    actions = []
    last_death_cause_by_phase = {}

    for event_log_index, event in enumerate(game.event_log):
        event_type = event.get("event_type")
        content = event.get("content", {})

        if event_type == "player_death":
            last_death_cause_by_phase[
                (event.get("round"), event.get("phase"))
            ] = content.get("cause")
            continue

        if event_type == "seer_check":
            actor_uid = content.get("seer_actor_uid")
            target_uid = content.get("target_actor_uid")
            actions.append(make_action(
                event,
                event_log_index,
                "seer_check",
                actor_uid,
                "seer_check",
                physical_target_uid=target_uid,
                physical_target_seat=content.get("target_physical_seat"),
                payload={
                    "target_is_wolf": content.get("target_is_wolf"),
                    "target_role": content.get("target_role"),
                    "target_suspicion_after": content.get(
                        "target_suspicion_after"
                    ),
                    "seer_check_strategy": content.get(
                        "seer_check_strategy"
                    ),
                },
            ))
            continue

        if event_type == "witch_save":
            actor_uid = displayed_to_actor_uid(
                displayed_to_actor,
                content.get("witch"),
            )
            target_uid = displayed_to_actor_uid(
                displayed_to_actor,
                content.get("saved_player"),
            )
            actions.append(make_action(
                event,
                event_log_index,
                "witch_save",
                actor_uid,
                "witch_save",
                physical_target_uid=target_uid,
                physical_target_seat=displayed_to_physical_seat(
                    displayed_to_physical,
                    content.get("saved_player"),
                ),
                payload={"used_antidote": content.get("used_antidote")},
            ))
            continue

        if event_type in {"night_kill", "night_kill_prevented"}:
            target_uid = displayed_to_actor_uid(
                displayed_to_actor,
                content.get("target"),
            )
            actions.append(make_action(
                event,
                event_log_index,
                "wolf_kill",
                "wolf_team",
                "wolf_kill",
                physical_target_uid=target_uid,
                physical_target_seat=displayed_to_physical_seat(
                    displayed_to_physical,
                    content.get("target"),
                ),
                payload={
                    "strategy": content.get("strategy"),
                    "prevented": event_type == "night_kill_prevented",
                },
            ))
            continue

        if event_type == "witch_poison":
            actor_uid = displayed_to_actor_uid(
                displayed_to_actor,
                content.get("witch"),
            )
            target_uid = displayed_to_actor_uid(
                displayed_to_actor,
                content.get("poisoned_player"),
            )
            actions.append(make_action(
                event,
                event_log_index,
                "witch_poison",
                actor_uid,
                "witch_poison",
                physical_target_uid=target_uid,
                physical_target_seat=displayed_to_physical_seat(
                    displayed_to_physical,
                    content.get("poisoned_player"),
                ),
                payload={
                    "target_role": content.get("target_role"),
                    "target_is_wolf": content.get("target_is_wolf"),
                    "used_poison": content.get("used_poison"),
                },
            ))
            continue

        if event_type == "hunter_shot":
            actor_uid = displayed_to_actor_uid(
                displayed_to_actor,
                content.get("hunter"),
            )
            target_uid = displayed_to_actor_uid(
                displayed_to_actor,
                content.get("shot_target"),
            )
            cause = last_death_cause_by_phase.get(
                (event.get("round"), event.get("phase")),
                "",
            )
            actions.append(make_action(
                event,
                event_log_index,
                f"hunter_shot_after_{cause or 'death'}",
                actor_uid,
                "hunter_shot",
                physical_target_uid=target_uid,
                physical_target_seat=displayed_to_physical_seat(
                    displayed_to_physical,
                    content.get("shot_target"),
                ),
                payload={
                    "target_role": content.get("target_role"),
                    "target_is_wolf": content.get("target_is_wolf"),
                    "death_cause": cause,
                },
            ))
            continue

        if event_type in {"speech", "last_words"}:
            speaker = content.get("speaker")
            target = content.get("target")
            actions.append(make_action(
                event,
                event_log_index,
                "last_words" if event_type == "last_words" else "speech",
                displayed_to_actor_uid(displayed_to_actor, speaker),
                "speech_action",
                physical_target_uid=displayed_to_actor_uid(
                    displayed_to_actor,
                    target,
                ),
                physical_target_seat=displayed_to_physical_seat(
                    displayed_to_physical,
                    target,
                ),
                payload={
                    "event_type": event_type,
                    "speech_type": content.get("speech_type"),
                    "deception_type": content.get("deception_type"),
                    "tokens": content.get("tokens"),
                    "text": content.get("text"),
                    "target": target,
                },
            ))
            continue

        if event_type == "day_vote":
            votes = content.get("votes", {})
            for vote_index, (voter_id, target_id) in enumerate(votes.items()):
                actions.append(make_action(
                    event,
                    event_log_index,
                    f"vote_{vote_index}",
                    displayed_to_actor_uid(displayed_to_actor, voter_id),
                    "vote",
                    physical_target_uid=displayed_to_actor_uid(
                        displayed_to_actor,
                        target_id,
                    ),
                    physical_target_seat=displayed_to_physical_seat(
                        displayed_to_physical,
                        target_id,
                    ),
                    payload={"method": content.get("method")},
                ))

            eliminated = content.get("eliminated")
            actions.append(make_action(
                event,
                event_log_index,
                "day_vote_resolution",
                "village_vote",
                "day_vote_resolution",
                physical_target_uid=displayed_to_actor_uid(
                    displayed_to_actor,
                    eliminated,
                ),
                physical_target_seat=displayed_to_physical_seat(
                    displayed_to_physical,
                    eliminated,
                ),
                payload={
                    "eliminated": eliminated,
                    "suspicion_scores": content.get("suspicion_scores", {}),
                    "p_wolf_scores": content.get("p_wolf_scores", {}),
                },
            ))
            continue

    actions.sort(key=sort_action_key)
    for index, action in enumerate(actions):
        action.action_sequence_index = index
        action.rng_stream_id = (
            f"{action.phase}:{action.round_number}:"
            f"{action.subphase}:{action.actor_uid}:{index}"
        )
    return actions


def sort_action_key(action):
    priority = ACTION_PRIORITY.get(action.action_type, 999)
    if action.action_type == "hunter_shot":
        cause = action.payload.get("death_cause")
        if cause == "night_kill":
            priority = 35
        elif cause == "witch_poison":
            priority = 45
        elif cause == "day_elimination":
            priority = 80
    return (
        int(action.round_number),
        PHASE_ORDER.get(action.phase, 99),
        priority,
        action.event_log_index if action.event_log_index is not None else 9999,
        action.subphase,
    )


def capture_replay_action_log(
    game,
    action_log_id,
    role_by_actor_uid=None,
    physical_seat_by_actor_uid=None,
    initial_p_wolf=0.3,
    metadata=None,
):
    _, _, actor_to_physical, role_by_actor_from_game = get_actor_maps_from_game(
        game
    )
    if role_by_actor_uid is None:
        role_by_actor_uid = role_by_actor_from_game
    if physical_seat_by_actor_uid is None:
        physical_seat_by_actor_uid = actor_to_physical
    if metadata is None:
        metadata = {}

    action_log = ReplayActionLog(
        action_log_id=action_log_id,
        role_by_actor_uid=dict(role_by_actor_uid),
        physical_seat_by_actor_uid=dict(physical_seat_by_actor_uid),
        actions=capture_actions_from_event_log(game),
        metadata=metadata,
        initial_p_wolf=initial_p_wolf,
    )
    annotate_action_log_checkpoints(action_log)
    return action_log


def annotate_action_log_checkpoints(action_log):
    controller = ReplayController(
        action_log.role_by_actor_uid,
        action_log.physical_seat_by_actor_uid,
        initial_p_wolf=action_log.initial_p_wolf,
    )
    for action in action_log.actions:
        pre_hash, post_hash = controller.apply_action(action)
        action.pre_state_hash = pre_hash
        action.post_state_hash = post_hash
    action_log.metadata["reference_final_state_hash"] = controller.state_hash()
    action_log.metadata["reference_final_alive_actor_uids"] = (
        controller.final_alive_actor_uids()
    )
    action_log.metadata["reference_winner"] = controller.winner
    action_log.metadata["reference_total_rounds"] = controller.round_number
    return action_log


def replay_action_log(action_log, compare_expected_hashes=True):
    controller = ReplayController(
        action_log.role_by_actor_uid,
        action_log.physical_seat_by_actor_uid,
        initial_p_wolf=action_log.initial_p_wolf,
    )
    result = controller.run(
        action_log,
        compare_expected_hashes=compare_expected_hashes,
    )
    result.winner_match = (
        controller.winner == action_log.metadata.get("reference_winner")
    )
    result.total_rounds_match = (
        controller.round_number
        == action_log.metadata.get("reference_total_rounds")
    )
    result.final_alive_set_match = (
        controller.final_alive_actor_uids()
        == action_log.metadata.get("reference_final_alive_actor_uids")
    )
    result.state_sequence_exact_match = (
        result.state_sequence_exact_match
        and result.winner_match
        and result.total_rounds_match
        and result.final_alive_set_match
    )
    return result, controller


def replay_mirrored_action_log(reference_action_log):
    mirrored_log = mirror_action_log(reference_action_log)
    controller = ReplayController(
        mirrored_log.role_by_actor_uid,
        mirrored_log.physical_seat_by_actor_uid,
        initial_p_wolf=mirrored_log.initial_p_wolf,
    )
    result = controller.run(mirrored_log, compare_expected_hashes=True)
    reference_controller = ReplayController(
        reference_action_log.role_by_actor_uid,
        reference_action_log.physical_seat_by_actor_uid,
        initial_p_wolf=reference_action_log.initial_p_wolf,
    )
    reference_controller.run(
        reference_action_log,
        compare_expected_hashes=True,
    )
    mirrored_state = canonical_mirrored_state(controller)
    reference_state = canonical_physical_state(reference_controller)
    state_match = mirrored_state == reference_state
    result.state_sequence_exact_match = (
        result.state_sequence_exact_match and state_match
    )
    result.winner_match = controller.winner == reference_controller.winner
    result.total_rounds_match = (
        controller.round_number == reference_controller.round_number
    )
    result.final_alive_set_match = (
        controller.final_alive_actor_uids()
        == reference_controller.final_alive_actor_uids()
    )
    return result, mirrored_log, controller


def compare_action_logs(reference_log, observed_log, observed_mirror_back=False):
    reference_signature = action_sequence_signature(reference_log.actions)
    observed_signature = action_sequence_signature(
        observed_log.actions,
        mirror_back=observed_mirror_back,
    )
    divergence = first_divergence(reference_signature, observed_signature)
    return {
        "action_sequence_match": reference_signature == observed_signature,
        "first_divergence": divergence,
        "reference_action_count": len(reference_signature),
        "observed_action_count": len(observed_signature),
    }


def get_seer_check_target_uids(action_log):
    return [
        action.physical_target_uid
        for action in action_log.actions
        if action.action_type == "seer_check"
    ]


def get_vote_sequence(action_log):
    return [
        (action.actor_uid, action.physical_target_uid)
        for action in action_log.actions
        if action.action_type == "vote"
    ]


def get_speech_sequence(action_log):
    return [
        (
            action.actor_uid,
            action.payload.get("speech_type"),
            action.physical_target_uid,
            action.payload.get("deception_type"),
        )
        for action in action_log.actions
        if action.action_type == "speech_action"
    ]


def get_outcome_metrics_from_game(game, result):
    seer_checks = [
        event for event in game.event_log
        if event.get("event_type") == "seer_check"
    ]
    checked_wolf = [
        event.get("content", {}).get("target_is_wolf") is True
        for event in seer_checks
    ]
    seer_actor_uid = ""
    for player in game.state.players:
        if player.role == SEER:
            seer_actor_uid = get_actor_uid(player)
            seer_alive = player.alive
            break
    else:
        seer_alive = False

    return {
        "winner": result["winner"],
        "village_win": 1 if result["winner"] == "village" else 0,
        "wolf_win": 1 if result["winner"] == "wolf" else 0,
        "total_rounds": result["round_number"],
        "seer_actor_uid": seer_actor_uid,
        "seer_survived_to_game_end": 1 if seer_alive else 0,
        "total_seer_checks": len(seer_checks),
        "found_wolf_by_check_1": int(any(checked_wolf[:1])),
        "found_wolf_by_check_2": int(any(checked_wolf[:2])),
        "found_wolf_by_check_3": int(any(checked_wolf[:3])),
    }


def compare_strategy_mirror_logs(reference_log, mirror_log):
    comparison = compare_action_logs(
        reference_log,
        mirror_log,
        observed_mirror_back=True,
    )
    reference_checks = get_seer_check_target_uids(reference_log)
    mirror_checks = get_seer_check_target_uids(mirror_log)
    first_check_match = (
        bool(reference_checks)
        and bool(mirror_checks)
        and reference_checks[0] == mirror_checks[0]
    )
    full_check_match = reference_checks == mirror_checks
    return {
        **comparison,
        "first_check_mirror_match": first_check_match,
        "full_check_sequence_mirror_match": full_check_match,
        "vote_sequence_mirror_match": (
            get_vote_sequence(reference_log) == get_vote_sequence(mirror_log)
        ),
        "speech_sequence_mirror_match": (
            get_speech_sequence(reference_log)
            == get_speech_sequence(mirror_log)
        ),
    }


def assert_mirrored_adjacency_preserved():
    for seat in PHYSICAL_SEATS:
        clockwise_neighbor = (
            (seat % TOTAL_SEATS) + 1
        )
        mirrored_seat = mirror_physical_seat(seat)
        mirrored_neighbor = mirror_physical_seat(clockwise_neighbor)
        distance = counterclockwise_distance_physical(
            mirrored_seat,
            mirrored_neighbor,
        )
        if distance != 1:
            raise AssertionError("Mirroring failed to preserve adjacency.")


def assert_direction_reversal_preserved():
    for start in PHYSICAL_SEATS:
        for target in PHYSICAL_SEATS:
            if start == target:
                continue
            cw = clockwise_distance_physical(start, target)
            mirrored_ccw = counterclockwise_distance_physical(
                mirror_physical_seat(start),
                mirror_physical_seat(target),
            )
            if cw != mirrored_ccw:
                raise AssertionError(
                    "Clockwise distance did not mirror to counterclockwise."
                )
