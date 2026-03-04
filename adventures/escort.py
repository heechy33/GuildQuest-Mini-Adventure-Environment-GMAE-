"""
Escort Adventure — co-op, guide an NPC to the goal before time runs out.
"""

from adventure import MiniAdventure

GRID_SIZE = 5
MAX_TURNS = 15


class EscortAdventure(MiniAdventure):
    NAME = "Escort"
    DESCRIPTION = "Co-op: guide the NPC to safety before turns run out."

    def start(self, players: list[dict]) -> None:
        self.players = players
        self.turn = 0
        self.npc_pos = [0, 0]
        self.goal = [GRID_SIZE - 1, GRID_SIZE - 1]
        self.done = False
        self.result = ""

    def handle_input(self, player_index: int, action: str) -> str:
        moves = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
        if action not in moves:
            return "Unknown action. Try: up, down, left, right"

        dr, dc = moves[action]
        self.npc_pos[0] = max(0, min(GRID_SIZE - 1, self.npc_pos[0] + dr))
        self.npc_pos[1] = max(0, min(GRID_SIZE - 1, self.npc_pos[1] + dc))

        if player_index == 1:
            self.turn += 1

        if self.npc_pos == self.goal:
            self.done = True
            self.result = "NPC reached safety — you win!"
        elif self.turn >= MAX_TURNS:
            self.done = True
            self.result = "Time's up — you lose."

        return f"NPC moved to {self.npc_pos}"

    def get_state(self) -> dict:
        return {"turn": self.turn, "npc": self.npc_pos, "goal": self.goal}

    def is_over(self) -> bool:
        return self.done

    def get_result(self) -> str:
        return self.result


ADVENTURE_CLASS = EscortAdventure