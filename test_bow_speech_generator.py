import random

from game import Game
from bow_speech_generator import (
    generate_utterance_from_speech_event,
    template_registry_rows,
)


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}")


def first_speech_event(game):
    past = []
    for index, event in enumerate(game.event_log):
        if event.get("event_type") == "speech":
            return event, past, index
        past.append(event)
    raise AssertionError("No speech event generated.")


def test_generator_creates_text_and_metadata():
    random.seed(42)
    game = Game(enable_speech=True, enable_wolf_deception=True)
    game.run_game(max_rounds=3)
    event, past, index = first_speech_event(game)
    utterance = generate_utterance_from_speech_event(
        game.state,
        event,
        past,
        game_id="test_game",
        seed=42,
        base_game_index=1,
        behavioral_regime="test",
        dataset_split="train",
        source_event_index=index,
    )
    check(utterance["utterance_text"], "utterance text is generated")
    check(utterance["template_family"], "template family is recorded")
    check(
        utterance["hidden_information_leakage_flag"] == "False",
        "hidden leakage flag is false",
    )


def test_template_registry_has_primary_and_ood_families():
    rows = template_registry_rows()
    primary = {
        row["template_family"] for row in rows
        if row["template_split_group"] == "primary"
    }
    ood = {
        row["template_family"] for row in rows
        if row["template_split_group"] == "ood_template"
    }
    check(len(primary) >= 20, "primary template family count is at least 20")
    check(ood, "OOD template families exist")
    check(not (primary & ood), "primary and OOD template families do not overlap")


if __name__ == "__main__":
    test_generator_creates_text_and_metadata()
    test_template_registry_has_primary_and_ood_families()
    print("test_bow_speech_generator.py passed")
