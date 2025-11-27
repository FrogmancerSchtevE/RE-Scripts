from System.Collections.Generic import List
from math import sqrt
import PathFinding

TREE_IDS = [
    0x0C95, 0x0C96, 0x0C99, 0x0C9B, 0x0C9C, 0x0C9D, 0x0C8A, 0x0CA6,
    0x0CA8, 0x0CAA, 0x0CAB, 0x0CC3, 0x0CC4, 0x0CC8, 0x0CC9, 0x0CCA, 0x0CCB,
    0x0CCC, 0x0CCD, 0x0CD0, 0x0CD3, 0x0CD6
]
SCAN_RADIUS = 10
TREE_COOLDOWN_MS = 1200000  # 20 minutes

visited = []
trees = []

class Tree:
    def __init__(self, x, y, z, tileid):
        self.x = x
        self.y = y
        self.z = z
        self.id = tileid

def scan_for_trees():
    global trees
    trees = []
    px, py = Player.Position.X, Player.Position.Y
    Misc.SendMessage("📡 Scanning for trees...", 55)
    for x in range(px - SCAN_RADIUS, px + SCAN_RADIUS + 1):
        for y in range(py - SCAN_RADIUS, py + SCAN_RADIUS + 1):
            tiles = Statics.GetStaticsTileInfo(x, y, 0)  # Force map 0
            for tile in tiles:
                if tile.StaticID in TREE_IDS:
                    key = (x, y)
                    if key not in visited and not Timer.Check(f"{x},{y}"):
                        trees.append(Tree(x, y, tile.StaticZ, tile.StaticID))
                        Misc.SendMessage(f"Found tree at {x},{y}", 68)
    trees.sort(key=lambda t: sqrt((t.x - px) ** 2 + (t.y - py) ** 2))
    Misc.SendMessage(f"Total trees found: {len(trees)}", 68)

def move_to_tree(tree):
    Misc.SendMessage(f"➡️ Trying to path to {tree.x},{tree.y}", 55)
    offsets = [(0, 1), (1, 0), (-1, 0), (0, -1)]
    for dx, dy in offsets:
        dest = PathFinding.Route()
        dest.X = tree.x + dx
        dest.Y = tree.y + dy
        dest.MaxRetry = 3
        dest.StopIfStuck = False
        Misc.SendMessage(f"🚶 Trying {dest.X},{dest.Y}", 55)
        if PathFinding.Go(dest):
            Misc.SendMessage("Pathing succeeded.", 68)
            Misc.Pause(1000)
            return True
        Misc.Pause(250)

    Misc.SendMessage("All path attempts failed.", 33)
    return False

def wait_for_depletion():
    Journal.Clear()
    Timer.Create("waitChop", 10000)
    while not Journal.Search("There's not enough wood here to harvest.") and Timer.Check("waitChop"):
        Misc.Pause(200)
    Journal.Clear()

def main():
    Misc.SendMessage("🌲 Tree Walker Activated", 68)

    while True:
        scan_for_trees()
        if not trees:
            Misc.SendMessage("⚠️ No trees found, pausing...", 33)
            Misc.Pause(3000)
            continue

        for tree in trees:
            if move_to_tree(tree):
                wait_for_depletion()
            visited.append((tree.x, tree.y))
            Timer.Create(f"{tree.x},{tree.y}", TREE_COOLDOWN_MS)

if __name__ == "__main__":
    main()
