"""Run the R6.1 Witch joint potion policy experiment."""

from __future__ import annotations

from r61_common_experiment import run_role_strategy_stage_r61


def run_witch_experiment():
    return run_role_strategy_stage_r61(modules=["witch"])


if __name__ == "__main__":
    results = run_witch_experiment()
    result = results[0]
    print("witch", len(result["game_rows"]), len(result["action_rows"]))
