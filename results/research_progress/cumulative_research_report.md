# DURF Werewolf Cumulative Research Report

## 1. Original Proposal and Research Questions

The project uses Werewolf as a controlled environment for hidden-information decision making. The proposal commitments include a 10-player simulation, Bag-of-Words speech quantification, suspicion and credibility decisions, herding, coordinated wolf behavior, role-specific payoff optimization, financial-market analogies, risk and opportunity-cost analysis, 10,000+ simulations, a final report, and a DURF presentation.

The original proposal file was not found in the repository during this audit. Proposal alignment therefore uses the user-provided proposal summary and repository evidence.

## 2. Simulation Environment

The repository implements a modular Python simulation with roles, players, game state, night/day phases, win conditions, randomized role assignment, event logs, and batch simulation. Both 7-player and 10-player settings are represented. The 10-player setup matches the proposal role pool: 3 wolves, 4 villagers, seer, witch, and hunter.

## 3. Payoff and Role Framework

Payoff calculation exists and has been used in ablation, ten-player, risk-preference, and ML outputs. However, a unified role-specific payoff matrix and formal payoff-optimization synthesis remain incomplete. Risk-adjusted return and Sharpe-like metrics are not yet fully implemented as formal financial analogues.

## 4. Low-Information Baseline

Question: Does the baseline expose a real hidden-information problem?

Hypothesis: Wolves dominate when village agents lack reliable information.

Design: Stage 1 ablation with random voting and no information mechanisms.

Evidence: The Stage 1 report gives random baseline wolf win 93% and village win 7%.

Formal analysis: Not performed; descriptive pilot only.

Conclusion: `hypothesis supported` descriptively. This baseline motivates all later information mechanisms.

## 5. Special-Role Actions

Question: Do seer, witch, and hunter mechanics reduce wolf dominance?

Hypothesis: Special roles add information and intervention value for the village.

Design: Sequential Stage 1 ablations.

Evidence: Stage 1 report shows seer_action village win 23%, witch_action 49%, and hunter_action 46%.

Formal analysis: Not performed.

Conclusion: `promising but uncertain`. Special roles matter, but effects were sequential and not fully isolated.

## 6. Speech and Information Flow

Question: Do speech-like signals turn voting into a social inference process?

Hypothesis: Speech, belief updating, and role priors improve village coordination.

Design: Stage 2 added structured speech acts, `p_wolf`, suspicion updates, herding, and role prior.

Evidence: Current exported ablation results show speech_enabled village win 59% versus 7% baseline, but Stage 2 values are exploratory and some report versions differ.

Formal analysis: Not performed for the early Stage 2 ablation.

Conclusion: `promising but uncertain`. Structured speech labels motivated the later R2 BoW text pipeline, which is now implemented as a shadow measurement layer.

## 7. Herding

Question: Does group pressure improve voting?

Hypothesis: Herding can amplify useful signals but may also amplify noise.

Design: Stage 2 and Stage 4 trust-weighted herding experiments.

Evidence: Stage 2 suggested herding added value beyond speech in exploratory runs. Later multi-seed summaries showed trust-weighted herding changed outcomes but did not always monotonically improve village performance.

Formal analysis: Not yet fully formalized for herding-specific claims.

Conclusion: `promising but uncertain`.

## 8. Wolf Strategy and Deception

Question: Can wolves regain advantage through night strategy and daytime deception?

Hypothesis: Deception helps wolves unless credibility costs penalize manipulation.

Design: Wolf night-kill diagnostics, wolf daytime deception policies, accusation costs, wrong-accusation penalties, and self-defense costs.

Evidence: `false_accuse` reached 78% wolf win before costs, then fell to 50% after accusation costs. Deflection fell to 46% after self-defense costs.

Formal analysis: Mostly descriptive diagnostics.

Conclusion: `promising but uncertain`. Deception matters, and credibility costs are necessary.

## 9. Risk Preference

Question: Does risk appetite alter collective resilience and payoff?

Hypothesis: Conservative populations should reduce false-positive eliminations and lower wolf win rate.

Design: Ten-player risk-preference multi-seed experiment.

Evidence: Conservative-majority trust memory had wolf mean 38.56% versus 42.96% for neutral trust memory. Aggressive-majority trust memory had wolf mean 50.96%.

Formal analysis: Replicated descriptive multi-seed summary, without formal contrast p-values.

Conclusion: `promising but uncertain`.

