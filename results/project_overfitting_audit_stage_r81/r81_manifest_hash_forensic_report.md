# R8.1 Manifest Hash Forensic Report

## Decision

**A. Historical hashes verified; R8.1 handoff values were calculated from a different representation.**

The historically frozen values are the manifest self-hashes embedded in the JSON files:

- R4 authoritative content hash: `eee8007693ec6a484632f61444a53f6f8b1b9feb64b18c865f0edf704a15c7cd`
- R5 authoritative content hash: `4b48f5aae165d6c30d5a13cd2e9c3e01f5b595ddbfeb93f7c1832b018f6861bf`

The R8.1 handoff values were raw-file SHA-256 hashes:

- R4 raw file hash: `90d1a087b52368dfd30de41b53b81330ba343bc5956f848b44bb68895e56c577`
- R5 raw file hash: `092f17ebf0d09806c7ceecc3ae2968f571f887b1db3ba53d5d29d5120f2f8ec9`

Those raw-file hashes are reproducible with `shasum -a 256 <path>`, but they are not the immutable manifest self-hashes. The raw file necessarily includes the self-hash field itself and JSON formatting. The canonical/content-level hash is computed using the generator method from `payoff_manifest.py` and `financial_metric_manifest.py`.

## Authoritative Paths

- R4: `results/payoff_matrix_stage_r4/r4_payoff_manifest.json`
- R5: `results/financial_risk_stage_r5/r5_metric_definition_manifest.json`

## Git History Finding

`git log --follow --stat -- <path>` shows that the R4 manifest path was introduced only in commit `896fc4c2335afd3233f017f223128be2f50f65a9`, and the R5 manifest path was introduced only in commit `8390ce1e255c8ba7a2b23f39ca1171d203821316`. No later Git patch modified either manifest file path through R8.1.

## Commit Comparison

### R4

| Stage | Manifest | Raw SHA-256 | Canonical SHA-256 | Matches Historical | Changed From Original |
| --- | --- | --- | --- | --- | --- |
| r4_original | r4_payoff_manifest | 90d1a087b52368dfd30de41b53b81330ba343bc5956f848b44bb68895e56c577 | eee8007693ec6a484632f61444a53f6f8b1b9feb64b18c865f0edf704a15c7cd | True | False |
| r5_original | r4_payoff_manifest | 90d1a087b52368dfd30de41b53b81330ba343bc5956f848b44bb68895e56c577 | eee8007693ec6a484632f61444a53f6f8b1b9feb64b18c865f0edf704a15c7cd | True | False |
| r62 | r4_payoff_manifest | 90d1a087b52368dfd30de41b53b81330ba343bc5956f848b44bb68895e56c577 | eee8007693ec6a484632f61444a53f6f8b1b9feb64b18c865f0edf704a15c7cd | True | False |
| r71 | r4_payoff_manifest | 90d1a087b52368dfd30de41b53b81330ba343bc5956f848b44bb68895e56c577 | eee8007693ec6a484632f61444a53f6f8b1b9feb64b18c865f0edf704a15c7cd | True | False |
| r8 | r4_payoff_manifest | 90d1a087b52368dfd30de41b53b81330ba343bc5956f848b44bb68895e56c577 | eee8007693ec6a484632f61444a53f6f8b1b9feb64b18c865f0edf704a15c7cd | True | False |
| r81 | r4_payoff_manifest | 90d1a087b52368dfd30de41b53b81330ba343bc5956f848b44bb68895e56c577 | eee8007693ec6a484632f61444a53f6f8b1b9feb64b18c865f0edf704a15c7cd | True | False |

### R5

| Stage | Manifest | Raw SHA-256 | Canonical SHA-256 | Matches Historical | Changed From Original |
| --- | --- | --- | --- | --- | --- |
| r4_original | r5_metric_manifest | absent | absent | not_applicable_absent_at_this_commit | not_applicable_absent_at_this_commit |
| r5_original | r5_metric_manifest | 092f17ebf0d09806c7ceecc3ae2968f571f887b1db3ba53d5d29d5120f2f8ec9 | 4b48f5aae165d6c30d5a13cd2e9c3e01f5b595ddbfeb93f7c1832b018f6861bf | True | False |
| r62 | r5_metric_manifest | 092f17ebf0d09806c7ceecc3ae2968f571f887b1db3ba53d5d29d5120f2f8ec9 | 4b48f5aae165d6c30d5a13cd2e9c3e01f5b595ddbfeb93f7c1832b018f6861bf | True | False |
| r71 | r5_metric_manifest | 092f17ebf0d09806c7ceecc3ae2968f571f887b1db3ba53d5d29d5120f2f8ec9 | 4b48f5aae165d6c30d5a13cd2e9c3e01f5b595ddbfeb93f7c1832b018f6861bf | True | False |
| r8 | r5_metric_manifest | 092f17ebf0d09806c7ceecc3ae2968f571f887b1db3ba53d5d29d5120f2f8ec9 | 4b48f5aae165d6c30d5a13cd2e9c3e01f5b595ddbfeb93f7c1832b018f6861bf | True | False |
| r81 | r5_metric_manifest | 092f17ebf0d09806c7ceecc3ae2968f571f887b1db3ba53d5d29d5120f2f8ec9 | 4b48f5aae165d6c30d5a13cd2e9c3e01f5b595ddbfeb93f7c1832b018f6861bf | True | False |

## Interpretation

- The raw files did **not** change from original introduction through R6.2, R7.1, R8, or R8.1.
- The historical hashes were **not** raw file hashes.
- The R4 historical hash is reproduced by `json.dumps(payload_without_manifest_hash, sort_keys=True)`.
- The R5 historical hash is reproduced by `json.dumps(payload_without_metric_manifest_hash, sort_keys=True, separators=(',', ':'))`.
- No line-ending or serialization rewrite occurred in Git history.
- The R8.1 handoff reported reproducible raw-file hashes but used them where the authoritative manifest self-hashes should have been reported.

## R8.2 Gate

R8.2 must not begin unless reports cite the authoritative embedded manifest hashes above. Raw-file hashes may be included only as secondary file-integrity checks.
