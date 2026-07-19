# player.py

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from roles import get_team, is_valid_role


@dataclass
class Player:
    """
    A player agent in the Werewolf simulation.

    This class stores player-level state.
    Decision logic such as voting, night actions, and speech generation
    should be handled by Game, Strategy, or Language modules later.
    """

    player_id: int
    role: str

    alive: bool = True
    suspicion_score: float = 0.0
    p_wolf: float = 0.0
    risk_preference: str = "neutral"
    side: Optional[str] = None
    seat_type: Optional[str] = None
    has_antidote: bool = True
    has_poison: bool = True
    has_given_last_words: bool = False

    vote_target: Optional[int] = None
    night_target: Optional[int] = None

    memory: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        if not is_valid_role(self.role):
            raise ValueError(f"Invalid role: {self.role}")

        self.team = get_team(self.role)

    def is_wolf(self) -> bool:
        return self.team == "wolf"

    def is_villager_team(self) -> bool:
        return self.team == "village"

    def kill(self) -> None:
        """
        Mark the player as dead.
        """
        self.alive = False
        self.vote_target = None
        self.night_target = None

    def reset_turn_actions(self) -> None:
        """
        Clear temporary actions after each day/night phase.
        """
        self.vote_target = None
        self.night_target = None

    def update_suspicion(self, delta: float) -> None:
        """
        Update suspicion score.

        Suspicion score is clipped to [0.0, 1.0].
        """
        self.suspicion_score += delta
        self.suspicion_score = max(0.0, min(1.0, self.suspicion_score))

    def update_p_wolf(self, delta: float) -> None:
        """
        Update perceived probability of being a wolf.

        p_wolf is clipped to [0.0, 1.0].
        """
        self.p_wolf += delta
        self.p_wolf = max(0.0, min(1.0, self.p_wolf))

    def add_memory(self, event_type: str, content: Dict[str, Any]) -> None:
        """
        Store an observed event.
        """
        self.memory.append({
            "event_type": event_type,
            "content": content
        })

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert player state to dictionary for logging or debugging.
        """
        return {
            "player_id": self.player_id,
            "role": self.role,
            "team": self.team,
            "alive": self.alive,
            "suspicion_score": self.suspicion_score,
            "p_wolf": self.p_wolf,
            "risk_preference": self.risk_preference,
            "side": self.side,
            "seat_type": self.seat_type,
            "has_antidote": self.has_antidote,
            "has_poison": self.has_poison,
            "has_given_last_words": self.has_given_last_words,
            "vote_target": self.vote_target,
            "night_target": self.night_target,
            "memory": self.memory,
        }


if __name__ == "__main__":
    p1 = Player(player_id=1, role="werewolf")
    p2 = Player(player_id=2, role="seer")

    print("Initial players:")
    print(p1.to_dict())
    print(p2.to_dict())

    p2.update_suspicion(0.3)
    p2.update_p_wolf(0.2)
    p2.add_memory("vote", {"voter": 1, "target": 2, "round": 1})

    print("\nAfter updates:")
    print(p2.to_dict())

    p2.kill()

    print("\nAfter death:")
    print(p2.to_dict())

    print("\nTesting invalid role:")
    try:
        p3 = Player(player_id=3, role="dragon")
    except ValueError as e:
        print(e)
