# roles.py

WEREWOLF = "werewolf"
VILLAGER = "villager"
SEER = "seer"
WITCH = "witch"
HUNTER = "hunter"

WOLF_TEAM = "wolf"
VILLAGE_TEAM = "village"

ALL_ROLES = [
    WEREWOLF,
    VILLAGER,
    SEER,
    WITCH,
    HUNTER,
]

ROLE_TO_TEAM = {
    WEREWOLF: WOLF_TEAM,
    VILLAGER: VILLAGE_TEAM,
    SEER: VILLAGE_TEAM,
    WITCH: VILLAGE_TEAM,
    HUNTER: VILLAGE_TEAM,
}


def get_team(role: str) -> str:
    """
    Return the team for a given role.
    """
    if role not in ROLE_TO_TEAM:
        raise ValueError(f"Unknown role: {role}")

    return ROLE_TO_TEAM[role]


def is_valid_role(role: str) -> bool:
    """
    Check whether a role is supported by the simulation.
    """
    return role in ALL_ROLES


if __name__ == "__main__":
    for role in ALL_ROLES:
        print(role, "->", get_team(role))

    print("Is seer valid?", is_valid_role(SEER))
    print("Is dragon valid?", is_valid_role("dragon"))