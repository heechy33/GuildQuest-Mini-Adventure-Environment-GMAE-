"""
Engine — loads adventures, manages profiles, runs the game loop.

Reused subsystems:
  - Geoffrey's: Character, InventoryItem, WorldClock (geoffreys_gmae_code/)
"""

import importlib
import pkgutil
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'geoffreys_gmae_code'))

from geoffreys_gmae import Character, InventoryItem
from adventure import MiniAdventure

PROFILES_FILE = "profiles.json"

_characters: dict[str, Character] = {}


def load_profiles() -> dict:
    if os.path.exists(PROFILES_FILE):
        with open(PROFILES_FILE) as f:
            return json.load(f)
    return {}


def save_profiles(profiles: dict) -> None:
    with open(PROFILES_FILE, "w") as f:
        json.dump(profiles, f, indent=2)


def get_or_create_profile(name: str, profiles: dict) -> dict:
    if name not in profiles:
        print("\n  [New player! Set up your GuildQuest character]")
        character_name = input("    Character name: ").strip() or name
        character_class = input("    Class (default: Adventurer): ").strip() or "Adventurer"
        preferred_realm = input("    Preferred realm (default: Elvenwood): ").strip() or "Elvenwood"
        profiles[name] = {
            "name": name,
            "wins": 0,
            "losses": 0,
            "character_name": character_name,
            "character_class": character_class,
            "character_level": 1,
            "preferred_realm": preferred_realm,
            "inventory": [],
            "quest_history": [],
        }
        save_profiles(profiles)
    return profiles[name]


def get_character(profile: dict) -> Character:
    name = profile["name"]
    if name not in _characters:
        char = Character(
            profile["character_name"],
            profile["character_class"],
            profile["character_level"],
        )
        for item_name in profile.get("inventory", []):
            char.add_item(InventoryItem(item_name, "Common", "Item"))
        _characters[name] = char
    return _characters[name]


def discover_adventures() -> list[type[MiniAdventure]]:
    import adventures
    found = []
    for _, mod_name, _ in pkgutil.iter_modules(adventures.__path__):
        mod = importlib.import_module(f"adventures.{mod_name}")
        cls = getattr(mod, "ADVENTURE_CLASS", None)
        if cls:
            found.append(cls)
    return found


def update_stats(profiles: dict, players: list[dict], adventure) -> None:
    winner_index = getattr(adventure, 'winner_index', None)
    for i, p in enumerate(players):
        name = p["name"]
        if winner_index is None:
            profiles[name]["wins"] += 1
        elif winner_index == -1:
            profiles[name]["losses"] += 1
        elif winner_index == i:
            profiles[name]["wins"] += 1
        else:
            profiles[name]["losses"] += 1
    save_profiles(profiles)


class Engine:
    def run(self):
        profiles = load_profiles()

        print("\n=== GuildQuest Mini-Adventure Environment ===\n")
        p1_name = input("Player 1 name: ").strip() or "Player1"
        p2_name = input("Player 2 name: ").strip() or "Player2"
        players = [
            get_or_create_profile(p1_name, profiles),
            get_or_create_profile(p2_name, profiles),
        ]

        adventure_classes = discover_adventures()
        if not adventure_classes:
            print("No adventures found in adventures/")
            return

        print("\nAvailable Adventures:")
        for i, cls in enumerate(adventure_classes, 1):
            print(f"  {i}. {cls.NAME} — {cls.DESCRIPTION}")
        choice = int(input("Choose an adventure: ")) - 1
        adventure = adventure_classes[choice]()

        adventure.start(players)
        quit_requested = False

        while not adventure.is_over():
            state = adventure.get_state()
            display = state.get("display", str(state)) if isinstance(state, dict) else str(state)
            print(f"\n{display}")

            for i, p in enumerate(players):
                if adventure.is_over():
                    break
                action = input(f"{p['name']}'s action (or 'quit'): ").strip().lower()

                if action == "quit":
                    print("\nAdventure abandoned. No stats recorded.")
                    quit_requested = True
                    break

                msg = adventure.handle_input(i, action)
                print(f"  → {msg}")

            if quit_requested:
                break

        if not quit_requested:
            result = adventure.get_result()
            print(f"\n{result}")

            winner_index = getattr(adventure, 'winner_index', None)
            adventure_name = type(adventure).NAME

            for i, p in enumerate(players):
                name = p["name"]
                if winner_index is None:
                    outcome = "Win"
                elif winner_index == -1:
                    outcome = "Loss"
                elif winner_index == i:
                    outcome = "Win"
                else:
                    outcome = "Loss"

                profiles[name]["quest_history"].append(
                    f"{adventure_name}: {outcome} — Day 1"
                )

            # Sync collected items from adventure into character inventories
            collected = getattr(adventure, 'collected_items', [[], []])
            for i, p in enumerate(players):
                char = get_character(p)
                for item in collected[i]:
                    char.add_item(item)
                profiles[p["name"]]["inventory"] = [
                    it.name for it in char.inventory.list_items()
                ]

            update_stats(profiles, players, adventure)

            print("\n" + "=" * 50)
            print("POST-GAME SUMMARY")
            for p in players:
                name = p["name"]
                pr = profiles[name]
                print(f"\n  {name} ({pr['character_name']}, {pr['character_class']} Lv.{pr['character_level']})")
                print(f"    Realm: {pr['preferred_realm']}")
                print(f"    Wins: {pr['wins']}  Losses: {pr['losses']}")
                recent = pr["quest_history"][-3:]
                if recent:
                    print(f"    Recent quests: {', '.join(recent)}")
            print("=" * 50)
