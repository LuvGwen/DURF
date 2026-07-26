# DURF Werewolf Simulation: Cumulative Research Report

## 1. Executive Summary

The DURF Werewolf project uses Werewolf as a controlled social-deduction environment for studying hidden information, belief updating, deception, credibility, trust, positional search, and machine-learning policy optimization.

The cumulative evidence supports three broad conclusions:

1. Low-information Werewolf strongly favors wolves.
2. Village information mechanisms can reduce wolf advantage, but their effects depend on calibration and validation.
3. Machine-learning policy improvements cannot be trusted from row-level or surrogate evaluation alone; live matched complete-game testing is required.

The latest ML Stage 2A result is negative for the frozen wolf-kill ML policy. The existing hand-coded wolf-kill rule won 69.50% of live games, while the frozen ML policy won 61.00%, the hybrid won 58.00%, and the epsilon-greedy ML policy won 61.00%. The hybrid policy was statistically significantly worse than the existing rule after Holm correction.

## 2. Research Program And Core Question

The core research question is:

> How do belief updating, speech signals, deception, credibility costs, trust memory, search strategy, and learned policies affect collective decision-making in a hidden-information social deduction environment?

The project is also motivated by risk management. `p_wolf` acts like a dynamic risk score, wolf deception resembles adversarial manipulation, and credibility or speaker-memory mechanisms resemble reputation-based controls.

## 3. Stage 1: Basic Simulation And Payoff

Stage 1 built the modular simulation framework with players, roles, game state, night/day phases, basic special-role actions, batch simulation, and payoff calculation.

The random baseline strongly favored wolves. In the exported ablation table, the random baseline produced 93 wolf wins and 7 village wins out of 100 games. Adding village information and role mechanisms reduced the wolf advantage.

Conclusion label: `descriptive only`.

## 4. Stage 2: Speech, Belief, Herding, Role Prior, And Wolf Strategy

Stage 2 added Bag-of-Words speech signals, `p_wolf` belief updating, herding pressure, role priors, and wolf night-kill strategy diagnostics.

The main Stage 2 pattern was that social information improved village performance. Speech and belief mechanisms helped the village turn noisy day discussion into voting-relevant signals. Wolf night-kill strategy mattered, but strategic killing alone did not restore the initial wolf dominance.

Conclusion label: `promising but uncertain`, because several Stage 2 comparisons were exploratory and some outputs used 100-game runs.

## 5. Stage 3: Wolf Deception And Credibility Costs

Stage 3 added wolf daytime deception. Initial `false_accuse` behavior was too strong, reaching a 78% wolf win rate before credibility penalties. After accusation pressure and wrong-accusation penalties, `false_accuse` fell to about 50%. After self-defense credibility costs, deflection was also reduced, and adaptive deception became more realistic.

The scientific lesson is that deception must carry credibility risk. Without costs, manipulative speech becomes a dominant strategy; with costs, deception remains relevant but no longer cost-free.

Conclusion label: `promising but uncertain`.

## 6. Stage 4: Speaker-Specific Trust Memory

Stage 4 added speaker-specific trust memory. Each player can track the credibility of other speakers and use that memory in voting. A trust-vote-weight sensitivity experiment showed that increasing trust weight could reduce wolf win rate: the reported wolf win rate fell from 47.80% at trust vote weight 0.00 to 36.40% at trust vote weight 0.40.

The trend was not strictly monotonic, and later trust-weighted speech/herding experiments showed that reputation systems can create unintended dynamics. The mechanism is valuable, but it requires calibration and formal multi-seed testing.

Conclusion label: `promising but uncertain`.

## 7. Ten-Player And Risk Preference Experiments

The ten-player extension tested larger-game dynamics, limited last words, risk preferences, and role-specific decision tendencies. Multi-seed risk preference results showed that conservative-majority trust-memory populations reduced wolf win rate relative to all-neutral trust memory, while aggressive-majority populations increased wolf win rate.

The risk-preference results suggest that group decision culture matters: conservative agents can resist wolf manipulation more effectively in this simulation, while aggressive agents may create noisy or exploitable eliminations.

Conclusion label: `promising but uncertain`.

## 8. Seer Position And Randomized Roles

The randomized-role seer-position analysis tested whether edge-priority checking retained an advantage after roles were randomized across seats. Across 17,500 completed games, edge seats were not meaningfully wolf-heavy after randomization. Edge-first did not outperform random checking in a statistically supported way.

Key result: adjusted edge-first versus random odds ratio was 1.05 with p = 0.417. Edge-first first-check wolf rate was 34.20%, while random was 34.72%.

Conclusion label: `hypothesis rejected` for the edge-priority advantage after role randomization.

## 9. Structured Seer Search

Structured seer search compared 14 strategies over 35,000 game-level rows. The omnibus strategy effect was statistically significant. `alternate_sides` had the highest descriptive village win rate at 44.16%, compared with random at 40.52%, but the positive contrast did not survive Holm correction: OR 1.161, raw p = 0.0092, Holm p = 0.0552.

Behaviorally exploitative strategies were harmful. `highest_p_wolf` versus random had OR 0.786 and Holm p = 0.000276, and `highest_suspicion` was similarly harmful.

