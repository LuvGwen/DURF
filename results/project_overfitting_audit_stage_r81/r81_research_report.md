# R8.1 Project-Wide Overfitting and Selection-Bias Audit

R8.1 audited the entire DURF Werewolf research pipeline for researcher degrees of freedom, multiple testing, outcome switching, seed reuse, post-selection winner's curse, payoff sensitivity, distribution shift, BoW/ML overfitting, literature confirmation bias, and overclaiming risk.

R4 manifest hash: `90d1a087b52368dfd30de41b53b81330ba343bc5956f848b44bb68895e56c577`

R5 metric manifest hash: `092f17ebf0d09806c7ceecc3ae2968f571f887b1db3ba53d5d29d5120f2f8ec9`

Main result: R4/R5 frozen manifests are unchanged and no raw gameplay leakage was found. However, R8 reused the R6.1 final seeds for maximum-payoff recommendation selection. This is classified as post-test policy selection, so Seer immediate_reveal and Witch aggressive_full are downgraded to replication-required experimental candidates. Villager trust_weighted remains the strongest supported positive policy; Hunter and Werewolf retain reference/default policies.

Readiness decision: **R8.2 TARGETED REPLICATION REQUIRED** before final R9 default-recommendation claims.
