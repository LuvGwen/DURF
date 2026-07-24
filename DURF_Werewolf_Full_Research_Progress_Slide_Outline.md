# DURF Werewolf Full Research Progress Slide Outline

## Slide 1: Deception, Credibility, and Search Under Hidden Information

- Research purpose: Introduce the project as a controlled simulation study of social deduction and risk scoring.
- Core content: Title, project name, and one-line framing: Werewolf is used as a laboratory for hidden information, adversarial signals, and sequential information search.
- Source files used: `README.md`, `final_research_report_outline.md`

## Slide 2: Werewolf Is a Compact Model of Hidden-Information Decision-Making

- Research purpose: Explain why the game is analytically useful.
- Core content: Hidden roles, asymmetric information, public speech, voting, deception, and reputation create a simplified but measurable decision environment.
- Source files used: `experiment_report.md`, `stage2_experiment_report.md`, `ten_player_experiment_report.md`

## Slide 3: The Central Question Became More Precise Over Time

- Research purpose: Establish the research question and show how it evolved.
- Core content: The question moved from "which mechanisms help the village?" to "how should bounded agents allocate sequential information-gathering actions under uncertainty?"
- Source files used: `final_research_report_outline.md`, `results/data_analysis/structured_seer_search/analysis_report.md`

## Slide 4: The Research Loop Was Hypothesis-Driven

- Research purpose: Show the repeated scientific workflow.
- Core content: Hypothesis -> experimental design -> simulation -> logging -> statistical interpretation -> revised hypothesis.
- Source files used: `README.md`, `experiment_report.md`, `results/data_analysis/seer_position_game_level/analysis_report.md`

## Slide 5: The Simulator Was Built as Modular Mechanisms

- Research purpose: Give the audience a mental model of the code architecture without overloading them.
- Core content: Game state, players, roles, speech, belief, trust, role actions, wolf strategy, payoff, and experiment runners are separable modules.
- Source files used: `experiment_report.md`, `stage2_experiment_report.md`, `stage3_experiment_report.md`, `stage4_experiment_report.md`

## Slide 6: Low-Information Baselines Established Wolf Dominance

- Research purpose: Show why the baseline mattered before adding complex behavior.
- Core content: Random/no-speech play gave the village only about 7% wins; suspicion voting alone barely helped; vote-driven suspicion update improved but did not solve the information problem.
- Source files used: `experiment_report.md`, `results/ablation_results.csv`

## Slide 7: Role Actions Demonstrated That Information and Intervention Matter

- Research purpose: Connect seer, witch, and hunter modules to measurable outcome shifts.
- Core content: Seer checks raised village performance; witch save/poison produced a large swing; hunter added complexity but did not monotonically improve village outcomes in the 7-player setup.
- Source files used: `experiment_report.md`, `results/ablation_results.csv`

## Slide 8: Speech and Belief Updating Turned the Game Into a Social Inference Model

- Research purpose: Explain the shift from role actions to social signals.
- Core content: Bag-of-Words speech, `p_wolf`, herding pressure, and role priors gave agents interpretable social evidence.
- Source files used: `stage2_experiment_report.md`, `multi_seed_robustness_report.md`

## Slide 9: Wolf Night Strategy Confirmed the Seer as an Information Bottleneck

- Research purpose: Explain why wolf strategy diagnostics mattered.
- Core content: `seer_first` was the best exploratory wolf night-kill strategy, implying seer information was a key village channel.
- Source files used: `stage2_experiment_report.md`, `results/wolf_strategy_results.md`

## Slide 10: Daytime Deception Showed That Speech Can Be Weaponized

- Research purpose: Present deception as the first explicit adversarial communication layer.
- Core content: `false_accuse` was powerful before costs; `false_role_claim` was harmful; deception strategy choice mattered.
- Source files used: `stage3_experiment_report.md`

## Slide 11: Credibility Costs Made Deception More Plausible

