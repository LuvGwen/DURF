"""Shadow recommendation extraction for R3 BoW vote policies."""


def shadow_rows_from_vote_event(base_row, event_content):
    recommendations = event_content.get("shadow_recommendations", {})
    existing_target = event_content.get("existing_target")
    selected_target = event_content.get("selected_target")
    row = {
        **base_row,
        "existing_target": existing_target,
        "selected_target": selected_target,
    }
    for policy_name, recommendation in sorted(recommendations.items()):
        target = recommendation.get("target")
        prefix = f"shadow_{policy_name}"
        row[f"{prefix}_target"] = target
        row[f"{prefix}_score"] = recommendation.get("score", 0.0)
        row[f"{prefix}_disagrees_with_existing"] = target != existing_target
        row[f"{prefix}_matches_selected"] = target == selected_target
    return [row]


def vote_decision_is_pivotal(votes, voter_id, existing_target, selected_target):
    if existing_target == selected_target:
        return False

    existing_votes = dict(votes)
    selected_votes = dict(votes)
    existing_votes[voter_id] = existing_target
    selected_votes[voter_id] = selected_target
    return eliminated_from_votes(existing_votes) != eliminated_from_votes(
        selected_votes,
    )


def eliminated_from_votes(votes):
    counts = {}
    for target in votes.values():
        counts[target] = counts.get(target, 0) + 1
    if not counts:
        return None
    highest = max(counts.values())
    tied = [target for target, count in counts.items() if count == highest]
    return sorted(tied)[0]


if __name__ == "__main__":
    print(eliminated_from_votes({1: 2, 2: 3, 3: 2}))
