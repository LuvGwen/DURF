"""Run the R6.1 Werewolf aggression versus deep-cover experiment."""

from __future__ import annotations

from r61_common_experiment import run_role_strategy_stage_r61


def run_wolf_experiment():
    return run_role_strategy_stage_r61(modules=["wolf"])


if __name__ == "__main__":
    results = run_wolf_experiment()
    result = results[0]
    print("wolf", len(result["game_rows"]), len(result["action_rows"]))
