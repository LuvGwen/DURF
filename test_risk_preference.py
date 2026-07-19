from game import Game
from game_state import GameState
from player import Player
from risk_preference import (
    HIGH_RISK_ACTION_MULTIPLIERS,
    RISK_MULTIPLIERS,
    assign_risk_preferences,
    get_risk_multiplier,
)
from roles import VILLAGER, WEREWOLF, WITCH
from speech_action import generate_speech_action
from witch_action import perform_witch_poison
from wolf_deception import generate_wolf_deception_action


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)

    print(f"PASS: {message}")


def make_players(count=30):
    roles = [WEREWOLF, WITCH] + [VILLAGER] * (count - 2)
    return [
        Player(player_id=i + 1, role=role)
        for i, role in enumerate(roles)
    ]


def test_player_default():
    player = Player(1, VILLAGER)
    assert_true(
        player.risk_preference == "neutral",
        "Player default risk_preference is neutral",
    )


def test_assign_risk_preferences():
    players = make_players(100)
    assign_risk_preferences(players, mode="mixed", seed=1)
    preferences = {player.risk_preference for player in players}
    assert_true(
        {"conservative", "neutral", "aggressive"}.issubset(preferences),
        "mixed mode can assign all three risk preferences",
    )


def test_all_neutral_mode():
    players = make_players(20)
    assign_risk_preferences(players, mode="all_neutral", seed=1)
    assert_true(
        all(player.risk_preference == "neutral" for player in players),
        "all_neutral mode assigns only neutral",
    )


def test_risk_multipliers():
    player = Player(1, VILLAGER)

    for preference, expected in RISK_MULTIPLIERS.items():
        player.risk_preference = preference
        assert_true(
            get_risk_multiplier(player) == expected,
            f"normal multiplier for {preference} is {expected}",
        )

    for preference, expected in HIGH_RISK_ACTION_MULTIPLIERS.items():
        player.risk_preference = preference
        assert_true(
            get_risk_multiplier(player, high_risk=True) == expected,
            f"high-risk multiplier for {preference} is {expected}",
        )


def test_high_risk_ordering():
    player = Player(1, VILLAGER)
    player.risk_preference = "conservative"
    conservative = get_risk_multiplier(player, high_risk=True)
    player.risk_preference = "neutral"
    neutral = get_risk_multiplier(player, high_risk=True)
    player.risk_preference = "aggressive"
    aggressive = get_risk_multiplier(player, high_risk=True)

    assert_true(
        conservative < neutral,
        "conservative high-risk multiplier is below neutral",
    )
    assert_true(
        aggressive > neutral,
        "aggressive high-risk multiplier is above neutral",
    )


def test_disabled_risk_preference_records_neutral_vote():
    players = [
        Player(1, WEREWOLF),
        Player(2, VILLAGER),
        Player(3, VILLAGER),
    ]
    players[0].suspicion_score = 0.9
    game = Game(
        players,
        enable_risk_preference=False,
        enable_seer=False,
        enable_witch=False,
        enable_hunter=False,
        enable_speech=False,
        enable_suspicion_update=False,
        enable_wolf_deception=False,
    )
    game.state.phase = "day"
    game.day_phase()
    day_votes = [
        event for event in game.event_log
        if event["event_type"] == "day_vote"
    ]
    preferences = day_votes[0]["content"]["voter_risk_preference"]
    assert_true(
        set(preferences.values()) == {"neutral"},
        "disabled risk preference keeps vote risk records neutral",
    )


def test_enabled_risk_preference_vote_event():
    players = [
        Player(1, WEREWOLF),
        Player(2, VILLAGER),
        Player(3, VILLAGER),
        Player(4, VILLAGER),
    ]
    game = Game(
        players,
        enable_risk_preference=True,
        risk_preference_mode="aggressive_majority",
        enable_seer=False,
        enable_witch=False,
        enable_hunter=False,
        enable_speech=False,
        enable_suspicion_update=False,
        enable_wolf_deception=False,
    )
    game.state.phase = "day"
    game.day_phase()
    day_vote = [
        event for event in game.event_log
        if event["event_type"] == "day_vote"
    ][0]
    assert_true(
        "voter_risk_preference" in day_vote["content"],
        "vote event records voter_risk_preference",
    )


def test_witch_poison_risk_event_fields():
    players = [
        Player(1, WEREWOLF),
        Player(2, WITCH),
        Player(3, VILLAGER),
    ]
    players[0].suspicion_score = 0.2
    players[1].risk_preference = "aggressive"
    state = GameState(players)
    _, event = perform_witch_poison(
        state,
        suspicion_threshold=0.3,
        enable_risk_preference=True,
    )
    assert_true(event is not None, "aggressive witch can poison at lowered threshold")
    assert_true(
        event["witch_risk_preference"] == "aggressive",
        "witch_poison event records witch_risk_preference",
    )
    assert_true(
        "poison_threshold_used" in event,
        "witch_poison event records poison_threshold_used",
    )


def test_wolf_deception_risk_event_fields():
    players = [
        Player(1, WEREWOLF),
        Player(2, VILLAGER),
        Player(3, VILLAGER),
    ]
    players[0].risk_preference = "aggressive"
    state = GameState(players)
    event = generate_wolf_deception_action(
        players[0],
        state,
        strategy="false_accuse",
        enable_risk_preference=True,
    )
    assert_true(event is not None, "aggressive wolf deception event is generated")
    assert_true(
        event["wolf_risk_preference"] == "aggressive",
        "wolf deception event records wolf_risk_preference",
    )
    assert_true(
        "deception_probability_used" in event,
        "wolf deception event records deception_probability_used",
    )


def test_speech_risk_event_field():
    players = [
        Player(1, VILLAGER),
        Player(2, WEREWOLF),
    ]
    players[0].risk_preference = "conservative"
    state = GameState(players)
    event = generate_speech_action(
        players[0],
        state,
        enable_risk_preference=True,
    )
    assert_true(
        event["speaker_risk_preference"] == "conservative",
        "speech event records speaker_risk_preference",
    )


def run_tests():
    test_player_default()
    test_assign_risk_preferences()
    test_all_neutral_mode()
    test_risk_multipliers()
    test_high_risk_ordering()
    test_disabled_risk_preference_records_neutral_vote()
    test_enabled_risk_preference_vote_event()
    test_witch_poison_risk_event_fields()
    test_wolf_deception_risk_event_fields()
    test_speech_risk_event_field()
    print("All risk preference tests passed.")


if __name__ == "__main__":
    run_tests()