Conclusion labels:

- Diversified structured search: `promising but uncertain`.
- Behavioral exploitation in seer search: `statistically supported harmful effect`.

## 10. Seat-Order Neutrality And Physical Symmetry

Seat-order-neutral experiments separated displayed labels from physical layout. Displayed-label rows were deterministic duplicates, so the effective independent sample size was based on physical configurations rather than raw rows.

The physical-clockwise strategy showed a possible 3.04 percentage-point advantage over random neutral, but this did not survive Holm correction. The exact replay and physical mirror experiment later showed 100% agreement for supplied-action replay, physical mirror replay, and strategy mirror action validation.

Conclusion labels:

- Displayed label artifact: `hypothesis rejected`.
- Physical path-layout effect: `promising but uncertain`.
- Engine mirror symmetry: `hypothesis supported`.

## 11. ML Stage 1: Observation-Safe Logging And Initial Models

ML Stage 1 created decision datasets and initial models. It produced 7,155 candidate rows across seer-check, wolf-kill, and day-vote contexts. The initial row-level village-vote model reported ROC-AUC 0.9458, but later grouped validation showed that this was optimistic.

The lesson is methodological: ordinary row splits are unsafe when candidate rows share games, decision states, and latent state histories.

Conclusion label: `weak/inconclusive` after later validation.

## 12. ML Stage 1.5: Full-State Rollout Validation

ML Stage 1.5 introduced grouped splits and full-state rollout validation. It found weak surrogate-to-full validity for wolf kills, with Spearman correlation 0.0718. It also showed that final-test village-vote identity ROC-AUC was only 0.6679, not the much higher Stage 1 row-split estimate.

The Stage 1.5 shadow wolf-kill policy looked promising, with a reported final-test shadow ML action-value recommendation of 0.85 versus 0.70 for the existing rule. This result motivated live Stage 2A testing but was not sufficient for deployment.

Conclusion label: `promising but uncertain`.

## 13. ML Stage 2A: Frozen Wolf-Kill Policy Live Test

ML Stage 2A froze the Stage 1.5 wolf-kill model and tested it in live complete games. The result was negative for the ML policies.

| Policy | Games | Wolf win rate | 95% CI | Difference vs existing | Holm p |
|---|---:|---:|---|---:|---:|
| existing_rule | 200 | 69.50% | 63.12%-75.88% | NA | NA |
| frozen_ml | 200 | 61.00% | 54.24%-67.76% | -8.50 pp | 0.0792 |
| frozen_hybrid_50_50 | 200 | 58.00% | 51.16%-64.84% | -11.50 pp | 0.0033 |
| frozen_ml_epsilon_010 | 200 | 61.00% | 54.24%-67.76% | -8.50 pp | 0.0792 |

The hybrid policy had a statistically supported harmful effect after Holm correction. The pure ML and epsilon variants were directionally harmful but not significant after correction.

Conclusion label: `statistically supported harmful effect` for the hybrid; `weak/inconclusive` but harmful direction for pure ML and epsilon.

## 14. Cross-Stage Evidence Chain

The evidence chain has become progressively stricter:

1. Single-seed ablations established mechanisms.
2. Multi-seed experiments tested robustness.
3. Randomized-role seer-position analysis removed fixed seat-role confounding.
4. Structured search separated path design from behavioral exploitation.
5. Seat-order-neutral experiments removed displayed-label artifacts.
6. Supplied-action replay validated physical mirror symmetry.
7. ML Stage 1.5 replaced row-level optimism with grouped and full-state validation.
8. ML Stage 2A required frozen live complete-game deployment.

The project increasingly rejects results that do not survive stronger validation.

## 15. Current Scientific Conclusions

Current best-supported conclusions:

- Wolves dominate low-information baselines.
- Village information mechanisms reduce wolf advantage.
- Deception can restore wolf advantage if it is cost-free.
- Credibility costs and trust memory are necessary controls against deception.
- Edge-priority seer checking is not supported after role randomization.
- Structured diversified seer search is promising but not yet corrected-significant against random.
- Behaviorally exploitative seer search using current suspicion or `p_wolf` signals is harmful.
- The simulation engine passes physical mirror replay validation.
- Frozen ML wolf-kill policies did not improve live games; the hybrid policy was statistically harmful.

## 16. Next Research Direction

The next experiment should not simply add a more complex model. It should address the failure mode revealed by Stage 2A:

> A learned policy must optimize live strategic consequences, not weak candidate-level proxies.

Recommended next direction:

1. Build role-removal-aware and information-suppression-aware wolf-kill features.
2. Keep all features observation-safe.
3. Use grouped splits and final live seeds held out from model selection.
4. Treat shadow rollout as screening only.
5. Require matched live complete-game validation before claiming improvement.
6. Compare against existing rule, frozen ML, hybrid, and role-removal-aware ML.
7. Report CIs, adjusted p-values, effect sizes, seed robustness, regime robustness, distribution shift, overfitting diagnostics, leakage audit, and failure cases.

The cumulative evidence registry for this report is stored at:

```text
results/research_progress/cumulative_evidence_registry.csv
```

