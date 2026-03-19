# GuildQuest Mini-Adventure Environment (GMAE)

A two-player CLI adventure engine that integrates teammate subsystems for character management, inventory, world clocks, rarity classification, and event notifications.

---

## Overview

GMAE is a pluggable mini-adventure platform where two players share a terminal session and compete or cooperate through short scenario-based adventures. It is built on top of two integrated teammate codebases:

- **Geoffrey's subsystems** — `Character`, `Inventory`, `WorldClock`, and `Realm` for player state and time tracking
- **Heehan's subsystems** — `Rarity`/`ItemType` enums, `EventDispatcher`/`UserNotifier` observer pattern, and swappable time-display strategies

---

## Project Structure

```
.
├── main.py                    # Entry point — profile setup, adventure selection, session loop
├── engine.py                  # Game loop, player profiles, win/loss stat tracking
├── adventure.py               # MiniAdventure abstract base class
├── adventures/
│   ├── escort.py              # Co-op: guide an NPC across a 5×5 grid
│   └── relic_hunt.py         # Competitive: race to collect relics by score
├── geoffreys_gmae_code/       # Geoffrey's Character, Inventory, WorldClock, Realm
├── heechans_gmae_code/        # Heehan's Rarity, EventDispatcher, UserNotifier, strategies
└── profiles.json              # Persisted player data (auto-created on first run)
```

---

## How to Run

```
python main.py
```

Requires **Python 3.10+**. No external dependencies.

---

## Player Profiles

On first launch, each player is prompted for:
- Character name
- Character class
- Preferred realm

Profiles persist across sessions and track:
- Win / loss counts
- Inventory (relics collected during Relic Hunt)
- Quest history

All data is stored in `profiles.json`, which is created automatically.

---

## Adventures

### Escort (co-op)

Two players work together to guide an NPC from the center of a 5×5 grid to the goal.

- **Grid:** 5×5. NPC starts at `[2,2]`, goal is `[4,4]`
- **Movement:** type `up`, `down`, `left`, or `right` on your turn
- **NPC pushing:** move adjacent to the NPC to push it one tile in your direction
- **Hazards (H):** stepping on one costs 2 turns
- **Items (I):** stepping on one grants bonus turns
- **Win:** NPC reaches the goal before turns run out
- **Loss:** turns reach zero
- Uses Heehan's `BothClocksStrategy` to display both world and realm time

### Relic Hunt (competitive)

Two players race across a 5×5 grid to collect relics and accumulate score.

- **Relics** spawn with weighted rarity:

  | Rarity    | Score weight |
  |-----------|-------------|
  | Common    | 1.0         |
  | Rare      | 1.5         |
  | Epic      | 2.0         |
  | Legendary | 2.0         |

- **Win condition:** first player to reach **3.0 score**
- Collected relics are added to the player's `Character` inventory
- Uses Heehan's `WorldClockStrategy` for time display

---

## Controls

| Input                          | Effect                              |
|-------------------------------|-------------------------------------|
| `up` / `down` / `left` / `right` | Move your character one tile        |
| `quit`                         | Abandon the adventure (no stats recorded) |

---

## Adding a New Adventure

1. Create `adventures/my_adventure.py` subclassing `MiniAdventure`
2. Set class attributes `NAME` and `DESCRIPTION`
3. Implement the required methods:
   - `start(players)` — initialize state
   - `handle_input(player_index, input_str)` — process a player's action
   - `get_state()` — return a string describing the current board/state
   - `is_over()` — return `True` when the adventure should end
   - `get_result()` — return a summary string
4. Set `winner_index`:
   - `None` — co-op win (all players win)
   - `-1` — all players lose
   - `0` or `1` — index of the winning player (competitive)
5. Export `ADVENTURE_CLASS = MyAdventure` at the bottom of the file — the engine auto-discovers it

---

## Integrated Teammate Subsystems

### Geoffrey's (`geoffreys_gmae_code/`)

| Component | Description |
|-----------|-------------|
| `WorldClock(days, hours, minutes)` | Game clock with `to_minutes()` and `from_minutes()` utilities |
| `Character` | Player character with name, class, and linked inventory |
| `Inventory` / `InventoryItem` | Loot tracking; relics are added here on collection |
| `Realm` + `FixedOffsetStrategy` | Converts world time to realm-local time |

### Heehan's (`heechans_gmae_code/`)

| Component | Description |
|-----------|-------------|
| `Rarity`, `ItemType` | Enums for classifying items by rarity and type |
| `EventDispatcher` + `UserNotifier` | Observer-pattern event system for in-game notifications |
| `WorldClockStrategy` | Displays current world clock time |
| `BothClocksStrategy` | Displays both world and realm time simultaneously |
