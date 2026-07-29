# R6 Information Leakage Audit

R6 is analysis-only and does not compute new in-game decisions. It reads
frozen outputs that already contain their own leakage audits where
applicable. Role recommendations do not use hidden role information from
future events as a decision input.

Source files reviewed: 25

Result: PASS for R6 synthesis scope. The remaining caveat is that
information-premium labels are outcome-dependent descriptive associations,
as documented in R5.1.
