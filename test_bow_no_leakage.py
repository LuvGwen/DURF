from bow_evaluation import (
    DIRECT_ROLE_WORDS,
    PLAYER_PLACEHOLDER_WORDS,
    structured_feature_row,
    token_counts_for_row,
)
from bow_tokenizer import tokenize


PROHIBITED_FEATURE_FIELDS = {
    "speaker_role",
    "speaker_is_wolf",
    "eventual_winner",
    "later_vote_target",
    "later_elimination_target",
    "seed",
    "game_id",
    "speaker_uid",
    "template_id",
}


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}")


def test_model_feature_builders_exclude_labels_and_ids():
    row = {
        "speech_intent": "false_accusation",
        "speech_subtype": "deceptive_accusation",
        "speech_type": "accuse",
        "deception_type": "false_accuse",
        "behavioral_regime": "deception",
        "accusation_flag": "True",
        "defense_flag": "False",
        "role_claim_flag": "False",
        "trust_building_flag": "False",
        "deflection_flag": "False",
        "information_report_flag": "False",
        "speaker_role": "werewolf",
        "speaker_is_wolf": "True",
        "game_id": "secret",
        "seed": "300",
        "template_id": "x",
        "tokens": "wolf accuse player_target",
    }
    features = structured_feature_row(row)
    features.update(token_counts_for_row(row, remove_tokens=DIRECT_ROLE_WORDS))
    check(
        not (set(features) & PROHIBITED_FEATURE_FIELDS),
        "feature builders exclude prohibited label/id fields",
    )


def test_seed_and_game_numbers_do_not_survive_tokenization():
    tokens = tokenize("seed 300 game 400 player 2")
    check("300" not in tokens and "400" not in tokens and "2" not in tokens, "numbers removed or normalized")


if __name__ == "__main__":
    test_model_feature_builders_exclude_labels_and_ids()
    test_seed_and_game_numbers_do_not_survive_tokenization()
    print("test_bow_no_leakage.py passed")
