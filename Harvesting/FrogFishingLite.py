# ==========================================================
# === Frog Fishing Lite (Razor Enhanced Script) ============
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

FISHING_POLE_IDS = [0x0DC0]
STANDARD_FISH_IDS = [0x09CC, 0x09CD, 0x09CE, 0x09CF]
FISH_STEAK_IDS = [0x097A]
COMMON_BLADE_IDS = [0x0F51, 0x0F52, 0x0EC2, 0x0EC3, 0x13F6, 0x13F7]

FISH_RESULT_MS = 9000
CUT_RESULT_MS = 1600
MOVE_RESULT_MS = 700
TARGET_CURSOR_TIMEOUT_MS = 2200
TARGET_CURSOR_RETRIES = 3
TARGET_CURSOR_RETRY_MS = 1600
TOOL_LOCKOUT_RETRY_MS = 2400
MAX_CUT_FAILURES = 3
MAX_MOVE_FAILURES = 3
MOUNT_RETRY_LIMIT = 5
MOUNT_RETRY_MS = 1200

TOOL_LOCKOUT_MESSAGES = ["you must wait a while to use this tool again"]
MOUNT_LOCKOUT_MESSAGES = ["you must wait to perform another action", "you must wait"]

# ====================================================================
# GLOBAL STATE
# ====================================================================

_storage_serial = 0
_storage_is_mobile = False
_blade_serial = 0
_failed_pole_serial = 0
_failed_blade_serial = 0
_cut_failures = {}

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


def wait_until_near_storage():
    mobile = valid_mobile(_storage_serial)
    if not _storage_is_mobile:
        return True

    if not mobile:
        Player.HeadMessage(53, "Bring your storage mount back within sight.")
        while Player.Connected and not Player.IsGhost:
            mobile = valid_mobile(_storage_serial)
            if mobile:
                break
            Misc.Pause(500)
        if not mobile:
            return False

    distance = target_distance(mobile)
    if distance < 0 or distance <= 2:
        return True

    Player.HeadMessage(53, "Bring your storage mount within 2 tiles.")
    while Player.Connected and not Player.IsGhost:
        mobile = valid_mobile(_storage_serial)
        if mobile:
            distance = target_distance(mobile)
            if distance < 0 or distance <= 2:
                return True
        Misc.Pause(500)

    return False


def player_mount_item():
    try:
        if Player.Mount:
            return Player.Mount
    except:
        pass

    try:
        return Player.GetItemOnLayer("Mount")
    except:
        return None


def player_is_mounted():
    return player_mount_item() is not None


def dismount_before_fishing():
    if not player_is_mounted():
        return True

    Player.HeadMessage(53, "Dismounting before fishing.")
    for attempt in range(MOUNT_RETRY_LIMIT):
        Journal.Clear()
        try:
            Mobiles.UseMobile(Player.Serial)
        except:
            pass
        Misc.Pause(MOUNT_RETRY_MS)

        if not player_is_mounted():
            Misc.SendMessage("Dismounted. The script will leave your mount alone now.", 68)
            return True

        if journal_any(MOUNT_LOCKOUT_MESSAGES):
            Misc.Pause(TOOL_LOCKOUT_RETRY_MS)

        Misc.SendMessage("Dismount retry {0}/{1}.".format(attempt + 1, MOUNT_RETRY_LIMIT), 53)

    Player.HeadMessage(33, "Could not dismount after five attempts. Script stopped.")
    return False


def find_tool(item_ids, failed_serial=0):
    candidates = []
    for layer in ["LeftHand", "RightHand"]:
        try:
            item = Player.GetItemOnLayer(layer)
            if item and int(item.ItemID) in item_ids:
                candidates.append(item)
        except:
            pass

    for item in backpack_items_recursive():
        try:
            if int(item.ItemID) in item_ids:
                candidates.append(item)
        except:
            pass

    for item in candidates:
        try:
            if int(item.Serial) != int(failed_serial):
                return item
        except:
            return item

    return None


def find_fishing_pole():
    return find_tool(FISHING_POLE_IDS, _failed_pole_serial)


def find_cutting_tool():
    selected = valid_item(_blade_serial)
    if selected:
        try:
            if int(selected.Serial) != int(_failed_blade_serial):
                return selected
        except:
            return selected
    return find_tool(COMMON_BLADE_IDS, _failed_blade_serial)


def find_direct_item(item_ids):
    for item in direct_backpack_items():
        try:
            if int(item.ItemID) in item_ids:
                return item
        except:
            pass
    return None


def count_direct_items(item_ids):
    total = 0
    for item in direct_backpack_items():
        try:
            if int(item.ItemID) in item_ids:
                total += max(1, int(item.Amount))
        except:
            pass
    return total


def move_steaks(item, destination):
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
# FISHING
# ====================================================================

def fish_once():
    global _failed_pole_serial

    pole = find_fishing_pole()
    if not pole:
        Player.HeadMessage(33, "No fishing pole found. Frog Fishing Lite stopped.")
        return False

    try:
        pole_serial = int(pole.Serial)
    except:
        pole_serial = 0

    for attempt in range(TARGET_CURSOR_RETRIES):
        Target.Cancel()
        Journal.Clear()

        try:
            Items.UseItem(pole)
        except:
            _failed_pole_serial = pole_serial
            return True

        if Target.WaitForTarget(TARGET_CURSOR_TIMEOUT_MS, False):
            Target.TargetExecute(Player.Serial)
            _failed_pole_serial = 0
            Misc.Pause(FISH_RESULT_MS)
            return True

        if not valid_item(pole_serial):
            _failed_pole_serial = pole_serial
            Misc.SendMessage("Fishing pole is unavailable; trying another.", 53)
            return True

        if journal_any(TOOL_LOCKOUT_MESSAGES):
            Misc.Pause(TOOL_LOCKOUT_RETRY_MS)
        else:
            Misc.Pause(TARGET_CURSOR_RETRY_MS)

    _failed_pole_serial = pole_serial
    Misc.SendMessage("Fishing cursor failed three times; trying another pole.", 53)
    return True


