# ML Stage 1 Limitations

This first ML stage creates observation-safe logs and offline baseline datasets. It does not deploy learned policies into the live simulator.

- The local environment does not include scikit-learn, so tree-based sklearn baselines are marked as unavailable.
- Counterfactual rollout values use a deterministic observation-safe surrogate evaluator rather than full mid-game simulator cloning.
- Existing global `p_wolf` and `suspicion_score` are treated as observable internal agent-state signals because the current rule engine already uses them for decisions.
- Larger recommended pilot scales can be run by increasing CLI limits and rollout counts.
