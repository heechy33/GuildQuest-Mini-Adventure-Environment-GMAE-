"""
Engine — loads adventures, manages profiles, runs the game loop.
"""

import importlib
import pkgutil
import json
import os
from adventure import MiniAdventure

PROFILES_FILE = "profiles.json"


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
        profiles[name] = {"name": name, "wins": 0, "losses": 0}
        save_profiles(profiles)
    return profiles[name]


def discover_adventures() -> list[type[MiniAdventure]]:
    import adventures
    found = []
    for _, mod_name, _ in pkgutil.iter_modules(adventures.__path__):
        mod = importlib.import_module(f"adventures.{mod_name}")
        cls = getattr(mod, "ADVENTURE_CLASS", None)
        if cls:
            found.append(cls)
    return found


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
        while not adventure.is_over():
            state = adventure.get_state()
            print(f"\n{state}")

            for i, p in enumerate(players):
                if adventure.is_over():
                    break
                action = input(f"{p['name']}'s action: ").strip()
                msg = adventure.handle_input(i, action)
                print(f"  → {msg}")

        print(f"\n{adventure.get_result()}")