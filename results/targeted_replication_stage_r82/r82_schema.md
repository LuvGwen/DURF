# R8.2 Dataset Schema

## Game-Level Raw Dataset

`r82_game_level_raw.csv` contains one complete-game row per module, policy arm,
and matched set. The core fields are inherited from the R6.1 game-level schema:
module, policy, matched_set_id, seed, behavioral_regime, game_seed, game_id,
winner, village_win, wolf_win, actor_role, actor_payoff, team_payoff, role action
counts, vote diagnostics, seer search diagnostics, and seat_assignment_signature.

## Action Raw Dataset

`r82_action_raw.csv.gz` contains gzip-compressed diagnostic event rows for the
active module only. Action rows are not independent statistical units;
complete-game rows are the independent matched units. The compressed artifact
can be restored with `gzip -dk r82_action_raw.csv.gz` if an uncompressed CSV is
needed locally.

## Primary Contrasts

`r82_primary_contrasts.csv` contains the preregistered primary actor-payoff
contrast and secondary village-win contrast for each frozen module. Holm
correction is applied across the three primary actor-payoff contrasts and
separately across the three secondary village-win contrasts.
