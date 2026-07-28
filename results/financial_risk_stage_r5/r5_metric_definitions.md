# R5 Metric Definitions

## Expected Payoff

Arithmetic mean player-game payoff.

## Volatility

Sample standard deviation of player-game payoff.

## Downside Deviation

`sqrt(mean((target - payoff)^2 for payoff < target))`, using target `0`.

## VaR-Like and CVaR-Like Metrics

Loss is defined as `-payoff`. The VaR-like payoff threshold is the empirical
lower-tail payoff quantile. The CVaR-like loss is the average `-payoff` among
observations at or below that threshold.

## Sharpe-Like Ratio

`(mean payoff - benchmark payoff) / payoff standard deviation`. The primary
benchmark is zero payoff. No risk-free-rate interpretation is used.

## Sortino-Like Ratio

`(mean payoff - target payoff) / downside deviation`. The primary target is
zero payoff.

## Opportunity-Cost Adjustment

R4 totals already include the opportunity-cost category. R5 therefore reports
`payoff_excluding_opportunity_cost + opportunity_cost`, which reconciles exactly
to `total_payoff` and avoids double counting.
