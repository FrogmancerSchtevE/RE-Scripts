# =================================================
# === Frog Butler Suite (Razor Enhanced Script) ===
# =================================================
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

# Status: In Development
#
# Compact home-storage launcher. Learned smart storage runs first,
# catalog-matched chest routes run second, and unmatched items may be
# sent to the optional Dump Chest last.

import json
import os
import re
import time

import Gumps
import Items
import Misc
import Player
import Target

from System.IO import Directory, File, Path


# ===========================================================
# USER SETTINGS
# ===========================================================

GUMP_X = 620
GUMP_Y = 330

# Delay after a server storage action. Increase this on a high-latency link.
ACTION_SETTLE_MS = 500

# Time allowed for a direct item move to become visible before retrying.
MOVE_VERIFY_MS = 550
MOVE_RETRY_LIMIT = 1

# Learn waits this long for the player to click the shelf's store action.
LEARN_CLICK_TIMEOUT_MS = 20000


# ===========================================================
# CONFIGURATION
# ===========================================================

VERSION = "0.2 alpha"
GUMP_ID = 0xF2064253

REFRESH_MS = 150
BUTTON_DEBOUNCE_MS = 150
SERVER_GUMP_WAIT_MS = 2500
SERVER_TARGET_WAIT_MS = 1500

HOME_WIDTH = 340
HOME_HEIGHT = 172
CONFIG_WIDTH = 780
CONFIG_HEIGHT = 510

BG_ID = 5054
PANEL_ID = 3000
FROG_ICON = 0x2130

TITLE_HUE = 1152
LABEL_HUE = 0x0481
DIM_HUE = 0x03B2
GOOD_HUE = 68
WARN_HUE = 53
BAD_HUE = 33

DATA_DIRECTORY = "FrogButlerData"
CATALOG_FILENAME = "FrogButlerItems.json"
CATALOG_RELATIVE_PATH = DATA_DIRECTORY + "/" + CATALOG_FILENAME
MAIN_FILENAME = "FrogButlerSuite.py"
PROJECT_FOLDER = "FrogButler"
IN_DEVELOPMENT_FOLDER = "In Development"
LEARN_LOG_FILENAME = "FrogButlerLearn.log"
SETTINGS_FORMAT = "frog-butler-character"
SETTINGS_VERSION = 2
CATALOG_FORMAT = "frog-butler-item-catalog"
CATALOG_VERSION = 1

MAX_SMART_STORAGE = 12
SMART_ROWS_PER_PAGE = 6
ROUTE_ROWS_PER_PAGE = 7

MODE_DIRECT = "direct"
MODE_TARGET_PLAYER = "target_player"
HUE_ANY = "any"
HUE_NONZERO = "nonzero"

CONFIG_VIEW_SMART = "smart"
CONFIG_VIEW_ROUTES = "routes"

# These keys exist only to migrate the original unscoped Shared Values.
LEGACY_KEY_PREFIX = "frogButler."
LEGACY_PROTECTED_KEY = LEGACY_KEY_PREFIX + "protected"
LEGACY_MIGRATED_KEY = LEGACY_KEY_PREFIX + "legacy_migrated_to"
LEGACY_STORAGE = [
    ("enchantment", "Enchantment Storage", MODE_DIRECT, 0, 0),
    ("resource_shelf", "Resource Shelf", MODE_DIRECT, 0x06ABCE12, 121),
    ("orb_box", "Mastery Orb Box", MODE_DIRECT, 0, 0),
    ("storage_shelf", "Storage Shelf", MODE_TARGET_PLAYER, 0, 0),
]


# ===========================================================
# GLOBAL STATE
# ===========================================================

_running = True
_current_page = "home"
_config_view = CONFIG_VIEW_SMART
_smart_page = 0
_route_page = 0
_dirty_ui = True
_render_stage = "Startup"

_status_msg = "Starting..."
_status_hue = LABEL_HUE

_project_directory = ""
_catalog_path = ""
_catalog_ready = False
_catalog_error = ""
_catalog_categories = []
_catalog_category_map = {}
_catalog_items = []
_catalog_exact = {}
_catalog_nonzero = {}
_catalog_any = {}
_catalog_counts = {}

_settings_path = ""
_settings_loaded = False
_settings_blocked = False
_settings_error_reported = False
_settings_character_serial = 0
_settings_character_name = ""

_smart_storage = []
_category_settings = {}
_dump_setting = {"serial": 0, "enabled": False}
_protected_serials = []

_store_active = False
_store_phase = "idle"
_smart_queue = []
_route_queue = []
_route_pending = None
_route_verify_at = 0

_smart_completed = 0
_smart_failed = 0
_store_skipped = 0
_route_moved = 0
_route_failed = 0
_route_kept = 0


# ===========================================================
# BUTTON IDS
# ===========================================================

BTN_STORE_ALL = 1001
BTN_CONFIG = 1002
BTN_BACK = 1003
BTN_CONFIG_VIEW = 1004
BTN_PAGE_PREV = 1005
BTN_PAGE_NEXT = 1006
BTN_RELOAD_CATALOG = 1007
BTN_CLOSE = 1099

BTN_SMART_TOGGLE_BASE = 1100
BTN_SMART_TARGET_BASE = 1200
BTN_SMART_LEARN_BASE = 1300
BTN_SMART_RESET_BASE = 1400

BTN_PROTECT_ITEM = 1501
BTN_CLEAR_PROTECTED = 1502
BTN_DUMP_TOGGLE = 1503
BTN_DUMP_TARGET = 1504
BTN_DUMP_RESET = 1505

BTN_CATEGORY_TOGGLE_BASE = 2000
BTN_CATEGORY_TARGET_BASE = 2200
BTN_CATEGORY_RESET_BASE = 2400


# ===========================================================
# VALUE HELPERS
# ===========================================================

def _int_value(value, fallback=0):
    try:
        if isinstance(value, str):
            text = value.strip()
            if text.lower().startswith("0x"):
                return int(text, 16)
            return int(text)
        return int(value)
    except:
        return int(fallback)


def _hex32(value):
    try:
        return "0x{0:08X}".format(int(value) & 0xFFFFFFFF)
    except:
        return "0x00000000"


def _hex16(value):
    try:
        return "0x{0:04X}".format(int(value) & 0xFFFF)
    except:
        return "0x0000"


def _short_text(value, limit):
    text = str(value or "")
    if len(text) <= limit:
        return text
    return text[:max(0, limit - 3)] + "..."


def _now_ms():
    return int(time.time() * 1000)


def _set_status(message, hue=LABEL_HUE):
    global _status_msg, _status_hue, _dirty_ui
    _status_msg = str(message)
    _status_hue = int(hue)
    _dirty_ui = True


def _valid_item(serial):
    try:
        serial = int(serial)
        if serial <= 0:
            return None
        return Items.FindBySerial(serial)
    except:
        return None


def _item_label(serial, empty_label="Not set"):
    item = _valid_item(serial)
    if not item:
        return empty_label if int(serial or 0) <= 0 else "Missing " + _hex32(serial)

    try:
        name = str(item.Name or "").strip()
    except:
        name = ""

    if name:
        return name + " " + _hex32(serial)
    return "Item " + _hex32(serial)


def _item_container_serial(item):
    try:
        container = item.Container
        if hasattr(container, "Serial"):
            return int(container.Serial)
        return int(container)
    except:
        return 0


def _player_identity():
    try:
        serial = int(Player.Serial) & 0xFFFFFFFF
    except:
        serial = 0
    try:
        name = str(Player.Name or "Unknown")
    except:
        name = "Unknown"
    return serial, name


