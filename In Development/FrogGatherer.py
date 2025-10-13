# ==============================
# === FrogGath - v0.3 (UI+Settings)
# ==============================

import time
import PathFinding
from math import sqrt

# CONFIG
GUMP_ID     = 0x51A0CAFE
REFRESH_MS  = 500
GUMP_POS    = (650, 650)

# Pages
PAGE_MAIN     = 0
PAGE_MINING   = 1
PAGE_LUMBER   = 2
PAGE_SETTINGS = 3

# State
_running        = True
_current_page   = PAGE_MAIN
_return_page    = PAGE_MAIN
_runtime_mining = False
_runtime_lumber = False
_runtime_lumber_auto = False


# Session Counters
mining_ore     = 0
mining_ingots  = 0
lumber_logs    = 0
lumber_boards  = 0

# Settings
settings = {
    "lumber_storage": "None",      
    "mining_storage": "None",      
    "smelting_method": "None",     
    "gather_method": "TreeID",     # TreeID or Self
    "beetle_serial": None,         
    "fire_beetle_serial": None,    
    "forge_serials": [],           
    "packy_serials": [],           
    "house_container_serial": None 
}


# Buttons
BTN_QUIT        = 9001
BTN_MAIN_MINING = 9002
BTN_MAIN_LUMBER = 9003
BTN_MAIN_SETTINGS = 9004

BTN_BACK        = 9010
BTN_RUNPAUSE    = 9011

BTN_SET_LUMBER  = 9020
BTN_SET_MINING  = 9021
BTN_SET_SMELT   = 9022
BTN_TARGET_BEETLE      = 9023
BTN_TARGET_FIREBEETLE  = 9024
BTN_TARGET_FORGE       = 9025
BTN_CLEAR_FORGES       = 9026
BTN_TARGET_PACKIES     = 9027
BTN_TARGET_HOUSE       = 9028
BTN_SET_GATHER         = 9029
BTN_TOGGLE_AUTO = 9050




# -------------------
# Utils
# -------------------
def msg(text, hue=68):
    try: Misc.SendMessage(text, hue)
    except: pass

def status_label(running):
    return ("RUNNING", 68) if running else ("paused", 33)

def short_serial(s):
    return hex(int(s)) if s else "None"

class Tree:
    def __init__(self, x, y, z, tileid):
        self.x = x
        self.y = y
        self.z = z
        self.id = tileid

visited_trees = set()
tree_list = []
TREE_COOLDOWN_MS = 1200000  # 20 minutes


# -------------------
# Gump Rendering
# -------------------
def render_main():
    Gumps.CloseGump(GUMP_ID)
    gd = Gumps.CreateGump(True)
    Gumps.AddPage(gd, 0)
    Gumps.AddBackground(gd, 0, 0, 250, 160, 9270)
    Gumps.AddAlphaRegion(gd, 0, 0, 250, 160)

    # Title
    Gumps.AddLabel(gd, 80, 10, 35, "FrogGath v0.31")

    # Settings gem (top-left)
    Gumps.AddButton(gd, 5, 5, 0x0846, 0x0846, BTN_MAIN_SETTINGS, 1, 0)

    # Menu options
    Gumps.AddButton(gd, 20, 50, 4017, 4018, BTN_MAIN_MINING, 1, 0)
    Gumps.AddLabel(gd, 55, 52, 81, "Mining")

    Gumps.AddButton(gd, 20, 80, 4017, 4018, BTN_MAIN_LUMBER, 1, 0)
    Gumps.AddLabel(gd, 55, 82, 81, "Lumberjacking")

    # Quit (top-right)
    Gumps.AddButton(gd, 200, 10, 4017, 4018, BTN_QUIT, 1, 0)
    Gumps.AddLabel(gd, 230, 12, 33, "Quit")

    Gumps.SendGump(GUMP_ID, Player.Serial, *GUMP_POS,
                   gd.gumpDefinition, gd.gumpStrings)


