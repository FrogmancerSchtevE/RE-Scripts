# ============================================
# ==  Frog Gatherer Suite v2.2 (Alpha)      ==
# ============================================
# Author: Frogmancer Schteve
#
# All-in-one harvesting assistant:
#   - Mining (Self Pilot, Strip Mine, Recall Mining)
#   - Lumberjacking (Self Pilot, Auto Pilot, Semi Manual)
#   - Cotton (Picker, Auto Picker, Weaver)
#
# This file now includes:
#   - Full Cotton Suite logic (inline)
#   - Shared Resource Handling Core
#   - Full Lumberjack Suite implementation
#
# NOTICE:
# This script is intended for personal use and community sharing.
# It is NOT intended to be fed into machine learning models, AI
# training pipelines, or derivative automated systems.
#
# If you found this, great! Use it, learn from it, and adapt it.
# But please don’t upload, re-ingest, or recycle it into LLMs.
#
# Contribute your own creativity instead — that’s how we built this.
#

from AutoComplete import *
from System import Int32
from System.Collections.Generic import List as CList, List
import time
from math import sqrt
import System
from System.Media import SoundPlayer, SystemSounds

# ===========================================================
# CONFIGURATION
# ===========================================================

GUMP_ID    = 0xF917C0DE
REFRESH_MS = 700
GUMP_X, GUMP_Y = 600, 300

# Pages
PAGE_MINING    = 0
PAGE_LUMBER    = 1
PAGE_COTTON    = 2
PAGE_SETTINGS  = 3

PAGE_NAMES = [
    "Mining",
    "Lumberjack",
    "Cotton",
    "Settings",
]

# Mining modes
MINING_MODE_SELF   = 1  # Self Pilot
MINING_MODE_STRIP  = 2  # Strip Mine
MINING_MODE_RECALL = 3  # Recall Mining

# Lumber modes
LUMBER_MODE_SELF  = 1  # Self Pilot
LUMBER_MODE_AUTO  = 2  # Auto Pilot
LUMBER_MODE_SEMI  = 3  # Semi Manual

# Cotton modes
COTTON_MODE_PICKER   = 1
COTTON_MODE_AUTOPICK = 2
COTTON_MODE_WEAVER   = 3

# SharedValue keys (for persistence)
SV_CLICK_KEY            = "FrogGathererSuite_Click"
SV_HOME_RUNE            = "fgs_general_home_rune"
SV_BANK_RUNE            = "fgs_general_bank_rune"

SV_MINING_FIRE_BEETLE   = "fgs_mining_fire_beetle"
SV_MINING_FORGE         = "fgs_mining_forge"
SV_MINING_GIANT_BEETLE  = "fgs_mining_giant_beetle"
SV_MINING_SATCHEL       = "fgs_mining_satchel"
SV_MINING_SMELT_MODE    = "fgs_mining_smelt_mode"    # "bulk" / "single"
SV_MINING_SMELT_TARGET  = "fgs_mining_smelt_target"  # "forge" / "beetle" / "auto"

SV_LUMBER_PACKY         = "fgs_lumber_packy"
SV_LUMBER_BEETLE        = "fgs_lumber_beetle"
SV_LUMBER_SATCHEL       = "fgs_lumber_satchel"

SV_COTTON_WHEEL         = "fgs_cotton_wheel"
SV_COTTON_LOOM          = "fgs_cotton_loom"

SV_AUTO_HIDE_ENABLED    = "fgs_general_auto_hide"

# Core item IDs
LOG_ID   = 0x1BDD
BOARD_ID = 0x1BD7

# Ore/ingot IDs for mining
ORE_IDS   = [0x19B7, 0x19B8, 0x19B9, 0x19BA, 0x19B2, 0x19B3]
INGOT_ID  = 0x1BF2
INGOT_IDS = [INGOT_ID]

# Mining tools: pickaxes, sturdy picks, garg pick, shovel
miningTools = [0x0E86, 0x0E85, 0x0FB4, 0x0F39]

# Storage mode label helper
MINING_MODES = ["firebeetle", "giantbeetle", "forge"]

# ===========================================================
# GLOBAL STATE
# ===========================================================

_running        = True
_current_page   = PAGE_MINING
_status_msg     = "Idle."

# Runtime toggles
_runtime_mining = False
_runtime_lumber = False
_runtime_cotton = False

# Mode selections
_mining_mode  = MINING_MODE_SELF
_lumber_mode  = LUMBER_MODE_SELF
_cotton_mode  = COTTON_MODE_PICKER

# General Globals
_auto_hide_enabled = False
_last_hide_attempt = 0

# Persisted serials (cached copies of SharedValues)
_home_rune        = 0
_bank_rune        = 0

_mining_firebet      = 0
_mining_forge        = 0
_mining_giantbeet    = 0
_mining_satchel      = 0
_mining_smelt_mode   = "bulk"
_mining_smelt_target = "auto"

_lumber_packy     = 0
_lumber_beetle    = 0
_lumber_satchel   = 0

_cotton_wheel     = 0
_cotton_loom      = 0

_last_button      = 0

_mining_mode_display = "firebeetle"

# Cotton internal globals
_last_clicked_cotton = {}
_last_count_cotton   = -1
_field_index         = 0
_started_autopick    = False
_next_bank_release   = 0
_arrived_at_field    = False

_cached_wheel_serial = 0
_cached_loom_serial  = 0
_next_spin_ready     = 0.0

# Lumber internal globals
TREE_IDS = [
    0x0C95, 0x0C96, 0x0C99, 0x0C9B, 0x0C9C, 0x0C9D, 0x0C8A, 0x0CA6,
    0x0CA8, 0x0CAA, 0x0CAB, 0x0CC3, 0x0CC4, 0x0CC8, 0x0CC9, 0x0CCA, 0x0CCB,
    0x0CCC, 0x0CCD, 0x0CD0, 0x0CD3, 0x0CD6
]
TREE_SCAN_RADIUS  = 10
TREE_COOLDOWN_MS  = 20 * 60 * 1000  # 20 minutes
WAIT_CHOP_MS      = 5000
_lumber_trees     = []
_lumber_visited   = []
_lumber_tree_idx  = 0

_last_button      = 0

# ===========================================================
# BUTTON IDS
# ===========================================================

BTN_CLOSE       = 9000
BTN_PAGE_PREV   = 9001
BTN_PAGE_NEXT   = 9002

# Mining page buttons
BTN_MINING_RUN         = 9100
BTN_MINING_MODE_SELF   = 9101
BTN_MINING_MODE_STRIP  = 9102
BTN_MINING_MODE_RECALL = 9103

# Lumber page buttons
BTN_LUMBER_RUN        = 9200
BTN_LUMBER_MODE_SELF  = 9201
BTN_LUMBER_MODE_AUTO  = 9202
BTN_LUMBER_MODE_SEMI  = 9203

# Cotton page buttons
BTN_COTTON_RUN           = 9300
BTN_COTTON_MODE_PICKER   = 9301
BTN_COTTON_MODE_AUTOPICK = 9302
BTN_COTTON_MODE_WEAVER   = 9303

# Settings page buttons
# General
BTN_SET_HOME_RUNE    = 9400
BTN_SET_BANK_RUNE    = 9401
BTN_TOGGLE_AUTO_HIDE = 9402
BTN_RESET_SERIALS    = 9410

# Mining settings
BTN_TOGGLE_MINING_MODE      = 9450
BTN_SET_MINING_FIRE_BEETLE  = 9451
BTN_SET_MINING_GIANT_BEETLE = 9452
BTN_SET_MINING_FORGE        = 9453
BTN_SET_MINING_SATCHEL      = 9454
BTN_TOGGLE_SMELT_MODE       = 9455
BTN_TOGGLE_SMELT_TARGET     = 9456

# Lumber settings
BTN_SET_LUMBER_PACKY   = 9500
BTN_SET_LUMBER_BEETLE  = 9501
BTN_SET_LUMBER_SATCHEL = 9502

# Cotton settings
BTN_SET_COTTON_WHEEL   = 9550
BTN_SET_COTTON_LOOM    = 9551

# ===========================================================
# SMALL HELPERS
# ===========================================================

def format_serial(s):
    try:
        if not s:
            return "None"
        return "0x{0:X}".format(int(s))
    except:
        return "None"

def read_shared_int(key, default=0):
    try:
        if Misc.CheckSharedValue(key):
            return int(Misc.ReadSharedValue(key))
    except:
        pass
    return default

def read_shared_str(key, default=""):
    try:
        if Misc.CheckSharedValue(key):
            val = Misc.ReadSharedValue(key)
            if isinstance(val, str):
                return val
            return str(val)
    except:
        pass
    return default

def write_shared(key, value):
    try:
        Misc.SetSharedValue(key, value)
    except:
        pass

def remove_shared(key):
    try:
        if Misc.CheckSharedValue(key):
            Misc.RemoveSharedValue(key)
    except:
        pass

