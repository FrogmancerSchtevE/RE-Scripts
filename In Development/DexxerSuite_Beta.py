# ==================================
# ==  Dexxer Suite (Frog Edition) ==
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
import Misc, Player, Items, Mobiles, Timer, Target, Gumps
from System import Int32
from System.Collections.Generic import List

# ====================================================================
# CONFIGS (DO NOT EDIT)
# ====================================================================
VERSION = "v0.4.2"
REFRESH_MS = 200
GUMP_ID = 884321

ID_BANDAGE      = 0x0E21
ID_POT_CURE     = 0x0F07
ID_POT_HEAL     = 0x0F0C
ID_POT_REFRESH  = 0x0F0B
ID_POT_AGILITY  = 0x0F08
ID_POT_STRENGTH = 0x0F09
ID_ORANGE_PETAL = 0x1021
ID_PURPLE_PETAL = 0x1021

BANDAGE_HP_THRESHOLD = 75
HEAL_HP_THRESHOLD = 45
REFRESH_STAM_GAP = 20

USE_BTN_NORMAL = 4011
USE_BTN_PRESSED = 4012
AUTO_ON_GEM  = 2361
AUTO_OFF_GEM = 2360
TOGGLE_MODE_BTN = 9004

# Button IDs
BTN_BANDAGE   = ID_BANDAGE
BTN_CUREPOT   = ID_POT_CURE
BTN_HEALPOT   = ID_POT_HEAL
BTN_STRPOT    = ID_POT_STRENGTH
BTN_REFRESH   = ID_POT_REFRESH
BTN_AGIPOT    = ID_POT_AGILITY
BTN_ORANGE    = ID_ORANGE_PETAL
BTN_PURPLE    = ID_PURPLE_PETAL

FROG_ICON = 0x2130
FROG_HUE  = 0x09E8

BG_GUMP_ID = 30546

# ====================================================================
# GLOBALS
# ====================================================================
_running = True
_compact_mode = False

_auto_bandage = False
_auto_heal = False
_auto_cure = False
_auto_refresh = False
_auto_str = False
_auto_agi = False
_auto_orange = False
_auto_purple = False

# ====================================================================
# HELPERS
# ====================================================================
def ms_pause(ms): Misc.Pause(int(ms))

def reset_timer(name, cd_ms): Timer.Create(name, int(cd_ms))
def timer_ready(name):
    try: return Timer.Check(name)
    except: return True

def find_in_pack(item_id, hue=-1):
    return Items.FindByID(int(item_id), int(hue), Player.Backpack.Serial, True, False)

def use_item(item_id):
    itm = find_in_pack(item_id)
    if itm:
        Items.UseItem(itm)
        return True
    return False

def short_name(name, maxlen=6):
    if not name: return "???"
    return name if len(name) <= maxlen else name[:maxlen]

def hp_color(percent):
    if percent >= 70: return 0x44
    elif percent >= 40: return 0x21
    else: return 0x25

def get_hostiles_sorted(limit=5):
    """Return hostile mobiles sorted by distance, with current attack target first."""
    myX, myY = Player.Position.X, Player.Position.Y
    flt = Mobiles.Filter()
    flt.Enabled = True
    flt.RangeMax = 30
    for n in [3, 4, 5, 6]:
        flt.Notorieties.Add(Int32(n))
    mobs = Mobiles.ApplyFilter(flt)

    results = []
    for m in mobs:
        try:
            d = int(((m.Position.X - myX) ** 2 + (m.Position.Y - myY) ** 2) ** 0.5)
            results.append((m, d))
        except:
            continue

    results.sort(key=lambda r: r[1])
    results = results[:limit]

    cur_target = Target.GetLastAttack()
    if cur_target and cur_target > 0:
        for i, (m, d) in enumerate(results):
            if m.Serial == cur_target:
                results.insert(0, results.pop(i))
                break

    return results    
    
_last_targets = []

