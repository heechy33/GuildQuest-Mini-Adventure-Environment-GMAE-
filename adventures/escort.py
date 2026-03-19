"""
Escort Adventure — co-op, guide an NPC to the goal before time runs out.
"""

import sys
import os
import random

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_root, 'geoffreys_gmae_code'))
sys.path.insert(0, os.path.join(_root, 'heechans_gmae_code'))

from geoffreys_gmae import (Realm, FixedOffsetStrategy, WorldClock,
                             InventoryItem)
from heechans_gmae import (Rarity, ItemType, EventDispatcher, UserNotifier,
                            BothClocksStrategy)
from heechans_gmae import Realm as HRealm
from adventure import MiniAdventure

GRID_SIZE = 5
MAX_TURNS = 20
TURN_MINUTES = 30
START_DAY, START_HOUR = 1, 8
REALM_OFFSET = 3


class EscortAdventure(MiniAdventure):
    NAME = "Escort"
    DESCRIPTION = "Co-op: guide the NPC to safety before turns run out."

    def start(self, players: list[dict]) -> None:
        self.players = players
        self.turn = 0
        self.extra_turns = 0
        self.player_pos = [[0, 2], [4, 2]]
        self.npc_pos = [2, 2]
        self.goal = [GRID_SIZE - 1, GRID_SIZE - 1]
        self.done = False
        self.winner_index = None
        self.collected_items = [[], []]

        self.g_realm = Realm("Ashfields", "A realm of ash and fire")
        self.g_realm.time_rule = FixedOffsetStrategy(REALM_OFFSET)
        self.h_realm = HRealm("Ashfields", "A realm of ash and fire", 1, REALM_OFFSET)
        self.clock = WorldClock(START_DAY, START_HOUR, 0)
        self.display_strategy = BothClocksStrategy()

        self.dispatcher = EventDispatcher()
        self.notifiers = [UserNotifier(p["name"]) for p in players]
        for notifier in self.notifiers:
            for event_type in ("npc_move", "hazard", "item_pickup"):
                self.dispatcher.subscribe(event_type, notifier)

        # Place hazards and items avoiding start positions, goal, and NPC
        occupied = {(0, 2), (4, 2), (2, 2), (GRID_SIZE - 1, GRID_SIZE - 1)}
        self.hazards: set[tuple] = set()
        num_hazards = random.randint(2, 3)
        while len(self.hazards) < num_hazards:
            pos = (random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1))
            if pos not in occupied and pos not in self.hazards:
                self.hazards.add(pos)

        self.items: dict[tuple, dict] = {}
        num_items = random.randint(1, 2)
        item_defs = [
            {"name": "Torch", "rarity": Rarity.COMMON, "item_type": ItemType.CONSUMABLE, "turns_bonus": 2},
            {"name": "Shield", "rarity": Rarity.RARE, "item_type": ItemType.ARMOR, "turns_bonus": 3},
        ]
        all_occupied = occupied | self.hazards
        for item_def in item_defs[:num_items]:
            attempts = 0
            while attempts < 50:
                pos = (random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1))
                if pos not in all_occupied and pos not in self.items:
                    self.items[pos] = item_def
                    break
                attempts += 1

    def _adjacent_or_same(self, player_pos: list, npc_pos: list) -> bool:
        return (abs(player_pos[0] - npc_pos[0]) <= 1 and
                abs(player_pos[1] - npc_pos[1]) <= 1)

    def _advance_clock(self) -> None:
        self.clock = WorldClock.from_minutes(self.clock.to_minutes() + TURN_MINUTES)

    def handle_input(self, player_index: int, action: str) -> str:
        moves = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
        if action not in moves:
            return "Unknown action. Try: up, down, left, right"

        dr, dc = moves[action]
        pos = self.player_pos[player_index]
        pos[0] = max(0, min(GRID_SIZE - 1, pos[0] + dr))
        pos[1] = max(0, min(GRID_SIZE - 1, pos[1] + dc))

        msg_parts = [f"P{player_index + 1} moved to {pos}"]

        # Check item pickup
        pos_tuple = tuple(pos)
        if pos_tuple in self.items:
            item_def = self.items.pop(pos_tuple)
            self.extra_turns += item_def["turns_bonus"]
            inv_item = InventoryItem(item_def["name"], item_def["rarity"].value, item_def["item_type"].value)
            self.collected_items[player_index].append(inv_item)
            self.dispatcher.notify("item_pickup",
                f"{self.players[player_index]['name']} picked up {item_def['name']} (+{item_def['turns_bonus']} turns)")
            msg_parts.append(f"picked up {item_def['name']}!")

        # If adjacent to NPC, push NPC in same direction
        if self._adjacent_or_same(pos, self.npc_pos):
            self.npc_pos[0] = max(0, min(GRID_SIZE - 1, self.npc_pos[0] + dr))
            self.npc_pos[1] = max(0, min(GRID_SIZE - 1, self.npc_pos[1] + dc))
            self.dispatcher.notify("npc_move",
                f"NPC pushed to {self.npc_pos}")
            msg_parts.append(f"NPC pushed to {self.npc_pos}")

            npc_tuple = tuple(self.npc_pos)
            if npc_tuple in self.hazards:
                self.extra_turns -= 2
                self.dispatcher.notify("hazard",
                    f"NPC hit a hazard at {self.npc_pos}! -2 turns")
                msg_parts.append("NPC hit a hazard! (-2 turns)")

            if self.npc_pos == self.goal:
                self.done = True
                self.winner_index = None
                msg_parts.append("NPC reached the goal — co-op victory!")

        if player_index == 1:
            self.turn += 1
            self._advance_clock()

        effective_max = MAX_TURNS + self.extra_turns
        if not self.done and self.turn >= effective_max:
            self.done = True
            self.winner_index = -1
            msg_parts.append("Time's up!")

        return " | ".join(msg_parts)

    def _render_grid(self) -> str:
        p1 = tuple(self.player_pos[0])
        p2 = tuple(self.player_pos[1])
        npc = tuple(self.npc_pos)
        goal = tuple(self.goal)

        sep = "─" * (GRID_SIZE * 4 + 1)
        lines = [sep]
        for r in range(GRID_SIZE):
            row = "|"
            for c in range(GRID_SIZE):
                cell = (r, c)
                if cell == p1 and cell == p2:
                    sym = "!!"
                elif cell == p1:
                    sym = "P1"
                elif cell == p2:
                    sym = "P2"
                elif cell == npc:
                    sym = "N "
                elif cell == goal:
                    sym = "G "
                elif cell in self.hazards:
                    sym = "H "
                elif cell in self.items:
                    sym = "I "
                else:
                    sym = ". "
                row += f" {sym}|"
            lines.append(row)
            lines.append(sep)
        return "\n".join(lines)

    def get_state(self) -> dict:
        effective_max = MAX_TURNS + self.extra_turns
        time_str = self.display_strategy.format_time(self.clock, self.h_realm)
        grid = self._render_grid()

        notif_lines = []
        for notifier in self.notifiers:
            recent = notifier.notifications[-3:]
            if recent:
                notif_lines.append(f"  {notifier.username}: " + " | ".join(recent))

        lines = [
            grid,
            f"Time: {time_str}",
            f"Turns remaining: {effective_max - self.turn}",
            f"NPC: {self.npc_pos}  Goal: {self.goal}",
            f"P1: {self.player_pos[0]}  P2: {self.player_pos[1]}",
        ]
        if notif_lines:
            lines.append("Notifications:")
            lines.extend(notif_lines)

        return {"display": "\n".join(lines)}

    def is_over(self) -> bool:
        return self.done

    def get_result(self) -> str:
        if self.winner_index is None:
            return "NPC reached safety — co-op victory!"
        return "Time's up — the NPC never reached safety. You lose."


ADVENTURE_CLASS = EscortAdventure