def render_mining():
    Gumps.CloseGump(GUMP_ID)
    gd = Gumps.CreateGump(True)
    Gumps.AddPage(gd, 0)
    Gumps.AddBackground(gd, 0, 0, 300, 160, 9270)
    Gumps.AddAlphaRegion(gd, 0, 0, 300, 160)

    Gumps.AddLabel(gd, 100, 10, 35, "Mining v0.31")

    # Settings gem (top-left)
    Gumps.AddButton(gd, 5, 5, 0x0846, 0x0846, BTN_MAIN_SETTINGS, 1, 0)

    label, hue = status_label(_runtime_mining)
    Gumps.AddButton(gd, 20, 35, 4017, 4018, BTN_RUNPAUSE, 1, 0)
    Gumps.AddLabel(gd, 55, 37, hue, label)

    Gumps.AddLabel(gd, 20, 65, 81, f"Ore: {mining_ore}")
    Gumps.AddLabel(gd, 150, 65, 81, f"Ingots: {mining_ingots}")

    Gumps.AddButton(gd, 20, 100, 4017, 4018, BTN_BACK, 1, 0)
    Gumps.AddLabel(gd, 55, 102, 81, "Back")

    Gumps.SendGump(GUMP_ID, Player.Serial, *GUMP_POS,
                   gd.gumpDefinition, gd.gumpStrings)


def render_lumber():
    Gumps.CloseGump(GUMP_ID)
    gd = Gumps.CreateGump(True)
    Gumps.AddPage(gd, 0)
    Gumps.AddBackground(gd, 0, 0, 300, 160, 9270)
    Gumps.AddAlphaRegion(gd, 0, 0, 300, 160)

    Gumps.AddLabel(gd, 90, 10, 35, "Lumber v0.31")

    # Settings gem (top-left)
    Gumps.AddButton(gd, 5, 5, 0x0846, 0x0846, BTN_MAIN_SETTINGS, 1, 0)

    # Run / Pause
    label, hue = status_label(_runtime_lumber)
    Gumps.AddButton(gd, 20, 35, 4017, 4018, BTN_RUNPAUSE, 1, 0)
    Gumps.AddLabel(gd, 55, 37, hue, label)

    # Resource counters
    Gumps.AddLabel(gd, 20, 65, 81, f"Logs: {lumber_logs}")
    Gumps.AddLabel(gd, 150, 65, 81, f"Boards: {lumber_boards}")

    # Auto / Manual toggle (right side of the row)
    label = "Auto" if _runtime_lumber_auto else "Manual"
    hue   = 68 if _runtime_lumber_auto else 33
    Gumps.AddButton(gd, 200, 35, 4017, 4018, BTN_TOGGLE_AUTO, 1, 0)
    Gumps.AddLabel(gd, 235, 37, hue, label)

    # Back
    Gumps.AddButton(gd, 20, 100, 4017, 4018, BTN_BACK, 1, 0)
    Gumps.AddLabel(gd, 55, 102, 81, "Back")

    Gumps.SendGump(GUMP_ID, Player.Serial, *GUMP_POS, gd.gumpDefinition, gd.gumpStrings)





def render_settings():
    Gumps.CloseGump(GUMP_ID)
    gd = Gumps.CreateGump(True)
    Gumps.AddPage(gd, 0)
    Gumps.AddBackground(gd, 0, 0, 340, 250, 9270)
    Gumps.AddAlphaRegion(gd, 0, 0, 340, 250)

    Gumps.AddLabel(gd, 120, 10, 35, "Settings v0.3")

    # Lumber storage
    Gumps.AddLabel(gd, 20, 40, 81, f"Lumber: {settings['lumber_storage']}")
    Gumps.AddButton(gd, 200, 38, 4017, 4018, BTN_SET_LUMBER, 1, 0)

    # Mining storage
    Gumps.AddLabel(gd, 20, 70, 81, f"Mining: {settings['mining_storage']}")
    Gumps.AddButton(gd, 200, 68, 4017, 4018, BTN_SET_MINING, 1, 0)

    # Smelting
    Gumps.AddLabel(gd, 20, 100, 81, f"Smelting: {settings['smelting_method']}")
    Gumps.AddButton(gd, 200, 98, 4017, 4018, BTN_SET_SMELT, 1, 0)

    # Gather Method
    Gumps.AddLabel(gd, 20, 160, 81, f"Lumber Mode: {settings['gather_method']}")
    Gumps.AddButton(gd, 200, 158, 4017, 4018, BTN_SET_GATHER, 1, 0)

    # Forge info
    Gumps.AddLabel(gd, 20, 130, 81, f"Forges: {len(settings['forge_serials'])}")
    Gumps.AddButton(gd, 200, 128, 4017, 4018, BTN_TARGET_FORGE, 1, 0)
    Gumps.AddLabel(gd, 240, 130, 81, "Add")
    Gumps.AddButton(gd, 200, 148, 4017, 4018, BTN_CLEAR_FORGES, 1, 0)
    Gumps.AddLabel(gd, 240, 150, 33, "Clear")

    # Packies
    Gumps.AddLabel(gd, 20, 180, 81, f"Packies: {len(settings['packy_serials'])}")
    Gumps.AddButton(gd, 200, 178, 4017, 4018, BTN_TARGET_PACKIES, 1, 0)

    # House
    Gumps.AddLabel(gd, 20, 210, 81, "House Storage")
    Gumps.AddButton(gd, 200, 208, 4017, 4018, BTN_TARGET_HOUSE, 1, 0)

    Gumps.AddButton(gd, 20, 220, 4017, 4018, BTN_BACK, 1, 0)
    Gumps.AddLabel(gd, 55, 222, 81, "Back")

    Gumps.SendGump(GUMP_ID, Player.Serial, *GUMP_POS,
                   gd.gumpDefinition, gd.gumpStrings)


