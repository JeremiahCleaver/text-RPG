# game/enemy.py
import random
from .data import ENEMY_TYPES, TYPE_WEAKNESSES, colored_text, COLOR_RED, COLOR_GREEN, COLOR_YELLOW
from .status_effect import StatusEffect

class Enemy:
    def __init__(self, type_key, turn):
        data = ENEMY_TYPES[type_key]
        self.name = data["name"]
        self.hp = data["base_hp"] + (turn * 5)
        self.attack = data["base_attack"] + (turn // 2)
        self.damage_type = data["damage_type"]
        self.gold_drop = data["gold_drop"] + (turn // 2)
        self.status_effects = []

    def is_alive(self):
        return self.hp > 0

    def take_damage(self, dmg):
        self.hp -= dmg
        return self.hp <= 0

    def on_defeated(self, player):
        player.gold += self.gold_drop
        print(colored_text(
            f"{player.name} looted {self.gold_drop} gold from {self.name}!",
            COLOR_YELLOW
        ))

    def process_status_effects(self):
        for eff in self.status_effects[:]:
            eff.apply_effect(self)
            if eff.duration <= 0:
                self.status_effects.remove(eff)