## 10. Position Theory

Question: Are edge seats inherently informative?

Hypothesis: Edge seats contain more wolves or edge-first checking improves village outcomes.

Design: Randomized-role seer-position experiments and game-level Data Analysis.

Evidence: Edge seat wolf probability was 30.23%, inner was 29.85%, and expected was 30.00%. Edge-first versus random adjusted OR was 1.05, p = 0.417.

Formal analysis: Formal game-level analysis exists.

Conclusion: `hypothesis rejected` for strong edge-seat theory after role randomization.

## 11. Structured Seer Search

Question: Do structured search paths beat random checking?

Hypothesis: Diversified search paths such as alternate_sides improve village win rate.

Design: 14-strategy, 35,000-game structured seer search with formal Data Analysis.

Evidence: Alternate_sides had 44.16% village win versus random 40.52%, OR 1.161, raw p = 0.0092, Holm p = 0.0552. Highest_p_wolf and highest_suspicion were statistically worse than random, Holm p = 0.000276.

Conclusion: Structured diversification is `promising but uncertain`; behavioral exploitation has a `statistically supported harmful effect`.

## 12. Seat-Order and Label Validity

Question: Are directional results artifacts of displayed labels?

Hypothesis: Neutralizing displayed labels should expose whether label order changes outcomes.

Design: Seat-order-neutral experiment with normal, mirrored, and rotated labels.

Evidence: Displayed-label invariance was exact across all tested physical trajectories and outcomes. Source rows were 30,000, but effective independent sample for strategy inference was 10,000 strategy/base rows and 2,500 physical configurations.

Conclusion: Displayed-label artifact rejected; physical clockwise advantage remains `promising but uncertain`.

## 13. Physical-Direction Engine Validation

Question: Is the engine physically mirror-symmetric under supplied actions?

Hypothesis: Replay and mirror transforms should preserve trajectories and outcomes if the engine is symmetric.

Design: Supplied-action replay and physical mirror validation.

Evidence: Exact replay, physical mirror replay, and strategy mirror action validation all matched at 100% with zero divergences.

Conclusion: `engine symmetry validated`.

## 14. Machine Learning Stage 1

Question: Can observation-safe features support ML identity and action models?

Hypothesis: Public and actor-available features contain useful signal.

Evidence: Stage 1 generated 7,155 candidate rows and reported village-vote logistic ROC-AUC 0.9458.

Formal analysis: Pilot only. The result was later revised by Stage 1.5.

Conclusion: `weak/inconclusive` for generalization; `implementation validated` for logging.

## 15. Machine Learning Stage 1.5

Question: Do ML signals survive grouped splits and full-state rollouts?

Hypothesis: Grouped validation and full rollouts should retain meaningful ML value.

Evidence: Village-vote ROC-AUC fell to 0.6679, close to existing `p_wolf` at 0.6586. Surrogate validity was weak for wolf-kill action value, with Spearman 0.0718. A final-test shadow wolf-kill recommendation still appeared promising with +0.150 action value.

Conclusion: `surrogate-only improvement` for shadow wolf-kill; not ready as a live policy.

## 16. Machine Learning Stage 2A

Question: Does the frozen ML wolf-kill policy improve live complete-game wolf win rate?

Hypothesis: Frozen ML, hybrid, and epsilon policies should outperform or match the existing rule.

Evidence: Existing rule wolf win was 69.50%. Frozen ML and epsilon were 61.00%, and hybrid was 58.00%. Hybrid difference was -11.50 pp with Holm p = 0.0033.

Conclusion: Hybrid has a `statistically supported harmful effect`; pure ML and epsilon are `weak/inconclusive` but harmful in direction. Existing rule remains default.

## 17. Cross-Stage Data Analysis Lessons

Raw rows are not always independent. Candidate rows are not games. Deterministic label duplicates must be collapsed. Shadow values are not live policy values. Model coefficients are not causal effects. Post-treatment variables such as first-check success and seer survival are diagnostic unless explicitly randomized.

## 18. Current Scientific Conclusions

The project supports the claim that information, credibility, and search structure shape social-deduction outcomes. It rejects strong edge-seat folklore after role randomization. It validates engine symmetry. It also shows that ML policies require live matched validation and can be harmful even after apparently promising shadow analysis.

## 19. Proposal Alignment