def render():
    if _current_page == PAGE_MAIN:
        render_main()
    elif _current_page == PAGE_MINING:
        render_mining()
    elif _current_page == PAGE_LUMBER:
        render_lumber()
    elif _current_page == PAGE_SETTINGS:
        render_settings()

# -------------------
# Lumber Logic
# -------------------

from math import sqrt
import PathFinding

TREE_IDS = [
    0x0C95, 0x0C96, 0x0C99, 0x0C9B, 0x0C9C, 0x0C9D,
    0x0C8A, 0x0CA6, 0x0CA8, 0x0CAA, 0x0CAB,
    0x0CC3, 0x0CC4, 0x0CC8, 0x0CC9, 0x0CCA, 0x0CCB,
    0x0CCC, 0x0CCD, 0x0CD0, 0x0CD3, 0x0CD6, 0x0CDD
]

AXE_ID   = 0x0F43  
AXE_HUE  = -1

_last_chop        = 0
CHOP_DELAY_MS     = 3000
MANUAL_CHOP_RANGE = 2
SCAN_RADIUS       = 12

TREE_COOLDOWN_MS  = 1200000  # 20 min cooldown for visited trees

# Tree memory
class Tree:
    def __init__(self, x, y, z, tileid):
        self.x = x
        self.y = y
        self.z = z
        self.id = tileid

tree_list     = []
visited_trees = set()


# --- Helpers ---
def get_axe():
    hand = Player.GetItemOnLayer("RightHand") or Player.GetItemOnLayer("LeftHand")
    if hand and hand.ItemID == AXE_ID:
        return hand
    axe = Items.FindByID(AXE_ID, AXE_HUE, Player.Backpack.Serial)
    return axe


def chop_tree(tree):
    global _last_chop, lumber_logs, lumber_boards
    axe = get_axe()
    if not axe:
        msg("No axe found!", 33)
        return False

    Journal.Clear()
    Items.UseItem(axe)
    if Target.WaitForTarget(1000):
        Target.TargetExecute(tree.x, tree.y, tree.z, tree.tile.StaticID)
        _last_chop = int(time.time() * 1000)
        Misc.Pause(600)

        if Journal.Search("You put") or Journal.Search("logs"):
            lumber_logs += 1
        if Journal.Search("boards"):
            lumber_boards += 1
        if Journal.Search("not enough wood"):
            return "depleted"

    return True


def find_nearest_tree(radius=4):
    """Manual mode helper: return (x, y, z, tile) for the nearest tree around the player."""
    px, py, pz = Player.Position.X, Player.Position.Y, Player.Position.Z
    best = None
    best_d2 = 10**9  # squared distance for speed

    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            x, y = px + dx, py + dy
            tiles = Statics.GetStaticsTileInfo(x, y, Player.Map)
            for tile in tiles:
                if tile.StaticID in TREE_IDS:
                    d2 = dx*dx + dy*dy
                    if d2 < best_d2:
                        best = (x, y, pz, tile)  # use player's Z for targeting
                        best_d2 = d2
    return best


