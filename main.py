import random
from collections import deque
import colorama

colorama.init()

WIDTH = 60
HEIGHT = 60

FACTION_NUMBERS = {
    "Knights of Peace": 1,
    "Mystic Knights": 2,
    "Eldermages": 3,
    "Ironclad Knights": 4,
    "Hilltribes": 5,
    "Wizard of the East": 6,
    "Deathknights": 7,
    "The Black Hand": 8,
    "Dark Mages": 9,
}

FACTION_LOCATIONS = [
    ("Knights of Peace", "Citadel", 1),
    ("Mystic Knights", "Castle", 1),
    ("Eldermages", "Tower", 3),
    ("Ironclad Knights", "Castle", 1),
    ("Hilltribes", "Fort", 3),
    ("Wizard of the East", "Citadel", 1),
    ("Deathknights", "Castle", 3),
    ("The Black Hand", "Tower", 5),
    ("The Black Hand", "Citadel", 1),
    ("Dark Mages", "Tower", 3),
]

class Location:
    def __init__(self, faction, loc_type, x, y):
        self.faction = faction
        self.loc_type = loc_type
        self.x = x
        self.y = y

BIOME_ASCII = {
    "Ocean":       ("~", 34),  # Blue
    "Forest":      ("F", 32),  # Green
    "Plains":      (".", 33),  # Yellow
    "Woods Creek": ("C", 36),  # Cyan
    "Tundra":      ("T", 37),  # White
    "Mountains":   ("^", 90),  # Grey
    "Hills":       ("h", 33),  # Yellow-ish
    "Desert":      ("D", 33),  # Yellow
    "Beach":       ("b", 93),  # Bright Yellow
    "Jungle":      ("J", 32),  # Green
    "Rainforest":  ("r", 32),  # Green
    "River":       ("=", 36),  # Cyan
    "Marsh":       ("m", 92),  # Bright Green
    "Swamp":       ("s", 92),  # Bright Green
     # Fallback for unassigned land
    "PlainsDefault": (".", 37),
}

def color_text(symbol, fg_color=37):
    return f"\033[{fg_color}m{symbol}\033[0m"

def generate_landmap(width=WIDTH, height=HEIGHT):
    world_map = [["Ocean" for _ in range(width)] for _ in range(height)]
    total_cells = width * height
    target_land_cells = int(total_cells * 0.70)

    center_x = width // 2
    center_y = height // 2

    visited = [[False] * width for _ in range(height)]
    queue = deque([(center_x, center_y)])
    visited[center_y][center_x] = True

    land_count = 0
    while queue and land_count < target_land_cells:
        cx, cy = queue.popleft()
        world_map[cy][cx] = None
        land_count += 1

        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        random.shuffle(directions)
        for dx, dy in directions:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < width and 0 <= ny < height:
                if not visited[ny][nx]:
                    if random.random() < 0.8:  # or 0.7 or 0.9, etc.
                        visited[ny][nx] = True
                        queue.append((nx, ny))


    return world_map

def place_faction_locations(world_map):
    width = len(world_map[0])
    height = len(world_map)

    location_list = []

    def manhattan_dist(ax, ay, bx, by):
        return abs(ax - bx) + abs(ay - by)

    for (faction, loc_type, count) in FACTION_LOCATIONS:
        tries = 0
        max_tries = width * height
        while count > 0 and tries < max_tries:
            rx = random.randint(2, width - 3)
            ry = random.randint(2, height - 3)
            if world_map[ry][rx] is None:
                too_close = False
                for loc in location_list:
                    if manhattan_dist(rx, ry, loc.x, loc.y) < 3:
                        too_close = True
                        break
                if too_close:
                    tries += 1
                    continue

                location_list.append(Location(faction, loc_type, rx, ry))
                count -= 1
            tries += 1
        if count > 0:
            print(f"Warning: Could not place all {loc_type} for {faction}.")

    return location_list