def targets_changed():
    """Return True if the hostile target list changed since last check."""
    global _last_targets
    mobs = get_hostiles_sorted(5)
    names = [(m.Serial, m.Hits, m.HitsMax) for m, d in mobs]  # track serial + HP snapshot
    if names != _last_targets:
        _last_targets = names
        return True
    return False    

# ====================================================================
# MODULE: WEAPON SWAPPER
# ====================================================================   

_main_weapon = None
_main_shield = None
_secondary_weapon = None
_secondary_shield = None

def equip_main():
    global _main_weapon, _main_shield

    if not _main_weapon:
        serial = Target.PromptTarget("Select MAIN weapon")
        if serial:
            _main_weapon = Items.FindBySerial(serial)
            Player.HeadMessage(68, "Main weapon saved")
        shield_serial = Target.PromptTarget("Select MAIN shield (ESC to skip)")
        if shield_serial:
            _main_shield = Items.FindBySerial(shield_serial)
            Player.HeadMessage(68, "Main shield saved")
        return

    desired_weapon = _main_weapon.Serial if _main_weapon else None
    desired_shield = _main_shield.Serial if _main_shield else None

    right = Player.GetItemOnLayer("RightHand")
    left  = Player.GetItemOnLayer("LeftHand")

    if right and desired_weapon and right.Serial == desired_weapon:
        Items.UseItem(_main_weapon)
        Player.HeadMessage(68, "Main equipped - using weapon")
        if desired_shield and (not left or left.Serial != desired_shield):
            Items.UseItem(_main_shield)
        return

    clear_hands(preserve_left_serial=desired_shield)
    Misc.Pause(400)

    if _main_weapon:
        Items.UseItem(_main_weapon)
        Player.HeadMessage(68, "Swapping to Main")
    else:
        Player.HeadMessage(33, "No main weapon set")

    if desired_shield:
        left = Player.GetItemOnLayer("LeftHand")
        if not left or left.Serial != desired_shield:
            Items.UseItem(_main_shield)
            
    save_weapons()  

def equip_secondary():
    global _secondary_weapon, _secondary_shield

    if not _secondary_weapon:
        serial = Target.PromptTarget("Select SECONDARY weapon")
        if serial:
            _secondary_weapon = Items.FindBySerial(serial)
            Player.HeadMessage(68, "Secondary weapon saved")
        shield_serial = Target.PromptTarget("Select SECONDARY shield (ESC to skip)")
        if shield_serial:
            _secondary_shield = Items.FindBySerial(shield_serial)
            Player.HeadMessage(68, "Secondary shield saved")
        return

    desired_weapon = _secondary_weapon.Serial if _secondary_weapon else None
    desired_shield = _secondary_shield.Serial if _secondary_shield else None

    right = Player.GetItemOnLayer("RightHand")
    left  = Player.GetItemOnLayer("LeftHand")

    if right and desired_weapon and right.Serial == desired_weapon:
        Items.UseItem(_secondary_weapon)
        Player.HeadMessage(68, "Secondary equipped - using weapon")
        if desired_shield and (not left or left.Serial != desired_shield):
            Items.UseItem(_secondary_shield)
        return

    clear_hands(preserve_left_serial=desired_shield)
    Misc.Pause(400)

    if _secondary_weapon:
        Items.UseItem(_secondary_weapon)
        Player.HeadMessage(68, "Swapping to Secondary")
    else:
        Player.HeadMessage(33, "No secondary weapon set")

    if desired_shield:
        left = Player.GetItemOnLayer("LeftHand")
        if not left or left.Serial != desired_shield:
            Items.UseItem(_secondary_shield)
    save_weapons()           
        
def disarm():
    clear_hands()
    Player.HeadMessage(68, "Clearing hands")
    
def use_shield():
    left = Player.GetItemOnLayer("LeftHand")
    if left:
        Items.UseItem(left)
        Player.HeadMessage(68, "Using Shield")
    else:
        Player.HeadMessage(33, "No shield equipped")
    
