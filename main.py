# main.py
from game.game import Game
import random
from collections import deque

# -----------------------------
# 1) Define Biome Lists / Symbols
# -----------------------------

LAND_BIOMES = [
    "Forest", "Plains", "Woods Creek", "Tundra", "Mountains", "Hills",
    "Desert", "Beach", "Jungle", "Rainforest", "River", "Marsh", "Swamp",
]
# We'll treat "Ocean" as water.

# For an ASCII display, we define a SYMBOL and a COLOR (ANSI code) for each biome.
# color codes reference (foreground):
# 30=black,31=red,32=green,33=yellow,34=blue,35=magenta,36=cyan,37=white,90=bright grey, etc.
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

WIDTH = 250
HEIGHT = 250


# -----------------------------
# 2) World Generation (Pangea-style)
# -----------------------------
def generate_pangea_world(width=WIDTH, height=HEIGHT) -> list[list[str]]:
    """
    Generates a 250x250 map with:
      - ~70% land as a single large continent (contiguous).
      - The rest is "Ocean."
      - The land is subdivided among LAND_BIOMES in contiguous lumps.
    Returns a 2D list of biome strings.
    """
    world_map = [["Ocean" for _ in range(width)] for _ in range(height)]

    total_cells = width * height
    target_land_ratio = 0.70  # ~70% land
    target_land_cells = int(total_cells * target_land_ratio)

    center_x = width // 2
    center_y = height // 2

    visited = [[False]*width for _ in range(height)]
    queue = deque()
    queue.append((center_x, center_y))
    visited[center_y][center_x] = True

    land_count = 0

    # First BFS to carve out "land" (None placeholders)
    while queue and land_count < target_land_cells:
        cx, cy = queue.popleft()
        world_map[cy][cx] = None  # None means "unassigned land"
        land_count += 1

        directions = [(0,1),(0,-1),(1,0),(-1,0)]
        random.shuffle(directions)
        for dx, dy in directions:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < width and 0 <= ny < height:
                if not visited[ny][nx]:
                    visited[ny][nx] = True
                    # random chance to expand so shape is not uniform
                    if random.random() < 0.8:
                        queue.append((nx, ny))

    # Subdivide land among the LAND_BIOMES
    random.shuffle(LAND_BIOMES)
    num_biomes = len(LAND_BIOMES)
    cells_per_biome = land_count // num_biomes
    leftover = land_count % num_biomes

    visited_land = [[False]*width for _ in range(height)]

    def get_neighbors(x, y):
        for (dx, dy) in [(0,1),(0,-1),(1,0),(-1,0)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < width and 0 <= ny < height:
                yield nx, ny

    for i, biome in enumerate(LAND_BIOMES):
        # each biome gets a BFS "lump"
        cells_for_biome = cells_per_biome
        if i < leftover:
            cells_for_biome += 1

        if cells_for_biome <= 0:
            continue

        # find a random unassigned land cell
        land_cells_list = []
        for r in range(height):
            for c in range(width):
                if world_map[r][c] is None and not visited_land[r][c]:
                    land_cells_list.append((c, r))

        if not land_cells_list:
            break  # no more unassigned land

        start_x, start_y = random.choice(land_cells_list)
        q2 = deque()
        q2.append((start_x, start_y))
        visited_land[start_y][start_x] = True

        assigned_count = 0

        while q2 and assigned_count < cells_for_biome:
            cx, cy = q2.popleft()
            world_map[cy][cx] = biome
            assigned_count += 1

            for nx, ny in get_neighbors(cx, cy):
                if world_map[ny][nx] is None and not visited_land[ny][nx]:
                    visited_land[ny][nx] = True
                    q2.append((nx, ny))

    # Fill leftover None with some default, e.g. "Plains"
    for r in range(height):
        for c in range(width):
            if world_map[r][c] is None:
                world_map[r][c] = "Plains"

    return world_map

# -----------------------------
# 3) Color / ASCII Display
# -----------------------------

def color_text(symbol: str, fg_color: int = 37) -> str:
    """
    Wrap the symbol with an ANSI escape code for the given fg_color.
    e.g. 32 = green, 34 = blue, etc.
    """
    return f"\033[{fg_color}m{symbol}\033[0m"

def display_world_ascii(world_map: list[list[str]], show_width=80, show_height=40):
    """
    Displays a portion of the generated map in ASCII, with color codes.
    :param show_width:  how many columns to show
    :param show_height: how many rows to show
    (Truncates if the map is larger, to avoid excessive console spam.)
    """
    max_y = min(show_height, len(world_map))
    max_x = min(show_width, len(world_map[0]) if world_map else 0)

    for row in range(max_y):
        row_str = []
        for col in range(max_x):
            biome = world_map[row][col]
            if biome in BIOME_ASCII:
                symbol, color_code = BIOME_ASCII[biome]
            else:
                # fallback
                symbol, color_code = BIOME_ASCII["PlainsDefault"]
            row_str.append(color_text(symbol, color_code))
        print("".join(row_str))


# -----------------------------
# 4) Main Entry (Game Start)
# -----------------------------
def start_game():
    print("Starting the game...")
    print("Generating a 250x250 Pangea-style world. Please wait...")

    # Generate the world
    world_map = generate_pangea_world(WIDTH, HEIGHT)

    # Display the final map (or a portion of it)
    print("\nHere is a portion of the generated world (80 wide x 40 tall):\n")
    display_world_ascii(world_map, show_width=80, show_height=40)

    print("\n...Map generation complete. Game world is ready!\n")

if __name__ == "__main__":
    start_game()
