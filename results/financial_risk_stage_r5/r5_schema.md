# R5 Schema

All CSV files are written with UTF-8 encoding and one header row. Primary
analysis files use `calculation_specification`, `role`, and either
`condition_name`, `seed`, or `behavioral_regime` as grouping keys. Payoff values
are game-payoff units from the frozen R4 ledger.

Event-level rows are used only for attribution and premium flags; they are not
treated as independent observations for risk metrics.
