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
    from System import Byte
except:
    Byte = None

import re, time
import Misc, Player, Mobiles, Gumps, Target, Spells


# ====================================================================
# GLOBAL CONFIGS
# ====================================================================
VERSION            = "1.2"
GUMP_ID            = 0xF2065353
LOOP_IDLE_MS       = 100
STATE_REFRESH_MS   = 400
BUTTON_DEBOUNCE_MS = 180
SCAN_RANGE         = 30
PLAYER_SCAN_RANGE  = 30
ROW_HEIGHT         = 18
GUMP_POS           = (980, 220)

AUTO_KILL_RANGE         = 3
AUTO_KILL_RESET_RANGE   = 6
AUTO_KILL_COOLDOWN_MS   = 1800

HEAL_THRESHOLD_PCT  = 70
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
OUT_OF_RANGE_TICKS = 10

BASE_SUMMON_NAMES = [
    "air elemental",
    "blade spirit",
    "blade spirits",
    "blood elemental",
    "daemon",
    "devourer of souls",
    "earth elemental",
    "energy vortex",
    "feral mauler",
    "fire elemental",
    "poison elemental",
    "shadow elemental",
    "shadow wisp",
    "volt wisp",
    "water elemental",
    "wisp",
]
SUMMON_NAME_ALIASES = {
    "afire elemental":"fire elemental",
    "ashadow wisp":"shadow wisp",
}
STATUS_MARKERS = ["*grows stronger*","*regens*","(summoned)","(familiar)","(controlled)","[paragon]","(paragon)"]

ENABLE_CUSTOM_NAMES = True
_ALLOWED = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ")

_rename_done = set()

