from r61_common_experiment import MODULES, game_config_for
from r61_seer_reveal_policies import maybe_apply_r61_seer_reveal
from game import Game
from player import Player
from roles import SEER, WEREWOLF, VILLAGER


def main():
    for module, spec in MODULES.items():
        config = game_config_for(module, spec["reference"], "baseline")
        assert config["enable_bow_r3"] is False
        assert config["enable_ml_wolf_kill_policy"] is False
    game = Game([Player(1, WEREWOLF), Player(2, SEER), Player(3, VILLAGER)])
    reveal = maybe_apply_r61_seer_reveal(
        game,
        {"seer": 2, "target": 1, "target_role": WEREWOLF, "target_is_wolf": True, "round": 1},
        "immediate_reveal",
    )
    assert reveal["information_source"] == "prior_seer_check"
    print("test_r61_no_leakage.py passed")


if __name__ == "__main__":
    main()
