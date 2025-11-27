# ==================================
# === Summoner Suite ===
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
try:
    from System import Byte, Int32
except:
    Byte = None
    Int32 = None

import re, time
import Misc, Player, Mobiles, Gumps, Target, Journal, Spells


# ====================================================================
# GLOBAL CONFIGS
# ====================================================================
VERSION            = "1.0"
GUMP_ID            = 0x53A0C0DE
REFRESH_MS         = 300
SCAN_RANGE         = 30
PLAYER_SCAN_RANGE  = 30
ROW_HEIGHT         = 18
GUMP_POS           = (850, 620)

HEAL_THRESHOLD_PCT  = 15
SUPPORT_COOLDOWN_MS = 1800
CURE_FIRST          = True
CHECK_LINE_OF_SIGHT = True
MAX_CAST_RANGE      = 12

BAR_SEG_ART        = 5210
BAR_SEG_W          = 12
BAR_W              = 78
BAR_HUE_BG         = 2999
HUES_BY_LEVEL      = [0x021, 0x026, 0x02B, 0x030, 0x035, 0x03A]

AUTO_TAG_SUMMONS   = True
TAG_PREFIX         = ""
USE_TAG_IN_RENAME  = False
SAFE_TAG_PREFIX    = ""
MAX_NAME_LEN       = 16
GRACE_TICKS        = 6
OUT_OF_RANGE_TICKS = 3

BASE_SUMMON_NAMES = [
    "blood elemental",
    "daemon",
    "a earth elemental",
    "afire elemental",
    "a water elemental",
    "a air elemental",
    "an energy vortex",
    "a blade spirits",
    "a wisp",
    "ashadow wisp",
    "a poison elemental",
    "a shadow elemental"
]
STATUS_MARKERS = ["*grows stronger*","*regens*","(summoned)","(familiar)","(controlled)","[paragon]","(paragon)"]

ENABLE_CUSTOM_NAMES = True
_ALLOWED = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ")

# ====================================================================
# Auto Renaming ( AUNUM) 
# ====================================================================
CUSTOM_SUMMON_NAMES = {
    "energy vortex":        "Vortex",
    "blade spirits":        "Blades",
    "a fire elemental":       "Fire",
    "a water elemental":      "Water",
    "a air elemental":        "AirElem",
    "a earth elemental":      "Earth",
    "daemon":               "Daemon",
    "a blood elemental":      "BloodElem",
}

MAJOR_SUMMON_OPTIONS = [
    "Summon Daemon",
    "Summon Earth Elemental",
    "Summon Fire Elemental",
    "Summon Water Elemental",
    "Summon Air Elemental",
    "Energy Vortex",
]
MAJOR_SUMMON_SPELL  = MAJOR_SUMMON_OPTIONS[3]
WISP_SUMMON_SPELL   = "Summon Creature"
BLADES_SUMMON_SPELL = "Blade Spirits"

MAX_LIST_ROWS       = 7

BG_GUMP_ID          = 30546
FROG_ICON           = 0x2130
FROG_HUE            = 1152

CMD_ALL_FOLLOW = "All follow me"
CMD_ALL_KILL   = "All kill"
CMD_ALL_GUARD  = "All guard me"
CMD_ALL_STOP   = "All stop"

# ====================================================================
# Button Settings (DO NOT EDIT)
# ====================================================================
BTN_SUMMON_MAJOR      = 70001
BTN_SUMMON_WISP       = 70002
BTN_SUMMON_BLADES     = 70003
BTN_ALL_FOLLOW        = 70101
BTN_ALL_KILL          = 70102
BTN_ALL_GUARD         = 70103
BTN_ALL_STOP          = 70104
BTN_OPEN_PET_GUMPS    = 70105  # Not used but keeping it if you wanna swap
BTN_SETTINGS_OPEN     = 70200
BTN_SETTINGS_BACK     = 70201
BTN_SELECT_MAJOR_BASE = 70300
BTN_QUIT              = 70999

# ====================================================================
# Run State Settings (DO NOT EDIT)
# ====================================================================
_running        = True
_dirty_ui       = True
_summons            = {}
_recent_candidates  = {}
_tick               = 0
_hostiles_rows      = []
_players_rows       = []
_last_hostile_snapshot = []
_last_player_snapshot  = []
_current_page        = 0
_current_major_index = 3


# ====================================================================
# HELPERS (DO NOT EDIT)
# ====================================================================
def dbg(msg,hue=0x0481):
    try: Misc.SendMessage(str(msg),hue)
    except: pass

