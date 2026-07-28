"""Distribution-shift summaries for R3 live BoW policies."""

from collections import defaultdict


def summarize_distribution_shift(game_rows, belief_rows, vote_rows):
    by_key = defaultdict(lambda: {
        "speech_events": 0,
        "bow_updates": 0,
        "vote_decisions": 0,
        "vote_disagreements": 0,
        "strong_template_shift_events": 0,
        "belief_divergence_sum": 0.0,
        "vote_divergence_sum": 0.0,
    })

    game_lookup = {row["game_uid"]: row for row in game_rows}

    for row in belief_rows:
        game = game_lookup.get(row["game_uid"], {})
        key = (
            row["policy_name"],
            game.get("template_condition", row.get("template_condition", "")),
            game.get("behavioral_regime", row.get("behavioral_regime", "")),
            row["round"],
        )
        target = by_key[key]
        target["speech_events"] += 1
        target["bow_updates"] += 1
        if row.get("ood_category") == "strong_template_shift":
            target["strong_template_shift_events"] += 1
        target["belief_divergence_sum"] += abs(float(row.get(
            "p_wolf_delta",
            0.0,
        )))

    for row in vote_rows:
        game = game_lookup.get(row["game_uid"], {})
        key = (
            row["policy_name"],
            game.get("template_condition", row.get("template_condition", "")),
            game.get("behavioral_regime", row.get("behavioral_regime", "")),
            row["round"],
        )
        target = by_key[key]
        target["vote_decisions"] += 1
        if row.get("disagrees_with_existing") == "True":
            target["vote_disagreements"] += 1
            target["vote_divergence_sum"] += 1.0

    rows = []
    for key, values in sorted(by_key.items()):
        policy_name, template_condition, behavioral_regime, round_number = key
        vote_decisions = values["vote_decisions"]
        bow_updates = values["bow_updates"]
        rows.append({
            "policy_name": policy_name,
            "template_condition": template_condition,
            "behavioral_regime": behavioral_regime,
            "round": round_number,
            "speech_events": values["speech_events"],
            "cumulative_bow_updates": bow_updates,
            "vote_decisions": vote_decisions,
            "vote_disagreements": values["vote_disagreements"],
            "strong_template_shift_events": (
                values["strong_template_shift_events"]
            ),
            "mean_belief_divergence": (
                values["belief_divergence_sum"] / bow_updates
                if bow_updates else 0.0
            ),
            "vote_divergence_rate": (
                values["vote_divergence_sum"] / vote_decisions
                if vote_decisions else 0.0
            ),
        })
    return rows


def summarize_repeated_use(belief_rows, vote_rows):
    by_game = defaultdict(lambda: {
        "bow_updates": 0,
        "vote_overrides": 0,
        "strong_template_shift_events": 0,
    })
    for row in belief_rows:
        item = by_game[row["game_uid"]]
        item["bow_updates"] += 1
        if row.get("ood_category") == "strong_template_shift":
            item["strong_template_shift_events"] += 1
    for row in vote_rows:
        if row.get("disagrees_with_existing") == "True":
            by_game[row["game_uid"]]["vote_overrides"] += 1

    return [
        {
            "game_uid": game_uid,
            **values,
            "repeated_use_level": (
                "high" if values["bow_updates"] >= 20 else "low"
            ),
        }
        for game_uid, values in sorted(by_game.items())
    ]


if __name__ == "__main__":
    print(summarize_distribution_shift([], [], []))
