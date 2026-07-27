"""Werewolf Bag-of-Words lexicon definitions.

This module keeps the small Stage 2 speech-token API intact while adding the
formal R2 core lexicon used for transparent BoW scoring.
"""

import csv
from pathlib import Path


SPEECH_TYPES = [
    "accuse",
    "defend",
    "claim_role",
    "deny",
    "agree",
    "question",
    "trust",
    "neutral",
]


BOW_LEXICON = {
    "accuse": [
        "suspicious",
        "wolf",
        "vote",
        "pressure",
        "fake",
    ],
    "defend": [
        "village",
        "honest",
        "clear",
        "help",
        "not_wolf",
    ],
    "claim_role": [
        "claim",
        "role",
        "seer",
        "witch",
        "hunter",
    ],
    "deny": [
        "deny",
        "false",
        "not_me",
        "wrong",
        "frame",
    ],
    "agree": [
        "agree",
        "same",
        "reasonable",
        "support",
        "yes",
    ],
    "question": [
        "why",
        "explain",
        "question",
        "evidence",
        "logic",
    ],
    "trust": [
        "trust",
        "clear",
        "village",
        "safe",
        "believe",
    ],
    "neutral": [
        "observe",
        "unsure",
        "wait",
        "think",
        "listen",
    ],
}


DEFAULT_NUM_TOKENS = 3
CORE_LEXICON_VERSION = "r2_core_lexicon_v1_frozen_pre_evaluation"

CORE_LEXICON_COLUMNS = [
    "token",
    "semantic_group",
    "polarity",
    "intensity_weight",
    "information_weight",
    "werewolf_leaning_weight",
    "source",
    "rationale",
    "included_in_primary_score",
    "notes",
]


def _row(
    token,
    semantic_group,
    polarity,
    intensity_weight,
    information_weight,
    werewolf_leaning_weight,
    rationale,
    included=True,
    notes="",
):
    return {
        "token": token,
        "semantic_group": semantic_group,
        "polarity": polarity,
        "intensity_weight": float(intensity_weight),
        "information_weight": float(information_weight),
        "werewolf_leaning_weight": float(werewolf_leaning_weight),
        "source": CORE_LEXICON_VERSION,
        "rationale": rationale,
        "included_in_primary_score": str(bool(included)),
        "notes": notes,
    }