def scan_for_trees():
    """Populate tree_list with valid nearby trees"""
    global tree_list
    tree_list = []
    px, py = Player.Position.X, Player.Position.Y
    for x in range(px - SCAN_RADIUS, px + SCAN_RADIUS + 1):
        for y in range(py - SCAN_RADIUS, py + SCAN_RADIUS + 1):
            tiles = Statics.GetStaticsTileInfo(x, y, Player.Map)
            for tile in tiles:
                if tile.StaticID in TREE_IDS:
                    key = (x, y)
                    if key not in visited_trees and not Timer.Check(f"{x},{y}"):
                        tree_list.append(Tree(x, y, tile.StaticZ, tile.StaticID))
    tree_list.sort(key=lambda t: sqrt((t.x - px) ** 2 + (t.y - py) ** 2))


def move_to_tree(tree):
    """Pathfind to an adjacent walkable tile near the tree."""
    offsets = [(0, 1), (1, 0), (-1, 0), (0, -1)]  # S, E, W, N
    for dx, dy in offsets:
        tx, ty = tree.x + dx, tree.y + dy
        if PathFinding.PathFindTo(tx, ty, tree.z):
            Misc.Pause(500)
            return True
    return False

    msg(f"Could not find walkable tile near tree at {tree.x},{tree.y}", 33)
    return False



# --- Modes ---
def lumber_loop_manual():
    """Player pilots, script just chops nearby trees"""
    px, py, pz = Player.Position.X, Player.Position.Y, Player.Position.Z
    for dx in range(-MANUAL_CHOP_RANGE, MANUAL_CHOP_RANGE + 1):
        for dy in range(-MANUAL_CHOP_RANGE, MANUAL_CHOP_RANGE + 1):
            x, y = px + dx, py + dy
            tiles = Statics.GetStaticsTileInfo(x, y, Player.Map)
            for tile in tiles:
                if tile.StaticID in TREE_IDS:
                    chop_tree(Tree(x, y, pz, tile.StaticID))


def lumber_loop_auto():
    """Full autopilot: scan, pathfind, chop until depletion"""
    global _last_chop

    now = int(time.time() * 1000)
    if now - _last_chop < CHOP_DELAY_MS:
        return

    axe = get_axe()
    if not axe:
        msg("No axe found! Stopping lumberjacking.", 33)
        _runtime_lumber = False
        return

    # Refresh tree list if empty
    if not tree_list:
        scan_for_trees()

    if not tree_list:
        msg("No trees found nearby.", 53)
        Misc.Pause(1000)
        return

    # Take the nearest tree from the list
    tree = tree_list.pop(0)

    # Move near the tree (1-tile offset)
    if not move_to_tree(tree):
        msg(f"Can't reach tree at {tree.x},{tree.y}", 33)
        return

    # Chop until depleted
    while True:
        result = chop_tree(tree.x, tree.y, tree.z, tree)

        if result == "depleted" or Journal.Search("There's not enough wood"):
            msg(f"Tree at {tree.x},{tree.y} depleted.", 53)
            visited_trees.add((tree.x, tree.y))
            Timer.Create(f"{tree.x},{tree.y}", TREE_COOLDOWN_MS)
            Journal.Clear()
            break  # stop chopping, move to next tree next tick

        Misc.Pause(800)

    # Reset chop delay so next loop can immediately scan for next tree
    _last_chop = int(time.time() * 1000) - CHOP_DELAY_MS



def lumber_loop():
    global _runtime_lumber, _last_chop, lumber_logs, lumber_boards

    if not _runtime_lumber:
        return

    now = int(time.time() * 1000)
    if now - _last_chop < CHOP_DELAY_MS:
        return

    axe = get_axe()
    if not axe:
        msg("No axe found! Stopping lumberjacking.", 33)
        _runtime_lumber = False
        return

    # Force TreeID if autopilot is ON
    method = settings.get("gather_method", "Self")
    if _runtime_lumber_auto:
        method = "TreeID"

    # -----------------------
    # Manual Self-Chop (AOE)
    # -----------------------
    if method == "Self" and not _runtime_lumber_auto:
        Journal.Clear()
        Items.UseItem(axe)
        if Target.WaitForTarget(1000):
            Target.TargetExecute(Player.Serial)
            _last_chop = now
            Misc.Pause(500)

            if Journal.Search("You put") or Journal.Search("logs"):
                lumber_logs += 1
            if Journal.Search("boards"):
                lumber_boards += 1

            if Journal.Search("There's not enough wood"):
                msg("No wood left in this area.", 53)
                Journal.Clear()

    # -----------------------
    # Manual TreeID (no path)
    # -----------------------
    elif method == "TreeID" and not _runtime_lumber_auto:
        tree = find_nearest_tree()
        if tree:
            x, y, z, tile = tree
            result = chop_tree(tree)
            if result == "depleted":
                msg("Tree depleted.", 53)
        else:
            msg("No trees nearby.", 53)

    # -----------------------
    # Full Auto Mode
    # -----------------------
    elif method == "TreeID" and _runtime_lumber_auto:
        lumber_loop_auto()
     

