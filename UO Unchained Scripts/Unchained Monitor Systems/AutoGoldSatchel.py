# ==================================
# === Auto Loot Gold > Satchel   ===
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

import Gumps, Player, Items, Target, Misc, Mobiles, time
from System import Int32
from System.Collections.Generic import List

# ===========================================================
# CONFIG
# ===========================================================
GUMP_ID    = 0xAA55EE11
REFRESH_MS = 400
LOOT_RANGE = 2
GUMP_X, GUMP_Y = 700, 600

GOLD_ID    = 0x0EED
SATCHEL_ID = 0x5575

# ===========================================================
# GLOBAL STATE
# ===========================================================
_running        = True
_auto_loot      = False
_status_msg     = "Idle"
_start_time = time.time()
_start_gold = Player.Gold if hasattr(Player, "Gold") else 0
_last_gold = _start_gold
_gold_per_hour = 0


_satchel_serial = Misc.ReadSharedValue('goldSatchelSerial') if Misc.CheckSharedValue('goldSatchelSerial') else 0

# ===========================================================
# BUTTON IDS
# ===========================================================
BTN_SET_SATCHEL = 5001
BTN_TOGGLE_LOOT = 5002
BTN_CLOSE       = 5003

# ===========================================================
# HELPERS
# ===========================================================
def get_gold_count():
    try:
        return Player.Gold or 0
    except:
        return 0


def set_satchel():
    global _satchel_serial, _status_msg

    Target.Cancel()
    Misc.SendMessage("Target your worn gold satchel or press ESC to cancel.", 55)
    serial = Target.PromptTarget("Select your gold satchel.", 0x3B2)

    if serial <= 0:
        Player.HeadMessage(33, "Satchel selection cancelled.")
        _status_msg = "Cancelled."
        return

    satchel = Items.FindBySerial(serial)
    if not satchel:
        Player.HeadMessage(55, "Custom equipped satchel targeted (Unchained).")
        _satchel_serial = serial
        Misc.SetSharedValue('goldSatchelSerial', _satchel_serial)
        _status_msg = "Custom satchel stored."
        return

    if _satchel_serial == serial:
        Player.HeadMessage(53, "Same satchel selected — keeping current setting.")
        _status_msg = "No change."
        return

    _satchel_serial = serial
    Misc.SetSharedValue('goldSatchelSerial', _satchel_serial)
    Player.HeadMessage(68, "Satchel set! (0x{0:X})".format(_satchel_serial))
    _status_msg = "Satchel updated."


def toggle_autoloot():
    global _auto_loot, _status_msg
    _auto_loot = not _auto_loot
    if _auto_loot:
        _status_msg = "AutoLoot Active"
        Misc.SendMessage("AutoLoot: ON", 68)
    else:
        _status_msg = "AutoLoot Disabled"
        Misc.SendMessage("AutoLoot: OFF", 33)


def loot_gold_from_ground():
    golds = Items.Filter()
    golds.Enabled = True
    golds.OnGround = True
    golds.Movable = True
    golds.RangeMax = LOOT_RANGE

    golds.Graphics = List[Int32]([GOLD_ID])

    gold_list = Items.ApplyFilter(golds)

    for g in gold_list:
        if not _running or not _auto_loot:
            return
        try:
            Items.Move(g.Serial, _satchel_serial, -1)
            Misc.Pause(600)
        except:
            Items.Move(g.Serial, Player.Backpack.Serial, -1)
            Misc.Pause(600)

def loot_gold_from_corpses():
    corpses = Items.Filter()
    corpses.Enabled = True
    corpses.OnGround = True
    corpses.IsCorpse = True
    corpses.RangeMax = LOOT_RANGE
    corpse_list = Items.ApplyFilter(corpses)

    for corpse in corpse_list:
        if not _running or not _auto_loot:
            return

        if not corpse.Contains:
            continue

        for item in corpse.Contains:
            if item.ItemID == GOLD_ID:
                try:
                    Items.Move(item.Serial, _satchel_serial, -1)
                    Misc.Pause(300)
                except:
                    Items.Move(item.Serial, Player.Backpack.Serial, -1)
                    Misc.Pause(300)

        Misc.Pause(150)
        
def autoloot_tick():
    if not _auto_loot or not _satchel_serial:
        return
    loot_gold_from_corpses()
    loot_gold_from_ground()

def update_gold_rate():
    global _last_gold, _gold_per_hour

    try:
        current_gold = Player.Gold or 0
    except:
        current_gold = _last_gold

    elapsed_sec = time.time() - _start_time
    if elapsed_sec < 60:  
        _gold_per_hour = 0
    else:
        diff = current_gold - _start_gold
        hours = elapsed_sec / 3600.0
        _gold_per_hour = int(diff / hours) if hours > 0 else 0

    _last_gold = current_gold
    

# ===========================================================
# GUI
# ===========================================================
def render_gui():
    total_gold = get_gold_count()
    satchel_label = "0x{0:X}".format(_satchel_serial) if _satchel_serial else "Not Set"
    loot_state = "ON" if _auto_loot else "OFF"

    Gumps.CloseGump(GUMP_ID)
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)

    Gumps.AddBackground(gd, 0, 0, 250, 150, 5054)
    Gumps.AddAlphaRegion(gd, 0, 0, 250, 150)
    Gumps.AddLabel(gd, 70, 5, 68, "Gold Satchel Tracker")

    Gumps.AddLabel(gd, 20, 35, 0x47E, f"Total Gold: {get_gold_count():,}")
    Gumps.AddLabel(gd, 130, 35, 0x47E, f"({int(_gold_per_hour):,}/hr)")
    Gumps.AddLabel(gd, 20, 55, 0x480, f"Satchel: {satchel_label}")
    Gumps.AddLabel(gd, 20, 75, 0x44E, f"Status: {_status_msg}")

    Gumps.AddButton(gd, 25, 100, 4011, 4012, BTN_SET_SATCHEL, 1, 0)
    Gumps.AddLabel(gd, 55, 100, 68, "Set Satchel")

    Gumps.AddButton(gd, 25, 120, 4005, 4007, BTN_TOGGLE_LOOT, 1, 0)
    Gumps.AddLabel(gd, 55, 120, 68, f"AutoLoot: {loot_state}")

    Gumps.AddButton(gd, 160, 120, 4017, 4018, BTN_CLOSE, 1, 0)
    Gumps.AddLabel(gd, 190, 120, 33, "Close")

    Gumps.SendGump(GUMP_ID, Player.Serial, GUMP_X, GUMP_Y, gd.gumpDefinition, gd.gumpStrings)


# ===========================================================
# MAIN LOOP
# ===========================================================
Misc.SendMessage("Starting Auto Gold Satchel...", 68)
Misc.Pause(200)
Gumps.ResetGump()

while _running and Player.Connected:
    gd = Gumps.GetGumpData(GUMP_ID)
    btn = gd.buttonid if gd else 0

    if btn:
        Gumps.ResetGump()
        if btn == BTN_SET_SATCHEL:
            set_satchel()
        elif btn == BTN_TOGGLE_LOOT:
            toggle_autoloot()
        elif btn == BTN_CLOSE:
            _running = False
            break

    autoloot_tick()

    update_gold_rate()
    render_gui()
    Misc.Pause(REFRESH_MS)

Gumps.CloseGump(GUMP_ID)
Misc.SendMessage("Gold Satchel stopped.", 33)
