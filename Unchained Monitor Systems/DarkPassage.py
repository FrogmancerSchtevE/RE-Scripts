# A compact souls progress bar for Dark Passage Lantern
# Author: Frogmancer SchtevE 

import re

# Configs
REFRESH_MS     = 700
GUMP_ID        = 0xD4A3BEEF
GUMP_X, GUMP_Y = 25, 25

ROW_H          = 18
LABEL_W        = 88
LABEL_GAP      = 4
BAR_W          = 120
BAR_BG_TILE    = 40004
BAR_FILL_TILE  = 9354

LABEL_HUE      = 0x47E

NAME_RE  = re.compile(r"dark\s+passage\s+lantern", re.I)
SOULS_RE = re.compile(r"collected\s+souls\s+(\d+)\s*/\s*(\d+)", re.I)

def pct_hue(frac):
    """Green→yellow→orange steps like RE durability (5 buckets)."""
    level = int(5 * max(0.0, min(1.0, frac)))
    return 0x21 + 5 * level

def find_equipped_lantern():
    """Return (layer, item) if the lantern is equipped, else (None, None)."""
    for layer in ("RightHand", "LeftHand"):
        itm = Player.GetItemOnLayer(layer)
        if not itm:
            continue
        if itm.Name and NAME_RE.search(itm.Name):
            return layer, itm
        Items.WaitForProps(itm.Serial, 1200)
        for line in Items.GetPropStringList(itm.Serial):
            if NAME_RE.search(line):
                return layer, itm
    return None, None

def read_collected_souls(itm, attempts=3):
    """
    Try to read souls (cur, cap). Returns (None, None) if not found.
    Retries a few times to smooth out laggy prop updates.
    """
    for _ in range(attempts):
        Items.WaitForProps(itm.Serial, 1200)
        lines = Items.GetPropStringList(itm.Serial)
        for line in lines:
            m = SOULS_RE.search(line)
            if m:
                cur = int(m.group(1))
                cap = max(1, int(m.group(2)))
                cur = max(0, min(cur, cap))
                return cur, cap
        Misc.Pause(150)
    return None, None

last_cur = None
last_cap = None
while Player.Connected:
    try:
        layer, lantern = find_equipped_lantern()

        if not lantern:
            Gumps.CloseGump(GUMP_ID)
            last_cur = last_cap = None
            Misc.Pause(REFRESH_MS)
            continue

        cur, cap = read_collected_souls(lantern, attempts=3)
        if cur is None or cap is None:
            cur, cap = last_cur, last_cap

        if cur is None or cap is None:
            Misc.Pause(REFRESH_MS)
            continue

        last_cur, last_cap = cur, cap

        frac = max(0.0, min(1.0, float(cur) / float(cap)))
        pct  = 100.0 * frac
        hue  = pct_hue(frac)

        left_text = "Souls Collected"
        tooltip = (f"<BASEFONT COLOR=\"#FFFF00\">Dark Passage Lantern</BASEFONT>"
                   f"<BR />Collected Souls: {cur} / {cap} ({pct:.1f}%)")

        total_w = 8 + LABEL_W + LABEL_GAP + BAR_W + 8
        total_h = 8 + ROW_H

        Gumps.CloseGump(GUMP_ID)
        gd = Gumps.CreateGump(movable=True)
        Gumps.AddPage(gd, 0)

        Gumps.AddBackground(gd, 0, 0, total_w, total_h, 30546)
        Gumps.AddAlphaRegion(gd, 0, 0, total_w, total_h)

        y = 4
        Gumps.AddLabel(gd, 6, y-1, LABEL_HUE, left_text)   # compact, slight raise
        Gumps.AddTooltip(gd, tooltip)

        bar_x = 6 + LABEL_W + LABEL_GAP
        bar_y = y + 1
        bar_h = ROW_H - 3

        Gumps.AddImageTiled(gd, bar_x, bar_y, BAR_W, bar_h, BAR_BG_TILE)
        Gumps.AddTooltip(gd, tooltip)

        fill_w = int(BAR_W * frac)
        if fill_w > 0:
            Gumps.AddImageTiled(gd, bar_x, bar_y, fill_w, bar_h, BAR_FILL_TILE)

        pct_text = f"{pct:.0f}%"
        TEXT_W_EST = 36
        tx = bar_x + (BAR_W - TEXT_W_EST) // 2
        Gumps.AddLabel(gd, tx, y-1, hue, pct_text)
        Gumps.AddTooltip(gd, tooltip)

        Gumps.SendGump(GUMP_ID, Player.Serial, GUMP_X, GUMP_Y, gd.gumpDefinition, gd.gumpStrings)

    except Exception as ex:
        Misc.SendMessage("DarkPassage error: " + str(ex), 33)
    finally:
        Misc.Pause(REFRESH_MS)
