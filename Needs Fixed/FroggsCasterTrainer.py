# ============================================
# UO Script Forge — Caster Trainer (RE Python)
# Targets: Training House (Amado) | Newbie Dungeon (Rico)
# Modes: Resist | Magery | Hybrid
# ============================================
# Layout: config → helpers → flows → gump → main
# ============================================

from System.Collections.Generic import List

# ------------- [ CONFIGURATION ] -------------
GUMP_ID                = 0xB01DC0DE
REFRESH_MS             = 900
STATLINE_H             = 18

LOC_TRAINING_HOUSE     = "Training House"    # Amado (regen dummy)
LOC_NEWBIE_DUNGEON     = "Newbie Dungeon"    # Rico  (regen dummy)

# Serial placeholders (set via gump; paste known values if you have them)
SERIAL_AMADO           = 0    # e.g., 0x01234567
SERIAL_RICO            = 0    # e.g., 0x089ABCDE

# Safety thresholds
MIN_SAFE_HITS          = 46
HEAL_THRESHOLD         = 50
MEDITATE_TO_MANA       = 75
TARGET_TIMEOUT_MS      = 3000

# Magery ladder thresholds (from your CE)
LADDER1_CAP            = 46.5   # Lightning until 46.5
LADDER2_CAP            = 75.0   # Invisibility to 75
LADDER3_CAP            = 89.3   # Flamestrike to 89.3
LADDER4_CAP            = 100.0  # Summon Water Elemental to 100

# Mana gates (shard‑agnostic)
MANA_LIGHTNING         = 12
MANA_INVIS             = 21
MANA_FS                = 40
MANA_WATER_ELEM        = 50

# Hybrid cadence
HYBRID_FS_INTERVAL     = 2       # Every N magery actions, inject one FS‑self

# ------------- [ RUNTIME FLAGS ] -------------
RUNNING                = False
MODE                   = "MAGERY"     # RESIST | MAGERY | HYBRID
ACTIVE_LOCATION        = LOC_TRAINING_HOUSE

# Optional: explicit FS target (overrides dummy for FS if set)
FS_TARGET_SERIAL       = 0

# ============================================
#                 HELPERS
# ============================================

def _msg(s, hue=68):
    try: Misc.SendMessage(s, hue)
    except: pass

def _is_connected():
    try: return Player.Connected
    except: return False

def _meditating():
    try:
        return Buffs.GetBuffIcon("Actively Meditating") or Buffs.GetBuffIcon("Meditation")
    except:
        try: return Player.BuffsExist("Actively Meditating")
        except: return False

def _use_skill(name):
    try:
        Player.UseSkill(name); return True
    except:
        try: Skills.UseSkill(name); return True
        except:
            _msg("Skill call failed: " + name, 33); return False

def _cast(spell_name):
    try:
        Spells.Cast(spell_name); return True
    except:
        try:
            Spells.CastMagery(spell_name); return True
        except:
            try:
                Spells.CastSpell(spell_name); return True
            except:
                _msg("Cast failed: " + spell_name, 33); return False

def _target_self():
    try:
        if Target.HasTarget():
            Target.Self(); return True
        if Target.WaitForTarget(TARGET_TIMEOUT_MS, False):
            Target.TargetExecute(Player.Serial); return True
    except: pass
    return False

def _target_serial(sn):
    try:
        if not sn: return False
        if Target.HasTarget():
            Target.TargetExecute(sn); return True
        if Target.WaitForTarget(TARGET_TIMEOUT_MS, False):
            Target.TargetExecute(sn); return True
    except: pass
    return False

def _ensure_mana(min_mana, burst_ms=10000):
    if Player.Mana >= min_mana: return True
    if not _meditating():
        _use_skill("Meditation"); Misc.Pause(1000)
    waited = 0
    goal = max(min_mana, MEDITATE_TO_MANA)
    while Player.Mana < goal and _is_connected():
        Misc.Pause(400); waited += 400
        if waited > burst_ms: break
    return Player.Mana >= min_mana

