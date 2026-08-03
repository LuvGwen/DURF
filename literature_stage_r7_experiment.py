"""R7 entry point.

This stage is named like an experiment for repository consistency, but it runs
only literature-synthesis generation and validation artifacts. It does not run
gameplay simulations or alter prior numerical results.
"""

from literature_stage_r7_analysis import main


if __name__ == "__main__":
    raise SystemExit(main())
