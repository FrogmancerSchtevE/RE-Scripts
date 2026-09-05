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
# But please don't upload, re-ingest, or recycle it into LLMs.
#
# Contribute your own creativity instead - that's how we built this.
#

import time

# ===========================================================
# CONFIGURATION
# ===========================================================

BANDAGE_ITEMID = 0x0E21
BANDAGE_HUE = -1

HEAL_BELOW_PCT = 0.86
PRIORITIZE_POISON = True
MAX_TARGET_RANGE = 2

BANDAGE_WAIT_MS = 1600
BANDAGE_DISPLAY_SECONDS = 4
BANDAGE_DISPLAY_MS = BANDAGE_DISPLAY_SECONDS * 1000

LOOP_IDLE_MS = 120
REFRESH_MS = 500
BUTTON_DEBOUNCE_MS = 200

MSG_COLOR = 68
WARN_COLOR = 53
ERR_COLOR = 33
OK_COLOR = 76

VETKIT_ITEMID = 0x6B93
VETKIT_HP_THRESHOLD = 0.75
VETKIT_PROP_WAIT_MS = 500
VETKIT_REFRESH_MS = 3000
VETKIT_RETRY_MS = 1500
VETKIT_RESULT_WAIT_MS = 750
VETKIT_NO_PETS_MESSAGE = "There are no injured pets nearby"

OUT_OF_BANDAGE_ALERT_MS = 10000

# ===========================================================
# GUI CONFIGURATION
# ===========================================================

GUMP_ID = 0xF2065632
GUI_ENABLED = True
DEFAULT_GUMP_POS = (650, 650)

GUMP_W = 350
BG_ART = 9270

ROW_H = 20
LEFT_PAD = 8

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
PET_SEG_W = 14

PET_LABEL_X = 8
PET_NAME_X = 32
PET_BAR_X = 192
PET_ROW_H = 24

BAND_SEGMENTS = PET_SEGMENTS
BAND_SEG_W = PET_SEG_W

COL_LABEL_X = LEFT_PAD
COL_VAL_X = LEFT_PAD + 85
COL_BAR_X = PET_BAR_X
VET_USES_VALUE_X = LEFT_PAD + 100

PAGE_MAIN = 0
PAGE_CONFIG = 1

# ===========================================================
# BUTTON IDS
# ===========================================================

BTN_TOGGLE_PAUSE = 9998
BTN_CONFIG = 9999
BTN_BACK = 9997
BTN_CLEAR_ALL = 9996
BTN_CYCLE_HEAL_MODE = 9995

BTN_SET_BASE = 9100
BTN_CLEAR_BASE = 9200

# ===========================================================
# PET SLOT STORAGE
# ===========================================================

MAX_PET_SLOTS = 5

PET_SERIAL_KEYS = [
    "froggeVet_Pet1_Serial",
    "froggeVet_Pet2_Serial",
    "froggeVet_Pet3_Serial",
    "froggeVet_Pet4_Serial",
    "froggeVet_Pet5_Serial",
]

PET_NAME_KEYS = [
    "froggeVet_Pet1_Name",
    "froggeVet_Pet2_Name",
    "froggeVet_Pet3_Name",
    "froggeVet_Pet4_Name",
    "froggeVet_Pet5_Name",
]

HEAL_MODE_KEY = "froggeVet_HealMode"
HEAL_MODE_BOTH = 0
HEAL_MODE_BANDAGES = 1
HEAL_MODE_VETKITS = 2

PET_SERIALS = [0, 0, 0, 0, 0]
PET_NAMES = ["", "", "", "", ""]

# ===========================================================
# GLOBAL STATE
# ===========================================================

PAUSED = False
HEAL_MODE = HEAL_MODE_BOTH

_current_page = PAGE_MAIN
_dirty_ui = True

last_bandage_alert = 0

_activity_status = "Starting..."
_activity_hue = HUE_TXT
_heal_kind = ""
_heal_target_name = ""

_vetkit_charge_cache = {}
_vetkit_charges = 0
_vetkit_unread = 0
_last_vetkit_refresh = 0
_last_vetkit_attempt = 0

# ===========================================================
# UTILITIES
# ===========================================================

def now_ms():
    return int(time.time() * 1000)