# ====================================================================
# Auto Renaming ( AUNUM) 
# ====================================================================
CUSTOM_SUMMON_NAMES = {
    "energy vortex":     "Vortex",
    "blade spirits":     "Blades",
    "blade spirit":      "Blades",
    "fire elemental":    "Fire",
    "water elemental":   "Water",
    "air elemental":     "AirElem",
    "earth elemental":   "Earth",
    "daemon":            "Daemon",
    "blood elemental":   "BloodElem",
    "devourer of souls": "Soul Sucker",
    "feral mauler":      "Mauler",
    "volt wisp":         "Pikachu",
    "poison elemental":  "Siefers Fart",
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

BG_GUMP_ID          = 5054
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
BTN_AUTO_KILL         = 70106
BTN_HEAL_LOWEST       = 70107
BTN_AUTO_SUPPORT      = 70108
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
_tick               = 0
_hostiles_rows      = []
_players_rows       = []
_last_summon_snapshot  = []
_last_hostile_snapshot = []
_last_player_snapshot  = []
_current_page        = 0
_current_major_index = 3
_auto_kill_enabled   = False
_auto_kill_target_serial = 0
_last_auto_kill_ms   = 0
_auto_support_enabled = False
_last_support_ms      = 0
_status_msg            = "Ready"
_status_hue            = 0x0481


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

def _set_status(message,hue=0x0481):
    global _status_msg,_status_hue,_dirty_ui
    message=str(message or "Ready")
    if message!=_status_msg or hue!=_status_hue:
        _status_msg=message
        _status_hue=hue
        _dirty_ui=True

def _canonical_summon_base(text):
    clean=_clean_name(text)
    clean=SUMMON_NAME_ALIASES.get(clean,clean)
    if clean.startswith("an "): clean=clean[3:]
    elif clean.startswith("a "): clean=clean[2:]
    if clean in BASE_SUMMON_NAMES:
        return clean
    for base,custom in CUSTOM_SUMMON_NAMES.items():
        if clean==_clean_name(custom):
            return base
    return None

def _base_name_from_props(m):
    try:
        if m.PropsUpdated:
            for p in m.Properties:
                base=_canonical_summon_base(str(p))
                if base: return base
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

def _remaining_time(entry):
    secs=entry.get("tl_secs")
    if secs is None: return None
    updated=entry.get("tl_updated",time.monotonic())
    elapsed=max(0,int(time.monotonic()-updated))
    return max(0,secs-elapsed)

def _fmt_timeleft(secs):
    if secs is None: return ""
    if secs<0: secs=0
    m,s=divmod(secs,60)
    return f"{m}:{s:02d}"

def _sanitize_pet_name(s):
    s="".join(ch for ch in (s or "") if ch in _ALLOWED).strip()
    if len(s)>MAX_NAME_LEN: s=s[:MAX_NAME_LEN]
    return s

def _resolve_name(m,prev_name,locked_name=None):
    if locked_name: return locked_name
    if not m: return prev_name or "???"
    raw=m.Name or ""
    if raw:
        c=_clean_name(raw)
        if c: return _proper(c)
    base=_base_name_from_props(m)
    if base: return _proper(base)
    return prev_name or "???"

def _custom_name_for_base(base_clean):
    if not ENABLE_CUSTOM_NAMES: return None
    return CUSTOM_SUMMON_NAMES.get(base_clean,_proper(base_clean))

def _try_autotag(m,base_clean):
    global _rename_done
    if not AUTO_TAG_SUMMONS or not m: return None
    serial = m.Serial
    if serial in _rename_done: return None
    try:
        desired = _custom_name_for_base(base_clean) if base_clean else None
        if not desired:
            return None
        if USE_TAG_IN_RENAME and SAFE_TAG_PREFIX:
            desired="%s %s" % (SAFE_TAG_PREFIX,desired)
        desired=_sanitize_pet_name(desired)
        if _clean_name(m.Name)==_clean_name(desired):
            _rename_done.add(serial)
            return desired
        Misc.PetRename(m, desired)
        _rename_done.add(serial)
        dbg("Renaming summon to: %s" % desired,0x44)
        return desired
    except:
        _rename_done.add(serial)
        return None


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

def _summon_snapshot():
    snapshot=[]
    for serial,entry in _summons.items():
        snapshot.append((
            serial,
            entry.get("name",""),
            entry.get("last",0),
            entry.get("max",0),
            entry.get("poisoned",False),
            entry.get("distance",99),
            _remaining_time(entry),
            entry.get("miss",0),
        ))
    snapshot.sort(key=lambda row:row[0])
    return snapshot

def scan_and_update():
    global _tick,_last_summon_snapshot,_dirty_ui
    _tick+=1
    mobs=_scan_friendlies()
    seen=set()
    for m in mobs:
        if not m: continue
        try:
            if m.IsHuman:  
                continue
        except: pass
        serial=m.Serial
        entry=_summons.get(serial)
        base_clean=_canonical_summon_base(m.Name) or _base_name_from_props(m)
        has_marker=_props_contain(m,["(summoned)","summoned creature","(familiar)"])
        if entry is None and not base_clean and not has_marker: continue
        if entry is None and _dist_to_player(m)>8: continue
        seen.add(m.Serial)
        tl=_extract_timeleft_from_props(m)
        if entry is None:
            locked_name=_try_autotag(m,base_clean)
            resolved_name=_resolve_name(m,None,locked_name)
            now=time.monotonic()
            entry={
                "name":resolved_name or "???",
                "base_name":base_clean or "",
                "locked_name":locked_name,
                "last":getattr(m,"Hits",0),
                "max":getattr(m,"HitsMax",0),
                "miss":0,
                "seen_tick":_tick,
                "tl_secs":tl,
                "tl_updated":now,
                "poisoned":bool(getattr(m,"Poisoned",False)),
                "distance":_dist_to_player(m),
            }
            _summons[serial]=entry
        else:
            if base_clean and not entry.get("base_name"):
                entry["base_name"]=base_clean
            if base_clean and not entry.get("locked_name") and serial not in _rename_done:
                entry["locked_name"]=_try_autotag(m,base_clean)
            resolved_name=_resolve_name(m,entry.get("name"),entry.get("locked_name"))
            if resolved_name and resolved_name != "???":
                entry["name"] = resolved_name
            if hasattr(m,"HitsMax") and m.HitsMax>0:
                entry["last"]=m.Hits; entry["max"]=m.HitsMax
            entry["miss"]=0; entry["seen_tick"]=_tick
            entry["poisoned"]=bool(getattr(m,"Poisoned",False))
            entry["distance"]=_dist_to_player(m)
            if tl is not None and tl!=entry.get("tl_secs"):
                entry["tl_secs"]=tl
                entry["tl_updated"]=time.monotonic()
    to_del=[]
    for s,e in _summons.items():
        if s not in seen:
            e["miss"]=e.get("miss",0)+1
            if e["miss"]>=OUT_OF_RANGE_TICKS: to_del.append(s)
    for s in to_del: 
        _summons.pop(s,None)
        if s in _rename_done:
            _rename_done.remove(s)
    new_snapshot=_summon_snapshot()
    if new_snapshot!=_last_summon_snapshot:
        _last_summon_snapshot=new_snapshot
        _dirty_ui=True

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
        _set_status("Casting %s" % spell_name,0x0044)
        Spells.Cast(spell_name)
        Misc.Pause(800)
    except:
        _set_status("Could not cast %s" % spell_name,33)

def do_summon_major(): cast_single_targetless(MAJOR_SUMMON_SPELL)
def do_summon_wisp(): cast_single_targetless(WISP_SUMMON_SPELL)
def do_summon_blades(): cast_single_targetless(BLADES_SUMMON_SPELL)

def say_and_maybe_target(cmd_text,target_serial=None):
    try: Player.ChatSay(0,cmd_text)
    except:
        _set_status("Command failed: %s" % cmd_text,33)
        return
    _set_status(cmd_text,0x0044)
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
    global _last_support_ms
    Target.Cancel()
    try:
        Spells.Cast("Greater Heal")
        if Target.WaitForTarget(1500):
            Target.TargetExecute(serial)
            _last_support_ms=int(time.monotonic()*1000)
            m=Mobiles.FindBySerial(serial)
            _set_status("Healing %s" % ((m.Name if m else "summon") or "summon"),0x0044)
            return True
        else:
            _set_status("No target cursor for Greater Heal",33)
    except:
        _set_status("Failed to cast Greater Heal",33)
    return False

def _support_visible_serials():
    if not CHECK_LINE_OF_SIGHT: return None
    try:
        f=Mobiles.Filter()
        f.Enabled=True; f.RangeMax=MAX_CAST_RANGE; f.CheckLineOfSight=True
        if Byte is not None:
            notos=List[Byte](); notos.Add(Byte(2)); f.Notorieties=notos
        else: f.Notorieties.Add(2)
        return set(m.Serial for m in (Mobiles.ApplyFilter(f) or []) if m)
    except:
        return None

def _support_candidate(require_injured=True):
    visible=_support_visible_serials()
    poisoned=[]
    injured=[]
    for serial,entry in _summons.items():
        m=Mobiles.FindBySerial(serial)
        if not m or _dist_to_player(m)>MAX_CAST_RANGE: continue
        if visible is not None and serial not in visible: continue
        try:
            if m.IsGhost or (m.HitsMax>0 and m.Hits<=0): continue
        except: pass
        mx=getattr(m,"HitsMax",0)
        cur=getattr(m,"Hits",0)
        if mx<=0: continue
        pct=int((cur*100)/max(1,mx))
        if CURE_FIRST and bool(getattr(m,"Poisoned",False)):
            poisoned.append((pct,m))
        if pct<100 and (not require_injured or pct<=HEAL_THRESHOLD_PCT):
            injured.append((pct,m))
    if poisoned:
        poisoned.sort(key=lambda row:row[0])
        return poisoned[0][1],"Cure",poisoned[0][0]
    if injured:
        injured.sort(key=lambda row:row[0])
        return injured[0][1],"Greater Heal",injured[0][0]
    return None,None,None

def _cast_support_spell(m,spell_name):
    global _last_support_ms
    if not m or not spell_name: return False
    try:
        Spells.Cast(spell_name)
        if Target.WaitForTarget(1500,False):
            Target.TargetExecute(m.Serial)
            _last_support_ms=int(time.monotonic()*1000)
            _set_status("%s: %s" % (spell_name,m.Name or "summon"),0x0044)
            return True
    except: pass
    _last_support_ms=int(time.monotonic()*1000)
    _set_status("Could not %s summon" % spell_name.lower(),33)
    return False

def heal_lowest_summon():
    m,spell_name,pct=_support_candidate(False)
    if not m:
        _set_status("All tracked summons are healthy",0x0044)
        return
    Target.Cancel()
    _cast_support_spell(m,spell_name)

def auto_support_step():
    global _last_support_ms
    if not _auto_support_enabled or _current_page!=0: return False
    try:
        if Target.HasTarget(): return False
    except: pass
    now_ms=int(time.monotonic()*1000)
    if now_ms-_last_support_ms<SUPPORT_COOLDOWN_MS: return False
    m,spell_name,pct=_support_candidate(True)
    if not m: return False
    _last_support_ms=now_ms
    _cast_support_spell(m,spell_name)
    return True

def toggle_auto_support():
    global _auto_support_enabled,_dirty_ui
    _auto_support_enabled=not _auto_support_enabled
    _dirty_ui=True
    state="ON" if _auto_support_enabled else "OFF"
    _set_status("Auto Support %s (heal at %d%%)" % (state,HEAL_THRESHOLD_PCT),68 if _auto_support_enabled else 53)
        
def do_all_kill_on_serial(serial):
    Target.Cancel()
    try: Player.ChatSay(0,CMD_ALL_KILL)
    except:
        Misc.SendMessage("Failed to issue All kill!",33)
        return False
    if Target.WaitForTarget(2000,False):
        try:
            Target.TargetExecute(serial)
            return True
        except:
            Misc.SendMessage("Failed to target mob!",33)
            return False
    Misc.SendMessage("No targeting cursor appeared!",33)
    return False

def _auto_kill_target_valid():
    if _auto_kill_target_serial<=0: return False
    m=Mobiles.FindBySerial(_auto_kill_target_serial)
    if not m: return False
    try:
        if m.IsGhost: return False
    except: pass
    try:
        if m.HitsMax>0 and m.Hits<=0: return False
    except: pass
    return _dist_to_player(m)<=AUTO_KILL_RESET_RANGE

def _nearest_auto_kill_candidate():
    for m,dist in _hostiles_rows:
        if not m or dist>AUTO_KILL_RANGE: continue
        try:
            if m.IsGhost: continue
        except: pass
        try:
            if m.HitsMax>0 and m.Hits<=0: continue
        except: pass
        return m
    return None

def auto_kill_step():
    global _auto_kill_target_serial,_last_auto_kill_ms
    if not _auto_kill_enabled or _current_page!=0: return
    try:
        if Target.HasTarget(): return
    except: pass
    if _auto_kill_target_valid(): return
    _auto_kill_target_serial=0
    now_ms=int(time.monotonic()*1000)
    if now_ms-_last_auto_kill_ms<AUTO_KILL_COOLDOWN_MS: return
    m=_nearest_auto_kill_candidate()
    if not m: return
    _last_auto_kill_ms=now_ms
    if do_all_kill_on_serial(m.Serial):
        _auto_kill_target_serial=m.Serial
        _set_status("Auto Kill: %s" % (m.Name or "target"),68)

def toggle_auto_kill():
    global _auto_kill_enabled,_auto_kill_target_serial,_dirty_ui
    _auto_kill_enabled=not _auto_kill_enabled
    _auto_kill_target_serial=0
    _dirty_ui=True
    state="ON" if _auto_kill_enabled else "OFF"
    _set_status("Auto Kill %s (%d tiles)" % (state,AUTO_KILL_RANGE),68 if _auto_kill_enabled else 53)

    
# ====================================================================
# RENDER FUNCTIONS (DO NOT EDIT)
# ====================================================================   
def render_main_page(gd,rows,summon_block_h,total_w,total_h):
    left_x=10; right_x=230
    Gumps.AddBackground(gd,0,0,total_w,total_h,BG_GUMP_ID)
    Gumps.AddAlphaRegion(gd,0,0,total_w,total_h)
    Gumps.AddItem(gd,5,5,FROG_ICON,FROG_HUE)
    Gumps.AddLabel(gd,40,8,1152,"Frog Summon Suite "+VERSION)
    Gumps.AddButton(gd,total_w-75,5,4029,4030,BTN_SETTINGS_OPEN,1,0)
    Gumps.AddButton(gd,total_w-40,5,4017,4018,BTN_QUIT,1,0)
    y=26
    Gumps.AddLabel(gd,left_x,y,1152,"Summons"); y+=16
    x=left_x
    Gumps.AddButton(gd,x,y,4014,4015,BTN_SUMMON_MAJOR,1,0)
    Gumps.AddLabel(gd,x+20,y,0x0481,"Major"); x+=80
    Gumps.AddButton(gd,x,y,4014,4015,BTN_SUMMON_WISP,1,0)
    Gumps.AddLabel(gd,x+20,y,0x0481,"Creature"); x+=70
    Gumps.AddButton(gd,x,y,4014,4015,BTN_SUMMON_BLADES,1,0)
    Gumps.AddLabel(gd,x+20,y,0x0481,"Blades")
    x=245
    Gumps.AddButton(gd,x,y,4005,4006,BTN_AUTO_KILL,1,0)
    Gumps.AddLabel(gd,x+20,y,68 if _auto_kill_enabled else 53,"Kill:ON" if _auto_kill_enabled else "Kill:OFF")
    x=345
    Gumps.AddButton(gd,x,y,4005,4006,BTN_AUTO_SUPPORT,1,0)
    Gumps.AddLabel(gd,x+20,y,68 if _auto_support_enabled else 53,"Support:ON" if _auto_support_enabled else "Support:OFF")
    y+=22
    Gumps.AddLabel(gd,left_x,y,0x0481,"--------------------------------------------"); y+=14
    Gumps.AddLabel(gd,left_x,y,1152,"Commands"); y+=16
    x=left_x
    Gumps.AddButton(gd,x,y,4005,4006,BTN_ALL_FOLLOW,1,0)
    Gumps.AddLabel(gd,x+20,y,0x0481,"Follow"); x+=80
    Gumps.AddButton(gd,x,y,4005,4006,BTN_ALL_KILL,1,0)
    Gumps.AddLabel(gd,x+20,y,0x0481,"Kill"); x+=70
    Gumps.AddButton(gd,x,y,4005,4006,BTN_ALL_GUARD,1,0)
    Gumps.AddLabel(gd,x+20,y,0x0481,"Guard"); x+=80
    Gumps.AddButton(gd,x,y,4005,4006,BTN_ALL_STOP,1,0)
    Gumps.AddLabel(gd,x+20,y,0x0481,"Stop"); x+=70
    Gumps.AddButton(gd,x,y,4005,4006,BTN_HEAL_LOWEST,1,0)
    Gumps.AddLabel(gd,x+20,y,0x0481,"Heal Low")
    y+=22
    Gumps.AddLabel(gd,left_x,y,_status_hue,"Status: "+_status_msg[:54]); y+=18
    Gumps.AddLabel(gd,left_x,y,0x0481,"--------------------------------------------"); y+=14
    Gumps.AddLabel(gd,left_x,y,0x0035,"Summons (%d) - gem heals" % len(rows)); y+=16
    for i,(serial,name_raw,cur,mx,frac,tl,poisoned,dist) in enumerate(rows):
        row_y=y+ROW_HEIGHT*i
        nm=(name_raw or "???").strip()
        hue=_health_hue(cur,mx)
        pct=int(round(frac*100)) if mx>0 else 0
        try: Gumps.AddButton(gd,left_x+2,row_y+1,0x0846,0x0846,int(serial),1,0)
        except: pass
        Gumps.AddLabel(gd,left_x+20,row_y,68 if poisoned else 0x0481,nm[:15])
        bar_x=left_x+125
        _draw_bar(gd,bar_x,row_y+1,BAR_W,frac,hue)
        Gumps.AddLabel(gd,bar_x+BAR_W+6,row_y,hue,f"{pct:>3d}%")
        tl_txt=_fmt_timeleft(tl)
        if tl_txt: Gumps.AddLabel(gd,bar_x+BAR_W+50,row_y,0x0035,tl_txt)
        Gumps.AddLabel(gd,bar_x+BAR_W+92,row_y,0x0481,"%dt" % dist)
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
            Gumps.AddLabel(gd,left_x+20,row_y,0x0481,nm[:15])
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
    width,height=300,270
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
    y+=4
    Gumps.AddLabel(gd,10,y,1152,"Support:"); y+=18
    Gumps.AddLabel(gd,10,y,0x0481,"Cure poisoned summons first: %s" % ("Yes" if CURE_FIRST else "No")); y+=18
    Gumps.AddLabel(gd,10,y,0x0481,"Heal at or below: %d%%" % HEAL_THRESHOLD_PCT); y+=18
    Gumps.AddLabel(gd,10,y,0x0481,"Maximum cast range: %d tiles" % MAX_CAST_RANGE)

def render_gui():
    global _dirty_ui
    _dirty_ui=False
    rows=[]
    for s,e in _summons.items():
        mx=max(0,e.get("max",0))
        cur=max(0,e.get("last",0))
        frac=(float(cur)/mx) if mx>0 else 0.0
        rows.append((s,e.get("name",""),cur,mx,frac,_remaining_time(e),e.get("poisoned",False),e.get("distance",99)))
    rows.sort(key=lambda it:it[4])
    summon_rows=len(rows)
    summon_block_h=20+summon_rows*ROW_HEIGHT if summon_rows>0 else 20
    total_h=352+summon_rows*ROW_HEIGHT
    total_w=455
    Gumps.CloseGump(GUMP_ID)
    gd=Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd,0)
    if _current_page==0:
        render_main_page(gd,rows,summon_block_h,total_w,total_h)
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
    elif button_id==BTN_AUTO_KILL:
        toggle_auto_kill()
    elif button_id==BTN_AUTO_SUPPORT:
        toggle_auto_support()
    elif button_id==BTN_HEAL_LOWEST:
        heal_lowest_summon()
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
_last_state_refresh_ms=0

while _running and Player.Connected:
    gd=Gumps.GetGumpData(GUMP_ID)
    btn=int(getattr(gd,"buttonid",0)) if gd else 0
    if btn>0:
        try: gd.buttonid=0
        except: pass
        Gumps.CloseGump(GUMP_ID)
        handle_button(btn)
        Misc.Pause(BUTTON_DEBOUNCE_MS)
        continue
    now_ms=int(time.monotonic()*1000)
    if now_ms-_last_state_refresh_ms>=STATE_REFRESH_MS:
        _last_state_refresh_ms=now_ms
        scan_and_update()
        update_hostiles_and_players()
        support_acted=auto_support_step()
        if not support_acted:
            auto_kill_step()
    if _dirty_ui or Gumps.GetGumpData(GUMP_ID) is None:
        render_gui()
    Misc.Pause(LOOP_IDLE_MS)

_summons.clear()
Gumps.CloseGump(GUMP_ID)
Misc.SendMessage("Frog Summon Suite stopped.",33)
