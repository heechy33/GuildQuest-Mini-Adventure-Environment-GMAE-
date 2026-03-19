"""
Relic Hunt — competitive, first player to reach 3.0 score wins.
Relics have different rarities with different point values.
"""

import sys
import os
import random

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_root, 'geoffreys_gmae_code'))
sys.path.insert(0, os.path.join(_root, 'heechans_gmae_code'))

from geoffreys_gmae import (Realm, FixedOffsetStrategy, WorldClock,
                             InventoryItem)
from heechans_gmae import (Rarity, EventDispatcher, UserNotifier,
                            WorldClockStrategy)
from adventure import MiniAdventure

GRID_SIZE = 5
RELICS_TO_WIN = 3.0
NUM_RELICS = 8
ROUND_MINUTES = 20
START_DAY, START_HOUR, START_MINUTE = 1, 6, 0
REALM_OFFSET = 2
RARITY_WEIGHTS = {
    Rarity.COMMON: 1.0,
    Rarity.RARE: 1.5,
    Rarity.EPIC: 2.0,
    Rarity.LEGENDARY: 2.0,
}


class RelicHuntAdventure(MiniAdventure):
    NAME = "Relic Hunt"
    DESCRIPTION = "Competitive: first to reach 3.0 relic score wins."

    def start(self, players: list[dict]) -> None:
        self.players = players
        self.turn = 0
        self.positions = [[0, 0], [GRID_SIZE - 1, GRID_SIZE - 1]]
        self.scores = [0.0, 0.0]
        self.done = False
        self.winner_index = None
        self.collected_items: list[list[InventoryItem]] = [[], []]

        self.realm = Realm("Elvenwood", "Ancient forest")
        self.realm.time_rule = FixedOffsetStrategy(REALM_OFFSET)
        self.clock = WorldClock(START_DAY, START_HOUR, START_MINUTE)
        self.display_strategy = WorldClockStrategy()

        self.dispatcher = EventDispatcher()
        self.notifiers = [UserNotifier(p["name"]) for p in players]
        for notifier in self.notifiers:
            self.dispatcher.subscribe("relic_pickup", notifier)

        start_pos = {(0, 0), (GRID_SIZE - 1, GRID_SIZE - 1)}
        relics: dict[tuple, Rarity] = {}
        while len(relics) < NUM_RELICS:
            pos = (random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1))
            if pos not in start_pos and pos not in relics:
                relics[pos] = random.choice(list(Rarity))
        self.relics = relics

    def handle_input(self, player_index: int, action: str) -> str:
        moves = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
        if action not in moves:
            return "Unknown action. Try: up, down, left, right"

        dr, dc = moves[action]
        pos = self.positions[player_index]
        pos[0] = max(0, min(GRID_SIZE - 1, pos[0] + dr))
        pos[1] = max(0, min(GRID_SIZE - 1, pos[1] + dc))

        msg_parts = [f"P{player_index + 1} moved to {pos}"]

        pos_tuple = tuple(pos)
        if pos_tuple in self.relics:
            rarity = self.relics.pop(pos_tuple)
            weight = RARITY_WEIGHTS[rarity]
            self.scores[player_index] += weight
            inv_item = InventoryItem(f"Relic ({rarity.value})", rarity.value, "Relic")
            self.collected_items[player_index].append(inv_item)
            self.dispatcher.notify("relic_pickup",
                f"{self.players[player_index]['name']} found a {rarity.value} relic (+{weight})")
            msg_parts.append(f"found a {rarity.value} relic! (+{weight:.1f}, total: {self.scores[player_index]:.1f})")

        if player_index == 1:
            self.turn += 1
            self.clock = WorldClock.from_minutes(self.clock.to_minutes() + ROUND_MINUTES)

        if self.scores[player_index] >= RELICS_TO_WIN:
            self.done = True
            self.winner_index = player_index

        return " | ".join(msg_parts)

    def _render_grid(self) -> str:
        p1 = tuple(self.positions[0])
        p2 = tuple(self.positions[1])

        sep = "─" * (GRID_SIZE * 4 + 1)
        lines = [sep]
        for r in range(GRID_SIZE):
            row = "|"
            for c in range(GRID_SIZE):
                cell = (r, c)
                if cell == p1 and cell == p2:
                    sym = "! "
                elif cell == p1:
                    sym = "1 "
                elif cell == p2:
                    sym = "2 "
                elif cell in self.relics:
                    sym = "R "
                else:
                    sym = ". "
                row += f" {sym}|"
            lines.append(row)
            lines.append(sep)
        return "\n".join(lines)

    def get_state(self) -> dict:
        time_str = self.display_strategy.format_time(self.clock)
        grid = self._render_grid()

        notif_lines = []
        for notifier in self.notifiers:
            recent = notifier.notifications[-3:]
            if recent:
                notif_lines.append(f"  {notifier.username}: " + " | ".join(recent))

        lines = [
            grid,
            f"Time: {time_str}",
            f"Scores — P1: {self.scores[0]:.1f}  P2: {self.scores[1]:.1f}  (need {RELICS_TO_WIN:.1f} to win)",
            f"Relics remaining: {len(self.relics)}",
        ]
        if notif_lines:
            lines.append("Notifications:")
            lines.extend(notif_lines)

        return {"display": "\n".join(lines)}

    def is_over(self) -> bool:
        return self.done

    def get_result(self) -> str:
        if self.winner_index is not None:
            name = self.players[self.winner_index]["name"]
            score = self.scores[self.winner_index]
            return f"{name} wins with {score:.1f} relic score!"
        return "The relic hunt ended without a winner."


ADVENTURE_CLASS = RelicHuntAdventure