def msg(text, color=MSG_COLOR):
    Misc.SendMessage(text, color)


def safe_getattr(obj, name, default=None):
    try:
        return getattr(obj, name)
    except:
        return default


def set_activity(text, hue=HUE_TXT):
    global _activity_status
    global _activity_hue
    global _dirty_ui

    text = str(text or "")

    if text == _activity_status and hue == _activity_hue:
        return

    _activity_status = text
    _activity_hue = hue
    _dirty_ui = True


def pet_name(pet):
    return str(safe_getattr(pet, "Name", "Pet") or "Pet")

# ===========================================================
# HEALING MODE
# ===========================================================

def heal_mode_label():
    if HEAL_MODE == HEAL_MODE_BANDAGES:
        return "Bandages Only"

    if HEAL_MODE == HEAL_MODE_VETKITS:
        return "Vet Kits Only"

    return "Both"


def load_heal_mode():
    global HEAL_MODE

    HEAL_MODE = HEAL_MODE_BOTH

    if not Misc.CheckSharedValue(HEAL_MODE_KEY):
        return

    try:
        saved_mode = int(Misc.ReadSharedValue(HEAL_MODE_KEY))
    except:
        return

    if saved_mode in (HEAL_MODE_BOTH, HEAL_MODE_BANDAGES, HEAL_MODE_VETKITS):
        HEAL_MODE = saved_mode


def cycle_heal_mode():
    global HEAL_MODE

    HEAL_MODE = (HEAL_MODE + 1) % 3
    Misc.SetSharedValue(HEAL_MODE_KEY, HEAL_MODE)
    set_activity("Healing mode: %s" % heal_mode_label(), HUE_GOOD)
    msg("FroggeVet healing mode: %s" % heal_mode_label(), OK_COLOR)


def mode_uses_bandages():
    return HEAL_MODE in (HEAL_MODE_BOTH, HEAL_MODE_BANDAGES)


def mode_uses_vetkits():
    return HEAL_MODE in (HEAL_MODE_BOTH, HEAL_MODE_VETKITS)

# ===========================================================
# BANDAGE TIMER
# ===========================================================

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

    return start and length and now_ms() < start + length


def bandage_time_left_ms():
    start = Misc.ReadSharedValue(HUD_BAND_START_KEY) if Misc.CheckSharedValue(HUD_BAND_START_KEY) else 0
    length = Misc.ReadSharedValue(HUD_BAND_LEN_KEY) if Misc.CheckSharedValue(HUD_BAND_LEN_KEY) else 0

    return max(0, (start + length) - now_ms()) if start and length else 0


def healing_in_progress():
    return bandage_running()


def start_heal_timer(kind, pet=None):
    global _heal_kind
    global _heal_target_name

    _heal_kind = str(kind or "Healing")
    _heal_target_name = pet_name(pet) if pet else ""

    set_bandage_timer(now_ms(), BANDAGE_DISPLAY_MS)

    if _heal_target_name:
        set_activity("Using %s on %s - waiting to heal" % (_heal_kind.lower(), _heal_target_name), HUE_GOOD)
    else:
        set_activity("Using %s - healing nearby pets" % _heal_kind.lower(), HUE_GOOD)

# ===========================================================
# INVENTORY HELPERS
# ===========================================================

def get_item_in_subbags(itemid, hue=-1):
    itm = Items.FindByID(itemid, hue, Player.Backpack.Serial)

    if itm:
        return itm

    for cont in Player.Backpack.Contains or []:
        itm = Items.FindByID(itemid, hue, cont.Serial)

        if itm:
            return itm

    return None


def count_in_subbags(itemid, hue=-1):
    try:
        return Items.BackpackCount(itemid, hue)
    except:
        return 0


def get_bandage():
    return get_item_in_subbags(BANDAGE_ITEMID, BANDAGE_HUE)


def get_vetkits():
    try:
        return list(Items.FindAllByID(VETKIT_ITEMID, -1, Player.Backpack.Serial, True) or [])
    except:
        pass

    kits = []
    pending = [Player.Backpack]
    seen = {}

    while pending:
        container = pending.pop()

        for item in safe_getattr(container, "Contains", None) or []:
            serial = int(safe_getattr(item, "Serial", 0) or 0)

            if serial <= 0 or serial in seen:
                continue

            seen[serial] = True

            if safe_getattr(item, "ItemID", 0) == VETKIT_ITEMID:
                kits.append(item)

            if safe_getattr(item, "Contains", None):
                pending.append(item)

    return kits


