# ==========================================================
# === Frog Lumberjacking Lite (Razor Enhanced Script) ======
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

HATCHET_IDS = [0x0F43, 0x0F44]
LOG_IDS = [0x1BDD]
BOARD_IDS = [0x1BD7]

HARVEST_RESULT_MS = 1900
LOG_CUT_RESULT_MS = 2000
TARGET_CURSOR_TIMEOUT_MS = 1800
TARGET_CURSOR_RETRIES = 3
TARGET_CURSOR_RETRY_MS = 1400
TOOL_LOCKOUT_RETRY_MS = 2200
MOVE_RESULT_MS = 700
MAX_LOG_CUT_FAILURES = 3
MAX_MOVE_FAILURES = 3
MOUNT_RETRY_LIMIT = 5
MOUNT_RETRY_MS = 1200

TOOL_FAILURE_MESSAGES = ["worn out", "tool has broken", "must use an axe"]
TOOL_LOCKOUT_MESSAGES = ["you must wait a while to use this tool again"]
MOUNT_LOCKOUT_MESSAGES = ["you must wait to perform another action", "you must wait"]

# ====================================================================
# GLOBAL STATE
# ====================================================================

_storage_serial = 0
_storage_is_mobile = False
_failed_hatchet_serial = 0
_remount_serial = 0
_log_cut_failures = {}

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


def wait_until_near(target):
    distance = target_distance(target)
    if distance < 0 or distance <= 2:
        return True

    Player.HeadMessage(53, "Move within 2 tiles of your storage beetle.")
    while Player.Connected and not Player.IsGhost:
        distance = target_distance(target)
        if distance < 0 or distance <= 2:
            return True
        Misc.Pause(500)

    return False


def find_hatchet():
    candidates = []
    for layer in ["LeftHand", "RightHand"]:
        try:
            item = Player.GetItemOnLayer(layer)
            if item and int(item.ItemID) in HATCHET_IDS:
                candidates.append(item)
        except:
            pass

    for item in backpack_items_recursive():
        try:
            if int(item.ItemID) in HATCHET_IDS:
                candidates.append(item)
        except:
            pass

    for item in candidates:
        try:
            if int(item.Serial) != int(_failed_hatchet_serial):
                return item
        except:
            return item

    return None


def find_log_stack():
    for item in direct_backpack_items():
        try:
            if int(item.ItemID) in LOG_IDS:
                return item
        except:
            pass
    return None


def find_board_stack():
    for item in direct_backpack_items():
        try:
            if int(item.ItemID) in BOARD_IDS:
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


def dismount_for_processing():
    global _remount_serial

    mount_item = player_mount_item()
    storage_mobile = valid_mobile(_storage_serial) if _storage_is_mobile else None
    suspected_storage_mount = bool(_storage_is_mobile and not storage_mobile)

    if not mount_item and not suspected_storage_mount:
        return True

    mount_hint = int(_storage_serial) if _storage_is_mobile else 0
    if mount_hint <= 0 and mount_item:
        try:
            mount_hint = int(mount_item.Serial)
        except:
            mount_hint = 0

    Player.HeadMessage(53, "Dismounting before cutting and storing lumber.")
    for attempt in range(MOUNT_RETRY_LIMIT):
        Journal.Clear()
        try:
            Mobiles.UseMobile(Player.Serial)
        except:
            pass
        Misc.Pause(MOUNT_RETRY_MS)

        storage_mobile = valid_mobile(_storage_serial) if _storage_is_mobile else None
        still_mounted = player_is_mounted()
        if not still_mounted and (not _storage_is_mobile or storage_mobile):
            _remount_serial = mount_hint
            Misc.SendMessage("Dismounted for lumber processing.", 68)
            return True

        if journal_any(MOUNT_LOCKOUT_MESSAGES):
            Misc.Pause(TOOL_LOCKOUT_RETRY_MS)

        Misc.SendMessage("Dismount retry {0}/{1}.".format(attempt + 1, MOUNT_RETRY_LIMIT), 53)

    Player.HeadMessage(33, "Could not dismount after five attempts. Script stopped.")
    return False


def ensure_mobile_access():
    mobile = valid_mobile(_storage_serial)
    if not mobile:
        Player.HeadMessage(33, "Storage beetle is unavailable.")
        return False

    return wait_until_near(mobile)


def remount_if_needed():
    global _remount_serial

    serial = int(_remount_serial)
    _remount_serial = 0
    if serial <= 0 or player_is_mounted():
        return True

    mobile = valid_mobile(serial)
    if not mobile and _storage_is_mobile:
        mobile = valid_mobile(_storage_serial)
    if not mobile:
        Player.HeadMessage(53, "Storage complete; beetle is unavailable for remounting.")
        return False

    for attempt in range(MOUNT_RETRY_LIMIT):
        Journal.Clear()
        try:
            Mobiles.UseMobile(mobile.Serial)
        except:
            pass
        Misc.Pause(MOUNT_RETRY_MS)
        if player_is_mounted():
            Misc.SendMessage("Remounted after lumber storage.", 68)
            return True
        if journal_any(MOUNT_LOCKOUT_MESSAGES):
            Misc.Pause(TOOL_LOCKOUT_RETRY_MS)

    Player.HeadMessage(53, "Storage complete; remount manually.")
    return False


def move_board_stack(item, destination):
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
# LUMBERJACKING
# ====================================================================