def load_persisted_settings():
    global _home_rune, _bank_rune
    global _mining_firebet, _mining_forge, _mining_giantbeet, _mining_satchel
    global _mining_smelt_mode, _mining_smelt_target
    global _lumber_packy, _lumber_beetle, _lumber_satchel
    global _cotton_wheel, _cotton_loom
    global _cached_wheel_serial, _cached_loom_serial
    global _auto_hide_enabled

    _home_rune   = read_shared_int(SV_HOME_RUNE, 0)
    _bank_rune   = read_shared_int(SV_BANK_RUNE, 0)

    _mining_firebet     = read_shared_int(SV_MINING_FIRE_BEETLE, 0)
    _mining_forge       = read_shared_int(SV_MINING_FORGE, 0)
    _mining_giantbeet   = read_shared_int(SV_MINING_GIANT_BEETLE, 0)
    _mining_satchel     = read_shared_int(SV_MINING_SATCHEL, 0)
    _mining_smelt_mode  = read_shared_str(SV_MINING_SMELT_MODE, "bulk")
    _mining_smelt_target= read_shared_str(SV_MINING_SMELT_TARGET, "auto")

    _lumber_packy   = read_shared_int(SV_LUMBER_PACKY, 0)
    _lumber_beetle  = read_shared_int(SV_LUMBER_BEETLE, 0)
    _lumber_satchel = read_shared_int(SV_LUMBER_SATCHEL, 0)

    _cotton_wheel   = read_shared_int(SV_COTTON_WHEEL, 0)
    _cotton_loom    = read_shared_int(SV_COTTON_LOOM, 0)

    _cached_wheel_serial = _cotton_wheel
    _cached_loom_serial  = _cotton_loom

    _auto_hide_enabled = bool(read_shared_int(SV_AUTO_HIDE_ENABLED, 0))

def reset_all_serials():
    global _home_rune, _bank_rune
    global _mining_firebet, _mining_forge, _mining_giantbeet, _mining_satchel
    global _lumber_packy, _lumber_beetle, _lumber_satchel
    global _cotton_wheel, _cotton_loom
    global _cached_wheel_serial, _cached_loom_serial

    for key in [
        SV_HOME_RUNE, SV_BANK_RUNE,
        SV_MINING_FIRE_BEETLE, SV_MINING_FORGE,
        SV_MINING_GIANT_BEETLE, SV_MINING_SATCHEL,
        SV_LUMBER_PACKY, SV_LUMBER_BEETLE, SV_LUMBER_SATCHEL,
        SV_COTTON_WHEEL, SV_COTTON_LOOM,
        SV_MINING_SMELT_MODE, SV_MINING_SMELT_TARGET,
    ]:
        remove_shared(key)

    _home_rune = _bank_rune = 0
    _mining_firebet = _mining_forge = 0
    _mining_giantbeet = _mining_satchel = 0
    _lumber_packy = _lumber_beetle = _lumber_satchel = 0
    _cotton_wheel = _cotton_loom = 0
    _cached_wheel_serial = 0
    _cached_loom_serial  = 0

def mining_mode_label():
    if _mining_mode == MINING_MODE_SELF:
        return "Self Pilot"
    if _mining_mode == MINING_MODE_STRIP:
        return "Strip Mine"
    if _mining_mode == MINING_MODE_RECALL:
        return "Recall Mining"
    return "Unknown"

def mining_storage_mode_label():
    mapping = {
        "firebeetle": "Fire Beetle + Satchel",
        "giantbeetle": "Giant Beetle + Forge",
        "forge": "Forge + Satchel",
    }
    return mapping.get(_mining_mode_display, "Unknown")

def lumber_mode_label():
    if _lumber_mode == LUMBER_MODE_SELF:
        return "Self Pilot"
    if _lumber_mode == LUMBER_MODE_AUTO:
        return "Auto Pilot"
    if _lumber_mode == LUMBER_MODE_SEMI:
        return "Semi Manual"
    return "Unknown"

def cotton_mode_label():
    if _cotton_mode == COTTON_MODE_PICKER:
        return "Picker"
    if _cotton_mode == COTTON_MODE_AUTOPICK:
        return "Auto Picker"
    if _cotton_mode == COTTON_MODE_WEAVER:
        return "Weaver"
    return "Unknown"

def player_xy():
    return Player.Position.X, Player.Position.Y

def is_overweight(threshold=0.8):
    try:
        return Player.Weight >= int(Player.MaxWeight * float(threshold))
    except:
        return False

def check_stop_runtime():
    if not _runtime_lumber and not _runtime_mining and not _runtime_cotton:
        raise Exception("STOP_SIGNAL")

def check_runtime(active_flag):
    if not active_flag:
        raise StopIteration("Runtime stop signal received")
        
# ===========================================================
# COTTON SUITE (CTNCORE)
# ===========================================================

# --- Picker Configs (Manual / Auto) ---
COTTON_PLANT_IDS   = [0x0C51, 0x0C52, 0x0C53, 0x0C54]
COTTON_ITEM_ID     = 0x0DF9
SCAN_RANGE_TILES   = 20
PICK_REACH_TILES   = 1
CLICK_PAUSE_MS     = 180
LOOP_PAUSE_MS      = 200
PLANT_COOLDOWN_SEC = 10
HIGHLIGHT_HUE      = 1152

FIELDS = [
    (1198, 1822),
    (1222, 1723),
    (1190, 1683),
    (1118, 1623),
    (1151, 1574)
]
SAFE_SPOT = (1410, 1733)

INITIAL_ROUTE_TO_FIELD1 = [
    (1386,1748),(1352,1752),(1318,1752),
    (1285,1746),(1249,1771),(1222,1807),
    (1198,1822)
]

FIELD_ROUTES = {
    1: [(1222,1723)],
    2: [(1190,1683)],
    3: [(1118,1623)],
    4: [(1151,1574)],
    5: [
        (1179,1596),(1188,1636),(1224,1663),
        (1255,1678),(1283,1707),(1309,1742),
        (1336,1751),(1383,1751),(1406,1742),
        (1410,1733)
    ]
}

BANK_ROUTE_UP = [
    (1410,1733),
    (1418,1721),
    (1418,1701),
    (1427,1699),
    (1422,1693)
]
BANK_ROUTE_DOWN = [
    (1432,1693),
    (1427,1699),
    (1418,1701),
    (1418,1721),
    (1404,1735),
    (1410,1733)
]

FIELD_LABEL = {
    0: "Field 1",
    1: "Field 2",
    2: "Field 3",
    3: "Field 4",
    4: "Field 5"
}

IDLE_BANK_SEC = 600  # 10 minutes idle at bank in auto mode

# Weaver configs
SPINNING_WHEEL_GRAPHICS = [0x1015, 0x1019, 0x101A, 0x101B]
LOOM_GRAPHICS           = [0x105F, 0x1060, 0x1061, 0x1062]

COTTON_TYPE_ID = 0x0DF9
SPOOL_TYPE_ID  = 0x0FA0

TARGET_TIMEOUT_MS   = 2000
SPIN_PAUSE_MS       = 4600
WEAVE_STEP_DELAY_MS = 120
JOURNAL_MSG_BOLT    = "You create some cloth"


def manhattan(ax, ay, bx, by):
    return abs(ax - bx) + abs(ay - by)

def find_cotton_plants():
    g_list = List[Int32]()
    for g in COTTON_PLANT_IDS:
        g_list.Add(g)

    f = Items.Filter()
    f.Enabled  = True
    f.OnGround = True
    f.RangeMax = SCAN_RANGE_TILES
    f.Graphics = g_list

    net_items = Items.ApplyFilter(f) or []
    items     = [it for it in net_items]

    px, py = player_xy()
    items.sort(key=lambda it: manhattan(px, py, it.Position.X, it.Position.Y))
    return items

def find_ground_cotton():
    g_list = List[Int32]()
    g_list.Add(COTTON_ITEM_ID)
    f = Items.Filter()
    f.Enabled  = True
    f.OnGround = True
    f.RangeMax = 2
    f.Graphics = g_list
    return list(Items.ApplyFilter(f) or [])

def in_reach(it):
    px, py = player_xy()
    return manhattan(px, py, it.Position.X, it.Position.Y) <= PICK_REACH_TILES

def highlight(it):
    try:
        Items.SetColor(it.Serial, HIGHLIGHT_HUE)
    except:
        pass

def click_plant(serial):
    try:
        Misc.DoubleClick(serial)
        return True
    except:
        try:
            Items.UseItem(serial)
            return True
        except:
            return False

def loot_cotton():
    bales = find_ground_cotton()
    for bale in bales:
        if bale and bale.Movable:
            Player.HeadMessage(68, "Grabbing cotton bale")
            Items.Move(bale, Player.Backpack.Serial, 0)
            Misc.Pause(600)

