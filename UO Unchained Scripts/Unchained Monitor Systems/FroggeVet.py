# ==================================
# === Vet Assistant (Frog Edition) ==
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

import time

# Configs/Constants
BANDAGE_ITEMID = 0x0E21
BANDAGE_HUE = -1
HEAL_BELOW_PCT = 0.80
PRIORITIZE_POISON = True
MAX_TARGET_RANGE = 2
BANDAGE_WAIT_MS = 1600
BANDAGE_DISPLAY_SECONDS = 4
BANDAGE_DISPLAY_MS = BANDAGE_DISPLAY_SECONDS * 1000
BEGIN_DETECT_TIMEOUT_MS = 2500
CURSOR_HOLD_MS = 2500
LOOP_IDLE_MS = 120
MSG_COLOR = 68
WARN_COLOR = 53
ERR_COLOR = 33
OK_COLOR = 76
VETKIT_ITEMID = 0x6B93
VETKIT_HUE = -1
VETKIT_HP_THRESHOLD = 0.60
OUT_OF_BANDAGE_ALERT_MS = 10000

# GUI Build
GUMP_ID = 0x5EA1BEEF
GUI_ENABLED = True
REFRESH_MS = 180
RESET_BUTTON_ID = 9999
DEFAULT_GUMP_POS = (650, 650)
ROW_H = 20
LEFT_PAD = 8
GUMP_W = 330
BG_ART = 9270
HUE_TITLE = 0x0035
HUE_TXT = 0x0481
HUE_GOOD = 0x0044
HUE_WARN = 0x0021
HUE_BAD = 0x0025
SEG_ART = 5210
HUE_EMPTY = 0
HUE_BAND_FILLED = 1154
HUE_PET_FILLED = 88
PET_SEGMENTS = 10
PET_SEG_W = 16
BAND_SEGMENTS = 4
BAND_SEG_W = 20
COL_LABEL_X = LEFT_PAD
COL_VAL_X = LEFT_PAD + 85
COL_BAR_X = LEFT_PAD + 140
TOGGLE_PAUSE_BUTTON_ID = 9998
PAUSED = False

# Save State
PET_NAMES = []
last_bandage_alert = 0

# Utilities
def now_ms(): return int(time.time() * 1000)
def msg(text, color=MSG_COLOR): Misc.SendMessage(text, color)
def safe_getattr(obj, name, default=None):
    try: return getattr(obj, name)
    except: return default

# Bandage Timer
HUD_BAND_START_KEY = "vet_hud_band_start"
HUD_BAND_LEN_KEY = "vet_hud_band_len"
def set_bandage_timer(start_ms, length_ms):
    Misc.SetSharedValue(HUD_BAND_START_KEY, int(start_ms))
    Misc.SetSharedValue(HUD_BAND_LEN_KEY, int(length_ms))
def clear_bandage_timer():
    Misc.SetSharedValue(HUD_BAND_START_KEY, None)
    Misc.SetSharedValue(HUD_BAND_LEN_KEY, None)
def bandage_running():
    start = Misc.ReadSharedValue(HUD_BAND_START_KEY) if Misc.CheckSharedValue(HUD_BAND_START_KEY) else 0
    length = Misc.ReadSharedValue(HUD_BAND_LEN_KEY) if Misc.CheckSharedValue(HUD_BAND_LEN_KEY) else 0
    return start and length and (now_ms() < start + length)
def bandage_time_left_ms():
    start = Misc.ReadSharedValue(HUD_BAND_START_KEY) if Misc.CheckSharedValue(HUD_BAND_START_KEY) else 0
    length = Misc.ReadSharedValue(HUD_BAND_LEN_KEY) if Misc.CheckSharedValue(HUD_BAND_LEN_KEY) else 0
    return max(0, (start + length) - now_ms()) if start and length else 0
def healing_in_progress(): return bandage_running()
def start_heal_timer(): set_bandage_timer(now_ms(), BANDAGE_DISPLAY_MS)

# Inventory Helper
def get_item_in_subbags(itemid, hue=-1):
    itm = Items.FindByID(itemid, hue, Player.Backpack.Serial)
    if itm: return itm
    for cont in Player.Backpack.Contains or []:
        itm = Items.FindByID(itemid, hue, cont.Serial)
        if itm: return itm
    return None
def count_in_subbags(itemid, hue=-1):
    try: return Items.BackpackCount(itemid, hue)
    except: return 0
