# game/companion.py
from .data import colored_text, COLOR_GREEN
from .status_effect import StatusEffect

class Companion:
    def __init__(self, name, hp=50, strength=5, magic=2, agility=3, damage_type="Physical"):
        self.name = name
        self.hp = hp
        self.strength = strength
        self.magic = magic
        self.agility = agility
        self.damage_type = damage_type
        self.level = 1
        self.xp = 0

        self.equipped_weapon = None
        self.equipped_armor = None
        self.equipped_relic = None

        self.status_effects = []

    def is_alive(self):
        return self.hp > 0

    def gain_xp(self, amount):
        self.xp += amount
        required_xp = 50 * self.level
        if self.xp >= required_xp:
            self.level += 1
            self.xp = 0
            self.hp += 10
            self.strength += 2
            self.magic += 2
            self.agility += 1
            print(colored_text(
                f"{self.name} (Companion) leveled up to {self.level}!",
                COLOR_GREEN
            ))

    def process_status_effects(self):
        for eff in self.status_effects[:]:
            eff.apply_effect(self)
            if eff.duration <= 0:
                self.status_effects.remove(eff)
