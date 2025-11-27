# ==================================
# === Cotton Picker  ===
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

# ---- CONFIG ----
COTTON_PLANT_IDS     = [0x0C51, 0x0C52, 0x0C53, 0x0C54]
COTTON_ITEM_ID       = 0x0DF9   
SCAN_RANGE_TILES     = 12
PICK_REACH_TILES     = 1
CLICK_PAUSE_MS       = 140
LOOP_PAUSE_MS        = 200
PLANT_COOLDOWN_SEC   = 10
HIGHLIGHT_HUE        = 1152

import time
import Misc, Items, Player
from System import Int32
from System.Collections.Generic import List

def manhattan(ax, ay, bx, by):
    return abs(ax - bx) + abs(ay - by)

def player_xy():
    return Player.Position.X, Player.Position.Y

def find_cotton_plants():
    g_list = List[Int32]()
    for g in COTTON_PLANT_IDS:
        g_list.Add(g)

    f = Items.Filter()
    f.Enabled = True
    f.OnGround = True
    f.RangeMax = SCAN_RANGE_TILES
    f.Graphics = g_list

    net_items = Items.ApplyFilter(f) or []
    items = [it for it in net_items]

    px, py = player_xy()
    items.sort(key=lambda it: manhattan(px, py, it.Position.X, it.Position.Y))
    return items

def find_ground_cotton():
    """Find dropped bales of cotton near the player"""
    g_list = List[Int32]()
    g_list.Add(COTTON_ITEM_ID)

    f = Items.Filter()
    f.Enabled = True
    f.OnGround = True
    f.RangeMax = 2
    f.Graphics = g_list  

    net_items = Items.ApplyFilter(f) or []
    return [it for it in net_items]

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
    """Move any nearby cotton bales into backpack"""
    bales = find_ground_cotton()
    for bale in bales:
        if bale and bale.Movable:
            Player.HeadMessage(68, "🎒 Grabbing cotton bale")
            Items.Move(bale, Player.Backpack.Serial, 0)
            Misc.Pause(600)

def main():
    Misc.SendMessage("Cotton Harvester running — scanning fields.", 68)
    last_clicked = {}
    last_count = -1  

    while True:
        plants = find_cotton_plants()
        now = time.monotonic()

        if len(plants) != last_count:
            if plants:
                Player.HeadMessage(55, f"Found {len(plants)} cotton plants nearby")
            else:
                Player.HeadMessage(33, "No cotton detected, swap fields")
            last_count = len(plants)

        did_any = False

        for p in plants:
            highlight(p)

            if not in_reach(p):
                continue
            if now - last_clicked.get(p.Serial, 0.0) < PLANT_COOLDOWN_SEC:
                continue

            Player.HeadMessage(68, "Picking cotton")
            if click_plant(p.Serial):
                last_clicked[p.Serial] = now
                did_any = True
                Misc.Pause(CLICK_PAUSE_MS)
                loot_cotton()

        if did_any:
            Player.HeadMessage(55, "Clear to move on")
        else:
            Misc.Pause(LOOP_PAUSE_MS)

# Run
main()
