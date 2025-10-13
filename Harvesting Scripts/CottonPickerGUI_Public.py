# ==================================
# === Cotton Picker (PUBLIC Build) ===
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
GUMP_ID    = 0x51C07A
REFRESH_MS = 200
GUMP_POS   = (650, 650)

_running        = True
_runtime_picker = False
_runtime_weaver = False
_runtime_autopick = False
_status_msg     = "Idle"

# ====================================================================
# BUTTON IDs
# ====================================================================
BTN_QUIT    = 8000
BTN_PICKER  = 8001
BTN_WEAVER  = 8002
BTN_AUTOPICK = 8003

# ====================================================================
# PICKER SECTION 
# ====================================================================
COTTON_PLANT_IDS   = [0x0C51, 0x0C52, 0x0C53, 0x0C54]
COTTON_ITEM_ID     = 0x0DF9
SCAN_RANGE_TILES   = 20
PICK_REACH_TILES   = 1
CLICK_PAUSE_MS     = 140
LOOP_PAUSE_MS      = 200
PLANT_COOLDOWN_SEC = 10
HIGHLIGHT_HUE      = 1152

_last_clicked = {}
_last_count   = -1

def manhattan(ax, ay, bx, by):
    return abs(ax - bx) + abs(ay - by)

def player_xy():
    return Player.Position.X, Player.Position.Y

def find_cotton_plants():
    g_list = List[Int32]()
    for g in COTTON_PLANT_IDS: g_list.Add(g)
    f = Items.Filter(); f.Enabled = True; f.OnGround = True
    f.RangeMax = SCAN_RANGE_TILES; f.Graphics = g_list
    items = list(Items.ApplyFilter(f) or [])
    px, py = player_xy()
    items.sort(key=lambda it: manhattan(px, py, it.Position.X, it.Position.Y))
    return items

def find_ground_cotton():
    g_list = List[Int32]()
    g_list.Add(COTTON_ITEM_ID)
    f = Items.Filter()
    f.Enabled = True
    f.OnGround = True
    f.RangeMax = 2
    f.Graphics = g_list   
    return list(Items.ApplyFilter(f) or [])


def in_reach(it):
    px, py = player_xy()
    return manhattan(px, py, it.Position.X, it.Position.Y) <= PICK_REACH_TILES

def highlight(it):
    try: Items.SetColor(it.Serial, HIGHLIGHT_HUE)
    except: pass

def click_plant(serial):
    try: Misc.DoubleClick(serial); return True
    except:
        try: Items.UseItem(serial); return True
        except: return False

def loot_cotton():
    for bale in find_ground_cotton():
        if bale and bale.Movable:
            Player.HeadMessage(68, "Grabbing cotton bale")
            Items.Move(bale, Player.Backpack.Serial, 0)
            Misc.Pause(600)

def picker_step():
    global _status_msg, _last_count, _last_clicked
    plants = find_cotton_plants()
    now = time.monotonic()

    if len(plants) != _last_count:
        msg = f"Found {len(plants)} cotton plants" if plants else "No cotton nearby"
        Player.HeadMessage(55 if plants else 33, msg)
        _last_count = len(plants)

    for p in plants:
        highlight(p)
        if now - _last_clicked.get(p.Serial, 0.0) < PLANT_COOLDOWN_SEC: continue
        if not in_reach(p): continue  # manual mode: no auto pathing
        _status_msg = "Picking cotton..."
        if click_plant(p.Serial):
            _last_clicked[p.Serial] = now
            Misc.Pause(CLICK_PAUSE_MS)
            loot_cotton()
            return
    _status_msg = "Idle"
    Misc.Pause(LOOP_PAUSE_MS)

# ====================================================================
# WEAVER SECTION 
# ====================================================================
COTTON_TYPE_ID = 0x0DF9
SPOOL_TYPE_ID  = 0x0FA0
TARGET_TIMEOUT_MS   = 2000
SPIN_PAUSE_MS       = 4600
WEAVE_STEP_DELAY_MS = 120
_cached_wheel_serial = None
_cached_loom_serial  = None
JOURNAL_MSG_BOLT_DONE = "You create some cloth"

def get_wheel_serial():
    global _cached_wheel_serial
    if not _cached_wheel_serial:
        Misc.SendMessage("🎡 Target your SPINNING WHEEL.", 55)
        _cached_wheel_serial = Target.PromptTarget("Target wheel")
    return _cached_wheel_serial

def get_loom_serial():
    global _cached_loom_serial
    if not _cached_loom_serial:
        Misc.SendMessage("🧵 Target your LOOM.", 55)
        _cached_loom_serial = Target.PromptTarget("Target loom")
    return _cached_loom_serial

