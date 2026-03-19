"""
GuildQuest — Campaign Organizer

Design Patterns:
  Strategy - swappable time-conversion algorithms (FixedOffset, LinearMultiplier)
  Template Method — shared timeline rendering skeleton, subclasses fill in the gaps
  Facade — GuildQuestFacade hides subsystem wiring from callers

Refactorings:
  Extract Method  — _format_events() pulled out of 4 identical render loops
  Replace Magic Number — 1440/60/24/7/30 replaced with named constants
  Encapsulate Collection — _items / _quest_events made private; access via methods only
  Introduce Parameter Object — EventTimeSpec replaces 6 loose time args in add_event()
"""

from __future__ import annotations
from typing import List, Optional, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass


# Named constants replace raw literals throughout the codebase.
MINUTES_PER_HOUR: int = 60
HOURS_PER_DAY:    int = 24
MINUTES_PER_DAY:  int = MINUTES_PER_HOUR * HOURS_PER_DAY
DAYS_PER_WEEK:    int = 7
DAYS_PER_MONTH:   int = 30


class WorldClock:
    def __init__(self, days: int, hours: int, minutes: int):
        self.days, self.hours, self.minutes = days, hours, minutes
        self._normalize()

    def _normalize(self) -> None:
        if self.minutes >= MINUTES_PER_HOUR:
            self.hours   += self.minutes // MINUTES_PER_HOUR
            self.minutes %= MINUTES_PER_HOUR
        if self.hours >= HOURS_PER_DAY:
            self.days  += self.hours // HOURS_PER_DAY
            self.hours %= HOURS_PER_DAY

    def to_minutes(self) -> int:
        return self.days * MINUTES_PER_DAY + self.hours * MINUTES_PER_HOUR + self.minutes

    @classmethod
    def from_minutes(cls, total: int) -> WorldClock:
        return cls(
            total // MINUTES_PER_DAY,
            (total % MINUTES_PER_DAY) // MINUTES_PER_HOUR,
            total % MINUTES_PER_HOUR,
        )

    def __str__(self) -> str:
        return f"Day {self.days}, {self.hours:02d}:{self.minutes:02d}"

    def __lt__(self, o: WorldClock) -> bool: return self.to_minutes() <  o.to_minutes()
    def __le__(self, o: WorldClock) -> bool: return self.to_minutes() <= o.to_minutes()
    def __eq__(self, o: object) -> bool:
        return isinstance(o, WorldClock) and self.to_minutes() == o.to_minutes()
    def __gt__(self, o: WorldClock) -> bool: return self.to_minutes() >  o.to_minutes()
    def __ge__(self, o: WorldClock) -> bool: return self.to_minutes() >= o.to_minutes()


# ── Strategy: Time Conversion ─────────────────────────────────────────────────
# Realm delegates time conversion to a swappable strategy object so that
# new conversion rules can be added without touching Realm.

class TimeConversionStrategy(ABC):
    @abstractmethod
    def world_to_local(self, world_time: WorldClock) -> WorldClock:
        ...


class FixedOffsetStrategy(TimeConversionStrategy):
    """Shifts world time by a fixed number of hours."""
    def __init__(self, offset_hours: int) -> None:
        self.offset_hours = offset_hours

    def world_to_local(self, world_time: WorldClock) -> WorldClock:
        return WorldClock.from_minutes(
            world_time.to_minutes() + self.offset_hours * MINUTES_PER_HOUR
        )


class LinearMultiplierStrategy(TimeConversionStrategy):
    """Scales time by a multiplier — for realms where time flows at a different rate."""
    def __init__(self, multiplier: float) -> None:
        self.multiplier = multiplier

    def world_to_local(self, world_time: WorldClock) -> WorldClock:
        return WorldClock.from_minutes(
            int(world_time.to_minutes() * self.multiplier)
        )


