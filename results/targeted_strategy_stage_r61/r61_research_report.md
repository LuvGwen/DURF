# R6.1 Targeted Role-Strategy Gap Closing Report

## Technical Summary

R6.1 runs 5 role modules, 30000 complete game rows, and 216587 diagnostic action rows. Each module uses 1000 matched sets per policy at pilot minimum scale. The matched set is the independent unit for formal contrasts.

## Manifest Verification

- R4 payoff manifest hash: `eee8007693ec6a484632f61444a53f6f8b1b9feb64b18c865f0edf704a15c7cd`
- R5 metric manifest hash: `4b48f5aae165d6c30d5a13cd2e9c3e01f5b595ddbfeb93f7c1832b018f6861bf`
- R4 and R5 manifest files were not modified by R6.1.

## Cross-Role Summary

| Module | Best Actor-Payoff Policy | Mean Actor Payoff | Village Win | Wolf Win |
|---|---|---:|---:|---:|
| hunter | reference | -0.414 | 0.305 | 0.695 |
| seer | immediate_reveal | -0.159 | 0.337 | 0.663 |
| witch | aggressive_full | -0.037 | 0.352 | 0.648 |
| wolf | reference | 0.697 | 0.292 | 0.708 |
| villager | trust_weighted | -0.094 | 0.402 | 0.598 |

## Formal Inference

8 contrasts reached Holm-adjusted 0.05 significance within their module-metric families. Full raw and adjusted p-values are exported in `r61_global_primary_contrasts.csv`.

## Validation and Caveats

- r4_payoff_manifest_unchanged: True (eee8007693ec6a484632f61444a53f6f8b1b9feb64b18c865f0edf704a15c7cd)
- r5_metric_manifest_unchanged: True (4b48f5aae165d6c30d5a13cd2e9c3e01f5b595ddbfeb93f7c1832b018f6861bf)
- seed_isolation: True (final seeds 520-539 excluded from development/validation)
- default_r61_flags_disabled: True (All R6.1 Game flags default to False.)
- no_live_bow_r3: True (R6.1 experiment configs set enable_bow_r3=False.)
- no_ml_deployment: True (R6.1 experiment configs disable ML wolf-kill policies.)
- hunter_module_validation: True (passed)
- seer_module_validation: True (passed)
- witch_module_validation: True (passed)
- wolf_module_validation: True (passed)
- villager_module_validation: True (passed)

Action rows are diagnostic; they are not treated as independent samples. This stage does not deploy ML, does not reintroduce live BoW overrides, and does not change win conditions or role setup.
