# ==================================
# ==  Stealther Detector          ==
# ==================================
# Copyright (c) Frogmancer Schteve. All rights reserved except as
# expressly permitted by the repository LICENSE.md.
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
# This notice is only a summary. The repository LICENSE.md contains
# the complete terms governing use of this software.
#
# Use it. Learn from it. Improve it.
# Just don't feed the frogs to the robots.
# ====================================================================

from System import Int32
from System.Collections.Generic import List
import Gumps, Player, Misc, time, Items

# ==================================================
# CONFIG
# ==================================================
GUMP_ID     = 0xF2065344
REFRESH_MS = 400
SCAN_RANGE = 12 # 24 is the max rendering distance

ALERT_HUE = 33
OK_HUE    = 68

FOOTSTEP_ITEM_IDS = [
    0x1E03,
    0x1E04,
    0x1E05,
    0x1E06,
]

HIGHLIGHT_HUES = [1152, 1161, 1693, 2773, 2947, 2977] #Add HUEs here
ARROW_LIFETIME = 1.5

# ==================================================
# STATE
# ==================================================
_alert_state = False
_last_alert  = 0

_colored      = {}
_seen_steps   = {}
_arrow_serial = None
_arrow_until  = 0

_last_gump_state = None
_footstep_filter = None

# ==================================================
# HELPERS
# ==================================================
def find_footsteps():
    global _footstep_filter

    if not _footstep_filter:
        flt = Items.Filter()
        flt.Enabled  = True
        flt.OnGround = True
        flt.RangeMax = SCAN_RANGE

        gfx = List[Int32]()
        for fid in FOOTSTEP_ITEM_IDS:
            gfx.Add(Int32(fid))

        flt.Graphics = gfx
        _footstep_filter = flt

    return Items.ApplyFilter(_footstep_filter) or []


def alert_player():
    global _last_alert
    now = time.time()
    if now - _last_alert > 2.0:
        Player.HeadMessage(ALERT_HUE, "Stealther Detected!!!")
        _last_alert = now


def highlight_footstep(item):
    if item.Serial in _colored:
        return

    hue = HIGHLIGHT_HUES[item.Serial % len(HIGHLIGHT_HUES)]
    try:
        Items.SetColor(item.Serial, hue)
        _colored[item.Serial] = hue
    except:
        pass


def point_arrow_at(x, y):
    try: Player.TrackingArrow(int(x), int(y), True)
    except: pass


def clear_arrow():
    try: Player.TrackingArrow(0, 0, False)
    except: pass


def get_direction(px, py, tx, ty):
    dx = tx - px
    dy = ty - py
    horiz = "East" if dx > 0 else "West" if dx < 0 else ""
    vert  = "South" if dy > 0 else "North" if dy < 0 else ""
    if vert and horiz:
        return f"{vert}-{horiz}"
    return vert or horiz or "Here"


def update_newest_footstep(footsteps):
    global _arrow_serial, _arrow_until

    now = time.time()

    for fp in footsteps:
        if fp.Serial not in _seen_steps:
            _seen_steps[fp.Serial] = now

    alive = set(fp.Serial for fp in footsteps)
    for s in list(_seen_steps.keys()):
        if s not in alive:
            _seen_steps.pop(s, None)
            if s == _arrow_serial:
                clear_arrow()
                _arrow_serial = None
                _arrow_until  = 0

    if not _seen_steps:
        return

    newest_serial = max(_seen_steps, key=_seen_steps.get)

    if _arrow_serial == newest_serial and now <= _arrow_until:
        return

    fp = next((f for f in footsteps if f.Serial == newest_serial), None)
    if not fp:
        return

    point_arrow_at(fp.Position.X, fp.Position.Y)
    _arrow_serial = newest_serial
    _arrow_until  = now + ARROW_LIFETIME


def arrow_tick():
    global _arrow_serial, _arrow_until

    if _arrow_serial and time.time() > _arrow_until:
        clear_arrow()
        _arrow_serial = None
        _arrow_until  = 0


# ==================================================
# GUMP
# ==================================================
def draw_gump():
    Gumps.CloseGump(GUMP_ID)

    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)

    w, h = 210, 70
    Gumps.AddBackground(gd, 0, 0, w, h, 9270)
    Gumps.AddAlphaRegion(gd, 0, 0, w, h)

    Gumps.AddLabel(gd, 15, 10, 88, "Frog Stealth Detector")

    if _alert_state:
        Gumps.AddLabel(gd, 25, 38, ALERT_HUE, "!!! ALERT !!!")
    else:
        Gumps.AddLabel(gd, 25, 38, OK_HUE, "Detector Running")

    Gumps.SendGump(
        GUMP_ID,
        Player.Serial,
        650,
        450,
        gd.gumpDefinition,
        gd.gumpStrings
    )
# ==================================================
# Frogge, Magus, Will
# ==================================================
# ==================================================
# MAIN LOOP
# ==================================================
while Player.Connected:
    footsteps = find_footsteps()
    _alert_state = len(footsteps) > 0

    alive = set(fp.Serial for fp in footsteps)
    for s in list(_colored.keys()):
        if s not in alive:
            _colored.pop(s, None)

    if len(_seen_steps) > 50:
        _seen_steps.clear()

    if _alert_state:
        alert_player()

        for fp in footsteps:
            highlight_footstep(fp)

        update_newest_footstep(footsteps)
    else:
        clear_arrow()
        _seen_steps.clear()

    arrow_tick()

    if _alert_state != _last_gump_state:
        draw_gump()
        _last_gump_state = _alert_state

    Misc.Pause(REFRESH_MS)