def read_vetkit_uses(kit):
    try:
        Items.WaitForProps(kit.Serial, VETKIT_PROP_WAIT_MS)
        lines = Items.GetPropStringList(kit.Serial)
    except:
        return None

    for raw_line in lines or []:
        line = str(raw_line).strip()
        lower_line = line.lower()
        marker = "uses remaining"
        marker_index = lower_line.find(marker)

        if marker_index < 0:
            continue

        digits = ""
        value_started = False

        for char in line[marker_index + len(marker):]:
            if char.isdigit():
                digits += char
                value_started = True
            elif value_started:
                break

        if digits:
            return int(digits)

    return None


def refresh_vetkit_charges(force=False):
    global _vetkit_charge_cache
    global _vetkit_charges
    global _vetkit_unread
    global _last_vetkit_refresh

    current_time = now_ms()

    if not force and _last_vetkit_refresh and current_time - _last_vetkit_refresh < VETKIT_REFRESH_MS:
        return

    total = 0
    unread = 0
    new_cache = {}

    for kit in get_vetkits():
        serial = int(safe_getattr(kit, "Serial", 0) or 0)
        uses = read_vetkit_uses(kit)

        if uses is None and serial in _vetkit_charge_cache:
            uses = _vetkit_charge_cache[serial]

        if uses is None:
            unread += 1
            continue

        uses = max(0, int(uses))
        total += uses
        new_cache[serial] = uses

    _vetkit_charge_cache = new_cache
    _vetkit_charges = total
    _vetkit_unread = unread
    _last_vetkit_refresh = current_time


def vetkit_charge_display():
    refresh_vetkit_charges()

    if _vetkit_unread > 0:
        return "%d+?" % _vetkit_charges

    return str(_vetkit_charges)


def note_vetkit_used(serial):
    global _vetkit_charges
    global _last_vetkit_refresh

    serial = int(serial or 0)

    if serial in _vetkit_charge_cache and _vetkit_charge_cache[serial] > 0:
        _vetkit_charge_cache[serial] -= 1
        _vetkit_charges = max(0, _vetkit_charges - 1)

    _last_vetkit_refresh = now_ms()

# ===========================================================
# PET SLOT HELPERS
# ===========================================================

def load_pet_slots():
    for slot in range(MAX_PET_SLOTS):
        serial = 0
        name = ""

        if Misc.CheckSharedValue(PET_SERIAL_KEYS[slot]):
            try:
                serial = int(Misc.ReadSharedValue(PET_SERIAL_KEYS[slot]) or 0)
            except:
                serial = 0

        if Misc.CheckSharedValue(PET_NAME_KEYS[slot]):
            try:
                name = str(Misc.ReadSharedValue(PET_NAME_KEYS[slot]) or "")
            except:
                name = ""

        PET_SERIALS[slot] = serial
        PET_NAMES[slot] = name

        if serial > 0 and not name:
            pet = Mobiles.FindBySerial(serial)

            if pet:
                recovered_name = safe_getattr(pet, "Name", "") or ""

                if recovered_name:
                    PET_NAMES[slot] = recovered_name
                    Misc.SetSharedValue(PET_NAME_KEYS[slot], recovered_name)


def save_pet_slot(slot, serial, name):
    PET_SERIALS[slot] = int(serial)
    PET_NAMES[slot] = str(name or "Pet")

    Misc.SetSharedValue(PET_SERIAL_KEYS[slot], PET_SERIALS[slot])
    Misc.SetSharedValue(PET_NAME_KEYS[slot], PET_NAMES[slot])


def clear_pet_slot(slot):
    PET_SERIALS[slot] = 0
    PET_NAMES[slot] = ""

    if Misc.CheckSharedValue(PET_SERIAL_KEYS[slot]):
        Misc.RemoveSharedValue(PET_SERIAL_KEYS[slot])

    if Misc.CheckSharedValue(PET_NAME_KEYS[slot]):
        Misc.RemoveSharedValue(PET_NAME_KEYS[slot])

    set_activity("Pet slot %d cleared" % (slot + 1), HUE_WARN)
    msg("Pet slot %d cleared." % (slot + 1), WARN_COLOR)


