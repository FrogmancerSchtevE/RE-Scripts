#
#
# I write silly shit here
#
#

import time, Misc, Gumps, Player, Items
from System import Int32
from System.Collections.Generic import List

# ====================================================================
# GLOBAL CONFIGS
# ====================================================================
GUMP_ID     = 0xC0FFEE42
REFRESH_MS  = 200
GUMP_POS    = (650, 650)
SCRIPT_VERSION = "v0.0.4"  

_running          = True
_runtime_detector = True
_status_msg       = "Idle"
_last_detect_time = 0
_last_detect_xy   = (0, 0)
_last_seen_serials = set()

# ====================================================================
# VISUAL / ICON SETTINGS
# ====================================================================
FROG_ICON = 0x2130
FROG_HUE  = 0x09E8

BTN_REFRESH_ID = 70001
BTN_QUIT_ID    = 70002

STYLE_BG_GFX      = 30546
STYLE_DIVIDER_GFX = 40004
STYLE_BAR_GFX     = 9354
STYLE_BORDER_GFX  = 2620
TITLE_COLOR       = 0x35
STATUS_COLOR_IDLE   = 0x021 
STATUS_COLOR_ACTIVE = 0x03C  

# ====================================================================
# DETECTOR CONFIG
# ====================================================================
SPARKLE_GRAPHICS = [
    0xAB42, 0xAB44, 0xAB45, 0xAB46, 0xAB47, 0xAB48,
    0xAB49, 0xAB4A, 0xAB4B, 0xAB4C, 0xAB4D, 0xAB4E,
    0xAB4F, 0xAB50, 0xAB51, 0xAB52, 0xAB53, 0xAB54, 0xAB55,
    0x373A, 0x373B, 0x373C, 0x373D, 0x373E, 0x373F,
    0x3740, 0x3741, 0x3742, 0x3743, 0x3744, 0x3745,
    0x3746, 0x3747, 0x3748, 0x3749
]

SCAN_RANGE_TILES = 24 # max range RE can interpret. 
SCAN_INTERVAL_MS = 300
ARROW_DURATION_SEC = 10

# ====================================================================
# HELPERS
# ====================================================================
def scan_for_sparkles():
    f = Items.Filter()
    f.Enabled = True
    f.OnGround = True
    f.RangeMax = SCAN_RANGE_TILES
    g_list = List[Int32]()
    for g in SPARKLE_GRAPHICS:
        g_list.Add(g)
    f.Graphics = g_list
    return list(Items.ApplyFilter(f) or [])

def soft_refresh():
    global _status_msg, _last_detect_time, _last_detect_xy, _last_seen_serials
    Misc.SendMessage("Soft refreshing Sparkle Detector...", 68)
    _status_msg = "Idle"
    _last_detect_time = 0
    _last_detect_xy = (0, 0)
    _last_seen_serials = set()
    try:
        Player.TrackingArrow(0, 0, False)
    except:
        pass

def stop_script():
    global _running
    Misc.SendMessage("Stopping Sparkle Detector", 33)
    _running = False
    try:
        Player.TrackingArrow(0, 0, False)
    except:
        pass
    Gumps.CloseGump(GUMP_ID)

# ====================================================================
# DETECTION STEP
# ====================================================================
def detector_step():
    global _status_msg, _last_detect_time, _last_detect_xy, _last_seen_serials

    sparkles = scan_for_sparkles()
    current_serials = set(it.Serial for it in sparkles)
    new_serials = current_serials - _last_seen_serials
    now = time.time()

    if new_serials:
        for serial in new_serials:
            it = Items.FindBySerial(serial)
            if not it:
                continue
            _last_detect_xy = (it.Position.X, it.Position.Y)
            _last_detect_time = now
            _status_msg = f"Detected at {_last_detect_xy[0]}, {_last_detect_xy[1]}"
            Misc.Beep()
            Player.HeadMessage(68, "Sparkle detected nearby!")
            try:
                Player.TrackingArrow(it.Position.X, it.Position.Y, True)
            except:
                pass
            break

    if _last_detect_time and now - _last_detect_time > ARROW_DURATION_SEC:
        try:
            Player.TrackingArrow(0, 0, False)
        except:
            pass
        _last_detect_time = 0
        _status_msg = "Idle"

    _last_seen_serials = current_serials
    Misc.Pause(SCAN_INTERVAL_MS)

# ====================================================================
# GUMP / GUI
# ====================================================================
def render_gui():
    Gumps.CloseGump(GUMP_ID)
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)

    width, height = 280, 105
    Gumps.AddBackground(gd, 0, 0, width, height, STYLE_BG_GFX)
    Gumps.AddAlphaRegion(gd, 0, 0, width, height)

    Gumps.AddImageTiled(gd, 0, 0, width, 5, STYLE_BORDER_GFX)
    Gumps.AddImageTiled(gd, 0, height - 5, width, 5, STYLE_BORDER_GFX)
    Gumps.AddImageTiled(gd, 0, 0, 5, height, STYLE_BORDER_GFX)
    Gumps.AddImageTiled(gd, width - 5, 0, 5, height, STYLE_BORDER_GFX)

    Gumps.AddItem(gd, 8, 6, FROG_ICON, FROG_HUE)

    title_text = "Sparkle Detector"
    text_width = len(title_text) * 6
    centered_x = (width // 2) - (text_width // 2)
    Gumps.AddLabel(gd, centered_x, 10, TITLE_COLOR, title_text)

    bx = width - 65
    Gumps.AddButton(gd, bx, 6, 4005, 4006, BTN_REFRESH_ID, 1, 0)
    Gumps.AddLabel(gd, bx + 18, 8, 68, "↻")

    Gumps.AddButton(gd, bx + 32, 6, 4017, 4018, BTN_QUIT_ID, 1, 0)
    Gumps.AddLabel(gd, bx + 50, 8, 33, "✖")

    Gumps.AddImageTiled(gd, 8, 32, width - 16, 1, STYLE_DIVIDER_GFX)

    pill_y = 45
    Gumps.AddImageTiled(gd, 10, pill_y, width - 20, 22, STYLE_BAR_GFX)
    color = STATUS_COLOR_ACTIVE if _status_msg != "Idle" else STATUS_COLOR_IDLE
    Gumps.AddLabel(gd, 18, pill_y + 4, color, f"Status: {_status_msg}")

    ver_text = f"{SCRIPT_VERSION}"
    ver_x = width - (len(ver_text) * 6) - 12
    Gumps.AddLabel(gd, ver_x, height - 20, 0x0481, ver_text)

    Gumps.SendGump(GUMP_ID, Player.Serial, GUMP_POS[0], GUMP_POS[1], gd.gumpDefinition, gd.gumpStrings)

# ====================================================================
# MAIN LOOP
# ====================================================================
def main():
    global _running
    Misc.SendMessage("Sparkle Detector started", 68)

    while _running and Player.Connected:
        gd = Gumps.GetGumpData(GUMP_ID)

        if _runtime_detector:
            detector_step()

        if gd:
            if gd.buttonid == BTN_REFRESH_ID:
                soft_refresh()
            elif gd.buttonid == BTN_QUIT_ID:
                stop_script()

        render_gui()
        Misc.Pause(REFRESH_MS)

if __name__ == "__main__":
    main()
