# ==================================
# === Summon Monitor ==
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
## This script features an auto support (Heal/Cure) of your summons using magery. This is off by default.
## Enabling this has a chance of you losing control of your character in dire situations.
## Use the feature if you want it to handle that tedium, Keep off if you don't.

from System.Collections.Generic import List
try:
    from System import Byte
except:
    Byte = None

import re, time

# CONFIG
GUMP_ID            = 0x51A0C0DE
REFRESH_MS         = 800
SCAN_RANGE         = 30
ROW_HEIGHT         = 18
GUMP_POS           = (870, 635)
VERSION            = "0.12"

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
TAG_PREFIX         = "" ## Change this to whatever you want. within the ""
USE_TAG_IN_RENAME  = False
SAFE_TAG_PREFIX    = "" ## Change this to whatever you want. within the ""
MAX_NAME_LEN       = 16
GRACE_TICKS        = 6
OUT_OF_RANGE_TICKS = 3
TOGGLE_BUTTON_ID   = 9998

BASE_SUMMON_NAMES = [
    "blood elemental","greater air elemental","greater earth elemental","greater fire elemental","greater water elemental",
    "daemon","earth elemental","fire elemental","water elemental","air elemental",
    "energy vortex","blade spirits","nature's fury","rising colossus",
    "wisp","shadow wisp","shade","hound","vampire bat","death adder","poison elemental","shadow elemental"
]
STATUS_MARKERS = ["*grows stronger*","*regens*","(summoned)","(familiar)","(controlled)","[paragon]","(paragon)"]

# Names
ENABLE_CUSTOM_NAMES = True
_ALLOWED = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ")

CUSTOM_SUMMON_NAMES = {
    "energy vortex":        "Vortex",
    "blade spirits":        "Blades",
    "rising colossus":      "Colossus",
    "nature's fury":        "Fury",
    "greater fire elemental":"GFireElem",
    "greater water elemental":"GWaterElem",
    "greater air elemental":"GAirElem",
    "greater earth elemental":"GEarthElem",
    "fire elemental":       "Fire",
    "water elemental":      "a fira elemental",
    "air elemental":        "AirElem",
    "earth elemental":      "Earth",
    "daemon":               "Daemon",
    "wisp":                 "Wisp",
    "shadow wisp":          "ShadowWisp",
    "blood elemental":      "BloodElem",
    "hound":                "Hound",
    "vampire bat":          "Bat",
    "death adder":          "Adder",
    "poison elemental":     "Poison",
    "shadow elemental":     "ShadowEle",
}

DEBUG = False
def dbg(msg, hue=0x03B2):
    if DEBUG:
        try: Misc.SendMessage(f"[FrogSum] {msg}", hue)
        except: pass

# Name/Text
def _proper(text):
    try:    return " ".join(w.capitalize() for w in (text or "").split())
    except: return text or ""

def _ascii_only(s):         return "".join((ch if ord(ch) < 128 else " ") for ch in (s or ""))
def _filter_allowed(s):     return "".join((ch if ch in _ALLOWED else " ") for ch in (s or ""))
def _collapse_spaces(s):    return " ".join((s or "").split())

def _sanitize_pet_name(name, max_len=MAX_NAME_LEN):
    s = _ascii_only(name); s = _filter_allowed(s)
    s = _collapse_spaces(s)[:max_len].strip()
    words = s.split(" ")
    def smart_cap(w): return w if (len(w) > 1 and w[1].isupper()) else (w.capitalize() if w else w)
    return " ".join(smart_cap(w) for w in words)

def _clean_name(name):
    s = (name or "").lower().strip()
    if s.startswith("a "):  s = s[2:]
    if s.startswith("an "): s = s[3:]
    for m in STATUS_MARKERS: s = s.replace(m.lower(), "")
    return " ".join(s.split())

def _true_name_from_props(m):
    try:
        if m.PropsUpdated:
            for p in m.Properties:
                t = str(p).strip()
                if t.startswith("a ") or t.startswith("an "): return t
    except: pass
    return None

def _props_contain(m, needles):
    try:
        if not m.PropsUpdated: return False
        for p in m.Properties:
            t = str(p).lower()
            for n in needles:
                if n in t: return True
    except: pass
    return False

