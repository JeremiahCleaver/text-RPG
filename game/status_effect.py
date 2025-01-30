# game/status_effect.py
from .data import colored_text, COLOR_GREEN, COLOR_RED

class StatusEffect:
    def __init__(self, name, duration, effect_type, value=0):
        self.name = name
        self.duration = duration
        self.effect_type = effect_type  # "poison", "burn", "stun", "regen", etc.
        self.value = value

    def apply_effect(self, target):
        """Apply the effect each turn to 'target'."""
        if self.effect_type == "poison":
            target.hp -= self.value
            print(colored_text(
                f"{target.name} takes {self.value} poison damage! (HP: {target.hp})",
                COLOR_GREEN
            ))
        elif self.effect_type == "burn":
            target.hp -= self.value
            print(colored_text(
                f"{target.name} suffers {self.value} burn damage! (HP: {target.hp})",
                COLOR_RED
            ))
        elif self.effect_type == "regen":
            old_hp = target.hp
            target.hp += self.value
            print(colored_text(
                f"{target.name} regenerates {self.value} HP! (from {old_hp} to {target.hp})",
                COLOR_GREEN
            ))

        # Decrement duration
        self.duration -= 1
