# ==========================================================
# === Frog Mining Lite (Razor Enhanced Script) =============
# ==========================================================
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
# ====================================================================

import Items
import Journal
import Misc
import Mobiles
import Player
import Target

# ====================================================================
# USER SETTINGS
# ====================================================================

WEIGHT_RATIO = 0.80

# ====================================================================
# CONFIGURATION
# ====================================================================

VERSION = "1.0"

MINING_TOOL_IDS = [0x0E86, 0x0E85, 0x0FB4, 0x0F39]
ORE_IDS = [0x19B7, 0x19B8, 0x19B9, 0x19BA, 0x19B2, 0x19B3]
INGOT_IDS = [0x1BF2]

PROTECTED_INGOT_ID = 0x1BF2
PROTECTED_INGOT_HUE = 0x0B05

MIN_ORE_PER_SMELT = 2
HARVEST_RESULT_MS = 2300
TARGET_CURSOR_TIMEOUT_MS = 1800
TARGET_CURSOR_RETRIES = 3
TARGET_CURSOR_RETRY_MS = 1400
TOOL_LOCKOUT_RETRY_MS = 2200
SMELT_RESULT_MS = 1000
MOVE_RESULT_MS = 700
MAX_SMELT_FAILURES = 3
MAX_MOVE_FAILURES = 3

TOOL_FAILURE_MESSAGES = ["worn out", "tool has broken", "must have a mining tool"]
TOOL_LOCKOUT_MESSAGES = ["you must wait a while to use this tool again"]

# ====================================================================
# GLOBAL STATE
# ====================================================================

_storage_serial = 0
_smelt_serial = 0
_smelt_mode = "save raw"
_failed_tool_serial = 0
_remount_serial = 0
_smelt_failures = {}
_unsmeltable_ore = {}

# ====================================================================
# HELPERS
# ====================================================================

def journal_any(fragments):
    for fragment in fragments:
        text = str(fragment)
        variants = [text]
        sentence_case = text[:1].upper() + text[1:]
        if sentence_case not in variants:
            variants.append(sentence_case)
        for variant in variants:
            try:
                if Journal.Search(variant):
                    return True
            except:
                pass
    return False


def valid_item(serial):
    try:
        return Items.FindBySerial(int(serial)) if int(serial) > 0 else None
    except:
        return None


def valid_mobile(serial):
    try:
        return Mobiles.FindBySerial(int(serial)) if int(serial) > 0 else None
    except:
        return None


def direct_backpack_items():
    try:
        return list(Player.Backpack.Contains or [])
    except:
        return []


def backpack_items_recursive():
    found = []
    pending = direct_backpack_items()
    seen = {}

    while pending and len(found) < 512:
        item = pending.pop(0)
        try:
            serial = int(item.Serial)
        except:
            continue
        if serial in seen:
            continue
        seen[serial] = True
        found.append(item)
        try:
            pending.extend(list(item.Contains or []))
        except:
            pass

    return found


def storage_container_serial(target_serial):
    item = valid_item(target_serial)
    if item:
        return int(item.Serial)

    mobile = valid_mobile(target_serial)
    if mobile:
        try:
            if mobile.Backpack:
                return int(mobile.Backpack.Serial)
        except:
            pass

    return 0


def serial_label(serial):
    item = valid_item(serial)
    if item:
        try:
            return str(item.Name or "container")
        except:
            return "container"

    mobile = valid_mobile(serial)
    if mobile:
        try:
            return str(mobile.Name or "beetle")
        except:
            return "beetle"

    return "not set"


def overweight():
    try:
        return int(Player.Weight) >= int(float(Player.MaxWeight) * float(WEIGHT_RATIO))
    except:
        return False


def target_distance(target):
    try:
        return int(Player.DistanceTo(target))
    except:
        return -1


def wait_until_near(target, label):
    distance = target_distance(target)
    if distance < 0 or distance <= 2:
        return True

    Player.HeadMessage(53, "Move within 2 tiles of your " + str(label) + ".")
    while Player.Connected and not Player.IsGhost:
        distance = target_distance(target)
        if distance < 0 or distance <= 2:
            return True
        Misc.Pause(500)

    return False


def is_protected_ingot(item):
    try:
        return int(item.ItemID) == PROTECTED_INGOT_ID and int(item.Hue) == PROTECTED_INGOT_HUE
    except:
        return False


