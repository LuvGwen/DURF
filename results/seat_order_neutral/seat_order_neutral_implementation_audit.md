# Seat-Order-Neutral Implementation Audit

| original file | function/path | original behavior | neutral-mode behavior | default behavior changed | validation method | residual limitation |
|---|---|---|---|---|---|---|
| seer_action.py | seer target selection | Legacy strategies can sort or sample by displayed player_id order. | Physical strategies use physical_seat; exact ties use actor_uid or sha256 tie-break. | No | test_seat_order_neutral.py and raw target diagnostics. | Legacy names intentionally retain legacy interpretation. |
| game.py | day speech/vote iteration | Alive-player order inherited state.players/displayed order. | Game.state.players is ordered by a stable actor_uid permutation. | No | Neutral actor order is logged and matched across label conditions. | Different game states can still diverge after real gameplay changes. |
| speech_action.py | build_speech_rng | Speech RNG included player_id. | Neutral mode uses sha256 sub-seeds from seed/base/round/actor_uid. | No | Speech sub-seed test checks same physical actor under mirroring. | Speech content can diverge after physical game states diverge. |
| voting.py | choose_vote_target | Stable sort preserved earlier candidate order on exact ties. | Exact ties add displayed-label-independent sha256 actor tie-break. | No | Neutral tie-break independence test. | Non-tied random noise remains part of existing gameplay. |
| wolf_strategy.py | choose_wolf_kill_target | Stable sort/random choice could depend on player list order. | Neutral mode uses actor_uid tie-break or neutral random choice. | No | Candidate-order tests and event-log diagnostics. | True branch divergence can still change later random consumption. |
| witch_action.py | perform_witch_poison | max() favored first candidate on equal suspicion. | Neutral mode sorts by score and sha256 actor tie-break. | No | Exact-tie unit test. | Potion policy itself is unchanged. |
| hunter_action.py | perform_hunter_shot | max() favored first candidate on equal suspicion. | Neutral mode sorts by score and sha256 actor tie-break. | No | Exact-tie unit test. | Hunter policy itself is unchanged. |
| seat_order_neutral_experiment.py | role assignment and labels | Previous mirrored games preserved roles but engine still used labels. | Roles are assigned to physical seats; labels are mapped afterward. | No | Matched-set validation checks physical seer/wolf seats. | This does not alter older randomized-role experiments. |

## Required Audit Answers

- **Are lower displayed IDs still favored on exact ties in neutral mode?** No. Neutral-mode exact ties use actor_uid or sha256 tie-breaks independent of displayed labels.
- **Does speech order still depend on displayed labels?** No. The game orders players by a neutral actor_uid permutation.
- **Does voting iteration depend on displayed labels?** No. Voting follows the same neutral actor_uid order.
- **Does speech RNG use displayed player_id?** No in neutral mode; yes in default mode for backward compatibility.
- **Do normal and mirrored pairs use equivalent physical actor ordering?** Yes. The neutral actor order is generated from seed, base index, and actor_uid.
- **Can displayed labels affect role assignment?** No in this experiment. Roles are assigned to physical seats before labels are mapped.
- **Can displayed labels affect main RNG substreams?** Main game seeds and neutral substreams are derived without displayed labels.
- **Are any known order-dependent paths still unresolved?** Residual divergence can occur after real physical state divergence and through non-tied gameplay randomness; these are logged rather than tuned away.