def assign_factions(world_map, locations):
    width = len(world_map[0])
    height = len(world_map)
    faction_map = [[None] * width for _ in range(height)]

    queue = deque()
    for loc in locations:
        fx = FACTION_NUMBERS[loc.faction]
        faction_map[loc.y][loc.x] = fx
        queue.append((loc.x, loc.y, fx))

    while queue:
        x, y, fac_num = queue.popleft()
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                if faction_map[ny][nx] is None and world_map[ny][nx] is None:
                    faction_map[ny][nx] = fac_num
                    queue.append((nx, ny, fac_num))

    return faction_map

FACTION_BIOMES = {
    1: ["Forest", "Plains"],
    2: ["Mountains", "Plains"],
    3: ["Hills", "Forest", "River"],
    4: ["Hills", "Plains"],
    5: ["Hills", "Forest"],
    6: ["Forest", "River"],
    7: ["Mountains", "Desert"],
    8: ["Swamp", "Marsh", "Plains"],
    9: ["Woods Creek", "Marsh"],
}

def build_biomes_for_factions(faction_map):
    width = len(faction_map[0])
    height = len(faction_map)

    final_map = [["Ocean"] * width for _ in range(height)]

    faction_cells = {}
    for r in range(height):
        for c in range(width):
            val = faction_map[r][c]
            if val == "Forest":
                final_map[r][c] = "Forest"
            elif val != -1 and isinstance(val, int):
                faction_cells.setdefault(val, []).append((c, r))

    for fac_num, cells in faction_cells.items():
        if fac_num not in FACTION_BIOMES:
            for (cx, cy) in cells:
                final_map[cy][cx] = "Plains"
            continue

        biomes_for_faction = FACTION_BIOMES[fac_num]
        biome_weights = [1] * len(biomes_for_faction)

        for (cx, cy) in cells:
            biome = random.choices(biomes_for_faction, weights=biome_weights, k=1)[0]
            final_map[cy][cx] = biome

    return final_map

def draw_road(final_map, x1, y1, x2, y2):
    dx = abs(x2 - x1)
    sx = 1 if x1 < x2 else -1
    dy = -abs(y2 - y1)
    sy = 1 if y1 < y2 else -1
    err = dx + dy
    x, y = x1, y1
    while True:
        if 0 <= x < len(final_map[0]) and 0 <= y < len(final_map):
            final_map[y][x] = "Road"
        if x == x2 and y == y2:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy

def build_roads(locations, final_map):
    def find_nearest(loc, locations):
        nearest = None
        min_dist = float('inf')
        for other in locations:
            if other == loc:
                continue
            dist = abs(loc.x - other.x) + abs(loc.y - other.y)
            if dist < min_dist:
                min_dist = dist
                nearest = other
        return nearest

    for loc in locations:
        nearest = find_nearest(loc, locations)
        if nearest:
            draw_road(final_map, loc.x, loc.y, nearest.x, nearest.y)

def display_world_ascii(final_map, show_w=60, show_h=30):
    max_y = min(show_h, len(final_map))
    max_x = min(show_w, len(final_map[0]))
    for row in range(max_y):
        rowstr = []
        for col in range(max_x):
            cell = final_map[row][col]
            if cell in BIOME_ASCII:
                sym, color = BIOME_ASCII[cell]
                rowstr.append(color_text(sym, color))
            else:
                s = cell[0].upper() if cell else "?"
                rowstr.append(color_text(s, 37))
        print(" ".join(rowstr))

def start_game():
    print("1) Generating land/water map...")
    landmap = generate_landmap(WIDTH, HEIGHT)

    print("2) Placing faction locations on land...")
    locs = place_faction_locations(landmap)

    print("3) Assigning each land cell to closest faction (Voronoi BFS).")
    faction_map = assign_factions(landmap, locs)

    print("4) Subdividing each faction's territory into biomes.")
    final_map = build_biomes_for_factions(faction_map)

    print("5) Building roads among locations, marking as 'Road'.")
    build_roads(locs, final_map)

    print("6) Display top-left portion of final map:\n")
    display_world_ascii(final_map, show_w=60, show_h=30)

    print("\nDone!")
    for L in locs:
        fac_num = FACTION_NUMBERS[L.faction]
        print(f"- {L.faction} {L.loc_type} at ({L.x},{L.y}), faction#{fac_num}")

if __name__ == "__main__":
    start_game()