def get_bandage(): return get_item_in_subbags(BANDAGE_ITEMID, BANDAGE_HUE)

# Pet Helpers
def valid_pet(m): return bool(m and not safe_getattr(m,"IsGhost",True) and safe_getattr(m,"HitsMax",0)>0)
def hp_pct(m):
    hm = float(safe_getattr(m,"HitsMax",0) or 0)
    return (float(safe_getattr(m,"Hits",0) or 0)/hm) if hm>0 else 0.0
def find_pet_by_name(name, max_range=18):
    if not name: return None
    f = Mobiles.Filter(); f.Enabled=True; f.RangeMax=max_range; f.Name=name
    try: f.Notorieties.Add(2)
    except: pass
    cands = Mobiles.ApplyFilter(f) or []
    return cands[0] if cands else None
def prompt_pet_names():
    global PET_NAMES
    PET_NAMES = []
    for i in range(1,6):
        msg(f"Target Pet {i} (ESC to skip)")
        s = Target.PromptTarget(f"Pet {i}")
        if not s: continue
        m = Mobiles.FindBySerial(s)
        if m and valid_pet(m): PET_NAMES.append(m.Name)
    msg(f"Tracking {len(PET_NAMES)} pets by name.", OK_COLOR)

# Healing
def use_vetkit_on(p):
    if healing_in_progress(): return False
    kit=get_item_in_subbags(VETKIT_ITEMID,VETKIT_HUE)
    if not (kit and valid_pet(p)): return False
    Journal.Clear(); Target.Cancel(); Items.UseItem(kit)
    if Target.WaitForTarget(1000): 
        Target.TargetExecute(p.Serial)
        start_heal_timer()
        Misc.Pause(400)
        return True
    return False
def bandage_target_by_name(name):
    global last_bandage_alert
    if not name or healing_in_progress(): return False
    m = find_pet_by_name(name, max_range=MAX_TARGET_RANGE*6)
    if not valid_pet(m): return False
    bandage = get_bandage()
    if not bandage:
        if now_ms() - last_bandage_alert > OUT_OF_BANDAGE_ALERT_MS:
            msg("Out of bandages!", ERR_COLOR)
            last_bandage_alert = now_ms()
        return False
    Journal.Clear(); Target.Cancel(); Items.UseItem(bandage)
    if not Target.WaitForTarget(BANDAGE_WAIT_MS): return False
    m2 = find_pet_by_name(name, max_range=MAX_TARGET_RANGE*6)
    if not valid_pet(m2): Target.Cancel(); return False
    Target.TargetExecute(m2.Serial)
    start_heal_timer()
    Misc.Pause(120)
    return True
def pick_target():
    fresh=[]
    for n in PET_NAMES:
        m=find_pet_by_name(n, max_range=30)
        if valid_pet(m):
            try: Mobiles.GetStatus(m)
            except: pass
            fresh.append(m)
    if PRIORITIZE_POISON:
        pois=[m for m in fresh if safe_getattr(m,"Poisoned",False)]
        if pois: return min(pois,key=hp_pct)
    cand=[m for m in fresh if hp_pct(m)<HEAL_BELOW_PCT]
    return min(cand,key=hp_pct) if cand else None
def toggle_pause():
    global PAUSED
    PAUSED = not PAUSED
    msg("Vet Assistant paused." if PAUSED else "Vet Assistant resumed.", WARN_COLOR if PAUSED else OK_COLOR)    

# GUI
def _health_hue(frac): return HUE_GOOD if frac>=.75 else HUE_WARN if frac>=.40 else HUE_BAD
def _draw_segments(gd,x,y,segments,seg_w,filled,hue_empty,hue_fill):
    for i in range(segments): Gumps.AddImage(gd,x+i*seg_w,y,SEG_ART,hue_empty)
    for i in range(min(segments,filled)): Gumps.AddImage(gd,x+i*seg_w,y,SEG_ART,hue_fill)