def _script_directory():
    # RE documents CurrentScriptDirectory as the global Scripts folder.
    # Prefer the executing file, matching the working Core path pattern.
    try:
        script_file = globals().get("__file__")
        if script_file:
            directory = Path.GetDirectoryName(Path.GetFullPath(str(script_file)))
            if directory:
                return str(directory)
    except:
        pass

    try:
        current = str(Misc.CurrentScriptDirectory())
    except:
        current = ""

    candidates = []
    if current:
        candidates = [
            current,
            str(Path.Combine(current, PROJECT_FOLDER)),
            str(Path.Combine(current, IN_DEVELOPMENT_FOLDER, PROJECT_FOLDER)),
        ]

    for candidate in candidates:
        try:
            if File.Exists(Path.Combine(candidate, MAIN_FILENAME)):
                return str(Path.GetFullPath(candidate))
        except:
            pass

    return current if current else os.getcwd()


def _data_directory():
    return str(Path.Combine(_project_directory, DATA_DIRECTORY))


def _top_level_backpack_items():
    try:
        return list(Player.Backpack.Contains)
    except:
        return []


# ===========================================================
# ITEM CATALOG
# ===========================================================

def _parse_hue_rule(value):
    if isinstance(value, str):
        text = value.strip().lower()
        if text in ("*", HUE_ANY):
            return HUE_ANY, 0
        if text in ("non-zero", "non_zero", HUE_NONZERO):
            return HUE_NONZERO, 0
    hue = _int_value(value, -1)
    if hue < 0 or hue > 0xFFFF:
        raise Exception("hue must be any, nonzero, or 0..65535")
    return "exact", hue


def _add_catalog_rule(index, key, record, description):
    existing = index.get(key)
    if existing and existing["category"] != record["category"]:
        raise Exception("conflicting {0}: {1} and {2}".format(description, existing["category"], record["category"]))
    if not existing:
        index[key] = record


def _load_catalog():
    global _catalog_path, _catalog_ready, _catalog_error
    global _catalog_categories, _catalog_category_map, _catalog_items
    global _catalog_exact, _catalog_nonzero, _catalog_any, _catalog_counts

    _catalog_path = str(Path.Combine(_data_directory(), CATALOG_FILENAME))
    _catalog_ready = False
    _catalog_error = ""
    _catalog_categories = []
    _catalog_category_map = {}
    _catalog_items = []
    _catalog_exact = {}
    _catalog_nonzero = {}
    _catalog_any = {}
    _catalog_counts = {}

    try:
        if not File.Exists(_catalog_path):
            raise Exception(CATALOG_RELATIVE_PATH + " was not found relative to the script")

        document = json.loads(File.ReadAllText(_catalog_path))
        if not isinstance(document, dict):
            raise Exception("catalog root is not an object")
        if str(document.get("format", "")) != CATALOG_FORMAT:
            raise Exception("unsupported catalog format")
        if _int_value(document.get("version"), 0) != CATALOG_VERSION:
            raise Exception("unsupported catalog version")

        categories = document.get("categories", [])
        items = document.get("items", [])
        if not isinstance(categories, list) or not isinstance(items, list):
            raise Exception("categories and items must be arrays")

        for position, raw_category in enumerate(categories):
            if not isinstance(raw_category, dict):
                raise Exception("category {0} is not an object".format(position + 1))
            key = str(raw_category.get("key", "")).strip().lower()
            label = str(raw_category.get("label", "")).strip()
            if not re.match(r"^[a-z0-9_]+$", key):
                raise Exception("category {0} has an invalid key".format(position + 1))
            if key == "dump":
                raise Exception("dump is reserved for the unmatched fallback")
            if not label:
                raise Exception("category {0} needs a label".format(key))
            if key in _catalog_category_map:
                raise Exception("duplicate category: " + key)

            category = {
                "key": key,
                "label": label,
                "default_enabled": bool(raw_category.get("default_enabled", False)),
                "order": position,
            }
            _catalog_categories.append(category)
            _catalog_category_map[key] = category
            _catalog_counts[key] = 0

        if not _catalog_categories:
            raise Exception("catalog has no categories")

        for position, raw_item in enumerate(items):
            if not isinstance(raw_item, dict):
                raise Exception("item {0} is not an object".format(position + 1))
            if raw_item.get("enabled", True) is False:
                continue

            name = str(raw_item.get("name", "")).strip()
            category_key = str(raw_item.get("category", "")).strip().lower()
            item_id = _int_value(raw_item.get("item_id"), -1)
            if not name:
                raise Exception("item {0} needs a name".format(position + 1))
            if category_key not in _catalog_category_map:
                raise Exception("item {0} uses unknown category {1}".format(name, category_key))
            if item_id <= 0 or item_id > 0xFFFF:
                raise Exception("item {0} has an invalid item_id".format(name))

            hue_kind, hue_value = _parse_hue_rule(raw_item.get("hue"))
            record = {
                "name": name,
                "item_id": item_id,
                "hue_kind": hue_kind,
                "hue": hue_value,
                "category": category_key,
            }
            _catalog_items.append(record)
            _catalog_counts[category_key] = _catalog_counts.get(category_key, 0) + 1

            if hue_kind == "exact":
                _add_catalog_rule(_catalog_exact, (item_id, hue_value), record, "ItemID/hue {0}/{1}".format(_hex16(item_id), _hex16(hue_value)))
            elif hue_kind == HUE_NONZERO:
                _add_catalog_rule(_catalog_nonzero, item_id, record, "nonzero-hue ItemID " + _hex16(item_id))
            else:
                _add_catalog_rule(_catalog_any, item_id, record, "any-hue ItemID " + _hex16(item_id))

        _catalog_ready = True
        return True
    except Exception as error:
        _catalog_error = str(error)
        return False


def _match_catalog_item(item):
    try:
        item_id = int(item.ItemID) & 0xFFFF
        hue = int(item.Hue) & 0xFFFF
    except:
        return None

    record = _catalog_exact.get((item_id, hue))
    if record:
        return record
    if hue != 0:
        record = _catalog_nonzero.get(item_id)
        if record:
            return record
    return _catalog_any.get(item_id)


# ===========================================================
# CHARACTER SETTINGS
# ===========================================================

def _default_smart_slot(index):
    return {
        "name": "Smart Storage {0}".format(index + 1),
        "serial": 0,
        "enabled": False,
        "gump_id": 0,
        "action_id": 0,
        "mode": MODE_DIRECT,
        "learned": False,
    }


def _reset_character_state():
    global _smart_storage, _category_settings, _dump_setting, _protected_serials
    _smart_storage = [_default_smart_slot(index) for index in range(MAX_SMART_STORAGE)]
    _category_settings = {}
    for category in _catalog_categories:
        _category_settings[category["key"]] = {
            "serial": 0,
            "enabled": bool(category["default_enabled"]),
        }
    _dump_setting = {"serial": 0, "enabled": False}
    _protected_serials = []


def _normalize_smart_slot(raw_slot, index):
    slot = _default_smart_slot(index)
    if not isinstance(raw_slot, dict):
        return slot

    slot["name"] = _short_text(str(raw_slot.get("name", slot["name"])).strip() or slot["name"], 40)
    slot["serial"] = max(0, _int_value(raw_slot.get("serial"), 0))
    slot["enabled"] = bool(raw_slot.get("enabled", False))
    slot["gump_id"] = max(0, _int_value(raw_slot.get("gump_id"), 0))
    slot["action_id"] = max(0, _int_value(raw_slot.get("action_id"), 0))
    slot["mode"] = str(raw_slot.get("mode", MODE_DIRECT))
    if slot["mode"] not in (MODE_DIRECT, MODE_TARGET_PLAYER):
        slot["mode"] = MODE_DIRECT
    slot["learned"] = bool(raw_slot.get("learned", False))
    return slot


