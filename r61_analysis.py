"""Analysis entry point for already generated R6.1 outputs."""

from __future__ import annotations

from pathlib import Path


RESULTS_DIR = Path("results/targeted_strategy_stage_r61")


def list_r61_outputs():
    return sorted(str(path) for path in RESULTS_DIR.glob("r61_*"))


if __name__ == "__main__":
    for path in list_r61_outputs():
        print(path)
