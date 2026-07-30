"""Run the R6.1 Villager structured-voting experiment."""

from __future__ import annotations

from r61_common_experiment import run_role_strategy_stage_r61


def run_villager_experiment():
    return run_role_strategy_stage_r61(modules=["villager"])


if __name__ == "__main__":
    results = run_villager_experiment()
    result = results[0]
    print("villager", len(result["game_rows"]), len(result["action_rows"]))
