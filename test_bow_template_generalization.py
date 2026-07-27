from bow_speech_generator import template_registry_rows


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}")


def test_ood_templates_are_separable():
    rows = template_registry_rows()
    primary = {
        row["template_family"] for row in rows
        if row["template_split_group"] == "primary"
    }
    ood = {
        row["template_family"] for row in rows
        if row["template_split_group"] == "ood_template"
    }
    check(primary, "primary template families exist")
    check(ood, "OOD template families exist")
    check(primary.isdisjoint(ood), "OOD template families are held out")


def test_major_intents_have_templates():
    intents = {row["speech_intent"] for row in template_registry_rows()}
    for intent in [
        "accusation",
        "defense",
        "false_accusation",
        "false_role_claim",
        "trust_building",
        "information_report",
        "neutral_statement",
    ]:
        check(intent in intents, f"{intent} has templates")


if __name__ == "__main__":
    test_ood_templates_are_separable()
    test_major_intents_have_templates()
    print("test_bow_template_generalization.py passed")