def clear_all_pet_slots():
    Target.Cancel()

    for slot in range(MAX_PET_SLOTS):
        PET_SERIALS[slot] = 0
        PET_NAMES[slot] = ""

        if Misc.CheckSharedValue(PET_SERIAL_KEYS[slot]):
            Misc.RemoveSharedValue(PET_SERIAL_KEYS[slot])

        if Misc.CheckSharedValue(PET_NAME_KEYS[slot]):
            Misc.RemoveSharedValue(PET_NAME_KEYS[slot])

    set_activity("Waiting - configure a pet", HUE_WARN)
    msg("All FroggeVet pet slots cleared.", WARN_COLOR)


def configured_slots():
    slots = []

    for slot in range(MAX_PET_SLOTS):
        if PET_SERIALS[slot] > 0:
            slots.append(slot)

    return slots


def configured_pet_count():
    return len(configured_slots())


def valid_pet(m):
    return bool(m and not safe_getattr(m, "IsGhost", True) and safe_getattr(m, "HitsMax", 0) > 0)


def hp_pct(m):
    hits_max = float(safe_getattr(m, "HitsMax", 0) or 0)

    if hits_max <= 0:
        return 0.0

    return float(safe_getattr(m, "Hits", 0) or 0) / hits_max


def pet_in_range(m, max_range):
    if not m:
        return False

    if max_range is None:
        return True

    try:
        return int(m.Distance) <= int(max_range)
    except:
        return True


def get_pet_by_slot(slot, max_range=None, refresh_status=False):
    if slot < 0 or slot >= MAX_PET_SLOTS:
        return None

    serial = PET_SERIALS[slot]

    if serial <= 0:
        return None

    pet = Mobiles.FindBySerial(serial)

    if not pet:
        return None

    if refresh_status:
        try:
            Mobiles.GetStatus(pet)
        except:
            pass

    if not valid_pet(pet):
        return None

    if not pet_in_range(pet, max_range):
        return None

    return pet


def set_pet_slot(slot):
    if slot < 0 or slot >= MAX_PET_SLOTS:
        return

    Target.Cancel()
    Gumps.CloseGump(GUMP_ID)

    msg("Target pet for slot %d. ESC cancels." % (slot + 1), MSG_COLOR)

    serial = Target.PromptTarget("Select Pet %d" % (slot + 1))

    if serial <= 0:
        set_activity("Pet setup cancelled", HUE_WARN)
        msg("Pet selection cancelled.", WARN_COLOR)
        return

    for other_slot in range(MAX_PET_SLOTS):
        if other_slot != slot and PET_SERIALS[other_slot] == serial:
            set_activity("Pet is already stored in slot %d" % (other_slot + 1), HUE_WARN)
            msg("That pet is already stored in slot %d." % (other_slot + 1), ERR_COLOR)
            return

    pet = Mobiles.FindBySerial(serial)

    if pet:
        try:
            Mobiles.GetStatus(pet)
            Misc.Pause(100)
        except:
            pass

    if not valid_pet(pet):
        set_activity("Pet setup failed - invalid target", HUE_BAD)
        msg("Invalid pet selected.", ERR_COLOR)
        return

    selected_name = safe_getattr(pet, "Name", "Pet") or "Pet"

    save_pet_slot(slot, pet.Serial, selected_name)

    set_activity("Pet %d configured: %s" % (slot + 1, selected_name), HUE_GOOD)
    Player.HeadMessage(OK_COLOR, "Pet %d set: %s" % (slot + 1, selected_name))
    msg("FroggeVet slot %d stored: %s" % (slot + 1, selected_name), OK_COLOR)

# ===========================================================
# HEALING
# ===========================================================

def use_vetkit():
    global _last_vetkit_attempt

    if healing_in_progress():
        return False

    current_time = now_ms()

    if _last_vetkit_attempt and current_time - _last_vetkit_attempt < VETKIT_RETRY_MS:
        return False

    _last_vetkit_attempt = current_time

    kits = get_vetkits()
    kit = kits[0] if kits else None

    if not kit:
        set_activity("No vet kits available", HUE_BAD)
        return False

    Journal.Clear()
    Items.UseItem(kit)
    start_heal_timer("vet kit")
    Misc.Pause(VETKIT_RESULT_WAIT_MS)

    if Journal.Search(VETKIT_NO_PETS_MESSAGE):
        set_activity("FrogVet found no injured pets in range", HUE_WARN)
        return False

    note_vetkit_used(kit.Serial)

    return True


