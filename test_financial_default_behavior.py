from game import Game, create_default_players


def main():
    game = Game(create_default_players())
    result = game.run_game(max_rounds=3)
    assert "r4_payoff_summary" not in result
    assert not hasattr(game, "r5_metric_manifest")
    print("test_financial_default_behavior.py passed")


if __name__ == "__main__":
    main()
