# Pairwise Strategy Comparisons

| Metric | Strategy A | Strategy B | Mean diff pp | 95% CI | Permutation p | Holm p | Cohen dz | >=3pp | Significant |
|---|---|---|---|---|---|---|---|---|---|
| wolf_win_rate | seer_default | seer_random | 3.04 | [0.49, 5.59] | 0.06 | 1.00 | 1.48 | True | False |
| wolf_win_rate | seer_default | seer_edge_first | 3.96 | [-0.10, 8.02] | 0.06 | 1.00 | 1.21 | True | False |
| wolf_win_rate | seer_default | seer_inner_first | 4.20 | [1.25, 7.15] | 0.06 | 1.00 | 1.77 | True | False |
| wolf_win_rate | seer_default | seer_highest_p_wolf | -2.60 | [-5.04, -0.16] | 0.06 | 1.00 | -1.32 | False | False |
| wolf_win_rate | seer_default | seer_highest_suspicion | -2.64 | [-4.79, -0.49] | 0.06 | 1.00 | -1.53 | False | False |
| wolf_win_rate | seer_default | seer_opposite_side | 2.04 | [-0.61, 4.69] | 0.12 | 1.00 | 0.96 | False | False |
| wolf_win_rate | seer_random | seer_edge_first | 0.92 | [-2.11, 3.95] | 0.50 | 1.00 | 0.38 | False | False |
| wolf_win_rate | seer_random | seer_inner_first | 1.16 | [-4.25, 6.57] | 0.56 | 1.00 | 0.27 | False | False |
| wolf_win_rate | seer_random | seer_highest_p_wolf | -5.64 | [-9.17, -2.11] | 0.06 | 1.00 | -1.99 | True | False |
| wolf_win_rate | seer_random | seer_highest_suspicion | -5.68 | [-7.93, -3.43] | 0.06 | 1.00 | -3.13 | True | False |
| wolf_win_rate | seer_random | seer_opposite_side | -1.00 | [-5.69, 3.69] | 0.50 | 1.00 | -0.26 | False | False |
| wolf_win_rate | seer_edge_first | seer_inner_first | 0.24 | [-5.56, 6.04] | 0.94 | 1.00 | 0.05 | False | False |
| wolf_win_rate | seer_edge_first | seer_highest_p_wolf | -6.56 | [-10.42, -2.70] | 0.06 | 1.00 | -2.11 | True | False |
| wolf_win_rate | seer_edge_first | seer_highest_suspicion | -6.60 | [-8.69, -4.51] | 0.06 | 1.00 | -3.92 | True | False |
| wolf_win_rate | seer_edge_first | seer_opposite_side | -1.92 | [-6.73, 2.89] | 0.38 | 1.00 | -0.50 | False | False |
| wolf_win_rate | seer_inner_first | seer_highest_p_wolf | -6.80 | [-10.11, -3.49] | 0.06 | 1.00 | -2.55 | True | False |
| wolf_win_rate | seer_inner_first | seer_highest_suspicion | -6.84 | [-10.86, -2.82] | 0.06 | 1.00 | -2.11 | True | False |
| wolf_win_rate | seer_inner_first | seer_opposite_side | -2.16 | [-3.96, -0.36] | 0.12 | 1.00 | -1.49 | False | False |
| wolf_win_rate | seer_highest_p_wolf | seer_highest_suspicion | -0.04 | [-2.30, 2.22] | 1.00 | 1.00 | -0.02 | False | False |
| wolf_win_rate | seer_highest_p_wolf | seer_opposite_side | 4.64 | [2.16, 7.12] | 0.06 | 1.00 | 2.32 | True | False |
| wolf_win_rate | seer_highest_suspicion | seer_opposite_side | 4.68 | [1.71, 7.65] | 0.06 | 1.00 | 1.96 | True | False |
| seer_found_wolf_rate | seer_default | seer_random | -3.37 | [-4.44, -2.30] | 0.06 | 1.00 | -3.90 | True | False |
| seer_found_wolf_rate | seer_default | seer_edge_first | -4.73 | [-6.04, -3.43] | 0.06 | 1.00 | -4.49 | True | False |
| seer_found_wolf_rate | seer_default | seer_inner_first | -2.91 | [-4.71, -1.11] | 0.06 | 1.00 | -2.01 | False | False |
| seer_found_wolf_rate | seer_default | seer_highest_p_wolf | -2.52 | [-4.04, -1.00] | 0.06 | 1.00 | -2.06 | False | False |
| seer_found_wolf_rate | seer_default | seer_highest_suspicion | -3.10 | [-5.39, -0.82] | 0.06 | 1.00 | -1.68 | True | False |
| seer_found_wolf_rate | seer_default | seer_opposite_side | -3.83 | [-5.32, -2.35] | 0.06 | 1.00 | -3.20 | True | False |
| seer_found_wolf_rate | seer_random | seer_edge_first | -1.36 | [-2.35, -0.38] | 0.12 | 1.00 | -1.72 | False | False |
| seer_found_wolf_rate | seer_random | seer_inner_first | 0.46 | [-1.11, 2.03] | 0.44 | 1.00 | 0.36 | False | False |
| seer_found_wolf_rate | seer_random | seer_highest_p_wolf | 0.85 | [-0.40, 2.10] | 0.19 | 1.00 | 0.84 | False | False |
| seer_found_wolf_rate | seer_random | seer_highest_suspicion | 0.27 | [-1.39, 1.92] | 0.56 | 1.00 | 0.20 | False | False |
| seer_found_wolf_rate | seer_random | seer_opposite_side | -0.46 | [-1.56, 0.63] | 0.38 | 1.00 | -0.52 | False | False |
| seer_found_wolf_rate | seer_edge_first | seer_inner_first | 1.82 | [-0.66, 4.30] | 0.12 | 1.00 | 0.91 | False | False |
| seer_found_wolf_rate | seer_edge_first | seer_highest_p_wolf | 2.21 | [0.17, 4.25] | 0.12 | 1.00 | 1.35 | False | False |
| seer_found_wolf_rate | seer_edge_first | seer_highest_suspicion | 1.63 | [-0.94, 4.20] | 0.19 | 1.00 | 0.79 | False | False |
| seer_found_wolf_rate | seer_edge_first | seer_opposite_side | 0.90 | [-1.11, 2.91] | 0.25 | 1.00 | 0.56 | False | False |
| seer_found_wolf_rate | seer_inner_first | seer_highest_p_wolf | 0.39 | [-0.25, 1.03] | 0.25 | 1.00 | 0.76 | False | False |
| seer_found_wolf_rate | seer_inner_first | seer_highest_suspicion | -0.19 | [-1.42, 1.03] | 0.81 | 1.00 | -0.20 | False | False |
| seer_found_wolf_rate | seer_inner_first | seer_opposite_side | -0.92 | [-1.99, 0.15] | 0.12 | 1.00 | -1.07 | False | False |
| seer_found_wolf_rate | seer_highest_p_wolf | seer_highest_suspicion | -0.58 | [-2.13, 0.96] | 0.31 | 1.00 | -0.47 | False | False |
| seer_found_wolf_rate | seer_highest_p_wolf | seer_opposite_side | -1.31 | [-2.58, -0.05] | 0.12 | 1.00 | -1.29 | False | False |
| seer_found_wolf_rate | seer_highest_suspicion | seer_opposite_side | -0.73 | [-1.60, 0.14] | 0.25 | 1.00 | -1.04 | False | False |
