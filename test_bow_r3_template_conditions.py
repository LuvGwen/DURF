from bow_r3_template_conditions import (
    R3_BEHAVIORAL_REGIMES,
    R3_TEMPLATE_CONDITIONS,
    render_r3_live_utterance,
)
from game import Game


if __name__ == "__main__":
    game = Game(enable_bow_r3=False)
    speech = {"speaker": 1, "speech_type": "accuse", "target": 2}
    seen = render_r3_live_utterance(
        game.state,
        speech,
        template_condition="in_distribution_templates",
    )
    unseen = render_r3_live_utterance(
        game.state,
        speech,
        template_condition="unseen_template_families",
    )
    paraphrased = render_r3_live_utterance(
        game.state,
        speech,
        template_condition="paraphrased_template_families",
    )
    assert seen["ood_category"] == "in_distribution"
    print("PASS: in-distribution template category")
    assert unseen["ood_category"] in {"strong_template_shift", "mild_template_shift"}
    print("PASS: unseen template category")
    assert paraphrased["utterance_text"] != seen["utterance_text"]
    print("PASS: paraphrased text differs from primary template")
    assert len(R3_TEMPLATE_CONDITIONS) == 3
    print("PASS: three template conditions registered")
    assert len(R3_BEHAVIORAL_REGIMES) >= 10
    print("PASS: at least ten behavioral regimes registered")
    print("test_bow_r3_template_conditions.py passed")