def bandage_target(pet):
    global last_bandage_alert

    if not valid_pet(pet):
        return False

    if healing_in_progress():
        return False

    pet_serial = pet.Serial
    bandage = get_bandage()

    if not bandage:
        set_activity("Out of bandages for %s" % pet_name(pet), HUE_BAD)

        if now_ms() - last_bandage_alert > OUT_OF_BANDAGE_ALERT_MS:
            msg("Out of bandages!", ERR_COLOR)
            last_bandage_alert = now_ms()

        return False

    Journal.Clear()
    Target.Cancel()
    set_activity("Preparing bandage for %s" % pet_name(pet), HUE_TXT)
    Items.UseItem(bandage)

    if not Target.WaitForTarget(BANDAGE_WAIT_MS):
        set_activity("Bandage targeting timed out", HUE_WARN)
        return False

    fresh_pet = Mobiles.FindBySerial(pet_serial)

    if not valid_pet(fresh_pet):
        Target.Cancel()
        set_activity("Bandage cancelled - pet unavailable", HUE_WARN)
        return False

    if not pet_in_range(fresh_pet, MAX_TARGET_RANGE * 6):
        Target.Cancel()
        set_activity("Bandage cancelled - %s is out of range" % pet_name(fresh_pet), HUE_WARN)
        return False

    Target.TargetExecute(fresh_pet.Serial)
    start_heal_timer("bandage", fresh_pet)
    Misc.Pause(120)

    return True


def get_tracked_pets(max_range=30):
    pets = []

    for slot in configured_slots():
        pet = get_pet_by_slot(slot, max_range=max_range, refresh_status=True)

        if pet:
            pets.append(pet)

    return pets


def pick_target(pets=None):
    fresh = pets if pets is not None else get_tracked_pets(max_range=30)

    if PRIORITIZE_POISON:
        poisoned = []

        for pet in fresh:
            if safe_getattr(pet, "Poisoned", False):
                poisoned.append(pet)

        if poisoned:
            return min(poisoned, key=hp_pct)

    candidates = []

    for pet in fresh:
        if hp_pct(pet) < HEAL_BELOW_PCT:
            candidates.append(pet)

    if candidates:
        return min(candidates, key=hp_pct)

    return None


def toggle_pause():
    global PAUSED
    global _dirty_ui

    PAUSED = not PAUSED
    _dirty_ui = True

    if PAUSED:
        set_activity("Paused by user", HUE_WARN)
        msg("Vet Assistant paused.", WARN_COLOR)
    else:
        if healing_in_progress() and _heal_kind:
            if _heal_target_name:
                set_activity("Using %s on %s - waiting to heal" % (_heal_kind.lower(), _heal_target_name), HUE_GOOD)
            else:
                set_activity("Using %s - healing nearby pets" % _heal_kind.lower(), HUE_GOOD)
        else:
            set_activity("Resuming pet checks...", HUE_TXT)

        msg("Vet Assistant resumed.", OK_COLOR)

# ===========================================================
# GUMP / GUI HELPERS
# ===========================================================

def _health_hue(frac):
    if frac >= 0.75:
        return HUE_GOOD

    if frac >= 0.40:
        return HUE_WARN

    return HUE_BAD


def _draw_segments(gd, x, y, segments, seg_w, filled, hue_empty, hue_fill):
    for i in range(segments):
        Gumps.AddImage(gd, x + i * seg_w, y, SEG_ART, hue_empty)

    for i in range(min(segments, filled)):
        Gumps.AddImage(gd, x + i * seg_w, y, SEG_ART, hue_fill)


def _new_gump(height):
    gd = Gumps.CreateGump(movable=True)
    gd.gumpId = GUMP_ID
    gd.serial = Player.Serial

    Gumps.AddPage(gd, 0)
    Gumps.AddBackground(gd, 0, 0, GUMP_W, height, BG_ART)

    return gd

# ===========================================================
# MAIN PAGE
# ===========================================================

