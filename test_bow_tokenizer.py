from bow_tokenizer import tokenize


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}")


def test_tokenizer_is_deterministic():
    text = "Player 3 is not a wolf, but Seat 4 is suspicious!"
    first = tokenize(text, speaker_id=1, target_id=3)
    second = tokenize(text, speaker_id=1, target_id=3)
    check(first == second, "same utterance tokenizes identically")


def test_player_ids_are_normalized():
    tokens = tokenize("Player 3 voted Seat 4 in game 42", target_id=3)
    check("3" not in tokens and "4" not in tokens and "42" not in tokens, "numeric IDs are not tokens")
    check("player_target" in tokens, "target player reference is normalized")
    check("number" not in tokens, "generic numbers are excluded from vocabulary-facing tokens")


def test_negation_is_preserved():
    tokens = tokenize("I am not wolf and never claimed seer")
    check("not" in tokens, "not is preserved")
    check("never" in tokens, "never is preserved")


if __name__ == "__main__":
    test_tokenizer_is_deterministic()
    test_player_ids_are_normalized()
    test_negation_is_preserved()
    print("test_bow_tokenizer.py passed")
