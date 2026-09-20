# ================================================
# === Frog Tamer Suite (Razor Enhanced Script) ===
# ================================================
# Copyright (c) Frogmancer Schteve. All rights reserved except as
# expressly permitted by the repository License.md.
#
# PERSONAL USE
# This script is provided for personal, non-commercial use.
# You may use, study, and modify it for your own use. Redistribution,
# resale, sublicensing, or incorporation into another distributed
# project is not permitted without prior permission.
#
# AI / LLM RESTRICTION
# Do NOT upload, submit, ingest, or otherwise provide this script,
# in whole or substantial part, to Large Language Models (LLMs),
# generative AI systems, AI coding assistants, machine-learning
# datasets, training/fine-tuning pipelines, retrieval systems, or
# automated code-generation systems.
#
# If you encounter a bug or compatibility issue, please submit an
# issue through the repository or contact Frogmancer Schteve directly
# rather than submitting the script to an AI service for troubleshooting.
#
# SHARD RULES
# You are responsible for ensuring your use of this script complies
# with the rules of the Ultima Online shard on which you play.
#
# This notice is only a summary. The repository License.md contains
# the complete terms governing use of this software.
#
# Use it. Learn from it. Improve it.
# Just don't feed the frogs to the robots.
# ====================================================================

from System.Collections.Generic import List
try:
    from System import Byte
except:
    Byte = None

import time
import Misc, Player, Mobiles, Gumps, Target, Items, Journal


# ===========================================================
# USER SETTINGS
# ===========================================================

HEAL_BELOW_PCT = 0.86
PRIORITIZE_POISON = True
MAX_TARGET_RANGE = 2

AUTO_KILL_RANGE = 3
AUTO_KILL_RESET_RANGE = 6
AUTO_KILL_COOLDOWN_MS = 1800

SCAN_RANGE = 30
PLAYER_SCAN_RANGE = 30
MAX_TRACKER_ROWS = 7


# ===========================================================
# CONFIGURATION
# ===========================================================

VERSION = "1.0"
GUMP_ID = 0xF2065453
DEFAULT_GUMP_POS = (900, 220)

LOOP_IDLE_MS = 120
STATE_REFRESH_MS = 500
BUTTON_DEBOUNCE_MS = 200

BANDAGE_ITEMID = 0x0E21
BANDAGE_HUE = -1
BANDAGE_WAIT_MS = 1600
BANDAGE_DISPLAY_SECONDS = 4
BANDAGE_DISPLAY_MS = BANDAGE_DISPLAY_SECONDS * 1000

VETKIT_ITEMID = 0x6B93
VETKIT_HP_THRESHOLD = 0.75
VETKIT_PROP_WAIT_MS = 500
VETKIT_REFRESH_MS = 3000
VETKIT_RETRY_MS = 1500
VETKIT_RESULT_WAIT_MS = 750
VETKIT_NO_PETS_MESSAGE = "There are no injured pets nearby"

OUT_OF_BANDAGE_ALERT_MS = 10000

GUMP_W = 570
BG_GUMP_ID = 5054
FROG_ICON = 0x2130
FROG_HUE = 1152

ROW_HEIGHT = 18
PET_ROW_HEIGHT = 24
LEFT_PAD = 10

HUE_TITLE = 1152
HUE_TEXT = 0x0481
HUE_GOOD = 0x0044
HUE_WARN = 0x0021
HUE_BAD = 0x0025

BAR_SEG_ART = 5210
BAR_SEG_W = 12
PET_BAR_SEGMENTS = 7
PET_BAR_W = PET_BAR_SEGMENTS * BAR_SEG_W
BAR_HUE_BG = 2999
HUES_BY_LEVEL = [0x021, 0x026, 0x02B, 0x030, 0x035, 0x03A]

MSG_COLOR = 68
WARN_COLOR = 53
ERR_COLOR = 33
OK_COLOR = 76

PAGE_MAIN = 0
PAGE_CONFIG = 1

CMD_ALL_FOLLOW = "All follow me"
CMD_ALL_KILL = "All kill"
CMD_ALL_GUARD = "All guard me"
CMD_ALL_STOP = "All stop"


# ===========================================================
# BUTTON IDS
# ===========================================================

BTN_VET_TOGGLE = 70001
BTN_AUTO_KILL_TOGGLE = 70002
BTN_CONFIG = 70003
BTN_BACK = 70004
BTN_QUIT = 70005
BTN_CLEAR_ALL = 70006
BTN_CYCLE_HEAL_MODE = 70007

BTN_ALL_FOLLOW = 70101
BTN_ALL_KILL = 70102
BTN_ALL_GUARD = 70103
BTN_ALL_STOP = 70104

BTN_PET_COME_BASE = 71000
BTN_PET_KILL_BASE = 71100
BTN_PET_STAY_BASE = 71200
BTN_PET_LORE_BASE = 71300

BTN_SET_BASE = 72000
BTN_CLEAR_BASE = 72100


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

HUD_BAND_START_KEY = "vet_hud_band_start"
HUD_BAND_LEN_KEY = "vet_hud_band_len"


# ===========================================================
# GLOBAL STATE
# ===========================================================

_running = True
_current_page = PAGE_MAIN
_dirty_ui = True

_vet_paused = False
_auto_kill_enabled = False
_auto_kill_target_serial = 0
_last_auto_kill_ms = 0

