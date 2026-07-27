from bow_feature_extractor import extract_bow_features, score_definition_manifest


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}")


def test_scores_are_in_range():
    features = extract_bow_features(
        "I suspect PLAYER_TARGET because the vote history is suspicious!"
    )
    for key in [
        "bow_werewolf_leaning_score",
        "bow_emotional_intensity_score",
        "bow_information_density_score",
    ]:
        check(0.0 <= features[key] <= 1.0, f"{key} is clipped to [0, 1]")


def test_empty_utterance_is_handled():
    features = extract_bow_features("")
    check(features["token_count"] == 0, "empty utterance token count is zero")
    check(
        0.0 <= features["bow_information_density_score"] <= 1.0,
        "empty utterance score is valid",
    )


def test_manifest_has_formulas():
    manifest = score_definition_manifest()
    check(
        "bow_werewolf_leaning_score" in manifest["formulas"],
        "score manifest includes werewolf formula",
    )
    check(
        "bow_emotional_intensity_score" in manifest["formulas"],
        "score manifest includes emotional formula",
    )
    check(
        "bow_information_density_score" in manifest["formulas"],
        "score manifest includes information formula",
    )


if __name__ == "__main__":
    test_scores_are_in_range()
    test_empty_utterance_is_handled()
    test_manifest_has_formulas()
    print("test_bow_feature_extractor.py passed")
