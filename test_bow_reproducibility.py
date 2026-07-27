import random

from game import Game
from bow_speech_generator import generate_utterance_from_speech_event


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}")


def first_speech(game):
    past = []
    for index, event in enumerate(game.event_log):
        if event.get("event_type") == "speech":
            return event, past, index
        past.append(event)
    raise AssertionError("No speech event found.")


def generate_once():
    random.seed(123)
    game = Game(enable_speech=True, enable_wolf_deception=True)
    game.run_game(max_rounds=3)
    event, past, index = first_speech(game)
    return generate_utterance_from_speech_event(
        game.state,
        event,
        past,
        game_id="repro_game",
        seed=123,
        base_game_index=1,
        behavioral_regime="repro",
        dataset_split="train",
        source_event_index=index,
    )


def test_generation_is_reproducible():
    first = generate_once()
    second = generate_once()
    check(first == second, "same generated utterance metadata is reproducible")


if __name__ == "__main__":
    test_generation_is_reproducible()
    print("test_bow_reproducibility.py passed")