def clear_hands(preserve_left_serial=None):
    r = Player.GetItemOnLayer("RightHand")
    if r:
        Items.Move(r, Player.Backpack.Serial, 0)
        Misc.Pause(400)

    l = Player.GetItemOnLayer("LeftHand")
    keep_serial = None
    try:
        keep_serial = int(preserve_left_serial.Serial) if preserve_left_serial else None
    except:
        try:
            keep_serial = int(preserve_left_serial) if preserve_left_serial is not None else None
        except:
            keep_serial = None

    if l and (keep_serial is None or l.Serial != keep_serial):
        Items.Move(l, Player.Backpack.Serial, 0)
        Misc.Pause(400)
  
# ====================================================================
# MODULE: PERSISTANCE
# ====================================================================       

def save_weapons():
    if _main_weapon:   Misc.SetSharedValue("dexxer_main_weapon", _main_weapon.Serial)
    else:              Misc.RemoveSharedValue("dexxer_main_weapon")
    if _main_shield:   Misc.SetSharedValue("dexxer_main_shield", _main_shield.Serial)
    else:              Misc.RemoveSharedValue("dexxer_main_shield")
    if _secondary_weapon: Misc.SetSharedValue("dexxer_secondary_weapon", _secondary_weapon.Serial)
    else:                 Misc.RemoveSharedValue("dexxer_secondary_weapon")
    if _secondary_shield: Misc.SetSharedValue("dexxer_secondary_shield", _secondary_shield.Serial)
    else:                 Misc.RemoveSharedValue("dexxer_secondary_shield")

def load_weapons():
    global _main_weapon, _main_shield, _secondary_weapon, _secondary_shield

    try:
        main = Misc.ReadSharedValue("dexxer_main_weapon")
        if main: _main_weapon = Items.FindBySerial(int(main))
    except: pass

    try:
        sh = Misc.ReadSharedValue("dexxer_main_shield")
        if sh: _main_shield = Items.FindBySerial(int(sh))
    except: pass

    try:
        sec = Misc.ReadSharedValue("dexxer_secondary_weapon")
        if sec: _secondary_weapon = Items.FindBySerial(int(sec))
    except: pass

    try:
        secsh = Misc.ReadSharedValue("dexxer_secondary_shield")
        if secsh: _secondary_shield = Items.FindBySerial(int(secsh))
    except: pass

def reset_weapons():
    global _main_weapon, _main_shield, _secondary_weapon, _secondary_shield
    _main_weapon = _main_shield = _secondary_weapon = _secondary_shield = None
    for key in ["dexxer_main_weapon", "dexxer_main_shield", "dexxer_secondary_weapon", "dexxer_secondary_shield"]:
        Misc.RemoveSharedValue(key)
    Player.HeadMessage(33, f"Reset: {_main_weapon}, {_main_shield}, {_secondary_weapon}, {_secondary_shield}")
    
load_weapons()   
if _main_weapon: Player.HeadMessage(68, "Loaded Main weapon")
if _main_shield: Player.HeadMessage(68, "Loaded Main shield")
if _secondary_weapon: Player.HeadMessage(68, "Loaded Secondary weapon")
if _secondary_shield: Player.HeadMessage(68, "Loaded Secondary shield")

# ====================================================================
# MODULE: MANUAL ACTIONS
# ====================================================================
def manual_bandage_self():
    itm = find_in_pack(ID_BANDAGE)
    if itm:
        Items.UseItem(itm)
        if Target.WaitForTarget(500):
            Target.Self()
        Misc.SendMessage("Manual bandage on self", 68)
    else:
        Misc.SendMessage("No bandages found!", 33)

def manual_healpot():
    if use_item(ID_POT_HEAL):
        Misc.SendMessage("Drank heal potion", 68)
    else:
        Misc.SendMessage("No heal potions found!", 33)

def manual_curepot():
    if use_item(ID_POT_CURE):
        Misc.SendMessage("Drank cure potion", 68)
    else:
        Misc.SendMessage("No cure potions found!", 33)

def manual_refreshpot():
    if use_item(ID_POT_REFRESH):
        Misc.SendMessage("Drank refresh potion", 68)
    else:
        Misc.SendMessage("No refresh potions found!", 33)

