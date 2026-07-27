# R2 BoW Pre-Registration

## Hypotheses

H-R2-1: BoW scores recover structured speech intent better than chance.
H-R2-2: Werewolf-leaning score distinguishes wolf-generated speech from village-generated speech on held-out game families.
H-R2-3: Emotional-intensity score is higher for aggressive, panic, and defensive speech than for neutral speech.
H-R2-4: Information-density score is higher for concrete claims, vote references, checks, or causal reasoning than vague speech.
H-R2-5: BoW features add predictive value beyond existing `p_wolf` and `suspicion_score`.
H-R2-6: BoW-only models are weaker than structured + BoW models.
H-R2-7: Template-family holdout tests determine whether the system is template-bound.
H-R2-8: Keyword ablation tests whether direct role words drive performance.

## Split Design

Vocabulary construction and model fitting use only `train` rows. Validation, final-test, unseen-template, and unseen-regime rows are held out. Template families marked as OOD templates are excluded from the training split.

## Decision Boundary

R2 is a shadow feature stage only. No live voting, seer checking, witch action, hunter action, wolf kill, payoff, or win-condition logic is changed.
