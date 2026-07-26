# ML Stage 2A Distribution Shift Report

| Category | Rows | Wolf Win Rate | Avg Standardized Distance | Avg Max |z| | Avg Fraction Outside Train Min/Max | Avg Prediction Extremity |
| --- | --- | --- | --- | --- | --- | --- |
| in_distribution | 3815 | 63.49% | 0.3727 | 1.5335 | 0.0012 | 0.2062 |
| mild_shift | 3684 | 60.59% | 0.6520 | 2.2142 | 0.1259 | 0.1935 |
| strong_shift | 6881 | 57.43% | 1.3228 | 3.8423 | 0.3084 | 0.1484 |
| existing_rule:in_distribution | 1120 | 71.25% | 0.3186 | 1.3295 | 0.0012 | 0.2096 |
| existing_rule:mild_shift | 743 | 63.80% | 0.7618 | 2.5735 | 0.1271 | 0.1879 |
| existing_rule:strong_shift | 1732 | 65.88% | 1.3135 | 3.8154 | 0.3165 | 0.1399 |
| frozen_hybrid_50_50:in_distribution | 1120 | 58.48% | 0.3186 | 1.3295 | 0.0012 | 0.2096 |
| frozen_hybrid_50_50:mild_shift | 749 | 55.27% | 0.7647 | 2.5825 | 0.1278 | 0.1890 |
| frozen_hybrid_50_50:strong_shift | 1726 | 53.82% | 1.3451 | 3.9034 | 0.3197 | 0.1458 |
| frozen_ml:in_distribution | 1120 | 62.77% | 0.3186 | 1.3295 | 0.0012 | 0.2096 |
| frozen_ml:mild_shift | 738 | 56.10% | 0.7575 | 2.5635 | 0.1261 | 0.1880 |
| frozen_ml:strong_shift | 1738 | 56.62% | 1.3402 | 3.8955 | 0.3194 | 0.1518 |
| frozen_ml_epsilon_010:in_distribution | 1120 | 62.77% | 0.3186 | 1.3295 | 0.0012 | 0.2096 |
| frozen_ml_epsilon_010:mild_shift | 741 | 55.74% | 0.7584 | 2.5631 | 0.1265 | 0.1887 |
| frozen_ml_epsilon_010:strong_shift | 1733 | 56.43% | 1.3348 | 3.8875 | 0.3192 | 0.1522 |

Distribution-shift flags are simple deterministic diagnostics, not a learned density model. They are used to identify candidate states where frozen-model failures may cluster.
