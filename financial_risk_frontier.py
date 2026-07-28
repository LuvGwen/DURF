"""Risk-return frontier utilities for R5."""

from __future__ import annotations


def dominates(candidate, other, return_key="mean_payoff", risk_key="risk_value"):
    candidate_return = float(candidate[return_key])
    other_return = float(other[return_key])
    candidate_risk = float(candidate[risk_key])
    other_risk = float(other[risk_key])
    return (
        candidate_return >= other_return
        and candidate_risk <= other_risk
        and (candidate_return > other_return or candidate_risk < other_risk)
    )


def mark_frontier(rows, return_key="mean_payoff", risk_key="risk_value"):
    marked = []
    for row in rows:
        dominated_by = [
            other["condition_name"]
            for other in rows
            if other is not row and dominates(other, row, return_key, risk_key)
        ]
        new_row = dict(row)
        new_row["is_efficient"] = not dominated_by
        new_row["is_dominated"] = bool(dominated_by)
        new_row["dominated_by"] = ";".join(sorted(set(dominated_by)))
        marked.append(new_row)
    return marked