def _dist_to_player(m):
    try:
        pp=Player.Position; mp=m.Position
        return max(abs(pp.X-mp.X),abs(pp.Y-mp.Y))
    except: return 99

def _clean_name(s):
    try:
        s=(s or "").strip().lower()
        for m in STATUS_MARKERS: s=s.replace(m.lower(),"")
        return " ".join(s.split())
    except: return ""

def _proper(text):
    try: return " ".join(t.capitalize() for t in text.split())
    except: return text

def _true_name_from_props(m):
    try:
        if m.PropsUpdated:
            for p in m.Properties:
                t=str(p).strip()
                if t.startswith("a ") or t.startswith("an "): return t
    except: pass
    return None

def _props_contain(m,needles):
    try:
        if not m.PropsUpdated: return False
        for p in m.Properties:
            t=str(p).lower()
            for n in needles:
                if n in t: return True
    except: pass
    return False

def _extract_timeleft_from_props(m):
    try:
        if not m.PropsUpdated: return None
        for p in m.Properties:
            line=str(p).strip().lower()
            m1=re.search(r"time left\s*:\s*(?:(\d+)\s*(?:min|m)\s*)?(\d+)\s*(?:sec|s)\w*",line)
            if m1:
                mins=int(m1.group(1) or 0)
                secs=int(m1.group(2) or 0)
                return mins*60+secs
    except: pass
    return None

def _fmt_timeleft(secs):
    if secs is None: return ""
    if secs<0: secs=0
    m,s=divmod(secs,60)
    return f"{m}:{s:02d}"

def _owned_by_tag(m):
    return False  

def _sanitize_pet_name(s):
    s="".join(ch for ch in (s or "") if ch in _ALLOWED).strip()
    if len(s)>MAX_NAME_LEN: s=s[:MAX_NAME_LEN]
    return s

def _resolve_name(m,prev_name):
    if not m: return prev_name or "???"
    true_name=_true_name_from_props(m)
    if true_name:
        c=_clean_name(true_name)
        if c: return _proper(c)
    raw=m.Name or ""
    if raw:
        c=_clean_name(raw)
        if c: return _proper(c)
    return prev_name or "???"

def _journal_says_unacceptable():
    try: return Journal.Search("unacceptable")
    except: return False

def _journal_says_renamed():
    try: return not Journal.Search("unacceptable")
    except: return True

def _variants_for_name(base_desired):
    s=_sanitize_pet_name(base_desired)
    variants,seen=[],set()
    def add(v):
        v2=_sanitize_pet_name(v)
        if v2 and v2 not in seen:
            variants.append(v2); seen.add(v2)
    add(s); add(s.replace(" ",""))
    if " " in s:
        add(s.split(" ")[0]); add(s.split(" ")[-1])
    if len(s)>8: add(s[:8])
    if len(s)>10: add(s[:10])
    if len(s)>=2: add(s[:-1])
    return variants

def _attempt_pet_rename(m,desired):
    variants=_variants_for_name(desired)
    if USE_TAG_IN_RENAME:
        variants=[f"{SAFE_TAG_PREFIX} {v}" for v in variants]+variants
    for v in variants:
        Journal.Clear()
        Misc.PetRename(m,v)
        Misc.Pause(250)
        if _journal_says_unacceptable(): continue
        Misc.Pause(200)
        if _journal_says_renamed():
            dbg(f"Renamed to: {v}",0x44); return True
    return False

def _custom_name_for_base(base_clean):
    if not ENABLE_CUSTOM_NAMES: return None
    return CUSTOM_SUMMON_NAMES.get(base_clean,_proper(base_clean))

def _try_autotag(m):
    if not AUTO_TAG_SUMMONS: return False
    try:
        base_clean=_clean_name(m.Name)
        if not base_clean: return False
        desired=_custom_name_for_base(base_clean) or base_clean
        ok=_attempt_pet_rename(m,desired)
        Misc.Pause(150)
        return ok
    except: return False

def _health_hue(cur,mx):
    if mx<=0: return HUES_BY_LEVEL[0]
    frac=max(0.0,min(1.0,float(cur)/float(mx)))
    idx=int(frac*5.0)
    if idx<0: idx=0
    elif idx>5: idx=5
    return HUES_BY_LEVEL[idx]