def _normalize_destination(raw_setting, default_enabled=False):
    if not isinstance(raw_setting, dict):
        raw_setting = {}
    return {
        "serial": max(0, _int_value(raw_setting.get("serial"), 0)),
        "enabled": bool(raw_setting.get("enabled", default_enabled)),
    }


def _ensure_category_settings():
    changed = False
    for category in _catalog_categories:
        key = category["key"]
        if key not in _category_settings:
            _category_settings[key] = {
                "serial": 0,
                "enabled": bool(category["default_enabled"]),
            }
            changed = True
    return changed


def _legacy_shared_int(key, fallback=0):
    try:
        if Misc.CheckSharedValue(key):
            return _int_value(Misc.ReadSharedValue(key), fallback)
    except:
        pass
    return int(fallback)


def _legacy_shared_text(key, fallback=""):
    try:
        if Misc.CheckSharedValue(key):
            return str(Misc.ReadSharedValue(key))
    except:
        pass
    return str(fallback)


def _legacy_key(storage_key, field):
    return LEGACY_KEY_PREFIX + storage_key + "." + field


def _migrate_legacy_settings():
    global _dump_setting, _protected_serials
    if _legacy_shared_int(LEGACY_MIGRATED_KEY, 0) > 0:
        return False

    migrated = False
    next_slot = 0

    for storage_key, label, default_mode, default_gump, default_action in LEGACY_STORAGE:
        serial = _legacy_shared_int(_legacy_key(storage_key, "serial"), 0)
        if serial <= 0 or next_slot >= MAX_SMART_STORAGE:
            continue

        slot = _default_smart_slot(next_slot)
        slot["name"] = label
        slot["serial"] = serial
        slot["enabled"] = _legacy_shared_int(_legacy_key(storage_key, "enabled"), 0) == 1
        slot["gump_id"] = _legacy_shared_int(_legacy_key(storage_key, "gump"), default_gump)
        slot["action_id"] = _legacy_shared_int(_legacy_key(storage_key, "action"), default_action)
        slot["mode"] = _legacy_shared_text(_legacy_key(storage_key, "mode"), default_mode)
        if slot["mode"] not in (MODE_DIRECT, MODE_TARGET_PLAYER):
            slot["mode"] = default_mode
        slot["learned"] = _legacy_shared_int(_legacy_key(storage_key, "learned"), 0) == 1
        _smart_storage[next_slot] = slot
        next_slot += 1
        migrated = True

    dump_serial = _legacy_shared_int(_legacy_key("dump_chest", "serial"), 0)
    if dump_serial > 0:
        _dump_setting = {
            "serial": dump_serial,
            "enabled": _legacy_shared_int(_legacy_key("dump_chest", "enabled"), 0) == 1,
        }
        migrated = True

    protected_text = _legacy_shared_text(LEGACY_PROTECTED_KEY, "")
    for value in protected_text.split(","):
        serial = _int_value(value.strip(), 0)
        if serial > 0 and serial not in _protected_serials:
            _protected_serials.append(serial)
            migrated = True

    return migrated


def _report_settings_error(message):
    global _settings_error_reported
    if _settings_error_reported:
        return
    _settings_error_reported = True
    try:
        Misc.SendMessage("[Frog Butler] " + str(message), BAD_HUE)
    except:
        pass


def _serialize_smart_slot(slot):
    return {
        "name": str(slot["name"]),
        "serial": _hex32(slot["serial"]),
        "enabled": bool(slot["enabled"]),
        "gump_id": _hex32(slot["gump_id"]),
        "action_id": int(slot["action_id"]),
        "mode": str(slot["mode"]),
        "learned": bool(slot["learned"]),
    }


def _serialize_destination(setting):
    return {
        "serial": _hex32(setting["serial"]),
        "enabled": bool(setting["enabled"]),
    }


def _save_character_settings():
    if not _settings_loaded or not _settings_path or _settings_blocked:
        return False

    current_serial, current_name = _player_identity()
    if current_serial <= 0 or current_serial != _settings_character_serial:
        _report_settings_error("save blocked because the active character changed")
        return False

    temporary_path = _settings_path + ".tmp"
    category_document = {}
    for key, setting in _category_settings.items():
        category_document[key] = _serialize_destination(setting)

    document = {
        "format": SETTINGS_FORMAT,
        "version": SETTINGS_VERSION,
        "character_serial": _settings_character_serial,
        "character_serial_hex": _hex32(_settings_character_serial),
        "character_name": current_name,
        "catalog_file": CATALOG_RELATIVE_PATH,
        "smart_storage": [_serialize_smart_slot(slot) for slot in _smart_storage],
        "category_destinations": category_document,
        "dump_fallback": _serialize_destination(_dump_setting),
        "protected_serials": [_hex32(serial) for serial in _protected_serials],
    }

    try:
        File.WriteAllText(temporary_path, json.dumps(document, indent=2, sort_keys=True) + "\n")
        if File.Exists(_settings_path):
            File.Replace(temporary_path, _settings_path, _settings_path + ".bak")
        else:
            File.Move(temporary_path, _settings_path)
        return True
    except Exception as error:
        try:
            if File.Exists(temporary_path):
                File.Delete(temporary_path)
        except:
            pass
        _report_settings_error("could not save character settings: " + str(error))
        return False


def _load_character_settings():
    global _settings_path, _settings_loaded, _settings_blocked, _settings_error_reported
    global _settings_character_serial, _settings_character_name
    global _smart_storage, _category_settings, _dump_setting, _protected_serials

    _settings_loaded = False
    _settings_blocked = False
    _settings_error_reported = False
    _settings_character_serial, _settings_character_name = _player_identity()
    _reset_character_state()

    if _settings_character_serial <= 0:
        _settings_blocked = True
        _report_settings_error("player serial is unavailable; settings were not loaded")
        return False

    data_directory = _data_directory()
    try:
        if not Directory.Exists(data_directory):
            Directory.CreateDirectory(data_directory)
    except Exception as error:
        _settings_blocked = True
        _report_settings_error("could not create the data folder: " + str(error))
        return False

    _settings_path = str(Path.Combine(data_directory, "character_0x{0:08X}.json".format(_settings_character_serial)))
    if File.Exists(_settings_path):
        try:
            document = json.loads(File.ReadAllText(_settings_path))
            if not isinstance(document, dict):
                raise Exception("settings root is not an object")
            if str(document.get("format", "")) != SETTINGS_FORMAT:
                raise Exception("unsupported settings format")
            if _int_value(document.get("version"), 0) != SETTINGS_VERSION:
                raise Exception("unsupported settings version")
            file_serial = _int_value(document.get("character_serial"), 0) & 0xFFFFFFFF
            if file_serial != _settings_character_serial:
                raise Exception("character mismatch")

            smart_document = document.get("smart_storage", [])
            category_document = document.get("category_destinations", {})
            protected_document = document.get("protected_serials", [])
            if not isinstance(smart_document, list):
                raise Exception("smart_storage is not an array")
            if not isinstance(category_document, dict):
                raise Exception("category_destinations is not an object")
            if not isinstance(protected_document, list):
                raise Exception("protected_serials is not an array")

            _smart_storage = []
            for index in range(MAX_SMART_STORAGE):
                raw_slot = smart_document[index] if index < len(smart_document) else {}
                _smart_storage.append(_normalize_smart_slot(raw_slot, index))

            _category_settings = {}
            for key, raw_setting in category_document.items():
                category_key = str(key).strip().lower()
                if re.match(r"^[a-z0-9_]+$", category_key):
                    _category_settings[category_key] = _normalize_destination(raw_setting)
            _ensure_category_settings()

            _dump_setting = _normalize_destination(document.get("dump_fallback", {}))
            _protected_serials = []
            for value in protected_document:
                serial = _int_value(value, 0)
                if serial > 0 and serial not in _protected_serials:
                    _protected_serials.append(serial)

            _settings_loaded = True
            _set_status("Loaded settings for {0}.".format(_settings_character_name), GOOD_HUE)
            return True
        except Exception as error:
            _settings_blocked = True
            _report_settings_error("profile rejected and preserved: " + str(error))
            _set_status("Character settings rejected; file preserved.", BAD_HUE)
            return False

    _settings_loaded = True
    migrated = _migrate_legacy_settings()
    if not _save_character_settings():
        return False

    if migrated:
        try:
            Misc.SetSharedValue(LEGACY_MIGRATED_KEY, int(_settings_character_serial))
        except:
            pass
        _set_status("Migrated old settings; verify targets for this character.", WARN_HUE)
    else:
        _set_status("Created settings for {0}.".format(_settings_character_name), GOOD_HUE)
    return True


