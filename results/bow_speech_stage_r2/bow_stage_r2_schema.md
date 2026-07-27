# R2 BoW Speech Dataset Schema

The primary dataset is `bow_speech_utterance_dataset.csv`. Each row is one generated utterance derived from one legal structured speech or last-words event.

## Identification

- `utterance_id`: Stable utterance identifier.
- `game_id`: Source game identifier. Not used as a model feature.
- `game_family_id`: Independent grouped unit for split and bootstrap logic.
- `base_configuration_id`: Split-specific base configuration label.
- `seed`: Source simulation seed. Not used as a model feature.
- `round`, `phase`: Public game timing fields.
- `speaker_uid`, `target_uid`: Evaluation identifiers. Not used as model features.
- `template_family`, `template_id`: Template metadata. Not used as model features.
- `behavioral_regime`, `dataset_split`: Regime and split labels.

## Text and BoW Features

- `utterance_text`: Generated English utterance using semantic placeholders such as `PLAYER_TARGET`.
- `tokens`: Deterministic lowercased BoW tokens.
- `token_count`, `unique_token_count`: Text length features.
- `bow_werewolf_leaning_score`: Rule-based score in [0, 1].
- `bow_emotional_intensity_score`: Rule-based score in [0, 1].
- `bow_information_density_score`: Rule-based score in [0, 1].

## Structured Labels and Evaluation Labels

Structured speech labels include `speech_intent`, `speech_subtype`, `deception_type`, and Boolean intent flags. Evaluation labels include `speaker_is_wolf`, `speaker_role`, `eventual_winner`, and `speaker_team_win`. True role and future outcomes are labels only and are excluded from feature extraction.
