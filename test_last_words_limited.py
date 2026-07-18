from game import Game
from player import Player
from roles import HUNTER, VILLAGER, WEREWOLF, WITCH


def make_game(enable_last_words=True):
    players = [
        Player(1, WEREWOLF),
        Player(2, VILLAGER),
        Player(3, VILLAGER),
        Player(4, WITCH),
        Player(5, HUNTER),
    ]
    players[0].p_wolf = 0.9
    players[0].suspicion_score = 0.9

    game = Game(
        players,
        enable_last_words=enable_last_words,
        enable_seer=False,
        enable_witch=False,
        enable_hunter=False,
        enable_speech=False,
        enable_speaker_memory=True,
    )
    return game, players


def last_word_events(game):
    return [
        event for event in game.event_log
        if event.get("event_type") == "last_words"
    ]


def kill_and_try_last_words(game, player_id, cause):
    game.state.kill_player(player_id)
    return game.log_last_words_after_death(player_id, cause)


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)

    print(f"PASS: {message}")


def test_disabled_last_words():
    game, _ = make_game(enable_last_words=False)
    event = kill_and_try_last_words(game, 2, "voted_out")

    assert_true(event is None, "disabled last words produce no event")
    assert_true(len(last_word_events(game)) == 0, "event log has no last words")


def test_voted_out_last_words():
    game, players = make_game()
    event = kill_and_try_last_words(game, 2, "voted_out")

    assert_true(event is not None, "voted-out player can give last words")
    assert_true(players[1].has_given_last_words, "last words flag is set")


def test_night1_kill_last_words():
    game, _ = make_game()
    game.state.round_number = 1
    event = kill_and_try_last_words(game, 2, "night_kill")

    assert_true(event is not None, "night 1 wolf-kill victim can give last words")


def test_night2_kill_no_last_words():
    game, _ = make_game()
    game.state.round_number = 2
    event = kill_and_try_last_words(game, 2, "night_kill")

    assert_true(event is None, "night 2 wolf-kill victim cannot give last words")


def test_witch_poison_no_last_words():
    game, _ = make_game()
    event = kill_and_try_last_words(game, 2, "witch_poison")

    assert_true(event is None, "witch poison victim cannot give last words")


def test_hunter_shot_no_last_words():
    game, _ = make_game()
    event = kill_and_try_last_words(game, 2, "hunter_shot")

    assert_true(event is None, "hunter shot victim cannot give last words")


def test_one_last_words_per_player():
    game, _ = make_game()
    first_event = kill_and_try_last_words(game, 2, "voted_out")
    second_event = game.log_last_words_after_death(2, "voted_out")

    assert_true(first_event is not None, "first last words event is created")
    assert_true(second_event is None, "same player cannot give last words twice")
    assert_true(len(last_word_events(game)) == 1, "only one last words event exists")


def test_dead_player_stays_dead():
    game, players = make_game()
    kill_and_try_last_words(game, 2, "voted_out")
    alive_ids = [player.player_id for player in game.state.get_alive_players()]

    assert_true(not players[1].alive, "last words speaker remains dead")
    assert_true(2 not in alive_ids, "dead speaker is not an alive player")
    assert_true(players[1].vote_target is None, "dead speaker has no vote target")
    assert_true(players[1].night_target is None, "dead speaker has no night target")


def test_event_log_shape():
    game, _ = make_game()
    kill_and_try_last_words(game, 2, "voted_out")
    events = last_word_events(game)
    content = events[0]["content"]

    assert_true(events[0]["event_type"] == "last_words", "event_type is last_words")
    assert_true(content["type"] == "last_words", "content type is last_words")
    assert_true("speaker" in content, "last words include speaker")
    assert_true("target" in content, "last words include target")
    assert_true("cause_of_death" in content, "last words include cause_of_death")
    assert_true("tokens" in content, "last words include tokens")


def run_tests():
    test_disabled_last_words()
    test_voted_out_last_words()
    test_night1_kill_last_words()
    test_night2_kill_no_last_words()
    test_witch_poison_no_last_words()
    test_hunter_shot_no_last_words()
    test_one_last_words_per_player()
    test_dead_player_stays_dead()
    test_event_log_shape()
    print("All limited last words tests passed.")


if __name__ == "__main__":
    run_tests()