- Research purpose: Explain why deception needed a constraint.
- Core content: Accusation and self-defense costs reduced cost-free deception dominance and made adaptive wolf deception more balanced.
- Source files used: `stage3_experiment_report.md`

## Slide 12: Speaker Memory Converted Credibility Into Reputation

- Research purpose: Show Stage 4 as the transition from global suspicion to speaker-specific trust.
- Core content: Players track speaker trust; correct accusations increase trust; wrong accusations and misleading defense reduce it; stronger trust-vote weights reduced wolf win rate in sensitivity tests.
- Source files used: `stage4_experiment_report.md`

## Slide 13: The 10-Player Extension Became a Stress Test

- Research purpose: Explain why the project moved beyond the 7-player setup.
- Core content: A 10-player role pool increases noise and hidden adversaries; speech helps, deception hurts, credibility and memory remain important.
- Source files used: `ten_player_experiment_report.md`, `results/ten_player_multi_seed_summary.md`

## Slide 14: Risk Preference Added Heterogeneous Agent Behavior

- Research purpose: Explain why agent heterogeneity was introduced.
- Core content: Conservative, neutral, and aggressive populations showed different village resilience and payoff distributions.
- Source files used: `risk_preference_experiment_report.md`, `results/ten_player_risk_preference_multi_seed_summary.md`

## Slide 15: Position Theory Began as a Testable Folk Heuristic

- Research purpose: Introduce the position-theory chapter.
- Core content: Edge seats and side structure were treated as hypotheses, not assumptions.
- Source files used: `seer_position_experiment_report.md`

## Slide 16: Fixed-Role Position Results Were Suggestive but Confounded

- Research purpose: Show why the early position experiment needed validation.
- Core content: Some strategies looked strong, but fixed role placement meant seat and role were not cleanly separated.
- Source files used: `seer_position_experiment_report.md`

## Slide 17: Randomizing Seat-Role Assignment Weakened the Edge Theory

- Research purpose: Present the randomized-role validation.
- Core content: Edge seats were near the expected wolf probability; edge-first became weak and close to inner-first.
- Source files used: `seer_position_randomized_roles_report.md`, `results/data_analysis/seer_position_game_level/analysis_report.md`

## Slide 18: Formal Analysis Found No Decisive Edge-Priority Advantage

- Research purpose: Distinguish suggestive from statistically supported claims.
- Core content: Edge-first vs random and edge-first vs inner-first did not survive correction; edge-first was only clearly above default in the adjusted model.
- Source files used: `results/data_analysis/seer_position_randomized_roles/analysis_report.md`, `results/data_analysis/seer_position_game_level/analysis_report.md`

## Slide 19: Game-Level Logging Revealed the More Important Mechanism

- Research purpose: Explain why one-row-per-game logging was added.
- Core content: Logging first check, checks until first wolf, seer survival, and outcomes revealed that early wolf discovery strongly predicts village victory.
- Source files used: `results/data_analysis/seer_position_game_level/analysis_report.md`, `results/ten_player_seer_position_randomized_roles_game_level_schema.md`

## Slide 20: The Hypothesis Shifted From Seat Category to Search Path

- Research purpose: Make the key intellectual transition explicit.
- Core content: Position category was not robust; speed and coverage of information acquisition became the next hypothesis.
- Source files used: `results/data_analysis/seer_position_game_level/analysis_report.md`, `results/structured_seer_search/structured_seer_search_experiment_report.md`

## Slide 21: Structured Sequential Search Tested the New Hypothesis

- Research purpose: Mark the transition from position category to deliberate search-path structure.
- Core content: The seer experiment moved from where to look toward how to search.
- Source files used: `results/structured_seer_search/structured_seer_search_experiment_report.md`, `results/data_analysis/seer_position_game_level/analysis_report.md`

## Slide 22: Structured Search Compared Four Strategy Families