def _extract_timeleft_from_props(m):
    try:
        if not m.PropsUpdated: return None
        for p in m.Properties:
            line = str(p).strip().lower()
            m1 = re.search(r"time left\s*:\s*(?:(\d+)\s*(?:min|m)\s*)?(\d+)\s*(?:sec|s)\w*", line)
            if m1:
                mins = int(m1.group(1) or 0); secs = int(m1.group(2) or 0)
                return mins*60 + secs
    except: pass
    return None

def _fmt_timeleft(secs):
    if secs is None: return ""
    if secs < 0: secs = 0
    m, s = divmod(secs, 60)
    return f"{m}:{s:02d}"

# Tagging Mobiles
def _owned_by_tag(m):
    try:    return (m.Name or "").startswith(TAG_PREFIX)
    except: return False

def _journal_says_unacceptable():
    try: return Journal.Search("unacceptable")
    except: return False

def _journal_says_renamed():
    try: return not Journal.Search("unacceptable")
    except: return True

def _variants_for_name(base_desired):
    s = _sanitize_pet_name(base_desired); variants, seen = [], set()
    def add(v):
        v2 = _sanitize_pet_name(v)
        if v2 and v2 not in seen: variants.append(v2); seen.add(v2)
    add(s); add(s.replace(" ",""))
    if " " in s: add(s.split(" ")[0]); add(s.split(" ")[-1])
    if len(s)>8: add(s[:8])
    if len(s)>10: add(s[:10])
    if len(s)>=2: add(s[:-1])
    return variants

def _attempt_pet_rename(m, desired):
    variants = _variants_for_name(desired)
    if USE_TAG_IN_RENAME:
        variants = [f"{SAFE_TAG_PREFIX} {v}" for v in variants] + variants
    for v in variants:
        Journal.Clear(); Misc.PetRename(m, v); Misc.Pause(250)
        if _journal_says_unacceptable(): continue
        Misc.Pause(200)
        if _journal_says_renamed():
            dbg(f"Renamed to: {v}", 0x44)
            return True
    return False

def _custom_name_for_base(base_clean):
    if not ENABLE_CUSTOM_NAMES: return None
    return CUSTOM_SUMMON_NAMES.get(base_clean, _proper(base_clean))

def _try_autotag(m):
    if not AUTO_TAG_SUMMONS: return False
    try:
        base_clean = _clean_name(m.Name)
        if not base_clean: return False
        desired = _custom_name_for_base(base_clean) or base_clean
        ok = _attempt_pet_rename(m, desired); Misc.Pause(150); return ok
    except: return False

def _dist_to_player(m):
    try:
        pp = Player.Position; mp = m.Position
        return max(abs(pp.X-mp.X), abs(pp.Y-mp.Y))
    except: return 99

def _health_hue(cur, mx):
    if mx <= 0: return HUES_BY_LEVEL[0]
    frac = max(0.0, min(1.0, float(cur)/float(mx)))
    idx = int(frac * 5.0)
    if   idx < 0: idx = 0
    elif idx > 5: idx = 5
    return HUES_BY_LEVEL[idx]

def _scan_friendlies():
    f = Mobiles.Filter(); f.Enabled = True; f.RangeMax = SCAN_RANGE; f.CheckLineOfSight = False
    try:
        if Byte is not None:
            notos = List[Byte](); notos.Add(Byte(2)); f.Notorieties = notos
        else: f.Notorieties.Add(2)
    except:
        try: f.Notorieties.Add(2)
        except: pass
    return Mobiles.ApplyFilter(f) or []

def _resolve_name(m, prev_name=None):
    nm = m.Name; tn = _true_name_from_props(m)
    if tn: return tn
    if nm and nm != "???": return nm
    try:
        Mobiles.SingleClick(m); Misc.Pause(120)
        m2 = Mobiles.FindBySerial(m.Serial)
        if m2:
            tn2 = _true_name_from_props(m2)
            if tn2: return tn2
            if m2.Name and m2.Name != "???": return m2.Name
    except: pass
    return prev_name or (nm if nm and nm != "???" else "")

