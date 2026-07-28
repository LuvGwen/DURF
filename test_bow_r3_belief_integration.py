from game_state import GameState
from player import Player
from roles import VILLAGER, WEREWOLF
from bow_r3_belief_integration import apply_r3_belief_policy
from bow_r3_template_conditions import render_r3_live_utterance


def assert_close(actual, expected, label):
    if abs(actual - expected) > 1e-9:
        raise AssertionError(f"{label}: expected {expected}, got {actual}")
    print(f"PASS: {label}")


def build_state():
    return GameState([
        Player(1, VILLAGER),
        Player(2, WEREWOLF),
        Player(3, VILLAGER),
    ])


def test_guarded_weights():
    state = build_state()
    target = state.get_player_by_id(2)
    target.p_wolf = 0.4
    target.suspicion_score = 0.4
    speech = {"speaker": 1, "speech_type": "accuse", "target": 2}
    row = render_r3_live_utterance(state, speech)
    event = apply_r3_belief_policy(
        state,
        speech,
        row,
        policy_name="guarded_bow_010",
    )
    expected = 0.9 * 0.4 + 0.1 * event["bow_signal"]
    assert_close(target.p_wolf, expected, "guarded 0.10 weighting")


def test_shadow_does_not_mutate():
    state = build_state()
    target = state.get_player_by_id(2)
    target.p_wolf = 0.4
    speech = {"speaker": 1, "speech_type": "accuse", "target": 2}
    row = render_r3_live_utterance(state, speech)
    apply_r3_belief_policy(
        state,
        speech,
        row,
        policy_name="bow_shadow_belief",
    )
    assert_close(target.p_wolf, 0.4, "shadow mode does not mutate belief")


def test_structured_plus_bow_weighting():
    state = build_state()
    target = state.get_player_by_id(2)
    target.p_wolf = 0.4
    speech = {"speaker": 1, "speech_type": "accuse", "target": 2}
    row = render_r3_live_utterance(state, speech)
    event = apply_r3_belief_policy(
        state,
        speech,
        row,
        policy_name="structured_bow_guarded",
    )
    expected = (
        0.70 * 0.4
        + 0.20 * event["structured_signal"]
        + 0.10 * event["bow_signal"]
    )
    assert_close(target.p_wolf, expected, "structured plus BoW weighting")


if __name__ == "__main__":
    test_guarded_weights()
    test_shadow_does_not_mutate()
    test_structured_plus_bow_weighting()
    print("test_bow_r3_belief_integration.py passed")
