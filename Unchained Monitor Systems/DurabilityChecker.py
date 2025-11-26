# ==================================
# ==  Durability Tracker          ==
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
from AutoComplete import *
from System.Collections.Generic import List as CList
from System import Byte

# ===========================================================
# CONFIGURATION
# ===========================================================
REFRESH_DURATION = 1000          
ALERT_LOW_DURABILITY = True
ALERT_THRESHOLD = 20
ROW_HEIGHT = 20
GUMP_ID = 0x51D07D               
TITLE = "Frogs Durability Tracker"

# ===========================================================
# HELPERS
# ===========================================================
def proper_case(text):
    return " ".join(word.capitalize() for word in text.split())

def gradient_hue(r):
    r = max(0.0, min(1.0, r))
    if r < 0.5:
        return 33  
    elif r < 0.75:
        return 53  
    elif r < 0.9:
        return 68  
    else:
        return 73  

# ===========================================================
# LAYER TRACKER
# ===========================================================
class LayerEntry:
    LAYERS = [
        "RightHand","LeftHand","Shoes","Pants","Shirt","Head",
        "Gloves","Ring","Neck","Waist","InnerTorso","Bracelet",
        "MiddleTorso","Earrings","Arms","Cloak",
        "OuterTorso","OuterLegs","InnerLegs","Talisman",
    ]

    @classmethod
    def iter_layers(cls):
        for layer in cls.LAYERS:
            item = Player.GetItemOnLayer(layer)
            if not item:
                continue
            Items.WaitForProps(item.Serial, 1000)
            if item.MaxDurability == 0:
                continue
            yield cls(
                item.Serial,
                layer,
                item.Durability,
                item.MaxDurability,
                proper_case(item.Name or "???")
            )

    def __init__(self, serial, layer, dur, max_dur, name):
        self.serial = serial
        self.layer = layer
        self.dur = dur
        self.max_dur = max_dur
        self.dur_ratio = float(dur) / max(1.0, float(max_dur))
        self.name = name

def VisualEffectSelf(src, tile_type=14284, duration=25, hue=53, render_mode=3):
    packet = b"\xc0"
    packet += b"\x03"
    packet += (src & 0xFFFFFFFF).to_bytes(4, "big")
    packet += (0).to_bytes(4, "big")
    packet += (tile_type & 0xFFFF).to_bytes(2, "big")
    packet += (0).to_bytes(2, "big") * 6
    packet += (1).to_bytes(1, "big")
    packet += (duration & 0xFF).to_bytes(1, "big")
    packet += (0).to_bytes(1, "big") * 4
    packet += (hue & 0xFFFFFFFF).to_bytes(4, "big")
    packet += (render_mode & 0xFFFFFFFF).to_bytes(4, "big")
    PacketLogger.SendToClient(CList[Byte](packet))

# ===========================================================
# MAIN LOOP
# ===========================================================
prev_layers = []

while Player.Connected:
    gump_closed = Gumps.WaitForGump(GUMP_ID, REFRESH_DURATION)
    cur_layers = list(LayerEntry.iter_layers())

    if ALERT_LOW_DURABILITY and not Timer.Check("blink"):
        if any(100 * e.dur_ratio <= ALERT_THRESHOLD for e in cur_layers):
            Misc.SendMessage("Some of your equipment has low durability!", 53)
            Timer.Create("blink", 3000)
            VisualEffectSelf(Player.Serial)

    if (not gump_closed) and (cur_layers == prev_layers):
        continue

    prev_layers = cur_layers
    cur_layers.sort(key=lambda x: x.dur_ratio)
    num_entries = len(cur_layers)

    Gumps.CloseGump(GUMP_ID)
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)

    height = 50 + ROW_HEIGHT * num_entries
    width = 290
    Gumps.AddBackground(gd, 0, 0, width, height, 5054)
    Gumps.AddAlphaRegion(gd, 0, 0, width, height)

    title_x = (width - (len(TITLE) * 8)) // 2
    Gumps.AddLabel(gd, title_x, 10, 0x480, TITLE)
    Gumps.AddImageTiled(gd, 10, 30, width - 20, 2, 30071)

    for i, entry in enumerate(cur_layers):
        r = entry.dur_ratio
        dur_perc = 100 * r
        cur_y = 35 + ROW_HEIGHT * i
        hue = gradient_hue(r)

        tooltip = (
            "<BASEFONT COLOR='#FFFF00'>%s</BASEFONT><BR />%d / %d (%.1f%%)"
            % (entry.name, entry.dur, entry.max_dur, dur_perc)
        )

        Gumps.AddLabel(gd, 15, cur_y, 0x47E, entry.layer)
        Gumps.AddTooltip(gd, tooltip)

        bar_x, bar_y, bar_w, bar_h = 130, cur_y + 2, 120, ROW_HEIGHT - 4
        Gumps.AddImageTiled(gd, bar_x, bar_y, bar_w, bar_h, 40004)

        fill_w = max(1, int(bar_w * r))
        if fill_w > 0:
            Gumps.AddImageTiled(gd, bar_x, bar_y, fill_w, bar_h, 9354,)

        Gumps.AddLabel(gd, 255, cur_y, hue, "%.0f%%" % dur_perc)

    Gumps.SendGump(GUMP_ID, Player.Serial, 25, 25, gd.gumpDefinition, gd.gumpStrings)
