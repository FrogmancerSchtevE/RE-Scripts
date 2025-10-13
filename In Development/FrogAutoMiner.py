# FrogAutoMiner.py — Razor Enhanced 


ENABLE_DEPOSIT_TO_BANK = True
ENABLE_DEPOSIT_TO_HOME = True     

BANK_RUNE_INDEX  = 1
HOME_RUNE_INDEX  = 2               

MINE_RUNE_INDICES = [3,4,5,6,7,8,9,10,11,12,13,14,15,16]
BLACKOUT_MINUTES = 23

USE_CLASSIC_BUTTON_MAP = False
BUTTON_BASE   = 6
BUTTON_STRIDE = 7
BUTTON_OFFSET = 0
CUSTOM_RUNE_BUTTON_IDS = {
    1:50,2:51,3:52,4:53,5:54,6:55,7:56,8:57,9:58,10:59,11:60,12:61,13:62,14:63,15:64,16:65
}

CAST_RETRY_MAX = 4
WAIT_RETRY_MAX = 6
WAIT_BACKOFF_MS = (600, 1200)
LANDING_SETTLE_MS = (700, 1100)
RECALL_VERIFY_TIMEOUT_MS = 5000

WEIGHT_SOFT_CAP = 0               
PREEMPT_BANK_WEIGHT = 425         
POST_SMELT_BANK_WEIGHT = 400      
MINING_TOOLS = [0x0E86, 0x0E85, 0x0FB4, 0x0F39]   
ORE_IDS   = [(0x19B7, -1), (0x19B8, -1), (0x19B9, -1), (0x1779, -1)]  
INGOT_IDS = [(0x1BF2, -1)]                                            

USE_FIRE_BEETLE_SMELT = True

AREA_RADIUS_TILES = 5            
NOHIT_MAX_SWINGS  = 6            
USE_SOUND_HINT    = True
MINING_SOUND_CODES = ["0x125", "feet05a.wav"]  

STATIONARY_SWINGS_RANGE = (6, 8)   
EMPTY_VEIN_PATTERNS = (
    "There is no metal here to mine|no metal here|You loosen some rocks but fail|You can't mine that|"
    "You cannot mine|no line of sight|You have worn out the spot"
)


HOUSE_SHELF_XY = (2061, 1184)
SHELF_ITEMID = 0x71FC          
SHELF_BUTTON_FILL = 121        
SHELF_SEARCH_RANGE = 4         

ANNOUNCE_PREFIX = "[FrogAutoMiner]"
SHOW_DEBUG = False

import System
from System import DateTime
from System.Collections.Generic import List
from System import Int32

_rng = System.Random()
def _randint(a,b):
    if b<a: a,b=b,a
    return a + _rng.Next(b-a+1)
def _jitter(ms_lo, ms_hi): Misc.Pause(_randint(ms_lo, ms_hi))
def _now_ms(): return int((DateTime.UtcNow - DateTime(1970,1,1)).TotalMilliseconds)
def _say(msg): Misc.SendMessage(f"{ANNOUNCE_PREFIX} {msg}", 68)
def _err(msg): Misc.SendMessage(f"{ANNOUNCE_PREFIX} {msg}", 33)
def _dbg(msg):
    if SHOW_DEBUG: Misc.SendMessage("[DBG] "+msg, 55)

_blackouts = {}
_last_recall_ms = 0
_last_mine_rune = None

def _shuffle_list(seq):
    arr = list(seq)
    n = len(arr)
    for i in range(n - 1, 0, -1):
        j = _rng.Next(i + 1)
        arr[i], arr[j] = arr[j], arr[i]
    return arr


RUNEBOOK_KEY = "frog_runebook_serial"
_RUNEBOOK_ITEMIDS = set([0x0EFA])
_RUNIC_ATLAS_ITEMIDS = set([0x2252, 0x2253])

def _looks_like_runebook(it):
    if not it: return False
    if it.ItemID in _RUNEBOOK_ITEMIDS or it.ItemID in _RUNIC_ATLAS_ITEMIDS: return True
    try:
        if it.Name and ("runebook" in it.Name.lower() or "atlas" in it.Name.lower()): return True
    except: pass
    try:
        props = Items.GetPropStringList(it)
        if props:
            joined = " ".join([str(p).lower() for p in props])
            if "runebook" in joined or "runic atlas" in joined: return True
    except: pass
    return False

def _btn_for_rune(index):
    if not USE_CLASSIC_BUTTON_MAP:
        return CUSTOM_RUNE_BUTTON_IDS.get(index)
    return BUTTON_BASE + (index-1)*BUTTON_STRIDE + BUTTON_OFFSET