def manual_strpot():
    if use_item(ID_POT_STRENGTH):
        Misc.SendMessage("Drank strength potion", 68)
    else:
        Misc.SendMessage("No strength potions found!", 33)

def manual_agipot():
    if use_item(ID_POT_AGILITY):
        Misc.SendMessage("Drank agility potion", 68)
    else:
        Misc.SendMessage("No agility potions found!", 33)

def manual_orange_petals():
    if use_item(ID_ORANGE_PETAL):
        Misc.SendMessage("Ate orange petals", 68)
    else:
        Misc.SendMessage("No orange petals found!", 33)

def manual_purple_petals():
    if use_item(ID_PURPLE_PETAL):
        Misc.SendMessage("Ate purple petals", 68)
    else:
        Misc.SendMessage("No purple petals found!", 33)    
      
# ====================================================================
# MODULE: AUTO LOGIC
# ====================================================================
def step_bandage():
    if not _auto_bandage: return
    if Player.Hits < BANDAGE_HP_THRESHOLD and timer_ready("bandageCD"):
        itm = find_in_pack(ID_BANDAGE)
        if itm:
            Items.UseItem(itm)
            if Target.WaitForTarget(500): Target.Self()
            reset_timer("bandageCD", 7000)

def step_healpot():
    if not _auto_heal: return
    if Player.Hits <= HEAL_HP_THRESHOLD and timer_ready("healPotCD"):
        if use_item(ID_POT_HEAL):
            reset_timer("healPotCD", 10000)

def step_curepot():
    if _auto_cure and Player.Poisoned:
        use_item(ID_POT_CURE)

def step_refreshpot():
    if not _auto_refresh: return
    if (Player.StamMax - Player.Stam) > REFRESH_STAM_GAP:
        if timer_ready("refreshCD") and use_item(ID_POT_REFRESH):
            reset_timer("refreshCD", 5000)

def step_strpot():
    if not _auto_str: return
    if not Player.BuffsExist("Strength") and timer_ready("strPotCD"):
        if use_item(ID_POT_STRENGTH):
            reset_timer("strPotCD", 120000)  

def step_agipot():
    if not _auto_agi: return
    if not Player.BuffsExist("Agility") and timer_ready("agiPotCD"):
        if use_item(ID_POT_AGILITY):
            reset_timer("agiPotCD", 120000)  

def step_petals():
    if not (_auto_orange or _auto_purple): return

    if _auto_orange:
        if not Player.BuffsExist("Orange Petals") and timer_ready("orangePetalCD"):
            if use_item(ID_ORANGE_PETAL):
                reset_timer("orangePetalCD", 180000)  

    if _auto_purple:
        if not Player.BuffsExist("Purple Petals") and timer_ready("purplePetalCD"):
            if use_item(ID_PURPLE_PETAL):
                reset_timer("purplePetalCD", 180000)       

