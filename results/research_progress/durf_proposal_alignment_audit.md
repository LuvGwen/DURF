# DURF Proposal Alignment Audit

## Source Note

The original DURF proposal file was not found in the repository during this audit. This alignment uses the proposal commitments supplied in the current task prompt and repository evidence files. Any final report should replace this source note with a citation to the original proposal if the proposal file is later added.

## Summary

The project has completed and extended the core simulator, 10-player setup, role mechanics, suspicion and credibility systems, wolf strategy, competing seer scenarios, large-scale simulations, Data Analysis outputs, visualization, presentation materials, and formal R2 Bag-of-Words speech quantification. It has partially completed payoff and financial analogy work. It has not yet completed BoW integration into live decisions, unified role-specific payoff optimization, risk-adjusted return, Sharpe-like analysis, or systematic literature comparison.

## Completed Or Extended

- Classic 10-player simulator.
- Night/day mechanics.
- Role-specific actions.
- Suspicion system.
- Credibility and trust.
- Herding.
- Wolf night strategy and deception.
- Competing seer scenarios.
- 10,000+ simulations.
- Data Analysis and visualization.
- DURF progress presentation.
- Formal BoW vocabulary, English tokenization, and three proposal-level speech scores.

## Partially Completed

- BoW integration into decisions: R2 implements BoW as a shadow-analysis pipeline, but live belief/voting integration is intentionally deferred to R3.
- Role-specific payoff matrix: payoff functions and summary payoffs exist, but the unified matrix and role-level synthesis are incomplete.
- Financial-market interpretation: conceptual analogies exist, but formal risk metrics are incomplete.
- Reproducibility documentation: many schemas exist, and this stage adds a permanent standard, but future stages must keep it current.

## Not Yet Completed

- Payoff variance.
- Risk-adjusted return.
- Sharpe-ratio analogue.
- Systematic literature cross-check.
- Final integrated written report.

## Requires A New Experiment

- BoW-driven decision integration.
- Unified role-specific payoff and risk-adjusted payoff analysis.

## Requires Documentation Only

- Financial-market analogy can be strengthened using existing deception, risk, and trust results, but quantitative financial metrics still require new analysis.
- Retail-investor, informed-trader, regulator, and manipulator analogies require a final report synthesis and literature cross-check.

## Matrix

The full component-by-component audit is in `results/research_progress/durf_proposal_alignment_matrix.csv`.

## ML Stage 2B Update

ML Stage 2B adds a formal offline-to-live failure diagnosis for the frozen
wolf-kill model. It preserves the existing rule as the default, uses isolated
final seeds, and reports single-intervention, repeated-decision,
distribution-shift, selective-override, hybrid-failure, and downstream
mechanism diagnostics in `results/ml_optimization_stage2b`.

## R2 BoW Update

R2 completes the formal BoW vocabulary, English tokenization, werewolf-leaning score, emotional-intensity score, and information-density score as shadow-analysis modules. `BoW integration into decisions` remains partially completed because R2 intentionally does not alter live voting, checking, killing, or payoff rules. The next required stage is R3: BoW Integration and Comparative Decision Analysis.

## R3 Guarded BoW Integration Update

BoW decision integration is now partially completed and live-validated under guarded experimental policies.

## R4 Unified Payoff Update

R4 resolves the role-specific payoff matrix gap and leaves payoff variance and Sharpe-like ratios for R5.

## R5 Financial-Risk Alignment

R5 addresses the proposal components for expected payoff, payoff variance, opportunity cost, risk-adjusted return, Sharpe-like analysis, downside risk, and financial-market interpretation. The analogy remains explicitly game-based rather than literal finance.

## R5.1 Attribution Audit Update

R5.1 resolves the strategy ownership ambiguity introduced by global R4 condition labels and prevents cross-role externalities from being reported as actor-specific strategy recommendations.


## R6 Role Strategy Synthesis Update

R6 partially completes the proposal requirement for role-specific strategy
analysis. It documents current defaults and evidence grades but does not
mark the full optimization requirement complete because Hunter policy,
Seer reveal timing, Witch joint potion policy, Werewolf aggression versus
deep cover, and Villager structured voting comparisons remain unresolved.
## R6.1 Targeted Strategy Alignment

R6.1 directly addresses the proposal-alignment gaps for role-specific strategy analysis and risk-adjusted comparison by producing matched live-validation policy families for all five roles. It does not add new roles, alter payoff rules, deploy ML policies, or revive live BoW overrides.


## R6.2 Proposal Alignment Update

Seer mortality risk and Witch wasted-potion cost are now represented with corrected metric definitions. Historical defaults remain separate from the recommended research configuration.