def _get_skill_val(skill_name):
    try:    return float(Skills.GetSkillValue(skill_name))
    except:
        try: return float(Player.GetSkillValue(skill_name))
        except: return 0.0

def _say(s):
    try: Player.ChatSay(s)
    except:
        try: Misc.Say(s)
        except: pass

def _prompt_serial(prompt_txt):
    try: return Target.PromptTarget(prompt_txt)
    except:
        _msg(prompt_txt, 88); return 0

def _active_dummy_serial():
    return SERIAL_AMADO if ACTIVE_LOCATION == LOC_TRAINING_HOUSE else SERIAL_RICO

# ---------- Robust button reader (works across RE builds) ----------
def read_button():
    """
    Return last pressed button id for our gump, or 0 if none.
    Tries several APIs and finally parses the raw buffer.
    """
    # 1) Preferred: GetGumpButton
    try:
        bid = Gumps.GetGumpButton(GUMP_ID)
        if isinstance(bid, int) and bid > 0:
            return bid
    except: pass

    # 2) Older alias: LastButton
    try:
        bid = Gumps.LastButton()
        if isinstance(bid, int) and bid > 0:
            return bid
    except: pass

    # 3) Another alias some builds have
    try:
        bid = Gumps.GetButton(GUMP_ID)
        if isinstance(bid, int) and bid > 0:
            return bid
    except: pass

    # 4) Fallback: parse raw gump data
    try:
        raw = Gumps.LastGumpRawData()
        import re
        m = re.search(r'buttonid[: ]\s*(\d+)', raw)
        if not m:
            m = re.search(r'\{\s*button\s+(\d+)\s*\}', raw)
        if m:
            return int(m.group(1))
    except: pass

    return 0

# ============================================
#               SPELL SHORTCUTS
# ============================================

def cast_greater_heal_self():
    if not _ensure_mana(12): return False
    if not _cast("Greater Heal"): return False
    Target.WaitForTarget(TARGET_TIMEOUT_MS, False)
    _target_self(); Misc.Pause(350); return True

def cast_lightning_on_dummy():
    if not _ensure_mana(MANA_LIGHTNING): return False
    if not _cast("Lightning"): return False
    Target.WaitForTarget(TARGET_TIMEOUT_MS, False)
    sn = _active_dummy_serial()
    if not _target_serial(sn): _target_self()
    Misc.Pause(800); return True

def cast_invisibility_self():
    if not _ensure_mana(MANA_INVIS): return False
    if not _cast("Invisibility"): return False
    Target.WaitForTarget(TARGET_TIMEOUT_MS, False)
    _target_self(); Misc.Pause(800); return True

def cast_flamestrike(target_override_sn=0):
    if not _ensure_mana(MANA_FS): return False
    if not (_cast("Flamestrike") or _cast("Flame Strike")): return False
    Target.WaitForTarget(TARGET_TIMEOUT_MS, False)
    sn = target_override_sn or FS_TARGET_SERIAL or _active_dummy_serial()
    # For resist mode we pass 0 to force self; elsewhere prefer dummy if set
    if sn: _target_serial(sn)
    else:  _target_self()
    Misc.Pause(800); return True

def cast_water_elemental():
    if not _ensure_mana(MANA_WATER_ELEM): return False
    if not _cast("Summon Water Elemental"): return False
    Misc.Pause(500); return True

def release_water_elemental():
    _say("all release"); Misc.Pause(300)
    _say("a water elemental release"); Misc.Pause(300)

# ============================================
#                   FLOWS
# ============================================

def flow_resist_only():
    # Heal if needed
    if Player.Hits < HEAL_THRESHOLD and Player.Mana > 11:
        cast_greater_heal_self(); Misc.Pause(350); return
    # Meditate if low
    if Player.Mana < 50 and not _meditating():
        _use_skill("Meditation"); Misc.Pause(1000); return
    # FS self while safe
    if Player.Hits > MIN_SAFE_HITS and Player.Mana > MANA_FS:
        cast_flamestrike(0)  # 0 forces self
        Misc.Pause(400); return

