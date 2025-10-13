# ==================================
# === WeDoAWeave ===
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

SPINNING_WHEEL_GRAPHICS = [0x1015, 0x1019, 0x101A, 0x101B]
LOOM_GRAPHICS           = [0x105F, 0x1060, 0x1061, 0x1062]

COTTON_TYPE_ID          = 0x0DF9  
SPOOL_TYPE_ID           = 0x0FA0  

RANGE_HINT_TILES        = 14


TARGET_TIMEOUT_MS       = 2000
SPIN_PAUSE_MS           = 1200   
WEAVE_STEP_DELAY_MS     = 250    

WEAVE_BATCH_PER_CYCLE   = 5

import Misc, Items, Target, Player, time
from System.Collections.Generic import List

def get_one_cotton():
    return Items.FindByID(COTTON_TYPE_ID, -1, Player.Backpack.Serial)

def get_one_spool():
    return Items.FindByID(SPOOL_TYPE_ID, -1, Player.Backpack.Serial)

def count_spools():
    try:
        return Items.BackpackCount(SPOOL_TYPE_ID, -1)
    except:
        return 0

_cached_wheel_serial = None
_cached_loom_serial  = None

def _find_nearest_ground_item_by_types(graphics_list, max_range):
    try:
        g_list = List[int]()
        for g in graphics_list:
            g_list.Add(g)
        flt = Items.Filter()
        flt.Enabled = True
        flt.OnGround = True
        flt.RangeMax = max_range
        flt.Graphics = g_list
        cands = Items.ApplyFilter(flt)
    except:
        cands = []
        for g in graphics_list:
            try:
                f2 = Items.Filter()
                f2.Enabled = True
                f2.OnGround = True
                f2.RangeMax = max_range
                f2.Graphic = g
                res = Items.ApplyFilter(f2)
                if res:
                    cands.extend(res)
            except:
                pass

    if not cands:
        return None

    try:
        px, py = Player.Position.X, Player.Position.Y
    except:
        px = py = 0

    def dist(it):
        try:
            return abs(it.Position.X - px) + abs(it.Position.Y - py)
        except:
            return 10**9

    cands.sort(key=dist)
    return cands[0]

def _prompt_world_target(msg):
    try:
        return Target.PromptTarget(msg)
    except:
        Misc.SendMessage(msg, 88)
        return None

def get_wheel_serial():
    global _cached_wheel_serial
    if _cached_wheel_serial:
        return _cached_wheel_serial
    itm = _find_nearest_ground_item_by_types(SPINNING_WHEEL_GRAPHICS, RANGE_HINT_TILES)
    if itm:
        _cached_wheel_serial = itm.Serial
        return _cached_wheel_serial
    s = _prompt_world_target("Target the SPINNING WHEEL.")
    if s:
        _cached_wheel_serial = s
    return _cached_wheel_serial

def get_loom_serial():
    global _cached_loom_serial
    if _cached_loom_serial:
        return _cached_loom_serial
    itm = _find_nearest_ground_item_by_types(LOOM_GRAPHICS, RANGE_HINT_TILES)
    if itm:
        _cached_loom_serial = itm.Serial
        return _cached_loom_serial
    s = _prompt_world_target("Target the LOOM.")
    if s:
        _cached_loom_serial = s
    return _cached_loom_serial

def use_pack_item_on_world(pack_item_serial, world_serial):
    if not world_serial:
        return False
    Items.UseItem(pack_item_serial)  
    if not Target.WaitForTarget(TARGET_TIMEOUT_MS, False):
        return False
    Target.TargetExecute(world_serial)
    return True

def spin_one_bale_fast():
    wheel = get_wheel_serial()
    if not wheel:
        Misc.SendMessage("No spinning wheel selected/in range.", 33)
        return False
    bale = get_one_cotton()
    if not bale:
        return False
    if not use_pack_item_on_world(bale.Serial, wheel):
        Misc.SendMessage("Failed to target wheel with cotton.", 33)
        return False
    Misc.Pause(SPIN_PAUSE_MS)
    return True

def weave_up_to_n_spools_fast(n):
    loom = get_loom_serial()
    if not loom:
        Misc.SendMessage("No loom selected/in range.", 33)
        return 0
    fed = 0
    while fed < n:
        sp = get_one_spool()
        if not sp:
            break
        Items.UseItem(sp.Serial)  
        if not Target.WaitForTarget(TARGET_TIMEOUT_MS, False):
            Misc.Pause(120)
            continue
        Target.TargetExecute(loom)
        fed += 1
        Misc.Pause(WEAVE_STEP_DELAY_MS)
    return fed

def main():
    Misc.SendMessage("Weaving Fast. Vroom", 68)

    while True:
        have_cotton = get_one_cotton() is not None
        have_spools = count_spools() > 0

        if not have_cotton and not have_spools:
            Misc.SendMessage("No cotton and no spools left. Finished.", 68)
            break

        if have_cotton:
            spin_one_bale_fast()

        if count_spools() > 0:
            weave_up_to_n_spools_fast(WEAVE_BATCH_PER_CYCLE)

        Misc.Pause(120)

    Misc.SendMessage("Script finished.", 68)

main()
