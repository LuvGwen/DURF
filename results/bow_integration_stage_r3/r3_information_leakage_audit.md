# R3 Information Leakage Audit

Status: PASS

- Live BoW feature input uses utterance text and public belief state.
- True role, speech_intent, deception_type, template ID, future vote, future winner, future elimination, game ID, seed, actor UID, and candidate true role are excluded from live target-selection features.
- OOD labels are used only for explicit selective-override guardrails.
- Full-rollout value labels are post-hoc analysis fields only.