CORE_LEXICON_ROWS = [
    _row("accuse", "accusation", "wolf_leaning", 0.40, 0.35, 0.35, "Direct accusation verb."),
    _row("suspect", "accusation", "wolf_leaning", 0.35, 0.30, 0.30, "Suspicion statement."),
    _row("suspicious", "suspicion", "wolf_leaning", 0.30, 0.25, 0.25, "Suspicion adjective."),
    _row("pressure", "accusation", "wolf_leaning", 0.35, 0.20, 0.30, "Coalition pressure language."),
    _row("push", "accusation", "wolf_leaning", 0.25, 0.20, 0.20, "Vote-steering language."),
    _row("liar", "accusation", "wolf_leaning", 0.70, 0.10, 0.45, "High-intensity credibility attack."),
    _row("fake", "deception", "wolf_leaning", 0.55, 0.20, 0.40, "Deception allegation or deceptive framing."),
    _row("frame", "deception", "wolf_leaning", 0.45, 0.25, 0.35, "Misdirection or framing claim."),
    _row("wolf", "suspicion", "wolf_leaning", 0.45, 0.45, 0.50, "Core role accusation word."),
    _row("wolfish", "suspicion", "wolf_leaning", 0.35, 0.30, 0.45, "Indirect wolf-likeness claim."),
    _row("pack", "suspicion", "wolf_leaning", 0.35, 0.25, 0.35, "Wolf-team reference."),
    _row("hidden", "suspicion", "wolf_leaning", 0.25, 0.20, 0.25, "Concealment language."),
    _row("cover", "deception", "wolf_leaning", 0.25, 0.20, 0.30, "Cover-story language."),
    _row("agenda", "deception", "wolf_leaning", 0.35, 0.20, 0.35, "Strategic manipulation cue."),
    _row("slip", "evidence", "wolf_leaning", 0.25, 0.40, 0.30, "Evidence-like behavioral cue."),
    _row("signal", "evidence", "wolf_leaning", 0.20, 0.35, 0.20, "Evidence-like behavioral cue."),
    _row("sure", "certainty", "wolf_leaning", 0.45, 0.10, 0.25, "Strong certainty can reflect overclaiming."),
    _row("certain", "certainty", "wolf_leaning", 0.45, 0.10, 0.25, "Strong certainty can reflect overclaiming."),
    _row("obvious", "certainty", "wolf_leaning", 0.50, 0.10, 0.30, "Unsupported certainty cue."),
    _row("definitely", "certainty", "wolf_leaning", 0.50, 0.10, 0.30, "Unsupported certainty cue."),
    _row("never", "negation", "defensive", 0.30, 0.10, 0.05, "Negation preserved for denial language."),
    _row("not", "negation", "defensive", 0.20, 0.10, -0.05, "Negation preserved for denial language."),
    _row("maybe", "uncertainty", "neutral", 0.10, 0.10, -0.05, "Uncertainty marker."),
    _row("unsure", "uncertainty", "neutral", 0.10, 0.10, -0.05, "Uncertainty marker."),
    _row("unclear", "uncertainty", "neutral", 0.10, 0.10, -0.05, "Uncertainty marker."),
    _row("question", "uncertainty", "neutral", 0.10, 0.20, 0.05, "Information-seeking language."),
    _row("why", "uncertainty", "neutral", 0.10, 0.20, 0.05, "Information-seeking language."),
    _row("explain", "evidence", "neutral", 0.15, 0.35, 0.05, "Requests justification."),
    _row("possible", "uncertainty", "neutral", 0.10, 0.15, 0.00, "Moderated claim."),
    _row("doubt", "uncertainty", "neutral", 0.20, 0.15, 0.10, "Doubt or hesitation."),
    _row("defend", "defense", "village_leaning", 0.20, 0.25, -0.20, "Defense action language."),
    _row("clear", "defense", "village_leaning", 0.15, 0.30, -0.25, "Clearing language."),
    _row("honest", "defense", "village_leaning", 0.10, 0.15, -0.15, "Credibility support."),
    _row("village", "defense", "village_leaning", 0.15, 0.35, -0.30, "Village-team claim."),
    _row("not_wolf", "defense", "village_leaning", 0.25, 0.30, -0.25, "Direct denial."),
    _row("innocent", "defense", "village_leaning", 0.20, 0.20, -0.20, "Innocence claim."),
    _row("protect", "defense", "village_leaning", 0.10, 0.20, -0.15, "Protective framing."),
    _row("trust", "trust", "village_leaning", 0.10, 0.20, -0.20, "Trust support."),
    _row("believe", "trust", "village_leaning", 0.10, 0.20, -0.15, "Belief support."),
    _row("support", "trust", "village_leaning", 0.10, 0.20, -0.10, "Coalition support."),
    _row("safe", "trust", "village_leaning", 0.10, 0.20, -0.20, "Safety claim."),
    _row("agree", "trust", "neutral", 0.10, 0.10, 0.05, "Agreement can amplify group pressure."),
    _row("ally", "trust", "village_leaning", 0.10, 0.20, -0.10, "Alliance language."),
    _row("deflect", "deception", "wolf_leaning", 0.30, 0.10, 0.35, "Suspicion redirection."),
    _row("divert", "deception", "wolf_leaning", 0.30, 0.10, 0.35, "Suspicion redirection."),
    _row("claim", "role_claim", "ambiguous", 0.20, 0.40, 0.10, "Observable role claim."),
    _row("counterclaim", "role_claim", "wolf_leaning", 0.40, 0.45, 0.25, "Role-claim conflict."),
    _row("story", "deception", "wolf_leaning", 0.20, 0.10, 0.20, "Narrative construction cue."),
    _row("mask", "deception", "wolf_leaning", 0.30, 0.10, 0.35, "Concealment cue."),
    _row("mislead", "misinformation", "wolf_leaning", 0.40, 0.20, 0.45, "Misinformation cue."),
    _row("vote", "voting", "neutral", 0.20, 0.35, 0.10, "Concrete vote action."),
    _row("votes", "voting", "neutral", 0.15, 0.35, 0.05, "Vote history reference."),
    _row("voted", "voting", "neutral", 0.15, 0.35, 0.05, "Vote history reference."),
    _row("eliminate", "voting", "wolf_leaning", 0.35, 0.30, 0.25, "Execution pressure."),
    _row("majority", "voting", "neutral", 0.20, 0.30, 0.10, "Coordination on votes."),
    _row("wagon", "voting", "wolf_leaning", 0.25, 0.25, 0.20, "Bandwagon pressure."),
    _row("tie", "voting", "neutral", 0.10, 0.25, 0.00, "Voting state reference."),
    _row("role", "role_claim", "ambiguous", 0.10, 0.35, 0.05, "Role discussion."),
    _row("seer", "role_claim", "ambiguous", 0.15, 0.45, 0.00, "Specific role word."),
    _row("witch", "role_claim", "ambiguous", 0.15, 0.45, 0.00, "Specific role word."),
    _row("hunter", "role_claim", "ambiguous", 0.15, 0.45, 0.00, "Specific role word."),
    _row("checked", "night_action", "neutral", 0.10, 0.55, -0.05, "Check-result reference."),
    _row("report", "evidence", "neutral", 0.10, 0.50, -0.05, "Information report."),
    _row("night", "night_action", "neutral", 0.10, 0.35, 0.00, "Night-action reference."),
    _row("kill", "night_action", "wolf_leaning", 0.40, 0.30, 0.25, "Night kill language."),
    _row("save", "night_action", "village_leaning", 0.15, 0.40, -0.15, "Witch save language."),
    _row("poison", "night_action", "wolf_leaning", 0.30, 0.40, 0.10, "Witch poison language."),
    _row("antidote", "night_action", "village_leaning", 0.10, 0.40, -0.10, "Witch antidote language."),
    _row("shot", "night_action", "neutral", 0.25, 0.35, 0.05, "Hunter shot language."),
    _row("panic", "emotional_intensity", "wolf_leaning", 0.80, 0.05, 0.25, "Panic cue."),
    _row("urgent", "emotional_intensity", "wolf_leaning", 0.70, 0.05, 0.25, "Urgency cue."),
    _row("now", "emotional_intensity", "wolf_leaning", 0.45, 0.05, 0.15, "Immediate action cue."),
    _row("angry", "emotional_intensity", "wolf_leaning", 0.70, 0.05, 0.25, "Emotional cue."),
    _row("serious", "emotional_intensity", "wolf_leaning", 0.45, 0.05, 0.10, "Intensity cue."),
    _row("stop", "emotional_intensity", "wolf_leaning", 0.55, 0.05, 0.20, "Urgent command."),
    _row("coordinate", "coordination", "neutral", 0.15, 0.40, 0.05, "Group coordination."),
    _row("plan", "coordination", "neutral", 0.10, 0.40, 0.00, "Group plan."),
    _row("follow", "coordination", "wolf_leaning", 0.20, 0.20, 0.15, "Coalition steering."),
    _row("together", "coordination", "neutral", 0.10, 0.20, 0.05, "Collective action."),
    _row("split", "coordination", "neutral", 0.10, 0.30, 0.00, "Vote split reference."),
    _row("because", "evidence", "neutral", 0.05, 0.50, -0.05, "Causal evidence marker."),
    _row("logic", "evidence", "neutral", 0.05, 0.45, -0.05, "Reasoning marker."),
    _row("evidence", "evidence", "neutral", 0.05, 0.55, -0.05, "Evidence marker."),
    _row("pattern", "evidence", "neutral", 0.05, 0.45, -0.05, "Pattern evidence."),
    _row("record", "evidence", "neutral", 0.05, 0.45, -0.05, "Historical evidence."),
    _row("reason", "evidence", "neutral", 0.05, 0.50, -0.05, "Reasoning marker."),
    _row("vote_history", "evidence", "neutral", 0.05, 0.55, -0.05, "Concrete vote-history reference."),
    _row("rumor", "misinformation", "wolf_leaning", 0.25, 0.05, 0.25, "Low-evidence claim."),
    _row("lie", "misinformation", "wolf_leaning", 0.50, 0.15, 0.40, "Misinformation accusation."),
    _row("misread", "misinformation", "neutral", 0.20, 0.10, 0.05, "Possible error cue."),
    _row("noise", "misinformation", "neutral", 0.15, 0.05, 0.05, "Low-information cue."),
    _row("threat", "threat", "wolf_leaning", 0.50, 0.20, 0.25, "Threat framing."),
    _row("danger", "threat", "wolf_leaning", 0.50, 0.15, 0.25, "Danger framing."),
    _row("risk", "threat", "neutral", 0.30, 0.20, 0.10, "Risk framing."),
]


CORE_LEXICON_BY_TOKEN = {
    row["token"]: row
    for row in CORE_LEXICON_ROWS
}


def semantic_tokens(group):
    return {
        row["token"]
        for row in CORE_LEXICON_ROWS
        if row["semantic_group"] == group
    }


def get_core_lexicon_rows():
    return [dict(row) for row in CORE_LEXICON_ROWS]


def write_core_lexicon_csv(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=CORE_LEXICON_COLUMNS,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(get_core_lexicon_rows())


if __name__ == "__main__":
    print(f"Core lexicon version: {CORE_LEXICON_VERSION}")
    print(f"Core lexicon size: {len(CORE_LEXICON_ROWS)}")
    print(f"Speech types: {', '.join(SPEECH_TYPES)}")
