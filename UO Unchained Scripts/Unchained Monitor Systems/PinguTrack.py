# ==================================
# == Quick n Dirty Pingu Tracker  ==
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

import Misc, Mobiles, Player, time
from System.Collections.Generic import List
from System import Int32


#========================
#          Configs
#======================== 

PENGUIN_GRAPHIC = 0x069C
MAX_RANGE       = 24
SCAN_DELAY      = 500
MESSAGE_COOLDOWN = 7    # seconds

gfx = List[Int32]()
gfx.Add(Int32(PENGUIN_GRAPHIC))

last_msg_time = 0

#=========================
#          Helpers
#=========================
def get_direction(px, py, tx, ty):
    dx = tx - px
    dy = ty - py
    horiz = "East" if dx > 0 else "West" if dx < 0 else ""
    vert  = "South" if dy > 0 else "North" if dy < 0 else ""
    if vert and horiz: return f"{vert}-{horiz}"
    return vert or horiz or "Here"

def point_arrow_at(x, y):
    try:
        Player.TrackingArrow(int(x), int(y), True)
    except:
        Player.HeadMessage(33, "TrackingArrow() failed.")

def clear_arrow():
    try:
        Player.TrackingArrow(0, 0, False)
    except:
        pass

        
#========================
#          MAIN
#========================       
while Player.Connected:

    f = Mobiles.Filter()
    f.Enabled = True
    f.RangeMax = MAX_RANGE
    f.Graphics = gfx

    penguins = Mobiles.ApplyFilter(f)

    if penguins:
        penguin = penguins[0]

        px, py = Player.Position.X, Player.Position.Y
        tx, ty = penguin.Position.X, penguin.Position.Y

        point_arrow_at(tx, ty)

        now = time.time()
        if now - last_msg_time >= MESSAGE_COOLDOWN:
            direction = get_direction(px, py, tx, ty)
            Player.HeadMessage(68, f"🐧 Penguin: {direction}")
            last_msg_time = now

    else:
        clear_arrow()

    Misc.Pause(SCAN_DELAY)
