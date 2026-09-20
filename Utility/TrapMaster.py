# ============================================================
# == Frogge Trap Placer                                    ==
# ============================================================
# Copyright (c) Frogmancer Schteve. All rights reserved except as
# expressly permitted by the repository License.md.
#
# PERSONAL USE
# This script is provided for personal, non-commercial use.
# You may use, study, and modify it for your own use. Redistribution,
# resale, sublicensing, or incorporation into another distributed
# project is not permitted without prior permission.
#
# AI / LLM RESTRICTION
# Do NOT upload, submit, ingest, or otherwise provide this script,
# in whole or substantial part, to Large Language Models (LLMs),
# generative AI systems, AI coding assistants, machine-learning
# datasets, training/fine-tuning pipelines, retrieval systems, or
# automated code-generation systems.
#
# If you encounter a bug or compatibility issue, please submit an
# issue through the repository or contact Frogmancer Schteve directly
# rather than submitting the script to an AI service for troubleshooting.
#
# SHARD RULES
# You are responsible for ensuring your use of this script complies
# with the rules of the Ultima Online shard on which you play.
#
# This notice is only a summary. The repository License.md contains
# the complete terms governing use of this software.
#
# Use it. Learn from it. Improve it.
# Just don't feed the frogs to the robots.
# ====================================================================

import time
import math
import Misc, Player, Items, Gumps, Journal

# ============================================================
# === TOOL IDENTITY ==========================================
# ============================================================

TITLE   = "Trap Placer"
VERSION = "v0.2"

GUMP_ID = 0xF206544D
GUMP_X  = 600
GUMP_Y  = 300

REFRESH_MS = 200

# ============================================================
# === ITEM DEFINITIONS =======================================
# ============================================================

TRAP_ITEM_ID = 0xC067
DETONATOR_ID = 0x7307

TORSO_ITEM_ID = 0x1D9F
TORSO_LOOT_RANGE = 2

BTN_LOOT_TORSO = 9001


TRAPS = [
    ("Poison",    0x0AD5),
    ("Mortal",    0x0B54),
    ("Bear",      0x0B49),
    ("Explosive", 0x0AD3),
    ("Gruesome",  0x0864),
]

# ============================================================
# === UI CONSTANTS ===========================================
# ============================================================

WIDTH  = 250
HEIGHT = 300
BG_ID  = 5054

TEXT_COLOR = 1152
GOOD_COLOR = 68
WARN_COLOR = 33
MUTED_LINE = 0x777

BTN_USE_BASE = 1000
BTN_DETONATE = 2131

CENTER_X = 125
CENTER_Y = 120
RADIUS   = 75

RADIAL_Y_OFFSET = 50

LABEL_Y_OFFSET  = -18
ITEM_Y_OFFSET   = 0
COUNT_X_OFFSET  = 28
COUNT_Y_OFFSET  = 6
BUTTON_Y_OFFSET = 24

ICON_HALF = 10

BRAND_ICON = 0x2130               # Decorative frog item art ID
BRAND_HUE = 0x09E8

GEM_ART_UP   = 10741
GEM_ART_DOWN = 10740


# ============================================================
# === RUNTIME STATE ==========================================
# ============================================================

_running        = True
_dirty_ui       = True
_status_msg     = "No Trap"
_trap_state     = "NONE"   # NONE | PLACED
_cooldown_until = 0

_last_button_time = 0
_last_cd_display  = -1

# ============================================================
# === HELPERS ================================================
# ============================================================

def now():
    return time.time()

def cooldown_remaining():
    return max(0, int(_cooldown_until - now()))

def count_traps(hue):
    return Items.ContainerCount(
        Player.Backpack.Serial,
        TRAP_ITEM_ID,
        hue,
        True
    )

def use_trap(hue):
    global _status_msg
    itm = Items.FindByID(
        TRAP_ITEM_ID,
        hue,
        Player.Backpack.Serial,
        True
    )
    if not itm:
        _status_msg = "Trap not found"
        return
    Items.UseItem(itm.Serial)
    _status_msg = "Placing trap..."

def use_detonator():
    global _status_msg
    det = Items.FindByID(DETONATOR_ID, -1, Player.Backpack.Serial)
    if not det:
        _status_msg = "No detonator!"
        return
    Items.UseItem(det.Serial)
    _status_msg = "Detonating..."
    
def loot_torso_from_ground():
    items = Items.Filter()
    items.Enabled = True
    items.OnGround = True
    items.Movable = True
    items.RangeMax = TORSO_LOOT_RANGE
    items.Graphics = [TORSO_ITEM_ID]

    found = Items.ApplyFilter(items) or []

    if not found:
        Misc.SendMessage("No torso found nearby.", 33)
        return

    for itm in found:
        try:
            Items.Move(itm.Serial, Player.Backpack.Serial, -1)
            Misc.Pause(250)
            Misc.SendMessage("Torso looted.", 68)
            return
        except:
            continue
    

# ============================================================
# === JOURNAL PARSING ========================================
# ============================================================