# -------------------
# Main Loop
# -------------------
msg("FrogGath v0.3 started.", 68)
render()

while _running and Player.Connected:
    gd = Gumps.GetGumpData(GUMP_ID)
    if gd and gd.buttonid:
        bid = gd.buttonid

        if _current_page == PAGE_MAIN:
            if bid == BTN_MAIN_MINING:
                _current_page = PAGE_MINING
            elif bid == BTN_MAIN_LUMBER:
                _current_page = PAGE_LUMBER
            elif bid == BTN_MAIN_SETTINGS:
                _return_page = PAGE_MAIN
                _current_page = PAGE_SETTINGS
            elif bid == BTN_QUIT:
                _running = False

        elif _current_page == PAGE_MINING:
            if bid == BTN_RUNPAUSE:
                _runtime_mining = not _runtime_mining
            elif bid == BTN_BACK:
                _current_page = PAGE_MAIN
            elif bid == BTN_MAIN_SETTINGS:
                _return_page = PAGE_MINING
                _current_page = PAGE_SETTINGS

        elif _current_page == PAGE_LUMBER:
            if bid == BTN_RUNPAUSE:
                _runtime_lumber = not _runtime_lumber
            elif bid == BTN_TOGGLE_AUTO:
                _runtime_lumber_auto = not _runtime_lumber_auto
            elif bid == BTN_BACK:
                _current_page = PAGE_MAIN
            elif bid == BTN_MAIN_SETTINGS:
                _return_page = PAGE_LUMBER
                _current_page = PAGE_SETTINGS




        elif _current_page == PAGE_SETTINGS:
            if bid == BTN_BACK:
                _current_page = _return_page
            elif bid == BTN_SET_LUMBER:
                opts = ["None", "Satchel", "Beetle", "Packhorses", "Bank", "House"]
                cur = settings["lumber_storage"]
                settings["lumber_storage"] = opts[(opts.index(cur) + 1) % len(opts)]
            elif bid == BTN_SET_MINING:
                opts = ["None", "Packhorses", "Bank", "House"]
                cur = settings["mining_storage"]
                settings["mining_storage"] = opts[(opts.index(cur) + 1) % len(opts)]
            elif bid == BTN_SET_SMELT:
                opts = ["None", "FireBeetle", "Forge"]
                cur = settings["smelting_method"]
                settings["smelting_method"] = opts[(opts.index(cur) + 1) % len(opts)]
            elif bid == BTN_TARGET_BEETLE:
                settings["beetle_serial"] = Target.PromptTarget("Target Lumber Beetle")
            elif bid == BTN_TARGET_FIREBEETLE:
                settings["fire_beetle_serial"] = Target.PromptTarget("Target Fire Beetle")
            elif bid == BTN_TARGET_FORGE:
                t = Target.PromptTarget("Target Forge")
                if t:
                    settings["forge_serials"].append(t)
            elif bid == BTN_CLEAR_FORGES:
                settings["forge_serials"] = []
            elif bid == BTN_TARGET_PACKIES:
                msg("Target packies (ESC to stop)...", 68)
                settings["packy_serials"] = []
                while True:
                    s = Target.PromptTarget("Packie (ESC to stop)")
                    if not s:
                        break
                    settings["packy_serials"].append(s)
            elif bid == BTN_TARGET_HOUSE:
                settings["house_container_serial"] = Target.PromptTarget("Target House Container")
            elif bid == BTN_SET_GATHER:
                opts = ["TreeID", "Self"]
                cur = settings["gather_method"]
                settings["gather_method"] = opts[(opts.index(cur) + 1) % len(opts)]


    # -------------------
    # Runtime logic
    # -------------------
    if _runtime_lumber:
        lumber_loop()

    if _runtime_mining:
        # mining loop will go here
        pass

    # Refresh UI
    render()
    Misc.Pause(REFRESH_MS)

# -------------------
# Cleanup
# -------------------
Gumps.CloseGump(GUMP_ID)
msg("FrogGath v0.3 stopped.", 33)