def find_mining_tool():
    candidates = []
    for layer in ["RightHand", "LeftHand"]:
        try:
            item = Player.GetItemOnLayer(layer)
            if item and int(item.ItemID) in MINING_TOOL_IDS:
                candidates.append(item)
        except:
            pass

    for item in backpack_items_recursive():
        try:
            if int(item.ItemID) in MINING_TOOL_IDS:
                candidates.append(item)
        except:
            pass

    for item in candidates:
        try:
            if int(item.Serial) != int(_failed_tool_serial):
                return item
        except:
            return item

    return None


def find_smeltable_ore():
    for item in direct_backpack_items():
        try:
            if (
                int(item.ItemID) in ORE_IDS
                and int(item.Amount) >= MIN_ORE_PER_SMELT
                and int(item.Serial) not in _unsmeltable_ore
            ):
                return item
        except:
            pass
    return None


def find_storable_resource():
    for item in direct_backpack_items():
        try:
            item_id = int(item.ItemID)
            serial = int(item.Serial)
            if item_id in INGOT_IDS and not is_protected_ingot(item):
                return item
            if item_id in ORE_IDS and (_smelt_mode == "save raw" or serial in _unsmeltable_ore):
                return item
        except:
            pass
    return None


def ensure_mobile_access(target_serial):
    global _remount_serial

    mobile = valid_mobile(target_serial)
    if not mobile:
        return True

    if not wait_until_near(mobile, "beetle"):
        return False

    if not Player.Mount:
        return True

    try:
        mount_serial = int(Player.Mount.Serial)
    except:
        mount_serial = 0

    if mount_serial != int(target_serial):
        return True

    Mobiles.UseMobile(Player.Serial)
    Misc.Pause(700)
    if Player.Mount:
        Player.HeadMessage(33, "Could not dismount the storage beetle.")
        return False

    _remount_serial = mount_serial
    return True


def remount_if_needed():
    global _remount_serial

    serial = int(_remount_serial)
    _remount_serial = 0
    if serial <= 0 or Player.Mount:
        return

    mobile = valid_mobile(serial)
    if not mobile:
        Player.HeadMessage(53, "Storage complete; beetle is unavailable for remounting.")
        return

    try:
        Mobiles.UseMobile(mobile.Serial)
        Misc.Pause(700)
    except:
        Player.HeadMessage(53, "Storage complete; remount manually.")


def move_resource(item, destination):
    try:
        serial = int(item.Serial)
        before_amount = int(item.Amount)
    except:
        return False

    try:
        Items.Move(item, int(destination), 0)
        Misc.Pause(MOVE_RESULT_MS)
    except:
        return False

    remaining = valid_item(serial)
    if not remaining:
        return True

    try:
        if int(remaining.Container) == int(destination) or int(remaining.RootContainer) == int(destination):
            return True
        if int(remaining.Amount) < before_amount:
            return True
    except:
        pass

    return False

# ====================================================================
# MINING
# ====================================================================

def harvest_once():
    global _failed_tool_serial

    tool = find_mining_tool()
    if not tool:
        Player.HeadMessage(33, "No mining tool found. Frog Mining Lite stopped.")
        return False

    try:
        tool_serial = int(tool.Serial)
    except:
        tool_serial = 0

    for attempt in range(TARGET_CURSOR_RETRIES):
        Target.Cancel()
        Journal.Clear()

        try:
            Items.UseItem(tool)
        except:
            _failed_tool_serial = tool_serial
            return True

        if Target.WaitForTarget(TARGET_CURSOR_TIMEOUT_MS, False):
            Target.TargetExecute(Player.Serial)
            _failed_tool_serial = 0
            Misc.Pause(HARVEST_RESULT_MS)
            return True

        if journal_any(TOOL_FAILURE_MESSAGES) or not valid_item(tool_serial):
            _failed_tool_serial = tool_serial
            Misc.SendMessage("Mining tool exhausted; trying another.", 53)
            return True

        if journal_any(TOOL_LOCKOUT_MESSAGES):
            Misc.Pause(TOOL_LOCKOUT_RETRY_MS)
        else:
            Misc.Pause(TARGET_CURSOR_RETRY_MS)

    _failed_tool_serial = tool_serial
    Misc.SendMessage("Mining cursor failed three times; trying another tool.", 53)
    return True