def cut_one_fish(fish):
    global _failed_blade_serial

    blade = find_cutting_tool()
    if not blade:
        Player.HeadMessage(33, "No dagger or knife found for cutting fish.")
        return False

    try:
        blade_serial = int(blade.Serial)
        fish_serial = int(fish.Serial)
        before_fish_amount = int(fish.Amount)
    except:
        return False

    before_steaks = count_direct_items(FISH_STEAK_IDS)

    for attempt in range(TARGET_CURSOR_RETRIES):
        Target.Cancel()
        Journal.Clear()

        try:
            Items.UseItem(blade)
        except:
            _failed_blade_serial = blade_serial
            return True

        if Target.WaitForTarget(TARGET_CURSOR_TIMEOUT_MS, False):
            Target.TargetExecute(fish_serial)
            Misc.Pause(CUT_RESULT_MS)

            remaining_fish = valid_item(fish_serial)
            fish_changed = not remaining_fish
            if remaining_fish:
                try:
                    fish_changed = int(remaining_fish.Amount) < before_fish_amount
                except:
                    fish_changed = False
            steaks_changed = count_direct_items(FISH_STEAK_IDS) > before_steaks

            if fish_changed or steaks_changed:
                _failed_blade_serial = 0
                _cut_failures[fish_serial] = 0
                return True

            failures = int(_cut_failures.get(fish_serial, 0)) + 1
            _cut_failures[fish_serial] = failures
            if failures >= MAX_CUT_FAILURES:
                Player.HeadMessage(33, "Fish did not convert after three attempts. Script stopped.")
                return False
            Misc.SendMessage("Fish cutting was not confirmed; retrying.", 53)
            return True

        if not valid_item(blade_serial):
            _failed_blade_serial = blade_serial
            Misc.SendMessage("Cutting tool is unavailable; trying another.", 53)
            return True

        if journal_any(TOOL_LOCKOUT_MESSAGES):
            Misc.Pause(TOOL_LOCKOUT_RETRY_MS)
        else:
            Misc.Pause(TARGET_CURSOR_RETRY_MS)

    _failed_blade_serial = blade_serial
    Misc.SendMessage("Cutting cursor failed three times; trying another blade.", 53)
    return True


def store_steaks():
    if not wait_until_near_storage():
        return False

    destination = storage_container_serial(_storage_serial)
    if destination <= 0:
        Player.HeadMessage(33, "Storage is unavailable. Frog Fishing Lite stopped.")
        return False

    while Player.Connected and not Player.IsGhost:
        steaks = find_direct_item(FISH_STEAK_IDS)
        if not steaks:
            break

        moved = False
        for attempt in range(MAX_MOVE_FAILURES):
            if move_steaks(steaks, destination):
                moved = True
                break
            Misc.Pause(MOVE_RESULT_MS)

        if not moved:
            Player.HeadMessage(33, "Storage rejected the fish steaks. Empty it, then restart.")
            return False

    if overweight():
        Player.HeadMessage(33, "Still heavy after storing fish steaks. Empty storage and restart.")
        return False

    Misc.SendMessage("Fish steaks stored; stationary fishing resumed.", 68)
    return True

# ====================================================================
# SETUP / MAIN
# ====================================================================

def configure():
    global _storage_serial, _storage_is_mobile, _blade_serial

    if not dismount_before_fishing():
        return False

    Target.Cancel()
    _storage_serial = int(Target.PromptTarget("Target one fish-steak storage bag, satchel, or mount.", 0x03B2))
    if _storage_serial <= 0 or storage_container_serial(_storage_serial) <= 0:
        Player.HeadMessage(33, "Valid storage is required. Script stopped.")
        return False

    _storage_is_mobile = valid_mobile(_storage_serial) is not None

    pole = find_fishing_pole()
    if not pole:
        Player.HeadMessage(33, "Put a fishing pole in your hands or backpack.")
        return False

    blade = find_cutting_tool()
    if not blade:
        Target.Cancel()
        _blade_serial = int(Target.PromptTarget("Target a dagger, knife, or fish-cutting blade.", 0x03B2))
        blade = valid_item(_blade_serial)
        if not blade:
            Player.HeadMessage(33, "A valid fish-cutting blade is required.")
            return False
    else:
        try:
            _blade_serial = int(blade.Serial)
        except:
            pass

    Misc.SendMessage("Fish-steak storage: " + serial_label(_storage_serial), 68)
    Player.HeadMessage(68, "Frog Fishing Lite active. Remain near fishable water.")
    return True


def Main():
    if not configure():
        return

    while Player.Connected:
        if Player.IsGhost:
            Player.HeadMessage(33, "Frog Fishing Lite stopped: player is dead.")
            break

        fish = find_direct_item(STANDARD_FISH_IDS)
        if fish:
            if not cut_one_fish(fish):
                break
            continue

        if overweight():
            if not store_steaks():
                break
            continue

        if not fish_once():
            break

        Misc.Pause(100)

    Target.Cancel()
    Misc.SendMessage("Frog Fishing Lite stopped.", 33)


Main()