# ====================================================================
# GUI / GUMP
# ====================================================================
def build_gui():
    global _dirty_ui
    Gumps.CloseGump(GUMP_ID)
    gd = Gumps.CreateGump(True)
    Gumps.AddPage(gd, 0)

    row_height = 30 if not _compact_mode else 20
    col_spacing = 160 if not _compact_mode else 110
    x, y = 10, 40

    est_rows = 4 + (0 if _compact_mode else 1) + 5   
    total_w = col_spacing*2 + (80 if not _compact_mode else 40)
    total_h = (row_height * est_rows) + 80

    Gumps.AddBackground(gd, 0, 0, total_w, total_h, BG_GUMP_ID)
    Gumps.AddAlphaRegion(gd, 0, 0, total_w, total_h)

    Gumps.AddItem(gd, 5, 5, FROG_ICON, FROG_HUE)
    Gumps.AddButton(gd, 5, 5, FROG_ICON, FROG_ICON, FROG_BTN_ID, 1, 0)
    Gumps.AddLabel(gd, 75, 10, 1152, "Dexxer Utility Suite " + VERSION)

    def add_row(ix, iy, label, art_id, use_id, auto_flag, hue=0):
        Gumps.AddItem(gd, ix, iy, art_id, hue)
        if not _compact_mode:
            Gumps.AddLabel(gd, ix+30, iy, 1152, label)
            use_x, auto_x = ix+100, ix+140
        else:
            use_x, auto_x = ix+35, ix+65
        Gumps.AddButton(gd, use_x, iy, USE_BTN_NORMAL, USE_BTN_PRESSED, use_id, 1, 0)
        gem = AUTO_ON_GEM if auto_flag else AUTO_OFF_GEM
        Gumps.AddButton(gd, auto_x, iy, gem, gem, use_id+1000, 1, 0)

    add_row(x, y, "Bandage", ID_BANDAGE, ID_BANDAGE, _auto_bandage); 
    add_row(x+col_spacing, y, "Cure", ID_POT_CURE, ID_POT_CURE, _auto_cure); 
    y += row_height

    add_row(x, y, "Heal", ID_POT_HEAL, ID_POT_HEAL, _auto_heal)
    add_row(x+col_spacing, y, "Strength", ID_POT_STRENGTH, ID_POT_STRENGTH, _auto_str); 
    y += row_height

    add_row(x, y, "Refresh", ID_POT_REFRESH, ID_POT_REFRESH, _auto_refresh)
    add_row(x+col_spacing, y, "Agility", ID_POT_AGILITY, ID_POT_AGILITY, _auto_agi); 
    y += row_height

    add_row(x, y, "Orange", ID_ORANGE_PETAL, ID_ORANGE_PETAL, _auto_orange, 43)
    add_row(x+col_spacing, y, "Purple", ID_PURPLE_PETAL, ID_PURPLE_PETAL, _auto_purple, 16)
    y += row_height  

    if _compact_mode:
        swap_x = x + (col_spacing // 2) - 30
        y += 5  
        Gumps.AddButton(gd, swap_x, y, 4035, 4035, 60004, 1, 0) 
        Gumps.AddButton(gd, swap_x+35, y, USE_BTN_NORMAL, USE_BTN_PRESSED, 60001, 1, 0) 
        Gumps.AddButton(gd, swap_x+70, y, USE_BTN_NORMAL, USE_BTN_PRESSED, 60002, 1, 0)  
        Gumps.AddButton(gd, swap_x+105, y, USE_BTN_NORMAL, USE_BTN_PRESSED, 60003, 1, 0) 
        Gumps.AddButton(gd, swap_x+140, y, 2381, 2381, 60005, 1, 0)  
        y += row_height

    else:
        Gumps.AddLabel(gd, x, y, 1152, "Weapon")
        swap_x = x + col_spacing//2
        Gumps.AddButton(gd, swap_x, y, 4035, 4035, 60004, 1, 0)  
        Gumps.AddButton(gd, swap_x+35, y, USE_BTN_NORMAL, USE_BTN_PRESSED, 60001, 1, 0)  
        Gumps.AddButton(gd, swap_x+70, y, USE_BTN_NORMAL, USE_BTN_PRESSED, 60002, 1, 0)  
        Gumps.AddButton(gd, swap_x+105, y, USE_BTN_NORMAL, USE_BTN_PRESSED, 60003, 1, 0) 
        Gumps.AddButton(gd, swap_x+140, y, 2381, 2381, 60005, 1, 0)  
        y += row_height


    Gumps.AddLabel(gd, x, y, 1152, "Targets:")
    y += 20
    for m, dist in get_hostiles_sorted(5):
        try:
            hp_pct = int((m.Hits * 100) / m.HitsMax) if m.HitsMax > 0 else 0
            c = hp_color(hp_pct)
            row_hue = 43 if m.Serial == Target.GetLastAttack() else 1152

            Gumps.AddButton(gd, x, y, 1209, 1209, int(m.Serial), 1, 0)

            if _compact_mode:
                Gumps.AddLabel(gd, x+25, y, row_hue, short_name(m.Name))
                Gumps.AddLabel(gd, x+85, y, c, f"{hp_pct}%")
                Gumps.AddLabel(gd, x+130, y, 1152, f"{dist}")
            else:
                Gumps.AddLabel(gd, x+25, y, row_hue, m.Name)
                Gumps.AddLabel(gd, x+185, y, c, f"{hp_pct}%")
                Gumps.AddLabel(gd, x+240, y, 1152, f"{dist}")
            y += 20
        except:
            continue

    Gumps.AddButton(
        gd,
        total_w - 30,   
        total_h - 30,   
        TOGGLE_MODE_BTN, TOGGLE_MODE_BTN,
        90001, 1, 0
)

    Gumps.SendGump(GUMP_ID, Player.Serial, 50, 50, gd.gumpDefinition, gd.gumpStrings)
    _dirty_ui = False

# ====================================================================
# BUTTON HANDLER
# ====================================================================
_drag_pause = 0
FROG_BTN_ID = 91000

def handle_button(buttonid):
    global _auto_bandage, _auto_heal, _auto_cure, _auto_refresh
    global _auto_str, _auto_agi, _auto_orange, _auto_purple
    global _compact_mode, _drag_pause

    if buttonid == BTN_BANDAGE:
        manual_bandage_self()
    elif buttonid == BTN_HEALPOT:
        manual_healpot()
    elif buttonid == BTN_CUREPOT:
        manual_curepot()
    elif buttonid == BTN_REFRESH:
        manual_refreshpot()
    elif buttonid == BTN_STRPOT:
        manual_strpot()
    elif buttonid == BTN_AGIPOT:
        manual_agipot()
    elif buttonid == BTN_ORANGE:
        manual_orange_petals()
    elif buttonid == BTN_PURPLE:
        manual_purple_petals()

    elif buttonid == ID_BANDAGE+1000: _auto_bandage = not _auto_bandage
    elif buttonid == ID_POT_HEAL+1000: _auto_heal = not _auto_heal
    elif buttonid == ID_POT_CURE+1000: _auto_cure = not _auto_cure
    elif buttonid == ID_POT_REFRESH+1000: _auto_refresh = not _auto_refresh
    elif buttonid == ID_POT_STRENGTH+1000: _auto_str = not _auto_str
    elif buttonid == ID_POT_AGILITY+1000: _auto_agi = not _auto_agi
    elif buttonid == ID_ORANGE_PETAL+1000: _auto_orange = not _auto_orange
    elif buttonid == ID_PURPLE_PETAL+1000: _auto_purple = not _auto_purple

    elif buttonid == 60001:  
        equip_main()
    elif buttonid == 60002:  
        equip_secondary()
    elif buttonid == 60003:  
        disarm()
    elif buttonid == 60004:  
        reset_weapons()
    elif buttonid == 60005: 
        use_shield()

    elif buttonid == 90001:  
        _compact_mode = not _compact_mode
    elif buttonid == FROG_BTN_ID:  
        _drag_pause = Misc.Timer()

    else:
        try:
            mob = Mobiles.FindBySerial(buttonid)
            if mob:
                Player.Attack(mob)

                notoriety_colors = {
                    1: 99,   
                    2: 68,   
                    3: 902,  
                    4: 43,   
                    5: 33,   
                    6: 83    
                }
                hue = notoriety_colors.get(mob.Notoriety, 68)

                if mob.Name:
                    Player.HeadMessage(hue, f"Attacking {mob.Name}")
                else:
                    Player.HeadMessage(hue, "Attacking target")
            else:
                Player.Attack(buttonid)
        except:
            pass




# ====================================================================
# MAIN LOOP
# ====================================================================
build_gui()

while _running and Player.Connected:
    step_bandage(); step_healpot(); step_curepot()
    step_refreshpot(); step_strpot(); step_agipot(); step_petals()

    gd = Gumps.GetGumpData(GUMP_ID)

    if gd is None:
        build_gui()
    elif gd.buttonid:
        handle_button(gd.buttonid)
        gd.buttonid = 0
        build_gui()  

    if Timer.Check("uiUpdate"):
        if targets_changed():
            build_gui()
        Timer.Create("uiUpdate", 3000)

    ms_pause(200)


