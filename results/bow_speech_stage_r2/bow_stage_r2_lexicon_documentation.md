# R2 BoW Lexicon Documentation

The core lexicon is hand-defined before final evaluation and saved in `bow_core_lexicon.csv`. It contains strategically meaningful Werewolf terms grouped into accusation, suspicion, certainty, uncertainty, defense, trust, deception, voting, role-claim, night-action, emotional-intensity, coordination, evidence, misinformation, and threat categories.

Weights are pre-specified:

- `werewolf_leaning_weight` contributes to the werewolf-leaning speech score.
- `intensity_weight` contributes to emotional intensity.
- `information_weight` contributes to information density.

The lexicon is transparent and intentionally small enough for audit. It is not tuned on final-test labels.

Tokenizer assumptions:

- Language: English.
- Casing: lowercased.
- Punctuation: normalized; exclamation marks become `exclamation`.
- Negation: `not`, `never`, `no`, `none`, and `cannot` are retained.
- Pronouns: retained only when not in the documented stopword set.
- Player references: numeric player/seat references are replaced by semantic placeholders before tokenization.
- Numbers: generic numeric strings are replaced with `NUMBER` and excluded from vocabulary construction.
