# ==================================
# === Cotton Picker (Private) ===
# ==================================
# Author: Frogmancer Schteve
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

import time, Misc, Gumps, Player, Items, Target, Journal
from System import Int32
from System.Collections.Generic import List
import PathFinding

# ====================================================================
# GLOBAL CONFIGS
# ====================================================================
GUMP_ID    = 0x51C07B
REFRESH_MS = 200
GUMP_POS   = (650, 650)

_running          = True
_runtime_picker   = False   # Manual picker: no pathing, only picks in-reach
_runtime_weaver   = False   # Concurrent spinner/weaver
_runtime_autopick = False   # Private: multi-field auto picker
_status_msg       = "Idle"

# ====================================================================
# BUTTON IDs
# ====================================================================
BTN_QUIT     = 8000
BTN_PICKER   = 8001
BTN_WEAVER   = 8002
BTN_AUTOPICK = 8003

# ====================================================================
# PICKER CONFIGS (Manual)
# ====================================================================
COTTON_PLANT_IDS   = [0x0C51, 0x0C52, 0x0C53, 0x0C54]
COTTON_ITEM_ID     = 0x0DF9
SCAN_RANGE_TILES   = 20
PICK_REACH_TILES   = 1
CLICK_PAUSE_MS     = 180
LOOP_PAUSE_MS      = 200
PLANT_COOLDOWN_SEC = 10
HIGHLIGHT_HUE      = 1152

FIELDS = [
    (1198, 1822),  # Field 1
    (1222, 1723),  # Field 2
    (1190, 1683),  # Field 3
    (1118, 1623),  # Field 4
    (1151, 1574)   # Field 5
]
SAFE_SPOT = (1410, 1733)

# Route from Safe → Field 1 (via bridge etc.)
INITIAL_ROUTE_TO_FIELD1 = [
    (1386,1748),(1352,1752),(1318,1752),
    (1285,1746),(1249,1771),(1222,1807),
    (1198,1822)  # center of Field 1
]

# Hop between fields, then back to Safe Spot
FIELD_ROUTES = {
    1: [(1222,1723)],      # Field 1 → Field 2
    2: [(1190,1683)],      # Field 2 → Field 3
    3: [(1118,1623)],      # Field 3 → Field 4
    4: [(1151,1574)],      # Field 4 → Field 5
    5: [                   # Field 5 → Safe Spot
        (1179,1596),(1188,1636),(1224,1663),
        (1255,1678),(1283,1707),(1309,1742),
        (1336,1751),(1383,1751),(1406,1742),
        (1410,1733)
    ]
}

# Smooth bank up/down from Safe Spot
BANK_ROUTE_UP = [
    (1410,1733),
    (1418,1721),
    (1418,1701),
    (1427,1699),
    (1422,1693)   # at stairs/bank
]
BANK_ROUTE_DOWN = [
    (1432,1693),
    (1427,1699),
    (1418,1701),
    (1418,1721),
    (1404,1735),
    (1410,1733)   # back to Safe Spot
]

FIELD_LABEL = {
    0: "Field 1",
    1: "Field 2",
    2: "Field 3",
    3: "Field 4",
    4: "Field 5"
}
_field_index        = 0
_started_autopick   = False
IDLE_BANK_SEC       = 600
_next_bank_release  = 0
_last_clicked       = {}
_last_count         = -1
_arrived_at_field   = False

# ====================================================================
# SHARED HELPERS
# ====================================================================
def manhattan(ax, ay, bx, by):
    return abs(ax - bx) + abs(ay - by)

def player_xy():
    return Player.Position.X, Player.Position.Y

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
    g_list = List[Int32](); g_list.Add(COTTON_ITEM_ID)
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
        Misc.DoubleClick(serial); return True
    except:
        try:
            Items.UseItem(serial); return True
        except:
            return False

def loot_cotton():
    bales = find_ground_cotton()
    for bale in bales:
        if bale and bale.Movable:
            Player.HeadMessage(68, "Grabbing cotton bale")
            Items.Move(bale, Player.Backpack.Serial, 0)
            Misc.Pause(600)

