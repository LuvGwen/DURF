# Residual Validity Assessment

## Source Reviewed

- `results/seat_order_neutral/seat_order_neutral_implementation_audit.md`
- Prior symmetry audit and structured-search analysis reports were used as background context.

## Assessment

The neutral engine successfully removes the displayed-label paths identified in the prior audit for this experiment: lower displayed IDs no longer decide exact ties, speech/vote iteration follows a neutral actor order, speech RNG uses actor_uid-based substreams, and role assignment is fixed in physical-seat terms before labels are mapped.

The strongest validation evidence is deterministic equivalence: normal, mirrored, and rotated label conditions produce identical physical check sequences, winners, total rounds, seer survival, and final physical alive sets in all matched sets. This is stronger than a non-significant label effect because no physical divergence is observed.

Residual limitations remain. The narrow no-strategy control checks engine equivalence under simplified conditions, but there is not yet a full externally supplied-action replay harness. Therefore, the analysis can rule out displayed-label artifacts in the neutral experiment, but it cannot fully rule out a deeper physical clockwise/counterclockwise asymmetry embedded in action resolution, strategy implementation, or circular-seat representation.

The physical direction strategies themselves appear symmetric in implementation: clockwise and counterclockwise use matching distance functions and differ only in direction. However, the game state and strategy path can still interact with physical wolf placement. Any clockwise advantage should therefore be interpreted as a possible physical path-layout effect until a supplied-action replay or randomized physical-orientation experiment closes this remaining validity gap.

## Audit Excerpt

```text
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

- **Ar
```
