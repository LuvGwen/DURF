# Documentation Inconsistencies And Revision Log

## 1. Original Proposal File Not Found

The prompt references a Dean's Undergraduate Research Fund proposal, but no proposal file was found in the repository. The proposal-alignment audit uses the prompt-provided proposal summary. Verification status: `source_not_found`.

## 2. Stage 1 Game Count Inconsistency

`experiment_report.md` states that each Stage 1 ablation condition was evaluated with 500 games. The current `results/ablation_results.csv` contains 100 games per condition and appears to reflect a later exported ablation state. Reports should cite the Stage 1 table when discussing Stage 1 and cite the CSV only with this caveat.

## 3. Stage 1 Identity ROC-AUC Revised By Stage 1.5

ML Stage 1 reported village-vote logistic ROC-AUC around 0.9458. ML Stage 1.5 grouped validation reported final-test ROC-AUC around 0.6679, close to existing `p_wolf` at 0.6586. The Stage 1 pilot estimate must not be cited without the Stage 1.5 correction.

## 4. Surrogate Action Values Revised By Full Rollout

Surrogate models appeared useful in early ML outputs, but Stage 1.5 found weak surrogate-to-full validity for wolf-kill and day-vote action values. Surrogate value must not be treated as live game value.

## 5. Stage 1.5 Shadow Advantage Revised By Stage 2A Live Test

Stage 1.5 shadow analysis suggested approximately +0.150 wolf-team action-value improvement for ML wolf-kill recommendation. Stage 2A live complete-game results showed existing_rule wolf win 69.50%, frozen_ml 61.00%, hybrid 58.00%, and epsilon 61.00%. The hybrid policy was statistically harmful after Holm correction.

## 6. Seat-Order-Neutral Raw Rows Versus Independent Units

The seat-order-neutral source file has 30,000 rows, but normal, mirrored, and rotated label rows are deterministic duplicates for tested physical mechanisms. Effective independent strategy inference uses 10,000 strategy/base rows and 2,500 physical configurations.

## 7. Structured Seer Search Positive Strategy Ranking

`alternate_sides` and `right_to_left` are descriptively strong, but their positive contrasts versus random do not survive Holm correction. They should be called promising but uncertain, not statistically superior.

## 8. Bag-of-Words Completion Risk

The project has structured speech act labels, but the proposal's BoW requirements include werewolf-leaning, emotional intensity, and information density. These should remain partially completed or not started until formal tokenized scores exist.

## 9. Financial-Metric Completion Risk

The project has payoff outputs and conceptual financial analogies, but formal risk cost, opportunity cost, payoff variance, risk-adjusted return, and Sharpe-like metrics remain incomplete.