def set_runebook(serial): Misc.SetSharedValue(RUNEBOOK_KEY, int(serial))

def get_runebook(force_prompt=False):
    if not force_prompt and Misc.CheckSharedValue(RUNEBOOK_KEY):
        s = Misc.ReadSharedValue(RUNEBOOK_KEY)
        it = Items.FindBySerial(s)
        if it and _looks_like_runebook(it): return it
    Misc.SendMessage("Target your mining runebook / atlas.", 68)
    sel = Target.PromptTarget("Target your runebook / atlas", 68)
    it = Items.FindBySerial(sel)
    if not it: _err("Invalid runebook target."); return None
    set_runebook(sel); return it

def throttle_recalls(ms_gap=900):
    global _last_recall_ms
    now = _now_ms()
    if now - _last_recall_ms < ms_gap:
        Misc.Pause(ms_gap - (now - _last_recall_ms))

def _player_xyz():
    try: return (Player.Position.X, Player.Position.Y, Player.Position.Z)
    except: return (0,0,0)

def _moved_far(from_xyz, min_tiles=4):
    x,y,z = _player_xyz(); fx,fy,fz = from_xyz
    return abs(x-fx) + abs(y-fy) >= min_tiles

def _saw_recall_journal():
    return Journal.Search("Kal Ort Por|Recall|Where do you wish to go")

BANK_BOX_KEY = "FROG_BANK_BOX_SERIAL"

def _prompt_container(key, prompt):
    if Misc.CheckSharedValue(key):
        return Misc.ReadSharedValue(key)
    sel = Target.PromptTarget(prompt, 68)
    if sel:
        Misc.SetSharedValue(key, sel)
        return sel
    return 0

def ensure_bank_serial():
    s = _prompt_container(BANK_BOX_KEY, "Target your BANK BOX")
    bx = Items.FindBySerial(s)
    if not bx or not bx.IsContainer:
        Misc.SendMessage("That wasn't a container; please target the **bank box** container.", 33)
        if Misc.CheckSharedValue(BANK_BOX_KEY):
            Misc.RemoveSharedValue(BANK_BOX_KEY)
        return _prompt_container(BANK_BOX_KEY, "Target your BANK BOX (container)")
    return s

def _move_list(dest, pairs):
    moved = 0
    pack = Player.Backpack
    if not pack: return 0
    for it in list(pack.Contains):
        for iid,h in pairs:
            if it.ItemID == iid and (h == -1 or it.Hue == h):
                Items.Move(it, dest, 0)
                Misc.Pause(450)
                moved += 1
                break
    return moved

def deposit_to_bank():
    if not ENABLE_DEPOSIT_TO_BANK: return False
    s = ensure_bank_serial()
    if not s: return False
    Player.ChatSay(0, "bank"); Misc.Pause(350)
    moved_ore   = _move_list(s, ORE_IDS)
    moved_ingot = _move_list(s, INGOT_IDS)
    total = moved_ore + moved_ingot
    _say(f"Bank deposit: ore {moved_ore}, ingot {moved_ingot} (total {total}).")
    return total > 0

BEETLE_MOBILE_KEY = "FROG_BEETLE_MOBILE"

def ensure_beetle_mobile():
    if not USE_FIRE_BEETLE_SMELT: return 0
    if Misc.CheckSharedValue(BEETLE_MOBILE_KEY):
        return Misc.ReadSharedValue(BEETLE_MOBILE_KEY)
    Misc.SendMessage("Target your FIRE BEETLE (mobile) for smelting.", 68)
    sel = Target.PromptTarget("Target your fire beetle", 68)
    if sel:
        Misc.SetSharedValue(BEETLE_MOBILE_KEY, sel)
        return sel
    return 0

def smelt_all_ore_on_beetle():
    if not USE_FIRE_BEETLE_SMELT: return False
    beetle = ensure_beetle_mobile()
    if not beetle: return False
    pack = Player.Backpack
    if not pack: return False
    smelted = 0
    for it in list(pack.Contains):
        for iid,h in ORE_IDS:
            if it.ItemID==iid and (h==-1 or it.Hue==h):
                Items.UseItem(it)
                if Target.WaitForTarget(1500, False):
                    Target.TargetExecute(beetle)
                Misc.Pause(950)
                smelted += 1
                break
    if smelted: _say(f"Smelted {smelted} ore stacks on fire beetle.")
    return smelted > 0