_heal_mode = HEAL_MODE_BOTH
_activity_status = "Starting..."
_activity_hue = HUE_TEXT
_heal_kind = ""
_heal_target_name = ""

_vetkit_charge_cache = {}
_vetkit_charges = 0
_vetkit_unread = 0
_last_vetkit_refresh = 0
_last_vetkit_attempt = 0
_last_bandage_alert = 0

_pet_rows = []
_hostiles_rows = []
_players_rows = []
_last_visible_snapshot = None
_last_state_refresh = 0
_render_stage = "startup"


# ===========================================================
# GENERAL HELPERS
# ===========================================================

def now_ms():
    return int(time.time() * 1000)


def msg(text, color=MSG_COLOR):
    try:
        Misc.SendMessage(str(text), color)
    except:
        pass


def safe_getattr(obj, name, default=None):
    try:
        return getattr(obj, name)
    except:
        return default


def set_activity(text, hue=HUE_TEXT):
    global _activity_status
    global _activity_hue
    global _dirty_ui

    text = str(text or "")

    if text == _activity_status and hue == _activity_hue:
        return

    _activity_status = text
    _activity_hue = hue
    _dirty_ui = True


def _dist_to_player(mobile):
    try:
        player_pos = Player.Position
        mobile_pos = mobile.Position
        return max(abs(player_pos.X - mobile_pos.X), abs(player_pos.Y - mobile_pos.Y))
    except:
        return 99


def _proper_name(text):
    try:
        return " ".join(part.capitalize() for part in str(text or "").split())
    except:
        return str(text or "")


def _health_hue(current, maximum):
    if maximum <= 0:
        return HUES_BY_LEVEL[0]

    frac = max(0.0, min(1.0, float(current) / float(maximum)))
    index = int(frac * 5.0)
    index = max(0, min(5, index))
    return HUES_BY_LEVEL[index]


