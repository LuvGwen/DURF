import random
from collections import Counter
from typing import List

from config import (
    DEFAULT_ENABLE_HERDING,
    DEFAULT_ENABLE_HUNTER,
    DEFAULT_ENABLE_ROLE_PRIOR,
    DEFAULT_ENABLE_WOLF_DECEPTION,
    DEFAULT_ENABLE_WOLF_STRATEGY,
    DEFAULT_HERDING_ALPHA,
    DEFAULT_HERDING_BETA,
    DEFAULT_HERDING_GAMMA,
    DEFAULT_ROLE_PRIOR_ALPHA,
    DEFAULT_ROLE_PRIOR_BETA,
    DEFAULT_ROLE_PRIOR_DELTA,
    DEFAULT_ROLE_PRIOR_GAMMA,
    DEFAULT_ROLE_SETUP,
    DEFAULT_WITCH_POISON_THRESHOLD,
    DEFAULT_WOLF_KILL_NOISE_LEVEL,
    DEFAULT_WOLF_KILL_STRATEGY,
    DEFAULT_WOLF_DECEPTION_STRATEGY,
    DEFAULT_ENABLE_DECEPTION_CREDIBILITY,
    DEFAULT_ENABLE_LAST_WORDS,
    DEFAULT_ENABLE_RISK_PREFERENCE,
    DEFAULT_ENABLE_SPEAKER_MEMORY,
    DEFAULT_TRUST_VOTE_WEIGHT,
    DEFAULT_ENABLE_TRUST_WEIGHTED_SPEECH,
    DEFAULT_TRUST_SPEECH_MIN_MULTIPLIER,
    DEFAULT_TRUST_SPEECH_MAX_MULTIPLIER,
    DEFAULT_ENABLE_TRUST_WEIGHTED_HERDING,
    DEFAULT_TRUST_HERDING_MIN_MULTIPLIER,
    DEFAULT_TRUST_HERDING_MAX_MULTIPLIER,
)
from belief_update import update_beliefs_from_event
from deception_credibility import (
    DEFAULT_FALSE_ACCUSATION_BASE_P_WOLF_COST,
    DEFAULT_FALSE_ACCUSATION_BASE_SUSPICION_COST,
    DEFAULT_REPEAT_P_WOLF_COST,
    DEFAULT_REPEAT_SELF_DEFENSE_P_WOLF_COST,
    DEFAULT_REPEAT_SELF_DEFENSE_SUSPICION_COST,
    DEFAULT_REPEAT_SUSPICION_COST,
    DEFAULT_REPEAT_TRUST_BUILDING_P_WOLF_COST,
    DEFAULT_REPEAT_TRUST_BUILDING_SUSPICION_COST,
    DEFAULT_WRONG_ACCUSATION_P_WOLF_PENALTY,
    DEFAULT_WRONG_ACCUSATION_SUSPICION_PENALTY,
    apply_accusation_pressure_cost,
    apply_self_defense_credibility_cost,
    apply_wrong_accusation_penalties,
)
from herding import calculate_herding_pressure
from hunter_action import perform_hunter_shot
from last_words import can_give_last_words, generate_last_words
from player import Player
from game_state import GameState
from position_model import (
    assign_positions,
    assign_random_roles_to_seats,
    summarize_seat_role_assignment,
)
from risk_preference import assign_risk_preferences
from role_prior import calculate_role_prior_score
from seer_action import perform_seer_action
from seat_order_neutral import (
    STRATEGY_SUBSEED_SCHEME,
    TIE_BREAK_SCHEME,
    build_neutral_actor_order,
    choose_neutral_candidate,
    get_actor_uid,
    get_displayed_to_physical_mapping_from_state,
    get_physical_to_displayed_mapping_from_state,
    initialize_neutral_player_metadata,
    json_dump,
    order_players_by_actor_order,
)
from speaker_memory import (
    apply_speaker_memory_from_credibility_event,
    apply_speaker_memory_from_reveal,
    calculate_trust_speech_multiplier,
    get_average_trust_received,
    initialize_speaker_memory,
    observe_speech,
)
from speech_action import generate_speech_action
from suspicion_update import update_suspicion_after_vote
from trust_update import update_trust_from_vote_outcome
from voting import choose_vote_target
from wolf_deception import generate_wolf_deception_action
from wolf_strategy import choose_wolf_kill_target
from witch_action import perform_witch_save, perform_witch_poison