def _persist_change(success_message, hue=GOOD_HUE):
    if _save_character_settings():
        _set_status(success_message, hue)
        return True
    _set_status("Settings could not be saved.", BAD_HUE)
    return False


# ===========================================================
# CONFIGURATION ACTIONS
# ===========================================================

def _smart_ready(index):
    slot = _smart_storage[index]
    if not _valid_item(slot["serial"]):
        return False, "target missing"
    if int(slot["gump_id"]) <= 0 or int(slot["action_id"]) <= 0:
        return False, "needs Learn"
    if slot["mode"] not in (MODE_DIRECT, MODE_TARGET_PLAYER):
        return False, "bad action mode"
    return True, "ready"


def _smart_mapping_label(index):
    slot = _smart_storage[index]
    if int(slot["gump_id"]) <= 0 or int(slot["action_id"]) <= 0:
        return "Needs Learn"
    action_name = "Fill" if slot["mode"] == MODE_DIRECT else "Restock"
    return "{0}: {1} / button {2}".format(action_name, _hex32(slot["gump_id"]), slot["action_id"])


def _toggle_smart(index):
    slot = _smart_storage[index]
    slot["enabled"] = not slot["enabled"]
    state = "enabled" if slot["enabled"] else "disabled"
    _persist_change("{0} {1}.".format(slot["name"], state))


def _target_smart(index):
    slot = _smart_storage[index]
    Target.Cancel()
    serial = Target.PromptTarget("Target a shelf, tome, key, or other smart storage item")
    item = _valid_item(serial)
    if not item:
        _set_status("Target cancelled or item not found.", BAD_HUE)
        return

    slot["serial"] = int(serial)
    slot["enabled"] = True
    try:
        name = str(item.Name or "").strip()
    except:
        name = ""
    if name:
        slot["name"] = _short_text(name, 40)
    _persist_change("{0} saved. Click Learn next.".format(slot["name"]), WARN_HUE)


def _reset_smart(index):
    old_name = _smart_storage[index]["name"]
    _smart_storage[index] = _default_smart_slot(index)
    _persist_change("{0} reset.".format(old_name), WARN_HUE)


def _category_setting(category_key):
    if category_key not in _category_settings:
        _category_settings[category_key] = {"serial": 0, "enabled": False}
    return _category_settings[category_key]


def _toggle_category(category_key):
    setting = _category_setting(category_key)
    setting["enabled"] = not setting["enabled"]
    label = _catalog_category_map[category_key]["label"]
    state = "enabled" if setting["enabled"] else "disabled"
    _persist_change("{0} route {1}.".format(label, state))


def _target_category(category_key):
    label = _catalog_category_map[category_key]["label"]
    Target.Cancel()
    serial = Target.PromptTarget("Target the destination for " + label)
    item = _valid_item(serial)
    if not item:
        _set_status("Target cancelled or item not found.", BAD_HUE)
        return

    # Some shard storage objects do not advertise themselves as containers.
    setting = _category_setting(category_key)
    setting["serial"] = int(serial)
    setting["enabled"] = True
    _persist_change("{0} destination saved.".format(label), GOOD_HUE)


def _reset_category(category_key):
    label = _catalog_category_map[category_key]["label"]
    _category_settings[category_key] = {"serial": 0, "enabled": False}
    _persist_change("{0} destination reset.".format(label), WARN_HUE)


def _toggle_dump():
    _dump_setting["enabled"] = not _dump_setting["enabled"]
    state = "enabled" if _dump_setting["enabled"] else "disabled"
    _persist_change("Unmatched Dump Chest {0}.".format(state))


def _target_dump():
    Target.Cancel()
    serial = Target.PromptTarget("Target the chest for unmatched backpack items")
    item = _valid_item(serial)
    if not item:
        _set_status("Target cancelled or item not found.", BAD_HUE)
        return
    _dump_setting["serial"] = int(serial)
    _dump_setting["enabled"] = True
    _persist_change("Unmatched Dump Chest saved.", GOOD_HUE)


def _reset_dump():
    global _dump_setting
    _dump_setting = {"serial": 0, "enabled": False}
    _persist_change("Unmatched Dump Chest reset.", WARN_HUE)


def _protect_item():
    Target.Cancel()
    serial = Target.PromptTarget("Target an item or bag direct chest routing must keep")
    item = _valid_item(serial)
    if not item:
        _set_status("Protection target cancelled or item not found.", BAD_HUE)
        return

    serial = int(serial)
    if serial not in _protected_serials:
        _protected_serials.append(serial)
    _persist_change("Protected: {0}".format(_item_label(serial)), GOOD_HUE)


def _clear_protected():
    global _protected_serials
    _protected_serials = []
    _persist_change("Protection list cleared.", WARN_HUE)


def _reload_catalog():
    if not _load_catalog():
        _set_status("Catalog rejected: " + _short_text(_catalog_error, 70), BAD_HUE)
        return
    changed = _ensure_category_settings()
    if changed:
        _save_character_settings()
    _set_status("Catalog reloaded: {0} items, {1} categories.".format(len(_catalog_items), len(_catalog_categories)), GOOD_HUE)


# ===========================================================
# GUMP ACTION LEARNER
# ===========================================================

def _learn_log_path():
    return str(Path.Combine(_data_directory(), LEARN_LOG_FILENAME))


def _start_response_capture(log_path):
    try:
        with open(log_path, "w") as log_file:
            log_file.write("FROG_BUTLER_LEARN\n")

        PacketLogger.Reset()
        PacketLogger.AddWhitelist(0xB1)
        PacketLogger.DiscardAll(True)
        PacketLogger.DiscardShowHeader(False)
        PacketLogger.ListenPacketPath("ClientToServer", True)
        PacketLogger.ListenPacketPath("ServerToClient", False)
        PacketLogger.Start(log_path, False)
        Misc.Pause(150)

        with open(log_path, "r") as log_file:
            return "Logging START" in log_file.read()
    except:
        return False


def _stop_response_capture():
    try:
        PacketLogger.Stop()
    except:
        pass
    try:
        PacketLogger.Reset()
    except:
        pass


