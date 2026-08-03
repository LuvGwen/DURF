# R7 Project Finding Comparison Report

Generated on 2026-08-04. This R7 artifact is literature synthesis only; no gameplay experiment was run.

## Finding-to-Literature Map

| Finding | Chapter | Relationship | Sources | Safe interpretation |
| --- | --- | --- | --- | --- |
| F01 | low_information_baseline | consistent_with_literature | S001;S009;S010 | Low-information hidden-role environments favor the informed minority. |
| F02 | information_and_speech | consistent_with_literature | S005;S011;S019 | Communication can transmit useful signals when credibility is bounded. |
| F03 | villager_strategy | consistent_with_literature | S019;S020;S021;S025 | Reputation-weighted aggregation parallels trust and reputation systems. |
| F04 | herding | consistent_with_literature | S015;S016;S017 | Cascades and conformity can propagate wrong signals. |
| F05 | bow_r2 | methodological_parallel | S038;S039;S040 | Sparse lexical features can carry predictive signal. |
| F06 | bow_r2 | consistent_with_literature | S041;S042;S043;S044 | Template failure is a domain-shift problem. |
| F07 | bow_r3 | consistent_with_literature | S041;S046;S047;S048 | Prediction quality need not translate into policy value. |
| F08 | ml_policy | consistent_with_literature | S046;S047;S048;S049;S050 | Offline or surrogate evaluation can fail under live distribution shift. |
| F09 | seer_information | consistent_with_literature | S009;S035;S036 | Private information can have strategic value. |
| F10 | seer_search | extends_literature | S042;S043;S055 | Local risk scores can be post-treatment or misleading if not calibrated. |
| F11 | position_theory | methodological_parallel | S055;S057 | Randomized assignment and validation can falsify intuitive artifacts. |
| F12 | seer_reveal | partially_consistent | S011;S012;S035 | Information revelation has benefits and strategic costs. |
| F13 | seer_reveal | extends_literature | S011;S030;S035 | Public signalers can become strategic targets. |
| F14 | risk_metrics | partially_consistent | S036;S058;S060 | Information value should be separated from outcome dependence. |
| F15 | witch | methodological_parallel | S047;S057;S064 | High-impact interventions can raise expected value but require risk controls. |
| F16 | witch | consistent_with_literature | S060;S063;S064 | Downside/tail metrics clarify intervention harm. |
| F17 | witch | extends_literature | S058;S060;S061 | Opportunity-cost framing explains excessive inaction. |
| F18 | witch | partially_consistent | S057;S064 | Risk aversion can be harmful when resources expire unused. |
| F19 | witch | consistent_with_literature | S060;S063 | Lower risk is not automatically higher payoff. |
| F20 | hunter | consistent_with_literature | S060;S061;S063 | Irreversible high-impact actions concentrate downside risk. |
| F21 | hunter | consistent_with_literature | S055;S057;S064 | Uninformed high-impact actions can be dominated by more conservative rules. |
| F22 | hunter | partially_consistent | S058;S060;S064 | Avoiding downside can also forgo positive option value. |
| F23 | hunter | no_direct_prior_comparison | S019;S060 | No direct prior Hunter policy literature was identified. |
| F24 | werewolf_strategy | consistent_with_literature | S006;S009;S055 | Strategic targeting matters in hidden-role games. |
| F25 | werewolf_strategy | partially_consistent | S002;S003;S030 | Concealment is useful only when it does not sacrifice strategic pressure. |
| F26 | werewolf_strategy | consistent_with_literature | S006;S030;S035 | Informed actors benefit from targeting high-value information sources. |
| F27 | ml_policy | consistent_with_literature | S047;S048;S050;S051 | Offline policies can fail when rolled out repeatedly. |
| F28 | ml_policy | consistent_with_literature | S047;S050;S051 | Combining model and rule scores can be unsafe without live validation. |
| F29 | werewolf_deception | partially_consistent | S030;S022;S024 | Manipulation can pay, but evidence quality depends on sample balance. |
| F30 | werewolf_deception | consistent_with_literature | S002;S003;S027;S028 | Deception effectiveness depends on type, credibility, and audience. |
| F31 | financial_risk | methodological_parallel | S029;S030;S058;S059 | High return can accompany high strategic risk in a payoff analogue. |
| F32 | financial_risk | consistent_with_literature | S060;S061;S063 | Tail-risk metrics reveal harms hidden by means. |
| F33 | financial_risk | methodological_parallel | S058;S059;S062 | Efficient-frontier analogies compare return against volatility and downside risk. |
| F34 | financial_risk | consistent_with_literature | S058;S060;S063 | Risk metrics must be interpreted with expected payoff. |
| F35 | financial_risk | consistent_with_literature | S063;S057 | Metric definitions and coefficients affect rankings. |
| F36 | financial_risk | methodological_parallel | S058;S062;S064 | Opportunity cost links inaction to forgone return. |
| F37 | engine_validity | consistent_with_literature | S055;S057 | Simulation validation should isolate artifacts. |
| F38 | engine_validity | consistent_with_literature | S055;S057 | Replay and counterfactual validation increase engine credibility. |
| F39 | ml_validation | consistent_with_literature | S042;S043;S044;S050 | Grouped validation controls overfitting and dataset leakage. |
| F40 | ml_validation | consistent_with_literature | S046;S047;S048;S049;S050 | Offline-to-online gaps require live validation. |
| F41 | method_validity | methodological_parallel | S055;S057;S063 | Attribution units and independent samples must match claims. |

## Interpretation

Most findings are consistent with or extend prior theory. Negative findings, especially BoW live failure and ML live-policy failure, are preserved rather than smoothed into success claims.
