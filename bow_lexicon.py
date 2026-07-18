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
