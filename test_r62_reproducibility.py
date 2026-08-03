from research_configuration import recommended_research_configuration
from run_recommended_configuration import run_recommended_configuration


def main():
    first_game, first_result = run_recommended_configuration(seed=6202)
    second_game, second_result = run_recommended_configuration(seed=6202)
    assert first_result["winner"] == second_result["winner"]
    assert len(first_game.event_log) == len(second_game.event_log)
    assert recommended_research_configuration()["configuration_hash"]
    print("test_r62_reproducibility.py passed")


if __name__ == "__main__":
    main()