def _draw_bar(gd, x, y, width, pct, hue_fill, hue_bg=BAR_HUE_BG):
    segments = max(1, width // BAR_SEG_W)
    filled = int(round(max(0.0, min(1.0, pct)) * segments))

    for index in range(segments):
        Gumps.AddImage(gd, x + index * BAR_SEG_W, y, BAR_SEG_ART, hue_bg)

    for index in range(filled):
        Gumps.AddImage(gd, x + index * BAR_SEG_W, y, BAR_SEG_ART, hue_fill)


def _add_labeled_button(gd, x, y, button_id, label, hue=HUE_TEXT):
    Gumps.AddButton(gd, x, y, 4005, 4006, button_id, 1, 0)
    Gumps.AddLabel(gd, x + 20, y, hue, label)


# ===========================================================
# HEALING MODE
# ===========================================================

def heal_mode_label():
    if _heal_mode == HEAL_MODE_BANDAGES:
        return "Bandages"

    if _heal_mode == HEAL_MODE_VETKITS:
        return "Vet Kits"

    return "Both"


def load_heal_mode():
    global _heal_mode

    _heal_mode = HEAL_MODE_BOTH

    if not Misc.CheckSharedValue(HEAL_MODE_KEY):
        return

    try:
        saved_mode = int(Misc.ReadSharedValue(HEAL_MODE_KEY))
    except:
        return

    if saved_mode in (HEAL_MODE_BOTH, HEAL_MODE_BANDAGES, HEAL_MODE_VETKITS):
        _heal_mode = saved_mode


def cycle_heal_mode():
    global _heal_mode

    _heal_mode = (_heal_mode + 1) % 3
    Misc.SetSharedValue(HEAL_MODE_KEY, _heal_mode)
    set_activity("Healing mode: %s" % heal_mode_label(), HUE_GOOD)
    msg("Frog Tamer healing mode: %s" % heal_mode_label(), OK_COLOR)


def mode_uses_bandages():
    return _heal_mode in (HEAL_MODE_BOTH, HEAL_MODE_BANDAGES)


def mode_uses_vetkits():
    return _heal_mode in (HEAL_MODE_BOTH, HEAL_MODE_VETKITS)


# ===========================================================
# BANDAGE TIMER
# ===========================================================

def set_bandage_timer(start_ms, length_ms):
    Misc.SetSharedValue(HUD_BAND_START_KEY, int(start_ms))
    Misc.SetSharedValue(HUD_BAND_LEN_KEY, int(length_ms))


def clear_bandage_timer():
    Misc.SetSharedValue(HUD_BAND_START_KEY, None)
    Misc.SetSharedValue(HUD_BAND_LEN_KEY, None)


def bandage_running():
    start = Misc.ReadSharedValue(HUD_BAND_START_KEY) if Misc.CheckSharedValue(HUD_BAND_START_KEY) else 0
    length = Misc.ReadSharedValue(HUD_BAND_LEN_KEY) if Misc.CheckSharedValue(HUD_BAND_LEN_KEY) else 0
    return bool(start and length and now_ms() < start + length)


def bandage_time_left_ms():
    start = Misc.ReadSharedValue(HUD_BAND_START_KEY) if Misc.CheckSharedValue(HUD_BAND_START_KEY) else 0
    length = Misc.ReadSharedValue(HUD_BAND_LEN_KEY) if Misc.CheckSharedValue(HUD_BAND_LEN_KEY) else 0
    return max(0, (start + length) - now_ms()) if start and length else 0


def start_heal_timer(kind, pet=None):
    global _heal_kind
    global _heal_target_name

    _heal_kind = str(kind or "Healing")
    _heal_target_name = pet_name(pet) if pet else ""
    set_bandage_timer(now_ms(), BANDAGE_DISPLAY_MS)

    if _heal_target_name:
        set_activity("Using %s on %s" % (_heal_kind.lower(), _heal_target_name), HUE_GOOD)
    else:
        set_activity("Using %s on nearby pets" % _heal_kind.lower(), HUE_GOOD)


# ===========================================================
# INVENTORY HELPERS
# ===========================================================

def get_item_in_subbags(itemid, hue=-1):
    item = Items.FindByID(itemid, hue, Player.Backpack.Serial)

    if item:
        return item

    for container in Player.Backpack.Contains or []:
        item = Items.FindByID(itemid, hue, container.Serial)

        if item:
            return item

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
    msg("All Frog Tamer pet slots cleared.", WARN_COLOR)


def configured_slots():
    slots = []

    for slot in range(MAX_PET_SLOTS):
        if PET_SERIALS[slot] > 0:
            slots.append(slot)

    return slots


def configured_pet_count():
    return len(configured_slots())


def valid_pet(pet):
    return bool(pet and not safe_getattr(pet, "IsGhost", True) and safe_getattr(pet, "HitsMax", 0) > 0)


def hp_pct(pet):
    hits_max = float(safe_getattr(pet, "HitsMax", 0) or 0)

    if hits_max <= 0:
        return 0.0

    return float(safe_getattr(pet, "Hits", 0) or 0) / hits_max


def pet_name(pet):
    return str(safe_getattr(pet, "Name", "Pet") or "Pet")


def pet_in_range(pet, max_range):
    if not pet:
        return False

    if max_range is None:
        return True

    return _dist_to_player(pet) <= int(max_range)


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
    msg("Target pet for slot %d. ESC cancels." % (slot + 1), MSG_COLOR)
    serial = Target.PromptTarget("Select Pet %d" % (slot + 1))

    if serial <= 0:
        set_activity("Pet setup cancelled", HUE_WARN)
        return

    for other_slot in range(MAX_PET_SLOTS):
        if other_slot != slot and PET_SERIALS[other_slot] == serial:
            set_activity("Pet already stored in slot %d" % (other_slot + 1), HUE_WARN)
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


def get_tracked_pets(max_range=30):
    pets = []

    for slot in configured_slots():
        pet = get_pet_by_slot(slot, max_range=max_range, refresh_status=True)

        if pet:
            pets.append(pet)

    return pets


def pick_heal_target(pets):
    if PRIORITIZE_POISON:
        poisoned = [pet for pet in pets if safe_getattr(pet, "Poisoned", False)]

        if poisoned:
            return min(poisoned, key=hp_pct)

    injured = [pet for pet in pets if hp_pct(pet) < HEAL_BELOW_PCT]

    if injured:
        return min(injured, key=hp_pct)

    return None


# ===========================================================
# PET COMMANDS AND LORE
# ===========================================================

def say_command(command):
    try:
        Player.ChatSay(0, command)
        return True
    except:
        set_activity("Could not issue pet command", HUE_BAD)
        return False


def say_target_command(command, target_serial=None):
    Target.Cancel()

    if target_serial is None:
        target_serial = Target.PromptTarget("Choose a target. ESC cancels.")

        if target_serial <= 0:
            set_activity("Pet attack cancelled", HUE_WARN)
            return False

        Target.Cancel()

    if not say_command(command):
        return False

    if not Target.WaitForTarget(2000, False):
        set_activity("No target cursor for %s" % command, HUE_WARN)
        return False

    try:
        Target.TargetExecute(int(target_serial))
        return True
    except:
        set_activity("Could not target that creature", HUE_BAD)
        return False


def all_follow():
    if say_command(CMD_ALL_FOLLOW):
        set_activity("All pets following", HUE_GOOD)


def all_kill():
    if say_target_command(CMD_ALL_KILL):
        set_activity("All pets attacking target", HUE_GOOD)


def all_guard():
    if say_command(CMD_ALL_GUARD):
        set_activity("All pets guarding", HUE_GOOD)


def all_stop():
    if say_command(CMD_ALL_STOP):
        set_activity("All pets stopped", HUE_WARN)


def pet_command_name(slot):
    if slot < 0 or slot >= MAX_PET_SLOTS:
        return ""

    return str(PET_NAMES[slot] or "").strip()


def individual_command(slot, command, needs_target=False):
    name = pet_command_name(slot)

    if not name:
        set_activity("Pet slot %d has no name" % (slot + 1), HUE_WARN)
        return

    full_command = "%s %s" % (name, command)

    if needs_target:
        if say_target_command(full_command):
            set_activity("%s attacking target" % name, HUE_GOOD)
    elif say_command(full_command):
        set_activity("%s: %s" % (name, command), HUE_GOOD)


def open_pet_lore(slot):
    pet = get_pet_by_slot(slot, max_range=SCAN_RANGE, refresh_status=False)

    if not pet:
        set_activity("Pet is out of lore range", HUE_WARN)
        return

    try:
        Player.UseSkill("Animal Lore", pet.Serial, True)
        set_activity("Opening lore for %s" % pet_name(pet), HUE_GOOD)
    except:
        try:
            Mobiles.UseMobile(pet.Serial)
            set_activity("Opening %s" % pet_name(pet), HUE_GOOD)
        except:
            set_activity("Could not open pet lore", HUE_BAD)


# ===========================================================
# VETERINARY MODULE
# ===========================================================

def use_vetkit():
    global _last_vetkit_attempt

    if bandage_running():
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
        clear_bandage_timer()
        set_activity("Vet kit found no injured nearby pets", HUE_WARN)
        return False

    note_vetkit_used(kit.Serial)
    return True


def bandage_target(pet):
    global _last_bandage_alert

    if not valid_pet(pet) or bandage_running():
        return False

    bandage = get_bandage()

    if not bandage:
        set_activity("Out of bandages for %s" % pet_name(pet), HUE_BAD)

        if now_ms() - _last_bandage_alert > OUT_OF_BANDAGE_ALERT_MS:
            msg("Out of bandages!", ERR_COLOR)
            _last_bandage_alert = now_ms()

        return False

    pet_serial = pet.Serial
    Journal.Clear()
    Target.Cancel()
    set_activity("Preparing bandage for %s" % pet_name(pet), HUE_TEXT)
    Items.UseItem(bandage)

    if not Target.WaitForTarget(BANDAGE_WAIT_MS, False):
        set_activity("Bandage targeting timed out", HUE_WARN)
        return False

    fresh_pet = Mobiles.FindBySerial(pet_serial)

    if not valid_pet(fresh_pet):
        Target.Cancel()
        set_activity("Bandage cancelled - pet unavailable", HUE_WARN)
        return False

    if not pet_in_range(fresh_pet, MAX_TARGET_RANGE * 6):
        Target.Cancel()
        set_activity("Bandage cancelled - pet out of range", HUE_WARN)
        return False

    Target.TargetExecute(fresh_pet.Serial)
    start_heal_timer("bandage", fresh_pet)
    Misc.Pause(120)
    return True


def veterinary_step():
    if _vet_paused or _current_page != PAGE_MAIN or bandage_running() or Target.HasTarget():
        return False

    pets = get_tracked_pets(max_range=SCAN_RANGE)
    nearby_pets = [pet for pet in pets if pet_in_range(pet, MAX_TARGET_RANGE)]
    target = pick_heal_target(nearby_pets)
    distant_target = target if target else pick_heal_target(pets)
    low_nearby = [pet for pet in nearby_pets if hp_pct(pet) < VETKIT_HP_THRESHOLD]

    should_use_vetkit = bool(target and mode_uses_vetkits())

    if _heal_mode == HEAL_MODE_BOTH:
        should_use_vetkit = should_use_vetkit and len(low_nearby) >= 2

    if should_use_vetkit and use_vetkit():
        return True

    if target and mode_uses_bandages():
        return bandage_target(target)

    if not configured_slots():
        set_activity("Waiting - configure a pet", HUE_WARN)
    elif not pets:
        set_activity("Waiting - tracked pets out of range", HUE_WARN)
    elif distant_target and not target:
        set_activity("Waiting - injured pets out of healing range", HUE_WARN)
    elif target and _heal_mode == HEAL_MODE_VETKITS:
        set_activity("Waiting - vet kit conditions not met", HUE_WARN)
    else:
        set_activity("Waiting - tracked pets are healthy", HUE_TEXT)

    return False


# ===========================================================
# MOB AND PLAYER TRACKING
# ===========================================================

def _notoriety_list(values):
    if Byte is None:
        return None

    result = List[Byte]()

    for value in values:
        result.Add(Byte(value))

    return result


def scan_hostiles():
    try:
        mobile_filter = Mobiles.Filter()
        mobile_filter.Enabled = True
        mobile_filter.RangeMax = SCAN_RANGE
        mobile_filter.CheckLineOfSight = False
        notorieties = _notoriety_list([3, 4, 5, 6])

        if notorieties is not None:
            mobile_filter.Notorieties = notorieties
        else:
            for notoriety in [3, 4, 5, 6]:
                mobile_filter.Notorieties.Add(notoriety)

        try:
            mobile_filter.IsHuman = 0
        except:
            pass

        rows = []

        for mobile in Mobiles.ApplyFilter(mobile_filter) or []:
            if not mobile:
                continue

            hits = int(safe_getattr(mobile, "Hits", 0) or 0)
            hits_max = int(safe_getattr(mobile, "HitsMax", 0) or 0)

            if safe_getattr(mobile, "IsGhost", False) or (hits_max > 0 and hits <= 0):
                continue

            rows.append((mobile, _dist_to_player(mobile)))

        rows.sort(key=lambda entry: entry[1])
        return rows[:MAX_TRACKER_ROWS]
    except:
        return []


def scan_players():
    players = []

    try:
        for notoriety in (1, 6):
            mobile_filter = Mobiles.Filter()
            mobile_filter.Enabled = True
            mobile_filter.RangeMax = PLAYER_SCAN_RANGE
            mobile_filter.CheckLineOfSight = False
            notorieties = _notoriety_list([notoriety])

            if notorieties is not None:
                mobile_filter.Notorieties = notorieties
            else:
                mobile_filter.Notorieties.Add(notoriety)

            try:
                mobile_filter.IsHuman = 1
            except:
                pass

            for mobile in Mobiles.ApplyFilter(mobile_filter) or []:
                if mobile and mobile.Serial != Player.Serial:
                    players.append((mobile, _dist_to_player(mobile)))
    except:
        return []

    seen = set()
    unique = []

    for mobile, distance in sorted(players, key=lambda entry: entry[1]):
        if mobile.Serial in seen:
            continue

        seen.add(mobile.Serial)
        unique.append((mobile, distance))

    return unique[:MAX_TRACKER_ROWS]


def update_pet_rows():
    global _pet_rows

    rows = []

    for slot in configured_slots():
        stored_name = PET_NAMES[slot] or "Pet %d" % (slot + 1)
        pet = get_pet_by_slot(slot, max_range=SCAN_RANGE, refresh_status=True)

        if pet:
            current_name = safe_getattr(pet, "Name", stored_name) or stored_name

            if current_name != PET_NAMES[slot]:
                PET_NAMES[slot] = current_name
                Misc.SetSharedValue(PET_NAME_KEYS[slot], current_name)

            rows.append((slot, pet, current_name, _dist_to_player(pet)))
        else:
            rows.append((slot, None, stored_name, 99))

    _pet_rows = rows


def make_visible_snapshot():
    pet_snapshot = []

    for slot, pet, name, distance in _pet_rows:
        pet_snapshot.append((
            slot,
            PET_SERIALS[slot],
            name,
            int(safe_getattr(pet, "Hits", 0) or 0) if pet else -1,
            int(safe_getattr(pet, "HitsMax", 0) or 0) if pet else -1,
            bool(safe_getattr(pet, "Poisoned", False)) if pet else False,
            distance,
        ))

    hostile_snapshot = []

    for mobile, distance in _hostiles_rows:
        hostile_snapshot.append((
            mobile.Serial,
            str(safe_getattr(mobile, "Name", "") or ""),
            int(safe_getattr(mobile, "Hits", 0) or 0),
            int(safe_getattr(mobile, "HitsMax", 0) or 0),
            distance,
        ))

    player_snapshot = []

    for mobile, distance in _players_rows:
        player_snapshot.append((
            mobile.Serial,
            str(safe_getattr(mobile, "Name", "") or ""),
            int(safe_getattr(mobile, "Notoriety", 0) or 0),
            distance,
        ))

    return (
        _current_page,
        _vet_paused,
        _auto_kill_enabled,
        _auto_kill_target_serial,
        _heal_mode,
        _activity_status,
        _activity_hue,
        bandage_time_left_ms() // 250,
        count_in_subbags(BANDAGE_ITEMID, BANDAGE_HUE),
        _vetkit_charges,
        _vetkit_unread,
        tuple(pet_snapshot),
        tuple(hostile_snapshot),
        tuple(player_snapshot),
    )


def refresh_visible_state(force=False):
    global _hostiles_rows
    global _players_rows
    global _last_visible_snapshot
    global _last_state_refresh
    global _dirty_ui

    current_time = now_ms()

    if not force and current_time - _last_state_refresh < STATE_REFRESH_MS:
        return

    update_pet_rows()
    _hostiles_rows = scan_hostiles()
    _players_rows = scan_players()
    refresh_vetkit_charges()

    snapshot = make_visible_snapshot()

    if snapshot != _last_visible_snapshot:
        _dirty_ui = True
        _last_visible_snapshot = snapshot

    _last_state_refresh = current_time


# ===========================================================
# AUTO KILL MODULE
# ===========================================================

def current_auto_kill_target_valid():
    if _auto_kill_target_serial <= 0:
        return False

    mobile = Mobiles.FindBySerial(_auto_kill_target_serial)

    if not mobile:
        return False

    hits = int(safe_getattr(mobile, "Hits", 0) or 0)
    hits_max = int(safe_getattr(mobile, "HitsMax", 0) or 0)

    if safe_getattr(mobile, "IsGhost", False) or (hits_max > 0 and hits <= 0):
        return False

    return _dist_to_player(mobile) <= AUTO_KILL_RESET_RANGE


def nearest_auto_kill_candidate():
    for mobile, distance in _hostiles_rows:
        if distance <= AUTO_KILL_RANGE:
            return mobile

    return None


def auto_kill_step():
    global _auto_kill_target_serial
    global _last_auto_kill_ms
    global _dirty_ui

    if not _auto_kill_enabled or _current_page != PAGE_MAIN or Target.HasTarget():
        return False

    if current_auto_kill_target_valid():
        return False

    if _auto_kill_target_serial > 0:
        _auto_kill_target_serial = 0
        _dirty_ui = True

    current_time = now_ms()

    if current_time - _last_auto_kill_ms < AUTO_KILL_COOLDOWN_MS:
        return False

    target = nearest_auto_kill_candidate()

    if not target:
        return False

    _last_auto_kill_ms = current_time

    if say_target_command(CMD_ALL_KILL, target.Serial):
        _auto_kill_target_serial = target.Serial
        set_activity("Auto Kill: %s" % (safe_getattr(target, "Name", "target") or "target"), HUE_GOOD)
        return True

    return False


def toggle_auto_kill():
    global _auto_kill_enabled
    global _auto_kill_target_serial
    global _dirty_ui

    _auto_kill_enabled = not _auto_kill_enabled
    _auto_kill_target_serial = 0
    _dirty_ui = True

    if _auto_kill_enabled:
        set_activity("Auto Kill armed at %d tiles" % AUTO_KILL_RANGE, HUE_GOOD)
    else:
        set_activity("Auto Kill off", HUE_WARN)


def attack_hostile_serial(serial):
    mobile = Mobiles.FindBySerial(serial)

    if not mobile:
        set_activity("Creature is no longer available", HUE_WARN)
        return

    if say_target_command(CMD_ALL_KILL, serial):
        set_activity("All pets attacking %s" % (safe_getattr(mobile, "Name", "target") or "target"), HUE_GOOD)


# ===========================================================
# GUI RENDERING
# ===========================================================

def render_pet_row(gd, row_y, slot, pet, stored_name):
    name = _proper_name(stored_name) or "Pet %d" % (slot + 1)
    Gumps.AddLabel(gd, LEFT_PAD, row_y, HUE_TEXT, "P%d" % (slot + 1))

    if pet:
        current = max(0, int(safe_getattr(pet, "Hits", 0) or 0))
        maximum = max(0, int(safe_getattr(pet, "HitsMax", 0) or 0))
        frac = float(current) / float(maximum) if maximum > 0 else 0.0
        percent = int(round(frac * 100.0)) if maximum > 0 else 0
        hue = _health_hue(current, maximum)
        poison_mark = " [P]" if safe_getattr(pet, "Poisoned", False) else ""

        Gumps.AddLabel(gd, 34, row_y, hue, name[:13] + poison_mark)
        _draw_bar(gd, 158, row_y + 1, PET_BAR_W, frac, hue)
        Gumps.AddLabel(gd, 246, row_y, hue, "%3d%%" % percent)
    else:
        Gumps.AddLabel(gd, 34, row_y, HUE_BAD, name[:11] + " [Out]")
        Gumps.AddLabel(gd, 246, row_y, HUE_BAD, "---")

    _add_labeled_button(gd, 286, row_y, BTN_PET_COME_BASE + slot, "Come")
    _add_labeled_button(gd, 354, row_y, BTN_PET_KILL_BASE + slot, "Kill")
    _add_labeled_button(gd, 414, row_y, BTN_PET_STAY_BASE + slot, "Stay")
    _add_labeled_button(gd, 478, row_y, BTN_PET_LORE_BASE + slot, "Lore")


def render_main_page(gd):
    global _render_stage

    pet_rows_count = max(1, len(_pet_rows))
    tracker_top = 100 + pet_rows_count * PET_ROW_HEIGHT
    gump_h = tracker_top + 18 + MAX_TRACKER_ROWS * ROW_HEIGHT + 48

    _render_stage = "main background"
    Gumps.AddBackground(gd, 0, 0, GUMP_W, gump_h, BG_GUMP_ID)
    Gumps.AddAlphaRegion(gd, 0, 0, GUMP_W, gump_h)
    Gumps.AddItem(gd, 5, 5, FROG_ICON, FROG_HUE)
    Gumps.AddLabel(gd, 40, 8, HUE_TITLE, "Frog Tamer Suite " + VERSION)

    Gumps.AddButton(gd, GUMP_W - 105, 5, 4029, 4030, BTN_CONFIG, 1, 0)
    Gumps.AddLabel(gd, GUMP_W - 83, 7, HUE_TEXT, "Config")
    Gumps.AddButton(gd, GUMP_W - 28, 5, 4017, 4018, BTN_QUIT, 1, 0)

    _render_stage = "global commands"
    y = 31
    Gumps.AddLabel(gd, LEFT_PAD, y, HUE_TITLE, "Commands")
    _add_labeled_button(gd, 82, y, BTN_ALL_FOLLOW, "Follow")
    _add_labeled_button(gd, 164, y, BTN_ALL_KILL, "Kill")
    _add_labeled_button(gd, 226, y, BTN_ALL_GUARD, "Guard")
    _add_labeled_button(gd, 306, y, BTN_ALL_STOP, "Stop")
    _add_labeled_button(gd, 378, y, BTN_AUTO_KILL_TOGGLE, "Auto Kill", HUE_GOOD if _auto_kill_enabled else HUE_TEXT)
    Gumps.AddLabel(gd, 475, y, HUE_GOOD if _auto_kill_enabled else HUE_WARN, "ON" if _auto_kill_enabled else "OFF")

    _render_stage = "veterinary status"
    y = 55
    Gumps.AddLabel(gd, LEFT_PAD, y, HUE_TITLE, "Vet")
    _add_labeled_button(gd, 46, y, BTN_VET_TOGGLE, "Resume" if _vet_paused else "Pause")
    Gumps.AddLabel(gd, 133, y, HUE_TEXT, "Mode: %s" % heal_mode_label())
    Gumps.AddLabel(gd, 245, y, HUE_TEXT, "Bandies: %d" % count_in_subbags(BANDAGE_ITEMID, BANDAGE_HUE))
    Gumps.AddLabel(gd, 350, y, HUE_TEXT, "Kit Uses: %s" % vetkit_charge_display())

    band_left_ms = bandage_time_left_ms()
    state_text = "ready" if band_left_ms <= 0 else "%.1fs" % (band_left_ms / 1000.0)
    Gumps.AddLabel(gd, 475, y, HUE_GOOD if band_left_ms <= 0 else HUE_WARN, state_text)

    _render_stage = "pet rows"
    y = 79
    Gumps.AddLabel(gd, LEFT_PAD, y, HUE_TITLE, "Pets / Rotation")

    if not _pet_rows:
        Gumps.AddLabel(gd, LEFT_PAD, y + 22, HUE_WARN, "No pets configured. Open Config to set pet slots.")
    else:
        for index, row in enumerate(_pet_rows):
            slot, pet, stored_name, distance = row
            render_pet_row(gd, y + 22 + index * PET_ROW_HEIGHT, slot, pet, stored_name)

    _render_stage = "creature and player trackers"
    y = tracker_top
    Gumps.AddLabel(gd, LEFT_PAD, y, HUE_TITLE, "Creatures")
    Gumps.AddLabel(gd, 300, y, HUE_TITLE, "Players")
    y += 18

    for index in range(MAX_TRACKER_ROWS):
        row_y = y + index * ROW_HEIGHT

        if index < len(_hostiles_rows):
            mobile, distance = _hostiles_rows[index]
            name = str(safe_getattr(mobile, "Name", "???") or "???").strip()
            hits = int(safe_getattr(mobile, "Hits", 0) or 0)
            hits_max = int(safe_getattr(mobile, "HitsMax", 0) or 0)
            hp_text = "%3d%%" % int((hits * 100) / max(1, hits_max)) if hits_max > 0 else ""

            try:
                Gumps.AddButton(gd, LEFT_PAD + 2, row_y + 1, 0x0846, 0x0846, int(mobile.Serial), 1, 0)
            except:
                pass

            Gumps.AddLabel(gd, LEFT_PAD + 20, row_y, HUE_TEXT, name[:20])
            Gumps.AddLabel(gd, 205, row_y, HUE_TEXT, "%2d" % distance)

            if hp_text:
                Gumps.AddLabel(gd, 235, row_y, HUE_TEXT, hp_text)

        if index < len(_players_rows):
            mobile, distance = _players_rows[index]
            name = str(safe_getattr(mobile, "Name", "???") or "???").strip()
            notoriety = int(safe_getattr(mobile, "Notoriety", 0) or 0)
            hue = ERR_COLOR if notoriety == 6 else MSG_COLOR
            Gumps.AddLabel(gd, 300, row_y, hue, name[:22])
            Gumps.AddLabel(gd, 510, row_y, hue, "%2d" % distance)

    _render_stage = "main footer"
    footer_y = gump_h - 42
    Gumps.AddLabel(gd, LEFT_PAD, footer_y, _activity_hue, "Status: %s" % _activity_status)
    Gumps.AddLabel(gd, LEFT_PAD, footer_y + 20, HUE_TEXT, "Tracked pets: %d   Auto Kill range: %d" % (configured_pet_count(), AUTO_KILL_RANGE))


def render_config_page(gd):
    global _render_stage

    _render_stage = "configuration page"
    gump_h = 245
    Gumps.AddBackground(gd, 0, 0, 390, gump_h, BG_GUMP_ID)
    Gumps.AddAlphaRegion(gd, 0, 0, 390, gump_h)
    Gumps.AddLabel(gd, LEFT_PAD, 8, HUE_TITLE, "Frog Tamer Configuration")
    Gumps.AddButton(gd, 355, 5, 4017, 4018, BTN_BACK, 1, 0)

    y = 36

    for slot in range(MAX_PET_SLOTS):
        serial = PET_SERIALS[slot]
        name = PET_NAMES[slot] or "Not Set"
        name_hue = HUE_GOOD if serial > 0 else HUE_WARN

        Gumps.AddLabel(gd, LEFT_PAD, y, HUE_TEXT, "Slot %d:" % (slot + 1))
        Gumps.AddLabel(gd, 64, y, name_hue, name[:18])
        _add_labeled_button(gd, 220, y - 1, BTN_SET_BASE + slot, "Set")

        if serial > 0:
            _add_labeled_button(gd, 290, y - 1, BTN_CLEAR_BASE + slot, "Clear", HUE_BAD)

        y += 27

    Gumps.AddLabel(gd, LEFT_PAD, y, HUE_TEXT, "Healing mode:")
    _add_labeled_button(gd, 110, y - 1, BTN_CYCLE_HEAL_MODE, heal_mode_label(), HUE_GOOD)
    y += 25
    Gumps.AddLabel(gd, LEFT_PAD, y, HUE_TEXT, "Auto-heal below: %d%%   Auto Kill defaults OFF each run." % int(HEAL_BELOW_PCT * 100))

    _add_labeled_button(gd, 245, gump_h - 28, BTN_CLEAR_ALL, "Clear All", HUE_BAD)
    _add_labeled_button(gd, LEFT_PAD, gump_h - 28, BTN_BACK, "Back")


def render_gui():
    global _dirty_ui
    global _render_stage

    _render_stage = "gump creation"
    Gumps.CloseGump(GUMP_ID)
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)

    if _current_page == PAGE_CONFIG:
        render_config_page(gd)
    else:
        render_main_page(gd)

    _render_stage = "gump send"
    Gumps.SendGump(GUMP_ID, Player.Serial, DEFAULT_GUMP_POS[0], DEFAULT_GUMP_POS[1], gd.gumpDefinition, gd.gumpStrings)
    _dirty_ui = False