def cotton_step_picker():
    global _status_msg, _last_count_cotton, _last_clicked_cotton
    plants = find_cotton_plants()
    now    = time.monotonic()

    if len(plants) != _last_count_cotton:
        if plants:
            Player.HeadMessage(55, "Found {0} cotton plants nearby".format(len(plants)))
        else:
            Player.HeadMessage(33, "No cotton detected nearby")
        _last_count_cotton = len(plants)

    for p in plants:
        highlight(p)
        if now - _last_clicked_cotton.get(p.Serial, 0.0) < PLANT_COOLDOWN_SEC:
            continue

        if not in_reach(p):
            continue

        _status_msg = "Picking cotton..."
        Player.HeadMessage(68, "Picking cotton")
        if click_plant(p.Serial):
            _last_clicked_cotton[p.Serial] = now
            Misc.Pause(CLICK_PAUSE_MS)
            loot_cotton()
            return

    _status_msg = "Idle"
    Misc.Pause(LOOP_PAUSE_MS)

def get_one_cotton():
    return Items.FindByID(COTTON_TYPE_ID, -1, Player.Backpack.Serial)

def get_one_spool():
    return Items.FindByID(SPOOL_TYPE_ID, -1, Player.Backpack.Serial)

def count_spools():
    try:
        return Items.BackpackCount(SPOOL_TYPE_ID, -1) or 0
    except:
        return 0

def get_wheel_serial():
    global _cached_wheel_serial, _cotton_wheel, _status_msg
    if _cached_wheel_serial:
        return _cached_wheel_serial
    if _cotton_wheel:
        _cached_wheel_serial = _cotton_wheel
        return _cached_wheel_serial

    Misc.SendMessage("Target your SPINNING WHEEL.", 55)
    s = Target.PromptTarget("Target your SPINNING WHEEL.", 0x3B2)
    if s and s > 0:
        _cached_wheel_serial = s
        _cotton_wheel = s
        write_shared(SV_COTTON_WHEEL, s)
        Misc.SendMessage("Wheel cached.", 68)
    else:
        _status_msg = "No wheel selected."
    return _cached_wheel_serial

def get_loom_serial():
    global _cached_loom_serial, _cotton_loom, _status_msg
    if _cached_loom_serial:
        return _cached_loom_serial
    if _cotton_loom:
        _cached_loom_serial = _cotton_loom
        return _cached_loom_serial

    Misc.SendMessage("Target your LOOM.", 55)
    s = Target.PromptTarget("Target your LOOM.", 0x3B2)
    if s and s > 0:
        _cached_loom_serial = s
        _cotton_loom = s
        write_shared(SV_COTTON_LOOM, s)
        Misc.SendMessage("Loom cached.", 68)
    else:
        _status_msg = "No loom selected."
    return _cached_loom_serial

def spin_one_bale_if_ready():
    global _next_spin_ready, _status_msg
    now = time.monotonic()
    if now < _next_spin_ready:
        return False

    wheel = get_wheel_serial()
    if not wheel:
        return False
    bale = get_one_cotton()
    if not bale:
        return False

    Items.UseItem(bale.Serial)
    if not Target.WaitForTarget(TARGET_TIMEOUT_MS, False):
        return False
    Target.TargetExecute(wheel)

    _next_spin_ready = now + (SPIN_PAUSE_MS / 1000.0)
    _status_msg = "Spinning cotton..."
    return True

def journal_saw_bolt(timeout_ms=1000):
    start = time.time()
    Journal.Clear()
    while time.time() - start < (timeout_ms / 1000.0):
        if Journal.Search(JOURNAL_MSG_BOLT):
            Journal.Clear()
            return True
        Misc.Pause(20)
    return False

def weave_one_spool_safely():
    global _status_msg
    loom = get_loom_serial()
    if not loom:
        return False
    sp = get_one_spool()
    if not sp:
        return False

    Items.UseItem(sp.Serial)
    if not Target.WaitForTarget(TARGET_TIMEOUT_MS, False):
        return False
    Target.TargetExecute(loom)
    Misc.Pause(WEAVE_STEP_DELAY_MS)

    if journal_saw_bolt(600):
        Misc.SendMessage("Bolt completed.", 68)
        _status_msg = "Bolt completed"
        return "bolt"
    return True

def cotton_step_weaver():
    global _status_msg

    spun = False
    if get_one_cotton():
        if spin_one_bale_if_ready():
            spun = True

    if count_spools() > 0:
        res = weave_one_spool_safely()
        if res == "bolt":
            _status_msg = "Bolt completed"
        elif res:
            _status_msg = "Weaving spools..."
        else:
            _status_msg = "Weave failed/timeout"
    elif not spun and not get_one_cotton():
        _status_msg = "Idle (no cotton or spools)"

def go_via_waypoints(waypoints):
    global _status_msg
    for (x, y) in waypoints:
        route = PathFinding.Route()
        route.X = x
        route.Y = y
        route.MaxRetry    = 3
        route.StopIfStuck = False
        _status_msg = "Moving to {0},{1}".format(x, y)
        Misc.SendMessage("Moving to {0},{1}".format(x, y), 55)
        if not PathFinding.Go(route):
            _status_msg = "Path failed at {0},{1}".format(x, y)
            Misc.SendMessage("Path failed at {0},{1}".format(x, y), 33)
            return False
        Misc.Pause(300)
    return True

def go_to_field(index):
    if index not in FIELD_ROUTES:
        Misc.SendMessage("No route defined for field {0}".format(index), 33)
        return False
    if go_via_waypoints(FIELD_ROUTES[index]):
        Misc.SendMessage("Arrived at {0}".format(FIELD_LABEL.get(index, "Field?")), 68)
        return True
    return False

def go_to_bank():
    return go_via_waypoints(BANK_ROUTE_UP)

def leave_bank_to_safe():
    return go_via_waypoints(BANK_ROUTE_DOWN)

def cotton_step_autopick():
    global _status_msg, _field_index, _last_clicked_cotton, _started_autopick
    global _next_bank_release, _arrived_at_field

    now = time.monotonic()

    if _status_msg.startswith("Idle at Bank"):
        remaining = int(_next_bank_release - now)
        if remaining > 0:
            mins, secs = divmod(remaining, 60)
            _status_msg = "Idle at Bank ({0:02}:{1:02} left)".format(mins, secs)
            Misc.Pause(400)
            return
        Misc.SendMessage("Bank idle finished, leaving bank", 68)
        leave_bank_to_safe()
        Misc.SendMessage("Now heading to Field 1", 68)
        _field_index = 0
        go_via_waypoints(INITIAL_ROUTE_TO_FIELD1)
        _arrived_at_field = True
        _status_msg = "Walking to Field 1"
        return

    if not _started_autopick:
        go_via_waypoints(INITIAL_ROUTE_TO_FIELD1)
        _field_index       = 0
        _arrived_at_field  = True
        _started_autopick  = True
        _status_msg        = "Walking to Field 1"
        return

    plants = find_cotton_plants()
    if plants:
        _status_msg = "Auto-Picking {0}".format(FIELD_LABEL.get(_field_index, "Field"))
        for p in plants:
            highlight(p)
            if now - _last_clicked_cotton.get(p.Serial, 0.0) < PLANT_COOLDOWN_SEC:
                continue
            if not in_reach(p):
                offsets = [(0,1),(1,0),(-1,0),(0,-1)]
                moved = False
                for dx, dy in offsets:
                    route = PathFinding.Route()
                    route.X = p.Position.X + dx
                    route.Y = p.Position.Y + dy
                    route.MaxRetry    = 2
                    route.StopIfStuck = False
                    if PathFinding.Go(route):
                        moved = True
                        Misc.Pause(250)
                        break
                if not moved:
                    continue

            _status_msg = "Picking cotton..."
            if click_plant(p.Serial):
                _last_clicked_cotton[p.Serial] = now
                Misc.Pause(CLICK_PAUSE_MS)
                loot_cotton()
                return
    else:
        if _arrived_at_field:
            Misc.SendMessage(
                "No cotton at {0}".format(FIELD_LABEL.get(_field_index, "Field")),
                33
            )
            _arrived_at_field = False
            Misc.Pause(200)
            return

        if _field_index < len(FIELD_ROUTES) - 1:
            _field_index += 1
            go_to_field(_field_index)
            _arrived_at_field = True
            _status_msg = "Walking to {0}".format(FIELD_LABEL.get(_field_index, "Field"))
        else:
            Misc.SendMessage("All fields empty → idling at Bank", 33)
            go_to_bank()
            _next_bank_release = now + IDLE_BANK_SEC
            mins, secs = divmod(IDLE_BANK_SEC, 60)
            _status_msg = "Idle at Bank ({0:02}:{1:02} left)".format(mins, secs)
            _field_index = 0


# ===========================================================
# RESOURCE HANDLING CORE (RHCORE)
# ===========================================================

def get_storage_container_serial(target_serial):
    if not target_serial:
        return 0
    mob = Mobiles.FindBySerial(target_serial)
    if mob and mob.Backpack:
        return mob.Backpack.Serial
    item = Items.FindBySerial(target_serial)
    if item:
        return item.Serial
    return 0

def mobile_distance(mob):
    try:
        return abs(Player.Position.X - mob.Position.X) + abs(Player.Position.Y - mob.Position.Y)
    except:
        return 9999