def get_one_cotton(): return Items.FindByID(COTTON_TYPE_ID, -1, Player.Backpack.Serial)
def get_one_spool():  return Items.FindByID(SPOOL_TYPE_ID, -1, Player.Backpack.Serial)
def count_spools():   return Items.BackpackCount(SPOOL_TYPE_ID, -1) or 0

def spin_one_bale():
    wheel = get_wheel_serial(); bale = get_one_cotton()
    if not (wheel and bale): return False
    Items.UseItem(bale.Serial)
    if Target.WaitForTarget(TARGET_TIMEOUT_MS, False): Target.TargetExecute(wheel)
    Misc.Pause(SPIN_PAUSE_MS); return True

def weave_one_spool():
    loom = get_loom_serial(); spool = get_one_spool()
    if not (loom and spool): return False
    Items.UseItem(spool.Serial)
    if Target.WaitForTarget(TARGET_TIMEOUT_MS, False): Target.TargetExecute(loom)
    Misc.Pause(WEAVE_STEP_DELAY_MS); return True

def wait_for_bolt_completion():
    if Journal.Search(JOURNAL_MSG_BOLT_DONE):
        Journal.Clear(); return True
    return False

def weaver_step():
    global _status_msg
    spun = False
    if get_one_cotton(): 
        spun = spin_one_bale()
        _status_msg = "Spun one bale" if spun else "Failed spinning"
    if count_spools() > 0:
        if weave_one_spool():
            if wait_for_bolt_completion():
                _status_msg = "✅ Bolt completed!"
            else:
                _status_msg = "Wove one spool"
    if not spun and count_spools() == 0 and not get_one_cotton():
        _status_msg = "Idle (no cotton/spools)"

# ====================================================================   
# AUTO PICKER (Private Build Only)
# ====================================================================
_autopick_warned = False

def autopick_step():
    global _status_msg, _autopick_warned

    if not _autopick_warned:
        Player.HeadMessage(33, "Auto-Pick not available in public build")
        _autopick_warned = True

    _status_msg = "See Frogmancer for details"
    Misc.Pause(300)  

# ====================================================================
# GUMP SECTION
# ====================================================================
def render_gui():
    gd = Gumps.CreateGump(True)
    Gumps.AddPage(gd, 0)
    Gumps.AddBackground(gd, 0, 0, 280, 180, 9270)
    Gumps.AddAlphaRegion(gd, 0, 0, 280, 180)
    Gumps.AddLabel(gd, 90, 10, 68, "Cotton Suite")
    for (btn, lbl, y, active) in [
        (BTN_PICKER,  "Picker",   40, _runtime_picker),
        (BTN_WEAVER,  "Weaver",   70, _runtime_weaver),
        (BTN_AUTOPICK,"AutoPick", 100,_runtime_autopick),
    ]:
        Gumps.AddButton(gd, 20, y, 4017, 4018, btn, 1, 0)
        hue = 68 if active else 33
        Gumps.AddLabel(gd, 55, y+2, hue, f"{lbl} [{'ON' if active else 'OFF'}]")
    Gumps.AddButton(gd, 230, 10, 4017, 4018, BTN_QUIT, 1, 0)
    Gumps.AddLabel(gd, 260, 12, 33, "Quit")
    mode = "Picker" if _runtime_picker else "Weaver" if _runtime_weaver else "AutoPick" if _runtime_autopick else "None"
    Gumps.AddLabel(gd, 20, 140, 1152, f"Running: {mode}")
    Gumps.AddLabel(gd, 20, 160, 81, f"Status: {_status_msg}")
    Gumps.SendGump(GUMP_ID, Player.Serial, *GUMP_POS, gd.gumpDefinition, gd.gumpStrings)

def handle_button(bid):
    global _runtime_picker, _runtime_weaver, _runtime_autopick, _running, _status_msg, _started_autopick
    if bid == BTN_PICKER:
        _runtime_picker = not _runtime_picker; _runtime_weaver = _runtime_autopick = False
    elif bid == BTN_WEAVER:
        _runtime_weaver = not _runtime_weaver; _runtime_picker = _runtime_autopick = False
    elif bid == BTN_AUTOPICK:
        _runtime_autopick = not _runtime_autopick; _runtime_picker = _runtime_weaver = False; _started_autopick = False
    elif bid == BTN_QUIT: _running = False
    _status_msg = "Idle"

# ====================================================================
# MAIN LOOP
# ====================================================================
Misc.SendMessage("Cotton Suite started", 68)
render_gui()
while _running and Player.Connected:
    gd = Gumps.GetGumpData(GUMP_ID)
    if gd and gd.buttonid: handle_button(gd.buttonid)
    if _runtime_picker: picker_step()
    elif _runtime_weaver: weaver_step()
    elif _runtime_autopick: autopick_step()
    else: _status_msg = "Idle"
    render_gui(); Misc.Pause(REFRESH_MS)
Gumps.CloseGump(GUMP_ID)
Misc.SendMessage("Cotton Suite stopped", 33)