def _scan_friendlies():
    f=Mobiles.Filter()
    f.Enabled=True; f.RangeMax=SCAN_RANGE; f.CheckLineOfSight=False
    try:
        if Byte is not None:
            notos=List[Byte](); notos.Add(Byte(2)); f.Notorieties=notos
        else: f.Notorieties.Add(2)
    except:
        try: f.Notorieties.Add(2)
        except: pass
    return Mobiles.ApplyFilter(f) or []

def scan_and_update():
    global _tick
    _tick+=1
    mobs=_scan_friendlies()
    seen=set()
    for m in mobs:
        if not m: continue
        try:
            if m.IsHuman:  
                continue
        except: pass
        accepted=False
        raw=(m.Name or "")
        clean=_clean_name(raw)
        looks_like_summon=(
            "(summoned)" in raw.lower()
            or _props_contain(m,["(summoned)","summoned creature","(familiar)"])
            or clean in BASE_SUMMON_NAMES
        )
        if looks_like_summon:
            if m.Serial not in _recent_candidates and _dist_to_player(m)<=8:
                _try_autotag(m)
                _recent_candidates[m.Serial]=_tick+GRACE_TICKS
            if _recent_candidates.get(m.Serial,0)>=_tick:
                accepted=True
        if not accepted: continue
        seen.add(m.Serial)
        tl=_extract_timeleft_from_props(m)
        prev_name=_summons.get(m.Serial,{}).get("name")
        resolved_name=_resolve_name(m,prev_name)
        if m.Serial not in _summons:
            _summons[m.Serial]={
                "name":resolved_name or prev_name or "???",
                "last":getattr(m,"Hits",0),
                "max":getattr(m,"HitsMax",0),
                "miss":0,
                "seen_tick":_tick,
                "tl_secs":tl,
            }
        else:
            e=_summons[m.Serial]
            if resolved_name: e["name"]=resolved_name
            if hasattr(m,"HitsMax") and m.HitsMax>0:
                e["last"]=m.Hits; e["max"]=m.HitsMax
            e["miss"]=0; e["seen_tick"]=_tick
            if tl is not None: e["tl_secs"]=tl
    to_del=[]
    for s,e in _summons.items():
        if s not in seen:
            e["miss"]=e.get("miss",0)+1
            if e["miss"]>=OUT_OF_RANGE_TICKS: to_del.append(s)
    for s in to_del: _summons.pop(s,None)
    for s,till in list(_recent_candidates.items()):
        if till<_tick: _recent_candidates.pop(s,None)

