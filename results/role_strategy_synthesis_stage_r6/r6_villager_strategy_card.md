# R6 Villager Strategy Card

## R6.2 Updated Recommendation

Current strongest tested policy: `trust_weighted_structured` voting.

- Village win: 40.2% versus reference 29.1%
- Vote accuracy: 41.3% versus 34.3%
- False-positive rate: 58.7% versus 65.7%
- Actor payoff difference: +0.245
- Holm-adjusted p-value: 0.005
- Stable under leave-one-seed-out and leave-one-regime-out checks

Evidence grade: Grade A. Confidence: high within the tested strategy space.

Rejected/not recommended: random vote, live guarded BoW, structured plus BoW live integration, and p_wolf-only voting as a replacement. Guarded herding remains promising but uncertain. This is not proof of global optimality.