class Game:
    """
    Minimal runnable Werewolf game loop.

    This version only handles random wolf kills, random day votes,
    phase switching, and win-condition checks.
    """

    def __init__(
        self,
        players=None,
        use_suspicion_voting=True,
        enable_suspicion_update=True,
        enable_seer=True,
        enable_witch=True,
        enable_hunter=None,
        enable_speech=True,
        enable_herding=None,
        herding_alpha=None,
        herding_beta=None,
        herding_gamma=None,
        enable_role_prior=None,
        role_prior_alpha=None,
        role_prior_beta=None,
        role_prior_gamma=None,
        role_prior_delta=None,
        enable_wolf_strategy=None,
        wolf_kill_strategy=None,
        wolf_kill_noise_level=None,
        enable_wolf_deception=None,
        wolf_deception_strategy=None,
        enable_deception_credibility=None,
        enable_speaker_memory=None,
        enable_last_words=False,
        enable_risk_preference=False,
        risk_preference_mode="mixed",
        speaker_memory_weight=None,
        trust_vote_weight=None,
        enable_trust_weighted_speech=None,
        trust_speech_min_multiplier=None,
        trust_speech_max_multiplier=None,
        enable_trust_weighted_herding=None,
        trust_herding_min_multiplier=None,
        trust_herding_max_multiplier=None,
        witch_poison_threshold=None,
        witch_save_probability=None,
        role_setup=None,
        initial_p_wolf=None,
        speech_signal_scale=1.0,
        credibility_cost_scale=1.0,
        seer_check_strategy="default",
        seer_avoid_repeat_checks=False,
        enable_position_model=False,
        randomize_seat_roles=False,
        seat_order_neutral_mode=False,
        neutral_seed=None,
        base_game_index=None,
        label_condition=None,
        rotation_offset=0,
        physical_to_displayed_mapping=None,
        main_game_seed=None,
        enable_ml_wolf_kill_policy=False,
        ml_wolf_kill_policy_name="existing_rule",
        ml_wolf_kill_model_manifest_path=None,
        ml_wolf_kill_manifest_hash=None,
        ml_wolf_kill_epsilon=0.10,
        ml_wolf_kill_hybrid_weight=0.50,
        enable_ml_stage2b_policy=False,
        ml_stage2b_selective_override_manifest_path=None,
    ):
        if players is None:
            players = create_default_players(
                role_setup=role_setup,
                initial_p_wolf=initial_p_wolf,
            )
        elif initial_p_wolf is not None:
            for player in players:
                player.p_wolf = initial_p_wolf

        if witch_poison_threshold is None:
            witch_poison_threshold = DEFAULT_WITCH_POISON_THRESHOLD

        if witch_save_probability is None:
            witch_save_probability = 0.7

        if enable_hunter is None:
            enable_hunter = DEFAULT_ENABLE_HUNTER

        if enable_herding is None:
            enable_herding = DEFAULT_ENABLE_HERDING

        if herding_alpha is None:
            herding_alpha = DEFAULT_HERDING_ALPHA

        if herding_beta is None:
            herding_beta = DEFAULT_HERDING_BETA

        if herding_gamma is None:
            herding_gamma = DEFAULT_HERDING_GAMMA

        if enable_role_prior is None:
            enable_role_prior = DEFAULT_ENABLE_ROLE_PRIOR

        if role_prior_alpha is None:
            role_prior_alpha = DEFAULT_ROLE_PRIOR_ALPHA

        if role_prior_beta is None:
            role_prior_beta = DEFAULT_ROLE_PRIOR_BETA

        if role_prior_gamma is None:
            role_prior_gamma = DEFAULT_ROLE_PRIOR_GAMMA

        if role_prior_delta is None:
            role_prior_delta = DEFAULT_ROLE_PRIOR_DELTA

        if enable_wolf_strategy is None:
            enable_wolf_strategy = DEFAULT_ENABLE_WOLF_STRATEGY

        if wolf_kill_strategy is None:
            wolf_kill_strategy = DEFAULT_WOLF_KILL_STRATEGY

        if wolf_kill_noise_level is None:
            wolf_kill_noise_level = DEFAULT_WOLF_KILL_NOISE_LEVEL

        if enable_wolf_deception is None:
            enable_wolf_deception = DEFAULT_ENABLE_WOLF_DECEPTION

        if wolf_deception_strategy is None:
            wolf_deception_strategy = DEFAULT_WOLF_DECEPTION_STRATEGY

        if enable_deception_credibility is None:
            enable_deception_credibility = DEFAULT_ENABLE_DECEPTION_CREDIBILITY

        if enable_speaker_memory is None:
            enable_speaker_memory = DEFAULT_ENABLE_SPEAKER_MEMORY

        if enable_last_words is None:
            enable_last_words = DEFAULT_ENABLE_LAST_WORDS

        if enable_risk_preference is None:
            enable_risk_preference = DEFAULT_ENABLE_RISK_PREFERENCE

        if speaker_memory_weight is None and trust_vote_weight is not None:
            speaker_memory_weight = trust_vote_weight

        if speaker_memory_weight is None:
            speaker_memory_weight = DEFAULT_TRUST_VOTE_WEIGHT

        if enable_trust_weighted_speech is None:
            enable_trust_weighted_speech = (
                DEFAULT_ENABLE_TRUST_WEIGHTED_SPEECH
            )

        if trust_speech_min_multiplier is None:
            trust_speech_min_multiplier = (
                DEFAULT_TRUST_SPEECH_MIN_MULTIPLIER
            )

        if trust_speech_max_multiplier is None:
            trust_speech_max_multiplier = (
                DEFAULT_TRUST_SPEECH_MAX_MULTIPLIER
            )

        if enable_trust_weighted_herding is None:
            enable_trust_weighted_herding = (
                DEFAULT_ENABLE_TRUST_WEIGHTED_HERDING
            )

        if trust_herding_min_multiplier is None:
            trust_herding_min_multiplier = (
                DEFAULT_TRUST_HERDING_MIN_MULTIPLIER
            )

        if trust_herding_max_multiplier is None:
            trust_herding_max_multiplier = (
                DEFAULT_TRUST_HERDING_MAX_MULTIPLIER
            )

        if speech_signal_scale is None:
            speech_signal_scale = 1.0

        if credibility_cost_scale is None:
            credibility_cost_scale = 1.0

        if seer_check_strategy is None:
            seer_check_strategy = "default"

        if seer_avoid_repeat_checks is None:
            seer_avoid_repeat_checks = False

        self.enable_position_model = enable_position_model
        self.randomize_seat_roles = randomize_seat_roles
        self.seat_order_neutral_mode = seat_order_neutral_mode
        self.neutral_seed = neutral_seed
        self.base_game_index = base_game_index
        self.label_condition = label_condition
        self.rotation_offset = rotation_offset
        self.main_game_seed = main_game_seed
        seat_role_assignment_event = None

        if self.randomize_seat_roles:
            if len(players) != 10:
                raise ValueError(
                    "randomize_seat_roles requires a 10-player game."
                )

            assign_random_roles_to_seats(players)
            seat_role_assignment_event = summarize_seat_role_assignment(
                players
            )
        elif (
            self.enable_position_model
            and len(players) == 10
            and not self.seat_order_neutral_mode
        ):
            assign_positions(players)

        if self.seat_order_neutral_mode:
            physical_to_displayed_mapping = initialize_neutral_player_metadata(
                players,
                mapping=physical_to_displayed_mapping,
            )
            self.neutral_actor_iteration_order = build_neutral_actor_order(
                players,
                seed=self.neutral_seed,
                base_game_index=self.base_game_index,
            )
            players = order_players_by_actor_order(
                players,
                self.neutral_actor_iteration_order,
            )
        else:
            self.neutral_actor_iteration_order = []

        self.state = GameState(players)
        self.state.seat_order_neutral_mode = self.seat_order_neutral_mode
        self.state.neutral_seed = self.neutral_seed
        self.state.base_game_index = self.base_game_index
        self.state.label_condition = self.label_condition
        self.state.rotation_offset = self.rotation_offset
        self.state.main_game_seed = self.main_game_seed
        if self.seat_order_neutral_mode:
            self.state.neutral_actor_iteration_order = (
                self.neutral_actor_iteration_order
            )
            self.state.physical_to_displayed_mapping = (
                physical_to_displayed_mapping
            )
            self.state.displayed_to_physical_mapping = (
                get_displayed_to_physical_mapping_from_state(self.state)
            )
        self.event_log = []
        self.payoffs = {}
        self.use_suspicion_voting = use_suspicion_voting
        self.enable_suspicion_update = enable_suspicion_update
        self.enable_seer = enable_seer
        self.enable_witch = enable_witch
        self.enable_speech = enable_speech
        self.enable_herding = enable_herding
        self.herding_alpha = herding_alpha
        self.herding_beta = herding_beta
        self.herding_gamma = herding_gamma
        self.enable_role_prior = enable_role_prior
        self.role_prior_alpha = role_prior_alpha
        self.role_prior_beta = role_prior_beta
        self.role_prior_gamma = role_prior_gamma
        self.role_prior_delta = role_prior_delta
        self.enable_wolf_strategy = enable_wolf_strategy
        self.wolf_kill_strategy = wolf_kill_strategy
        self.wolf_kill_noise_level = wolf_kill_noise_level
        self.enable_wolf_deception = enable_wolf_deception
        self.wolf_deception_strategy = wolf_deception_strategy
        self.enable_deception_credibility = enable_deception_credibility
        self.enable_speaker_memory = enable_speaker_memory
        self.enable_last_words = enable_last_words
        self.enable_risk_preference = enable_risk_preference
        self.risk_preference_mode = risk_preference_mode
        self.speaker_memory_weight = speaker_memory_weight
        self.enable_trust_weighted_speech = enable_trust_weighted_speech
        self.trust_speech_min_multiplier = trust_speech_min_multiplier
        self.trust_speech_max_multiplier = trust_speech_max_multiplier
        self.enable_trust_weighted_herding = enable_trust_weighted_herding
        self.trust_herding_min_multiplier = trust_herding_min_multiplier
        self.trust_herding_max_multiplier = trust_herding_max_multiplier
        self.witch_poison_threshold = witch_poison_threshold
        self.witch_save_probability = witch_save_probability
        self.enable_hunter = enable_hunter
        self.speech_signal_scale = speech_signal_scale
        self.credibility_cost_scale = credibility_cost_scale
        self.seer_check_strategy = seer_check_strategy
        self.seer_avoid_repeat_checks = seer_avoid_repeat_checks
        self.enable_ml_wolf_kill_policy = enable_ml_wolf_kill_policy
        self.ml_wolf_kill_policy_name = ml_wolf_kill_policy_name
        self.ml_wolf_kill_model_manifest_path = (
            ml_wolf_kill_model_manifest_path
        )
        self.ml_wolf_kill_manifest_hash = ml_wolf_kill_manifest_hash
        self.ml_wolf_kill_epsilon = ml_wolf_kill_epsilon
        self.ml_wolf_kill_hybrid_weight = ml_wolf_kill_hybrid_weight
        self.enable_ml_stage2b_policy = enable_ml_stage2b_policy
        self.ml_stage2b_selective_override_manifest_path = (
            ml_stage2b_selective_override_manifest_path
        )

        if self.enable_risk_preference:
            assign_risk_preferences(
                self.state.players,
                mode=self.risk_preference_mode,
            )

        if self.enable_speaker_memory:
            initialize_speaker_memory(self.state.players)

        if self.seat_order_neutral_mode:
            self.log_event(
                "seat_order_neutral_setup",
                {
                    "seat_order_neutral_mode": True,
                    "neutral_seed": self.neutral_seed,
                    "base_game_index": self.base_game_index,
                    "label_condition": self.label_condition,
                    "rotation_offset": self.rotation_offset,
                    "actor_uid_to_physical_seat": {
                        player.actor_uid: player.physical_seat
                        for player in self.state.players
                    },
                    "actor_uid_to_displayed_id": {
                        player.actor_uid: player.player_id
                        for player in self.state.players
                    },
                    "physical_to_displayed_mapping": (
                        get_physical_to_displayed_mapping_from_state(
                            self.state
                        )
                    ),
                    "displayed_to_physical_mapping": (
                        get_displayed_to_physical_mapping_from_state(
                            self.state
                        )
                    ),
                    "neutral_actor_iteration_order": (
                        self.neutral_actor_iteration_order
                    ),
                    "tie_break_scheme": TIE_BREAK_SCHEME,
                    "strategy_subseed_scheme": STRATEGY_SUBSEED_SCHEME,
                    "main_game_seed": self.main_game_seed,
                },
            )

        if seat_role_assignment_event is not None:
            self.log_event(
                "seat_role_assignment",
                {
                    "randomize_seat_roles": True,
                    **seat_role_assignment_event,
                },
            )

    def log_event(self, event_type, content):
        event = {
            "round": self.state.round_number,
            "phase": self.state.phase,
            "event_type": event_type,
            "content": content,
        }
        self.event_log.append(event)
        update_beliefs_from_event(self.state, event)

    def get_alive_players(self):
        return self.state.get_alive_players()

    def get_alive_wolves(self):
        return self.state.get_alive_wolves()

    def get_alive_villagers(self):
        return self.state.get_alive_villagers()

    def log_player_death(self, player_id, cause):
        self.log_event("player_death", {
            "player": player_id,
            "cause": cause,
        })

        if not self.enable_deception_credibility:
            return

        penalty_event = apply_wrong_accusation_penalties(
            self.state,
            self.event_log,
            player_id,
            suspicion_penalty=(
                DEFAULT_WRONG_ACCUSATION_SUSPICION_PENALTY
                * self.credibility_cost_scale
            ),
            p_wolf_penalty=(
                DEFAULT_WRONG_ACCUSATION_P_WOLF_PENALTY
                * self.credibility_cost_scale
            ),
        )

        if penalty_event is not None:
            self.log_event("wrong_accusation_penalty", penalty_event)

        if self.enable_speaker_memory:
            memory_event = apply_speaker_memory_from_reveal(
                self.state,
                self.event_log,
                player_id,
            )

            if memory_event is not None:
                self.log_event("speaker_trust_update", memory_event)

    def log_last_words_after_death(self, player_id, cause_of_death):
        try:
            player = self.state.get_player_by_id(player_id)
        except ValueError:
            return None

        if not can_give_last_words(
            player,
            self.state,
            cause_of_death,
            self.enable_last_words,
        ):
            return None

        last_words_event = generate_last_words(
            player,
            self.state,
            cause_of_death=cause_of_death,
        )
        player.has_given_last_words = True
        self.log_event("last_words", last_words_event)

        if self.enable_speaker_memory:
            observe_speech(self.state, last_words_event)

        return last_words_event

    def kill_player_with_hunter_check(self, player_id, cause):
        player = self.state.get_player_by_id(player_id)

        if not player.alive:
            return

        self.state.kill_player(player_id)
        self.log_player_death(player_id, cause)

        if not self.enable_hunter or self.state.game_over:
            return

        shot_target_id, shot_event = perform_hunter_shot(
            self.state,
            player_id,
        )

        if shot_event is not None:
            self.log_event("hunter_shot", shot_event)

        if shot_target_id is None or self.state.game_over:
            return

        try:
            shot_target = self.state.get_player_by_id(shot_target_id)
        except ValueError:
            return

        if not shot_target.alive:
            return

        self.state.kill_player(shot_target_id)
        self.log_player_death(shot_target_id, "hunter_shot")

    def night_phase(self):
        if self.state.game_over:
            return

        alive_wolves = self.get_alive_wolves()
        alive_villagers = self.get_alive_villagers()

        if not alive_wolves or not alive_villagers:
            self.state.check_win_condition()
            return

        if self.enable_seer:
            seer_event = perform_seer_action(
                self.state,
                seer_check_strategy=self.seer_check_strategy,
                event_log=self.event_log,
                avoid_repeat=self.seer_avoid_repeat_checks,
            )
            if seer_event is not None:
                self.log_event("seer_check", seer_event)

        wolf_kill_strategy = (
            self.wolf_kill_strategy
            if self.enable_wolf_strategy
            else "random"
        )
        ml_policy_event = None

        if self.enable_ml_wolf_kill_policy:
            from ml_stage2b_interventions import (
                STAGE2B_WOLF_KILL_POLICIES,
                choose_stage2b_wolf_kill_target,
            )

            if (
                self.enable_ml_stage2b_policy
                and self.ml_wolf_kill_policy_name
                in STAGE2B_WOLF_KILL_POLICIES
            ):
                target, ml_policy_event = choose_stage2b_wolf_kill_target(
                    self,
                    policy_name=self.ml_wolf_kill_policy_name,
                    manifest_path=self.ml_wolf_kill_model_manifest_path,
                    selective_override_manifest_path=(
                        self.ml_stage2b_selective_override_manifest_path
                    ),
                    existing_rule_strategy=wolf_kill_strategy,
                    epsilon=self.ml_wolf_kill_epsilon,
                )
            else:
                from ml_wolf_kill_policy import (
                    choose_stage2a_wolf_kill_target,
                )

                target, ml_policy_event = choose_stage2a_wolf_kill_target(
                    self,
                    policy_name=self.ml_wolf_kill_policy_name,
                    manifest_path=self.ml_wolf_kill_model_manifest_path,
                    existing_rule_strategy=wolf_kill_strategy,
                    epsilon=self.ml_wolf_kill_epsilon,
                )
            wolf_kill_strategy = self.ml_wolf_kill_policy_name
            if ml_policy_event is not None:
                self.log_event(
                    "wolf_kill_policy_decision",
                    ml_policy_event,
                )
        else:
            target = choose_wolf_kill_target(
                self.state,
                strategy=wolf_kill_strategy,
                noise_level=self.wolf_kill_noise_level,
            )

        if target is None:
            self.state.check_win_condition()
            return

        night_kill_target_id = target.player_id

        saved = False
        save_event = None
        poison_excluded_witch_ids = set()

        if self.enable_witch:
            saved, save_event = perform_witch_save(
                self.state,
                night_kill_target_id,
                save_probability=self.witch_save_probability,
            )

        if save_event is not None:
            self.log_event("witch_save", save_event)
            poison_excluded_witch_ids.add(save_event["witch"])

        if not saved:
            self.kill_player_with_hunter_check(
                night_kill_target_id,
                cause="night_kill",
            )
            self.log_event(
                "night_kill",
                {
                    "target": night_kill_target_id,
                    "strategy": wolf_kill_strategy,
                },
            )
            self.log_last_words_after_death(
                night_kill_target_id,
                "night_kill",
            )
        else:
            self.log_event(
                "night_kill_prevented",
                {
                    "target": night_kill_target_id,
                    "strategy": wolf_kill_strategy,
                },
            )

        if self.state.game_over:
            return

        if not self.enable_witch:
            return

        poison_target_id, poison_event = perform_witch_poison(
            self.state,
            suspicion_threshold=self.witch_poison_threshold,
            excluded_witch_ids=poison_excluded_witch_ids,
            enable_risk_preference=self.enable_risk_preference,
        )

        if poison_event is not None:
            self.log_event("witch_poison", poison_event)

        if poison_target_id is None or self.state.game_over:
            return

        try:
            poison_player = self.state.get_player_by_id(poison_target_id)
        except ValueError:
            return

        if poison_player.alive:
            self.kill_player_with_hunter_check(
                poison_target_id,
                cause="witch_poison",
            )

    def day_phase(self):
        if self.state.game_over:
            return

        alive_players = self.get_alive_players()

        if len(alive_players) < 2:
            self.state.check_win_condition()
            return

        speech_events = []

        if self.enable_speech:
            for player in alive_players:
                if self.enable_wolf_deception and player.is_wolf():
                    speech_event = generate_wolf_deception_action(
                        player,
                        self.state,
                        strategy=self.wolf_deception_strategy,
                        event_log=self.event_log,
                        enable_risk_preference=(
                            self.enable_risk_preference
                        ),
                    )

                    if speech_event is None:
                        speech_event = generate_speech_action(
                            player,
                            self.state,
                            enable_risk_preference=(
                                self.enable_risk_preference
                            ),
                        )
                else:
                    speech_event = generate_speech_action(
                        player,
                        self.state,
                        enable_risk_preference=(
                            self.enable_risk_preference
                        ),
                    )

                speech_event["speaker_risk_preference"] = getattr(
                    player,
                    "risk_preference",
                    "neutral",
                )

                if (
                    self.enable_speaker_memory
                    and self.enable_trust_weighted_speech
                ):
                    speaker_average_trust = get_average_trust_received(
                        self.state,
                        player.player_id,
                    )
                    trust_speech_multiplier = (
                        calculate_trust_speech_multiplier(
                            self.state,
                            player.player_id,
                            min_multiplier=(
                                self.trust_speech_min_multiplier
                            ),
                            max_multiplier=(
                                self.trust_speech_max_multiplier
                            ),
                        )
                    )
                else:
                    speaker_average_trust = 0.5
                    trust_speech_multiplier = 1.0

                speech_event["speaker_average_trust"] = speaker_average_trust
                speech_event["trust_speech_multiplier"] = (
                    trust_speech_multiplier * self.speech_signal_scale
                )
                speech_event["speech_signal_scale"] = (
                    self.speech_signal_scale
                )
                speech_event["trust_weighted_speech_enabled"] = (
                    self.enable_trust_weighted_speech
                )

                speech_events.append(speech_event)
                self.log_event("speech", speech_event)

                if self.enable_speaker_memory:
                    observe_speech(self.state, speech_event)

                if self.enable_deception_credibility:
                    credibility_event = apply_accusation_pressure_cost(
                        self.state,
                        speech_event,
                        self.event_log,
                        repeat_suspicion_cost=(
                            DEFAULT_REPEAT_SUSPICION_COST
                            * self.credibility_cost_scale
                        ),
                        repeat_p_wolf_cost=(
                            DEFAULT_REPEAT_P_WOLF_COST
                            * self.credibility_cost_scale
                        ),
                        false_accusation_base_suspicion_cost=(
                            DEFAULT_FALSE_ACCUSATION_BASE_SUSPICION_COST
                            * self.credibility_cost_scale
                        ),
                        false_accusation_base_p_wolf_cost=(
                            DEFAULT_FALSE_ACCUSATION_BASE_P_WOLF_COST
                            * self.credibility_cost_scale
                        ),
                    )

                    if credibility_event is not None:
                        self.log_event(
                            "accusation_pressure_cost",
                            credibility_event,
                        )

                        if self.enable_speaker_memory:
                            memory_event = (
                                apply_speaker_memory_from_credibility_event(
                                    self.state,
                                    "accusation_pressure_cost",
                                    credibility_event,
                                )
                            )

                            if memory_event is not None:
                                self.log_event(
                                    "speaker_trust_update",
                                    memory_event,
                                )

                    self_defense_event = apply_self_defense_credibility_cost(
                        self.state,
                        speech_event,
                        self.event_log,
                        repeat_self_defense_suspicion_cost=(
                            DEFAULT_REPEAT_SELF_DEFENSE_SUSPICION_COST
                            * self.credibility_cost_scale
                        ),
                        repeat_self_defense_p_wolf_cost=(
                            DEFAULT_REPEAT_SELF_DEFENSE_P_WOLF_COST
                            * self.credibility_cost_scale
                        ),
                        repeat_trust_building_suspicion_cost=(
                            DEFAULT_REPEAT_TRUST_BUILDING_SUSPICION_COST
                            * self.credibility_cost_scale
                        ),
                        repeat_trust_building_p_wolf_cost=(
                            DEFAULT_REPEAT_TRUST_BUILDING_P_WOLF_COST
                            * self.credibility_cost_scale
                        ),
                    )

                    if self_defense_event is not None:
                        self.log_event(
                            "self_defense_credibility_cost",
                            self_defense_event,
                        )

                        if self.enable_speaker_memory:
                            memory_event = (
                                apply_speaker_memory_from_credibility_event(
                                    self.state,
                                    "self_defense_credibility_cost",
                                    self_defense_event,
                                )
                            )

                            if memory_event is not None:
                                self.log_event(
                                    "speaker_trust_update",
                                    memory_event,
                                )

        votes = {}

        for voter in alive_players:
            if self.use_suspicion_voting:
                vote_speech_events = (
                    speech_events
                    if self.enable_herding or self.enable_role_prior
                    else None
                )
                role_prior_gamma = (
                    self.role_prior_gamma
                    if self.enable_herding
                    else 0.0
                )
                target = choose_vote_target(
                    voter,
                    alive_players,
                    recent_speech_events=vote_speech_events,
                    game_state=self.state,
                    event_log=self.event_log,
                    enable_speaker_memory=self.enable_speaker_memory,
                    speaker_memory_weight=self.speaker_memory_weight,
                    alpha=self.role_prior_alpha,
                    beta=self.role_prior_beta,
                    gamma=role_prior_gamma,
                    delta=self.role_prior_delta,
                    enable_role_prior=self.enable_role_prior,
                    enable_trust_weighted_herding=(
                        self.enable_trust_weighted_herding
                    ),
                    trust_herding_min_multiplier=(
                        self.trust_herding_min_multiplier
                    ),
                    trust_herding_max_multiplier=(
                        self.trust_herding_max_multiplier
                    ),
                    enable_risk_preference=self.enable_risk_preference,
                )
            else:
                possible_targets = [
                    player for player in alive_players
                    if player.player_id != voter.player_id
                ]
                if (
                    possible_targets
                    and self.seat_order_neutral_mode
                ):
                    target = choose_neutral_candidate(
                        self.state,
                        possible_targets,
                        "random_vote_target",
                        acting_player=voter,
                    )
                else:
                    target = (
                        random.choice(possible_targets)
                        if possible_targets
                        else None
                    )

            if target is None:
                continue

            voter.vote_target = target.player_id
            votes[voter.player_id] = target.player_id

        if not votes:
            self.state.check_win_condition()
            return

        vote_counts = Counter(votes.values())
        highest_vote_count = max(vote_counts.values())
        tied_targets = [
            player_id for player_id, vote_count in vote_counts.items()
            if vote_count == highest_vote_count
        ]
        if self.seat_order_neutral_mode and len(tied_targets) > 1:
            tied_players = [
                self.state.get_player_by_id(player_id)
                for player_id in tied_targets
            ]
            eliminated_player = choose_neutral_candidate(
                self.state,
                tied_players,
                "day_vote_elimination_tie",
                acting_player=None,
            )
            eliminated_id = eliminated_player.player_id
        else:
            eliminated_id = random.choice(tied_targets)

        if self.enable_suspicion_update:
            update_suspicion_after_vote(self.state, votes, eliminated_id)

        vote_outcome_trust_events = []

        if self.enable_speaker_memory:
            vote_outcome_trust_events = update_trust_from_vote_outcome(
                self.state,
                speech_events,
                eliminated_id,
            )

        self.kill_player_with_hunter_check(
            eliminated_id,
            cause="day_elimination",
        )
        self.log_last_words_after_death(eliminated_id, "voted_out")

        self.log_event("day_vote", {
            "method": (
                "suspicion_based"
                if self.use_suspicion_voting
                else "random"
            ),
            "votes": votes,
            "votes_by_actor_uid": {
                get_actor_uid(self.state.get_player_by_id(voter_id)): (
                    get_actor_uid(self.state.get_player_by_id(target_id))
                )
                for voter_id, target_id in votes.items()
            },
            "voter_risk_preference": {
                voter_id: getattr(
                    self.state.get_player_by_id(voter_id),
                    "risk_preference",
                    "neutral",
                )
                for voter_id in votes
            },
            "eliminated": eliminated_id,
            "eliminated_actor_uid": get_actor_uid(
                self.state.get_player_by_id(eliminated_id)
            ),
            "vote_outcome_trust_events": vote_outcome_trust_events,
            "suspicion_scores": {
                player.player_id: player.suspicion_score
                for player in self.state.players
            },
            "p_wolf_scores": {
                player.player_id: player.p_wolf
                for player in self.state.players
            },
            "herding_pressure": {
                player.player_id: calculate_herding_pressure(
                    self.state,
                    player.player_id,
                    recent_speech_events=speech_events,
                    enable_trust_weighted_herding=(
                        self.enable_trust_weighted_herding
                    ),
                    trust_herding_min_multiplier=(
                        self.trust_herding_min_multiplier
                    ),
                    trust_herding_max_multiplier=(
                        self.trust_herding_max_multiplier
                    ),
                )
                for player in self.state.players
            },
            "trust_weighted_herding_enabled": (
                self.enable_trust_weighted_herding
            ),
            "role_prior_scores": {
                player.player_id: (
                    calculate_role_prior_score(
                        self.state,
                        player.player_id,
                        recent_speech_events=speech_events,
                        event_log=self.event_log,
                    )
                    if self.enable_role_prior
                    else 0.0
                )
                for player in self.state.players
            },
            "speaker_trust_scores": {
                player.player_id: (
                    get_average_trust_received(
                        self.state,
                        player.player_id,
                    )
                    if self.enable_speaker_memory
                    else 0.5
                )
                for player in self.state.players
            },
            "neutral_mode_enabled": self.seat_order_neutral_mode,
        })

    def run_one_round(self):
        if self.state.game_over:
            return

        if self.state.phase != "night":
            self.state.phase = "night"

        self.night_phase()

        if self.state.game_over:
            return

        self.state.switch_phase()
        self.day_phase()

        if self.state.game_over:
            return

        self.state.switch_phase()
        self.state.reset_turn_actions()

    def run_game(self, max_rounds=20):
        rounds_played = 0

        while not self.state.game_over and rounds_played < max_rounds:
            self.run_one_round()
            rounds_played += 1

        if not self.state.game_over:
            self.state.game_over = True
            self.state.winner = "draw"

        from payoff import calculate_payoffs

        self.payoffs = calculate_payoffs(self)
        summary = self.state.summary()
        summary["payoffs"] = self.payoffs
        return summary


def create_default_players(
    role_setup=None,
    initial_p_wolf=None,
    risk_preferences=None,
):
    if role_setup is None:
        role_setup = DEFAULT_ROLE_SETUP

    players = [
        Player(player_id=i + 1, role=role)
        for i, role in enumerate(role_setup)
    ]

    if initial_p_wolf is not None:
        for player in players:
            player.p_wolf = initial_p_wolf

    if risk_preferences is not None:
        for player, risk_preference in zip(players, risk_preferences):
            player.risk_preference = risk_preference

    return players


if __name__ == "__main__":
    players = create_default_players()
    game = Game(players)

    result = game.run_game(max_rounds=20)

    print("Final result:")
    print(result)

    print("\nEvent log:")
    for event in game.event_log:
        print(event)