def _uint_from_bytes(values, start, length):
    result = 0
    for index in range(start, start + length):
        result = (result << 8) | int(values[index])
    return result


def _response_packets(log_path):
    try:
        with open(log_path, "r") as log_file:
            log_text = log_file.read()
    except:
        return []

    packets = []
    pattern = re.compile(r"(?m)^[ \t]*0000[ \t]+((?:[0-9A-Fa-f]{2}[ \t]+){15}[0-9A-Fa-f]{2})")
    for block in log_text.split("0xB1")[1:]:
        match = pattern.search(block)
        if not match:
            continue
        try:
            values = [int(token, 16) for token in re.findall(r"[0-9A-Fa-f]{2}", match.group(1))]
            if len(values) < 15 or values[0] != 0xB1:
                continue
            packets.append({
                "serial": _uint_from_bytes(values, 3, 4),
                "gump_id": _uint_from_bytes(values, 7, 4),
                "button_id": _uint_from_bytes(values, 11, 4),
            })
        except:
            pass
    return packets


def _find_response(log_path, expected_gump_id):
    for packet in reversed(_response_packets(log_path)):
        if int(packet["gump_id"]) == int(expected_gump_id) and int(packet["button_id"]) > 0:
            return packet
    return None


def _learn_smart(index):
    slot = _smart_storage[index]
    item = _valid_item(slot["serial"])
    if not item:
        _set_status("Set this smart-storage target before Learn.", BAD_HUE)
        return

    log_path = _learn_log_path()
    if not _start_response_capture(log_path):
        _stop_response_capture()
        _set_status("Learn needs Razor Enhanced Packet Agent enabled.", BAD_HUE)
        Player.HeadMessage(BAD_HUE, "Enable Packet Agent, then try Learn again.")
        return

    learned_response = None
    server_gump_id = 0
    try:
        Gumps.CloseGump(GUMP_ID)
        Target.Cancel()
        Items.UseItem(item)
        Gumps.WaitForGump(0, SERVER_GUMP_WAIT_MS)

        try:
            server_gump_id = int(Gumps.CurrentGump())
        except:
            server_gump_id = 0

        if server_gump_id <= 0 or server_gump_id == GUMP_ID:
            _set_status("The targeted storage did not open a server gump.", BAD_HUE)
            return

        Misc.SendMessage("[Frog Butler] Click Fill from Backpack or Restock Shelf now.", WARN_HUE)
        Player.HeadMessage(WARN_HUE, "Click this storage's STORE action now.")

        waited = 0
        while waited < LEARN_CLICK_TIMEOUT_MS and Player.Connected:
            learned_response = _find_response(log_path, server_gump_id)
            if learned_response:
                break
            Misc.Pause(100)
            waited += 100

        if not learned_response:
            _set_status("Learn timed out. Try again and click the store action.", BAD_HUE)
            return

        has_target = Target.WaitForTarget(SERVER_TARGET_WAIT_MS, False)
        learned_mode = MODE_TARGET_PLAYER if has_target or Target.HasTarget() else MODE_DIRECT
        if learned_mode == MODE_TARGET_PLAYER and Target.HasTarget():
            Target.TargetExecute(Player.Serial)
            Misc.Pause(ACTION_SETTLE_MS)

        slot["gump_id"] = int(learned_response["gump_id"])
        slot["action_id"] = int(learned_response["button_id"])
        slot["mode"] = learned_mode
        slot["learned"] = True
        if not _save_character_settings():
            _set_status("Learned action but could not save it.", BAD_HUE)
            return

        mode_label = "Restock + backpack target" if learned_mode == MODE_TARGET_PLAYER else "Fill from backpack"
        _set_status("Learned {0}: {1}.".format(slot["name"], mode_label), GOOD_HUE)
    except Exception as error:
        _set_status("Learn failed: " + str(error), BAD_HUE)
    finally:
        _stop_response_capture()
        if server_gump_id > 0:
            try:
                Gumps.CloseGump(server_gump_id)
            except:
                pass


# ===========================================================
# STORE ALL ENGINE
# ===========================================================

def _all_destination_serials():
    serials = []
    for slot in _smart_storage:
        serial = int(slot["serial"])
        if serial > 0 and serial not in serials:
            serials.append(serial)
    for setting in _category_settings.values():
        serial = int(setting["serial"])
        if serial > 0 and serial not in serials:
            serials.append(serial)
    dump_serial = int(_dump_setting["serial"])
    if dump_serial > 0 and dump_serial not in serials:
        serials.append(dump_serial)
    return serials


def _destination_for_category(category_key):
    setting = _category_settings.get(category_key)
    if not setting or not setting["enabled"]:
        return 0
    return int(setting["serial"]) if _valid_item(setting["serial"]) else 0


def _dump_destination():
    if not _dump_setting["enabled"]:
        return 0
    return int(_dump_setting["serial"]) if _valid_item(_dump_setting["serial"]) else 0


def _cancel_store_all(message="Store All stopped."):
    global _store_active, _store_phase, _smart_queue, _route_queue
    global _route_pending, _route_verify_at
    _store_active = False
    _store_phase = "idle"
    _smart_queue = []
    _route_queue = []
    _route_pending = None
    _route_verify_at = 0
    if Target.HasTarget():
        Target.Cancel()
    _set_status(message, WARN_HUE)


def _start_store_all():
    global _store_active, _store_phase, _smart_queue, _route_queue
    global _route_pending, _route_verify_at
    global _smart_completed, _smart_failed, _store_skipped
    global _route_moved, _route_failed, _route_kept

    if _store_active:
        _cancel_store_all()
        return
    if not _catalog_ready:
        _set_status("Catalog is not ready: " + _short_text(_catalog_error, 50), BAD_HUE)
        return
    if _settings_blocked or not _settings_loaded:
        _set_status("Character settings are not ready.", BAD_HUE)
        return

    _smart_queue = []
    _store_skipped = 0
    for index, slot in enumerate(_smart_storage):
        if not slot["enabled"]:
            continue
        ready, reason = _smart_ready(index)
        if ready:
            _smart_queue.append(index)
        else:
            _store_skipped += 1
            Misc.SendMessage("[Frog Butler] Skipping {0}: {1}.".format(slot["name"], reason), BAD_HUE)

    ready_routes = 0
    for category in _catalog_categories:
        if _destination_for_category(category["key"]) > 0:
            ready_routes += 1
    dump_ready = _dump_destination() > 0

    if not _smart_queue and ready_routes <= 0 and not dump_ready:
        _set_status("No ready storage destinations. Open Configs.", WARN_HUE)
        return

    _route_queue = []
    _route_pending = None
    _route_verify_at = 0
    _smart_completed = 0
    _smart_failed = 0
    _route_moved = 0
    _route_failed = 0
    _route_kept = 0
    _store_active = True
    _store_phase = "smart"
    _set_status("Store All started: smart storage first.", GOOD_HUE)