class LocalTimeRule:
    """Backward-compatible wrapper — delegates to FixedOffsetStrategy."""
    def __init__(self, offset_hours: int) -> None:
        self._strategy: TimeConversionStrategy = FixedOffsetStrategy(offset_hours)

    def world_to_local(self, world_time: WorldClock) -> WorldClock:
        return self._strategy.world_to_local(world_time)


class Realm:
    _next_id: int = 1

    def __init__(self, name: str, description: str = "") -> None:
        self.realm_id = Realm._next_id
        Realm._next_id += 1
        self.name = name
        self.description = description
        self.time_rule: TimeConversionStrategy = FixedOffsetStrategy(0)

    def get_local_time(self, world_time: WorldClock) -> WorldClock:
        return self.time_rule.world_to_local(world_time)


class InventoryItem:
    def __init__(self, name: str, rarity: str, item_type: str, description: str = "") -> None:
        self.name, self.rarity, self.item_type, self.description = name, rarity, item_type, description


# ── Encapsulate Collection: Inventory ────────────────────────────────────────
# The backing list is private. All access goes through named methods so
# invariants stay intact and callers cannot mutate the list directly.

class Inventory:
    def __init__(self):
        self._items: List[InventoryItem] = []

    def add_item(self, item: InventoryItem):
        self._items.append(item)

    def remove_item(self, item_name: str) -> bool:
        for i, item in enumerate(self._items):
            if item.name == item_name:
                self._items.pop(i)
                return True
        return False

    def get_item(self, item_name: str) -> Optional[InventoryItem]:
        return next((item for item in self._items if item.name == item_name), None)

    def list_items(self) -> List[InventoryItem]:
        return self._items.copy()

    def count(self) -> int:
        return len(self._items)

    def clear(self) -> None:
        self._items.clear()


class Character:
    def __init__(self, name: str, char_class: str, level: int) -> None:
        self.name, self.char_class, self.level = name, char_class, level
        self.inventory = Inventory()

    def add_item(self, item: InventoryItem):
        self.inventory.add_item(item)

    def remove_item(self, item_name: str) -> bool:
        return self.inventory.remove_item(item_name)

    def level_up(self):
        self.level += 1


class QuestEvent:
    def __init__(self, name: str, start_time: WorldClock, realm: Realm,
                 end_time: Optional[WorldClock] = None) -> None:
        self.name, self.start_time, self.end_time, self.realm = name, start_time, end_time, realm
        self.participants: List[Character] = []

    def add_character(self, character: Character):
        if character not in self.participants:
            self.participants.append(character)

    def remove_character(self, character: Character) -> bool:
        if character in self.participants:
            self.participants.remove(character)
            return True
        return False

    def get_local_time(self) -> Tuple[WorldClock, Optional[WorldClock]]:
        local_start = self.realm.get_local_time(self.start_time)
        local_end = self.realm.get_local_time(self.end_time) if self.end_time else None
        return (local_start, local_end)


# ── Encapsulate Collection: Campaign ─────────────────────────────────────────
# quest_events is private so external code cannot bypass Campaign's own add/remove logic.

class Campaign:
    def __init__(self, name: str, owner):
        self.name, self.owner = name, owner
        self._quest_events: List[QuestEvent] = []
        self.is_public = False

    def add_quest_event(self, event: QuestEvent):
        self._quest_events.append(event)

    def remove_quest_event(self, event: QuestEvent) -> bool:
        if event in self._quest_events:
            self._quest_events.remove(event)
            return True
        return False

    def get_events_sorted(self) -> List[QuestEvent]:
        return sorted(self._quest_events, key=lambda e: e.start_time)

    def get_events_for_day(self, day: int) -> List[QuestEvent]:
        return [e for e in self._quest_events if e.start_time.days == day]

    def get_events_for_week(self, start_day: int) -> List[QuestEvent]:
        return [e for e in self._quest_events
                if start_day <= e.start_time.days <= start_day + DAYS_PER_WEEK - 1]

    def get_events_for_month(self, start_day: int) -> List[QuestEvent]:
        return [e for e in self._quest_events
                if start_day <= e.start_time.days <= start_day + DAYS_PER_MONTH - 1]

    def count_events(self) -> int:
        return len(self._quest_events)

    def clear_events(self) -> None:
        self._quest_events.clear()

    def set_public(self, is_public: bool):
        self.is_public = is_public

    def can_access(self, user) -> bool:
        return self.owner == user or self.is_public


