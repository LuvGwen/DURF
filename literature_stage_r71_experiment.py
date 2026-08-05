"""R7.1 entry point.

This stage is named like an experiment for repository consistency. It performs
literature DOI and recency auditing only; it does not run gameplay simulation.
"""

from literature_stage_r71_analysis import main


if __name__ == "__main__":
    raise SystemExit(main())
