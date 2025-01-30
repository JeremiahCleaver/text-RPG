# game/data.py
import random
import json
import os

########################################
#   Attempt to import tabulate
########################################
try:
    from tabulate import tabulate
    USE_TABULATE = True
except ImportError:
    USE_TABULATE = False


########################################
#   ANSI COLOR CONSTANTS (for colored text)
########################################
COLOR_RED = "\033[91m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_BLUE = "\033[94m"
COLOR_RESET = "\033[0m"

def colored_text(text, color=COLOR_RESET):
    return f"{color}{text}{COLOR_RESET}"


########################################
#   Global Data / Definitions
########################################

SKILLS = {
    "Power Strike": {
        "damage_multiplier": 1.5,
        "mana_cost": 0,
        "description": "A powerful melee attack that does 150% weapon damage."
    },
    "Fireball": {
        "damage_multiplier": 2.0,
        "mana_cost": 5,
        "description": "A blazing sphere of fire dealing double Magic-based damage."
    },
    # Add more...
}

TALENT_TREES = {
    "Warrior": [
        {"name": "Strong Arms", "description": "+3 Strength", 
         "effect": lambda pl: pl.stats.__setitem__("Strength", pl.stats["Strength"] + 3)},
        {"name": "Iron Skin", "description": "+10 HP", 
         "effect": lambda pl: setattr(pl, "hp", pl.hp + 10)},
    ],
    "Mage": [
        {"name": "Arcane Intellect", "description": "+3 Magic", 
         "effect": lambda pl: pl.stats.__setitem__("Magic", pl.stats["Magic"] + 3)},
        {"name": "Meditation", "description": "+5 Mana (if you track mana)", 
         "effect": lambda pl: setattr(pl, "max_mana", getattr(pl, "max_mana", 10) + 5)},
    ],
    "Thief": [
        {"name": "Quick Hands", "description": "+3 Agility", 
         "effect": lambda pl: pl.stats.__setitem__("Agility", pl.stats["Agility"] + 3)},
    ],
    "Cleric": [
        {"name": "Divine Blessing", "description": "+2 Magic, +2 Strength", 
         "effect": lambda pl: [pl.stats.__setitem__("Magic", pl.stats["Magic"] + 2),
                               pl.stats.__setitem__("Strength", pl.stats["Strength"] + 2)]},
    ],
}

# Basic status effect system references
# (We'll define the StatusEffect class itself in status_effect.py)

PET_EVOLUTIONS = {
    # "Fire Lizard": ("Flame Drake", 10, {"hp_bonus": 20, "damage_bonus": 5})
}

CRAFTING_RECIPES = {
    "Iron Sword": {
        "ingredients": {"Iron Ore": 3},
        "result": {"name": "Iron Sword","type":"weapon","cost":80,"damage":7,"rarity":"Uncommon"},
    },
    "Healing Potion": {
        "ingredients": {"Herb":2,"Water":1},
        "result":{"name":"Healing Potion","type":"potion","cost":10,"heal":50,"rarity":"Common"}
    },
    # Add more...
}

AREA_DATA = {
    "Forest": {
        "enemies": ["Goblin", "Skeleton"],
        "loot_mod": 1.0
    },
    "Volcano": {
        "enemies": ["Fire Elemental"],
        "loot_mod": 1.2
    },
    "Graveyard": {
        "enemies": ["Zombie", "Skeleton"],
        "loot_mod": 1.1
    },
}

RANDOM_EVENTS = [
    {"text": "A wandering merchant appears, offering a unique potion for 30 gold.", 
     "trigger": "special_merchant"},
    {"text": "You stumble into a hidden trap! Lose 10 HP.", 
     "trigger": "hidden_trap"},
    {"text": "A lost traveler gives you a relic in thanks. You gain a random relic.",
     "trigger": "gain_random_relic"},
]

TYPE_WEAKNESSES = {
    "Physical": "Arcane",
    "Arcane":   "Poison",
    "Poison":   "Holy",
    "Holy":     "Physical"
}

ENEMY_TYPES = {
    "Goblin": {
        "name": "Goblin",
        "base_hp": 30,
        "base_attack": 5,
        "damage_type": "Physical",
        "gold_drop": 10
    },
    "Skeleton": {
        "name": "Skeleton",
        "base_hp": 40,
        "base_attack": 7,
        "damage_type": "Physical",
        "gold_drop": 15
    },
    "Fire Elemental": {
        "name": "Fire Elemental",
        "base_hp": 35,
        "base_attack": 6,
        "damage_type": "Arcane",
        "gold_drop": 20
    },
    "Zombie": {
        "name": "Zombie",
        "base_hp": 50,
        "base_attack": 4,
        "damage_type": "Physical",
        "gold_drop": 18
    },
    "Boss Monster": {
        "name": "Boss Monster",
        "base_hp": 150,
        "base_attack": 12,
        "damage_type": "Physical",
        "gold_drop": 100
    },
}

SHOP_TIERS = {
    1: [
        {
            "name": "Short Sword", 
            "type": "weapon", 
            "cost": 50, 
            "damage": 5, 
            "rarity": "Common", 
            "class_req": ["Warrior","Thief","Cleric"]
        },
        {
            "name": "Cloth Armor", 
            "type": "armor", 
            "cost": 40, 
            "defense": 2, 
            "rarity": "Common"
        },
        {
            "name": "Health Potion", 
            "type": "potion", 
            "cost": 20, 
            "heal": 30, 
            "rarity": "Common"
        },
        {
            "name": "Sacred Talisman",
            "type": "relic", 
            "cost": 150, 
            "effect": "holy_light",
            "rarity": "Uncommon"
        },
    ],
    2: [
        {
            "name": "Long Sword",  
            "type": "weapon", 
            "cost": 100, 
            "damage": 8, 
            "rarity": "Uncommon",
            "class_req": ["Warrior","Thief","Cleric"]
        },
        {
            "name": "Leather Armor",
            "type": "armor",  
            "cost": 70,  
            "defense": 4,
            "rarity": "Common"
        },
        {
            "name": "Super Potion", 
            "type": "potion", 
            "cost": 50,  
            "heal": 70,
            "rarity": "Uncommon"
        },
        {
            "name": "Dark Amulet",  
            "type": "relic",  
            "cost": 150, 
            "effect": "shadow_power",
            "rarity": "Rare"
        },
    ],
    3: [
        {
            "name": "Wizard Staff", 
            "type": "weapon", 
            "cost": 200, 
            "damage": 12, 
            "rarity": "Uncommon", 
            "class_req": ["Mage"]
        },
        {
            "name": "War Axe", 
            "type": "weapon", 
            "cost": 220, 
            "damage": 14, 
            "rarity": "Uncommon", 
            "class_req": ["Warrior"]
        },
        {
            "name": "Venom Blade", 
            "type": "weapon", 
            "cost": 180, 
            "damage": 10, 
            "rarity": "Uncommon", 
            "class_req": ["Thief"]
        },
        {
            "name": "Radiant Scepter", 
            "type": "weapon", 
            "cost": 200, 
            "damage": 8, 
            "rarity": "Uncommon", 
            "class_req": ["Cleric"]
        },
        {
            "name": "Mega Potion", 
            "type": "potion", 
            "cost": 80, 
            "heal": 150, 
            "rarity": "Uncommon"
        },
    ],
    4: [
        {
            "name": "Mystic Robes", 
            "type": "armor",  
            "cost": 250,  
            "defense": 8, 
            "rarity": "Rare", 
            "class_req": ["Mage"]
        },
        {
            "name": "Titan Plate", 
            "type": "armor", 
            "cost": 280, 
            "defense": 12, 
            "rarity": "Rare", 
            "class_req": ["Warrior","Cleric"]
        },
        {
            "name": "Silent Boots", 
            "type": "armor",  
            "cost": 220,  
            "defense": 6,  
            "rarity": "Rare", 
            "class_req": ["Thief"]
        },
        {
            "name": "Ultra Potion", 
            "type": "potion", 
            "cost": 120, 
            "heal": 250, 
            "rarity": "Rare"
        },
        {
            "name": "Dragon Eye", 
            "type": "relic", 
            "cost": 500, 
            "effect": "dragon_gaze", 
            "rarity": "Epic"
        },
    ],
    5: [
        {
            "name": "Elder Wand", 
            "type": "weapon", 
            "cost": 600, 
            "damage": 20, 
            "class_req": ["Mage"], 
            "rarity": "Epic"
        },
        {
            "name": "Legendary Sword", 
            "type": "weapon", 
            "cost": 700, 
            "damage": 25, 
            "class_req": ["Warrior"], 
            "rarity": "Epic"
        },
        {
            "name": "Assassin's Mantle",
            "type": "armor",
            "cost": 400, 
            "defense": 12, 
            "class_req": ["Thief"], 
            "rarity": "Epic"
        },
        {
            "name": "Holy Grail", 
            "type": "relic", 
            "cost": 1000, 
            "effect": "holy_protection", 
            "rarity": "Legendary"
        },
        {
            "name": "Omnipotent Elixir",
            "type": "potion",
            "cost": 200,
            "heal": 500, 
            "rarity": "Legendary"
        },
    ],
}
