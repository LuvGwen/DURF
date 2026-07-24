# Physical Direction Replay Implementation Audit

| file | path | behavior | isolation |
|---|---|---|---|
| physical_direction_replay.py | SuppliedAction | Structured action record keyed by actor_uid and physical target. | New diagnostic-only representation; no default engine change. |
| physical_direction_replay.py | ReplayController | Consumes supplied actions without strategy modules choosing new targets. | Validation errors raise ReplayError with phase/action context. |
| physical_direction_replay.py | mirror_physical_seat | Uses 1<->10, 2<->9, 3<->8, 4<->7, 5<->6. | Involutive and reverses clockwise/counterclockwise distances. |
| physical_direction_replay_experiment.py | Experiment A | Capture normal game actions and replay same physical actions. | Replay correctness test, not a mirror test. |
| physical_direction_replay_experiment.py | Experiment B | Replay mirrored supplied actions in mirrored physical layout. | Compares canonical mirrored state back to reference coordinates. |
| physical_direction_replay_experiment.py | Experiment C | Run clockwise original vs counterclockwise mirrored strategy. | Does not force actions; compares generated action signatures. |

No simulator default behavior is changed by this stage.