def flow_magery_only():
    m = _get_skill_val("Magery")

    if m < LADDER1_CAP:
        cast_lightning_on_dummy(); return

    if m < LADDER2_CAP:
        cast_invisibility_self(); return

    if m < LADDER3_CAP:
        cast_flamestrike(_active_dummy_serial()); return

    if m < LADDER4_CAP:
        if Player.Mana >= MANA_WATER_ELEM:
            cast_water_elemental()
        release_water_elemental(); return

def flow_hybrid():
    cnt = Misc.ReadSharedValue("cs_hybrid_cnt") if Misc.CheckSharedValue("cs_hybrid_cnt") else 0

    if Player.Hits < HEAL_THRESHOLD and Player.Mana > 11:
        cast_greater_heal_self(); Misc.Pause(350); return

    if cnt % HYBRID_FS_INTERVAL == 0 and Player.Hits > MIN_SAFE_HITS and Player.Mana > MANA_FS:
        cast_flamestrike(0)  # self for resist
        cnt += 1; Misc.SetSharedValue("cs_hybrid_cnt", cnt); return

    flow_magery_only()
    cnt += 1; Misc.SetSharedValue("cs_hybrid_cnt", cnt)

# ============================================
#                   GUMP
# ============================================

# Button IDs
BTN_START   = 1001
BTN_STOP    = 1002
BTN_RESIST  = 1102
BTN_MAGERY  = 1103
BTN_HYBRID  = 1104
BTN_THOUSE  = 1301
BTN_NDUNG   = 1302
BTN_SET_AM  = 1201
BTN_SET_RI  = 1202
BTN_SET_FS  = 1401

def render_gump():
    # Build & send gump (reply buttons, no paging)
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)

    mag = _get_skill_val("Magery")
    lbl_run  = "RUNNING" if RUNNING else "STOPPED"
    dims_w   = 340
    rows     = 14

    Gumps.AddBackground(gd, 0, 0, dims_w, 10 + STATLINE_H*rows, 30546)
    Gumps.AddAlphaRegion(gd, 0, 0, dims_w, 10 + STATLINE_H*rows)

    y = 6
    Gumps.AddLabel(gd, 10, y, 0x47E, f"Caster Trainer  •  {lbl_run}"); y += STATLINE_H
    Gumps.AddLabel(gd, 10, y, 0x480, f"Mode: {MODE}"); y += STATLINE_H
    Gumps.AddLabel(gd, 10, y, 0x480, f"Location: {ACTIVE_LOCATION}"); y += STATLINE_H
    Gumps.AddLabel(gd, 10, y, 0x44F, f"Magery: {mag:.1f}"); y += STATLINE_H
    Gumps.AddLabel(gd, 10, y, 0x44F, f"HP/Mana/Stam: {Player.Hits}/{Player.Mana}/{Player.Stam}"); y += STATLINE_H

    # Start / Stop (type=0 reply)
    Gumps.AddButton(gd, 10,  y, 4005, 4007, BTN_START, 0, 0); Gumps.AddLabel(gd, 35,  y, 0x35, "Start")
    Gumps.AddButton(gd, 80,  y, 4017, 4019, BTN_STOP,  0, 0); Gumps.AddLabel(gd, 105, y, 0x20, "Stop")
    y += STATLINE_H

    # Modes
    Gumps.AddButton(gd, 10,  y, 4005, 4007, BTN_RESIST, 0, 0); Gumps.AddLabel(gd, 35,  y, 0x47E, "Resist")
    Gumps.AddButton(gd, 140, y, 4005, 4007, BTN_MAGERY, 0, 0); Gumps.AddLabel(gd, 165, y, 0x47E, "Magery")
    Gumps.AddButton(gd, 240, y, 4005, 4007, BTN_HYBRID, 0, 0); Gumps.AddLabel(gd, 265, y, 0x47E, "Hybrid")
    y += STATLINE_H

    # Location select
    Gumps.AddLabel(gd, 10, y, 0x44F, "Training Target:"); y += STATLINE_H
    Gumps.AddButton(gd, 10,  y, 4005, 4007, BTN_THOUSE, 0, 0); Gumps.AddLabel(gd, 35,  y, 0x47E, f"{LOC_TRAINING_HOUSE}  [{hex(SERIAL_AMADO) if SERIAL_AMADO else 'unset'}]")
    y += STATLINE_H
    Gumps.AddButton(gd, 10,  y, 4005, 4007, BTN_NDUNG,  0, 0); Gumps.AddLabel(gd, 35,  y, 0x47E, f"{LOC_NEWBIE_DUNGEON} [{hex(SERIAL_RICO) if SERIAL_RICO else 'unset'}]")
    y += STATLINE_H

    # Set serials
    Gumps.AddButton(gd, 10,  y, 4005, 4007, BTN_SET_AM, 0, 0); Gumps.AddLabel(gd, 35,  y, 0x47E, "Set Amado Serial")
    Gumps.AddButton(gd, 180, y, 4005, 4007, BTN_SET_RI, 0, 0); Gumps.AddLabel(gd, 205, y, 0x47E, "Set Rico Serial")
    y += STATLINE_H

    # Optional FS target override
    Gumps.AddButton(gd, 10,  y, 4005, 4007, BTN_SET_FS, 0, 0); Gumps.AddLabel(gd, 35,  y, 0x47E, f"Set FS Target [{hex(FS_TARGET_SERIAL) if FS_TARGET_SERIAL else 'location/self'}]")
    y += STATLINE_H

    Gumps.SendGump(GUMP_ID, Player.Serial, 50, 50, gd.gumpDefinition, gd.gumpStrings)