def ensure_beetle_dismounted(serial):
    if not serial:
        return False
    try:
        mount = Player.GetMount()
        if mount and mount.Serial == serial:
            Player.Dismount()
            Misc.Pause(600)
            return True
    except:
        pass
    return False

def remount_if_needed(serial):
    if not serial:
        return False
    try:
        mount = Mobiles.FindBySerial(serial)
        if mount:
            current_mount = Player.GetMount()
            if not current_mount or current_mount.Serial != serial:
                Misc.SendMessage("Remounting beetle...", 55)
                Mobiles.UseMobile(serial)
                Misc.Pause(800)
                return True
    except:
        pass
    return False

def is_valid_storage(target_serial, max_distance=15):
    if not target_serial:
        return False

    ensure_beetle_dismounted(target_serial)

    mob = Mobiles.FindBySerial(target_serial)
    if mob:
        if mob.IsGhost:
            return False
        if mobile_distance(mob) <= max_distance and mob.Backpack:
            return True
        return False

    item = Items.FindBySerial(target_serial)
    if item:
        return abs(Player.Position.X - item.Position.X) + abs(Player.Position.Y - item.Position.Y) <= max_distance
    return False

def find_beetle():
    f = Mobiles.Filter()
    f.RangeMax = 10
    f.Bodies = List[Int32]([0x0317])
    result = Mobiles.ApplyFilter(f)
    return result[0] if result else None

def deposit_items_by_ids(item_ids, storage_candidates, label="items"):
    global _status_msg

    if not storage_candidates:
        _status_msg = "No storage configured"
        return False

    to_move = [it for it in Player.Backpack.Contains if it.ItemID in item_ids]
    if not to_move:
        return False

    moved_any = False
    beetle = None

    if Player.Mount:
        Misc.SendMessage("Dismounting for storage actions...", 55)
        Mobiles.UseMobile(Player.Serial)
        Misc.Pause(1200)
        if Player.Mount:
            Misc.SendMessage("Failed to dismount.", 33)
            return False

    beetle = find_beetle()

    for it in to_move:
        placed = False
        for target in storage_candidates:
            if not target:
                continue
            mob = Mobiles.FindBySerial(target)
            if mob and mob.Backpack:
                Items.Move(it, mob.Backpack.Serial, 0)
                Misc.Pause(400)
                moved_any = True
                placed = True
                break
        if not placed and beetle and beetle.Backpack:
            Items.Move(it, beetle.Backpack.Serial, 0)
            Misc.Pause(400)
            moved_any = True

    if beetle and not Player.Mount:
        Misc.SendMessage("Remounting beetle...", 55)
        retry_count = 0
        max_retries = 5
        success = False
        while retry_count < max_retries and not Player.Mount:
            Journal.Clear()
            Mobiles.UseMobile(beetle.Serial)
            Misc.Pause(1000)
            if Journal.Search("You must wait"):
                Misc.SendMessage("Server delay detected, retrying remount...", 33)
                Misc.Pause(1000)
                retry_count += 1
                continue
            if Player.Mount:
                success = True
                break
            retry_count += 1
        if success:
            Misc.SendMessage("Remounted beetle successfully.", 68)
        else:
            Misc.SendMessage("Failed to remount beetle after retries.", 33)

    if moved_any:
        _status_msg = "Deposited {0} to storage".format(label)
        return True

    _status_msg = "No valid storage found for {0}".format(label)
    return False

def deposit_logs_to_storage():
    candidates = []
    if _lumber_packy:
        candidates.append(_lumber_packy)
    if _lumber_beetle and _lumber_beetle not in candidates:
        candidates.append(_lumber_beetle)
    if _lumber_satchel and _lumber_satchel not in candidates:
        candidates.append(_lumber_satchel)
    return deposit_items_by_ids([LOG_ID, BOARD_ID], candidates, "logs/boards")

def deposit_ore_to_storage():
    candidates = []
    if _mining_giantbeet:
        candidates.append(_mining_giantbeet)
    if _mining_firebet and _mining_firebet not in candidates:
        candidates.append(_mining_firebet)
    ids = list(ORE_IDS)
    ids.append(INGOT_ID)
    return deposit_items_by_ids(ids, candidates, "ore/ingots")

# ===========================================================
# LUMBERJACK SUITE (LJCORE)
# ===========================================================

def find_hatchet():
    for layer in ['LeftHand', 'RightHand']:
        item = Player.GetItemOnLayer(layer)
        if item and item.ItemID == 0x0F43:
            return item
    return Items.FindByID(0x0F43, -1, Player.Backpack.Serial)

def cut_tree_self():
    hatchet = find_hatchet()
    if not hatchet:
        Misc.SendMessage("No hatchet found!", 33)
        return False

    if not Player.GetItemOnLayer('LeftHand') and not Player.GetItemOnLayer('RightHand'):
        Player.EquipItem(hatchet)
        Misc.Pause(600)

    Items.UseItem(hatchet)
    if not Target.WaitForTarget(1200, False):
        return False
    Target.TargetExecute(Player.Serial)
    Misc.Pause(600)
    return True

def cut_logs_in_pack():
    hatchet = find_hatchet()
    if not hatchet:
        return False

    found_logs = False
    for item in list(Player.Backpack.Contains):
        if item.ItemID == LOG_ID:
            Items.UseItem(hatchet)
            if Target.WaitForTarget(1500, False):
                Target.TargetExecute(item)
                Misc.Pause(1800)
                found_logs = True
    return found_logs

def journal_no_wood_here():
    if Journal.Search("There's not enough wood here to harvest."):
        Journal.Clear()
        return True
    return False

class Tree:
    def __init__(self, x, y, z, tileid):
        self.x = x
        self.y = y
        self.z = z
        self.id = tileid

def scan_for_trees():
    global _lumber_trees
    _lumber_trees = []
    px, py = player_xy()
    Misc.SendMessage("Scanning for trees...", 55)
    for x in range(px - TREE_SCAN_RADIUS, px + TREE_SCAN_RADIUS + 1):
        for y in range(py - TREE_SCAN_RADIUS, py + TREE_SCAN_RADIUS + 1):
            tiles = Statics.GetStaticsTileInfo(x, y, 0)
            for tile in tiles:
                if tile.StaticID in TREE_IDS:
                    key = (x, y)
                    if key not in _lumber_visited and not Timer.Check("{0},{1}".format(x, y)):
                        _lumber_trees.append(Tree(x, y, tile.StaticZ, tile.StaticID))
    _lumber_trees.sort(key=lambda t: sqrt((t.x - px) ** 2 + (t.y - py) ** 2))
    Misc.SendMessage("Total trees found: {0}".format(len(_lumber_trees)), 68)

def move_to_tree(tree):
    Misc.SendMessage("Trying to path to {0},{1}".format(tree.x, tree.y), 55)
    offsets = [(0, 1), (1, 0), (-1, 0), (0, -1)]
    for dx, dy in offsets:
        dest = PathFinding.Route()
        dest.X = tree.x + dx
        dest.Y = tree.y + dy
        dest.MaxRetry    = 3
        dest.StopIfStuck = False
        Misc.SendMessage("Trying {0},{1}".format(dest.X, dest.Y), 55)
        if PathFinding.Go(dest):
            Misc.SendMessage("Pathing succeeded.", 68)
            Misc.Pause(1000)
            return True
        Misc.Pause(250)

    Misc.SendMessage("All path attempts failed.", 33)
    return False

def wait_for_depletion_or_threshold():
    Journal.Clear()
    Timer.Create("waitChop", WAIT_CHOP_MS)
    while not Journal.Search("There's not enough wood here to harvest.") and Timer.Check("waitChop"):
        if is_overweight(0.8):
            Misc.SendMessage("Overweight during chop; breaking.", 55)
            break
        cut_tree_self()
        Misc.Pause(800)
    Journal.Clear()

def lumber_step_self_pilot():
    global _status_msg
    try:
        check_runtime(_runtime_lumber)

        # --- Weight check ---
        if is_overweight(0.8):
            _status_msg = "Overweight, processing lumber..."
            cut_logs_in_pack()
            deposit_logs_to_storage()
            check_runtime(_runtime_lumber)
            Misc.Pause(600)
            return

        check_runtime(_runtime_lumber)

        # --- No wood message check ---
        if journal_no_wood_here():
            _status_msg = "No wood here."
            Misc.Pause(400)
            return

        check_runtime(_runtime_lumber)

        # --- Perform chopping action ---
        if cut_tree_self():
            _status_msg = "Chopping (Self Pilot)..."
            Misc.Pause(800)
        else:
            _status_msg = "No hatchet found."
            Misc.Pause(600)

        check_runtime(_runtime_lumber)

    except StopIteration:
        _status_msg = "Stopped."
        return