# ====================================================================
# PICKER (MANUAL, NO PATH)
# ====================================================================
def picker_step():
    global _status_msg, _last_count, _last_clicked
    plants = find_cotton_plants()
    now    = time.monotonic()

    if len(plants) != _last_count:
        if plants:
            Player.HeadMessage(55, f"Found {len(plants)} cotton plants nearby")
        else:
            Player.HeadMessage(33, "No cotton detected nearby")
        _last_count = len(plants)

    for p in plants:
        highlight(p)
        if now - _last_clicked.get(p.Serial, 0.0) < PLANT_COOLDOWN_SEC:
            continue

        # Manual mode: only pick if already in reach
        if not in_reach(p):
            continue

        _status_msg = "Picking cotton..."
        Player.HeadMessage(68, "Picking cotton")
        if click_plant(p.Serial):
            _last_clicked[p.Serial] = now
            Misc.Pause(CLICK_PAUSE_MS)
            loot_cotton()
            return  # one plant per tick

    _status_msg = "Idle"
    Misc.Pause(LOOP_PAUSE_MS)

# ====================================================================
# WEAVER (CONCURRENT SPIN + SAFE WEAVE)
# ====================================================================
SPINNING_WHEEL_GRAPHICS = [0x1015, 0x1019, 0x101A, 0x101B]  # not used in private build auto-find
LOOM_GRAPHICS           = [0x105F, 0x1060, 0x1061, 0x1062]  # not used in private build auto-find

COTTON_TYPE_ID = 0x0DF9
SPOOL_TYPE_ID  = 0x0FA0

TARGET_TIMEOUT_MS   = 2000
SPIN_PAUSE_MS       = 4600   # wheel cooldown is bottleneck
WEAVE_STEP_DELAY_MS = 120    # fast & stable
JOURNAL_MSG_BOLT    = "You create some cloth"

_cached_wheel_serial = None
_cached_loom_serial  = None
_next_spin_ready     = 0.0   # monotonic timestamp

def get_one_cotton():
    return Items.FindByID(COTTON_TYPE_ID, -1, Player.Backpack.Serial)

def get_one_spool():
    return Items.FindByID(SPOOL_TYPE_ID, -1, Player.Backpack.Serial)

def count_spools():
    return Items.BackpackCount(SPOOL_TYPE_ID, -1) or 0

def get_wheel_serial():
    global _cached_wheel_serial
    if _cached_wheel_serial:
        return _cached_wheel_serial
    Misc.SendMessage("🎡 Target your SPINNING WHEEL.", 55)
    s = Target.PromptTarget("Target your SPINNING WHEEL.")
    if s:
        _cached_wheel_serial = s
        Misc.SendMessage("✅ Wheel cached", 68)
    return _cached_wheel_serial

def get_loom_serial():
    global _cached_loom_serial
    if _cached_loom_serial:
        return _cached_loom_serial
    Misc.SendMessage("🧵 Target your LOOM.", 55)
    s = Target.PromptTarget("Target your LOOM.")
    if s:
        _cached_loom_serial = s
        Misc.SendMessage("✅ Loom cached", 68)
    return _cached_loom_serial

def spin_one_bale_if_ready():
    """Spin one bale if wheel cooldown passed."""
    global _next_spin_ready
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
    return True

def journal_saw_bolt(timeout_ms=1000):
    """Peek journal briefly to detect bolt completion."""
    start = time.time()
    while time.time() - start < (timeout_ms/1000.0):
        if Journal.Search(JOURNAL_MSG_BOLT):
            Journal.Clear()
            return True
        Misc.Pause(20)
    return False

def weave_one_spool_safely():
    """Feed one spool → stop early if a bolt completes."""
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
    # Stop if bolt just finished (avoid wasting partials)
    if journal_saw_bolt(600):
        Misc.SendMessage("✅ Bolt completed!", 68)
        return "bolt"
    return True

