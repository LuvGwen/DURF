"""Natural-language utterance generation for formal R2 BoW analysis.

The generator is a shadow feature system: it converts existing structured
speech events into observable text without changing game decisions.
"""

import hashlib
import random

from roles import HUNTER, SEER, WITCH
from seat_order_neutral import get_actor_uid


SPEECH_GENERATOR_VERSION = "r2_template_generator_v1"


def stable_seed(*parts):
    digest = hashlib.sha256(
        "|".join(str(part) for part in parts).encode("utf-8")
    ).hexdigest()
    return int(digest[:16], 16) % (2 ** 32)


def template(template_id, family, intent, subtype, text, holdout=False):
    return {
        "template_id": template_id,
        "template_family": family,
        "speech_intent": intent,
        "speech_subtype": subtype,
        "template_text": text,
        "template_split_group": "ood_template" if holdout else "primary",
        "generator_version": SPEECH_GENERATOR_VERSION,
    }


TEMPLATE_REGISTRY = [
    template("neutral_001", "neutral_observation", "neutral_statement", "low_information", "I am still listening and comparing the vote pattern.", False),
    template("neutral_002", "neutral_observation", "neutral_statement", "low_information", "For now I want more evidence before we push.", False),
    template("neutral_003", "neutral_waiting", "neutral_statement", "low_information", "The room feels unclear, so I will wait for a better reason.", False),
    template("neutral_ood_001", "neutral_process_ood", "neutral_statement", "low_information", "My read is not settled yet; I need another round of information.", True),
    template("accuse_001", "accusation_reasoned", "accusation", "standard_accusation", "I suspect PLAYER_TARGET because their vote record has a wolfish pattern.", False),
    template("accuse_002", "accusation_reasoned", "accusation", "standard_accusation", "PLAYER_TARGET looks suspicious; the logic around their push is weak.", False),
    template("accuse_003", "accusation_pressure", "accusation", "vote_pressure", "We should pressure PLAYER_TARGET and see whether the story changes.", False),
    template("accuse_ood_001", "accusation_chain_ood", "accusation", "standard_accusation", "The evidence points toward PLAYER_TARGET, and I want that claim tested.", True),
    template("strong_001", "strong_accusation_certainty", "strong_accusation", "high_certainty", "I am sure PLAYER_TARGET is hiding something; vote there now.", False),
    template("strong_002", "strong_accusation_urgency", "strong_accusation", "urgent_vote", "Stop drifting. PLAYER_TARGET is the danger today!", False),
    template("strong_ood_001", "strong_accusation_flashpoint_ood", "strong_accusation", "urgent_vote", "This is urgent: PLAYER_TARGET is the clear threat if we want to survive!", True),
    template("defense_001", "defense_evidence", "defense", "target_defense", "I defend PLAYER_TARGET because their record looks honest.", False),
    template("defense_002", "defense_vote_record", "defense", "target_defense", "PLAYER_TARGET has a village pattern in the vote history.", False),
    template("defense_ood_001", "defense_consistency_ood", "defense", "target_defense", "I do not see a wolf agenda from PLAYER_TARGET; the evidence is thin.", True),
    template("selfdef_001", "self_defense_denial", "self_defense", "denial", "I am not a wolf, and the case against me is a misread.", False),
    template("selfdef_002", "self_defense_counter_pressure", "self_defense", "counter_pressure", "That push on me is noise; question the reason before you vote.", False),
    template("selfdef_ood_001", "self_defense_process_ood", "self_defense", "denial", "The accusation against PLAYER_SELF does not match the public record.", True),
    template("trust_001", "trust_support_clear", "trust_support", "trust_target", "I trust PLAYER_TARGET for now; their reasoning has been clear.", False),
    template("trust_002", "trust_support_vote_follow", "trust_support", "trust_target", "I can follow PLAYER_TARGET because the plan is reasonable.", False),
    template("trust_ood_001", "trust_consensus_ood", "trust_support", "trust_target", "PLAYER_TARGET feels safe enough to coordinate with today.", True),
    template("vote_req_001", "vote_request_coalition", "vote_request", "vote_call", "Vote PLAYER_TARGET with me so the majority is not split.", False),
    template("vote_req_002", "vote_request_pressure", "vote_request", "vote_call", "Move votes to PLAYER_TARGET; this is the best pressure point.", False),
    template("vote_req_ood_001", "vote_request_deadline_ood", "vote_request", "vote_call", "Before the day ends, put the vote on PLAYER_TARGET.", True),
    template("vote_exp_001", "vote_explanation_reasoned", "vote_explanation", "reasoned_vote", "My vote on PLAYER_TARGET is because of the earlier pattern.", False),
    template("vote_exp_002", "vote_explanation_history", "vote_explanation", "reasoned_vote", "The vote history gives me a reason to choose PLAYER_TARGET.", False),
    template("vote_exp_ood_001", "vote_explanation_trace_ood", "vote_explanation", "reasoned_vote", "I am voting PLAYER_TARGET because the public sequence does not fit.", True),
    template("uncertain_001", "uncertainty_questioning", "uncertainty", "question", "Why should we trust that read on PLAYER_TARGET?", False),
    template("uncertain_002", "uncertainty_probe", "uncertainty", "probe", "Can someone explain the evidence against PLAYER_TARGET?", False),
    template("uncertain_ood_001", "uncertainty_counterfactual_ood", "uncertainty", "probe", "I am unsure; what changes if PLAYER_TARGET is actually village?", True),
    template("info_001", "information_report_check", "information_report", "seer_private_report", "My check says PLAYER_TARGET is CHECK_RESULT.", False),
    template("info_002", "information_report_vote_history", "information_report", "public_vote_report", "The vote history shows PLAYER_TARGET was central in the last push.", False),
    template("info_ood_001", "information_report_sequence_ood", "information_report", "public_vote_report", "The public sequence gives concrete evidence about PLAYER_TARGET.", True),
    template("seer_claim_001", "seer_claim_check", "seer_claim", "role_claim", "I claim seer and my check matters for PLAYER_TARGET.", False),
    template("seer_claim_ood_001", "seer_claim_result_ood", "seer_claim", "role_claim", "As a seer claim, I want the table to remember PLAYER_TARGET.", True),
    template("witch_claim_001", "witch_claim_potion", "witch_claim", "role_claim", "I claim witch; the save and poison choices matter now.", False),
    template("witch_claim_ood_001", "witch_claim_resource_ood", "witch_claim", "role_claim", "My witch claim is about potion risk, not a random story.", True),
    template("hunter_claim_001", "hunter_claim_retaliation", "hunter_claim", "role_claim", "I claim hunter, so a reckless push on me has a shot risk.", False),
    template("hunter_claim_ood_001", "hunter_claim_warning_ood", "hunter_claim", "role_claim", "As hunter, I am warning the village not to waste the vote.", True),
    template("counter_001", "counter_claim_conflict", "counter_claim", "role_conflict", "That role claim sounds fake; I counterclaim the story.", False),
    template("counter_ood_001", "counter_claim_timing_ood", "counter_claim", "role_conflict", "The timing of that claim is wrong, and I do not trust it.", True),
    template("deflect_001", "deflection_redirect", "deflection", "redirect", "Do not focus on me; PLAYER_TARGET is a better question.", False),
    template("deflect_002", "deflection_process", "deflection", "process_redirect", "This pressure is a distraction, so look at PLAYER_TARGET instead.", False),
    template("deflect_ood_001", "deflection_misdirection_ood", "deflection", "redirect", "The push on me is a frame; move attention to PLAYER_TARGET.", True),
    template("false_accuse_001", "false_accusation_pressure", "false_accusation", "deceptive_accusation", "I am certain PLAYER_TARGET is wolf; vote there before they hide.", False),
    template("false_accuse_002", "false_accusation_certainty", "false_accusation", "deceptive_accusation", "PLAYER_TARGET is the obvious threat, and waiting only helps wolves.", False),
    template("false_accuse_ood_001", "false_accusation_stampede_ood", "false_accusation", "deceptive_accusation", "Everyone should push PLAYER_TARGET now; the danger is obvious.", True),
    template("false_claim_001", "false_role_claim_authority", "false_role_claim", "deceptive_role_claim", "I claim ROLE_CLAIM, and that should clear my vote.", False),
    template("false_claim_ood_001", "false_role_claim_badge_ood", "false_role_claim", "deceptive_role_claim", "My ROLE_CLAIM claim gives me authority in this vote.", True),
    template("trust_build_001", "trust_building_soft", "trust_building", "deceptive_trust", "I trust PLAYER_TARGET, and I want us to coordinate together.", False),
    template("trust_build_002", "trust_building_coalition", "trust_building", "deceptive_trust", "PLAYER_TARGET and I are aligned on the plan, so follow this vote.", False),
    template("trust_build_ood_001", "trust_building_bridge_ood", "trust_building", "deceptive_trust", "I want to build trust with PLAYER_TARGET and keep the village together.", True),
    template("panic_001", "panic_urgency", "panic", "urgent_emotion", "This is panic time; if we miss now, the wolves control the vote!", False),
    template("panic_ood_001", "panic_countdown_ood", "panic", "urgent_emotion", "There is no time left, and a wrong vote is dangerous!", True),
    template("retaliate_001", "retaliation_counter", "retaliation", "counter_attack", "That accusation is a lie, so I suspect PLAYER_TARGET back.", False),
    template("retaliate_ood_001", "retaliation_mirror_ood", "retaliation", "counter_attack", "If PLAYER_TARGET attacks me with no reason, I will vote back.", True),
    template("coord_001", "coordination_plan", "coordination", "group_plan", "We need a plan: compare claims, then coordinate the vote.", False),
    template("coord_ood_001", "coordination_partition_ood", "coordination", "group_plan", "Split the reads into trust, suspect, and unsure before voting.", True),
    template("last_001", "last_words_warning", "last_words", "death_warning", "My last words are simple: remember who pushed this vote.", False),
    template("last_ood_001", "last_words_trace_ood", "last_words", "death_warning", "After I die, check the people who created this wagon.", True),
]