def lumber_step_auto_pilot():
    global _status_msg, _lumber_trees, _lumber_tree_idx, _lumber_visited
    try:
        check_runtime(_runtime_lumber)

        # Check for overweight condition
        if is_overweight(0.8):
            _status_msg = "Overweight, processing lumber..."
            cut_logs_in_pack()
            deposit_logs_to_storage()
            check_runtime(_runtime_lumber)
            Misc.Pause(600)
            return

        # Tree list exhausted or empty, rescan
        if not _lumber_trees or _lumber_tree_idx >= len(_lumber_trees):
            scan_for_trees()
            _lumber_tree_idx = 0
            check_runtime(_runtime_lumber)
            if not _lumber_trees:
                _status_msg = "No trees found nearby."
                Misc.Pause(800)
                return

        # Safety check for index bounds
        if _lumber_tree_idx >= len(_lumber_trees):
            _status_msg = "No trees in queue."
            Misc.Pause(400)
            return

        # Select next target tree
        tree = _lumber_trees[_lumber_tree_idx]
        coord_key = (tree.x, tree.y)

        # Skip trees recently chopped
        if coord_key in _lumber_visited or Timer.Check("{0},{1}".format(tree.x, tree.y)):
            _lumber_tree_idx += 1
            return

        # Attempt to move to target tree
        check_runtime(_runtime_lumber)
        if not move_to_tree(tree):
            _status_msg = "Path failed, skipping tree."
            _lumber_tree_idx += 1
            Misc.Pause(400)
            return

        # Chop and wait for depletion or weight threshold
        check_runtime(_runtime_lumber)
        _status_msg = "Chopping at tree {0},{1}".format(tree.x, tree.y)
        wait_for_depletion_or_threshold()

        # Mark tree as visited and cooldown timer
        _lumber_visited.append(coord_key)
        Timer.Create("{0},{1}".format(tree.x, tree.y), TREE_COOLDOWN_MS)
        _lumber_tree_idx += 1

        check_runtime(_runtime_lumber)
        Misc.Pause(200)

    except StopIteration:
        _status_msg = "Stopped."
        return

def lumber_step_semi_manual():
    global _status_msg
    if cut_tree_self():
        _status_msg = "Chopping (Semi Manual)..."
    else:
        _status_msg = "No hatchet found."
    Misc.Pause(800)
    
# ===========================================================
# MINING SUITE (MINECORE)
# ===========================================================
def find_equipped_mining_tool():
    for layer_name in ["RightHand", "LeftHand"]:
        item = Player.GetItemOnLayer(layer_name)
        if item and item.ItemID in miningTools:
            return item
    return None

def find_mining_tool_in_pack():
    for tool_id in miningTools:
        tool = Items.FindByID(tool_id, -1, Player.Backpack.Serial)
        if tool:
            return tool
    return None

def find_fire_beetle():
    """
    Prefer the user-configured fire beetle serial.
    Fallback to nearby fire beetle body IDs.
    """
    # 1) Use configured serial first
    if _mining_firebet:
        mob = Mobiles.FindBySerial(_mining_firebet)
        if mob:
            return mob

    # 2) Fallback to body search nearby
    beetle_body_ids = [0x031A]  # expand if your shard uses variants
    f = Mobiles.Filter()
    f.RangeMax = 8
    f.Bodies   = List[Int32](beetle_body_ids)
    result = Mobiles.ApplyFilter(f)
    return result[0] if result else None

def find_giant_beetle():
    f = Mobiles.Filter()
    f.RangeMax = 8
    f.Bodies = List[Int32]([0x0317])
    result = Mobiles.ApplyFilter(f)
    return result[0] if result else None

def find_worn_resource_satchel():
    for layer_name in ["OuterTorso", "MiddleTorso", "InnerTorso",
                       "Pants", "OuterLegs", "Waist"]:
        try:
            item = Player.GetItemOnLayer(layer_name)
        except:
            item = None
        if item and item.ItemID == 0x5576:
            return item
    return None

def find_nearest_forge_item():
    """
    Finds the closest forge item by checking known forge graphics.
    Works even if statics aren’t returned properly by the shard.
    """
    forge_ids = [0x0FB1, 0x197A, 0x197E, 0x1982, 0x1996]  # Common forge types

    f = Items.Filter()
    f.Enabled = True
    f.OnGround = True
    f.RangeMax = 12
    f.Graphics = List[Int32](forge_ids)

    items = Items.ApplyFilter(f)
    if not items or len(items) == 0:
        return None

    # Sort by distance
    items = sorted(items, key=lambda i: Player.DistanceTo(i))
    return items[0]


def smelt_ore_in_pack():
    """
    Smelt ores based on mining storage mode:

      - firebeetle:
          Smelt on fire beetle only, then store ingots in satchel > beetle.
      - giantbeetle:
          If a forge is configured, smelt on it; otherwise store raw ore.
      - forge:
          Smelt on configured forge, then store ingots in satchel.

    If no valid smelting target is available, raw ore is just stored.
    """
    ores = [i for i in Player.Backpack.Contains if i.ItemID in ORE_IDS]
    if not ores:
        return

    mode = _mining_mode_display.lower()

    # -------------------------------------------------------
    # 1) Fire Beetle + Satchel mode
    # -------------------------------------------------------
    if mode == "firebeetle":
        beetle = find_fire_beetle()
        if not beetle:
            Misc.SendMessage("No fire beetle found for smelting; storing raw ore.", 33)
            deposit_ore_to_storage()
            return

        Misc.SendMessage("Smelting on fire beetle...", 68)
        for ore in ores:
            check_runtime(_runtime_mining)
            Items.UseItem(ore)
            if Target.WaitForTarget(2000):
                Target.TargetExecute(beetle.Serial)
                Misc.Pause(700)

        deposit_ingots_to_preferred_storage()
        return

    # -------------------------------------------------------
    # 2) Giant Beetle + Forge mode
    #    - if forge configured, smelt there
    #    - if no forge, just store raw ore
    # -------------------------------------------------------
    if mode == "giantbeetle":
        forge = Items.FindBySerial(_mining_forge) if _mining_forge else None
        if forge:
            Misc.SendMessage("Smelting on configured forge...", 68)

            # Move closer if needed, highlight forge while out of range
            while Player.DistanceTo(forge) > 2:
                Misc.SendMessage("Move closer to forge!", 33)
                try:
                    Items.SetColor(forge.Serial, 1152)
                except:
                    pass
                Misc.Pause(1500)
            try:
                Items.SetColor(forge.Serial, 0)
            except:
                pass

            for ore in ores:
                check_runtime(_runtime_mining)
                Items.UseItem(ore)
                if Target.WaitForTarget(2000):
                    Target.TargetExecute(forge.Serial)
                    Misc.Pause(700)

            deposit_ingots_to_preferred_storage()
        else:
            Misc.SendMessage("No forge set; storing raw ores on beetle/satchel.", 33)
            deposit_ore_to_storage()
        return

    # -------------------------------------------------------
    # 3) Forge + Satchel mode
    # -------------------------------------------------------
    if mode == "forge":
        forge = Items.FindBySerial(_mining_forge) if _mining_forge else None
        if not forge:
            Misc.SendMessage("Forge mode selected but no forge set; storing raw ore.", 33)
            deposit_ore_to_storage()
            return

        Misc.SendMessage("Smelting on configured forge...", 68)
        while Player.DistanceTo(forge) > 2:
            Misc.SendMessage("Move closer to forge!", 33)
            try:
                Items.SetColor(forge.Serial, 1152)
            except:
                pass
            Misc.Pause(1500)
        try:
            Items.SetColor(forge.Serial, 0)
        except:
            pass

        for ore in ores:
            check_runtime(_runtime_mining)
            Items.UseItem(ore)
            if Target.WaitForTarget(2000):
                Target.TargetExecute(forge.Serial)
                Misc.Pause(700)

        deposit_ingots_to_preferred_storage()
        return

    # -------------------------------------------------------
    # Fallback: unknown mode, just store raw ore
    # -------------------------------------------------------
    Misc.SendMessage("Unknown mining mode; storing raw ores.", 33)
    deposit_ore_to_storage()

def deposit_ingots_to_preferred_storage():
    ingots = [i for i in Player.Backpack.Contains if i.ItemID in INGOT_IDS]
    if not ingots:
        return

    satchel = None
    beetle  = None

    if _mining_satchel:
        satchel = Items.FindBySerial(_mining_satchel)
    if not satchel:
        satchel = find_worn_resource_satchel()

    if _mining_giantbeet:
        beetle = Mobiles.FindBySerial(_mining_giantbeet)
    if not beetle:
        beetle = find_giant_beetle()

    dest_serial = None
    dest_label  = None

    if satchel:
        dest_serial = satchel.Serial
        dest_label  = "resource satchel"
    elif beetle and beetle.Backpack:
        dest_serial = beetle.Backpack.Serial
        dest_label  = "giant beetle"

    if not dest_serial:
        return

    Misc.SendMessage("Storing ingots in {0}...".format(dest_label), 55)
    for ingot in ingots:
        Items.Move(ingot, dest_serial, 0)
        Misc.Pause(500)