def render_gui():
    band_left_ms = bandage_time_left_ms()
    total_ms = Misc.ReadSharedValue(HUD_BAND_LEN_KEY) if Misc.CheckSharedValue(HUD_BAND_LEN_KEY) else BANDAGE_DISPLAY_MS
    bcount = count_in_subbags(BANDAGE_ITEMID, BANDAGE_HUE)
    Gumps.CloseGump(GUMP_ID)
    rows = 3 + len(PET_NAMES)*2
    gump_h = max(220, 10+rows*ROW_H)
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd,0)
    Gumps.AddBackground(gd,0,0,GUMP_W,gump_h,BG_ART)
    y=6
    Gumps.AddLabel(gd,COL_LABEL_X,y,HUE_TITLE,"Vet Assistant")
    Gumps.AddButton(gd,GUMP_W-120,6,4017,4018,TOGGLE_PAUSE_BUTTON_ID,1,0)
    Gumps.AddLabel(gd,GUMP_W-95,8,HUE_TXT,"Resume" if PAUSED else "Pause")
    Gumps.AddButton(gd,GUMP_W-60,6,4017,4018,RESET_BUTTON_ID,1,0)
    Gumps.AddLabel(gd,GUMP_W-35,8,HUE_TXT,"Reset")
    y+=ROW_H
    label="ready" if band_left_ms<=0 else f"{band_left_ms/1000:.1f}s"
    filled=0 if band_left_ms<=0 else int((total_ms-band_left_ms)//1000)
    Gumps.AddLabel(gd,COL_LABEL_X,y,HUE_TXT,"Bandage:")
    Gumps.AddLabel(gd,COL_VAL_X,y,HUE_TXT,label)
    y+=ROW_H-4
    _draw_segments(gd,COL_BAR_X,y,BAND_SEGMENTS,BAND_SEG_W,filled,HUE_EMPTY,HUE_BAND_FILLED)
    y+=ROW_H+2
    Gumps.AddLabel(gd,COL_LABEL_X,y,HUE_TXT,"Bandies:")
    hue = HUE_BAD if bcount == 0 else HUE_TXT
    Gumps.AddLabel(gd,COL_VAL_X,y,hue,str(bcount))
    y+=ROW_H+2
    for i,name in enumerate(PET_NAMES,1):
        m=find_pet_by_name(name)
        if not m:
            Gumps.AddLabel(gd,COL_LABEL_X,y,HUE_TXT,f"Pet {i}:")
            Gumps.AddLabel(gd,COL_VAL_X,y,HUE_BAD,f"{name} [Missing]")
            y+=ROW_H*2
            continue
        frac=hp_pct(m)
        pct=int(frac*100)
        nm=safe_getattr(m,"Name","Pet")+(" [P]" if safe_getattr(m,"Poisoned",False) else "")
        fill=int(round(frac*PET_SEGMENTS))
        Gumps.AddLabel(gd,COL_LABEL_X,y,HUE_TXT,f"Pet {i}:")
        Gumps.AddLabel(gd,COL_VAL_X,y,_health_hue(frac),f"{nm} {pct}%")
        y+=ROW_H-4
        _draw_segments(gd,COL_BAR_X,y,PET_SEGMENTS,PET_SEG_W,fill,HUE_EMPTY,HUE_PET_FILLED)
        y+=ROW_H+2
    Gumps.SendGump(GUMP_ID,Player.Serial,*DEFAULT_GUMP_POS,gd.gumpDefinition,gd.gumpStrings)
    
# Main
def main():
    prompt_pet_names()
    msg(f"Vet online with {len(PET_NAMES)} pets.",OK_COLOR)
    last_gui=0
    while True:
        gd=Gumps.GetGumpData(GUMP_ID)
        if gd:
            if gd.buttonid==RESET_BUTTON_ID:
                prompt_pet_names()
            elif gd.buttonid==TOGGLE_PAUSE_BUTTON_ID:
                toggle_pause()

        # If paused, just refresh GUI and idle
        if PAUSED:
            if GUI_ENABLED and now_ms()-last_gui>=REFRESH_MS:
                render_gui(); last_gui=now_ms()
            Misc.Pause(LOOP_IDLE_MS)
            continue

        # --- Normal healing logic below ---
        pets=[find_pet_by_name(n, max_range=30) for n in PET_NAMES if find_pet_by_name(n, max_range=30)]
        pets=[p for p in pets if valid_pet(p)]
        low_pets=[p for p in pets if hp_pct(p)<VETKIT_HP_THRESHOLD]
        if len(low_pets)>=2 and not healing_in_progress():
            low=min(low_pets,key=hp_pct)
            if use_vetkit_on(low):
                Misc.Pause(LOOP_IDLE_MS)
                continue
        tgt=pick_target()
        if tgt and not healing_in_progress():
            bandage_target_by_name(safe_getattr(tgt,"Name",None))

        if GUI_ENABLED and now_ms()-last_gui>=REFRESH_MS:
            render_gui(); last_gui=now_ms()
        Misc.Pause(LOOP_IDLE_MS)

main()
