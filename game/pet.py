# game/pet.py
from .data import colored_text, COLOR_GREEN, COLOR_RED, PET_EVOLUTIONS
from .status_effect import StatusEffect

class Pet:
    def __init__(self, name, hp=30, cuteness=100, damage=3, damage_type="Physical"):
        self.name = name
        self.hp = hp
        self.cuteness = cuteness
        self.damage = damage
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
        required_xp = 30 * self.level
        self.xp += amount
        if self.xp >= required_xp:
            self.level += 1
            self.xp = 0
            self.hp += 5
            self.damage += 1
            print(colored_text(
                f"{self.name} (Pet) leveled up to {self.level}!",
                COLOR_GREEN
            ))
            self.check_evolution()

    def check_evolution(self):
        if self.name in PET_EVOLUTIONS:
            evo_name, evo_level, evo_stats = PET_EVOLUTIONS[self.name]
            if self.level >= evo_level:
                old_name = self.name
                self.name = evo_name
                self.hp += evo_stats["hp_bonus"]
                self.damage += evo_stats["damage_bonus"]
                print(colored_text(
                    f"{old_name} evolved into {self.name}!",
                    COLOR_RED
                ))
                del PET_EVOLUTIONS[old_name]

    def process_status_effects(self):
        for eff in self.status_effects[:]:
            eff.apply_effect(self)
            if eff.duration <= 0:
                self.status_effects.remove(eff)