def _run_smart_storage(index):
    slot = _smart_storage[index]
    item = _valid_item(slot["serial"])
    if not item:
        return False, "{0}: target is missing.".format(slot["name"])

    gump_id = int(slot["gump_id"])
    action_id = int(slot["action_id"])
    try:
        Gumps.CloseGump(gump_id)
    except:
        pass
    Misc.Pause(100)

    try:
        Items.UseItem(item)
        if not Gumps.WaitForGump(gump_id, SERVER_GUMP_WAIT_MS):
            return False, "{0}: mapped gump did not open.".format(slot["name"])

        Gumps.SendAction(gump_id, action_id)
        if slot["mode"] == MODE_TARGET_PLAYER:
            if not Target.WaitForTarget(SERVER_TARGET_WAIT_MS, False):
                return False, "{0}: action did not request a target.".format(slot["name"])
            Target.TargetExecute(Player.Serial)

        Misc.Pause(ACTION_SETTLE_MS)
        return True, "{0}: store action sent.".format(slot["name"])
    except Exception as error:
        return False, "{0}: {1}".format(slot["name"], str(error))
    finally:
        if Target.HasTarget():
            Target.Cancel()
        try:
            Gumps.CloseGump(gump_id)
        except:
            pass


def _prepare_routing():
    global _route_queue, _route_pending, _route_verify_at, _route_kept
    _route_queue = []
    _route_pending = None
    _route_verify_at = 0

    excluded = list(_protected_serials)
    for serial in _all_destination_serials():
        if serial not in excluded:
            excluded.append(serial)

    dump_serial = _dump_destination()
    for item in _top_level_backpack_items():
        try:
            serial = int(item.Serial)
            if serial in excluded:
                _route_kept += 1
                continue
            if _item_container_serial(item) != int(Player.Backpack.Serial):
                continue

            record = _match_catalog_item(item)
            if record:
                category_key = record["category"]
                destination = _destination_for_category(category_key)
                if destination > 0:
                    _route_queue.append({
                        "serial": serial,
                        "destination": destination,
                        "category": category_key,
                        "label": _catalog_category_map[category_key]["label"],
                        "name": str(item.Name or record["name"]),
                        "attempts": 0,
                    })
                else:
                    _route_kept += 1
                continue

            if dump_serial > 0:
                _route_queue.append({
                    "serial": serial,
                    "destination": dump_serial,
                    "category": "dump",
                    "label": "Dump Chest",
                    "name": str(item.Name or "Unmatched item"),
                    "attempts": 0,
                })
            else:
                _route_kept += 1
        except:
            _route_kept += 1

    order_map = {}
    for category in _catalog_categories:
        order_map[category["key"]] = int(category["order"])
    order_map["dump"] = len(_catalog_categories) + 1
    _route_queue.sort(key=lambda entry: (order_map.get(entry["category"], 9999), int(entry["serial"])))


def _route_step():
    global _route_pending, _route_verify_at, _route_moved, _route_failed

    if _route_pending:
        if _now_ms() < _route_verify_at:
            return

        entry = _route_pending
        _route_pending = None
        _route_verify_at = 0
        item = _valid_item(entry["serial"])
        still_top_level = item and _item_container_serial(item) == int(Player.Backpack.Serial)

        if not still_top_level:
            _route_moved += 1
            _set_status("Stored {0} -> {1} ({2} left).".format(_short_text(entry["name"], 24), entry["label"], len(_route_queue)), GOOD_HUE)
            return

        if int(entry["attempts"]) < MOVE_RETRY_LIMIT:
            entry["attempts"] = int(entry["attempts"]) + 1
            _route_queue.insert(0, entry)
            _set_status("Retrying {0}.".format(_short_text(entry["name"], 30)), WARN_HUE)
            return

        _route_failed += 1
        _set_status("Could not move {0}; left in backpack.".format(_short_text(entry["name"], 28)), BAD_HUE)
        return

    while _route_queue:
        entry = _route_queue.pop(0)
        item = _valid_item(entry["serial"])
        if not item or _item_container_serial(item) != int(Player.Backpack.Serial):
            continue
        if not _valid_item(entry["destination"]):
            _route_failed += 1
            _set_status("{0} destination is missing; item kept.".format(entry["label"]), BAD_HUE)
            return
        if Target.HasTarget():
            _route_queue.insert(0, entry)
            _set_status("Paused for your active target cursor.", WARN_HUE)
            return

        try:
            Items.Move(int(entry["serial"]), int(entry["destination"]), -1)
            _route_pending = entry
            _route_verify_at = _now_ms() + MOVE_VERIFY_MS
            _set_status("Moving {0} -> {1}.".format(_short_text(entry["name"], 26), entry["label"]), LABEL_HUE)
        except Exception as error:
            _route_failed += 1
            _set_status("Move failed: " + _short_text(str(error), 60), BAD_HUE)
        return


def _finish_store_all():
    global _store_active, _store_phase
    _store_active = False
    _store_phase = "idle"
    hue = GOOD_HUE if _smart_failed == 0 and _route_failed == 0 else WARN_HUE
    _set_status("Done: {0} smart, {1} moved, {2} failed, {3} kept.".format(_smart_completed, _route_moved, _smart_failed + _route_failed, _route_kept + _store_skipped), hue)


def _store_all_step():
    global _store_phase, _smart_completed, _smart_failed
    if not _store_active:
        return

    if _store_phase == "smart":
        if _smart_queue:
            index = int(_smart_queue.pop(0))
            success, message = _run_smart_storage(index)
            if success:
                _smart_completed += 1
                _set_status(message, GOOD_HUE)
            else:
                _smart_failed += 1
                _set_status(message, BAD_HUE)
                Misc.SendMessage("[Frog Butler] " + message, BAD_HUE)
            return

        _prepare_routing()
        _store_phase = "routes"
        _set_status("Chest routing prepared: {0} item(s).".format(len(_route_queue)), LABEL_HUE)
        return

    if _store_phase == "routes":
        if _route_queue or _route_pending:
            _route_step()
            return
        _finish_store_all()


# ===========================================================
# GUI HELPERS
# ===========================================================

def _add_button(gump, x, y, button_id, label, hue=LABEL_HUE, art_up=4005, art_down=4007):
    Gumps.AddButton(gump, x, y, art_up, art_down, button_id, 1, 0)
    Gumps.AddLabel(gump, x + 24, y, hue, label)


def _add_header(gump, width, title, back_button=False):
    Gumps.AddItem(gump, 7, 5, FROG_ICON, TITLE_HUE)
    Gumps.AddLabel(gump, 40, 8, TITLE_HUE, title)
    if back_button:
        Gumps.AddButton(gump, width - 66, 7, 4014, 4015, BTN_BACK, 1, 0)
    Gumps.AddButton(gump, width - 30, 7, 4017, 4018, BTN_CLOSE, 1, 0)


def _render_home():
    global _dirty_ui, _render_stage
    _render_stage = "Home shell"
    Gumps.CloseGump(GUMP_ID)
    gump = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gump, 0)
    Gumps.AddBackground(gump, 0, 0, HOME_WIDTH, HOME_HEIGHT, BG_ID)
    Gumps.AddAlphaRegion(gump, 0, 0, HOME_WIDTH, HOME_HEIGHT)
    _add_header(gump, HOME_WIDTH, "FROG BUTLER " + VERSION)

    Gumps.AddBackground(gump, 10, 36, HOME_WIDTH - 20, 82, PANEL_ID)
    Gumps.AddAlphaRegion(gump, 10, 36, HOME_WIDTH - 20, 82)
    store_label = "STOP" if _store_active else "STORE ALL"
    store_hue = WARN_HUE if _store_active else GOOD_HUE
    _add_button(gump, 28, 50, BTN_STORE_ALL, store_label, store_hue, 4014, 4015)
    _add_button(gump, 185, 50, BTN_CONFIG, "CONFIGS", LABEL_HUE, 4005, 4007)
    Gumps.AddLabel(gump, 17, 82, DIM_HUE, "Smart storage -> category chests -> dump.")
    catalog_hue = GOOD_HUE if _catalog_ready else BAD_HUE
    catalog_text = "Catalog: {0} items / {1} categories".format(len(_catalog_items), len(_catalog_categories)) if _catalog_ready else "Catalog error: " + _short_text(_catalog_error, 34)
    Gumps.AddLabel(gump, 17, 99, catalog_hue, catalog_text)

    Gumps.AddLabel(gump, 12, 124, TITLE_HUE, "STATUS")
    Gumps.AddLabel(gump, 12, 145, _status_hue, _short_text(_status_msg, 52))
    Gumps.SendGump(GUMP_ID, Player.Serial, GUMP_X, GUMP_Y, gump.gumpDefinition, gump.gumpStrings)
    _render_stage = "Complete"
    _dirty_ui = False