def _pathfind_to(x,y,z=None):
    try:
        if z is None: z = Player.Position.Z
    except:
        z = 0
    try:
        PathFinding.Go(x,y,z); return True
    except: pass
    try:
        Misc.PathFindTo(x,y,z); return True
    except: pass
    return False

def _land_z(x,y):
    try:
        return Statics.GetLandZ(x, y, Player.Map)
    except:
        return 0

def _find_nearby_shelf(range_tiles=SHELF_SEARCH_RANGE):
    f = Items.Filter()
    f.Enabled = True
    f.RangeMax = range_tiles
    f.Graphics = List[Int32]([SHELF_ITEMID])
    f.OnGround = 1
    lst = Items.ApplyFilter(f)
    return lst[0] if lst else None

def deposit_ingots_to_house_shelf():
    hx, hy = HOUSE_SHELF_XY
    hz = _land_z(hx, hy)
    _pathfind_to(hx, hy, hz); Misc.Pause(300)

    shelf = _find_nearby_shelf()
    if not shelf:
        for _ in range(4):
            _pathfind_to(hx+_randint(-1,1), hy+_randint(-1,1), hz); Misc.Pause(250)
            shelf = _find_nearby_shelf()
            if shelf: break
    if not shelf:
        _err("Resource shelf not found near house coords.")
        return False

    Items.UseItem(shelf)
    if not Gumps.WaitForGump(0, 4000):
        _err("Shelf gump did not open.")
        return False

    gid = Gumps.CurrentGump()
    if gid:
        Gumps.SendAction(gid, SHELF_BUTTON_FILL)
        Misc.Pause(600)
        try: Gumps.CloseGump(gid)
        except: pass
        _say("Deposited resources to house shelf.")
        return True

    _err("No active shelf gump to click.")
    return False

def _nudge_step():
    x, y, z = _player_xyz()
    dx = _randint(-1, 1)
    dy = _randint(-1, 1)
    if dx == 0 and dy == 0: dx = 1
    _pathfind_to(x + dx, y + dy, z)
    Misc.Pause(_randint(220, 380))

def _recall_clicked_moved(start_xyz, timeout_ms):
    deadline = _now_ms() + timeout_ms
    while _now_ms() < deadline:
        if _moved_far(start_xyz, 4) or _saw_recall_journal():
            return True
        Misc.Pause(80)
    return False

def recall_to_rune(index):
    """Open book → click rune → verify. If not moved, nudge once and retry once."""
    global _last_recall_ms
    throttle_recalls()

    rb = get_runebook()
    if not rb:
        _err("No runebook selected."); return False

    btn = _btn_for_rune(index)
    if btn is None:
        _err("Runebook mapping missing for rune %d" % index); return False

    def _click_rune():
        Items.UseItem(rb)
        if not Gumps.WaitForGump(0, 3000):
            return False
        g = Gumps.CurrentGump()
        if not g: return False
        Misc.Pause(_randint(90, 160))
        Gumps.SendAction(g, btn)
        Misc.Pause(_randint(130, 210))
        return True

    attempts = 0
    start_xyz = _player_xyz()
    Journal.Clear()
    while attempts < 2:
        if not _click_rune():
            attempts += 1
            continue

        if _recall_clicked_moved(start_xyz, RECALL_VERIFY_TIMEOUT_MS + _randint(400, 900)):
            _last_recall_ms = _now_ms()
            _jitter(*LANDING_SETTLE_MS)
            return True

        _dbg("Recall didn’t move → nudge + retry")
        _nudge_step()
        attempts += 1
        Journal.Clear()

    _err("Recall clicked, but position didn’t change; treating as failed.")
    return False

def weight_soft_cap():
    if WEIGHT_SOFT_CAP>0: return WEIGHT_SOFT_CAP
    try: return max(0, Player.MaxWeight-5)
    except: return 375

def overweight():
    try: return Player.Weight >= weight_soft_cap()
    except: return False

def select_tool():
    for layer in ("RightHand","LeftHand"):
        t = Player.GetItemOnLayer(layer)
        if t and t.ItemID in MINING_TOOLS: return t
    for iid in MINING_TOOLS:
        t = Items.FindByID(iid, -1, Player.Backpack.Serial)
        if t: return t
    return None

def ring_positions(cx, cy, radius):
    pts = []
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if abs(dx) + abs(dy) <= radius:
                pts.append((cx + dx, cy + dy))
    return _shuffle_list(pts)

def _sound_hit():
    if not USE_SOUND_HINT: return False
    if not Journal.Search("Playing Sound:"): return False
    for token in MINING_SOUND_CODES:
        if Journal.Search(token): return True
    return False

