# ==================================
# ==  Grinch Satchel Detector     ==
# ==================================
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
# ====================================================================.

from System import Int32
from System.Collections.Generic import List
import Gumps, Player, Misc, Items, time

# ==================================================
# CONFIG
# ==================================================
GUMP_ID        = 0xF2064753
REFRESH_MS    = 400
SCAN_RANGE    = 24

TARGET_ITEMID = 0xA2C7
HIGHLIGHT_HUE = 1152

ALERT_HUE     = 33
OK_HUE        = 68

ARROW_LIFETIME = 10.0  

# ==================================================
# STATE
# ==================================================
_alert_state   = False
_last_alert    = 0
_seen_items    = set()
_arrow_until   = 0
_item_filter   = None

# ==================================================
# HELPERS
# ==================================================
def build_filter():
    flt = Items.Filter()
    flt.Enabled  = True
    flt.OnGround = True
    flt.RangeMax = SCAN_RANGE

    gfx = List[Int32]()
    gfx.Add(Int32(TARGET_ITEMID))
    flt.Graphics = gfx
    return flt

def find_satchels():
    global _item_filter
    if not _item_filter:
        _item_filter = build_filter()
    return Items.ApplyFilter(_item_filter) or []

def alert_player():
    global _last_alert
    now = time.time()
    if now - _last_alert > 2.0:
        Player.HeadMessage(ALERT_HUE, "Grinch Satchel Detected!")
        _last_alert = now

def highlight_item(itm):
    try:
        Items.SetColor(itm.Serial, HIGHLIGHT_HUE)
    except:
        pass

def point_arrow(itm):
    global _arrow_until
    try:
        Player.TrackingArrow(
            int(itm.Position.X),
            int(itm.Position.Y),
            True
        )
        _arrow_until = time.time() + ARROW_LIFETIME
    except:
        pass

def clear_arrow_if_needed():
    global _arrow_until
    if _arrow_until and time.time() > _arrow_until:
        try:
            Player.TrackingArrow(0, 0, False)
        except:
            pass
        _arrow_until = 0

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

    Gumps.AddLabel(gd, 15, 10, 88, "Grinch Satchel Detector")

    if _alert_state:
        Gumps.AddLabel(gd, 25, 38, ALERT_HUE, "SATCHEL FOUND!")
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
# MAIN LOOP
# ==================================================

while Player.Connected:

    found_any = False
    satchels = find_satchels()

    for itm in satchels:
        if not itm or itm.Serial in _seen_items:
            continue

        _seen_items.add(itm.Serial)
        found_any = True

        # highlight_item(itm)
        alert_player()
        point_arrow(itm)

    _alert_state = found_any
    draw_gump()

    clear_arrow_if_needed()
    Misc.Pause(REFRESH_MS)