def render_main_page():
    slots = configured_slots()
    pet_count = len(slots)

    band_left_ms = bandage_time_left_ms()

    if Misc.CheckSharedValue(HUD_BAND_LEN_KEY):
        total_ms = Misc.ReadSharedValue(HUD_BAND_LEN_KEY)
    else:
        total_ms = BANDAGE_DISPLAY_MS

    bcount = count_in_subbags(BANDAGE_ITEMID, BANDAGE_HUE)
    vet_uses = vetkit_charge_display()

    gump_h = max(175, 132 + pet_count * PET_ROW_H)

    gd = _new_gump(gump_h)

    y = 6

    # -------------------------------------------------------
    # HEADER
    # -------------------------------------------------------

    Gumps.AddLabel(gd, LEFT_PAD, y, HUE_TITLE, "FroggeVet")

    Gumps.AddButton(gd, GUMP_W - 145, 6, 4017, 4018, BTN_CONFIG, 1, 0)
    Gumps.AddLabel(gd, GUMP_W - 120, 8, HUE_TXT, "Config")

    Gumps.AddButton(gd, GUMP_W - 70, 6, 4017, 4018, BTN_TOGGLE_PAUSE, 1, 0)
    Gumps.AddLabel(gd, GUMP_W - 45, 8, HUE_TXT, "Resume" if PAUSED else "Pause")

    y += ROW_H

    # -------------------------------------------------------
    # BANDAGE STATUS / TIMER
    # -------------------------------------------------------

    if band_left_ms <= 0:
        band_label = "ready"
        band_filled = 0
    else:
        band_label = "%.1fs" % (band_left_ms / 1000.0)
        elapsed_ms = max(0, total_ms - band_left_ms)
        band_filled = int((float(elapsed_ms) / float(total_ms)) * BAND_SEGMENTS) if total_ms > 0 else 0
        band_filled = max(0, min(BAND_SEGMENTS, band_filled))

    Gumps.AddLabel(gd, COL_LABEL_X, y, HUE_TXT, "State:")
    Gumps.AddLabel(gd, COL_VAL_X, y, HUE_TXT, band_label)

    _draw_segments(gd, COL_BAR_X, y + 6, BAND_SEGMENTS, BAND_SEG_W, band_filled, HUE_EMPTY, HUE_BAND_FILLED)

    y += ROW_H

    # -------------------------------------------------------
    # RESOURCE COUNTERS
    # -------------------------------------------------------

    Gumps.AddLabel(gd, COL_LABEL_X, y, HUE_TXT, "Bandies:")
    Gumps.AddLabel(gd, COL_VAL_X, y, HUE_BAD if bcount == 0 else HUE_TXT, str(bcount))

    y += ROW_H

    if _vetkit_unread > 0:
        vet_uses_hue = HUE_WARN
    elif _vetkit_charges <= 0:
        vet_uses_hue = HUE_BAD
    else:
        vet_uses_hue = HUE_TXT

    Gumps.AddLabel(gd, COL_LABEL_X, y, HUE_TXT, "Vet Kit Uses:")
    Gumps.AddLabel(gd, VET_USES_VALUE_X, y, vet_uses_hue, vet_uses)

    y += ROW_H + 2

    # -------------------------------------------------------
    # PET ROWS
    # -------------------------------------------------------

    if not slots:
        Gumps.AddLabel(gd, PET_LABEL_X, y, HUE_WARN, "No pets configured.")
        Gumps.AddLabel(gd, PET_LABEL_X, y + ROW_H, HUE_TXT, "Open Config to set pet slots.")

    else:
        for slot in slots:
            stored_name = PET_NAMES[slot]

            if not stored_name:
                stored_name = "Pet %d" % (slot + 1)

            pet = get_pet_by_slot(slot, max_range=18, refresh_status=True)

            Gumps.AddLabel(gd, PET_LABEL_X, y, HUE_TXT, "P%d" % (slot + 1))

            if not pet:
                Gumps.AddLabel(gd, PET_NAME_X, y, HUE_BAD, "%s [Out of Range]" % stored_name)
                y += PET_ROW_H
                continue

            frac = hp_pct(pet)
            pct = int(frac * 100)

            name = safe_getattr(pet, "Name", stored_name) or stored_name

            if name != PET_NAMES[slot]:
                PET_NAMES[slot] = name
                Misc.SetSharedValue(PET_NAME_KEYS[slot], name)

            if safe_getattr(pet, "Poisoned", False):
                name += " [P]"

            fill = int(round(frac * PET_SEGMENTS))

            Gumps.AddLabel(gd, PET_NAME_X, y, _health_hue(frac), "%s %d%%" % (name, pct))

            _draw_segments(gd, PET_BAR_X, y + 2, PET_SEGMENTS, PET_SEG_W, fill, HUE_EMPTY, HUE_PET_FILLED)

            y += PET_ROW_H

    # -------------------------------------------------------
    # FOOTER
    # -------------------------------------------------------

    footer_y = gump_h - 45

    Gumps.AddLabel(gd, LEFT_PAD, footer_y, _activity_hue, "Status: %s" % _activity_status)
    Gumps.AddLabel(gd, LEFT_PAD, footer_y + ROW_H, HUE_TXT, "Tracking %d pet%s" % (pet_count, "" if pet_count == 1 else "s"))

    Gumps.SendGump(GUMP_ID, Player.Serial, DEFAULT_GUMP_POS[0], DEFAULT_GUMP_POS[1], gd.gumpDefinition, gd.gumpStrings)