# AUTO-SUPPORT STATE
_RUNTIME_AUTO_SUPPORT = False  ## DO NOT EDIT: Default False = off on launch. 

_last_cast_ms = 0

def _can_cast_now():
    global _last_cast_ms
    now = int(time.time()*1000)
    return (now - _last_cast_ms) >= SUPPORT_COOLDOWN_MS

def _mark_cast():
    global _last_cast_ms
    _last_cast_ms = int(time.time()*1000)

def _safe_in_range_and_los(m):
    try:
        if _dist_to_player(m) > MAX_CAST_RANGE: return False
        if CHECK_LINE_OF_SIGHT:
            try: Mobiles.WaitForProps(m, 200)
            except: pass
        return True
    except:
        return True

def _cast(spell_name, target_serial):
    try:
        Spells.Cast(spell_name)
        if Target.WaitForTarget(1200, False):
            Target.TargetExecute(target_serial)
            _mark_cast()
            dbg(f"Cast {spell_name} → {hex(int(target_serial))}", 0x44)
            Misc.Pause(200)
            return True
    except:
        pass
    return False

def _maybe_support():
    if not _RUNTIME_AUTO_SUPPORT or not _can_cast_now(): return False

    cands = []
    for s, e in _summons.items():
        m = Mobiles.FindBySerial(s)
        if not m: continue
        if not _safe_in_range_and_los(m): continue
        mx = max(1, int(e.get("max", 0)) or 1)
        cur = max(0, int(e.get("last", 0)) or 0)
        pct = (100.0 * cur) / float(mx)
        poisoned = False
        try: poisoned = bool(m.Poisoned)
        except: pass
        cands.append((m, pct, poisoned))

    if not cands: return False

    if CURE_FIRST:
        for m, pct, poisoned in cands:
            if poisoned and _cast("Cure", m.Serial):
                return True

    low = [t for t in cands if t[1] < HEAL_THRESHOLD_PCT]
    low.sort(key=lambda t: t[1])
    for m, pct, poisoned in low:
        if poisoned:
            if _cast("Cure", m.Serial): return True
        else:
            if _cast("Greater Heal", m.Serial): return True

    return False

# Monitoring System (DO NOT EDIT)
_summons = {}
_recent_candidates = {}
_tick = 0

def scan_and_update():
    global _tick
    _tick += 1

    mobs = _scan_friendlies()
    seen = set()

    for m in mobs:
        if not m: continue

        accepted = False
        if _owned_by_tag(m):
            accepted = True
        else:
            raw = (m.Name or ""); clean = _clean_name(raw)
            looks_like = ("(summoned)" in raw.lower()) or _props_contain(m, ["(summoned)","summoned creature","(familiar)"]) or any(b in clean for b in BASE_SUMMON_NAMES)
            if looks_like:
                if m.Serial not in _recent_candidates and _dist_to_player(m) <= 8:
                    _try_autotag(m)
                    _recent_candidates[m.Serial] = _tick + GRACE_TICKS
                if _owned_by_tag(m) or (_recent_candidates.get(m.Serial, 0) >= _tick):
                    accepted = True

        if not accepted: continue
        seen.add(m.Serial)

        tl = _extract_timeleft_from_props(m)
        prev_name = _summons.get(m.Serial, {}).get("name")
        resolved_name = _resolve_name(m, prev_name)

        if m.Serial not in _summons:
            _summons[m.Serial] = {
                "name": resolved_name or prev_name or "???",
                "last": getattr(m, "Hits", 0),
                "max":  getattr(m, "HitsMax", 0),
                "miss": 0,
                "seen_tick": _tick,
                "tl_secs": tl
            }
        else:
            e = _summons[m.Serial]
            if resolved_name: e["name"] = resolved_name
            if hasattr(m, "HitsMax") and m.HitsMax > 0:
                e["last"] = m.Hits; e["max"]  = m.HitsMax
            e["miss"] = 0; e["seen_tick"] = _tick
            if tl is not None: e["tl_secs"] = tl

    to_del = []
    for s, e in _summons.items():
        if s not in seen:
            e["miss"] = e.get("miss", 0) + 1
            if e["miss"] >= OUT_OF_RANGE_TICKS:
                to_del.append(s)
    for s in to_del: _summons.pop(s, None)

    for s, till in list(_recent_candidates.items()):
        if till < _tick: _recent_candidates.pop(s, None)

