"""Run all R6.1 targeted role-strategy experiments."""

from __future__ import annotations

from r61_common_experiment import run_role_strategy_stage_r61


if __name__ == "__main__":
    results = run_role_strategy_stage_r61()
    print("R6.1 targeted role-strategy experiment complete")
    for result in results:
        print(
            f"{result['module']}: "
            f"{len(result['game_rows'])} game rows, "
            f"{len(result['action_rows'])} action rows"
        )