TEMPLATES_BY_INTENT = {}
for item in TEMPLATE_REGISTRY:
    TEMPLATES_BY_INTENT.setdefault(item["speech_intent"], []).append(item)


def safe_get_player(game_state, player_id):
    if player_id is None:
        return None
    try:
        return game_state.get_player_by_id(int(player_id))
    except (TypeError, ValueError):
        return None


def latest_private_seer_check(past_events, seer_id, target_id=None):
    for event in reversed(past_events):
        if event.get("event_type") != "seer_check":
            continue
        content = event.get("content", {})
        if content.get("seer") != seer_id:
            continue
        if target_id is not None and content.get("target") != target_id:
            continue
        return content
    return None


def infer_speech_intent(content, speaker, target, past_events, rng):
    deception_type = content.get("deception_type")
    speech_type = content.get("speech_type", "neutral")

    if deception_type == "false_accuse":
        return "false_accusation", "deceptive_accusation"
    if deception_type == "false_defend":
        return "defense", "deceptive_defense"
    if deception_type == "false_role_claim":
        return "false_role_claim", "deceptive_role_claim"
    if deception_type == "deflect_suspicion":
        return "deflection", "redirect"
    if deception_type == "trust_building":
        return "trust_building", "deceptive_trust"

    private_check = None
    if speaker.role == SEER:
        private_check = latest_private_seer_check(
            past_events,
            speaker.player_id,
            target.player_id if target is not None else None,
        )
    if private_check is not None and speech_type in {"accuse", "trust", "claim_role"}:
        return "information_report", "seer_private_report"

    if speech_type == "accuse":
        if float(content.get("speaker_suspicion", 0.0)) >= 0.45:
            return "strong_accusation", "high_certainty"
        return rng.choice([
            ("accusation", "standard_accusation"),
            ("vote_request", "vote_call"),
            ("vote_explanation", "reasoned_vote"),
        ])
    if speech_type == "defend":
        return "defense", "target_defense"
    if speech_type == "claim_role":
        if speaker.role == SEER:
            return "seer_claim", "role_claim"
        if speaker.role == WITCH:
            return "witch_claim", "role_claim"
        if speaker.role == HUNTER:
            return "hunter_claim", "role_claim"
        return "counter_claim", "role_conflict"
    if speech_type == "deny":
        return "self_defense", "denial"
    if speech_type == "agree":
        return rng.choice([
            ("trust_support", "trust_target"),
            ("coordination", "group_plan"),
        ])
    if speech_type == "question":
        return "uncertainty", "question"
    if speech_type == "trust":
        return "trust_support", "trust_target"
    if speech_type == "last_words":
        return "last_words", "death_warning"
    return "neutral_statement", "low_information"


