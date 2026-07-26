# ML Stage 1.5 Limitations

- This is a controlled full-simulator pilot, not a 100,000-rollout final run.
- Day-vote interventions force one actor's vote, so individual-vote causal leverage may be weak.
- scikit-learn is still unavailable locally; standard-library linear baselines are used.
- Full rollout is real simulator continuation from cloned snapshots, but snapshots are sampled at canonical decision boundaries.