# UI (DO NOT EDIT)
def _draw_bar(gd, x, y, width, pct, hue_fill, hue_bg=BAR_HUE_BG):
    segs = max(1, width // BAR_SEG_W); filled = int(round(pct * segs))
    for i in range(segs): Gumps.AddImage(gd, x + i*BAR_SEG_W, y, BAR_SEG_ART, hue_bg)
    for i in range(filled): Gumps.AddImage(gd, x + i*BAR_SEG_W, y, BAR_SEG_ART, hue_fill)

def render_gump():
    rows = []
    for s, e in _summons.items():
        mx = max(0, e.get("max", 0)); cur = max(0, e.get("last", 0))
        frac = (float(cur)/mx) if mx > 0 else 0.0
        rows.append((s, e.get("name",""), cur, mx, frac, e.get("tl_secs")))
    rows.sort(key=lambda it: it[4])

    Gumps.CloseGump(GUMP_ID)

    width  = 320
    height = 40 + ROW_HEIGHT * len(rows)

    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)
    Gumps.AddBackground(gd, 0, 0, width, height, 30546)
    Gumps.AddAlphaRegion(gd, 0, 0, width, height)

    Gumps.AddLabel(gd, 90, 6, 0x0035, f"Summon Monitor v{VERSION}")

    Gumps.AddButton(gd, 8, 4, 4017, 4018, TOGGLE_BUTTON_ID, 1, 0)
    label = "Pause" if _RUNTIME_AUTO_SUPPORT else "Start"
    hue   = 0x0044 if _RUNTIME_AUTO_SUPPORT else 0x0025
    Gumps.AddLabel(gd, 32, 6, hue, label)

    for i, (serial, name_raw, cur, mx, frac, tl) in enumerate(rows):
        y = 34 + ROW_HEIGHT * i
        nm  = _proper(_clean_name(name_raw)) or "???"
        hue = _health_hue(cur, mx)
        pct = int(round(frac * 100)) if mx > 0 else 0

        try:
            Gumps.AddButton(gd, 4, y+1, 0x0846, 0x0846, int(serial), 1, 0)
        except:
            pass

        Gumps.AddLabel(gd, 20, y, 0x0481, nm)
        bar_x = 116
        _draw_bar(gd, bar_x, y+1, BAR_W, frac, hue)
        Gumps.AddLabel(gd, bar_x + BAR_W + 6, y, hue, f"{pct:>3d}%")
        tl_txt = _fmt_timeleft(tl)
        if tl_txt:
            Gumps.AddLabel(gd, bar_x + BAR_W + 48, y, 0x0035, tl_txt)

    Gumps.SendGump(GUMP_ID, Player.Serial, GUMP_POS[0], GUMP_POS[1], gd.gumpDefinition, gd.gumpStrings)

# MAIN
Misc.SendMessage("Frogs' Summon Monitor running…", 0x44)

while Player.Connected:
    gd = Gumps.GetGumpData(GUMP_ID)
    if gd and gd.buttonid:
        if gd.buttonid == TOGGLE_BUTTON_ID:
            _RUNTIME_AUTO_SUPPORT = not _RUNTIME_AUTO_SUPPORT
            hue = 68 if _RUNTIME_AUTO_SUPPORT else 33
            txt = "Auto Support ENABLED" if _RUNTIME_AUTO_SUPPORT else "Auto Support DISABLED"
            Misc.SendMessage(txt, hue)
        else:
            m = Mobiles.FindBySerial(gd.buttonid)
            if m:
                Mobiles.UseMobile(m.Serial)

    scan_and_update()
    _maybe_support()
    render_gump()

    Misc.Pause(REFRESH_MS)

_summons.clear()
_recent_candidates.clear()
Gumps.CloseGump(GUMP_ID)
Misc.SendMessage("Summon Monitor stopped.", 33)



