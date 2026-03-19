from enum import Enum
from abc import ABC, abstractmethod


class Visibility(Enum):
    PUBLIC = "Public"
    PRIVATE = "Private"

class Permission(Enum):
    VIEW_ONLY = "View Only"
    COLLABORATIVE = "Collaborative"

class Theme(Enum):
    CLASSIC = "Classic"
    MODERN = "Modern"

class Resolution(Enum):
    RES16_9 = "16:9"
    RES5_4 = "5:4"
    RES4_3 = "4:3"

class Language(Enum):
    ENGLISH = "English"
    SPANISH = "Spanish"
    MANDARIN = "Mandarin"
    JAPANESE = "Japanese"

class Rarity(Enum):
    COMMON = "Common"
    RARE = "Rare"
    EPIC = "Epic"
    LEGENDARY = "Legendary"

class ItemType(Enum):
    WEAPON = "Weapon"
    ARMOR = "Armor"
    CONSUMABLE = "Consumable"

class Settings:
    def __init__(self):
        self.theme = Theme.CLASSIC
        self.language = Language.ENGLISH
        self.resolution = Resolution.RES16_9
        self.time_display = WorldClockStrategy()
        self.current_realm = None


class WorldDate:
    def __init__(self, years, months, weeks, days):
        self.years = years
        self.months = months
        self.weeks = weeks
        self.days = days

    def __str__(self):
        return f"Y:{self.years} M:{self.months} W:{self.weeks} D:{self.days}"

class WorldTime:
    def __init__(self, hours, minutes):
        self.hours = hours
        self.minutes = minutes

    def __str__(self):
        return f"{self.hours}:{self.minutes:02d}"


class WorldClock:
    def __init__(self, date: WorldDate, time: WorldTime):
        self.date = date
        self.time = time

    @property
    def years(self):
        return self.date.years

    @property
    def months(self):
        return self.date.months

    @property
    def weeks(self):
        return self.date.weeks

    @property
    def days(self):
        return self.date.days

    @property
    def hours(self):
        return self.time.hours

    @property
    def minutes(self):
        return self.time.minutes

    def __str__(self):
        return f"{self.date} [{self.time}]"

class Realm:
    def __init__(self, name, description, map_id, time_offset_hours):
        self.name = name
        self.description = description
        self.map_id = map_id
        self.time_offset_hours = time_offset_hours

    def toLocalTime(self, world_clock):
        local_hours = world_clock.hours + self.time_offset_hours
        local_days = world_clock.days

        while local_hours >= 24:
            local_hours -= 24
            local_days += 1

        while local_hours < 0:
            local_hours += 24
            local_days -= 1

        return local_hours, world_clock.minutes, local_days
    
class TimeDisplayStrategy(ABC):

    @abstractmethod
    def format_time(self, world_clock, realm=None):
        pass

class WorldClockStrategy(TimeDisplayStrategy):
    
    def format_time(self, world_clock, realm=None):
        return f"World Time — {world_clock}"

class RealmClockStrategy(TimeDisplayStrategy):

    def format_time(self, world_clock, realm=None):
        if realm is None:
            return f"Realm is not specified"
        
        local_hours, local_minutes, local_days = realm.toLocalTime(world_clock)

        return (f"Realm Time ({realm.name}) — " f"Day {local_days}, {local_hours}:{local_minutes:02d}")

class BothClocksStrategy(TimeDisplayStrategy):

    def format_time(self, world_clock, realm=None):
        world = WorldClockStrategy().format_time(world_clock, realm)
        realm_str = RealmClockStrategy().format_time(world_clock, realm)
        
        return f"{world}  |  {realm_str}"

class Item:
    def __init__(self, name, rarity, item_type, description):
        self.name = name
        self.rarity = rarity
        self.item_type = item_type
        self.description = description


class Character:
    def __init__(self, name, char_class, level):
        self.name = name
        self.char_class = char_class
        self.level = level
        self.inventory = []

    def addItem(self, item):
        self.inventory.append(item)

    def removeItem(self, item):
        self.inventory.remove(item)


class QuestEvent:
    def __init__(self, name, startTime, endTime, realm=None):
        self.name = name
        self.startTime = startTime
        self.endTime = endTime
        self.realm = realm
        self.participants = []
        self.access_map = {}

    def addParticipants(self, character):
        self.participants.append(character)

    def removeParticipants(self, character):
        self.participants.remove(character)

def find_by_name(list_items, name):
    for item in list_items:
        if item.name == name:
            return item
        
    return None

class Campaign:
    def __init__(self, name, visibility):
        self.name = name
        self.visibility = visibility
        self.quest_events = []
        self.access_map = {}

    def addQuestEvent(self, quest_event):
        self.quest_events.append(quest_event)

    def removeQuestEvent(self, quest_event):
        self.quest_events.remove(quest_event)

    def findQuestEvent(self, name):
        return find_by_name(self.quest_events, name)

    def updateQuestEvent(self, quest_event_name, newName):
        event = self.findQuestEvent(quest_event_name)
        if event:
            event.name = newName
        else:
            print("QuestEvent does not exist")

    def shareQuestEvent(self, quest_event, user, permission):
        quest_event.access_map[user.username] = permission


