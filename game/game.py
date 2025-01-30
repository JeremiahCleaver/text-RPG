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
# Import your classes
from .player import Player
from .enemy import Enemy
from .companion import Companion
from .pet import Pet

class Game:
    def __init__(self, input_func=None):
        self.turn = 1
        self.player = None
        self.input_func = input_func if input_func else input
        self.current_tier = 1
        self.shop_inventory = SHOP_TIERS[1][:]
        self.current_area = "Forest"  # default area
        self.current_enemies = []

    def start(self):
        print("Welcome to the RPG Adventure!")
        print("1) New Game\n2) Load Game")
        while True:
            choice = self.input_func("Enter choice (1 or 2): ").strip()
            if choice == "1":
                self.start_new_game()
                return
            elif choice == "2":
                self.load_game_slot()
                if self.player:
                    self.main_loop()
                return
            else:
                print("Invalid choice.")

    def start_new_game(self):
        name = self.input_func("Enter your character's name: ").strip()
        class_map = {"1": "Warrior", "2": "Mage", "3": "Thief", "4": "Cleric"}

        player_class = ""
        while player_class not in class_map:
            player_class = self.input_func(
                "Choose your class (1: Warrior, 2: Mage, 3: Thief, 4: Cleric): "
            ).strip()
            if player_class not in class_map:
                print("Invalid choice.")

        self.player = Player(name, class_map[player_class])
        self.main_loop()

    def main_loop(self):
        while self.player and self.player.is_alive():
            print(colored_text(f"\n===== Turn {self.turn} =====", COLOR_YELLOW))
            self.random_event_check()
            self.choose_area_menu()
            self.display_stats_table()

            self.check_for_new_tier()

            if self.turn % 10 == 0:
                self.special_battle()
            else:
                self.normal_battle()

            if not self.player.is_alive():
                break

            # Auto-equip
            self.auto_equip_character(self.player)
            for c in self.player.companions:
                self.auto_equip_character(c)
            for p in self.player.pets:
                self.auto_equip_character(p)

            # Shop
            self.shop_menu()
            if not self.player.is_alive():
                break

            print(colored_text("\n--- End of Turn Stats ---", COLOR_BLUE))
            self.display_stats_table()

            self.input_func("Press Enter to proceed to the next turn...")
            self.turn += 1

        print(colored_text("Game Over! Restarting game...", COLOR_RED))
        self.__init__(input_func=self.input_func)
        self.start()

    ########################################
    #   Display Stats Table
    ########################################
    def display_stats_table(self):
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
                wpn = c.equipped_weapon["name"] if c.equipped_weapon else "None"
                arm = c.equipped_armor["name"] if c.equipped_armor else "None"
                rlc = c.equipped_relic["name"] if c.equipped_relic else "None"
                table_data.append([
                    c.name,
                    f"Companion ({c.damage_type})",
                    c.hp,
                    c.strength,
                    c.magic,
                    c.agility,
                    c.level,
                    c.xp,
                    wpn, arm, rlc
                ])

        # Pets
        for p in self.player.pets:
            if p.is_alive():
                wpn = p.equipped_weapon["name"] if p.equipped_weapon else "None"
                arm = p.equipped_armor["name"] if p.equipped_armor else "None"
                rlc = p.equipped_relic["name"] if p.equipped_relic else "None"
                table_data.append([
                    p.name,
                    f"Pet ({p.damage_type})",
                    p.hp,
                    "-", "-", "-",  # No separate STR, MAG, AGI
                    p.level,
                    p.xp,
                    wpn, arm, rlc
                ])

        if USE_TABULATE and tabulate:
            print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
        else:
            # Fallback if tabulate not installed
            hline = " | ".join(headers)
            print(hline)
            print("-"*len(hline))
            for row in table_data:
                print(" | ".join(str(x) for x in row))
        print()

    ########################################
    #   Random Events
    ########################################
    def random_event_check(self):
        if random.random() < 0.3:
            from .data import RANDOM_EVENTS
            event = random.choice(RANDOM_EVENTS)
            print(colored_text(event["text"], COLOR_GREEN))
            if hasattr(self, event["trigger"]):
                getattr(self, event["trigger"])()

    def special_merchant(self):
        print("He offers you 'Super Secret Potion' for 30 gold. Buy? (y/n)")
        choice = self.input_func("> ").strip().lower()
        if choice == 'y':
            if self.player.gold >= 30:
                self.player.gold -= 30
                item = {
                    "name":"Secret Potion",
                    "type":"potion",
                    "cost":0,
                    "heal":150,
                    "rarity":"Rare"
                }
                self.player.inventory.append(item)
                print("You bought the secret potion!")
            else:
                print("Not enough gold.")
        else:
            print("You decline.")

    def hidden_trap(self):
        print("You lost 10 HP!")
        self.player.hp -= 10

    def gain_random_relic(self):
        all_relics = []
        for tier_list in SHOP_TIERS.values():
            for it in tier_list:
                if it["type"] == "relic":
                    all_relics.append(it)
        if all_relics:
            relic = random.choice(all_relics).copy()
            self.player.inventory.append(relic)
            print(f"You received {relic['name']}!")
        else:
            print("No relic found.")

    ########################################
    #   Area Selection
    ########################################
    def choose_area_menu(self):
        from .data import AREA_DATA
        print("\nCurrent area:", self.current_area)
        print("1) Stay in current area")
        print("2) Travel to a different area")
        choice = self.input_func("> ").strip()
        if choice == "2":
            areas = list(AREA_DATA.keys())
            for i, ar in enumerate(areas, start=1):
                print(f"{i}. {ar}")
            sel = self.input_func("Pick area # or 'back': ").strip()
            if sel.lower() == "back":
                return
            if sel.isdigit():
                idx = int(sel)-1
                if 0 <= idx < len(areas):
                    self.current_area = areas[idx]
                    print(f"You travel to the {self.current_area}!")

    ########################################
    #   Battles
    ########################################
    def special_battle(self):
        print(colored_text("\nA special boss appears!", COLOR_RED))
        boss = Enemy("Boss Monster", self.turn)
        self.battle_enemies([boss])

    def normal_battle(self):
        wave = self.get_enemy_wave()
        if not wave:
            print("No enemies found here.")
            return
        print("\nEnemies you face:")
        for e in wave:
            print(f" - {e.name} (HP={e.hp}, ATK={e.attack}, Type={e.damage_type})")
        self.battle_enemies(wave)

    def get_enemy_wave(self):
        from .data import AREA_DATA
        if self.current_area not in AREA_DATA:
            return []
        area_enemies = AREA_DATA[self.current_area]["enemies"]
        how_many = 2 if self.turn > 5 else 1
        wave = []
        for _ in range(how_many):
            chosen = random.choice(area_enemies)
            wave.append(Enemy(chosen, self.turn))
        return wave

    def battle_enemies(self, enemies):
        self.current_enemies = enemies
        while any(e.is_alive() for e in enemies) and self.player.is_alive():
            # Process ongoing status each round
            self.player.process_status_effects()
            for c in self.player.companions:
                c.process_status_effects()
            for p in self.player.pets:
                p.process_status_effects()
            for e in enemies:
                e.process_status_effects()

            alive_list = [e for e in enemies if e.is_alive()]
            if not alive_list:
                break

            print("\nEnemies present:")
            for idx, e in enumerate(alive_list, start=1):
                print(f"  {idx}) {e.name} (HP={e.hp})")

            action = self.input_func("\n1: Attack | 2: Use Skill | 3: Use Item | 4: Flee: ").strip()
            if action == "1":
                target = self.choose_enemy(alive_list)
                if target:
                    self.party_attack(target)
                    if not target.is_alive():
                        print(f"\nYou defeated {target.name}!")
                        target.on_defeated(self.player)
                        self.distribute_xp(20)
                self.enemies_attack(enemies)

            elif action == "2":
                self.use_skill()
                self.enemies_attack(enemies)

            elif action == "3":
                self.use_item()
                self.enemies_attack(enemies)

            elif action == "4":
                print("You fled!")
                return
            else:
                print("Invalid input.")

        if any(e.is_alive() for e in enemies):
            print(colored_text("\n*** You have been defeated! ***", COLOR_RED))
        else:
            print(colored_text("\nAll enemies are defeated!", COLOR_GREEN))
            self.distribute_xp(50)

    def choose_enemy(self, alive_enemies):
        if not alive_enemies:
            return None
        if len(alive_enemies) == 1:
            return alive_enemies[0]
        choice = self.input_func("Choose an enemy # to attack: ").strip()
        if not choice.isdigit():
            return alive_enemies[0]
        idx = int(choice)-1
        if idx < 0 or idx >= len(alive_enemies):
            return alive_enemies[0]
        return alive_enemies[idx]

    def party_attack(self, enemy):
        from .data import TYPE_WEAKNESSES, colored_text, COLOR_YELLOW, COLOR_RED
        # Player
        if self.player.is_alive() and enemy.is_alive():
            dmg = self.calculate_damage(self.player)
            print(colored_text(f"{self.player.name} attacks {enemy.name}!", COLOR_YELLOW))
            if TYPE_WEAKNESSES.get(enemy.damage_type) == self.player.damage_type:
                dmg *= 2
                print(colored_text("It's super effective!", COLOR_RED))
            enemy.take_damage(dmg)
            print(colored_text(f"Damage dealt: {dmg} (Enemy HP: {enemy.hp})", COLOR_RED))

        # Companions
        for c in self.player.companions:
            if c.is_alive() and enemy.is_alive():
                base = c.strength + random.randint(0,3)
                if c.equipped_weapon:
                    base += c.equipped_weapon.get("damage",0)//2
                dmg = base
                if TYPE_WEAKNESSES.get(enemy.damage_type) == c.damage_type:
                    dmg *= 2
                    print(colored_text(f"{c.name}'s attack is super effective!", COLOR_RED))
                enemy.take_damage(dmg)
                print(f"{c.name} dealt {dmg} (Enemy HP: {enemy.hp})")

        # Pets
        for p in self.player.pets:
            if p.is_alive() and enemy.is_alive():
                dmg = p.damage
                if p.equipped_weapon:
                    dmg += p.equipped_weapon.get("damage",0)//2
                if TYPE_WEAKNESSES.get(enemy.damage_type) == p.damage_type:
                    dmg *= 2
                    print(colored_text(f"{p.name}'s pet attack is super effective!", COLOR_RED))
                enemy.take_damage(dmg)
                print(f"{p.name} dealt {dmg} (Enemy HP: {enemy.hp})")

    def calculate_damage(self, entity):
        base = 5
        if hasattr(entity, 'stats'):
            base = entity.stats.get("Strength", 5)
            if entity.equipped_weapon:
                base += entity.equipped_weapon.get("damage", 0)
        return base

    def enemies_attack(self, enemies):
        from .data import TYPE_WEAKNESSES, colored_text, COLOR_RED
        for e in enemies:
            if e.is_alive():
                living_targets = []
                if self.player.is_alive():
                    living_targets.append(self.player)
                for c in self.player.companions:
                    if c.is_alive():
                        living_targets.append(c)
                for p in self.player.pets:
                    if p.is_alive():
                        living_targets.append(p)

                if not living_targets:
                    return

                target = random.choice(living_targets)
                dmg = e.attack
                t_type = getattr(target, 'damage_type', 'Physical')
                if TYPE_WEAKNESSES.get(t_type) == e.damage_type:
                    dmg *= 2
                    print(colored_text(
                        f"{e.name}'s attack is super effective vs {t_type}!",
                        COLOR_RED
                    ))

                target.hp -= dmg
                print(colored_text(
                    f"{e.name} hits {target.name} for {dmg}! (HP: {target.hp})",
                    COLOR_RED
                ))
                if target.hp <= 0:
                    print(colored_text(f"{target.name} has fallen!", COLOR_RED))

    def distribute_xp(self, amount):
        self.player.gain_xp(amount)
        for c in self.player.companions:
            if c.is_alive():
                c.gain_xp(amount)
        for p in self.player.pets:
            if p.is_alive():
                p.gain_xp(amount)

    ########################################
    #   Skills
    ########################################
    def use_skill(self):
        from .data import SKILLS, colored_text, COLOR_YELLOW, COLOR_GREEN
        if not self.player.skills:
            print("You have no skills to use!")
            return
        print("\nYour Skills:")
        for i, sname in enumerate(self.player.skills, start=1):
            info = SKILLS[sname]
            print(f"{i}. {sname} - {info['description']} (mana cost={info['mana_cost']})")

        choice = self.input_func("Choose # or 'back': ").strip()
        if choice.lower() == 'back':
            return
        if not choice.isdigit():
            print("Invalid choice.")
            return
        idx = int(choice)-1
        if idx < 0 or idx >= len(self.player.skills):
            print("Invalid skill choice.")
            return

        skill_name = self.player.skills[idx]
        skill_data = SKILLS[skill_name]

        if self.player.mana < skill_data["mana_cost"]:
            print("Not enough mana!")
            return
        self.player.mana -= skill_data["mana_cost"]

        alive_enemies = [e for e in self.current_enemies if e.is_alive()]
        if not alive_enemies:
            print("No enemies available!")
            return
        target = self.choose_enemy(alive_enemies)
        if not target:
            return

        dmg = self.calculate_damage(self.player)
        dmg = int(dmg * skill_data["damage_multiplier"])

        print(colored_text(f"{self.player.name} uses {skill_name} on {target.name}!", COLOR_YELLOW))
        target.take_damage(dmg)
        print(f"It dealt {dmg} damage. (Enemy HP: {target.hp})")
        if not target.is_alive():
            print(colored_text(f"{target.name} was defeated!", COLOR_GREEN))
            target.on_defeated(self.player)
            self.distribute_xp(20)

    ########################################
    #   Auto-Equip
    ########################################
    def can_equip(self, entity, item):
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

    def auto_equip_character(self, entity):
        # Move old gear back to inventory
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
                dmg = it.get("damage",0)
                if dmg > best_val:
                    best_val = dmg
                    best_wpn = it
                    best_idx = i
        if best_wpn:
            entity.equipped_weapon = best_wpn
            self.player.inventory.pop(best_idx)
            print(f"{entity.name} auto-equipped weapon: {best_wpn['name']}")

        # Best armor
        best_arm = None
        best_val = -1
        best_idx = -1
        for i, it in enumerate(self.player.inventory):
            if it["type"]=="armor" and self.can_equip(entity, it):
                dfs = it.get("defense",0)
                if dfs > best_val:
                    best_val = dfs
                    best_arm = it
                    best_idx = i
        if best_arm:
            entity.equipped_armor = best_arm
            self.player.inventory.pop(best_idx)
            print(f"{entity.name} auto-equipped armor: {best_arm['name']}")

        # Best relic
        best_rlc = None
        best_val = -1
        best_idx = -1
        for i, it in enumerate(self.player.inventory):
            if it["type"]=="relic" and self.can_equip(entity, it):
                cost_val = it.get("cost",0)
                if cost_val > best_val:
                    best_val = cost_val
                    best_rlc = it
                    best_idx = i
        if best_rlc:
            entity.equipped_relic = best_rlc
            self.player.inventory.pop(best_idx)
            print(f"{entity.name} auto-equipped relic: {best_rlc['name']}")

    ########################################
    #   Use Item
    ########################################
    def use_item(self):
        usable_items = [
            i for i in self.player.inventory 
            if i["type"] in ["potion","scroll","ring"]
        ]
        if not usable_items:
            print("No usable items in inventory!")
            return

        print("\nYour Usable Items:")
        for idx, item in enumerate(usable_items, start=1):
            desc = []
            if "heal" in item: 
                desc.append(f"Heals {item['heal']} HP")
            if "effect" in item: 
                desc.append(f"Effect: {item['effect']}")
            r = item.get("rarity","Common")
            print(f"{idx}. {item['name']} [{r}] ({', '.join(desc)})")

        valid = [str(i) for i in range(1, len(usable_items)+1)] + ["back"]
        choice = self.input_func("Choose # (or 'back'): ").strip().lower()
        if choice == "back": 
            return

        if choice not in valid:
            print("Invalid choice.")
            return
        sel_idx = int(choice)-1
        selected = usable_items[sel_idx]

        if selected["type"]=="potion" and "heal" in selected:
            max_hp = 100 + 10*(self.player.level-1)
            old = self.player.hp
            self.player.hp = min(self.player.hp + selected["heal"], max_hp)
            print(colored_text(
                f"You used {selected['name']} and healed from {old} to {self.player.hp} HP!",
                COLOR_GREEN
            ))
        elif selected["type"]=="scroll" and "effect" in selected:
            print(f"You used {selected['name']} and activated its effect: {selected['effect']}!")
        elif selected["type"]=="ring" and "effect" in selected:
            print(f"You equipped {selected['name']} and gained its effect: {selected['effect']}!")
        else:
            print("This item cannot be used right now.")

        self.player.inventory.remove(selected)

    ########################################
    #   Save/Load with Slots
    ########################################
    def save_game_slot(self):
        print("Which save slot (1-3)?")
        slot = self.input_func("> ").strip()
        if slot not in ["1","2","3"]:
            print("Invalid slot. Cancelling save.")
            return
        filename = f"savegame_{slot}.json"
        data = {
            "turn": self.turn,
            "current_tier": self.current_tier,
            "player": self.player.to_dict() if self.player else None,
            "shop_inventory": self.shop_inventory,
            "current_area": self.current_area
        }
        with open(filename,"w") as f:
            json.dump(data, f, indent=4)
        print(colored_text(f"Game saved to {filename}!", COLOR_GREEN))

    def load_game_slot(self):
        print("Which save slot (1-3)?")
        slot = self.input_func("> ").strip()
        if slot not in ["1","2","3"]:
            print("Invalid slot.")
            return
        filename = f"savegame_{slot}.json"
        if not os.path.exists(filename):
            print(f"No save file at {filename}.")
            return
        with open(filename,"r") as f:
            data = json.load(f)
        self.turn = data["turn"]
        self.current_tier = data["current_tier"]
        self.current_area = data.get("current_area","Forest")
        if data["player"]:
            self.player = Player.from_dict(data["player"])
        else:
            self.player = None
        self.shop_inventory = data.get("shop_inventory",[])
        print(colored_text(f"Game loaded from {filename}!", COLOR_GREEN))

    ########################################
    #   Shop Menu
    ########################################
    def shop_menu(self):
        while True:
            print("\nShop Menu:")
            print("  1: Buy")
            print("  2: Sell Items")
            print("  3: Hire Companion")
            print("  4: Hire Pet")
            print("  5: Enter cheat")
            print("  6: Save game (choose slot)")
            print("  7: Load game (choose slot)")
            print("  8: Help")
            print("  9: Crafting")
            print("  10: Sort Inventory")
            print("  11: Leave shop")

            choice = self.input_func("Choose an action: ").strip()

            if choice=="1":
                self.buy_items()
            elif choice=="2":
                self.sell_items()
            elif choice=="3":
                self.hire_companion()
            elif choice=="4":
                self.hire_pet()
            elif choice=="5":
                self.cheat_codes()
            elif choice=="6":
                self.save_game_slot()
            elif choice=="7":
                self.load_game_slot()
            elif choice=="8":
                self.show_help()
            elif choice=="9":
                self.crafting_menu()
            elif choice=="10":
                self.sort_inventory_menu()
            elif choice=="11":
                print("Leaving the shop...")
                break
            else:
                print("Invalid input!")

    def buy_items(self):
        if not self.shop_inventory:
            print("Shop is empty!")
            return
        print("\n--- Shop Inventory ---")
        for i, it in enumerate(self.shop_inventory, start=1):
            r = it.get("rarity","Common")
            print(f"{i}. {it['name']} [{r}] (Type={it['type']}, Cost={it['cost']})")

        choice = self.input_func("Choose item # to buy (or 'back'): ").strip()
        if choice.lower()=="back": 
            return
        if not choice.isdigit():
            print("Invalid choice.")
            return
        idx = int(choice)-1
        if idx<0 or idx>=len(self.shop_inventory):
            print("Invalid choice.")
            return

        selected = self.shop_inventory[idx]
        if self.player.gold>=selected["cost"]:
            self.player.gold -= selected["cost"]
            self.player.inventory.append(selected)
            print(colored_text(f"You bought {selected['name']}!", COLOR_GREEN))
        else:
            print(f"Not enough gold! (You have {self.player.gold})")

    def sell_items(self):
        if not self.player.inventory:
            print("No items to sell.")
            return
        print("\n--- Your Inventory ---")
        for i, it in enumerate(self.player.inventory, start=1):
            half = it["cost"]//2
            r = it.get("rarity","Common")
            print(f"{i}. {it['name']} [{r}] => Sell for {half} gold")

        choice = self.input_func("Choose # to sell (or 'back'): ").strip()
        if choice.lower()=="back": 
            return
        if not choice.isdigit():
            print("Invalid.")
            return
        idx = int(choice)-1
        if idx<0 or idx>=len(self.player.inventory):
            print("Invalid choice.")
            return
        sel = self.player.inventory[idx]
        sp = sel["cost"]//2
        self.player.gold += sp
        self.player.inventory.remove(sel)
        print(colored_text(f"Sold {sel['name']} for {sp} gold!", COLOR_GREEN))

    def hire_companion(self):
        cost = 150 * self.current_tier
        print(f"Hiring companion at Tier {self.current_tier} costs {cost} gold.")
        if self.player.gold < cost:
            print("Not enough gold.")
            return

        c_types = {
            "1": {
                "name": "Swordsman",
                "hp": 60+(10*self.current_tier),
                "strength": 7+self.current_tier,
                "magic": 0,
                "agility": 3+self.current_tier,
                "damage_type": "Physical"
            },
            "2": {
                "name": "Archer",
                "hp": 50+(10*self.current_tier),
                "strength": 5+self.current_tier,
                "magic": 0,
                "agility": 7+self.current_tier,
                "damage_type": "Physical"
            },
            "3": {
                "name": "Mage",
                "hp": 40+(10*self.current_tier),
                "strength": 2+self.current_tier,
                "magic": 10+self.current_tier,
                "agility": 5+self.current_tier,
                "damage_type": "Arcane"
            },
        }
        for k,v in c_types.items():
            print(f"{k}. {v['name']} (HP={v['hp']}, STR={v['strength']}, AGI={v['agility']})")

        ch = self.input_func("Pick # or 'back': ").strip()
        if ch.lower()=="back": 
            return
        if ch not in c_types:
            print("Invalid.")
            return
        self.player.gold -= cost
        data = c_types[ch]

        import random
        comp_name = random.choice(["Arthur","Lancelot","Guinevere","Robin"])
        c = Companion(
            comp_name, data["hp"], data["strength"],
            data["magic"], data["agility"], data["damage_type"]
        )
        self.player.companions.append(c)
        print(colored_text(f"You hired {c.name} the {data['name']}!", COLOR_GREEN))

    def hire_pet(self):
        cost = 80*self.current_tier
        print(f"Hiring a pet costs {cost} gold.")
        if self.player.gold < cost:
            print("Not enough gold.")
            return
        pet_list = {
            "1": {
                "name":"Fluffy Rabbit",
                "hp":30+(5*self.current_tier),
                "damage":3+self.current_tier,
                "type":"Physical"
            },
            "2": {
                "name":"Fire Lizard",
                "hp":35+(5*self.current_tier),
                "damage":5+self.current_tier,
                "type":"Arcane"
            },
            "3": {
                "name":"Shadow Wolf",
                "hp":40+(5*self.current_tier),
                "damage":7+self.current_tier,
                "type":"Poison"
            },
        }
        for k,v in pet_list.items():
            print(f"{k}. {v['name']} (HP={v['hp']}, DMG={v['damage']})")

        ch = self.input_func("Pick # or 'back': ").strip()
        if ch.lower()=="back":
            return
        if ch not in pet_list:
            print("Invalid.")
            return
        self.player.gold -= cost
        data = pet_list[ch]

        import random
        p_name = random.choice(["Fluffy","Spike","Shadow","Ziggy"])
        newp = Pet(p_name, data["hp"], 100, data["damage"], data["type"])
        self.player.pets.append(newp)
        print(colored_text(f"You hired {newp.name} the {data['name']}!", COLOR_GREEN))

    def cheat_codes(self):
        code = self.input_func("Enter cheat code: ").strip().lower()
        if code == "satoshi":
            self.player.gold += 1000
            print(colored_text("Cheat activated! +1000 Gold.", COLOR_YELLOW))
        elif code == "trump":
            self.player.hp = 1000
            self.player.stats["Strength"] = 1000
            print(colored_text("Cheat activated! HP and Strength maxed out!", COLOR_YELLOW))
        else:
            print("Invalid cheat code.")

    def check_for_new_tier(self):
        next_tier = self.current_tier+1
        needed = 10*self.current_tier
        if self.turn >= needed and next_tier in SHOP_TIERS:
            self.current_tier = next_tier
            self.shop_inventory = SHOP_TIERS[next_tier][:]
            print(colored_text(
                f"\n*** Tier {next_tier} Items Unlocked in the Shop! ***",
                COLOR_YELLOW
            ))

    ########################################
    #   Crafting
    ########################################
    def crafting_menu(self):
        from .data import CRAFTING_RECIPES, colored_text, COLOR_GREEN
        print("\n=== Crafting Menu ===")
        print("Your Materials:")
        mat_counts = {}
        for it in self.player.inventory:
            if it["type"]=="material":
                mat_counts[it["name"]] = mat_counts.get(it["name"],0)+1
        if not mat_counts:
            print("You have no crafting materials.")
        else:
            for k,v in mat_counts.items():
                print(f"{k} x{v}")

        print("\nAvailable Recipes:")
        all_recipes = list(CRAFTING_RECIPES.keys())
        for i, rname in enumerate(all_recipes, start=1):
            rdata = CRAFTING_RECIPES[rname]
            ing_str = ", ".join(
                f"{k}x{v}" for k,v in rdata["ingredients"].items()
            )
            print(f"{i}. {rname} => requires {ing_str}")

        choice = self.input_func("Pick recipe # or 'back': ").strip()
        if choice.lower()=="back": 
            return
        if not choice.isdigit():
            print("Invalid.")
            return
        idx = int(choice)-1
        if idx<0 or idx>=len(all_recipes):
            print("Invalid.")
            return
        rname = all_recipes[idx]
        recipe = CRAFTING_RECIPES[rname]
        if self.can_craft(recipe):
            self.do_craft(recipe)
        else:
            print("You lack the required materials.")

    def can_craft(self, recipe):
        needed = recipe["ingredients"]
        inv_mats = {}
        for it in self.player.inventory:
            if it["type"]=="material":
                nm = it["name"]
                inv_mats[nm] = inv_mats.get(nm,0)+1
        for k,v in needed.items():
            if inv_mats.get(k,0)<v:
                return False
        return True

    def do_craft(self, recipe):
        from .data import colored_text, COLOR_GREEN
        # remove mats
        for mat, count_needed in recipe["ingredients"].items():
            removed = 0
            idx = 0
            while removed<count_needed and idx<len(self.player.inventory):
                it = self.player.inventory[idx]
                if it["type"]=="material" and it["name"]==mat:
                    self.player.inventory.pop(idx)
                    removed += 1
                else:
                    idx += 1

        result = recipe["result"].copy()
        self.player.inventory.append(result)
        print(colored_text(f"You crafted {result['name']}!", COLOR_GREEN))

    ########################################
    #   Sorting
    ########################################
    def sort_inventory_menu(self):
        print("1) Sort by Type\n2) Sort by Rarity\n3) Sort by Name\n4) Back")
        choice = self.input_func("> ").strip()
        if choice=="1":
            self.sort_inventory("type")
            print("Sorted by type.")
        elif choice=="2":
            self.sort_inventory("rarity")
            print("Sorted by rarity.")
        elif choice=="3":
            self.sort_inventory("name")
            print("Sorted by name.")
        elif choice=="4":
            return

    def sort_inventory(self, criterion):
        if criterion == "type":
            self.player.inventory.sort(key=lambda i: i["type"])
        elif criterion == "rarity":
            rarity_order = {"Common":1,"Uncommon":2,"Rare":3,"Epic":4,"Legendary":5}
            self.player.inventory.sort(
                key=lambda i: rarity_order.get(i.get("rarity","Common"),1)
            )
        elif criterion == "name":
            self.player.inventory.sort(key=lambda i: i["name"])

    ########################################
    #   Help
    ########################################
    def show_help(self):
        print(colored_text("\n=== GAME HELP ===", COLOR_BLUE))
        print("Combat: Attack, Use Skill, Use Item, or Flee.")
        print("Skills: Unlock special moves/spells with higher damage or effects.")
        print("Inventory: Use potions, scrolls, or equip gear.")
        print("Shop: Buy/sell, hire companions/pets.")
        print("Save Slots: Up to 3 separate saves.")
        print("Crafting: Combine materials into items.")
        print("Talents: On level-up, pick talents for stat boosts.")
        print("Pet Evolution: Some pets evolve at certain levels.")
        print("===================\n")
