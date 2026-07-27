# R2 BoW Information Leakage Audit

Status: PASS

Checks performed:

- True role is present only in evaluation label columns such as `speaker_role`.
- Final winner and downstream actions are labels only.
- Game IDs, seeds, actor UIDs, speaker UIDs, target UIDs, and template IDs are excluded from model feature builders.
- Player references in text are semantic placeholders, not numeric IDs.
- Data-derived vocabulary is built from train rows only.
- OOD template families do not overlap with train template families.
- Seer private check text is emitted only for the seer after a logged private check.
- Wolf deception text is labelled as deception or claim language, not truth.

Feature files audited:
- `bow_document_term_matrix.csv`
- `bow_vocabulary.csv`
- `bow_role_prediction_metrics.csv`
- `bow_feature_ablation_metrics.csv`

Prohibited feature metadata kept out of feature extraction:
- `speaker_role`
- `speaker_is_wolf`
- `eventual_winner`
- `later_vote_target`
- `later_elimination_target`
- `seed`
- `game_id`
- `speaker_uid`
- `template_id`
