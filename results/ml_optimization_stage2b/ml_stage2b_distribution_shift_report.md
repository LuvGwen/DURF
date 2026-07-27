# ML Stage 2B Distribution Shift Report

| Policy | Shift | Rows | Wolf Win | Avg Margin | Avg Prior ML | Avg Cum. ML |
| --- | --- | --- | --- | --- | --- | --- |
| continuous_frozen_ml | in_distribution | 152 | 61.84% | 0.0086 | 0.0000 | 1.0000 |
| continuous_frozen_ml | mild_shift | 137 | 62.77% | 0.0108 | 0.7080 | 1.7080 |
| continuous_frozen_ml | strong_shift | 380 | 58.68% | 0.0108 | 1.9395 | 2.9395 |
| existing_rule | in_distribution | 177 | 73.45% | 0.0093 | 0.0000 | 0.0000 |
| existing_rule | mild_shift | 99 | 66.67% | 0.0099 | 0.0000 | 0.0000 |
| existing_rule | strong_shift | 406 | 69.70% | 0.0125 | 0.0000 | 0.0000 |
| existing_with_ml_shadow | in_distribution | 177 | 73.45% | 0.0093 | 0.0000 | 0.0000 |
| existing_with_ml_shadow | mild_shift | 99 | 66.67% | 0.0099 | 0.0000 | 0.0000 |
| existing_with_ml_shadow | strong_shift | 406 | 69.70% | 0.0125 | 0.0000 | 0.0000 |
| high_confidence_shadow | in_distribution | 177 | 73.45% | 0.0093 | 0.0000 | 0.0000 |
| high_confidence_shadow | mild_shift | 99 | 66.67% | 0.0099 | 0.0000 | 0.0000 |
| high_confidence_shadow | strong_shift | 406 | 69.70% | 0.0125 | 0.0000 | 0.0000 |
| ml_first_kill_only | in_distribution | 152 | 75.66% | 0.0086 | 0.0000 | 1.0000 |
| ml_first_kill_only | mild_shift | 127 | 68.50% | 0.0102 | 0.6220 | 1.0000 |
| ml_first_kill_only | strong_shift | 405 | 71.60% | 0.0120 | 1.0000 | 1.0000 |
| ml_first_two_kills | in_distribution | 152 | 67.11% | 0.0086 | 0.0000 | 1.0000 |
| ml_first_two_kills | mild_shift | 137 | 59.12% | 0.0107 | 0.7080 | 1.6496 |
| ml_first_two_kills | strong_shift | 386 | 61.66% | 0.0113 | 1.6917 | 2.0000 |
| ml_single_random_kill | in_distribution | 169 | 68.64% | 0.0091 | 0.0000 | 0.3314 |
| ml_single_random_kill | mild_shift | 114 | 65.79% | 0.0106 | 0.2982 | 0.7193 |

Decision rows, not candidate rows, are the diagnostic unit for this report.