def cut_log_stack(log):
    global _failed_hatchet_serial

    hatchet = find_hatchet()
    if not hatchet:
        Player.HeadMessage(33, "No hatchet available to cut logs into boards.")
        return False

    try:
        hatchet_serial = int(hatchet.Serial)
        log_serial = int(log.Serial)
        before_log_amount = int(log.Amount)
    except:
        return False

    before_boards = count_direct_items(BOARD_IDS)

    for attempt in range(TARGET_CURSOR_RETRIES):
        Target.Cancel()
        Journal.Clear()

        try:
            Items.UseItem(hatchet)
        except:
            _failed_hatchet_serial = hatchet_serial
            return True

        if Target.WaitForTarget(TARGET_CURSOR_TIMEOUT_MS, False):
            Target.TargetExecute(log_serial)
            Misc.Pause(LOG_CUT_RESULT_MS)

            remaining_log = valid_item(log_serial)
            log_changed = not remaining_log
            if remaining_log:
                try:
                    log_changed = int(remaining_log.Amount) < before_log_amount
                except:
                    log_changed = False
            boards_changed = count_direct_items(BOARD_IDS) > before_boards

            if log_changed or boards_changed:
                _failed_hatchet_serial = 0
                _log_cut_failures[log_serial] = 0
                return True

            failures = int(_log_cut_failures.get(log_serial, 0)) + 1
            _log_cut_failures[log_serial] = failures
            if failures >= MAX_LOG_CUT_FAILURES:
                Player.HeadMessage(33, "Logs did not convert after three attempts. Script stopped.")
                return False
            Misc.SendMessage("Log conversion was not confirmed; retrying.", 53)
            return True

        if journal_any(TOOL_FAILURE_MESSAGES) or not valid_item(hatchet_serial):
            _failed_hatchet_serial = hatchet_serial
            Misc.SendMessage("Hatchet exhausted while cutting logs; trying another.", 53)
            return True

        if journal_any(TOOL_LOCKOUT_MESSAGES):
            Misc.Pause(TOOL_LOCKOUT_RETRY_MS)
        else:
            Misc.Pause(TARGET_CURSOR_RETRY_MS)

    _failed_hatchet_serial = hatchet_serial
    Misc.SendMessage("Hatchet cursor failed while cutting logs; trying another tool.", 53)
    return True

def harvest_once():
    global _failed_hatchet_serial

    hatchet = find_hatchet()
    if not hatchet:
        Player.HeadMessage(33, "No hatchet found. Frog Lumberjacking Lite stopped.")
        return False

    try:
        hatchet_serial = int(hatchet.Serial)
    except:
        hatchet_serial = 0

    for attempt in range(TARGET_CURSOR_RETRIES):
        Target.Cancel()
        Journal.Clear()

        try:
            Items.UseItem(hatchet)
        except:
            _failed_hatchet_serial = hatchet_serial
            return True

        if Target.WaitForTarget(TARGET_CURSOR_TIMEOUT_MS, False):
            Target.TargetExecute(Player.Serial)
            _failed_hatchet_serial = 0
            Misc.Pause(HARVEST_RESULT_MS)
            return True

        if journal_any(TOOL_FAILURE_MESSAGES) or not valid_item(hatchet_serial):
            _failed_hatchet_serial = hatchet_serial
            Misc.SendMessage("Hatchet exhausted; trying another.", 53)
            return True

        if journal_any(TOOL_LOCKOUT_MESSAGES):
            Misc.Pause(TOOL_LOCKOUT_RETRY_MS)
        else:
            Misc.Pause(TARGET_CURSOR_RETRY_MS)

    _failed_hatchet_serial = hatchet_serial
    Misc.SendMessage("Hatchet cursor failed three times; trying another tool.", 53)
    return True


def process_load():
    if not dismount_for_processing():
        return False

    destination = storage_container_serial(_storage_serial)
    if destination <= 0:
        Player.HeadMessage(33, "Storage is unavailable. Frog Lumberjacking Lite stopped.")
        return False

    if valid_mobile(_storage_serial):
        if not ensure_mobile_access():
            return False
        destination = storage_container_serial(_storage_serial)
        if destination <= 0:
            Player.HeadMessage(33, "Could not open the storage beetle pack.")
            return False

    while Player.Connected and not Player.IsGhost:
        log = find_log_stack()
        if log:
            if not cut_log_stack(log):
                return False
            continue

        board = find_board_stack()
        if not board:
            break

        moved = False
        for attempt in range(MAX_MOVE_FAILURES):
            if move_board_stack(board, destination):
                moved = True
                break
            Misc.Pause(MOVE_RESULT_MS)

        if not moved:
            Player.HeadMessage(33, "Storage rejected the boards. Empty it, then restart.")
            return False

    if not remount_if_needed():
        return False
    if overweight():
        Player.HeadMessage(33, "Still heavy after storing boards. Empty storage and restart.")
        return False

    Misc.SendMessage("Logs cut, boards stored, and mount restored.", 68)
    return True

# ====================================================================
# SETUP / MAIN
# ====================================================================

def configure():
    global _storage_serial, _storage_is_mobile

    Misc.SendMessage("If using a beetle, dismount before targeting it.", 55)
    Target.Cancel()
    _storage_serial = int(Target.PromptTarget("Target one storage bag, satchel, or beetle.", 0x03B2))
    if _storage_serial <= 0 or storage_container_serial(_storage_serial) <= 0:
        Player.HeadMessage(33, "Valid storage is required. Script stopped.")
        return False

    _storage_is_mobile = valid_mobile(_storage_serial) is not None

    Misc.SendMessage("Log storage: " + serial_label(_storage_serial), 68)
    Player.HeadMessage(68, "Frog Lumberjacking Lite active. You control movement.")
    return True


def Main():
    if not configure():
        return

    while Player.Connected:
        if Player.IsGhost:
            Player.HeadMessage(33, "Frog Lumberjacking Lite stopped: player is dead.")
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
    Misc.SendMessage("Frog Lumberjacking Lite stopped.", 33)


Main()
