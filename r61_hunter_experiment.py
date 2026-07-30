"""Run the R6.1 Hunter targeted policy experiment."""

from __future__ import annotations

from r61_common_experiment import run_role_strategy_stage_r61


def run_hunter_experiment():
    return run_role_strategy_stage_r61(modules=["hunter"])


if __name__ == "__main__":
    results = run_hunter_experiment()
    result = results[0]
    print("hunter", len(result["game_rows"]), len(result["action_rows"]))
