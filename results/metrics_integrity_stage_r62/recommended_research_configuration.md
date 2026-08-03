# Recommended Research Configuration

This configuration is explicit opt-in only. It preserves historical defaults and activates trust-weighted structured Villager voting while leaving Seer immediate reveal and Witch aggressive_full as experimental candidates.

Configuration hash: `0d5e284c625dd63181c6ee852e565a10506271cba3b3684da3b612c634d2e537`

| Component | Recommendation | Grade | Confidence |
|---|---|---|---|
| villager_voting_policy | trust_weighted_structured | A | high within tested strategy space |
| seer_checking_policy | random_or_diversified_reference | B | moderate |
| seer_reveal_policy | private_reference | B | moderate for current reference |
| witch_joint_policy | reference | B | low to moderate |
| hunter_policy | reference | B | moderate |
| werewolf_night_kill_policy | threat_based | B | moderate |
| werewolf_deception_policy | adaptive_with_credibility_costs | B | moderate |
| speech_policy | structured_speech_enabled | B | moderate |
| herding_policy | guarded_configurable | C | low to moderate |
| bow_mode | shadow_diagnostics_only | E for live deployment | high rejection for live override |
| ml_mode | diagnostic_only | E for deployment | moderate |