def _page_count(total_rows, rows_per_page):
    if total_rows <= 0:
        return 1
    return ((total_rows - 1) // rows_per_page) + 1


def _render_config_tabs(gump):
    view_label = "VIEW: SMART STORAGE" if _config_view == CONFIG_VIEW_SMART else "VIEW: CHEST ROUTES"
    _add_button(gump, 16, 39, BTN_CONFIG_VIEW, view_label, TITLE_HUE, 4005, 4007)
    _add_button(gump, 585, 39, BTN_RELOAD_CATALOG, "Reload JSON", GOOD_HUE)

    current = _smart_page if _config_view == CONFIG_VIEW_SMART else _route_page
    total = _page_count(MAX_SMART_STORAGE, SMART_ROWS_PER_PAGE) if _config_view == CONFIG_VIEW_SMART else _page_count(len(_catalog_categories), ROUTE_ROWS_PER_PAGE)
    Gumps.AddButton(gump, 420, 39, 4014, 4015, BTN_PAGE_PREV, 1, 0)
    Gumps.AddLabel(gump, 451, 40, LABEL_HUE, "{0}/{1}".format(current + 1, total))
    Gumps.AddButton(gump, 510, 39, 4005, 4007, BTN_PAGE_NEXT, 1, 0)


def _render_smart_row(gump, index, y):
    slot = _smart_storage[index]
    Gumps.AddBackground(gump, 10, y, CONFIG_WIDTH - 20, 50, PANEL_ID)
    Gumps.AddAlphaRegion(gump, 10, y, CONFIG_WIDTH - 20, 50)

    toggle_hue = GOOD_HUE if slot["enabled"] else DIM_HUE
    _add_button(gump, 18, y + 5, BTN_SMART_TOGGLE_BASE + index, "ON" if slot["enabled"] else "OFF", toggle_hue)
    Gumps.AddLabel(gump, 79, y + 5, TITLE_HUE, _short_text(slot["name"], 23))
    _add_button(gump, 272, y + 5, BTN_SMART_TARGET_BASE + index, "Target", LABEL_HUE)
    _add_button(gump, 360, y + 5, BTN_SMART_LEARN_BASE + index, "Learn", GOOD_HUE if slot["learned"] else WARN_HUE)
    _add_button(gump, 448, y + 5, BTN_SMART_RESET_BASE + index, "Reset", BAD_HUE)

    ready, reason = _smart_ready(index)
    Gumps.AddLabel(gump, 548, y + 5, GOOD_HUE if ready else BAD_HUE, "Ready" if ready else _short_text(reason, 20))
    Gumps.AddLabel(gump, 22, y + 27, DIM_HUE, _short_text(_item_label(slot["serial"]), 45))
    Gumps.AddLabel(gump, 365, y + 27, LABEL_HUE, _short_text(_smart_mapping_label(index), 55))


def _render_smart_config(gump):
    start = _smart_page * SMART_ROWS_PER_PAGE
    end = min(start + SMART_ROWS_PER_PAGE, MAX_SMART_STORAGE)
    y = 70
    for index in range(start, end):
        _render_smart_row(gump, index, y)
        y += 54

    Gumps.AddLabel(gump, 18, 401, DIM_HUE, "Learn any shelf/tome/key. Protection controls direct moves; a shelf may still scan supported items.")
    _add_button(gump, 18, 427, BTN_PROTECT_ITEM, "Protect item/bag", GOOD_HUE)
    _add_button(gump, 190, 427, BTN_CLEAR_PROTECTED, "Clear list", BAD_HUE)
    Gumps.AddLabel(gump, 320, 428, LABEL_HUE, "Protected: {0}".format(len(_protected_serials)))


def _render_category_row(gump, category, index, y):
    key = category["key"]
    setting = _category_setting(key)
    Gumps.AddBackground(gump, 10, y, CONFIG_WIDTH - 20, 39, PANEL_ID)
    Gumps.AddAlphaRegion(gump, 10, y, CONFIG_WIDTH - 20, 39)

    toggle_hue = GOOD_HUE if setting["enabled"] else DIM_HUE
    _add_button(gump, 18, y + 8, BTN_CATEGORY_TOGGLE_BASE + index, "ON" if setting["enabled"] else "OFF", toggle_hue)
    Gumps.AddLabel(gump, 79, y + 8, TITLE_HUE, _short_text(category["label"], 25))
    Gumps.AddLabel(gump, 275, y + 8, DIM_HUE, "{0} rules".format(_catalog_counts.get(key, 0)))
    _add_button(gump, 355, y + 8, BTN_CATEGORY_TARGET_BASE + index, "Target", LABEL_HUE)
    _add_button(gump, 445, y + 8, BTN_CATEGORY_RESET_BASE + index, "Reset", BAD_HUE)
    ready = setting["enabled"] and _valid_item(setting["serial"])
    label = _item_label(setting["serial"], "No destination")
    Gumps.AddLabel(gump, 542, y + 8, GOOD_HUE if ready else DIM_HUE, _short_text(label, 31))


def _render_route_config(gump):
    start = _route_page * ROUTE_ROWS_PER_PAGE
    end = min(start + ROUTE_ROWS_PER_PAGE, len(_catalog_categories))
    y = 70
    for index in range(start, end):
        _render_category_row(gump, _catalog_categories[index], index, y)
        y += 43

    dump_y = 376
    Gumps.AddBackground(gump, 10, dump_y, CONFIG_WIDTH - 20, 46, PANEL_ID)
    Gumps.AddAlphaRegion(gump, 10, dump_y, CONFIG_WIDTH - 20, 46)
    _add_button(gump, 18, dump_y + 5, BTN_DUMP_TOGGLE, "ON" if _dump_setting["enabled"] else "OFF", GOOD_HUE if _dump_setting["enabled"] else DIM_HUE)
    Gumps.AddLabel(gump, 79, dump_y + 5, TITLE_HUE, "Unmatched Dump Chest")
    _add_button(gump, 275, dump_y + 5, BTN_DUMP_TARGET, "Target", LABEL_HUE)
    _add_button(gump, 365, dump_y + 5, BTN_DUMP_RESET, "Reset", BAD_HUE)
    dump_ready = _dump_setting["enabled"] and _valid_item(_dump_setting["serial"])
    Gumps.AddLabel(gump, 465, dump_y + 5, GOOD_HUE if dump_ready else DIM_HUE, _short_text(_item_label(_dump_setting["serial"], "Disabled/no target"), 40))
    Gumps.AddLabel(gump, 79, dump_y + 25, DIM_HUE, "Only unmatched top-level backpack items go here; matched items with missing routes stay put.")

    _add_button(gump, 18, 431, BTN_PROTECT_ITEM, "Protect item/bag", GOOD_HUE)
    _add_button(gump, 190, 431, BTN_CLEAR_PROTECTED, "Clear list", BAD_HUE)
    Gumps.AddLabel(gump, 320, 432, LABEL_HUE, "Protected: {0}".format(len(_protected_serials)))


def _render_config():
    global _dirty_ui, _render_stage
    _render_stage = "Config shell"
    Gumps.CloseGump(GUMP_ID)
    gump = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gump, 0)
    Gumps.AddBackground(gump, 0, 0, CONFIG_WIDTH, CONFIG_HEIGHT, BG_ID)
    Gumps.AddAlphaRegion(gump, 0, 0, CONFIG_WIDTH, CONFIG_HEIGHT)
    _add_header(gump, CONFIG_WIDTH, "FROG BUTLER CONFIGS", True)
    _render_config_tabs(gump)

    _render_stage = "Config rows"
    if _config_view == CONFIG_VIEW_SMART:
        _render_smart_config(gump)
    else:
        _render_route_config(gump)

    profile_name = Path.GetFileName(_settings_path) if _settings_path else "No character profile"
    Gumps.AddLabel(gump, 12, CONFIG_HEIGHT - 39, DIM_HUE, _short_text(str(profile_name), 58))
    Gumps.AddLabel(gump, 12, CONFIG_HEIGHT - 21, _status_hue, _short_text(_status_msg, 118))
    Gumps.SendGump(GUMP_ID, Player.Serial, GUMP_X, GUMP_Y, gump.gumpDefinition, gump.gumpStrings)
    _render_stage = "Complete"
    _dirty_ui = False