def mine_once_feet():
    tool = select_tool()
    if not tool:
        _err("No mining tool found.")
        return False

    Journal.Clear()
    Items.UseItem(tool)
    if not Target.WaitForTarget(1500, False):
        return False

    Target.TargetExecute(Player.Serial)  # feet
    Misc.Pause(900)
    return True

def mine_tile_here(_ignored_tile_attempts_param):
    """
    Mine current tile for a randomized number of swings (STATIONARY_SWINGS_RANGE),
    returning (hits, stopped_early).
    """
    target_swings = _randint(STATIONARY_SWINGS_RANGE[0], STATIONARY_SWINGS_RANGE[1])
    hits = 0
    nohit = 0

    for _ in range(target_swings):
        if overweight():
            return hits, True

        if not mine_once_feet():
            Misc.Pause(250)
            continue

        got_hit = False
        if Journal.Search("You put|You loosen|ore into your backpack"):
            got_hit = True
        elif _sound_hit():
            got_hit = True
        elif Journal.Search(EMPTY_VEIN_PATTERNS):
            Journal.Clear()
            break

        Journal.Clear()

        if got_hit:
            hits += 1
            nohit = 0
            _jitter(250, 400)
        else:
            nohit += 1
            _jitter(220, 320)
            if nohit >= NOHIT_MAX_SWINGS:
                break

    return hits, False

def mine_area(radius):
    """Walk a randomized diamond area around landing and mine each tile briefly (but stationary per-tile)."""
    px,py,pz = _player_xyz()
    tiles = ring_positions(px, py, radius)
    total_hits = 0
    for x,y in tiles:
        if overweight(): break
        if (x,y) != (Player.Position.X, Player.Position.Y):
            _pathfind_to(x,y,pz); Misc.Pause(300)
        hits, stopped = mine_tile_here(None)
        total_hits += hits
        if stopped: break
    return total_hits > 0

def is_blackout(r): return _now_ms() < _blackouts.get(r, 0)

def set_blackout(r, minutes):
    _blackouts[r] = _now_ms() + int(minutes*60*1000)
    _say(f"Blackout rune {r} for {minutes} min")

def pick_next_rune():
    pool = [r for r in MINE_RUNE_INDICES if not is_blackout(r)]
    if not pool: return None
    return pool[_rng.Next(len(pool))]

def unload_resources():
    """
    Smelt first, then re-check weight; if still heavy (>= POST_SMELT_BANK_WEIGHT), recall to bank and dump.
    Also try house shelf deposit (ingots) by walking to (2061,1184) and clicking button 121.
    """
    did = False

    if USE_FIRE_BEETLE_SMELT:
        did = smelt_all_ore_on_beetle() or did

    if ENABLE_DEPOSIT_TO_HOME:
        try:
            if deposit_ingots_to_house_shelf():
                did = True
        except: pass

    try:
        if Player.Weight >= POST_SMELT_BANK_WEIGHT and ENABLE_DEPOSIT_TO_BANK:
            if recall_to_rune(BANK_RUNE_INDEX):
                if deposit_to_bank():
                    did = True
    except: pass

    return did

def mining_loop():
    global _last_mine_rune
    _say("Starting FrogAutoMiner (foot travel, beetle-smelt, bank @400, house-shelf enabled).")
    rb = get_runebook(force_prompt=True)
    if not rb:
        _err("No runebook selected; stopping."); return
    if USE_FIRE_BEETLE_SMELT: ensure_beetle_mobile()

    while Player.Connected:
        try:
            if Player.Weight >= PREEMPT_BANK_WEIGHT:
                _say("Heavy → unload.")
                if unload_resources() and _last_mine_rune:
                    recall_to_rune(_last_mine_rune)
                continue
        except: pass

        r = pick_next_rune()
        if r is None:
            _say("All runes blacked out; resting."); _jitter(3000, 4500); continue

        if not recall_to_rune(r):
            _jitter(800, 1200); continue

        _last_mine_rune = r
        found = mine_area(AREA_RADIUS_TILES)

        if not found:
            set_blackout(r, BLACKOUT_MINUTES)

        try:
            if Player.Weight >= PREEMPT_BANK_WEIGHT:
                _say("Heavy → unload.")
                unload_resources()
                if _last_mine_rune:
                    recall_to_rune(_last_mine_rune)
        except: pass

        _jitter(350, 900)

if __name__ == "__main__":
    try:
        mining_loop()
    except Exception as e:
        _err("Script error - check Python log.")
        _err(str(e))