The project has completed and extended the core simulator, night/day mechanics, role actions, suspicion, credibility, herding, wolf coordination, competing seer scenarios, 10,000+ simulations, Data Analysis, visualization, presentation outputs, and R2 formal BoW speech quantification. It has partially completed payoff and financial-market interpretation. BoW integration into live decisions, unified payoff optimization, risk-adjusted return, Sharpe-like analysis, and systematic literature comparison remain incomplete.

## 20. Remaining Deliverables

Remaining deliverables are ordered in `remaining_work_roadmap.md`: BoW integration, unified role-specific payoff matrix, financial risk metrics, role strategy optimization synthesis, systematic literature comparison, final integrated Data Analysis, and final DURF report/presentation.

## 21. Next Research Priorities

The exact next stage is R3 - BoW Integration and Comparative Decision Analysis. It should test whether the validated R2 BoW scores improve belief and voting updates in matched live games, while keeping credibility and speaker-memory safeguards active.

## 22. Reproducibility and Source Index

The cumulative evidence registry is `results/research_progress/cumulative_evidence_registry.csv`. Source traceability is `results/research_progress/source_traceability_index.csv`. Known inconsistencies are documented in `results/research_progress/documentation_inconsistencies.md`.

## 23. Machine Learning Stage 2B

Question: Why did the frozen wolf-kill ML policy fail after promising shadow
analysis?

Hypothesis: The offline-to-live gap is caused by mixed mechanisms: repeated
intervention compounding, distribution shift, low-margin instability,
hybrid score incompatibility, and downstream interaction with witch, hunter,
seer, speech, and voting systems.

Design: Stage 2B uses the unchanged Stage 2A frozen wolf-kill model in
matched complete games. Selective override thresholds are calibrated from
development/validation shadow seeds only, then evaluated on isolated final
seeds. Primary comparisons are matched against `existing_rule` with Holm
correction.

Evidence: See `results/ml_optimization_stage2b/ml_stage2b_research_report.md` and
`results/ml_optimization_stage2b/stage2b_primary_contrasts.csv`.

Conclusion: The existing rule remains the default. The frozen ML model should
be retained for diagnostics only unless a later, pre-registered selective
override validation shows stable non-harmful value.

## 24. R2 Formal Bag-of-Words Speech Quantification

Question: Can the simulator implement proposal-level Bag-of-Words speech metrics rather than relying only on structured speech labels?

Design: R2 generates English natural-language utterances from existing legal speech events without changing gameplay policy. It tokenizes text deterministically, builds a train-only BoW vocabulary, extracts werewolf-leaning, emotional-intensity, and information-density scores, and evaluates role prediction, intent prediction, template generalization, regime generalization, ablations, leakage, and overfitting.

Evidence: See `results/bow_speech_stage_r2/bow_stage_r2_research_report.md`. The dataset contains 1,600 source games, 32,721 utterances, 48 template families, 6 behavioral regimes, and a 289-term train-derived vocabulary. BoW score contrasts are significant after Holm correction. Final-test BoW-score ROC-AUC for speaker-is-wolf is 0.692, compared with 0.569 for `p_wolf` and 0.515 for suspicion. Structured labels remain stronger, and the full legal combined model does not clearly improve over `p_wolf + suspicion + structured` labels.

Conclusion: `promising but uncertain`. R2 validates the BoW measurement pipeline, but live decision integration remains R3.

## 25. R3 Guarded Bag-of-Words Integration

R3 integrated formal BoW speech scores into belief and village voting under explicit experimental flags. The stage generated matched live-game, speech, belief-update, vote-decision, shadow, template-shift, and disagreement-branch proxy datasets. Default gameplay remains unchanged unless `enable_bow_r3=True`.

## 26. R4 Unified Role-Specific Payoff Matrix

R4 implemented a unified, versioned, role-specific payoff matrix and event-level
ledger. The validation dataset contains 2000 games,
10 seeds, 5 regimes, and
200660 payoff-event rows. The payoff system reconciles
event-level, player-level, and game-level totals and is ready for R5
risk-adjusted analysis.

## 27. R5 Financial Risk Metrics

R5 computed expected payoff, volatility, downside deviation, VaR-like and CVaR-like tail metrics, Sharpe-like and Sortino-like payoff ratios, opportunity-cost-adjusted payoff, information and manipulation premiums, and role-specific strategy frontiers from the frozen R4 payoff dataset. The stage keeps the financial-market language explicitly analogical and does not alter gameplay or the R4 payoff manifest.