def choose_template_for_intent(intent, dataset_split, rng):
    templates = TEMPLATES_BY_INTENT.get(intent) or TEMPLATES_BY_INTENT[
        "neutral_statement"
    ]
    if dataset_split == "ood_template":
        preferred = [
            item for item in templates
            if item["template_split_group"] == "ood_template"
        ]
    else:
        preferred = [
            item for item in templates
            if item["template_split_group"] == "primary"
        ]
    return rng.choice(preferred or templates)


def public_information_summary(game_state, past_events):
    deaths = sum(1 for event in past_events if event.get("event_type") == "player_death")
    votes = sum(1 for event in past_events if event.get("event_type") == "day_vote")
    speeches = sum(1 for event in past_events if event.get("event_type") in {"speech", "last_words"})
    return (
        f"round={game_state.round_number};phase={game_state.phase};"
        f"past_deaths={deaths};past_votes={votes};past_speeches={speeches}"
    )


def render_template(template_row, content, speaker, target, check_content):
    false_claim_role = content.get("false_claim_role") or speaker.role
    if check_content is None:
        check_result = "unclear"
    else:
        check_result = "wolf" if check_content.get("target_is_wolf") else "not wolf"
    text = template_row["template_text"]
    text = text.replace("PLAYER_SELF", "PLAYER_SELF")
    text = text.replace("PLAYER_TARGET", "PLAYER_TARGET" if target else "PLAYER_OTHER")
    text = text.replace("ROLE_CLAIM", str(false_claim_role))
    text = text.replace("CHECK_RESULT", check_result)
    return text