- Research purpose: Introduce the 14-strategy structured search design.
- Core content: Baseline, positional, behavioral exploitation, structured diversification, and hybrid/proxy strategies were compared across 35,000 games.
- Source files used: `results/structured_seer_search/structured_seer_search_experiment_report.md`, `results/structured_seer_search/structured_seer_search_schema.md`

## Slide 23: Structured Search Produced a Promising Descriptive Ranking

- Research purpose: Present the main descriptive structured-search results.
- Core content: `alternate_sides`, `right_to_left`, and `farthest_first` led descriptively; suspicion-only strategies performed poorly.
- Source files used: `results/structured_seer_search/structured_seer_search_strategy_summary.csv`, `results/data_analysis/structured_seer_search/analysis_report.md`

## Slide 24: Statistical Interpretation Was More Cautious Than the Ranking

- Research purpose: Separate descriptive ranking from confirmed effects.
- Core content: Overall strategy effect was significant, but positive strategy-vs-random contrasts did not survive Holm correction; `highest_p_wolf` and `highest_suspicion` were statistically worse than random.
- Source files used: `results/data_analysis/structured_seer_search/analysis_report.md`, `results/data_analysis/structured_seer_search/pairwise_strategy_contrasts.csv`

## Slide 25: Exploitation Underperformed Diversified Search

- Research purpose: Establish the exploration-exploitation insight.
- Core content: Structured diversification had about 42.66% village wins, while behavioral exploitation had about 35.52%; exploitation did not improve early discovery enough and lowered seer survival.
- Source files used: `results/data_analysis/structured_seer_search/exploitation_vs_diversification.csv`, `results/data_analysis/structured_seer_search/analysis_report.md`

## Slide 26: Directional Asymmetry Became a Validity Problem

- Research purpose: Show why a follow-up was scientifically necessary.
- Core content: `right_to_left` looked stronger than `left_to_right`; because this was not an original hypothesis, implementation artifacts had to be audited.
- Source files used: `results/data_analysis/structured_seer_search/analysis_report.md`

## Slide 27: Code Audit Identified Seat-Label and Order Dependencies

- Research purpose: Summarize the main asymmetry risks in the engine.
- Core content: Ascending player order, lower-ID tie-breaks, numeric left/right classification, stable sorting, and speech RNG tied to `player_id` can all introduce display-label effects.
- Source files used: `results/seat_order_symmetry/seat_order_asymmetry_code_audit.md`

## Slide 28: Mirror Validation Did Not Produce a Clean Direction Reversal

- Research purpose: Present the latest validation result.
- Core content: Normal and mirrored labels did not simply reverse left/right results; paired outcome agreement was only about 46%-53%, showing that mirrored labels alter downstream trajectories.
- Source files used: `results/seat_order_symmetry/seat_order_symmetry_experiment_report.md`, `results/seat_order_symmetry/seat_order_symmetry_strategy_summary.csv`

## Slide 29: The Current Research Position Is More Precise

- Research purpose: Synthesize what is supported, promising, and not yet valid to claim.
- Core content: Information flow matters, edge seats are not intrinsically wolf-heavy, early discovery predicts village victory, suspicion-only checking performs poorly, structured search is promising but not proven, and seat-order-neutral validation is the next step.
- Source files used: `results/data_analysis/seer_position_game_level/analysis_report.md`, `results/data_analysis/structured_seer_search/analysis_report.md`, `results/seat_order_symmetry/seat_order_symmetry_experiment_report.md`

## Slide 30: The Next Stage Is Mechanism Isolation in a Seat-Order-Neutral Engine

- Research purpose: End with a scientifically framed next step.
- Core content: Neutralize lower-ID advantages, decouple displayed labels from behavioral RNG, control player iteration order, preserve paired random streams, and retest left/right/alternate/random strategies.
- Source files used: `results/seat_order_symmetry/seat_order_asymmetry_code_audit.md`, `results/seat_order_symmetry/seat_order_symmetry_experiment_report.md`
