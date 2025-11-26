# ==================================
# ==  Player Monitor Tool         ==
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
from System.Collections.Generic import List
from System import Byte

LABEL_HEADER   = 89
LABEL_WHITE    = 1152
LABEL_BLUE     = 89
LABEL_RED      = 33
BUTTON_REFRESH = 4017
ICON_FROG      = 0x2130
FROG_HUE       = 0x09E8
BG_FRAME_ID    = 30546
BAR_TILE_ID    = 40004

EXCLUDE_FULL    = [
    "an exiled revenant",
    "an exiled mage",
    "an exiled knight",
    "Trent",
    "a lesser inferni",
]  
EXCLUDE_PARTIAL = [
    "exiled",
    "inferni",
] 

alertGumpNumber = 883009
showBlues, showReds = [], []
switchOn = False

def draw_bar(gd, x, y, w, h):
    Gumps.AddImageTiled(gd, x, y, w, h, BAR_TILE_ID)

def _norm(s):
    try:
        return (s or "").strip().lower()
    except:
        return ""

def _excluded(name):
    n = _norm(name)
    if not n:
        return False
    if n in (_norm(x) for x in EXCLUDE_FULL):
        return True
    for token in EXCLUDE_PARTIAL:
        if _norm(token) and _norm(token) in n:
            return True
    return False

def updatePlayerGump():
    global switchOn
    gd = Gumps.CreateGump(movable=True)
    if not gd: return
    Gumps.AddPage(gd, 0)

    width = 600
    rowheight = 20
    maxrows = min(max(len(showBlues), len(showReds), 1), 15)
    height = 45 + (maxrows * rowheight) + 35

    Gumps.AddBackground(gd, 210, 120, width, height, BG_FRAME_ID)
    Gumps.AddAlphaRegion(gd, 210, 120, width, height)

    draw_bar(gd, 210, 120, width, 26)
    try:
        Gumps.AddItem(gd, 222, 122, ICON_FROG, FROG_HUE)
    except:
        Gumps.AddItem(gd, 222, 122, ICON_FROG)
    Gumps.AddLabel(gd, 260, 127, LABEL_HEADER, "Frogge Player Watch")

    Gumps.AddLabel(gd, 255, 147, LABEL_HEADER, "Red")
    Gumps.AddLabel(gd, 400, 147, LABEL_HEADER, "X")
    Gumps.AddLabel(gd, 450, 147, LABEL_HEADER, "Y")
    Gumps.AddLabel(gd, 505, 147, LABEL_HEADER, "Dst")

    Gumps.AddLabel(gd, 555, 147, LABEL_HEADER, "Blue")
    Gumps.AddLabel(gd, 650, 147, LABEL_HEADER, "X")
    Gumps.AddLabel(gd, 700, 147, LABEL_HEADER, "Y")
    Gumps.AddLabel(gd, 750, 147, LABEL_HEADER, "Dst")

    y_base = 170
    for idx in range(maxrows):
        if idx < len(showReds):
            name, x, y_pos, dist = showReds[idx]
            name_color = (LABEL_RED if switchOn else LABEL_WHITE)
            Gumps.AddLabel(gd, 250, y_base + idx*rowheight, name_color, str(name))
            Gumps.AddLabel(gd, 400, y_base + idx*rowheight, LABEL_WHITE, str(x))
            Gumps.AddLabel(gd, 450, y_base + idx*rowheight, LABEL_WHITE, str(y_pos))
            Gumps.AddLabel(gd, 505, y_base + idx*rowheight, LABEL_WHITE, str(dist))
        if idx < len(showBlues):
            name, x, y_pos, dist = showBlues[idx]
            name_color = (LABEL_BLUE if switchOn else LABEL_WHITE)
            Gumps.AddLabel(gd, 550, y_base + idx*rowheight, name_color, str(name))
            Gumps.AddLabel(gd, 650, y_base + idx*rowheight, LABEL_WHITE, str(x))
            Gumps.AddLabel(gd, 700, y_base + idx*rowheight, LABEL_WHITE, str(y_pos))
            Gumps.AddLabel(gd, 750, y_base + idx*rowheight, LABEL_WHITE, str(dist))

    if not showReds:
        Gumps.AddLabel(gd, 250, y_base, LABEL_HEADER, "No red players.")
    if not showBlues:
        Gumps.AddLabel(gd, 550, y_base, LABEL_HEADER, "No blue players.")

    draw_bar(gd, 210, 120 + height - 27, width, 26)
    Gumps.AddLabel(gd, 225, 120 + height - 19, LABEL_HEADER, "Red: {}".format(len(showReds)))
    Gumps.AddLabel(gd, 462, 120 + height - 19, LABEL_HEADER, "Blue: {}".format(len(showBlues)))
    Gumps.AddButton(gd, 710, 120 + height - 23, BUTTON_REFRESH, BUTTON_REFRESH + 1, 9999, 1, 1)
    Gumps.AddLabel(gd, 750, 120 + height - 19, LABEL_HEADER, "Refresh")

    Gumps.SendGump(alertGumpNumber, Player.Serial, 420, 120, gd.gumpDefinition, gd.gumpStrings)
    switchOn = not switchOn

while True:
    Misc.Pause(350)

    gd = Gumps.GetGumpData(alertGumpNumber)
    if gd and gd.buttonid == 9999:
        gd.buttonid = -1
        updatePlayerGump()
        continue

    myX, myY = Player.Position.X, Player.Position.Y
    showBlues, showReds = [], []

    fB = Mobiles.Filter(); fB.Enabled=True; fB.RangeMax=50; fB.Notorieties=List[Byte](bytes([1])); fB.IsHuman=1
    for m in Mobiles.ApplyFilter(fB):
        if _excluded(m.Name): continue
        d = int(((m.Position.X-myX)**2 + (m.Position.Y-myY)**2)**0.5)
        showBlues.append((m.Name, m.Position.X, m.Position.Y, d))
    showBlues.sort(key=lambda r: r[3])

    fR = Mobiles.Filter(); fR.Enabled=True; fR.RangeMax=50; fR.Notorieties=List[Byte](bytes([6])); fR.IsHuman=1
    for m in Mobiles.ApplyFilter(fR):
        if _excluded(m.Name): continue
        d = int(((m.Position.X-myX)**2 + (m.Position.Y-myY)**2)**0.5)
        showReds.append((m.Name, m.Position.X, m.Position.Y, d))
    showReds.sort(key=lambda r: r[3])

    updatePlayerGump()