def render_gui_safe():
    global _dirty_ui

    try:
        render_gui()
        return
    except Exception as error:
        error_text = str(error)
        msg("Frog Tamer render error at %s: %s" % (_render_stage, error_text), ERR_COLOR)

    try:
        Gumps.CloseGump(GUMP_ID)
        gd = Gumps.CreateGump(movable=True)
        Gumps.AddPage(gd, 0)
        Gumps.AddBackground(gd, 0, 0, 390, 85, BG_GUMP_ID)
        Gumps.AddAlphaRegion(gd, 0, 0, 390, 85)
        Gumps.AddLabel(gd, 10, 8, HUE_BAD, "Frog Tamer render error")
        Gumps.AddLabel(gd, 10, 32, HUE_WARN, "Stage: %s" % _render_stage)
        Gumps.AddLabel(gd, 10, 54, HUE_TEXT, error_text[:55])
        Gumps.SendGump(GUMP_ID, Player.Serial, DEFAULT_GUMP_POS[0], DEFAULT_GUMP_POS[1], gd.gumpDefinition, gd.gumpStrings)
    except:
        pass

    _dirty_ui = False


# ===========================================================
# BUTTON HANDLING
# ===========================================================

def toggle_vet_pause():
    global _vet_paused
    global _dirty_ui

    _vet_paused = not _vet_paused
    _dirty_ui = True

    if _vet_paused:
        set_activity("Veterinary module paused", HUE_WARN)
    else:
        set_activity("Veterinary module resumed", HUE_GOOD)


