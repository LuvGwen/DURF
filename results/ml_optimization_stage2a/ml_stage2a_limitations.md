# ML Stage 2A Limitations

- This is a pilot-scale live A/B test with 800 complete games and 200 matched sets. It is smaller than the preferred large-scale design in the prompt, so statistical power is limited.
- The frozen model is a linear ridge model trained on Stage 1.5 full-rollout targets. It is interpretable but may underfit nonlinear target-selection interactions.
- The existing production wolf-kill rule is preserved as the control condition even though it may use true role knowledge internally. The frozen ML feature matrix itself excludes true village role labels and future outcomes.
- Shadow evaluation used 105 decision states and 2940 rollout simulations, below the preferred 75,000+ rollout scale.
- Hybrid weight 0.50 and epsilon 0.10 are fixed pilot settings, not optimized on live-test data.
- Coefficients are reported for interpretation only and are not causal estimates.
- Standard-library paired tests are used instead of conditional logistic regression because no external statistical packages are used.