def smelt_one_stack(ore):
    serial = int(ore.Serial)
    before_amount = int(ore.Amount)
    target = valid_mobile(_smelt_serial) if _smelt_mode == "fire beetle" else valid_item(_smelt_serial)
    if not target:
        Player.HeadMessage(53, "Move back within sight of your " + _smelt_mode + ".")
        while Player.Connected and not Player.IsGhost:
            target = valid_mobile(_smelt_serial) if _smelt_mode == "fire beetle" else valid_item(_smelt_serial)
            if target:
                break
            Misc.Pause(500)
        if not target:
            return False

    if not wait_until_near(target, _smelt_mode):
        return False
    if _smelt_mode == "fire beetle" and not ensure_mobile_access(_smelt_serial):
        return False

    Journal.Clear()
    Items.UseItem(ore)
    if not Target.WaitForTarget(2000, False):
        failures = int(_smelt_failures.get(serial, 0)) + 1
        _smelt_failures[serial] = failures
    else:
        Target.TargetExecute(int(_smelt_serial))
        Misc.Pause(SMELT_RESULT_MS)
        remaining = valid_item(serial)
        changed = not remaining
        if remaining:
            try:
                changed = int(remaining.Amount) < before_amount
            except:
                changed = False
        if changed:
            _smelt_failures[serial] = 0
            return True
        failures = int(_smelt_failures.get(serial, 0)) + 1
        _smelt_failures[serial] = failures

    if int(_smelt_failures.get(serial, 0)) >= MAX_SMELT_FAILURES:
        _unsmeltable_ore[serial] = True
        Misc.SendMessage("Ore did not smelt after three attempts; storing it raw.", 53)

    return True


def process_load():
    destination = storage_container_serial(_storage_serial)
    if destination <= 0:
        Player.HeadMessage(33, "Storage is unavailable. Frog Mining Lite stopped.")
        return False

    while Player.Connected and not Player.IsGhost:
        if _smelt_mode != "save raw":
            ore = find_smeltable_ore()
            if ore:
                if not smelt_one_stack(ore):
                    return False
                continue

        resource = find_storable_resource()
        if resource:
            if valid_mobile(_storage_serial):
                if not ensure_mobile_access(_storage_serial):
                    return False
                destination = storage_container_serial(_storage_serial)
                if destination <= 0:
                    Player.HeadMessage(33, "Could not open the storage beetle pack.")
                    return False

            moved = False
            for attempt in range(MAX_MOVE_FAILURES):
                if move_resource(resource, destination):
                    moved = True
                    break
                Misc.Pause(MOVE_RESULT_MS)
            if not moved:
                Player.HeadMessage(33, "Storage rejected the metal. Empty it, then restart.")
                return False
            continue

        remount_if_needed()
        if overweight():
            Player.HeadMessage(33, "Still heavy after storing metal. Empty storage and restart.")
            return False

        Misc.SendMessage("Mining load processed; move to the next area.", 68)
        return True

    return False

# ====================================================================
# SETUP / MAIN
# ====================================================================

def configure():
    global _storage_serial, _smelt_serial, _smelt_mode

    Misc.SendMessage("If using a beetle, dismount before targeting it.", 55)
    Target.Cancel()
    _storage_serial = int(Target.PromptTarget("Target one storage bag, satchel, or beetle.", 0x03B2))
    if _storage_serial <= 0 or storage_container_serial(_storage_serial) <= 0:
        Player.HeadMessage(33, "Valid storage is required. Script stopped.")
        return False

    Target.Cancel()
    _smelt_serial = int(Target.PromptTarget("Target a fire beetle or forge. Press ESC to save raw ore.", 0x03B2))
    if _smelt_serial <= 0:
        _smelt_serial = 0
        _smelt_mode = "save raw"
    elif valid_mobile(_smelt_serial):
        _smelt_mode = "fire beetle"
    elif valid_item(_smelt_serial):
        _smelt_mode = "forge"
    else:
        Player.HeadMessage(33, "Smelting target was invalid. Script stopped.")
        return False

    Misc.SendMessage("Storage: {0}. Smelting: {1}.".format(serial_label(_storage_serial), _smelt_mode), 68)
    Player.HeadMessage(68, "Frog Mining Lite active. You control movement.")
    return True


def Main():
    if not configure():
        return

    while Player.Connected:
        if Player.IsGhost:
            Player.HeadMessage(33, "Frog Mining Lite stopped: player is dead.")
            break

        if overweight():
            if not process_load():
                break
            continue

        if not harvest_once():
            break

        Misc.Pause(100)

    remount_if_needed()
    Target.Cancel()
    Misc.SendMessage("Frog Mining Lite stopped.", 33)


Main()