class UserSettings:
    def __init__(self):
        self.current_realm: Optional[Realm] = None
        self.time_display = "world"

    def set_current_realm(self, realm: Realm):
        self.current_realm = realm

    def set_time_display(self, display: str):
        self.time_display = display


class User:
    def __init__(self, username: str):
        self.username = username
        self.campaigns: List[Campaign] = []
        self.characters: List[Character] = []
        self.settings = UserSettings()

    def create_campaign(self, name: str) -> Campaign:
        campaign = Campaign(name, self)
        self.campaigns.append(campaign)
        return campaign

    def delete_campaign(self, campaign: Campaign) -> bool:
        if campaign in self.campaigns:
            campaign.clear_events()
            self.campaigns.remove(campaign)
            return True
        return False

    def rename_campaign(self, campaign: Campaign, new_name: str) -> bool:
        if campaign in self.campaigns:
            campaign.name = new_name
            return True
        return False

    def get_campaign(self, name: str) -> Optional[Campaign]:
        return next((c for c in self.campaigns if c.name == name), None)

    def create_character(self, name: str, char_class: str, level: int) -> Character:
        character = Character(name, char_class, level)
        self.characters.append(character)
        return character

    def delete_character(self, character: Character) -> bool:
        if character in self.characters:
            character.inventory.clear()
            self.characters.remove(character)
            return True
        return False

    def get_character(self, name: str) -> Optional[Character]:
        return next((c for c in self.characters if c.name == name), None)

    def list_campaigns(self) -> List[Campaign]: return self.campaigns.copy()
    def list_characters(self) -> List[Character]: return self.characters.copy()


# ── Template Method + Extract Method: TimelineView ───────────────────────────
# render() is the fixed skeleton — subclasses supply only the two pieces
# that vary: which events to fetch and what header to show.
# _format_events() was extracted from four identical loops that previously lived in each view method.

class TimelineView(ABC):
    def __init__(self, campaign: Campaign, user_settings: UserSettings) -> None:
        self.campaign = campaign
        self.user_settings = user_settings

    @abstractmethod
    def _get_events(self) -> List[QuestEvent]:
        ...

    @abstractmethod
    def _header(self) -> str:
        ...

    def _format_events(self, events: List[QuestEvent], header: str) -> str:
        if not events:
            return f"{header}: No events"
        result = f"=== {header} ===\n"
        for e in sorted(events, key=lambda x: x.start_time):
            result += f"  - {e.name} @ {e.realm.name} ({e.start_time})\n"
        return result

    def render(self) -> str:
        return self._format_events(self._get_events(), self._header())


class DayView(TimelineView):
    def __init__(self, campaign: Campaign, settings: UserSettings, day: int) -> None:
        super().__init__(campaign, settings)
        self._day = day

    def _get_events(self) -> List[QuestEvent]:
        return self.campaign.get_events_for_day(self._day)

    def _header(self) -> str:
        return f"Day {self._day}"


class WeekView(TimelineView):
    def __init__(self, campaign: Campaign, settings: UserSettings, start_day: int) -> None:
        super().__init__(campaign, settings)
        self._start = start_day

    def _get_events(self) -> List[QuestEvent]:
        return self.campaign.get_events_for_week(self._start)

    def _header(self) -> str:
        return f"Week: Days {self._start}-{self._start + DAYS_PER_WEEK - 1}"


class MonthView(TimelineView):
    def __init__(self, campaign: Campaign, settings: UserSettings, start_day: int) -> None:
        super().__init__(campaign, settings)
        self._start = start_day

    def _get_events(self) -> List[QuestEvent]:
        return self.campaign.get_events_for_month(self._start)

    def _header(self) -> str:
        return f"Month: Days {self._start}-{self._start + DAYS_PER_MONTH - 1}"


