"""Run the R6.1 Seer reveal-timing experiment."""

from __future__ import annotations

from r61_common_experiment import run_role_strategy_stage_r61


def run_seer_experiment():
    return run_role_strategy_stage_r61(modules=["seer"])


if __name__ == "__main__":
    results = run_seer_experiment()
    result = results[0]
    print("seer", len(result["game_rows"]), len(result["action_rows"]))