def _draw_bar(gd,x,y,width,pct,hue_fill,hue_bg=BAR_HUE_BG):
    segs=max(1,width//BAR_SEG_W)
    filled=int(round(pct*segs))
    for i in range(segs): Gumps.AddImage(gd,x+i*BAR_SEG_W,y,BAR_SEG_ART,hue_bg)
    for i in range(filled): Gumps.AddImage(gd,x+i*BAR_SEG_W,y,BAR_SEG_ART,hue_fill)

    
# Player Tracking, Feel free to steal    
def update_hostiles_and_players():
    global _hostiles_rows,_players_rows,_last_hostile_snapshot,_last_player_snapshot,_dirty_ui
    hostiles=[]
    try:
        f=Mobiles.Filter()
        f.Enabled=True; f.RangeMax=SCAN_RANGE; f.CheckLineOfSight=False
        if Byte is not None:
            notos=List[Byte]()
            for n in [3,4,5,6]: notos.Add(Byte(n))
            f.Notorieties=notos
        else:
            for n in [3,4,5,6]: f.Notorieties.Add(n)
        try: f.IsHuman=0
        except: pass
        mobs=Mobiles.ApplyFilter(f) or []
        for m in mobs:
            if not m: continue
            dist=_dist_to_player(m)
            hostiles.append((m,dist))
    except: hostiles=[]
    hostiles.sort(key=lambda t:t[1])
    hostiles=hostiles[:MAX_LIST_ROWS]
    players=[]
    try:
        for noto in (1,6):
            f=Mobiles.Filter()
            f.Enabled=True; f.RangeMax=PLAYER_SCAN_RANGE; f.CheckLineOfSight=False
            if Byte is not None:
                notos=List[Byte](); notos.Add(Byte(noto)); f.Notorieties=notos
            else: f.Notorieties.Add(noto)
            try: f.IsHuman=1
            except: pass
            plist=Mobiles.ApplyFilter(f) or []
            for m in plist:
                if not m: continue
                if m.Serial==Player.Serial: continue
                dist=_dist_to_player(m)
                players.append((m,dist))
    except: players=[]
    seen=set(); uniq_players=[]
    for m,d in sorted(players,key=lambda t:t[1]):
        if m.Serial in seen: continue
        seen.add(m.Serial); uniq_players.append((m,d))
    uniq_players=uniq_players[:MAX_LIST_ROWS]
    new_hostile_snap=[(h[0].Serial,h[0].Hits,h[0].HitsMax,h[1]) for h in hostiles]
    new_player_snap=[(p[0].Serial,p[0].Notoriety,p[1]) for p in uniq_players]
    if new_hostile_snap!=_last_hostile_snapshot or new_player_snap!=_last_player_snapshot:
        _dirty_ui=True
    _hostiles_rows=hostiles; _players_rows=uniq_players
    _last_hostile_snapshot=new_hostile_snap
    _last_player_snapshot=new_player_snap

def load_settings():
    global _current_major_index,MAJOR_SUMMON_SPELL
    selected=None
    try:
        if Misc.CheckSharedValue("frog_major_summon"):
            selected=Misc.ReadSharedValue("frog_major_summon")
    except: selected=None
    if selected in MAJOR_SUMMON_OPTIONS:
        _current_major_index=MAJOR_SUMMON_OPTIONS.index(selected)
    else: _current_major_index=3
    MAJOR_SUMMON_SPELL=MAJOR_SUMMON_OPTIONS[_current_major_index]

def save_settings():
    try: Misc.SetSharedValue("frog_major_summon",MAJOR_SUMMON_SPELL)
    except: pass

def cast_single_targetless(spell_name):
    try:
        Spells.Cast(spell_name)
        Misc.Pause(800)
    except: pass

def do_summon_major(): cast_single_targetless(MAJOR_SUMMON_SPELL)
def do_summon_wisp(): cast_single_targetless(WISP_SUMMON_SPELL)
def do_summon_blades(): cast_single_targetless(BLADES_SUMMON_SPELL)

def say_and_maybe_target(cmd_text,target_serial=None):
    try: Player.ChatSay(0,cmd_text)
    except: return
    if target_serial is not None:
        if Target.WaitForTarget(1200,False):
            try: Target.TargetExecute(target_serial)
            except: pass

def pet_all_follow(): say_and_maybe_target(CMD_ALL_FOLLOW,Player.Serial)
def pet_all_kill_global(): say_and_maybe_target(CMD_ALL_KILL)
def pet_all_guard(): say_and_maybe_target(CMD_ALL_GUARD,Player.Serial)
def pet_all_stop(): say_and_maybe_target(CMD_ALL_STOP)

def open_pet_gumps():
    for s in list(_summons.keys()):
        m=Mobiles.FindBySerial(s)
        if not m: continue
        try:
            Mobiles.UseMobile(m.Serial)
            Misc.Pause(250)
        except: pass

def cast_greater_heal_on(serial):
    Target.Cancel()
    try:
        Spells.Cast("Greater Heal")
        if Target.WaitForTarget(1500):
            Target.TargetExecute(serial)
        else:
            Misc.SendMessage("No target cursor for Greater Heal", 33)
    except:
        Misc.SendMessage("Failed to cast Greater Heal", 33)        
        
def do_all_kill_on_serial(serial):
    Target.Cancel()
    Player.ChatSay(0,CMD_ALL_KILL)
    if Target.WaitForTarget(2000):
        try: Target.TargetExecute(serial)
        except: Misc.SendMessage("Failed to target mob!",33)
    else: Misc.SendMessage("No targeting cursor appeared!",33)

    
# ====================================================================
# RENDER FUNCTIONS (DO NOT EDIT)
# ====================================================================   
def render_main_page(gd,rows,summon_block_h,list_block_h,total_w,total_h):
    left_x=10; right_x=190
    Gumps.AddBackground(gd,0,0,total_w,total_h,BG_GUMP_ID)
    Gumps.AddAlphaRegion(gd,0,0,total_w,total_h)
    Gumps.AddItem(gd,5,5,FROG_ICON,FROG_HUE)
    Gumps.AddLabel(gd,40,8,1152,"Frog Summon Suite "+VERSION)
    Gumps.AddButton(gd,total_w-65,5,4029,4030,BTN_SETTINGS_OPEN,1,0)
    Gumps.AddButton(gd,total_w-25,5,4017,4018,BTN_QUIT,1,0)
    y=26
    Gumps.AddLabel(gd,left_x,y,1152,"Summons"); y+=16
    x=left_x
    Gumps.AddButton(gd,x,y,4014,4015,BTN_SUMMON_MAJOR,1,0)
    Gumps.AddLabel(gd,x+20,y,0x0481,"Major"); x+=80
    Gumps.AddButton(gd,x,y,4014,4015,BTN_SUMMON_WISP,1,0)
    Gumps.AddLabel(gd,x+20,y,0x0481,"Creature"); x+=70
    Gumps.AddButton(gd,x,y,4014,4015,BTN_SUMMON_BLADES,1,0)
    Gumps.AddLabel(gd,x+20,y,0x0481,"Blades")
    y+=22
    Gumps.AddLabel(gd,left_x,y,0x0481,"--------------------------------"); y+=14
    Gumps.AddLabel(gd,left_x,y,1152,"Commands"); y+=16
    x=left_x
    Gumps.AddButton(gd,x,y,4005,4006,BTN_ALL_FOLLOW,1,0)
    Gumps.AddLabel(gd,x+20,y,0x0481,"Follow"); x+=80
    Gumps.AddButton(gd,x,y,4005,4006,BTN_ALL_KILL,1,0)
    Gumps.AddLabel(gd,x+20,y,0x0481,"Kill"); x+=70
    Gumps.AddButton(gd,x,y,4005,4006,BTN_ALL_GUARD,1,0)
    Gumps.AddLabel(gd,x+20,y,0x0481,"Guard"); x+=80
    Gumps.AddButton(gd,x,y,4005,4006,BTN_ALL_STOP,1,0)
    Gumps.AddLabel(gd,x+20,y,0x0481,"Stop")
    y+=22
    Gumps.AddLabel(gd,left_x,y,0x0481,"--------------------------------"); y+=14
    Gumps.AddLabel(gd,left_x,y,0x0035,"Summons:"); y+=16
    for i,(serial,name_raw,cur,mx,frac,tl) in enumerate(rows):
        row_y=y+ROW_HEIGHT*i
        nm=_proper(_clean_name(name_raw)) or "???"
        hue=_health_hue(cur,mx)
        pct=int(round(frac*100)) if mx>0 else 0
        try: Gumps.AddButton(gd,left_x+2,row_y+1,0x0846,0x0846,int(serial),1,0)
        except: pass
        Gumps.AddLabel(gd,left_x+20,row_y,0x0481,nm)
        bar_x=left_x+110
        _draw_bar(gd,bar_x,row_y+1,BAR_W,frac,hue)
        Gumps.AddLabel(gd,bar_x+BAR_W+6,row_y,hue,f"{pct:>3d}%")
        tl_txt=_fmt_timeleft(tl)
        if tl_txt: Gumps.AddLabel(gd,bar_x+BAR_W+50,row_y,0x0035,tl_txt)
    y=y+summon_block_h
    Gumps.AddLabel(gd,left_x,y,1152,"Creatures:")
    Gumps.AddLabel(gd,right_x,y,1152,"Players:"); y+=16
    for i in range(MAX_LIST_ROWS):
        row_y=y+ROW_HEIGHT*i
        if i<len(_hostiles_rows):
            m,dist=_hostiles_rows[i]
            nm=(m.Name or "???").strip()
            hp_txt=""
            try:
                if hasattr(m,"HitsMax") and m.HitsMax>0:
                    hp_pct=int((m.Hits*100)/max(1,m.HitsMax))
                    hp_txt=f"{hp_pct:3d}%"
            except: pass
            try: Gumps.AddButton(gd,left_x+2,row_y+1,0x0846,0x0846,int(m.Serial),1,0)
            except: pass
            Gumps.AddLabel(gd,left_x+20,row_y,0x0481,nm[:18])
            Gumps.AddLabel(gd,left_x+135,row_y,0x0481,f"{dist:2d}")
            if hp_txt: Gumps.AddLabel(gd,left_x+155,row_y,0x0481,hp_txt)
        if i<len(_players_rows):
            m,dist=_players_rows[i]
            nm=(m.Name or "???").strip()
            hue=0x59
            try:
                noto=m.Notoriety
                if noto==6: hue=33
                elif noto==1: hue=68
            except: pass
            Gumps.AddLabel(gd,right_x,row_y,hue,nm[:18])
            Gumps.AddLabel(gd,right_x+130,row_y,hue,f"{dist:2d}")

def render_settings_page(gd):
    width,height=260,220
    Gumps.AddBackground(gd,0,0,width,height,BG_GUMP_ID)
    Gumps.AddAlphaRegion(gd,0,0,width,height)
    Gumps.AddLabel(gd,10,8,1152,"Summon Settings")
    Gumps.AddButton(gd,width-25,5,4017,4018,BTN_SETTINGS_BACK,1,0)
    y=40
    Gumps.AddLabel(gd,10,y,1152,"Major Summon:"); y+=20
    for idx,spell in enumerate(MAJOR_SUMMON_OPTIONS):
        btn_id=BTN_SELECT_MAJOR_BASE+idx
        label=spell.replace("Summon ","")
        Gumps.AddButton(gd,10,y,4005,4006,btn_id,1,0)
        Gumps.AddLabel(gd,35,y,0x0481,label)
        if spell==MAJOR_SUMMON_SPELL: Gumps.AddLabel(gd,190,y,68,"✔")
        y+=22

def render_gui():
    global _dirty_ui
    _dirty_ui=False
    rows=[]
    for s,e in _summons.items():
        mx=max(0,e.get("max",0))
        cur=max(0,e.get("last",0))
        frac=(float(cur)/mx) if mx>0 else 0.0
        rows.append((s,e.get("name",""),cur,mx,frac,e.get("tl_secs")))
    rows.sort(key=lambda it:it[4])
    summon_rows=len(rows)
    summon_block_h=20+summon_rows*ROW_HEIGHT if summon_rows>0 else 20
    list_block_h=20+MAX_LIST_ROWS*ROW_HEIGHT
    total_h=60+summon_block_h+list_block_h
    total_w=360
    Gumps.CloseGump(GUMP_ID)
    gd=Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd,0)
    if _current_page==0:
        render_main_page(gd,rows,summon_block_h,list_block_h,total_w,total_h)
    else:
        render_settings_page(gd)
    Gumps.SendGump(GUMP_ID,Player.Serial,GUMP_POS[0],GUMP_POS[1],gd.gumpDefinition,gd.gumpStrings)

    
