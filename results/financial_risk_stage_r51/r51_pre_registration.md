# R5.1 Pre-Registration

Primary objective: audit R5 strategy attribution and rebuild actor-specific
strategy comparisons without changing R4 payoff manifests, R5 metric formulas,
or simulator behavior.

Primary unit: matched R4 validation games clustered by `matched_set_id`.

Primary correction rule: actor-specific rows require
`strategy_owner_role == affected_role`.