def weaver_step():
    """Try to spin (if ready), and weave in the same tick."""
    global _status_msg

    spun = False
    if get_one_cotton():
        if spin_one_bale_if_ready():
            spun = True
            _status_msg = "Spinning cotton..."

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

# ====================================================================
# AUTO PICKER (PRIVATE)
# ====================================================================
def go_via_waypoints(waypoints):
    for (x, y) in waypoints:
        route = PathFinding.Route()
        route.X = x
        route.Y = y
        route.MaxRetry    = 3
        route.StopIfStuck = False
        _status_msg = f"Moving to {x},{y}"
        Misc.SendMessage(f"🚶 Moving to {x},{y}", 55)
        if not PathFinding.Go(route):
            _status_msg = f"Path failed at {x},{y}"
            Misc.SendMessage(f"❌ Path failed at {x},{y}", 33)
            return False
        Misc.Pause(300)
    return True

def go_to_field(index):
    if index not in FIELD_ROUTES:
        Misc.SendMessage(f"No route defined for field {index}", 33)
        return False
    if go_via_waypoints(FIELD_ROUTES[index]):
        Misc.SendMessage(f"Arrived at {FIELD_LABEL.get(index,'Field?')}", 68)
        return True
    return False

def go_to_bank():
    return go_via_waypoints(BANK_ROUTE_UP)

def leave_bank_to_safe():
    return go_via_waypoints(BANK_ROUTE_DOWN)

def autopick_step():
    """Automated multi-field picker w/ idle-at-bank loop."""
    global _status_msg, _field_index, _last_clicked, _started_autopick
    global _next_bank_release, _arrived_at_field

    now = time.monotonic()

    # If we're idling at bank, count down and leave when done
    if _status_msg.startswith("Idle at Bank"):
        remaining = int(_next_bank_release - now)
        if remaining > 0:
            mins, secs = divmod(remaining, 60)
            _status_msg = f"Idle at Bank ({mins:02}:{secs:02} left)"
            Misc.Pause(400)
            return
        Misc.SendMessage("⏰ Bank idle finished, leaving bank", 68)
        leave_bank_to_safe()
        Misc.SendMessage("➡ Now heading to Field 1", 68)
        _field_index = 0
        go_via_waypoints(INITIAL_ROUTE_TO_FIELD1)
        _arrived_at_field = True
        _status_msg = "Walking to Field 1"
        return

    # First activation → walk to Field 1
    if not _started_autopick:
        go_via_waypoints(INITIAL_ROUTE_TO_FIELD1)
        _field_index       = 0
        _arrived_at_field  = True
        _started_autopick  = True
        _status_msg        = "Walking to Field 1"
        return

    # Field work
    plants = find_cotton_plants()
    if plants:
        _status_msg = f"Auto-Picking Field {_field_index+1}"
        for p in plants:
            highlight(p)
            if now - _last_clicked.get(p.Serial, 0.0) < PLANT_COOLDOWN_SEC:
                continue
            if not in_reach(p):
                # In auto mode we’ll walk adjacent to plant
                # (short 4-way fan-in attempt)
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
                _last_clicked[p.Serial] = now
                Misc.Pause(CLICK_PAUSE_MS)
                loot_cotton()
                return  # one plant per tick
    else:
        # Confirm empty once before advancing
        if _arrived_at_field:
            Misc.SendMessage(f"No cotton at Field {_field_index+1}", 33)
            _arrived_at_field = False
            Misc.Pause(200)
            return

        # Advance route or finish the loop
        if _field_index < len(FIELD_ROUTES) - 1:
            _field_index += 1
            go_to_field(_field_index)
            _arrived_at_field = True
            _status_msg = f"Walking to Field {_field_index+1}"
        else:
            Misc.SendMessage("🌙 All fields empty → idling at Bank", 33)
            go_to_bank()
            _next_bank_release = now + IDLE_BANK_SEC
            mins, secs = divmod(IDLE_BANK_SEC, 60)
            _status_msg = f"Idle at Bank ({mins:02}:{secs:02} left)"
            _field_index = 0