def mining_step_self_pilot():
    global _status_msg
    try:
        check_runtime(_runtime_mining)

        if Player.Mount:
            Misc.SendMessage("Dismounting before mining.", 55)
            Mobiles.UseMobile(Player.Serial)
            Misc.Pause(800)
            check_runtime(_runtime_mining)

        if is_overweight(0.8):
            _status_msg = "Overweight, smelting ore..."
            smelt_ore_in_pack()
            Misc.Pause(800)
            return

        check_runtime(_runtime_mining)

        tool = find_equipped_mining_tool() or find_mining_tool_in_pack()
        if not tool:
            _status_msg = "No mining tool found!"
            Misc.SendMessage("No pickaxe or shovel found!", 33)
            Misc.Pause(1000)
            return

        _status_msg = "Mining nearby veins..."
        Items.UseItem(tool)
        if Target.WaitForTarget(1500):
            Target.TargetExecute(Player.Serial)
        Misc.Pause(900)

        if Journal.Search("You put") or Journal.Search("ore"):
            _status_msg = "Collected ore."
        elif Journal.Search("no metal") or Journal.Search("too far"):
            _status_msg = "No ore found here."
        else:
            _status_msg = "Waiting for result..."

        check_runtime(_runtime_mining)
        Misc.Pause(400)

    except StopIteration:
        _status_msg = "Stopped."
        return

def mining_step_auto_pilot():
    global _status_msg
    _status_msg = "Auto Pilot Mining: Currently unavailable."
    Misc.SendMessage("Mining Auto Pilot mode is currently unavailable.", 33)
    Misc.Pause(1000)
    return

def mining_step_recall():
    global _status_msg
    _status_msg = "Recall Mining: Currently unavailable."
    Misc.SendMessage("Recall Mining mode is currently unavailable.", 33)
    Misc.Pause(1000)
    return
# ===========================================================
# Bonus Harvest Gumps Check (ANTIBOT)
# ===========================================================

# Number Captcha =  "0x968740"
# Picta Captcha = "0xd0c93672"

_last_gump_alert = 0
_last_gump_id = None

def check_special_gumps():
    """
    Detect special gumps and play an audible alert.
    Works in IronPython without System.Speech.
    """
    global _last_gump_alert, _last_gump_id

    try:
        gump = Gumps.CurrentGump()
        if not gump:
            return

        gid = int(gump.GumpID)
        target_gumps = [0x968740, 0xD0C93672]

        if gid in target_gumps:
            now = time.time()
            if gid != _last_gump_id or (now - _last_gump_alert) > 10:
                _last_gump_alert = now
                _last_gump_id = gid

                # --- Play system "Exclamation" sound ---
                SystemSounds.Exclamation.Play()

                Misc.SendMessage(f"Alert! Gump {hex(gid)} detected.", 68)
    except Exception as e:
        Misc.SendMessage(f"Gump check error: {e}", 33)

# ===========================================================
# GUI RENDERING
# ===========================================================

def render_mining_page(gd):
    mode_lbl = mining_mode_label()
    run_lbl  = "ON" if _runtime_mining else "OFF"
    run_hue  = 68 if _runtime_mining else 33

    Gumps.AddLabel(gd, 15, 40, 68, "Mining Suite")
    Gumps.AddLabel(gd, 15, 60, 81, "Mode: {0}".format(mode_lbl))
    Gumps.AddLabel(gd, 15, 80, 81, "Run: {0}".format(run_lbl))

    Gumps.AddButton(gd, 15, 110, 4017, 4018, BTN_MINING_MODE_SELF, 1, 0)
    Gumps.AddLabel(gd, 45, 112, 81 if _mining_mode == MINING_MODE_SELF else 33,
                   "Self Pilot")

    Gumps.AddButton(gd, 15, 140, 4017, 4018, BTN_MINING_MODE_STRIP, 1, 0)
    Gumps.AddLabel(gd, 45, 142, 81 if _mining_mode == MINING_MODE_STRIP else 33,
                   "Strip Mine")

    Gumps.AddButton(gd, 15, 170, 4017, 4018, BTN_MINING_MODE_RECALL, 1, 0)
    Gumps.AddLabel(gd, 45, 172, 81 if _mining_mode == MINING_MODE_RECALL else 33,
                   "Recall Mining")

    Gumps.AddButton(gd, 300, 40, 4017, 4018, BTN_MINING_RUN, 1, 0)
    Gumps.AddLabel(gd, 330, 42, run_hue, "Start/Stop")

def render_lumber_page(gd):
    mode_lbl = lumber_mode_label()
    run_lbl  = "ON" if _runtime_lumber else "OFF"
    run_hue  = 68 if _runtime_lumber else 33

    Gumps.AddLabel(gd, 15, 40, 68, "Lumberjack Suite")
    Gumps.AddLabel(gd, 15, 60, 81, "Mode: {0}".format(mode_lbl))
    Gumps.AddLabel(gd, 15, 80, 81, "Run: {0}".format(run_lbl))

    Gumps.AddButton(gd, 15, 110, 4017, 4018, BTN_LUMBER_MODE_SELF, 1, 0)
    Gumps.AddLabel(gd, 45, 112, 81 if _lumber_mode == LUMBER_MODE_SELF else 33,
                   "Self Pilot")

    Gumps.AddButton(gd, 15, 140, 4017, 4018, BTN_LUMBER_MODE_AUTO, 1, 0)
    Gumps.AddLabel(gd, 45, 142, 81 if _lumber_mode == LUMBER_MODE_AUTO else 33,
                   "Auto Pilot")

    Gumps.AddButton(gd, 15, 170, 4017, 4018, BTN_LUMBER_MODE_SEMI, 1, 0)
    Gumps.AddLabel(gd, 45, 172, 81 if _lumber_mode == LUMBER_MODE_SEMI else 33,
                   "Semi Manual")

    Gumps.AddButton(gd, 300, 40, 4017, 4018, BTN_LUMBER_RUN, 1, 0)
    Gumps.AddLabel(gd, 330, 42, run_hue, "Start/Stop")

def render_cotton_page(gd):
    mode_lbl = cotton_mode_label()
    run_lbl  = "ON" if _runtime_cotton else "OFF"
    run_hue  = 68 if _runtime_cotton else 33

    Gumps.AddLabel(gd, 15, 40, 68, "Cotton Suite")
    Gumps.AddLabel(gd, 15, 60, 81, "Mode: {0}".format(mode_lbl))
    Gumps.AddLabel(gd, 15, 80, 81, "Run: {0}".format(run_lbl))

    Gumps.AddButton(gd, 15, 110, 4017, 4018, BTN_COTTON_MODE_PICKER, 1, 0)
    Gumps.AddLabel(gd, 45, 112, 81 if _cotton_mode == COTTON_MODE_PICKER else 33,
                   "Picker")

    Gumps.AddButton(gd, 15, 140, 4017, 4018, BTN_COTTON_MODE_AUTOPICK, 1, 0)
    Gumps.AddLabel(gd, 45, 142, 81 if _cotton_mode == COTTON_MODE_AUTOPICK else 33,
                   "Auto Picker")

    Gumps.AddButton(gd, 15, 170, 4017, 4018, BTN_COTTON_MODE_WEAVER, 1, 0)
    Gumps.AddLabel(gd, 45, 172, 81 if _cotton_mode == COTTON_MODE_WEAVER else 33,
                   "Weaver")

    Gumps.AddButton(gd, 300, 40, 4017, 4018, BTN_COTTON_RUN, 1, 0)
    Gumps.AddLabel(gd, 330, 42, run_hue, "Start/Stop")