class User:
    def __init__(self, username):
        self.username = username
        self.campaigns = []
        self.characters = []
        self.settings = Settings()

    def addCampaign(self, campaign):
        self.campaigns.append(campaign)

    def removeCampaign(self, campaign):
        self.campaigns.remove(campaign)

    def findCampaign(self, name):
        return find_by_name(self.campaigns, name)

    def updateCampaignVisibility(self, campaign_name, newVisibility):
        campaign = self.findCampaign(campaign_name)

        if campaign:
            campaign.visibility = newVisibility
        else:
            print("Campaign not found")

    def updateCampaignName(self, campaign_name, newName):
        campaign = self.findCampaign(campaign_name)

        if campaign:
            campaign.name = newName
        else:
            print("Campaign not found")

    def shareCampaign(self, campaign, user, permission):
        campaign.access_map[user.username] = permission


class GuildQuest:
    def __init__(self):
        self.users = []
        self.realms = []

    def addUser(self, username):
        new_user = User(username)
        self.users.append(new_user)
        return new_user

    def findUser(self, username):
        for user in self.users:
            if user.username == username:
                return user
        return None

    def addRealm(self, realm):
        self.realms.append(realm)

class GuildQuestFacade:

    def __init__(self, app: GuildQuest):
        self._app = app
        self.dispatcher = EventDispatcher()

    def create_user(self, username):
        return self._app.addUser(username)

    def create_campaign(self, owner_username, campaign_name, visibility):
        owner = self._app.findUser(owner_username)

        if owner is None:
            print(f"User '{owner_username}' not found.")
            return None
        
        camp = Campaign(campaign_name, visibility)
        owner.addCampaign(camp)

        return camp

    def share_campaign(self, campaign, owner_username, target_username, permission):
        owner  = self._app.findUser(owner_username)
        target = self._app.findUser(target_username)

        if owner is None or target is None:
            print("User not found")
            return
        
        owner.shareCampaign(campaign, target, permission)

        self.dispatcher.notify("campaign_shared", f"'{campaign.name}' was shared with you ({permission.value})")

    def schedule_event(self, campaign, name, start, end, realm=None):
        event = QuestEvent(name, start, end, realm)
        campaign.addQuestEvent(event)

        self.dispatcher.notify("QuestEvent_scheduled", f"New QuestEvent '{name}' scheduled in '{campaign.name}'")
        return event

    def rename_event(self, campaign, old_name, new_name):
        campaign.updateQuestEvent(old_name, new_name)

    def set_time_display(self, username, strategy):
        user = self._app.findUser(username)

        if user:
            user.settings.time_display = strategy

class Observer(ABC):
    @abstractmethod
    def update(self, event_type, message):
        pass

class UserNotifier(Observer):

    def __init__(self, username):
        self.username = username
        self.notifications = []

    def update(self, event_type, message):
        self.notifications.append(f"[{event_type}] {message}")

class EventDispatcher:

    def __init__(self):
        self._subscribers = {}

    def subscribe(self, event_type, observer):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append(observer)

    def unsubscribe(self, event_type, observer):
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(observer)

    def notify(self, event_type, message):
        for obs in self._subscribers.get(event_type, []):
            obs.update(event_type, message)

