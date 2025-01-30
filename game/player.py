# game/player.py
from .data import (
    colored_text,
    COLOR_GREEN, COLOR_YELLOW, 
    TALENT_TREES, SKILLS
)
from .status_effect import StatusEffect
from .companion import Companion
from .pet import Pet

class Player:
    def __init__(self, name, player_class):
        self.name = name
        self.player_class = player_class
        self.level = 1
        self.xp = 0
        self.karma = 0
        self.gold = 100
        self.hp = 100
        self.max_mana = 10
        self.mana = 10

        self.stats = {}
        self.init_class_stats()
        self.init_damage_type()

        self.inventory = []
        self.companions = []
        self.pets = []

        self.equipped_weapon = None
        self.equipped_armor = None
        self.equipped_relic = None

        self.skills = []
        self.load_class_skills()

        self.status_effects = []

    def init_class_stats(self):
        base_stats = {
            "Warrior": {"Strength": 10, "Magic": 2,  "Agility": 5},
            "Mage":    {"Strength": 2,  "Magic": 10, "Agility": 5},
            "Thief":   {"Strength": 5,  "Magic": 4,  "Agility": 10},
            "Cleric":  {"Strength": 4,  "Magic": 8,  "Agility": 6},
        }
        self.stats = base_stats.get(self.player_class, {"Strength":5,"Magic":5,"Agility":5})

    def init_damage_type(self):
        mapping = {
            "Warrior": "Physical",
            "Mage":    "Arcane",
            "Thief":   "Poison",
            "Cleric":  "Holy",
        }
        self.damage_type = mapping.get(self.player_class, "Physical")

    def load_class_skills(self):
        if self.player_class == "Warrior":
            self.skills = ["Power Strike"]
        elif self.player_class == "Mage":
            self.skills = ["Fireball"]
        # etc.

    def is_alive(self):
        return self.hp > 0

    def process_status_effects(self):
        for eff in self.status_effects[:]:
            eff.apply_effect(self)
            if eff.duration <= 0:
                self.status_effects.remove(eff)

    def gain_xp(self, amount):
        self.xp += amount
        required = 100 * self.level
        if self.xp >= required:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.xp = 0
        print(colored_text(f"\n*** {self.name} has leveled up to {self.level}! ***", COLOR_GREEN))
        for stat in self.stats:
            self.stats[stat] += 1
        self.pick_talent()

    def pick_talent(self):
        talents = TALENT_TREES.get(self.player_class, [])
        if not talents:
            return
        print("\nChoose a talent:")
        for i, t in enumerate(talents, start=1):
            print(f"{i}. {t['name']} - {t['description']}")
        choice = input("Pick # or 'skip': ").strip()
        if choice.isdigit():
            idx = int(choice)-1
            if 0 <= idx < len(talents):
                talent = talents[idx]
                talent["effect"](self)
                print(colored_text(f"You gained the talent: {talent['name']}", COLOR_YELLOW))

    def to_dict(self):
        return {
            "name": self.name,
            "player_class": self.player_class,
            "level": self.level,
            "xp": self.xp,
            "karma": self.karma,
            "gold": self.gold,
            "hp": self.hp,
            "mana": self.mana,
            "max_mana": self.max_mana,
            "stats": self.stats,
            "inventory": self.inventory,
            "companions": [self.companion_to_dict(c) for c in self.companions],
            "pets": [self.pet_to_dict(p) for p in self.pets],
            "equipped_weapon": self.equipped_weapon,
            "equipped_armor": self.equipped_armor,
            "equipped_relic": self.equipped_relic,
            "skills": self.skills,
            "damage_type": self.damage_type,
        }

    def companion_to_dict(self, c: Companion):
        return {
            "name": c.name,
            "hp": c.hp,
            "strength": c.strength,
            "magic": c.magic,
            "agility": c.agility,
            "damage_type": c.damage_type,
            "level": c.level,
            "xp": c.xp,
            "equipped_weapon": c.equipped_weapon,
            "equipped_armor": c.equipped_armor,
            "equipped_relic": c.equipped_relic,
        }

    def pet_to_dict(self, p: Pet):
        return {
            "name": p.name,
            "hp": p.hp,
            "cuteness": p.cuteness,
            "damage": p.damage,
            "damage_type": p.damage_type,
            "level": p.level,
            "xp": p.xp,
            "equipped_weapon": p.equipped_weapon,
            "equipped_armor": p.equipped_armor,
            "equipped_relic": p.equipped_relic,
        }

    @staticmethod
    def from_dict(data):
        from .player import Player  # safe import inside method
        from .companion import Companion
        from .pet import Pet

        p = Player(data["name"], data["player_class"])
        p.level = data["level"]
        p.xp = data["xp"]
        p.karma = data["karma"]
        p.gold = data["gold"]
        p.hp = data["hp"]
        p.mana = data.get("mana", 10)
        p.max_mana = data.get("max_mana", 10)
        p.stats = data["stats"]
        p.inventory = data["inventory"]
        # Rebuild companions
        for cdict in data["companions"]:
            c = Companion(
                cdict["name"], cdict["hp"],
                cdict["strength"], cdict["magic"],
                cdict["agility"], cdict["damage_type"]
            )
            c.level = cdict["level"]
            c.xp = cdict["xp"]
            c.equipped_weapon = cdict["equipped_weapon"]
            c.equipped_armor = cdict["equipped_armor"]
            c.equipped_relic = cdict["equipped_relic"]
            p.companions.append(c)
        # Rebuild pets
        for pdict in data["pets"]:
            pt = Pet(
                pdict["name"], pdict["hp"], pdict["cuteness"],
                pdict["damage"], pdict["damage_type"]
            )
            pt.level = pdict["level"]
            pt.xp = pdict["xp"]
            pt.equipped_weapon = pdict["equipped_weapon"]
            pt.equipped_armor = pdict["equipped_armor"]
            pt.equipped_relic = pdict["equipped_relic"]
            p.pets.append(pt)

        p.equipped_weapon = data["equipped_weapon"]
        p.equipped_armor = data["equipped_armor"]
        p.equipped_relic = data["equipped_relic"]
        p.skills = data.get("skills", [])
        p.damage_type = data.get("damage_type", "Physical")

        return p