def render_settings_page(gd):
    Gumps.AddLabel(gd, 15, 40, 68, "-- General Settings --")
    Gumps.AddButton(gd, 15, 60, 4017, 4018, BTN_SET_HOME_RUNE, 1, 0)
    Gumps.AddLabel(gd, 45, 62, 81, "Home Rune: {0}".format(format_serial(_home_rune)))
    Gumps.AddButton(gd, 15, 85, 4017, 4018, BTN_SET_BANK_RUNE, 1, 0)
    Gumps.AddLabel(gd, 45, 87, 81, "Bank Rune: {0}".format(format_serial(_bank_rune)))

    auto_hide_hue = 68 if _auto_hide_enabled else 33
    Gumps.AddButton(gd, 250, 60, 4017, 4018, BTN_TOGGLE_AUTO_HIDE, 1, 0)
    Gumps.AddLabel(gd, 280, 62, auto_hide_hue,
                   "Auto Hide: {0}".format("ON" if _auto_hide_enabled else "OFF"))

    Gumps.AddLabel(gd, 15, 115, 68, "-- Mining Settings --")

    Gumps.AddButton(gd, 15, 135, 4017, 4018, BTN_TOGGLE_MINING_MODE, 1, 0)
    Gumps.AddLabel(gd, 45, 137, 81, "Mode: {0}".format(mining_storage_mode_label()))

    Gumps.AddButton(gd, 15, 160, 4017, 4018, BTN_SET_MINING_FIRE_BEETLE, 1, 0)
    Gumps.AddLabel(gd, 45, 162, 81, "Fire Beetle: {0}".format(format_serial(_mining_firebet)))

    Gumps.AddButton(gd, 15, 185, 4017, 4018, BTN_SET_MINING_GIANT_BEETLE, 1, 0)
    Gumps.AddLabel(gd, 45, 187, 81, "Giant Beetle: {0}".format(format_serial(_mining_giantbeet)))

    Gumps.AddButton(gd, 15, 210, 4017, 4018, BTN_SET_MINING_FORGE, 1, 0)
    Gumps.AddLabel(gd, 45, 212, 81, "Forge: {0}".format(format_serial(_mining_forge)))

    Gumps.AddButton(gd, 15, 235, 4017, 4018, BTN_SET_MINING_SATCHEL, 1, 0)
    Gumps.AddLabel(gd, 45, 237, 81, "Satchel: {0}".format(format_serial(_mining_satchel)))

    Gumps.AddButton(gd, 220, 135, 4017, 4018, BTN_TOGGLE_SMELT_MODE, 1, 0)
    Gumps.AddLabel(gd, 250, 137, 81, "Smelt: {0}".format("Bulk" if _mining_smelt_mode == "bulk" else "Single"))

    Gumps.AddButton(gd, 220, 160, 4017, 4018, BTN_TOGGLE_SMELT_TARGET, 1, 0)
    Gumps.AddLabel(gd, 250, 162, 81, "Target: {0}".format(_mining_smelt_target.capitalize()))

    Gumps.AddLabel(gd, 15, 265, 68, "-- Lumberjack Settings --")
    Gumps.AddButton(gd, 15, 285, 4017, 4018, BTN_SET_LUMBER_PACKY, 1, 0)
    Gumps.AddLabel(gd, 45, 287, 81, "Packy: {0}".format(format_serial(_lumber_packy)))
    Gumps.AddButton(gd, 220, 285, 4017, 4018, BTN_SET_LUMBER_BEETLE, 1, 0)
    Gumps.AddLabel(gd, 250, 287, 81, "Beetle: {0}".format(format_serial(_lumber_beetle)))
    Gumps.AddButton(gd, 220, 310, 4017, 4018, BTN_SET_LUMBER_SATCHEL, 1, 0)
    Gumps.AddLabel(gd, 250, 312, 81, "Satchel: {0}".format(format_serial(_lumber_satchel)))

    Gumps.AddLabel(gd, 15, 340, 68, "-- Cotton Settings --")
    Gumps.AddButton(gd, 15, 360, 4017, 4018, BTN_SET_COTTON_WHEEL, 1, 0)
    Gumps.AddLabel(gd, 45, 362, 81, "Wheel: {0}".format(format_serial(_cotton_wheel)))
    Gumps.AddButton(gd, 220, 360, 4017, 4018, BTN_SET_COTTON_LOOM, 1, 0)
    Gumps.AddLabel(gd, 250, 362, 81, "Loom: {0}".format(format_serial(_cotton_loom)))

    Gumps.AddButton(gd, 220, 390, 4017, 4018, BTN_RESET_SERIALS, 1, 0)
    Gumps.AddLabel(gd, 250, 392, 33, "Reset Serials")

def render_gui():
    page_name = PAGE_NAMES[_current_page]

    Gumps.CloseGump(GUMP_ID)
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)

    width  = 430
    height = 420
    Gumps.AddBackground(gd, 0, 0, width, height, 9270)
    Gumps.AddAlphaRegion(gd, 0, 0, width, height)

    Gumps.AddLabel(gd, 110, 5, 68, "Frog Gatherer Suite v2.2")
    Gumps.AddLabel(gd, 15, 20, 81, "Page: {0}".format(page_name))

    Gumps.AddButton(gd, width - 35, 8, 4017, 4018, BTN_CLOSE, 1, 0)
    Gumps.AddLabel(gd, width - 15, 10, 33, "X")

    if _current_page == PAGE_MINING:
        render_mining_page(gd)
    elif _current_page == PAGE_LUMBER:
        render_lumber_page(gd)
    elif _current_page == PAGE_COTTON:
        render_cotton_page(gd)
    elif _current_page == PAGE_SETTINGS:
        render_settings_page(gd)

    Gumps.AddButton(gd, 15, height - 35, 4014, 4016, BTN_PAGE_PREV, 1, 0)
    Gumps.AddLabel(gd, 35, height - 33, 81, "< Prev")

    Gumps.AddButton(gd, width - 80, height - 35, 4005, 4007, BTN_PAGE_NEXT, 1, 0)
    Gumps.AddLabel(gd, width - 55, height - 33, 81, "Next >")

    Gumps.AddLabel(gd, 110, height - 33, 81,
                   "Status: {0}".format(_status_msg[:40]))

    Gumps.SendGump(GUMP_ID, Player.Serial, GUMP_X, GUMP_Y,
                   gd.gumpDefinition, gd.gumpStrings)

# ===========================================================
# BUTTON HANDLING
# ===========================================================