if __name__ == "__main__":
    app = GuildQuest()
    facade = GuildQuestFacade(app)

    bob = facade.create_user("Bob")
    jack = facade.create_user("Jack")

    camp1 = facade.create_campaign("Bob", "Daily", Visibility.PRIVATE)
    camp2 = facade.create_campaign("Jack", "Patrol", Visibility.PUBLIC)

    t1 = WorldClock(WorldDate(100, 3, 1, 1), WorldTime(10, 0))
    t2 = WorldClock(WorldDate(100, 3, 1, 1), WorldTime(14, 0))

    facade.schedule_event(camp1, "Kill dragon", t1, t2)
    facade.schedule_event(camp2, "Heal a goblin", t1, t2)

    elf = Character("elf", "healer", 5)
    elf.addItem(Item("Ring", Rarity.LEGENDARY, ItemType.WEAPON, "The one ring"))
    elf.addItem(Item("Bread", Rarity.COMMON, ItemType.CONSUMABLE, "Sourdough bread"))
    bob.characters.append(elf)

    legolas_notifier = UserNotifier("Legolas")
    facade.dispatcher.subscribe("campaign_shared", legolas_notifier)
    facade.dispatcher.subscribe("event_scheduled", legolas_notifier)

    print("Welcome to GuildQuest!")

    while True:
        print("\n--- Menu ---")
        print("1. View all data")
        print("2. Share a campaign")
        print("3. View notifications")
        print("4. Change time display")
        print("5. Find a quest event")
        print("6. Update campaign name/visibility")
        print("7. Add/remove participant")
        print("0. Exit")

        choice = input("\nChoice: ")

        if choice == "1":
            for u in app.users:
                print(f"\n{u.username} | Strategy: {type(u.settings.time_display).__name__}")

                for c in u.campaigns:
                    shared = list(c.access_map.keys())

                    print(f"  Campaign: '{c.name}' [{c.visibility.value}]" +
                          (f" — shared with: {', '.join(shared)}" if shared else ""))
                    
                    for e in c.quest_events:
                        pnames = [p.name for p in e.participants]
                        print(f"    Event: '{e.name}' | {e.startTime} -> {e.endTime}")
                        if pnames:
                            print(f"      Participants: {', '.join(pnames)}")

                for c in u.characters:
                    print(f"  Character: {c.name} ({c.char_class} Lv.{c.level})")
                    for item in c.inventory:
                        print(f"    [{item.rarity.value}] {item.name} ({item.item_type.value}) - {item.description}")

        elif choice == "2":
            owner = input("Owner username: ")
            camp_name = input("Campaign name to share: ")
            target = input("Share with: ")
            print("Permission — 1. View Only  2. Collaborative")

            p = input("Choice: ")
            perm = Permission.VIEW_ONLY if p == "1" else Permission.COLLABORATIVE
            owner_user = app.findUser(owner)
            camp = owner_user.findCampaign(camp_name) if owner_user else None

            if camp:
                facade.share_campaign(camp, owner, target, perm)
                print(f"Shared! Check {target}'s notifications (option 3).")
            else:
                print("User or campaign not found.")

        elif choice == "3":
            username = input("Username: ")

            if legolas_notifier.username.lower() == username.lower():
                if legolas_notifier.notifications:
                    print(f"\n{username}'s notifications:")
                    for n in legolas_notifier.notifications:
                        print(f"  {n}")
                else:
                    print("Inbox is empty. Try sharing a campaign first (option 2).")
            else:
                print("No notifier found for that user.")

        elif choice == "4":
            username = input("Username: ")
            user = app.findUser(username)
            
            if user:
                print("1. World Clock  2. Realm Clock  3. Both")
                s = input("Pick: ")
                if s == "1":
                    user.settings.time_display = WorldClockStrategy()
                elif s == "2":
                    user.settings.time_display = RealmClockStrategy()
                elif s == "3":
                    user.settings.time_display = BothClocksStrategy()
                sample = WorldClock(WorldDate(100, 1, 1, 1), WorldTime(14, 30))
                print(f"Result: {user.settings.time_display.format_time(sample)}")
            else:
                print("User not found.")

        elif choice == "5":
            camp_name = input("Campaign name: ")
            event_name = input("Event name: ")
            camp = find_by_name([c for u in app.users for c in u.campaigns], camp_name)

            if camp:
                result = camp.findQuestEvent(event_name)
                print(f"Found: '{result.name}' | {result.startTime}" if result else "Event not found.")
            else:
                print("Campaign not found.")

        elif choice == "6":
            username = input("Username: ")
            camp_name = input("Campaign name: ")
            user = app.findUser(username)
            camp = user.findCampaign(camp_name) if user else None

            if camp:
                print("1. Rename  2. Change visibility")
                sub = input("Choice: ")
                if sub == "1":
                    new_name = input("New name: ")
                    user.updateCampaignName(camp.name, new_name)
                    print(f"Renamed to '{camp.name}'.")
                elif sub == "2":
                    print("1. Public  2. Private")
                    v = input("Choice: ")
                    user.updateCampaignVisibility(camp.name, Visibility.PUBLIC if v == "1" else Visibility.PRIVATE)
                    print(f"Visibility: {camp.visibility.value}")
            else:
                print("User or campaign not found.")

        elif choice == "7":
            camp_name = input("Campaign name: ")
            event_name = input("Event name: ")
            char_name = input("Character name: ")
            camp = find_by_name([c for u in app.users for c in u.campaigns], camp_name)
            event = camp.findQuestEvent(event_name) if camp else None
            char = find_by_name([c for u in app.users for c in u.characters], char_name)

            if event and char:
                print("1. Add  2. Remove")
                action = input("Choice: ")
                
                if action == "1":
                    event.addParticipants(char)
                    print(f"{char.name} added to '{event.name}'.")
                elif action == "2" and char in event.participants:
                    event.removeParticipants(char)
                    print(f"{char.name} removed from '{event.name}'.")
                else:
                    print("Not a participant or invalid choice.")
            else:
                print("Event or character not found.")

        elif choice == "0":
            print("Goodbye!")
            break

        else:
            print("Invalid option.")