def handle_slot_button(button_id, base, action):
    if base <= button_id < base + MAX_PET_SLOTS:
        action(button_id - base)
        return True

    return False


def handle_button(button_id):
    global _running
    global _current_page
    global _dirty_ui

    if button_id == BTN_QUIT:
        _running = False
        return

    if button_id == BTN_CONFIG:
        _current_page = PAGE_CONFIG
        _dirty_ui = True
        return

    if button_id == BTN_BACK:
        _current_page = PAGE_MAIN
        _dirty_ui = True
        return

    if button_id == BTN_VET_TOGGLE:
        toggle_vet_pause()
        return

    if button_id == BTN_AUTO_KILL_TOGGLE:
        toggle_auto_kill()
        return

    if button_id == BTN_CYCLE_HEAL_MODE:
        cycle_heal_mode()
        return

    if button_id == BTN_CLEAR_ALL:
        clear_all_pet_slots()
        _dirty_ui = True
        return

    if button_id == BTN_ALL_FOLLOW:
        all_follow()
        return

    if button_id == BTN_ALL_KILL:
        all_kill()
        return

    if button_id == BTN_ALL_GUARD:
        all_guard()
        return

    if button_id == BTN_ALL_STOP:
        all_stop()
        return

    if handle_slot_button(button_id, BTN_SET_BASE, set_pet_slot):
        _dirty_ui = True
        return

    if handle_slot_button(button_id, BTN_CLEAR_BASE, clear_pet_slot):
        _dirty_ui = True
        return

    if handle_slot_button(button_id, BTN_PET_COME_BASE, lambda slot: individual_command(slot, "come")):
        return

    if handle_slot_button(button_id, BTN_PET_KILL_BASE, lambda slot: individual_command(slot, "kill", True)):
        return

    if handle_slot_button(button_id, BTN_PET_STAY_BASE, lambda slot: individual_command(slot, "stay")):
        return

    if handle_slot_button(button_id, BTN_PET_LORE_BASE, open_pet_lore):
        return

    mobile = Mobiles.FindBySerial(button_id)

    if mobile:
        attack_hostile_serial(button_id)


