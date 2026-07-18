# game_state.py

from typing import List, Optional

from player import Player
from roles import WOLF_TEAM, VILLAGE_TEAM


class GameState:
    """
    Stores and updates the global state of a Werewolf game.

    This class does not decide player actions.
    It only tracks round number, phase, alive players, and win conditions.
    """

    def __init__(self, players: List[Player]):
        if not players:
            raise ValueError("GameState requires at least one player.")

        self.players = players
        self.round_number = 1
        self.phase = "night"
        self.game_over = False
        self.winner: Optional[str] = None

    def get_alive_players(self) -> List[Player]:
        """
        Return all alive players.
        """
        return [player for player in self.players if player.alive]

    def get_dead_players(self) -> List[Player]:
        """
        Return all dead players.
        """
        return [player for player in self.players if not player.alive]

    def get_alive_wolves(self) -> List[Player]:
        """
        Return alive werewolf-team players.
        """
        return [
            player for player in self.players
            if player.alive and player.team == WOLF_TEAM
        ]

    def get_alive_villagers(self) -> List[Player]:
        """
        Return alive village-team players.
        """
        return [
            player for player in self.players
            if player.alive and player.team == VILLAGE_TEAM
        ]

    def count_alive_players(self) -> int:
        return len(self.get_alive_players())

    def count_alive_wolves(self) -> int:
        return len(self.get_alive_wolves())

    def count_alive_villagers(self) -> int:
        return len(self.get_alive_villagers())

    def get_player_by_id(self, player_id: int) -> Player:
        """
        Find a player by ID.
        """
        for player in self.players:
            if player.player_id == player_id:
                return player

        raise ValueError(f"No player found with id: {player_id}")

    def kill_player(self, player_id: int) -> None:

      if self.game_over:
        raise ValueError("Cannot kill player because the game is already over.")

      player = self.get_player_by_id(player_id)

      if not player.alive:
        raise ValueError(f"Player {player_id} is already dead.")

      player.kill()
      self.check_win_condition()
     

    def switch_phase(self) -> None:
        """
        Switch between night and day.

        night -> day
        day -> night, and round number increases
        """
        if self.phase == "night":
            self.phase = "day"
        elif self.phase == "day":
            self.phase = "night"
            self.round_number += 1
        else:
            raise ValueError(f"Invalid phase: {self.phase}")

    def check_win_condition(self) -> bool:
        """
        Check whether the game has ended.

        Village wins if all wolves are dead.
        Wolves win if number of wolves is greater than or equal to
        number of alive village-team players.
        """
        alive_wolves = self.count_alive_wolves()
        alive_villagers = self.count_alive_villagers()

        if alive_wolves == 0:
            self.game_over = True
            self.winner = VILLAGE_TEAM
            return True

        if alive_wolves >= alive_villagers:
            self.game_over = True
            self.winner = WOLF_TEAM
            return True

        self.game_over = False
        self.winner = None
        return False

    def reset_turn_actions(self) -> None:
        """
        Reset temporary actions for all players.
        """
        for player in self.players:
            player.reset_turn_actions()

    def summary(self) -> dict:
        """
        Return a compact summary of the current game state.
        """
        return {
            "round_number": self.round_number,
            "phase": self.phase,
            "game_over": self.game_over,
            "winner": self.winner,
            "alive_players": [p.player_id for p in self.get_alive_players()],
            "dead_players": [p.player_id for p in self.get_dead_players()],
            "alive_wolves": [p.player_id for p in self.get_alive_wolves()],
            "alive_villagers": [p.player_id for p in self.get_alive_villagers()],
            "num_alive_players": self.count_alive_players(),
            "num_alive_wolves": self.count_alive_wolves(),
            "num_alive_villagers": self.count_alive_villagers(),
        }


if __name__ == "__main__":
    players = [
        Player(player_id=1, role="werewolf"),
        Player(player_id=2, role="werewolf"),
        Player(player_id=3, role="villager"),
        Player(player_id=4, role="villager"),
        Player(player_id=5, role="seer"),
        Player(player_id=6, role="witch"),
    ]

    game_state = GameState(players)

    print("Initial game state:")
    print(game_state.summary())

    print("\nSwitch phase:")
    game_state.switch_phase()
    print(game_state.summary())

    print("\nKill player 3:")
    game_state.kill_player(3)
    print(game_state.summary())

    print("\nKill player 4:")
    game_state.kill_player(4)
    print(game_state.summary())

    print("\nTry to kill player 5 after game over:")
    try:
        game_state.kill_player(5)
    except ValueError as e:
        print(e)

    print(game_state.summary())