# ====================================================================
# BUTTON HANDLERS (DO NOT EDIT)
# ====================================================================    
def handle_button(button_id):
    global _running,_dirty_ui,_current_page,_current_major_index,MAJOR_SUMMON_SPELL
    if button_id==BTN_SETTINGS_OPEN:
        _current_page=1; _dirty_ui=True; return
    if button_id==BTN_SETTINGS_BACK:
        _current_page=0; _dirty_ui=True; return
    if BTN_SELECT_MAJOR_BASE<=button_id<BTN_SELECT_MAJOR_BASE+len(MAJOR_SUMMON_OPTIONS):
        idx=button_id-BTN_SELECT_MAJOR_BASE
        if 0<=idx<len(MAJOR_SUMMON_OPTIONS):
            _current_major_index=idx
            MAJOR_SUMMON_SPELL=MAJOR_SUMMON_OPTIONS[idx]
            save_settings()
        _current_page=0; _dirty_ui=True; return
    if button_id==BTN_SUMMON_MAJOR:
        do_summon_major()
    elif button_id==BTN_SUMMON_WISP:
        do_summon_wisp()
    elif button_id==BTN_SUMMON_BLADES:
        do_summon_blades()
    elif button_id==BTN_ALL_FOLLOW:
        pet_all_follow()
    elif button_id==BTN_ALL_KILL:
        pet_all_kill_global()
    elif button_id==BTN_ALL_GUARD:
        pet_all_guard()
    elif button_id==BTN_ALL_STOP:
        pet_all_stop()
    elif button_id==BTN_OPEN_PET_GUMPS:
        open_pet_gumps()
    elif button_id==BTN_QUIT:
        _running=False; return
    else:
        if button_id in _summons:
            cast_greater_heal_on(button_id)
        else:
            m=Mobiles.FindBySerial(button_id)
            if m: do_all_kill_on_serial(button_id)
    _dirty_ui=True

    
# ====================================================================
# Main Loop
# ====================================================================    
load_settings()
Misc.SendMessage("Frog Summon Suite running…",0x44)

while _running and Player.Connected:
    gd=Gumps.GetGumpData(GUMP_ID)
    if gd and gd.buttonid:
        btn=gd.buttonid; gd.buttonid=0
        handle_button(btn)
        Misc.Pause(150)
        continue
    scan_and_update()
    update_hostiles_and_players()
    if _dirty_ui: render_gui()
    Misc.Pause(REFRESH_MS)

_summons.clear()
_recent_candidates.clear()
Gumps.CloseGump(GUMP_ID)
Misc.SendMessage("Frog Summon Suite stopped.",33)
