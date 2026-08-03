# R7 Risk Metrics Literature

Generated on 2026-08-04. This R7 artifact is literature synthesis only; no gameplay experiment was run.

## Synthesis

R7 retained 13 sources connected to this domain. The sources support comparison, theory framing, and citation-ready wording, but they do not replace the project's own simulation evidence.

| Source | Quality | Supported claim | Limitation |
| --- | --- | --- | --- |
| J. Bradford De Long (1990) | A | Higher payoff can coexist with higher self-created risk, supporting risk-return framing. | Financial asset-price model; DURF payoffs are game utilities. |
| Nicholas Barberis (1998) | A | Behavioral biases can produce underreaction and overreaction patterns. | General market psychology model, not simulated hidden-role inference. |
| Miroslav Dudik (2011) | A | Offline policy estimates can be biased or high variance without appropriate estimators. | DURF uses matched live validation rather than DR estimators. |
| Philip Thomas (2015) | A | Unsafe policies should not be deployed based only on weak offline estimates. | Confidence-bound method not implemented directly in DURF. |
| Nan Jiang (2016) | A | Sequential policy evaluation has bias-variance tradeoffs and can be hard. | Not a direct model of the project's shadow rollout diagnostics. |
| Averill M. Law (2015) | B | Simulation studies need explicit replication, validation, and output analysis. | General simulation methods textbook. |
| William F. Sharpe (1966) | A | Sharpe-like ratios are a recognized way to compare mean return per unit volatility. | DURF payoff ratios are analogues and not investment returns. |
| Frank A. Sortino (1994) | A | Sortino-like ratios isolate downside deviation rather than total volatility. | Project payoff denominators are game-specific. |
| R. Tyrrell Rockafellar (2000) | A | Tail-risk metrics should examine expected losses conditional on bad outcomes. | Optimization framework, while DURF reports CVaR-like descriptive metrics. |
| Philippe Jorion (2007) | B | VaR-like metrics summarize percentile tail exposure. | Book metadata requires manual edition review; used for conceptual metric framing. |
| Harry Markowitz (1952) | A | Risk-return tradeoffs are a formal basis for strategy frontier analogies. | Portfolio optimization is not equivalent to role selection in a game. |
| Philippe Artzner (1999) | A | Risk metrics require explicit definitions and caveats about what properties they satisfy. | DURF VaR/CVaR-like metrics are descriptive analogues, not full coherent-risk optimization. |
| Daniel Kahneman (1979) | A | Risk preferences can alter choices and payoff distributions. | The project's risk-preference labels are simplified and not calibrated prospect-theory parameters. |

## DURF Interpretation

The project should cite these sources to frame mechanisms, not to overstate real-world causal transfer.