# ====================================================================
# GUMP UI
# ====================================================================
def render_gui():
    # Always re-send the gump so it stays interactive
    Gumps.CloseGump(GUMP_ID)
    gd = Gumps.CreateGump(True)
    Gumps.AddPage(gd, 0)
    Gumps.AddBackground(gd, 0, 0, 300, 185, 9270)
    Gumps.AddAlphaRegion(gd, 0, 0, 300, 185)

    Gumps.AddLabel(gd, 95, 8, 68, "Cotton Suite (Private)")

    # Picker
    lbl = "ON" if _runtime_picker else "OFF"
    hue = 68 if _runtime_picker else 33
    Gumps.AddButton(gd, 16, 36, 4017, 4018, BTN_PICKER, 1, 0)
    Gumps.AddLabel(gd, 48, 38, hue, f"Picker [{lbl}]")

    # Weaver
    lbl = "ON" if _runtime_weaver else "OFF"
    hue = 68 if _runtime_weaver else 33
    Gumps.AddButton(gd, 16, 66, 4017, 4018, BTN_WEAVER, 1, 0)
    Gumps.AddLabel(gd, 48, 68, hue, f"Weaver [{lbl}]")

    # Auto-Pick
    lbl = "ON" if _runtime_autopick else "OFF"
    hue = 68 if _runtime_autopick else 33
    Gumps.AddButton(gd, 16, 96, 4017, 4018, BTN_AUTOPICK, 1, 0)
    Gumps.AddLabel(gd, 48, 98, hue, f"Auto-Pick [{lbl}]")

    # Quit
    Gumps.AddButton(gd, 250, 8, 4017, 4018, BTN_QUIT, 1, 0)
    Gumps.AddLabel(gd, 272, 10, 33, "X")

    active = "Picker" if _runtime_picker else "Weaver" if _runtime_weaver else "Auto-Pick" if _runtime_autopick else "None"
    Gumps.AddLabel(gd, 16, 132, 1152, f"Running: {active}")
    Gumps.AddLabel(gd, 16, 150, 81,   f"Status: {_status_msg}")

    Gumps.SendGump(GUMP_ID, Player.Serial, *GUMP_POS, gd.gumpDefinition, gd.gumpStrings)

def handle_button(bid):
    global _runtime_picker, _runtime_weaver, _runtime_autopick, _running, _status_msg, _started_autopick
    if bid == BTN_PICKER:
        _runtime_picker   = not _runtime_picker
        if _runtime_picker:
            _runtime_weaver = _runtime_autopick = False
        _status_msg = "Idle"
    elif bid == BTN_WEAVER:
        _runtime_weaver   = not _runtime_weaver
        if _runtime_weaver:
            _runtime_picker = _runtime_autopick = False
        _status_msg = "Idle"
    elif bid == BTN_AUTOPICK:
        _runtime_autopick = not _runtime_autopick
        if _runtime_autopick:
            _runtime_picker = _runtime_weaver = False
            _started_autopick = False  # force fresh route to Field 1
        _status_msg = "Idle"
    elif bid == BTN_QUIT:
        _running = False

# ====================================================================
# MAIN LOOP
# ====================================================================
Misc.SendMessage("Cotton Suite (Private) started", 68)
render_gui()

while _running and Player.Connected:
    gd = Gumps.GetGumpData(GUMP_ID)
    if gd and gd.buttonid:
        handle_button(gd.buttonid)

    if _runtime_picker:
        picker_step()
    elif _runtime_weaver:
        weaver_step()
    elif _runtime_autopick:
        autopick_step()
    else:
        _status_msg = "Idle"

    render_gui()
    Misc.Pause(REFRESH_MS)

Gumps.CloseGump(GUMP_ID)
Misc.SendMessage("Cotton Suite stopped", 33)