def process_journal():
    global _trap_state, _status_msg, _cooldown_until, _dirty_ui

    if Journal.Search("You begin carefully placing"):
        _status_msg = "Placing trap..."
        _dirty_ui = True
        Journal.Clear()

    if Journal.Search("you hide the trap to the best of your ability"):
        _trap_state = "PLACED"
        _status_msg = "Trap placed"
        _dirty_ui = True
        Journal.Clear()

    if Journal.Search("There is already a trap in this area"):
        _status_msg = "Area already trapped"
        _dirty_ui = True
        Journal.Clear()

    if Journal.Search("You already have a trap placed"):
        _trap_state = "PLACED"
        _status_msg = "Trap already placed"
        _dirty_ui = True
        Journal.Clear()

    if Journal.Search("You detonate your trap"):
        _trap_state = "NONE"
        _status_msg = "Trap detonated"
        _dirty_ui = True
        Journal.Clear()

    if Journal.Search("You must wait"):
        _cooldown_until = now() + 12
        _status_msg = "Trap cooldown"
        _dirty_ui = True
        Journal.Clear()


# ============================================================
# === GUI ====================================================
# ============================================================

def build_gui():
    global _dirty_ui
    _dirty_ui = False

    gd = Gumps.CreateGump(True)
    Gumps.AddPage(gd, 0)

    Gumps.AddBackground(gd, 0, 0, WIDTH, HEIGHT, BG_ID)
    Gumps.AddAlphaRegion(gd, 0, 0, WIDTH, HEIGHT)
    
    Gumps.AddItem(gd, 5, 5, BRAND_ICON, BRAND_HUE)

    # Header
    Gumps.AddLabel(gd, 90, 10, TEXT_COLOR, TITLE)
    Gumps.AddLabel(
        gd,
        20,
        35,
        GOOD_COLOR if _trap_state == "PLACED" else TEXT_COLOR,
        f"Status: {_status_msg}"
    )

    # Separator
    Gumps.AddLabel(gd, 25, 60, MUTED_LINE, "-" * 32)

    # Cooldown
    if cooldown_remaining() > 0:
        Gumps.AddLabel(
            gd,
            20,
            75,
            WARN_COLOR,
            f"Cooldown: {cooldown_remaining()}s"
        )

    # =========================
    # Center Detonator
    # =========================
    Gumps.AddButton(
        gd,
        CENTER_X - 18,
        CENTER_Y + RADIAL_Y_OFFSET - 18,
        2642,
        2643,
        BTN_DETONATE,
        1,
        0
    )

    # =========================
    # Radial Trap Nodes
    # =========================
    angle_step = 360.0 / len(TRAPS)

    for i, (name, hue) in enumerate(TRAPS):
        angle = angle_step * i - 90
        rad   = angle * math.pi / 180.0

        cx = int(CENTER_X + RADIUS * math.cos(rad))
        cy = int(CENTER_Y + RADIAL_Y_OFFSET + RADIUS * math.sin(rad))

        btn_id = BTN_USE_BASE + i
        count  = count_traps(hue)
        label_hue = TEXT_COLOR if count > 0 else WARN_COLOR

        # Label
        Gumps.AddLabel(
            gd,
            cx - 14,
            cy + LABEL_Y_OFFSET,
            label_hue,
            name
        )

        # Item
        Gumps.AddItem(
            gd,
            cx - ICON_HALF,
            cy + ITEM_Y_OFFSET,
            TRAP_ITEM_ID,
            hue
        )

        # Count
        Gumps.AddLabel(
            gd,
            cx + COUNT_X_OFFSET,
            cy + COUNT_Y_OFFSET,
            TEXT_COLOR,
            str(count)
        )

        # Button
        Gumps.AddButton(
            gd,
            cx - ICON_HALF,
            cy + BUTTON_Y_OFFSET,
            10830,
            10850,
            btn_id,
            1,
            0
        )

    Gumps.AddLabel(
        gd,
        30,
        HEIGHT - 32,
        TEXT_COLOR,
        "Torso"
    )

        
        
    # Correct movable SendGump path
    Gumps.SendGump(
        GUMP_ID,
        Player.Serial,
        GUMP_X,
        GUMP_Y,
        gd.gumpDefinition,
        gd.gumpStrings
    )

# ============================================================
# === BUTTON HANDLING ========================================
# ============================================================

def handle_button(bid):
    global _cooldown_until, _trap_state, _last_button_time, _dirty_ui

    if now() - _last_button_time < 0.2:
        return
    _last_button_time = now()

    if bid == BTN_DETONATE:
        if _trap_state == "PLACED":
            use_detonator()
            _dirty_ui = True
        return

    if bid >= BTN_USE_BASE:
        if cooldown_remaining() > 0:
            return

        idx = bid - BTN_USE_BASE
        if idx < 0 or idx >= len(TRAPS):
            return

        hue = TRAPS[idx][1]
        use_trap(hue)
        _trap_state = "PLACED"
        _cooldown_until = now() + 12
        _dirty_ui = True

    if bid == BTN_LOOT_TORSO:
        loot_torso_from_ground()
        return
   
        
# ============================================================
# === MAIN LOOP ==============================================
# ============================================================

Journal.Clear()
Gumps.CloseGump(GUMP_ID)

while _running and Player.Connected:
    gd = Gumps.GetGumpData(GUMP_ID)
    if gd and gd.buttonid:
        handle_button(gd.buttonid)

    process_journal()

    cd = cooldown_remaining()
    if cd != _last_cd_display:
        _last_cd_display = cd
        _dirty_ui = True

    if _dirty_ui:
        build_gui()

    Misc.Pause(REFRESH_MS)

Gumps.CloseGump(GUMP_ID)
