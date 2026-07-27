# ML Stage 2B Hybrid Failure Report

| Policy | Decisions | ML/Rule Disagree | Hybrid=ML | Hybrid=Rule | Hybrid=Neither | Avg ML Range | Avg Rule Range | Diagnosis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous_frozen_ml | 669 | 82.21% | 46.04% | 62.63% | 9.12% | 0.0411 | 0.2136 | multiple mechanisms |
| existing_rule | 682 | 85.19% | 44.43% | 62.76% | 7.62% | 0.0432 | 0.2172 | multiple mechanisms |
| existing_with_ml_shadow | 682 | 85.19% | 44.43% | 62.76% | 7.62% | 0.0432 | 0.2172 | multiple mechanisms |
| high_confidence_shadow | 682 | 85.19% | 44.43% | 62.76% | 7.62% | 0.0432 | 0.2172 | multiple mechanisms |
| ml_first_kill_only | 684 | 85.09% | 43.86% | 62.87% | 8.19% | 0.0424 | 0.2115 | multiple mechanisms |
| ml_first_two_kills | 675 | 81.33% | 45.93% | 63.26% | 9.48% | 0.0418 | 0.2175 | multiple mechanisms |
| ml_single_random_kill | 670 | 85.07% | 44.48% | 62.69% | 7.76% | 0.0426 | 0.2103 | multiple mechanisms |
| selective_ml_override | 684 | 85.67% | 45.03% | 61.55% | 7.75% | 0.0428 | 0.2176 | multiple mechanisms |

The 50/50 hybrid is diagnosed only; no new hybrid weight is optimized.