# ===========================================================
# CONFIG PAGE
# ===========================================================

def render_config_page():
    gump_h = 220
    gd = _new_gump(gump_h)

    Gumps.AddLabel(gd, LEFT_PAD, 6, HUE_TITLE, "FroggeVet Pet Configuration")

    y = 32

    for slot in range(MAX_PET_SLOTS):
        serial = PET_SERIALS[slot]

        if serial > 0:
            name = PET_NAMES[slot] or "Pet"
            name_hue = HUE_GOOD
        else:
            name = "Not Set"
            name_hue = HUE_WARN

        set_button = BTN_SET_BASE + slot
        clear_button = BTN_CLEAR_BASE + slot

        Gumps.AddLabel(gd, LEFT_PAD, y, HUE_TXT, "Slot %d:" % (slot + 1))
        Gumps.AddLabel(gd, 62, y, name_hue, name)

        Gumps.AddButton(gd, 212, y - 1, 4005, 4006, set_button, 1, 0)
        Gumps.AddLabel(gd, 239, y, HUE_TXT, "SET")

        if serial > 0:
            Gumps.AddButton(gd, 275, y - 1, 4005, 4006, clear_button, 1, 0)
            Gumps.AddLabel(gd, 302, y, HUE_BAD, "CLEAR")

        y += 24

    Gumps.AddLabel(gd, LEFT_PAD, y, HUE_TXT, "Healing:")
    Gumps.AddButton(gd, 75, y - 1, 4005, 4006, BTN_CYCLE_HEAL_MODE, 1, 0)
    Gumps.AddLabel(gd, 102, y, HUE_GOOD, heal_mode_label())

    Gumps.AddButton(gd, LEFT_PAD, gump_h - 28, 4014, 4015, BTN_BACK, 1, 0)
    Gumps.AddLabel(gd, LEFT_PAD + 27, gump_h - 26, HUE_TXT, "BACK")

    Gumps.AddButton(gd, 210, gump_h - 28, 4017, 4018, BTN_CLEAR_ALL, 1, 0)
    Gumps.AddLabel(gd, 237, gump_h - 26, HUE_BAD, "CLEAR ALL")

    Gumps.SendGump(GUMP_ID, Player.Serial, DEFAULT_GUMP_POS[0], DEFAULT_GUMP_POS[1], gd.gumpDefinition, gd.gumpStrings)


def render_gui():
    global _dirty_ui

    if _current_page == PAGE_MAIN:
        refresh_vetkit_charges()

    Gumps.CloseGump(GUMP_ID)

    if _current_page == PAGE_CONFIG:
        render_config_page()
    else:
        render_main_page()

    _dirty_ui = False

# ===========================================================
# BUTTON HANDLING
# ===========================================================