# ===========================================================
# MAIN
# ===========================================================

def main():
    global _dirty_ui

    load_heal_mode()
    load_pet_slots()
    clear_bandage_timer()
    refresh_visible_state(force=True)

    count = configured_pet_count()

    if count > 0:
        set_activity("Waiting - checking tracked pets", HUE_TEXT)
    else:
        set_activity("Waiting - configure a pet", HUE_WARN)

    msg("Frog Tamer Suite online with %d configured pet%s." % (count, "" if count == 1 else "s"), OK_COLOR)

    while _running and Player.Connected:
        handled_button = False
        gd = None

        try:
            gd = Gumps.GetGumpData(GUMP_ID)
        except:
            gd = None

        button_id = int(safe_getattr(gd, "buttonid", 0) or 0) if gd else 0

        if button_id > 0:
            try:
                gd.buttonid = 0
            except:
                pass

            Gumps.CloseGump(GUMP_ID)
            handle_button(button_id)
            handled_button = True
            Misc.Pause(BUTTON_DEBOUNCE_MS)

        if not _running:
            break

        if not handled_button:
            refresh_visible_state()
            acted = auto_kill_step()

            if not acted:
                veterinary_step()

            if _dirty_ui or Gumps.GetGumpData(GUMP_ID) is None:
                render_gui_safe()

        Misc.Pause(LOOP_IDLE_MS)

    clear_bandage_timer()
    Target.Cancel()
    Gumps.CloseGump(GUMP_ID)
    msg("Frog Tamer Suite stopped.", WARN_COLOR)


main()
