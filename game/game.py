# game/game.py

import random
import json
import os

# Import global data
from .data import (
    colored_text, USE_TABULATE, tabulate,
    COLOR_RED, COLOR_GREEN, COLOR_YELLOW, COLOR_BLUE,
    AREA_DATA, RANDOM_EVENTS, SHOP_TIERS, CRAFTING_RECIPES, TYPE_WEAKNESSES,
)
from .player import Player
from .enemy import Enemy
from .companion import Companion
from .pet import Pet


class Game:
    def __init__(self):
        # Game state
        self.turn = 1
        self.player = None
        self.current_tier = 1
        self.shop_inventory = SHOP_TIERS[1][:]
        self.current_area = "Forest"
        self.current_enemies = []
        self.running = False  # track if the game is "active"

    # ------------------------------------------------------------------
    # 1) GAME START & MAIN LOOP-LIKE FUNCTIONS
    # ------------------------------------------------------------------

    def start_new_game(self, name: str, class_key: str) -> list[str]:
        """
        Creates a new game with the given player name and class_key (e.g. '1' => 'Warrior').
        Returns a list of log messages about what happened.
        """
        logs = []
        class_map = {"1": "Warrior", "2": "Mage", "3": "Thief", "4": "Cleric"}
        if class_key not in class_map:
            logs.append("Invalid class key. Cannot start new game.")
            return logs

        chosen_class = class_map[class_key]
        self.player = Player(name, chosen_class)
        self.turn = 1
        self.current_tier = 1
        self.shop_inventory = SHOP_TIERS[1][:]
        self.current_area = "Forest"
        self.running = True

        logs.append(colored_text(f"New Game Started!", COLOR_GREEN))
        logs.append(colored_text(f"Welcome, {name} the {chosen_class}!", COLOR_GREEN))
        logs.append("Type 'help' to see a list of commands.")
        return logs

    def is_game_over(self) -> bool:
        """
        Returns True if the game is no longer running (e.g. player died or forced exit).
        """
        if not self.running or not self.player:
            return True
        return not self.player.is_alive()

    def next_turn(self) -> list[str]:
        """
        Called each time we move to the next turn.  
        Returns log messages (like a turn header, random event, etc.).
        """
        logs = []
        if not self.player or not self.player.is_alive():
            self.running = False
            logs.append(colored_text("Game Over (player is dead or missing).", COLOR_RED))
            return logs

        logs.append(colored_text(f"\n===== Turn {self.turn} =====", COLOR_YELLOW))
        logs.extend(self.random_event_check())
        self.turn += 1

        # Check if we should unlock a new tier
        logs.extend(self.check_for_new_tier())
        return logs

    # ------------------------------------------------------------------
    # 2) RANDOM EVENTS
    # ------------------------------------------------------------------

    def random_event_check(self) -> list[str]:
        """
        30% chance of a random event. Returns logs describing the event.
        """
        logs = []
        if random.random() < 0.3:
            event = random.choice(RANDOM_EVENTS)
            logs.append(colored_text(event["text"], COLOR_GREEN))
            trigger = event["trigger"]
            if hasattr(self, trigger):
                # e.g. 'special_merchant', 'hidden_trap', 'gain_random_relic'
                # Each of these can be a method returning logs
                method = getattr(self, trigger)
                logs.extend(method())
        return logs

    def special_merchant(self) -> list[str]:
        """
        The merchant appears offering a secret potion for 30 gold.
        Returns logs. The actual yes/no choice is handled by a separate method:
        `merchant_buy_secret_potion()`.
        """
        logs = []
        logs.append("A special merchant appears, offering a secret potion for 30 gold.")
        logs.append("Use 'merchant_buy_secret_potion()' to buy or ignore otherwise.")
        return logs

    def merchant_buy_secret_potion(self) -> list[str]:
        """
        If the player decides to buy the secret potion from the merchant.
        """
        logs = []
        if self.player.gold >= 30:
            self.player.gold -= 30
            item = {
                "name": "Secret Potion",
                "type": "potion",
                "cost": 0,
                "heal": 150,
                "rarity": "Rare"
            }
            self.player.inventory.append(item)
            logs.append("You bought the secret potion!")
        else:
            logs.append("Not enough gold to buy the secret potion.")
        return logs

    def hidden_trap(self) -> list[str]:
        """
        The player steps into a hidden trap, losing 10 HP.
        """
        logs = []
        logs.append("A hidden trap triggers! You lose 10 HP.")
        self.player.hp -= 10
        if self.player.hp <= 0:
            logs.append("The trap proved fatal!")
            self.running = False
        return logs

    def gain_random_relic(self) -> list[str]:
        """
        The player gains a random relic from a traveler.
        """
        logs = []
        all_relics = []
        for tier_list in SHOP_TIERS.values():
            for it in tier_list:
                if it["type"] == "relic":
                    all_relics.append(it)
        if all_relics:
            relic = random.choice(all_relics).copy()
            self.player.inventory.append(relic)
            logs.append(f"You received {relic['name']}!")
        else:
            logs.append("No relic found (strange...).")
        return logs

    # ------------------------------------------------------------------
    # 3) AREA / TRAVEL
    # ------------------------------------------------------------------

    def show_area_info(self) -> list[str]:
        """
        Returns a list of areas and the current area.
        """
        logs = []
        logs.append("Areas you can travel to:")
        for area in AREA_DATA.keys():
            logs.append(f" - {area}")
        logs.append(f"Currently in: {self.current_area}")
        return logs

    def travel_to_area(self, area_name: str) -> list[str]:
        """
        Tries to move the player to another area. Returns logs.
        """
        logs = []
        if area_name in AREA_DATA:
            self.current_area = area_name
            logs.append(f"You travel to the {area_name}!")
        else:
            logs.append(f"'{area_name}' is not a valid area.")
        return logs

    # ------------------------------------------------------------------
    # 4) BATTLES
    # ------------------------------------------------------------------

    def normal_battle(self) -> list[str]:
        """
        Initiates a normal battle (non-boss). Returns logs of the encounter.
        """
        logs = []
        wave = self.get_enemy_wave()
        if not wave:
            logs.append("No enemies found in this area.")
            return logs

        logs.append("Enemies you face:")
        for e in wave:
            logs.append(f" - {e.name} (HP={e.hp}, ATK={e.attack}, Type={e.damage_type})")

        logs.extend(self.battle_enemies(wave))
        return logs

    def special_battle(self) -> list[str]:
        """
        Initiates a boss battle. Returns logs.
        """
        logs = []
        logs.append(colored_text("A special boss appears!", COLOR_RED))
        boss = Enemy("Boss Monster", self.turn)
        logs.extend(self.battle_enemies([boss]))
        return logs

    def get_enemy_wave(self) -> list[Enemy]:
        """
        Returns a list of enemies for a normal battle in the current area.
        """
        if self.current_area not in AREA_DATA:
            return []
        area_enemies = AREA_DATA[self.current_area]["enemies"]
        how_many = 2 if self.turn > 5 else 1
        wave = []
        for _ in range(how_many):
            chosen_type = random.choice(area_enemies)
            wave.append(Enemy(chosen_type, self.turn))
        return wave

    def battle_enemies(self, enemies: list[Enemy]) -> list[str]:
        """
        Simulate a single 'round' of battle with the given enemies.
        If you want turn-by-turn, you'd call separate methods like
        battle_action('attack'), etc. 
        For now, let's do a simplified single-round example.
        """
        logs = []
        self.current_enemies = enemies

        # Process existing status effects
        self.player.process_status_effects()
        for c in self.player.companions:
            c.process_status_effects()
        for p in self.player.pets:
            p.process_status_effects()
        for e in enemies:
            e.process_status_effects()

        # Quick example: Player party attacks the first alive enemy, 
        # then enemies attack back
        alive_list = [e for e in enemies if e.is_alive()]
        if not alive_list:
            logs.append("No alive enemies left.")
            return logs

        target = alive_list[0]
        logs.extend(self.party_attack(target))
        if not target.is_alive():
            logs.append(f"You defeated {target.name}!")
            target.on_defeated(self.player)
            self.distribute_xp(20)

        # Let enemies retaliate if they're still alive
        if any(e.is_alive() for e in enemies):
            logs.extend(self.enemies_attack(enemies))
            # Check if any remain
            if not any(e.is_alive() for e in enemies):
                logs.append(colored_text("All enemies are defeated!", COLOR_GREEN))
                self.distribute_xp(50)
        else:
            # If the target died and there are no more alive
            if not any(e.is_alive() for e in enemies):
                logs.append(colored_text("All enemies are defeated!", COLOR_GREEN))
                self.distribute_xp(50)

        # Check if player died
        if not self.player.is_alive():
            logs.append(colored_text("You have been defeated!", COLOR_RED))
            self.running = False

        return logs

    def party_attack(self, enemy: Enemy) -> list[str]:
        logs = []
        if self.player.is_alive() and enemy.is_alive():
            dmg = self.calculate_damage(self.player)
            logs.append(colored_text(f"{self.player.name} attacks {enemy.name}!", COLOR_YELLOW))
            if TYPE_WEAKNESSES.get(enemy.damage_type) == self.player.damage_type:
                dmg *= 2
                logs.append(colored_text("It's super effective!", COLOR_RED))
            enemy.take_damage(dmg)
            logs.append(colored_text(f"Damage dealt: {dmg} (Enemy HP: {enemy.hp})", COLOR_RED))

        # Companions
        for c in self.player.companions:
            if c.is_alive() and enemy.is_alive():
                base = c.strength + random.randint(0,3)
                if c.equipped_weapon:
                    base += c.equipped_weapon.get("damage",0)//2
                dmg = base
                if TYPE_WEAKNESSES.get(enemy.damage_type) == c.damage_type:
                    dmg *= 2
                    logs.append(colored_text(f"{c.name}'s attack is super effective!", COLOR_RED))
                enemy.take_damage(dmg)
                logs.append(f"{c.name} dealt {dmg} (Enemy HP: {enemy.hp})")

        # Pets
        for p in self.player.pets:
            if p.is_alive() and enemy.is_alive():
                dmg = p.damage
                if p.equipped_weapon:
                    dmg += p.equipped_weapon.get("damage",0)//2
                if TYPE_WEAKNESSES.get(enemy.damage_type) == p.damage_type:
                    dmg *= 2
                    logs.append(colored_text(f"{p.name}'s attack is super effective!", COLOR_RED))
                enemy.take_damage(dmg)
                logs.append(f"{p.name} dealt {dmg} (Enemy HP: {enemy.hp})")

        return logs

    def enemies_attack(self, enemies: list[Enemy]) -> list[str]:
        logs = []
        for e in enemies:
            if e.is_alive():
                # pick a random living target
                living_targets = []
                if self.player.is_alive():
                    living_targets.append(self.player)
                living_targets.extend([c for c in self.player.companions if c.is_alive()])
                living_targets.extend([p for p in self.player.pets if p.is_alive()])

                if not living_targets:
                    logs.append("All party members have fallen.")
                    self.running = False
                    return logs

                target = random.choice(living_targets)
                dmg = e.attack
                t_type = getattr(target, 'damage_type', 'Physical')
                if TYPE_WEAKNESSES.get(t_type) == e.damage_type:
                    dmg *= 2
                    logs.append(colored_text(f"{e.name}'s attack is super effective vs {t_type}!", COLOR_RED))

                target.hp -= dmg
                logs.append(colored_text(f"{e.name} hits {target.name} for {dmg}! (HP: {target.hp})", COLOR_RED))
                if target.hp <= 0:
                    logs.append(colored_text(f"{target.name} has fallen!", COLOR_RED))
        return logs

    def calculate_damage(self, entity) -> int:
        """
        Helper to calculate base damage for a Player/Companion/Pet. 
        """
        base = 5
        if hasattr(entity, 'stats'):
            base = entity.stats.get("Strength", 5)
            if entity.equipped_weapon:
                base += entity.equipped_weapon.get("damage", 0)
        return base

    def distribute_xp(self, amount: int) -> None:
        """
        Distribute XP to player, companions, and pets.
        """
        if not self.player:
            return
        self.player.gain_xp(amount)
        for c in self.player.companions:
            if c.is_alive():
                c.gain_xp(amount)
        for p in self.player.pets:
            if p.is_alive():
                p.gain_xp(amount)

    # ------------------------------------------------------------------
    # 5) SKILLS
    # ------------------------------------------------------------------

    def use_skill(self, skill_index: int) -> list[str]:
        """
        Use one of the player's skills by index.
        Returns logs describing the outcome.
        """
        logs = []
        if not self.player or not self.player.skills:
            logs.append("You have no skills to use!")
            return logs
        if skill_index < 0 or skill_index >= len(self.player.skills):
            logs.append("Invalid skill index.")
            return logs

        from .data import SKILLS
        skill_name = self.player.skills[skill_index]
        skill_data = SKILLS[skill_name]

        if self.player.mana < skill_data["mana_cost"]:
            logs.append("Not enough mana!")
            return logs

        self.player.mana -= skill_data["mana_cost"]

        # Must have enemies to use skill on
        alive_enemies = [e for e in self.current_enemies if e.is_alive()]
        if not alive_enemies:
            logs.append("No enemies available!")
            return logs

        # Attack the first enemy, or let the UI pass an enemy index, etc.
        target = alive_enemies[0]
        dmg = self.calculate_damage(self.player)
        dmg = int(dmg * skill_data["damage_multiplier"])

        logs.append(colored_text(f"{self.player.name} uses {skill_name} on {target.name}!", COLOR_YELLOW))
        target.take_damage(dmg)
        logs.append(f"It dealt {dmg} damage. (Enemy HP: {target.hp})")

        if not target.is_alive():
            logs.append(colored_text(f"{target.name} was defeated!", COLOR_GREEN))
            target.on_defeated(self.player)
            self.distribute_xp(20)

        return logs

    # ------------------------------------------------------------------
    # 6) AUTO-EQUIP & INVENTORY
    # ------------------------------------------------------------------

    def can_equip(self, entity, item: dict) -> bool:
        """
        Checks if the given entity (Player/Companion/Pet) can equip this item.
        """
        if item.get("pet_only", False) and not isinstance(entity, Pet):
            return False
        if item.get("companion_only", False) and not isinstance(entity, Companion):
            return False
        if "class_req" in item:
            # If entity is a Player
            if isinstance(entity, Player):
                if entity.player_class not in item["class_req"]:
                    return False
            else:
                return False
        return True

    def auto_equip_all(self) -> list[str]:
        logs = []
        logs.extend(self.auto_equip_character(self.player))
        for c in self.player.companions:
            logs.extend(self.auto_equip_character(c))
        for p in self.player.pets:
            logs.extend(self.auto_equip_character(p))
        return logs

    def auto_equip_character(self, entity) -> list[str]:
        """
        Removes currently equipped items (put back into player inventory),
        then tries to equip the best weapon/armor/relic from inventory.
        Returns a list of log messages.
        """
        logs = []
        # Move old gear to inventory
        if entity.equipped_weapon:
            self.player.inventory.append(entity.equipped_weapon)
            entity.equipped_weapon = None
        if entity.equipped_armor:
            self.player.inventory.append(entity.equipped_armor)
            entity.equipped_armor = None
        if entity.equipped_relic:
            self.player.inventory.append(entity.equipped_relic)
            entity.equipped_relic = None

        # Best weapon
        best_wpn = None
        best_val = -1
        best_idx = -1
        for i, it in enumerate(self.player.inventory):
            if it["type"] == "weapon" and self.can_equip(entity, it):
                dmg = it.get("damage", 0)
                if dmg > best_val:
                    best_val = dmg
                    best_wpn = it
                    best_idx = i
        if best_wpn:
            entity.equipped_weapon = best_wpn
            self.player.inventory.pop(best_idx)
            logs.append(f"{entity.name} auto-equipped weapon: {best_wpn['name']}")

        # Best armor
        best_arm = None
        best_val = -1
        best_idx = -1
        for i, it in enumerate(self.player.inventory):
            if it["type"] == "armor" and self.can_equip(entity, it):
                dfs = it.get("defense", 0)
                if dfs > best_val:
                    best_val = dfs
                    best_arm = it
                    best_idx = i
        if best_arm:
            entity.equipped_armor = best_arm
            self.player.inventory.pop(best_idx)
            logs.append(f"{entity.name} auto-equipped armor: {best_arm['name']}")

        # Best relic
        best_rlc = None
        best_val = -1
        best_idx = -1
        for i, it in enumerate(self.player.inventory):
            if it["type"] == "relic" and self.can_equip(entity, it):
                cost_val = it.get("cost", 0)
                if cost_val > best_val:
                    best_val = cost_val
                    best_rlc = it
                    best_idx = i
        if best_rlc:
            entity.equipped_relic = best_rlc
            self.player.inventory.pop(best_idx)
            logs.append(f"{entity.name} auto-equipped relic: {best_rlc['name']}")

        return logs

    def use_item(self, item_index: int) -> list[str]:
        """
        Use an item in the player's inventory by index (if it's a potion, ring, etc.).
        Returns logs describing what happened.
        """
        logs = []
        usable_items = [i for i in self.player.inventory if i["type"] in ["potion", "scroll", "ring"]]

        if item_index < 0 or item_index >= len(usable_items):
            logs.append("Invalid item choice.")
            return logs

        selected = usable_items[item_index]
        # We need to remove it from player.inventory properly
        # i.e., find it by reference in the main inventory list
        # not just by the sub-slice index
        actual_idx = self.player.inventory.index(selected)

        if selected["type"] == "potion" and "heal" in selected:
            max_hp = 100 + 10 * (self.player.level - 1)
            old_hp = self.player.hp
            self.player.hp = min(self.player.hp + selected["heal"], max_hp)
            logs.append(colored_text(f"You used {selected['name']} and healed from {old_hp} to {self.player.hp} HP!", COLOR_GREEN))
            self.player.inventory.pop(actual_idx)

        elif selected["type"] == "scroll" and "effect" in selected:
            logs.append(f"You used {selected['name']} and activated its effect: {selected['effect']}!")
            self.player.inventory.pop(actual_idx)

        elif selected["type"] == "ring" and "effect" in selected:
            logs.append(f"You equipped {selected['name']} and gained its effect: {selected['effect']}!")
            self.player.inventory.pop(actual_idx)

        else:
            logs.append("This item cannot be used right now.")
        return logs

    # ------------------------------------------------------------------
    # 7) SHOP & ECONOMY
    # ------------------------------------------------------------------

    def list_shop_inventory(self) -> list[str]:
        """
        Return logs describing the items in the current shop_inventory.
        """
        logs = []
        if not self.shop_inventory:
            logs.append("Shop is empty!")
            return logs

        logs.append("--- Shop Inventory ---")
        for i, it in enumerate(self.shop_inventory, start=1):
            r = it.get("rarity", "Common")
            logs.append(f"{i}. {it['name']} [{r}] (Type={it['type']}, Cost={it['cost']})")
        return logs

    def buy_item_from_shop(self, index: int) -> list[str]:
        """
        Attempt to buy an item from shop_inventory by index (1-based).
        """
        logs = []
        idx = index - 1
        if idx < 0 or idx >= len(self.shop_inventory):
            logs.append("Invalid shop item number.")
            return logs

        selected = self.shop_inventory[idx]
        if self.player.gold >= selected["cost"]:
            self.player.gold -= selected["cost"]
            self.player.inventory.append(selected)
            logs.append(colored_text(f"You bought {selected['name']}!", COLOR_GREEN))
        else:
            logs.append(f"Not enough gold! (You have {self.player.gold})")

        return logs

    def list_player_inventory(self) -> list[str]:
        """
        Return lines describing the items in the player's inventory.
        """
        logs = []
        if not self.player.inventory:
            logs.append("Your inventory is empty.")
            return logs

        logs.append("--- Your Inventory ---")
        for i, it in enumerate(self.player.inventory, start=1):
            half = it["cost"] // 2
            r = it.get("rarity", "Common")
            logs.append(f"{i}. {it['name']} [{r}] => Sell value ~ {half} gold")
        return logs

    def sell_item(self, index: int) -> list[str]:
        """
        Sell an item from the player's inventory (1-based index).
        """
        logs = []
        idx = index - 1
        if idx < 0 or idx >= len(self.player.inventory):
            logs.append("Invalid item choice.")
            return logs

        sel = self.player.inventory[idx]
        sp = sel["cost"] // 2
        self.player.gold += sp
        self.player.inventory.remove(sel)
        logs.append(colored_text(f"Sold {sel['name']} for {sp} gold!", COLOR_GREEN))
        return logs

    def hire_companion(self, choice_key: str) -> list[str]:
        """
        Attempt to hire a companion at the current tier. 
        choice_key is '1', '2', or '3' for available companion types.
        """
        logs = []
        cost = 150 * self.current_tier
        if self.player.gold < cost:
            logs.append("Not enough gold to hire companion.")
            return logs

        c_types = {
            "1": {
                "name": "Swordsman",
                "hp": 60 + (10*self.current_tier),
                "strength": 7 + self.current_tier,
                "magic": 0,
                "agility": 3 + self.current_tier,
                "damage_type": "Physical"
            },
            "2": {
                "name": "Archer",
                "hp": 50 + (10*self.current_tier),
                "strength": 5 + self.current_tier,
                "magic": 0,
                "agility": 7 + self.current_tier,
                "damage_type": "Physical"
            },
            "3": {
                "name": "Mage",
                "hp": 40 + (10*self.current_tier),
                "strength": 2 + self.current_tier,
                "magic": 10 + self.current_tier,
                "agility": 5 + self.current_tier,
                "damage_type": "Arcane"
            },
        }
        if choice_key not in c_types:
            logs.append("Invalid companion choice.")
            return logs

        data = c_types[choice_key]
        import random
        comp_name = random.choice(["Arthur", "Lancelot", "Guinevere", "Robin"])
        c = Companion(
            comp_name,
            data["hp"],
            data["strength"],
            data["magic"],
            data["agility"],
            data["damage_type"]
        )
        self.player.companions.append(c)
        self.player.gold -= cost
        logs.append(colored_text(f"You hired {c.name} the {data['name']}!", COLOR_GREEN))
        return logs

    def hire_pet(self, choice_key: str) -> list[str]:
        """
        Attempt to hire a pet at the current tier.
        """
        logs = []
        cost = 80 * self.current_tier
        if self.player.gold < cost:
            logs.append("Not enough gold to hire a pet.")
            return logs

        pet_list = {
            "1": {"name": "Fluffy Rabbit", "hp": 30 + (5*self.current_tier), "damage": 3 + self.current_tier, "type": "Physical"},
            "2": {"name": "Fire Lizard",   "hp": 35 + (5*self.current_tier), "damage": 5 + self.current_tier, "type": "Arcane"},
            "3": {"name": "Shadow Wolf",   "hp": 40 + (5*self.current_tier), "damage": 7 + self.current_tier, "type": "Poison"},
        }
        if choice_key not in pet_list:
            logs.append("Invalid pet choice.")
            return logs

        data = pet_list[choice_key]
        import random
        p_name = random.choice(["Fluffy", "Spike", "Shadow", "Ziggy"])
        newp = Pet(p_name, data["hp"], 100, data["damage"], data["type"])
        self.player.pets.append(newp)
        self.player.gold -= cost
        logs.append(colored_text(f"You hired {newp.name} the {data['name']}!", COLOR_GREEN))
        return logs

    def cheat_code(self, code: str) -> list[str]:
        """
        Process a cheat code. Return logs of what happened.
        """
        logs = []
        code = code.lower()
        if code == "satoshi":
            self.player.gold += 1000
            logs.append(colored_text("Cheat activated! +1000 Gold.", COLOR_YELLOW))
        elif code == "trump":
            self.player.hp = 1000
            self.player.stats["Strength"] = 1000
            logs.append(colored_text("Cheat activated! HP and Strength maxed out!", COLOR_YELLOW))
        else:
            logs.append("Invalid cheat code.")
        return logs

    # ------------------------------------------------------------------
    # 8) TIERS, SAVING, LOADING
    # ------------------------------------------------------------------

    def check_for_new_tier(self) -> list[str]:
        logs = []
        next_tier = self.current_tier + 1
        needed = 10 * self.current_tier
        if self.turn >= needed and next_tier in SHOP_TIERS:
            self.current_tier = next_tier
            self.shop_inventory = SHOP_TIERS[next_tier][:]
            logs.append(colored_text(f"*** Tier {next_tier} Items Unlocked! ***", COLOR_YELLOW))
        return logs

    def save_game_slot(self, slot: str) -> list[str]:
        """
        Save the current game state to 'savegame_{slot}.json'.
        Returns logs about success/failure.
        """
        logs = []
        if slot not in ["1", "2", "3"]:
            logs.append("Invalid save slot. Must be '1','2', or '3'.")
            return logs

        filename = f"savegame_{slot}.json"
        data = {
            "turn": self.turn,
            "current_tier": self.current_tier,
            "current_area": self.current_area,
            "player": self.player.to_dict() if self.player else None,
            "shop_inventory": self.shop_inventory
        }
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
        logs.append(colored_text(f"Game saved to {filename}!", COLOR_GREEN))
        return logs

    def load_game_slot(self, slot: str) -> list[str]:
        """
        Load the game state from 'savegame_{slot}.json'.
        Returns logs about success/failure.
        """
        logs = []
        if slot not in ["1", "2", "3"]:
            logs.append("Invalid load slot. Must be '1','2', or '3'.")
            return logs

        filename = f"savegame_{slot}.json"
        if not os.path.exists(filename):
            logs.append(f"No save file at {filename}.")
            return logs

        with open(filename, "r") as f:
            data = json.load(f)
        self.turn = data["turn"]
        self.current_tier = data["current_tier"]
        self.current_area = data.get("current_area", "Forest")
        if data["player"]:
            self.player = Player.from_dict(data["player"])
        else:
            self.player = None
        self.shop_inventory = data.get("shop_inventory", [])
        self.running = True if self.player and self.player.is_alive() else False

        logs.append(colored_text(f"Game loaded from {filename}!", COLOR_GREEN))
        return logs

    # ------------------------------------------------------------------
    # 9) CRAFTING
    # ------------------------------------------------------------------

    def list_crafting_recipes(self) -> list[str]:
        """
        Return logs listing all crafting recipes.
        """
        logs = []
        logs.append("=== Crafting Recipes ===")
        i = 1
        for rname, rdata in CRAFTING_RECIPES.items():
            ing_str = ", ".join(f"{k}x{v}" for k,v in rdata["ingredients"].items())
            logs.append(f"{i}. {rname} => requires {ing_str}")
            i += 1
        return logs

    def craft_item_by_name(self, recipe_name: str) -> list[str]:
        """
        Attempt to craft the given recipe_name. Returns logs.
        """
        logs = []
        if recipe_name not in CRAFTING_RECIPES:
            logs.append(f"No such recipe: {recipe_name}")
            return logs

        recipe = CRAFTING_RECIPES[recipe_name]
        if not self.can_craft(recipe):
            logs.append("You lack the required materials.")
            return logs

        logs.extend(self.do_craft(recipe))
        return logs

    def can_craft(self, recipe: dict) -> bool:
        needed = recipe["ingredients"]
        inv_mats = {}
        for it in self.player.inventory:
            if it["type"] == "material":
                nm = it["name"]
                inv_mats[nm] = inv_mats.get(nm, 0) + 1
        for k, v in needed.items():
            if inv_mats.get(k, 0) < v:
                return False
        return True

    def do_craft(self, recipe: dict) -> list[str]:
        """
        Remove required materials from inventory and add the result item.
        """
        logs = []
        needed = recipe["ingredients"]
        for mat, count_needed in needed.items():
            removed = 0
            idx = 0
            while removed < count_needed and idx < len(self.player.inventory):
                it = self.player.inventory[idx]
                if it["type"] == "material" and it["name"] == mat:
                    self.player.inventory.pop(idx)
                    removed += 1
                else:
                    idx += 1

        result = recipe["result"].copy()
        self.player.inventory.append(result)
        logs.append(colored_text(f"You crafted {result['name']}!", COLOR_GREEN))
        return logs

    # ------------------------------------------------------------------
    # 10) SORTING / HELP
    # ------------------------------------------------------------------

    def sort_inventory(self, criterion: str) -> list[str]:
        """
        Sort the player's inventory by one of: 'type', 'rarity', or 'name'.
        Returns logs about the sort.
        """
        logs = []
        if criterion == "type":
            self.player.inventory.sort(key=lambda i: i["type"])
            logs.append("Inventory sorted by item type.")
        elif criterion == "rarity":
            rarity_order = {"Common":1,"Uncommon":2,"Rare":3,"Epic":4,"Legendary":5}
            self.player.inventory.sort(key=lambda i: rarity_order.get(i.get("rarity","Common"),1))
            logs.append("Inventory sorted by rarity.")
        elif criterion == "name":
            self.player.inventory.sort(key=lambda i: i["name"])
            logs.append("Inventory sorted by name.")
        else:
            logs.append("Invalid sort criterion.")
        return logs

    def show_help(self) -> list[str]:
        """
        Return a list of strings describing possible commands.
        """
        logs = []
        logs.append(colored_text("=== GAME HELP ===", COLOR_BLUE))
        logs.append("Commands you might implement in a UI:")
        logs.append(" - help : Show this help text.")
        logs.append(" - stats : Show character stats.")
        logs.append(" - area : Show/Travel to areas.")
        logs.append(" - shop : Open shop menu (buy, sell, hire).")
        logs.append(" - battle : Start a fight (normal or special).")
        logs.append(" - skill X : Use skill #X.")
        logs.append(" - item X : Use item #X (potion, scroll, ring).")
        logs.append(" - craft 'RecipeName' : Craft an item if you have mats.")
        logs.append(" - cheat 'code' : Use a cheat code.")
        logs.append(" - save [1-3], load [1-3].")
        logs.append(" - end_turn : Move to next turn.")
        return logs

    # ------------------------------------------------------------------
    # 11) DISPLAY STATS
    # ------------------------------------------------------------------

    def display_stats_table(self) -> list[str]:
        """
        Return a list of strings containing a table of the player's party stats.
        """
        logs = []
        if not self.player:
            logs.append("No player found.")
            return logs

        headers = [
            "Name", "Class/Type", "HP", "Strength",
            "Magic", "Agility", "Level", "XP",
            "Weapon", "Armor", "Relic"
        ]
        table_data = []

        # Player row
        wpn = self.player.equipped_weapon["name"] if self.player.equipped_weapon else "None"
        arm = self.player.equipped_armor["name"] if self.player.equipped_armor else "None"
        rlc = self.player.equipped_relic["name"] if self.player.equipped_relic else "None"
        table_data.append([
            self.player.name,
            self.player.player_class,
            self.player.hp,
            self.player.stats["Strength"],
            self.player.stats["Magic"],
            self.player.stats["Agility"],
            self.player.level,
            self.player.xp,
            wpn, arm, rlc
        ])

        # Companions
        for c in self.player.companions:
            if c.is_alive():
                wpn_c = c.equipped_weapon["name"] if c.equipped_weapon else "None"
                arm_c = c.equipped_armor["name"] if c.equipped_armor else "None"
                rlc_c = c.equipped_relic["name"] if c.equipped_relic else "None"
                table_data.append([
                    c.name,
                    f"Companion ({c.damage_type})",
                    c.hp,
                    c.strength,
                    c.magic,
                    c.agility,
                    c.level,
                    c.xp,
                    wpn_c, arm_c, rlc_c
                ])

        # Pets
        for p in self.player.pets:
            if p.is_alive():
                wpn_p = p.equipped_weapon["name"] if p.equipped_weapon else "None"
                arm_p = p.equipped_armor["name"] if p.equipped_armor else "None"
                rlc_p = p.equipped_relic["name"] if p.equipped_relic else "None"
                # pets don't have separate STR, MAG, AGI
                table_data.append([
                    p.name,
                    f"Pet ({p.damage_type})",
                    p.hp,
                    "-", "-", "-",
                    p.level,
                    p.xp,
                    wpn_p, arm_p, rlc_p
                ])

        if USE_TABULATE and tabulate:
            table_str = tabulate(table_data, headers=headers, tablefmt="fancy_grid")
            logs.append(table_str)
        else:
            hline = " | ".join(headers)
            logs.append(hline)
            logs.append("-" * len(hline))
            for row in table_data:
                logs.append(" | ".join(str(x) for x in row))

        return logs