def handle_button(button_id):
    global _current_page
    global _dirty_ui

    if button_id == BTN_TOGGLE_PAUSE:
        toggle_pause()
        return

    if button_id == BTN_CONFIG:
        _current_page = PAGE_CONFIG
        _dirty_ui = True
        return

    if button_id == BTN_BACK:
        _current_page = PAGE_MAIN
        _dirty_ui = True
        return

    if button_id == BTN_CLEAR_ALL:
        clear_all_pet_slots()
        _dirty_ui = True
        return

    if button_id == BTN_CYCLE_HEAL_MODE:
        cycle_heal_mode()
        _dirty_ui = True
        return

    if BTN_SET_BASE <= button_id < BTN_SET_BASE + MAX_PET_SLOTS:
        slot = button_id - BTN_SET_BASE
        set_pet_slot(slot)
        _dirty_ui = True
        return

    if BTN_CLEAR_BASE <= button_id < BTN_CLEAR_BASE + MAX_PET_SLOTS:
        slot = button_id - BTN_CLEAR_BASE
        clear_pet_slot(slot)
        _dirty_ui = True
        return

# ===========================================================
# MAIN
# ===========================================================

def main():
    global _dirty_ui

    load_heal_mode()
    load_pet_slots()
    clear_bandage_timer()

    count = configured_pet_count()

    if count > 0:
        set_activity("Waiting - checking tracked pets", HUE_TXT)
    else:
        set_activity("Waiting - configure a pet", HUE_WARN)

    msg("FroggeVet online with %d configured pet%s. Healing mode: %s." % (count, "" if count == 1 else "s", heal_mode_label()), OK_COLOR)

    last_gui = 0

    _dirty_ui = True
    render_gui()
    last_gui = now_ms()

    while Player.Connected:

        # ---------------------------------------------------
        # BUTTON HANDLING
        # ---------------------------------------------------

        gd = None

        try:
            gd = Gumps.GetGumpData(GUMP_ID)
        except:
            gd = None

        if gd and gd.buttonid:
            button_id = int(gd.buttonid)

            try:
                gd.buttonid = 0
            except:
                pass

            handle_button(button_id)

            Misc.Pause(BUTTON_DEBOUNCE_MS)

            if GUI_ENABLED and _dirty_ui:
                render_gui()
                last_gui = now_ms()

            continue

        # ---------------------------------------------------
        # HEALING
        # ---------------------------------------------------

        if not PAUSED and _current_page == PAGE_MAIN and not healing_in_progress():
            pets = get_tracked_pets(max_range=30)
            nearby_pets = []

            for pet in pets:
                if pet_in_range(pet, MAX_TARGET_RANGE):
                    nearby_pets.append(pet)

            target = pick_target(nearby_pets)
            distant_target = target if target else pick_target(pets)
            low_pets = []

            for pet in nearby_pets:
                if hp_pct(pet) < VETKIT_HP_THRESHOLD:
                    low_pets.append(pet)

            should_use_vetkit = target and mode_uses_vetkits()

            if HEAL_MODE == HEAL_MODE_BOTH:
                should_use_vetkit = should_use_vetkit and len(low_pets) >= 2

            if should_use_vetkit:
                if use_vetkit():
                    Misc.Pause(LOOP_IDLE_MS)
                    continue

            if target and mode_uses_bandages():
                bandage_target(target)
            elif not configured_slots():
                set_activity("Waiting - configure a pet", HUE_WARN)
            elif not pets:
                set_activity("Waiting - tracked pets out of range", HUE_WARN)
            elif distant_target and not target:
                set_activity("Waiting - injured pets out of healing range", HUE_WARN)
            elif target and HEAL_MODE == HEAL_MODE_VETKITS:
                pass
            else:
                set_activity("Waiting - tracked pets are healthy", HUE_TXT)

        # ---------------------------------------------------
        # GUI REFRESH
        # ---------------------------------------------------

        if GUI_ENABLED:

            if _dirty_ui:
                render_gui()
                last_gui = now_ms()

            elif _current_page == PAGE_MAIN and now_ms() - last_gui >= REFRESH_MS:
                render_gui()
                last_gui = now_ms()

        Misc.Pause(LOOP_IDLE_MS)

    # -------------------------------------------------------
    # CLEANUP
    # -------------------------------------------------------

    clear_bandage_timer()
    Target.Cancel()
    Gumps.CloseGump(GUMP_ID)

    msg("FroggeVet stopped.", WARN_COLOR)


main()
