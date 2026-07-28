from payoff_ledger import PayoffLedger
from payoff_manifest import build_manifest
from player import Player
from roles import VILLAGER


if __name__ == "__main__":
    manifest = build_manifest(source_commit="test")
    ledger = PayoffLedger(manifest, "game")
    actor = Player(1, VILLAGER)
    target = Player(2, "werewolf")
    ledger.add(
        "correct_vote_for_wolf",
        actor,
        1,
        "day",
        "source1",
        "test vote",
        target=target,
    )
    assert ledger.validate_unique_ids()
    assert ledger.duplicate_component_sources() == {}
    assert abs(ledger.totals_by_player()[1] - 0.05) < 1e-9
    print("test_payoff_ledger.py passed")
