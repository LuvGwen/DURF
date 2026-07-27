from bow_lexicon import CORE_LEXICON_COLUMNS, get_core_lexicon_rows


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}")


def test_core_lexicon_size_and_columns():
    rows = get_core_lexicon_rows()
    check(50 <= len(rows) <= 100, "core lexicon has 50-100 terms")
    check(
        set(CORE_LEXICON_COLUMNS).issubset(rows[0]),
        "core lexicon rows contain required columns",
    )


def test_core_lexicon_tokens_are_unique():
    rows = get_core_lexicon_rows()
    tokens = [row["token"] for row in rows]
    check(len(tokens) == len(set(tokens)), "core lexicon tokens are unique")


def test_weights_are_numeric():
    for row in get_core_lexicon_rows():
        float(row["intensity_weight"])
        float(row["information_weight"])
        float(row["werewolf_leaning_weight"])
    check(True, "lexicon weights are numeric")


if __name__ == "__main__":
    test_core_lexicon_size_and_columns()
    test_core_lexicon_tokens_are_unique()
    test_weights_are_numeric()
    print("test_bow_lexicon.py passed")