class AllEventsView(TimelineView):
    def _get_events(self) -> List[QuestEvent]:
        return self.campaign.get_events_sorted()

    def _header(self) -> str:
        return self.campaign.name


# ── Introduce Parameter Object: EventTimeSpec ────────────────────────────────
# Bundles the six time-related arguments that add_event() previously accepted
# individually into one named object. Conversion to WorldClock pairs lives
# here, where the data is, rather than inside the Facade method.

@dataclass
class EventTimeSpec:
    start_day:    int
    start_hour:   int
    start_minute: int = 0
    end_day:      Optional[int] = None
    end_hour:     Optional[int] = None
    end_minute:   int = 0

    def to_world_clocks(self) -> Tuple[WorldClock, Optional[WorldClock]]:
        start = WorldClock(self.start_day, self.start_hour, self.start_minute)
        end: Optional[WorldClock] = None
        if self.end_day is not None and self.end_hour is not None:
            end = WorldClock(self.end_day, self.end_hour, self.end_minute)
        return start, end


# ── Facade: GuildQuestFacade ──────────────────────────────────────────────────
# Single entry point for common operations. Callers never need to touch
# WorldClock, QuestEvent, or TimelineView subclasses directly.

class GuildQuestFacade:

    def __init__(self, username: str) -> None:
        self.user = User(username)

    def create_campaign(self, name: str, public: bool = False) -> Campaign:
        campaign = self.user.create_campaign(name)
        campaign.set_public(public)
        return campaign

    def create_realm(self, name: str, description: str = "",
                     offset_hours: int = 0) -> Realm:
        realm = Realm(name, description)
        realm.time_rule = FixedOffsetStrategy(offset_hours)
        return realm

    def add_event(self, campaign: Campaign, name: str, realm: Realm,
                  time_spec: EventTimeSpec) -> QuestEvent:
        start, end = time_spec.to_world_clocks()
        event = QuestEvent(name, start, realm, end)
        campaign.add_quest_event(event)
        return event

    def render_all(self, campaign: Campaign) -> str:
        return AllEventsView(campaign, self.user.settings).render()

    def render_week(self, campaign: Campaign, start_day: int) -> str:
        return WeekView(campaign, self.user.settings, start_day).render()

    def render_day(self, campaign: Campaign, day: int) -> str:
        return DayView(campaign, self.user.settings, day).render()

    def create_character(self, name: str, char_class: str, level: int) -> Character:
        return self.user.create_character(name, char_class, level)


def main():
    print("=" * 60)
    print("GUILDQUEST - Revised UML Implementation")
    print("=" * 60)

    gq = GuildQuestFacade("Alice")

    elvenwood = gq.create_realm("Elvenwood", "Ancient forest", offset_hours=2)

    aragorn = gq.create_character("Aragorn", "Ranger", 10)
    aragorn.add_item(InventoryItem("Anduril", "Legendary", "Sword"))

    campaign = gq.create_campaign("Fellowship Journey", public=True)

    event1 = gq.add_event(campaign, "Council of Elrond", elvenwood,
                          EventTimeSpec(start_day=0, start_hour=9))
    event1.add_character(aragorn)

    gq.add_event(campaign, "Battle of Helm's Deep", elvenwood,
                 EventTimeSpec(start_day=5, start_hour=14, start_minute=30,
                               end_day=5, end_hour=18))

    print(gq.render_all(campaign))
    print()
    print(gq.render_week(campaign, start_day=0))
    print()
    print(gq.render_day(campaign, day=0))

    print("\n" + "=" * 60)
    print(f"Campaign: {campaign.name} ({'Public' if campaign.is_public else 'Private'})")
    print(f"Events: {campaign.count_events()}")
    print(f"Characters: {len(gq.user.list_characters())}")
    print(f"Inventory Items: {aragorn.inventory.count()}")
    print("=" * 60)


if __name__ == "__main__":
    main()