def _render_error(error):
    global _dirty_ui
    try:
        Gumps.CloseGump(GUMP_ID)
        gump = Gumps.CreateGump(movable=True)
        Gumps.AddPage(gump, 0)
        Gumps.AddBackground(gump, 0, 0, 520, 115, BG_ID)
        Gumps.AddItem(gump, 7, 5, FROG_ICON, TITLE_HUE)
        Gumps.AddLabel(gump, 40, 8, BAD_HUE, "FROG BUTLER GUI ERROR")
        Gumps.AddButton(gump, 490, 7, 4017, 4018, BTN_CLOSE, 1, 0)
        Gumps.AddLabel(gump, 12, 38, WARN_HUE, "Stage: " + _short_text(_render_stage, 65))
        Gumps.AddLabel(gump, 12, 61, BAD_HUE, _short_text(str(error), 78))
        Gumps.AddLabel(gump, 12, 84, DIM_HUE, "Stop the script and report this stage/message.")
        Gumps.SendGump(GUMP_ID, Player.Serial, GUMP_X, GUMP_Y, gump.gumpDefinition, gump.gumpStrings)
        _dirty_ui = False
    except:
        Misc.SendMessage("Frog Butler render failed at {0}: {1}".format(_render_stage, str(error)), BAD_HUE)


def _render_gui_safe():
    try:
        if _current_page == "config":
            _render_config()
        else:
            _render_home()
    except Exception as error:
        _render_error(error)


# ===========================================================
# BUTTON HANDLING
# ===========================================================

def _index_for_button(button_id, base, count):
    index = int(button_id) - int(base)
    if index < 0 or index >= count:
        return -1
    return index


def _change_config_page(direction):
    global _smart_page, _route_page, _dirty_ui
    if _config_view == CONFIG_VIEW_SMART:
        total = _page_count(MAX_SMART_STORAGE, SMART_ROWS_PER_PAGE)
        _smart_page = (_smart_page + direction) % total
    else:
        total = _page_count(len(_catalog_categories), ROUTE_ROWS_PER_PAGE)
        _route_page = (_route_page + direction) % total
    _dirty_ui = True


def _handle_button(button_id):
    global _running, _current_page, _config_view, _dirty_ui

    if button_id == BTN_CLOSE:
        _running = False
        return
    if button_id == BTN_BACK:
        _current_page = "home"
        _dirty_ui = True
        return
    if button_id == BTN_CONFIG:
        _current_page = "config"
        _dirty_ui = True
        return
    if button_id == BTN_STORE_ALL:
        _start_store_all()
        return
    if button_id == BTN_CONFIG_VIEW:
        _config_view = CONFIG_VIEW_ROUTES if _config_view == CONFIG_VIEW_SMART else CONFIG_VIEW_SMART
        _dirty_ui = True
        return
    if button_id == BTN_PAGE_PREV:
        _change_config_page(-1)
        return
    if button_id == BTN_PAGE_NEXT:
        _change_config_page(1)
        return
    if button_id == BTN_RELOAD_CATALOG:
        _reload_catalog()
        return
    if button_id == BTN_PROTECT_ITEM:
        _protect_item()
        return
    if button_id == BTN_CLEAR_PROTECTED:
        _clear_protected()
        return
    if button_id == BTN_DUMP_TOGGLE:
        _toggle_dump()
        return
    if button_id == BTN_DUMP_TARGET:
        _target_dump()
        return
    if button_id == BTN_DUMP_RESET:
        _reset_dump()
        return

    index = _index_for_button(button_id, BTN_SMART_TOGGLE_BASE, MAX_SMART_STORAGE)
    if index >= 0:
        _toggle_smart(index)
        return
    index = _index_for_button(button_id, BTN_SMART_TARGET_BASE, MAX_SMART_STORAGE)
    if index >= 0:
        _target_smart(index)
        return
    index = _index_for_button(button_id, BTN_SMART_LEARN_BASE, MAX_SMART_STORAGE)
    if index >= 0:
        _learn_smart(index)
        return
    index = _index_for_button(button_id, BTN_SMART_RESET_BASE, MAX_SMART_STORAGE)
    if index >= 0:
        _reset_smart(index)
        return

    count = len(_catalog_categories)
    index = _index_for_button(button_id, BTN_CATEGORY_TOGGLE_BASE, count)
    if index >= 0:
        _toggle_category(_catalog_categories[index]["key"])
        return
    index = _index_for_button(button_id, BTN_CATEGORY_TARGET_BASE, count)
    if index >= 0:
        _target_category(_catalog_categories[index]["key"])
        return
    index = _index_for_button(button_id, BTN_CATEGORY_RESET_BASE, count)
    if index >= 0:
        _reset_category(_catalog_categories[index]["key"])


# ===========================================================
# MAIN
# ===========================================================

def Main():
    global _project_directory, _dirty_ui

    _project_directory = _script_directory()
    catalog_loaded = _load_catalog()
    _load_character_settings()
    if not catalog_loaded:
        _set_status("Catalog rejected: " + _short_text(_catalog_error, 60), BAD_HUE)
    _render_gui_safe()

    try:
        while _running and Player.Connected:
            handled_button = False
            try:
                gump_data = Gumps.GetGumpData(GUMP_ID)
            except:
                gump_data = None

            button_id = int(getattr(gump_data, "buttonid", 0) or 0) if gump_data else 0
            if button_id > 0:
                try:
                    gump_data.buttonid = 0
                except:
                    pass
                Gumps.CloseGump(GUMP_ID)
                _handle_button(button_id)
                handled_button = True
                Misc.Pause(BUTTON_DEBOUNCE_MS)

            if not _running:
                break

            if not handled_button:
                if _store_active:
                    _store_all_step()

                try:
                    gump_missing = Gumps.GetGumpData(GUMP_ID) is None
                except:
                    gump_missing = True
                if _dirty_ui or gump_missing:
                    _render_gui_safe()

            Misc.Pause(REFRESH_MS)
    finally:
        _stop_response_capture()
        if Target.HasTarget():
            Target.Cancel()
        Gumps.CloseGump(GUMP_ID)


Main()