def generate_utterance_from_speech_event(
    game_state,
    event,
    past_events,
    game_id,
    seed,
    base_game_index,
    behavioral_regime,
    dataset_split,
    source_event_index,
):
    content = event.get("content", {})
    speaker = safe_get_player(game_state, content.get("speaker"))
    if speaker is None:
        raise ValueError("Speech event has no valid speaker.")
    target = safe_get_player(game_state, content.get("target"))
    rng = random.Random(
        stable_seed(
            SPEECH_GENERATOR_VERSION,
            game_id,
            source_event_index,
            content.get("speaker"),
            content.get("target"),
            content.get("speech_type"),
            content.get("deception_type"),
        )
    )
    intent, subtype = infer_speech_intent(
        content,
        speaker,
        target,
        past_events,
        rng,
    )
    check_content = None
    private_information_used = "none"
    if intent in {"information_report", "seer_claim"}:
        check_content = latest_private_seer_check(
            past_events,
            speaker.player_id,
            target.player_id if target is not None else None,
        )
        if check_content is not None:
            private_information_used = "seer_private_check"
            if target is None:
                target = safe_get_player(game_state, check_content.get("target"))
    if content.get("is_deception"):
        private_information_used = (
            "wolf_team_private_identity"
            if private_information_used == "none"
            else f"{private_information_used};wolf_team_private_identity"
        )
    template_row = choose_template_for_intent(intent, dataset_split, rng)
    text = render_template(template_row, content, speaker, target, check_content)
    utterance_id = "utt_" + hashlib.sha256(
        f"{game_id}|{source_event_index}|{template_row['template_id']}".encode(
            "utf-8"
        )
    ).hexdigest()[:16]
    target_uid = get_actor_uid(target) if target is not None else ""

    return {
        "utterance_id": utterance_id,
        "game_id": game_id,
        "game_family_id": f"{dataset_split}_{behavioral_regime}_{seed}_{base_game_index}",
        "base_configuration_id": f"r2_{dataset_split}_{behavioral_regime}",
        "seed": seed,
        "round": event.get("round"),
        "phase": event.get("phase"),
        "speaker_uid": get_actor_uid(speaker),
        "speaker_team": speaker.team,
        "speaker_role": speaker.role,
        "speech_intent": intent,
        "speech_subtype": subtype,
        "target_uid": target_uid,
        "utterance_text": text,
        "template_family": template_row["template_family"],
        "template_id": template_row["template_id"],
        "behavioral_regime": behavioral_regime,
        "dataset_split": dataset_split,
        "deception_type": content.get("deception_type", ""),
        "speech_type": content.get("speech_type", ""),
        "public_information_available": public_information_summary(
            game_state,
            past_events,
        ),
        "private_information_used": private_information_used,
        "hidden_information_leakage_flag": "False",
        "source_event_index": source_event_index,
        "generator_version": SPEECH_GENERATOR_VERSION,
    }


def template_registry_rows():
    return [dict(row) for row in TEMPLATE_REGISTRY]


if __name__ == "__main__":
    from game import Game

    random.seed(42)
    game = Game(enable_speech=True, enable_wolf_deception=True)
    game.run_game(max_rounds=3)
    past = []
    for index, item in enumerate(game.event_log):
        if item.get("event_type") == "speech":
            print(generate_utterance_from_speech_event(
                game.state,
                item,
                past,
                "demo_game",
                42,
                1,
                "demo",
                "train",
                index,
            ))
            break
        past.append(item)
