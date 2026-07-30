from game import Game
from player import Player
from roles import SEER, VILLAGER, WEREWOLF


def main():
    game = Game([
        Player(1, WEREWOLF),
        Player(2, SEER),
        Player(3, VILLAGER),
    ])
    game.run_one_round()
    checks = [event for event in game.event_log if event["event_type"] == "seer_check"]
    assert len(checks) <= 1
    if checks:
        content = checks[0]["content"]
        assert content["target"] != content["seer"]
        assert content["target_role"]
        assert isinstance(content["target_is_wolf"], bool)
    print("test_r61_seer_information_legality.py passed")


if __name__ == "__main__":
    main()