def handle_gump_buttons():
    global RUNNING, MODE, ACTIVE_LOCATION, SERIAL_AMADO, SERIAL_RICO, FS_TARGET_SERIAL

    btn = read_button()
    if not btn:
        return

    if btn == BTN_START: RUNNING = True
    elif btn == BTN_STOP: RUNNING = False

    elif btn == BTN_RESIST: MODE = "RESIST"
    elif btn == BTN_MAGERY: MODE = "MAGERY"
    elif btn == BTN_HYBRID: MODE = "HYBRID"

    elif btn == BTN_THOUSE: ACTIVE_LOCATION = LOC_TRAINING_HOUSE
    elif btn == BTN_NDUNG:  ACTIVE_LOCATION = LOC_NEWBIE_DUNGEON

    elif btn == BTN_SET_AM:
        SERIAL_AMADO = _prompt_serial("Target AMADO (Training House)")
        _msg("Amado set to " + (hex(SERIAL_AMADO) if SERIAL_AMADO else "unset"))
    elif btn == BTN_SET_RI:
        SERIAL_RICO = _prompt_serial("Target RICO (Newbie Dungeon)")
        _msg("Rico set to " + (hex(SERIAL_RICO) if SERIAL_RICO else "unset"))

    elif btn == BTN_SET_FS:
        FS_TARGET_SERIAL = _prompt_serial("Target for Flamestrike (ESC for location/self)")
        if not FS_TARGET_SERIAL: _msg("FS Target: cleared (use location/self)")
        else: _msg("FS Target set: " + hex(FS_TARGET_SERIAL))

    # after any click, redraw once so UI reflects changes
    try: Gumps.CloseGump(GUMP_ID)
    except: pass
    render_gump()

# ============================================
#                    MAIN
# ============================================

def main():
    _msg("Caster Trainer (Amado/Rico) loaded.", 88)

    # Initial draw
    render_gump()
    tick = 0

    while _is_connected():
        # 1) Process any click that happened since last loop
        handle_gump_buttons()

        # 2) Do work if running
        if RUNNING:
            if MODE == "RESIST":
                flow_resist_only()
            elif MODE == "MAGERY":
                flow_magery_only()
            elif MODE == "HYBRID":
                flow_hybrid()

        # 3) Light periodic refresh so stats update even without clicks
        tick += 1
        if tick % 5 == 0:
            try: Gumps.CloseGump(GUMP_ID)
            except: pass
            render_gump()
            tick = 0

        Misc.Pause(REFRESH_MS)

# Kickoff
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        _msg("Caster Trainer stopped: " + str(e), 33)
