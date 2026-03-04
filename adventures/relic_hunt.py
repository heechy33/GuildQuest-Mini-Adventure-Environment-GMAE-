"""
Relic Hunt — competitive, first player to collect 3 relics wins.
"""

import random
from adventure import MiniAdventure

GRID_SIZE = 5
RELICS_TO_WIN = 3


class RelicHuntAdventure(MiniAdventure):
    NAME = "Relic Hunt"
    DESCRIPTION = "Competitive: first to collect 3 relics wins."

    def start(self, players: list[dict]) -> None:
        self.players = players
        self.turn = 0
        self.positions = [[0, 0], [GRID_SIZE - 1, GRID_SIZE - 1]]
        self.scores = [0, 0]
        self.relics = {
            (random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1))
            for _ in range(6)
        }
        self.done = False
        self.result = ""

    def handle_input(self, player_index: int, action: str) -> str:
        moves = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
        if action not in moves:
            return "Unknown action. Try: up, down, left, right"

        dr, dc = moves[action]
        pos = self.positions[player_index]
        pos[0] = max(0, min(GRID_SIZE - 1, pos[0] + dr))
        pos[1] = max(0, min(GRID_SIZE - 1, pos[1] + dc))

        msg = f"P{player_index + 1} moved to {pos}"
        if tuple(pos) in self.relics:
            self.relics.discard(tuple(pos))
            self.scores[player_index] += 1
            msg += " — picked up a relic!"

        if player_index == 1:
            self.turn += 1

        if self.scores[player_index] >= RELICS_TO_WIN:
            self.done = True
            self.result = f"{self.players[player_index]['name']} wins with {RELICS_TO_WIN} relics!"

        return msg

    def get_state(self) -> dict:
        return {"turn": self.turn, "positions": self.positions, "scores": self.scores}

    def is_over(self) -> bool:
        return self.done

    def get_result(self) -> str:
        return self.result


ADVENTURE_CLASS = RelicHuntAdventure