def handle_button(btn):
    global _running, _current_page
    global _runtime_mining, _runtime_lumber, _runtime_cotton
    global _mining_mode, _lumber_mode, _cotton_mode
    global _status_msg
    global _home_rune, _bank_rune
    global _mining_firebet, _mining_forge, _mining_giantbeet, _mining_satchel
    global _mining_smelt_mode, _mining_smelt_target, _mining_mode_display
    global _lumber_packy, _lumber_beetle, _lumber_satchel
    global _cotton_wheel, _cotton_loom
    global _cached_wheel_serial, _cached_loom_serial
    global _started_autopick, _field_index, _arrived_at_field
    global _lumber_trees, _lumber_tree_idx, _lumber_visited
    global _auto_hide_enabled

    if btn == BTN_CLOSE:
        _running = False
        return

    if btn == BTN_PAGE_PREV:
        _current_page = (_current_page - 1) % len(PAGE_NAMES)
        return

    if btn == BTN_PAGE_NEXT:
        _current_page = (_current_page + 1) % len(PAGE_NAMES)
        return

    if btn == BTN_MINING_RUN:
        _runtime_mining = not _runtime_mining
        _status_msg = "Mining: {0}".format("Running" if _runtime_mining else "Stopped")
        return

    if btn == BTN_MINING_MODE_SELF:
        _mining_mode = MINING_MODE_SELF
        _status_msg = "Mining mode set: Self Pilot"
        return

    if btn == BTN_MINING_MODE_STRIP:
        _mining_mode = MINING_MODE_STRIP
        _status_msg = "Mining mode set: Strip Mine"
        return

    if btn == BTN_MINING_MODE_RECALL:
        _mining_mode = MINING_MODE_RECALL
        _status_msg = "Mining mode set: Recall Mining"
        return

    if btn == BTN_TOGGLE_AUTO_HIDE:
        _auto_hide_enabled = not _auto_hide_enabled
        write_shared(SV_AUTO_HIDE_ENABLED, 1 if _auto_hide_enabled else 0)
        _status_msg = "Auto Hide: {0}".format("Enabled" if _auto_hide_enabled else "Disabled")
        return

    if btn == BTN_TOGGLE_MINING_MODE:
        idx = MINING_MODES.index(_mining_mode_display)
        _mining_mode_display = MINING_MODES[(idx + 1) % len(MINING_MODES)]
        _status_msg = "Mining storage mode set to: {0}".format(mining_storage_mode_label())
        return

    if btn == BTN_SET_MINING_FIRE_BEETLE:
        Target.Cancel()
        Misc.SendMessage("Target your FIRE BEETLE (or ESC).", 55)
        s = Target.PromptTarget("Fire beetle", 0x3B2)
        if s > 0:
            _mining_firebet = s
            write_shared(SV_MINING_FIRE_BEETLE, s)
            _status_msg = "Fire beetle set."
        else:
            _status_msg = "Fire beetle selection cancelled."
        return

    if btn == BTN_SET_MINING_GIANT_BEETLE:
        Target.Cancel()
        Misc.SendMessage("Target your GIANT BEETLE (or ESC).", 55)
        s = Target.PromptTarget("Giant beetle", 0x3B2)
        if s > 0:
            _mining_giantbeet = s
            write_shared(SV_MINING_GIANT_BEETLE, s)
            _status_msg = "Giant beetle set."
        else:
            _status_msg = "Giant beetle selection cancelled."
        return

    if btn == BTN_SET_MINING_FORGE:
        Target.Cancel()
        Misc.SendMessage("Target a FORGE (or ESC).", 55)
        s = Target.PromptTarget("Forge", 0x3B2)
        if s > 0:
            _mining_forge = s
            write_shared(SV_MINING_FORGE, s)
            _status_msg = "Forge set."
        else:
            _status_msg = "Forge selection cancelled."
        return

    if btn == BTN_SET_MINING_SATCHEL:
        Target.Cancel()
        Misc.SendMessage("Target your mining resource SATCHEL (or ESC).", 55)
        s = Target.PromptTarget("Mining satchel", 0x3B2)
        if s > 0:
            _mining_satchel = s
            write_shared(SV_MINING_SATCHEL, s)
            _status_msg = "Mining satchel set."
        else:
            _status_msg = "Mining satchel selection cancelled."
        return

    if btn == BTN_TOGGLE_SMELT_MODE:
        _mining_smelt_mode = "single" if _mining_smelt_mode == "bulk" else "bulk"
        write_shared(SV_MINING_SMELT_MODE, _mining_smelt_mode)
        _status_msg = "Smelt mode set to: {0}".format(
            "Bulk" if _mining_smelt_mode == "bulk" else "Single")
        return

    if btn == BTN_TOGGLE_SMELT_TARGET:
        if _mining_smelt_target == "auto":
            _mining_smelt_target = "forge"
        elif _mining_smelt_target == "forge":
            _mining_smelt_target = "beetle"
        else:
            _mining_smelt_target = "auto"
        write_shared(SV_MINING_SMELT_TARGET, _mining_smelt_target)
        _status_msg = "Smelt target set to: {0}".format(_mining_smelt_target.capitalize())
        return

    if btn == BTN_LUMBER_RUN:
        _runtime_lumber = not _runtime_lumber
        if _runtime_lumber and _lumber_mode == LUMBER_MODE_AUTO:
            _lumber_trees    = []
            _lumber_tree_idx = 0
            _lumber_visited  = []
        _status_msg = "Lumber: {0}".format("Running" if _runtime_lumber else "Stopped")
        return

    if btn == BTN_LUMBER_MODE_SELF:
        _lumber_mode = LUMBER_MODE_SELF
        _status_msg = "Lumber mode set: Self Pilot"
        return

    if btn == BTN_LUMBER_MODE_AUTO:
        _lumber_mode = LUMBER_MODE_AUTO
        _lumber_trees    = []
        _lumber_tree_idx = 0
        _lumber_visited  = []
        _status_msg = "Lumber mode set: Auto Pilot"
        return

    if btn == BTN_LUMBER_MODE_SEMI:
        _lumber_mode = LUMBER_MODE_SEMI
        _status_msg = "Lumber mode set: Semi Manual"
        return

    if btn == BTN_COTTON_RUN:
        _runtime_cotton = not _runtime_cotton
        if _runtime_cotton and _cotton_mode == COTTON_MODE_AUTOPICK:
            _started_autopick = False
            _field_index = 0
            _arrived_at_field = False
        _status_msg = "Cotton: {0}".format("Running" if _runtime_cotton else "Stopped")
        return

    if btn == BTN_COTTON_MODE_PICKER:
        _cotton_mode = COTTON_MODE_PICKER
        _status_msg = "Cotton mode set: Picker"
        return

    if btn == BTN_COTTON_MODE_AUTOPICK:
        _cotton_mode = COTTON_MODE_AUTOPICK
        _started_autopick = False
        _field_index = 0
        _arrived_at_field = False
        _status_msg = "Cotton mode set: Auto Picker"
        return

    if btn == BTN_COTTON_MODE_WEAVER:
        _cotton_mode = COTTON_MODE_WEAVER
        _status_msg = "Cotton mode set: Weaver"
        return

    if btn == BTN_SET_HOME_RUNE:
        Target.Cancel()
        Misc.SendMessage("Target your HOME rune (or ESC to cancel).", 55)
        s = Target.PromptTarget("Home rune", 0x3B2)
        if s > 0 and Items.FindBySerial(s):
            _home_rune = s
            write_shared(SV_HOME_RUNE, s)
            _status_msg = "Home rune set."
        else:
            _status_msg = "Home rune selection cancelled/invalid."
        return

    if btn == BTN_SET_BANK_RUNE:
        Target.Cancel()
        Misc.SendMessage("Target your BANK rune (or ESC to cancel).", 55)
        s = Target.PromptTarget("Bank rune", 0x3B2)
        if s > 0 and Items.FindBySerial(s):
            _bank_rune = s
            write_shared(SV_BANK_RUNE, s)
            _status_msg = "Bank rune set."
        else:
            _status_msg = "Bank rune selection cancelled/invalid."
        return

    if btn == BTN_RESET_SERIALS:
        reset_all_serials()
        _status_msg = "All stored serials reset."
        return

    if btn == BTN_SET_LUMBER_PACKY:
        Target.Cancel()
        Misc.SendMessage("Target your lumber pack horse (or ESC).", 55)
        s = Target.PromptTarget("Lumber packy", 0x3B2)
        if s > 0:
            _lumber_packy = s
            write_shared(SV_LUMBER_PACKY, s)
            _status_msg = "Lumber packy set."
        else:
            _status_msg = "Lumber packy selection cancelled."
        return

    if btn == BTN_SET_LUMBER_BEETLE:
        Target.Cancel()
        Misc.SendMessage("Target your lumber beetle (or ESC).", 55)
        s = Target.PromptTarget("Lumber beetle", 0x3B2)
        if s > 0:
            _lumber_beetle = s
            write_shared(SV_LUMBER_BEETLE, s)
            _status_msg = "Lumber beetle set."
        else:
            _status_msg = "Lumber beetle selection cancelled."
        return

    if btn == BTN_SET_LUMBER_SATCHEL:
        Target.Cancel()
        Misc.SendMessage("Target your lumber resource satchel (or ESC).", 55)
        s = Target.PromptTarget("Lumber satchel", 0x3B2)
        if s > 0:
            _lumber_satchel = s
            write_shared(SV_LUMBER_SATCHEL, s)
            _status_msg = "Lumber satchel set."
        else:
            _status_msg = "Lumber satchel selection cancelled."
        return

    if btn == BTN_SET_COTTON_WHEEL:
        Target.Cancel()
        Misc.SendMessage("Target your SPINNING WHEEL (or ESC).", 55)
        s = Target.PromptTarget("Spinning wheel", 0x3B2)
        if s > 0:
            _cotton_wheel = s
            _cached_wheel_serial = s
            write_shared(SV_COTTON_WHEEL, s)
            _status_msg = "Spinning wheel set."
        else:
            _status_msg = "Wheel selection cancelled."
        return

    if btn == BTN_SET_COTTON_LOOM:
        Target.Cancel()
        Misc.SendMessage("Target your LOOM (or ESC).", 55)
        s = Target.PromptTarget("Loom", 0x3B2)
        if s > 0:
            _cotton_loom = s
            _cached_loom_serial = s
            write_shared(SV_COTTON_LOOM, s)
            _status_msg = "Loom set."
        else:
            _status_msg = "Loom selection cancelled."
        return

# ===========================================================
# MAIN LOOP
# ===========================================================

Misc.SendMessage("Frog Gatherer Suite v2.2 starting...", 68)
Misc.Pause(200)
Gumps.ResetGump()
load_persisted_settings()
render_gui()

while _running and Player.Connected:
    check_special_gumps()
    gd = Gumps.GetGumpData(GUMP_ID)
    current_button = 0
    if gd and gd.buttonid:
        current_button = gd.buttonid

    if current_button and current_button != _last_button:
        Misc.SetSharedValue(SV_CLICK_KEY, current_button)
        _last_button = current_button

    if Misc.CheckSharedValue(SV_CLICK_KEY):
        cached_btn = Misc.ReadSharedValue(SV_CLICK_KEY)
        if cached_btn:
            Gumps.ResetGump()
            handle_button(int(cached_btn))
            Misc.RemoveSharedValue(SV_CLICK_KEY)
            Misc.Pause(150)
            render_gui()
            Misc.Pause(REFRESH_MS)
            continue

    any_running = False

    if _runtime_mining:
        any_running = True
        if _mining_mode == MINING_MODE_SELF:
            mining_step_self_pilot()
        elif _mining_mode == MINING_MODE_STRIP:
            mining_step_auto_pilot()
        elif _mining_mode == MINING_MODE_RECALL:
            mining_step_recall()

    if _runtime_lumber:
        any_running = True
        if _lumber_mode == LUMBER_MODE_SELF:
            lumber_step_self_pilot()
        elif _lumber_mode == LUMBER_MODE_AUTO:
            lumber_step_auto_pilot()
        elif _lumber_mode == LUMBER_MODE_SEMI:
            lumber_step_semi_manual()

    if _runtime_cotton:
        any_running = True
        if _cotton_mode == COTTON_MODE_PICKER:
            cotton_step_picker()
        elif _cotton_mode == COTTON_MODE_AUTOPICK:
            cotton_step_autopick()
        elif _cotton_mode == COTTON_MODE_WEAVER:
            cotton_step_weaver()

    if not any_running and not _status_msg:
        _status_msg = "Idle."

    if _auto_hide_enabled and not Player.IsGhost:
        now = time.time()
        if now - _last_hide_attempt > 10:
            _last_hide_attempt = now
            if Player.Visible:
                _status_msg = "Auto-hiding..."
                Player.UseSkill("Hiding")
                Misc.Pause(100)

    render_gui()
    Misc.Pause(REFRESH_MS)

Gumps.CloseGump(GUMP_ID)
Misc.SendMessage("Frog Gatherer Suite stopped.", 33)
