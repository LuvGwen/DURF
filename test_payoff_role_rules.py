from payoff_ledger import PayoffLedger
from payoff_manifest import build_manifest
from player import Player
from roles import VILLAGER, WEREWOLF


if __name__ == "__main__":
    manifest = build_manifest(source_commit="test")
    ledger = PayoffLedger(manifest, "role_rules")
    villager = Player(1, VILLAGER)
    wolf = Player(2, WEREWOLF)
    try:
        ledger.add(
            "wolf_team_win",
            villager,
            1,
            "terminal",
            "bad_source",
            "villager cannot receive wolf-only reward",
        )
        raise AssertionError("Expected invalid role reward to fail")
    except ValueError:
        pass
    try:
        ledger.add(
            "seer_investigation_used",
            wolf,
            1,
            "night",
            "bad_source_2",
            "wolf cannot receive seer-only reward",
        )
        raise AssertionError("Expected invalid seer reward to fail")
    except ValueError:
        pass
    print("test_payoff_role_rules.py passed")
