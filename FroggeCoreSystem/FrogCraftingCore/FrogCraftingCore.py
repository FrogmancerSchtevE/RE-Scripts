# ==================================================
# === Frog Crafting Core (Razor Enhanced Script) ===
# ==================================================
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

import clr
clr.AddReference("System.Web.Extensions")

import json
import re
import time

from System.IO import Directory, File, Path
from System.Web.Script.Serialization import JavaScriptSerializer

import Gumps
import Items
import Journal
import Misc
import Player
import Target

try:
    from System import String
except:
    String = None

try:
    from System.Collections import IDictionary, IEnumerable
except:
    IDictionary = None
    IEnumerable = None


# ===========================================================
# USER SETTINGS
# ===========================================================

# Leave blank unless Razor Enhanced cannot locate this suite folder.
PROJECT_DIRECTORY_OVERRIDE = ""

DEFAULT_CRAFT_AMOUNT = 10
MAX_CRAFT_AMOUNT = 9999
DEFAULT_TOOL_BOOK_CHARGES = 50
RESTOCK_CHUNK_CRAFTS = 25

# The Resource Shelf withdrawal text must be set and locked to this value
# by the player. The core intentionally does not edit that server text field.
RESOURCE_SHELF_WITHDRAW_AMOUNT = 100


# ===========================================================
# CONFIGURATION
# ===========================================================

VERSION = "1.0"
PROJECT_FOLDER = "FrogCraftingCore"
IN_DEVELOPMENT_FOLDER = "In Development"
MODULE_DIRECTORY = "Modules"
TRAINING_DIRECTORY = "Training"
DATA_DIRECTORY = "Data"
PLUGIN_DIRECTORY = "Plugins"
SETTINGS_DIRECTORY = "Settings"
SETTINGS_FORMAT = "frog-crafting-character-settings"
RESOURCE_SHELF_FILE = "resource_shelf.json"
REAGENT_SHELF_FILE = "reagent_gem_shelf.json"
INGREDIENT_IDS_FILE = "ingredient_ids.json"

CORE_GUMP_ID = 0xF2064643
GUMP_X, GUMP_Y = 520, 210
GUMP_WIDTH = 670
CRAFT_GUMP_HEIGHT = 506
TRAIN_GUMP_WIDTH = 560
TRAIN_GUMP_HEIGHT = 262
PLUGIN_GUMP_HEIGHT = 420
GLASSES_GUMP_HEIGHT = 360
REFRESH_MS = 100
BUTTON_DEBOUNCE_MS = 180
CRAFTING_GLASSES_VERIFY_MS = 2500
CRAFTING_GLASSES_POLL_MS = 100
CRAFTING_GLASSES_LAYER_SETTLE_MS = 500
CRAFTING_GLASSES_SWAP_SETTLE_MS = 1000
CRAFTING_GLASSES_SKILL_EPSILON = 0.01
ARTIFICER_GLASSES_ITEM_ID = 0x2FB8
TEMPLATE_CONFIRM_GUMP_ID = 0x11775C2E
TEMPLATE_CONFIRM_BUTTON = 1
TEMPLATE_GUMP_WAIT_MS = 3500
TEMPLATE_APPLY_WAIT_MS = 1500
TEMPLATE_COMMAND_COOLDOWN_MS = 4000
MAX_TEMPLATE_SLOT = 20

SERVER_GUMP_WAIT_MS = 2500
CRAFT_RESULT_PAUSE_MS = 700
CRAFT_FALLBACK_SETTLE_MS = 300
CRAFT_RESULT_POLL_MS = 50
CRAFT_MENU_SETTLE_MS = 75
CRAFT_OPEN_SETTLE_MS = 75
CRAFT_GUMP_RETURN_POLL_MS = 25
MAKE_LAST_CONFIRMATIONS_REQUIRED = 2
QUEST_RESULT_WAIT_MS = 2500
JOURNAL_POLL_MS = 100
MOVE_PAUSE_MS = 700
SHELF_DELIVERY_WAIT_MS = 4000
TARGET_CURSOR_WAIT_MS = 2500
TOOL_BOOK_GUMP_ID = 0xC3DE2C83
TOOL_BOOK_RETRIEVE_BUTTON = 100
TOOL_BOOK_TEXT_ENTRY_ID = 0
TOOL_BOOK_CATEGORY_FIELD_VALUE = "50"
MAX_CONSECUTIVE_FAILURES = 10
MAX_BUTTON_SEQUENCE_RETRIES = 3
MAX_ACTION_RETRIES = 3
GLOBAL_QUEST_SUCCESS_PREFIX = "global quest progress:"
GLOBAL_QUEST_SUCCESS_SUFFIX = " contributed"
WEEKLY_QUEST_SUCCESS_PREFIX = "weekly quest: crafted "
BOD_BOOK_PROGRESS_PATTERN = r"\bbod progress:\s*(\d+)\s*/\s*(\d+)\b"
BOD_BOOK_COMPLETE_PATTERN = r"\bbod complete!\s+you earned\s+([\d,]+)\s+artificer points?\b"
FOCUS_NEXT_BUTTON = 126
FOCUS_PREVIOUS_BUTTON = 119
FOCUS_ORDER = ("none", "bod_book", "weekly", "global", "guild")
FOCUS_TEXT = {
    "none": "No Crafting Focus Active. Items are not consumed",
    "bod_book": "Crafted items fill your active bulk order deeds book tasks",
    "weekly": "Crafted items count toward your weekly work orders",
    "global": "Crafted items contribute to the active global quest",
    "guild": "Crafted items advance your guild crafting quest",
}
FOCUS_LABELS = {"unchanged": "As-is", "none": "None", "bod_book": "BOD Book", "weekly": "Weekly", "global": "Global", "guild": "Guild"}

BG_ID = 5054
TITLE_HUE = 1152
LABEL_HUE = 0x0481
DIM_HUE = 0x044E
GOOD_HUE = 68
WARN_HUE = 53
BAD_HUE = 33

CATEGORY_ROWS = 9
RECIPE_ROWS = 10

SOURCE_CHEST = "chest"
SOURCE_SHELF = "shelf"
RESOURCE_SHELF_IDS = (0x71FC, 0x71FD)
REAGENT_SHELF_IDS = (0xAFC1, 0xAFC2)

VIEW_HOME = "home"
VIEW_CRAFT = "craft"
VIEW_TRAINING = "training"
VIEW_PLUGIN = "plugin"
VIEW_GLASSES = "glasses"
VIEW_TEMPLATES = "templates"

CRAFTING_GLASSES_PROFILES = (
    {"id": "blacksmithy", "label": "Blacksmith", "aliases": ("blacksmith", "blacksmithy", "blacksmithing")},
    {"id": "fletching", "label": "Bowcraft/Fletching", "aliases": ("bowcraft", "fletching", "bowcraft/fletching", "bowcraft and fletching", "bowcraft & fletching")},
    {"id": "carpentry", "label": "Carpentry", "aliases": ("carpentry",)},
    {"id": "cooking", "label": "Cooking", "aliases": ("cooking",)},
    {"id": "inscription", "label": "Inscription", "aliases": ("inscription",)},
    {"id": "cartography", "label": "Cartography", "aliases": ("cartography",)},
    {"id": "alchemy", "label": "Alchemy", "aliases": ("alchemy",)},
    {"id": "tailoring", "label": "Tailoring", "aliases": ("tailoring",)},
    {"id": "tinkering", "label": "Tinkering", "aliases": ("tinkering",)},
)
CRAFT_SKILL_PROFILES = CRAFTING_GLASSES_PROFILES

DISPOSAL_NONE = "none"
DISPOSAL_SAVE = "save"
DISPOSAL_TRASH = "trash"
DISPOSAL_SMELT = "smelt"
DISPOSAL_SALVAGE = "salvage"
DISPOSAL_RECYCLE = "recycle"
TARGETED_DISPOSAL_MODES = (DISPOSAL_SMELT, DISPOSAL_SALVAGE, DISPOSAL_RECYCLE)

KEY_PREFIX = "frog_crafting_core_"
KEY_AMOUNT = KEY_PREFIX + "amount"
KEY_SOURCE_MODE = KEY_PREFIX + "source_mode"
KEY_RESOURCE_CHEST = KEY_PREFIX + "resource_chest"
KEY_RESOURCE_SHELF = KEY_PREFIX + "resource_shelf"
KEY_REAGENT_SHELF = KEY_PREFIX + "reagent_shelf"
KEY_OUTPUT_CHEST = KEY_PREFIX + "output_chest"
KEY_TOOL_BOOK = KEY_PREFIX + "tool_book"
KEY_TRASH_CONTAINER = KEY_PREFIX + "trash_container"
KEY_CRAFT_BAG_ENABLED = KEY_PREFIX + "craft_bag_enabled"
KEY_CRAFT_BAG = KEY_PREFIX + "craft_bag"
KEY_MODULE_ID = KEY_PREFIX + "module_id"
KEY_CRAFT_FOCUS = KEY_PREFIX + "craft_focus"


# ===========================================================
# BUTTON IDS
# ===========================================================

BTN_CLOSE = 9000
BTN_TOGGLE_RUN = 9001
BTN_CANCEL = 9002
BTN_HOME = 9003

BTN_MODULE_PREV = 9010
BTN_MODULE_NEXT = 9011
BTN_MODULE_RELOAD = 9012

BTN_CATEGORY_PREV = 9020
BTN_CATEGORY_NEXT = 9021
BTN_RECIPE_PREV = 9022
BTN_RECIPE_NEXT = 9023

BTN_AMOUNT_MINUS_10 = 9030
BTN_AMOUNT_MINUS_1 = 9031
BTN_AMOUNT_PLUS_1 = 9032
BTN_AMOUNT_PLUS_10 = 9033
BTN_AMOUNT_MINUS_100 = 9034
BTN_AMOUNT_PLUS_100 = 9035

BTN_SOURCE_TOGGLE = 9040
BTN_SET_RESOURCE_CHEST = 9041
BTN_SET_RESOURCE_SHELF = 9042
BTN_SET_OUTPUT_CHEST = 9043
BTN_SET_TOOL_BOOK = 9044
BTN_SET_TRASH_CONTAINER = 9045
BTN_CRAFT_BAG_TOGGLE = 9046
BTN_SET_CRAFT_BAG = 9047
BTN_SET_REAGENT_SHELF = 9048
BTN_FOCUS_PREV = 9049

BTN_CHOICE_GROUP_NEXT = 9050
BTN_CHOICE_PREV = 9051
BTN_CHOICE_NEXT = 9052
BTN_FOCUS_NEXT = 9053
BTN_GLASSES_SETUP = 9054
BTN_GLASSES_BACK = 9055
BTN_TEMPLATES_SETUP = 9056
BTN_TEMPLATES_BACK = 9057
BTN_TEMPLATE_FORGET_ACTIVE = 9058

BTN_ACTION_SMELT = 9060
BTN_ACTION_REPAIR = 9061
BTN_ACTION_MARK = 9062
BTN_ACTION_SALVAGE = 9063
BTN_ACTION_RECYCLE = 9064

BTN_TRAIN_TOGGLE = 9070
BTN_TRAIN_WORKBENCH = 9071

BTN_CATEGORY_BASE = 10000
BTN_RECIPE_BASE = 11000
BTN_MODULE_BASE = 12000
BTN_TRAINING_MODULE_BASE = 13000
BTN_PLUGIN_BASE = 14000
BTN_GLASSES_SET_BASE = 15000
BTN_GLASSES_CLEAR_BASE = 15100
BTN_TEMPLATE_MINUS_BASE = 15200
BTN_TEMPLATE_PLUS_BASE = 15300

PLUGIN_BUTTON_BASE = 20000
PLUGIN_BUTTON_STRIDE = 1000


# ===========================================================
# GLOBAL STATE
# ===========================================================

_running = True
_runtime_active = False
_status_msg = "Loading crafting modules..."
_status_hue = WARN_HUE
_step_name = "Startup"
_dirty_ui = True
_last_ui_snapshot = None
_render_stage = "Not started"

_serializer = JavaScriptSerializer()
_project_directory = ""
_settings_path = ""
_settings_data = {}
_settings_dirty = False
_settings_write_blocked = False
_settings_warning_logged = False
_module_directory_path = ""
_module_files = []
_modules = []
_module_errors = []
_training_directory_path = ""
_training_profiles = {}
_training_errors = []
_plugin_directory_path = ""
_plugins = []
_plugin_errors = []
_active_plugin_id = ""
_plugin_craft_owner = ""
_plugin_craft_context = {}
_craft_focus = "unchanged"
_active_module_index = 0
_current_view = VIEW_HOME

_shelf_data = {}
_shelf_resources = {}
_reagent_shelf_data = {}
_reagent_shelf_resources = {}

_selected_category_id = ""
_selected_recipe_id = ""
_category_page = 0
_recipe_page = 0
_choice_group_index = 0
_choice_indices = {}

_category_button_map = {}
_recipe_button_map = {}
_module_button_map = {}
_training_module_button_map = {}
_plugin_button_map = {}
_glasses_set_button_map = {}
_glasses_clear_button_map = {}
_template_minus_button_map = {}
_template_plus_button_map = {}

_target_amount = DEFAULT_CRAFT_AMOUNT
_completed_amount = 0
_consecutive_failures = 0
_button_sequence_failures = 0
_verified_make_last_signature = ""
_make_last_candidate_signature = ""
_make_last_confirmation_count = 0
_make_last_gump_id = 0
_action_failures = {}
_operation_interrupted = False
_component_recipe_stack = []
_component_parent_focus = ""

_session_resources = []
_cleanup_active = False
_cleanup_stage = ""
_cleanup_resources = []
_cleanup_final_message = ""
_cleanup_final_hue = GOOD_HUE
_cleanup_final_step = "Complete"
_cleanup_head_message = ""
_cleanup_returned = 0
_cleanup_notes = []
_cleanup_retry_count = 0
_cleanup_skipped_serials = []
_plugin_cleanup_saved_bag_enabled = None

_training_active = False
_training_crafts = 0
_training_start_skill = 0.0
_training_session_module_id = ""
_training_pending_outputs = []
_training_pending_disposal = {}
_training_pending_module_id = ""
_training_pending_recipe_id = ""
_training_pending_recipe_name = ""
_training_pending_recovery = []
_training_pending_recovery_module_id = ""
_training_pending_recovery_completion = ""

_source_mode = SOURCE_CHEST
_resource_chest_serial = 0
_resource_shelf_serial = 0
_reagent_shelf_serial = 0
_output_chest_serial = 0
_tool_book_serial = 0
_trash_container_serial = 0
_craft_bag_enabled = False
_craft_bag_serial = 0
_crafting_glasses_serials = {}
_crafting_glasses_bonus_cache = {}
_verified_glasses_serial = 0
_verified_glasses_skill_name = ""
_verified_glasses_skill_value = 0.0
_crafting_template_map = {}
_known_active_template = 0
_last_template_command_at = 0.0


# ===========================================================
# BASIC HELPERS
# ===========================================================

def set_status(message, hue=LABEL_HUE, step=None):
    global _status_msg, _status_hue, _step_name, _dirty_ui

    changed = _status_msg != str(message) or _status_hue != int(hue)
    _status_msg = str(message)
    _status_hue = int(hue)

    if step is not None and _step_name != str(step):
        _step_name = str(step)
        changed = True

    if changed:
        _dirty_ui = True


def training_work_pending():
    return bool(_training_pending_outputs or _training_pending_recovery)


def short_text(value, length):
    text = str(value or "")
    if len(text) <= length:
        return text
    return text[:max(0, length - 3)] + "..."


def wrapped_text_lines(value, width, maximum_lines=2):
    words = str(value or "").split()
    if not words:
        return [""]

    width = max(1, int_value(width, 1))
    maximum_lines = max(1, int_value(maximum_lines, 1))
    lines = []
    current = ""

    for index in range(len(words)):
        word = words[index]
        candidate = word if not current else current + " " + word
        if not current or len(candidate) <= width:
            current = candidate
            continue

        lines.append(current)
        current = word
        if len(lines) >= maximum_lines - 1:
            remainder = " ".join([current] + words[index + 1:])
            lines.append(short_text(remainder, width))
            return lines

    if current:
        lines.append(short_text(current, width))
    return lines[:maximum_lines]


def clean_key(value):
    cleaned = []
    for char in str(value or "").strip().lower():
        if char.isalnum() or char in ("-", "_"):
            cleaned.append(char)
        elif cleaned and cleaned[-1] != "_":
            cleaned.append("_")
    return "".join(cleaned).strip("_")


def normalized_item_name(value):
    cleaned = []
    text = str(value or "").strip().lower().replace("’", "'").replace("‘", "'")
    for char in text:
        if char.isalnum():
            cleaned.append(char)
        elif cleaned and cleaned[-1] != " ":
            cleaned.append(" ")
    return " ".join("".join(cleaned).split())


def int_value(value, fallback=0):
    try:
        text = str(value).strip().lower()
        if text.startswith("0x"):
            return int(text, 16)
        return int(value)
    except:
        return int(fallback)


def number_value(value, fallback=None):
    try:
        return float(value)
    except:
        return fallback


def list_value(value):
    return value if isinstance(value, list) else []


def dict_value(value):
    return value if isinstance(value, dict) else {}


def configured_names(record, field_name="item_names", include_name=True):
    names = []
    seen = []
    if not isinstance(record, dict):
        return names

    values = list_value(record.get(field_name))
    if include_name:
        values = values + [record.get("name")]

    for value in values:
        text = str(value or "").strip()
        normalized = normalized_item_name(text)
        if text and normalized and normalized not in seen:
            seen.append(normalized)
            names.append(text)
    return names


def close_gump(gump_id):
    try:
        Gumps.CloseGump(int(gump_id))
    except:
        pass


def gump_is_open(gump_id):
    try:
        return Gumps.GetGumpData(int(gump_id)) is not None
    except:
        try:
            return int(Gumps.CurrentGump()) == int(gump_id)
        except:
            return False


def valid_item(serial):
    if int_value(serial) <= 0:
        return None
    try:
        return Items.FindBySerial(int(serial))
    except:
        return None


def item_label(serial, unset_text):
    item = valid_item(serial)
    if not item:
        return unset_text

    try:
        name = str(item.Name or "")
    except:
        name = ""

    if name:
        return short_text(name, 22) + " [0x{0:X}]".format(int(serial))
    return "0x{0:X}".format(int(serial))


def craft_skill_profile(value):
    wanted_key = clean_key(value)
    wanted_name = normalized_item_name(value)
    for profile in CRAFT_SKILL_PROFILES:
        if wanted_key == clean_key(profile.get("id")):
            return profile
        if wanted_name == normalized_item_name(profile.get("label")):
            return profile
        for alias in profile.get("aliases", ()):
            if wanted_name == normalized_item_name(alias):
                return profile
    return None


def crafting_glasses_profile(value):
    return craft_skill_profile(value)


def crafting_glasses_profile_for_module(module):
    profile = crafting_glasses_profile(dict_value(module).get("id"))
    if profile:
        return profile
    return crafting_glasses_profile(dict_value(module).get("skill_name"))


def item_property_lines(item, wait_ms=0):
    if not item:
        return []
    if int_value(wait_ms) > 0:
        try:
            Items.WaitForProps(item, int(wait_ms))
        except:
            pass
    try:
        return [str(value or "").strip() for value in list(Items.GetPropStringList(item.Serial) or []) if str(value or "").strip()]
    except:
        return []


def crafting_glasses_bonus(item, profile, wait_ms=0):
    aliases = [normalized_item_name(value) for value in dict_value(profile).get("aliases", ())]
    aliases.append(normalized_item_name(dict_value(profile).get("label")))
    aliases = [value for value in aliases if value]
    best = 0.0
    for line in item_property_lines(item, wait_ms):
        normalized = normalized_item_name(line)
        if not any(alias in normalized for alias in aliases):
            continue
        for match in re.findall(r"[-+]?\d+(?:\.\d+)?", str(line)):
            try:
                value = float(match)
                if value > best:
                    best = value
            except:
                pass
    return best


def crafting_glasses_item_matches(item, profile, wait_ms=0):
    if not item or not profile:
        return False, 0.0, "item is unavailable"
    name = normalized_item_name(item_name(item))
    if int_value(getattr(item, "ItemID", 0)) != ARTIFICER_GLASSES_ITEM_ID and "artificer glasses" not in name:
        return False, 0.0, "target is not Artificer Glasses (0x{0:04X})".format(ARTIFICER_GLASSES_ITEM_ID)
    bonus = crafting_glasses_bonus(item, profile, wait_ms)
    return True, bonus, ""


def configured_crafting_glasses_serial(profile):
    if not profile:
        return 0
    return int_value(_crafting_glasses_serials.get(str(profile.get("id", ""))), 0)


def configured_crafting_glasses_bonus(profile, wait_ms=0):
    if not profile:
        return 0.0
    profile_id = str(profile.get("id", ""))
    serial = configured_crafting_glasses_serial(profile)
    item = valid_item(serial)
    if not item:
        return 0.0
    cached = _crafting_glasses_bonus_cache.get(profile_id)
    if isinstance(cached, tuple) and len(cached) == 2 and int_value(cached[0]) == serial:
        return number_value(cached[1], 0.0)
    matches, bonus, _reason = crafting_glasses_item_matches(item, profile, wait_ms)
    if matches:
        _crafting_glasses_bonus_cache[profile_id] = (serial, bonus)
        return bonus
    return 0.0


def equipped_earrings_serial():
    try:
        item = Player.GetItemOnLayer("Earrings")
        return int(item.Serial) if item else 0
    except:
        return 0


def crafting_glasses_equipped(serial, item=None):
    wanted = int_value(serial)
    if wanted <= 0:
        return False
    if equipped_earrings_serial() == wanted:
        return True
    candidate = item if item and int_value(getattr(item, "Serial", 0)) == wanted else valid_item(wanted)
    if not candidate:
        return False
    try:
        return int_value(candidate.Container) == int_value(Player.Serial) and clean_key(candidate.Layer) == "earrings"
    except:
        return False


def alternate_crafting_glasses(wanted_serial):
    wanted = int_value(wanted_serial)
    seen = set()
    for profile in CRAFTING_GLASSES_PROFILES:
        serial = configured_crafting_glasses_serial(profile)
        if serial <= 0 or serial == wanted or serial in seen:
            continue
        seen.add(serial)
        item = valid_item(serial)
        matches, _bonus, _reason = crafting_glasses_item_matches(item, profile, 0)
        if matches:
            return profile, item
    return None, None


def wait_for_crafting_glasses_swap_settle():
    deadline = time.time() + (float(CRAFTING_GLASSES_SWAP_SETTLE_MS) / 1000.0)
    while time.time() < deadline:
        if consume_priority_control_button():
            return False
        remaining_ms = max(1, int((deadline - time.time()) * 1000.0))
        Misc.Pause(min(CRAFTING_GLASSES_POLL_MS, remaining_ms))
    return True


def reset_verified_crafting_glasses():
    global _verified_glasses_serial, _verified_glasses_skill_name, _verified_glasses_skill_value

    _verified_glasses_serial = 0
    _verified_glasses_skill_name = ""
    _verified_glasses_skill_value = 0.0


def remember_verified_crafting_glasses(serial, skill_name, skill_value):
    global _verified_glasses_serial, _verified_glasses_skill_name, _verified_glasses_skill_value

    _verified_glasses_serial = int_value(serial)
    _verified_glasses_skill_name = str(skill_name or "")
    _verified_glasses_skill_value = number_value(skill_value, 0.0)


def verified_crafting_glasses_active(serial, skill_name):
    if int_value(serial) <= 0 or int_value(_verified_glasses_serial) != int_value(serial):
        return False
    if clean_key(_verified_glasses_skill_name) != clean_key(skill_name):
        return False
    current = player_modified_skill_value(skill_name)
    return current + CRAFTING_GLASSES_SKILL_EPSILON >= number_value(_verified_glasses_skill_value, 0.0)


def wait_for_crafting_glasses_equip(serial, skill_name, skill_before):
    deadline = time.time() + (float(CRAFTING_GLASSES_VERIFY_MS) / 1000.0)
    last_skill = number_value(skill_before, 0.0)
    layer_confirmed_at = 0.0
    while time.time() < deadline:
        last_skill = player_modified_skill_value(skill_name)
        if last_skill > number_value(skill_before, 0.0) + CRAFTING_GLASSES_SKILL_EPSILON:
            remember_verified_crafting_glasses(serial, skill_name, last_skill)
            return "ready", last_skill, "skill increase"
        if crafting_glasses_equipped(serial):
            if layer_confirmed_at <= 0.0:
                layer_confirmed_at = time.time()
            elif (time.time() - layer_confirmed_at) * 1000.0 >= CRAFTING_GLASSES_LAYER_SETTLE_MS:
                remember_verified_crafting_glasses(serial, skill_name, last_skill)
                return "ready", last_skill, "Earrings layer"
        if consume_priority_control_button():
            return "interrupted", last_skill, "player control"
        remaining_ms = max(1, int((deadline - time.time()) * 1000.0))
        Misc.Pause(min(CRAFTING_GLASSES_POLL_MS, remaining_ms))
    return "error", last_skill, "no Earrings-layer or skill increase confirmation"


def crafting_glasses_status(profile):
    serial = configured_crafting_glasses_serial(profile)
    if serial <= 0:
        return "Not set", DIM_HUE
    item = valid_item(serial)
    if not item:
        return "Missing [0x{0:X}]".format(serial), BAD_HUE
    bonus = configured_crafting_glasses_bonus(profile, 500)
    if bonus <= 0:
        return "Set [0x{0:X}]".format(serial), GOOD_HUE
    bonus_text = str(int(bonus)) if float(bonus).is_integer() else "{0:.1f}".format(bonus)
    return "+{0} [0x{1:X}]".format(bonus_text, serial), GOOD_HUE


def target_crafting_glasses(profile_id):
    global _crafting_glasses_serials, _crafting_glasses_bonus_cache, _dirty_ui

    profile = crafting_glasses_profile(profile_id)
    if not profile:
        set_status("Unknown crafting glasses profile.", BAD_HUE, "Glasses Setup")
        return

    Target.Cancel()
    serial = int_value(Target.PromptTarget("Target the {0} Artificer Glasses.".format(profile.get("label", "crafting"))), 0)
    item = valid_item(serial)
    if not item:
        set_status("Glasses target cancelled or unavailable.", WARN_HUE, "Glasses Setup")
        return

    matches, bonus, reason = crafting_glasses_item_matches(item, profile, 1500)
    if not matches:
        set_status("Could not set {0} glasses: {1}.".format(profile.get("label", "crafting"), reason), BAD_HUE, "Glasses Setup")
        return

    _crafting_glasses_serials[str(profile.get("id", ""))] = int(item.Serial)
    _crafting_glasses_bonus_cache[str(profile.get("id", ""))] = (int(item.Serial), bonus)
    reset_verified_crafting_glasses()
    save_settings()
    if bonus > 0:
        bonus_text = str(int(bonus)) if float(bonus).is_integer() else "{0:.1f}".format(bonus)
        message = "Saved {0} Artificer Glasses (+{1}).".format(profile.get("label", "crafting"), bonus_text)
    else:
        message = "Saved {0} Artificer Glasses; skill tooltip text was not required.".format(profile.get("label", "crafting"))
    set_status(message, GOOD_HUE, "Glasses Setup")
    _dirty_ui = True


def clear_crafting_glasses(profile_id):
    global _crafting_glasses_serials, _crafting_glasses_bonus_cache, _dirty_ui

    profile = crafting_glasses_profile(profile_id)
    if not profile:
        return
    _crafting_glasses_serials.pop(str(profile.get("id", "")), None)
    _crafting_glasses_bonus_cache.pop(str(profile.get("id", "")), None)
    reset_verified_crafting_glasses()
    save_settings()
    set_status("Cleared {0} Artificer Glasses.".format(profile.get("label", "crafting")), GOOD_HUE, "Glasses Setup")
    _dirty_ui = True


def ensure_crafting_glasses(module=None, skill_name=""):
    profile = crafting_glasses_profile_for_module(module) if module else crafting_glasses_profile(skill_name)
    if not profile:
        return "ready", ""
    serial = configured_crafting_glasses_serial(profile)
    if serial <= 0:
        return "ready", ""
    checked_skill = str(dict_value(module).get("skill_name", "")) if module else str(skill_name or "")
    if not checked_skill:
        checked_skill = str(profile.get("label", "crafting"))
    current_skill = player_modified_skill_value(checked_skill)
    item = valid_item(serial)
    if crafting_glasses_equipped(serial, item):
        remember_verified_crafting_glasses(serial, checked_skill, current_skill)
        return "ready", ""
    if verified_crafting_glasses_active(serial, checked_skill):
        return "ready", ""

    if not item:
        return "error", "Configured {0} Artificer Glasses are unavailable".format(profile.get("label", "crafting"))
    matches, _bonus, reason = crafting_glasses_item_matches(item, profile, 750)
    if not matches:
        return "error", "Configured {0} glasses are invalid: {1}".format(profile.get("label", "crafting"), reason)

    alternate_profile, alternate_item = (None, None)
    if equipped_earrings_serial() <= 0:
        alternate_profile, alternate_item = alternate_crafting_glasses(serial)
    if alternate_item:
        reset_verified_crafting_glasses()
        try:
            Items.UseItem(alternate_item)
        except Exception as ex:
            return "error", "Could not use alternate {0} Artificer Glasses before equipping {1}: {2}".format(alternate_profile.get("label", "crafting"), profile.get("label", "crafting"), ex)
        if not wait_for_crafting_glasses_swap_settle():
            return "interrupted", "Artificer Glasses alternate-pair swap was interrupted"
        current_skill = player_modified_skill_value(checked_skill)

    try:
        Items.UseItem(item)
    except Exception as ex:
        return "error", "Could not use {0} Artificer Glasses to equip them: {1}".format(profile.get("label", "crafting"), ex)
    equip_state, skill_after, verification = wait_for_crafting_glasses_equip(serial, checked_skill, current_skill)
    if equip_state == "interrupted":
        return "interrupted", "{0} Artificer Glasses equip was interrupted".format(profile.get("label", "crafting"))
    if equip_state != "ready":
        reset_verified_crafting_glasses()
        return "error", "{0} Artificer Glasses did not verify: {1} ({2:.1f} before, {3:.1f} after)".format(profile.get("label", "crafting"), verification, current_skill, skill_after)
    if verification == "skill increase":
        return "ready", "Equipped {0} Artificer Glasses; {1} rose from {2:.1f} to {3:.1f}".format(profile.get("label", "crafting"), checked_skill, current_skill, skill_after)
    return "ready", "Equipped {0} Artificer Glasses; verified on Earrings layer".format(profile.get("label", "crafting"))


def equipped_artificer_glasses_item():
    try:
        item = Player.GetItemOnLayer("Earrings")
    except:
        item = None
    if not item:
        return None
    name = normalized_item_name(item_name(item))
    if int_value(getattr(item, "ItemID", 0)) == ARTIFICER_GLASSES_ITEM_ID or "artificer glasses" in name:
        return item
    return None


def suppress_crafting_glasses_for_training():
    reset_verified_crafting_glasses()
    item = equipped_artificer_glasses_item()
    if not item:
        return "ready", ""
    backpack = Player.Backpack
    if not backpack:
        return "error", "Main backpack is unavailable; cannot remove Artificer Glasses for training"

    serial = int_value(item.Serial)
    try:
        Items.Move(serial, int(backpack.Serial), 0)
    except Exception as ex:
        return "error", "Could not remove Artificer Glasses for training: " + str(ex)

    deadline = time.time() + (float(CRAFTING_GLASSES_VERIFY_MS) / 1000.0)
    while time.time() < deadline:
        worn = equipped_artificer_glasses_item()
        moved = valid_item(serial)
        in_backpack = False
        if moved:
            try:
                in_backpack = int_value(moved.Container) == int_value(backpack.Serial)
            except:
                in_backpack = False
        if not worn and in_backpack:
            return "ready", "Moved Artificer Glasses to the main backpack for unmodified-skill training"
        if consume_priority_control_button():
            return "interrupted", "Training glasses removal was interrupted"
        remaining_ms = max(1, int((deadline - time.time()) * 1000.0))
        Misc.Pause(min(CRAFTING_GLASSES_POLL_MS, remaining_ms))
    return "error", "Artificer Glasses still appear equipped or did not reach the main backpack"


def crafting_template_profile_for_module(module):
    profile = craft_skill_profile(dict_value(module).get("id"))
    if profile:
        return profile
    return craft_skill_profile(dict_value(module).get("skill_name"))


def configured_crafting_template(profile):
    if not profile:
        return 0
    return int_value(_crafting_template_map.get(str(profile.get("id", ""))), 0)


def configured_template_for_skill(skill_name):
    return configured_crafting_template(craft_skill_profile(skill_name))


def pending_template_for_skill(skill_name):
    wanted = configured_template_for_skill(skill_name)
    if wanted > 0 and wanted != int_value(_known_active_template):
        return wanted
    return 0


def change_crafting_template(profile_id, direction):
    global _crafting_template_map, _dirty_ui

    profile = craft_skill_profile(profile_id)
    if not profile:
        return
    profile_id = str(profile.get("id", ""))
    current = configured_crafting_template(profile)
    if int_value(direction) < 0:
        updated = max(0, current - 1)
    else:
        updated = 1 if current <= 0 else min(MAX_TEMPLATE_SLOT, current + 1)
    if updated > 0:
        _crafting_template_map[profile_id] = updated
    else:
        _crafting_template_map.pop(profile_id, None)
    reset_make_last(True)
    save_settings()
    label = "[template {0}".format(updated) if updated > 0 else "Unassigned"
    set_status("{0} template: {1}.".format(profile.get("label", "Crafting"), label), GOOD_HUE, "Template Setup")
    _dirty_ui = True


def forget_active_template():
    global _known_active_template, _dirty_ui

    _known_active_template = 0
    reset_make_last(True)
    close_gump(TEMPLATE_CONFIRM_GUMP_ID)
    set_status("Active template forgotten; the next mapped craft will synchronize it.", WARN_HUE, "Template Setup")
    _dirty_ui = True


def wait_for_template_command_cooldown():
    if _last_template_command_at <= 0.0 or TEMPLATE_COMMAND_COOLDOWN_MS <= 0:
        return True
    deadline = _last_template_command_at + (float(TEMPLATE_COMMAND_COOLDOWN_MS) / 1000.0)
    while time.time() < deadline:
        if consume_priority_control_button():
            return False
        remaining_ms = max(1, int((deadline - time.time()) * 1000.0))
        Misc.Pause(min(100, remaining_ms))
    return True


def wait_for_template_apply():
    deadline = time.time() + (float(TEMPLATE_APPLY_WAIT_MS) / 1000.0)
    while time.time() < deadline:
        if consume_priority_control_button():
            return False
        remaining_ms = max(1, int((deadline - time.time()) * 1000.0))
        Misc.Pause(min(100, remaining_ms))
    return True


def ensure_crafting_template(module=None, skill_name=""):
    global _known_active_template, _last_template_command_at, _dirty_ui

    profile = crafting_template_profile_for_module(module) if module else craft_skill_profile(skill_name)
    wanted = configured_crafting_template(profile)
    if wanted <= 0 or wanted == int_value(_known_active_template):
        return "ready", ""

    reset_make_last(True)
    reset_verified_crafting_glasses()
    if not wait_for_template_command_cooldown():
        return "interrupted", "Template synchronization was interrupted"

    close_gump(TEMPLATE_CONFIRM_GUMP_ID)
    try:
        Gumps.ResetGump()
    except:
        pass
    try:
        Player.ChatSay("[template {0}".format(wanted))
        _last_template_command_at = time.time()
        Gumps.WaitForGump(TEMPLATE_CONFIRM_GUMP_ID, TEMPLATE_GUMP_WAIT_MS)
    except Exception as ex:
        close_gump(TEMPLATE_CONFIRM_GUMP_ID)
        return "error", "Could not request template {0}: {1}".format(wanted, ex)

    if consume_priority_control_button():
        close_gump(TEMPLATE_CONFIRM_GUMP_ID)
        return "interrupted", "Template synchronization was interrupted"
    if not gump_is_open(TEMPLATE_CONFIRM_GUMP_ID):
        return "error", "[template {0} did not open confirmation gump 0x{1:08X}".format(wanted, TEMPLATE_CONFIRM_GUMP_ID)

    try:
        Gumps.SendAction(TEMPLATE_CONFIRM_GUMP_ID, TEMPLATE_CONFIRM_BUTTON)
    except Exception as ex:
        close_gump(TEMPLATE_CONFIRM_GUMP_ID)
        return "error", "Could not confirm template {0}: {1}".format(wanted, ex)

    if not wait_for_template_apply():
        close_gump(TEMPLATE_CONFIRM_GUMP_ID)
        return "interrupted", "Template {0} confirmation was interrupted".format(wanted)
    close_gump(TEMPLATE_CONFIRM_GUMP_ID)
    _known_active_template = wanted
    _dirty_ui = True
    return "ready", "Template {0} confirmed for {1}".format(wanted, profile.get("label", "crafting"))


def load_shared_int(key, fallback=0):
    try:
        if Misc.CheckSharedValue(key):
            return int(Misc.ReadSharedValue(key))
    except:
        pass
    return int(fallback)


def load_shared_text(key, fallback=""):
    try:
        if Misc.CheckSharedValue(key):
            return str(Misc.ReadSharedValue(key))
    except:
        pass
    return str(fallback)


def save_settings():
    global _settings_dirty

    module = active_module()
    plugin_context = dict_value(_plugin_craft_context) if _plugin_craft_owner else {}
    saved_bag_enabled = bool(plugin_context.get("craft_bag_enabled", _craft_bag_enabled))
    if _plugin_cleanup_saved_bag_enabled is not None:
        saved_bag_enabled = bool(_plugin_cleanup_saved_bag_enabled)
    saved_output_chest = int_value(plugin_context.get("output_chest_serial"), _output_chest_serial)
    core_settings = {
        "amount": int(_target_amount),
        "source_mode": str(_source_mode),
        "resource_chest": int(_resource_chest_serial),
        "resource_shelf": int(_resource_shelf_serial),
        "reagent_shelf": int(_reagent_shelf_serial),
        "output_chest": saved_output_chest,
        "tool_book": int(_tool_book_serial),
        "trash_container": int(_trash_container_serial),
        "craft_bag_enabled": saved_bag_enabled,
        "craft_bag": int(_craft_bag_serial),
        "module_id": str(module.get("id", "")) if module else "",
        "craft_focus": str(_craft_focus),
        "crafting_glasses": dict(_crafting_glasses_serials),
        "crafting_templates": dict(_crafting_template_map),
    }
    if _settings_data.get("core") != core_settings:
        _settings_data["core"] = core_settings
        _settings_dirty = True
    save_player_settings_json()

    try:
        Misc.SetSharedValue(KEY_AMOUNT, int(_target_amount))
        Misc.SetSharedValue(KEY_SOURCE_MODE, str(_source_mode))
        Misc.SetSharedValue(KEY_RESOURCE_CHEST, int(_resource_chest_serial))
        Misc.SetSharedValue(KEY_RESOURCE_SHELF, int(_resource_shelf_serial))
        Misc.SetSharedValue(KEY_REAGENT_SHELF, int(_reagent_shelf_serial))
        Misc.SetSharedValue(KEY_OUTPUT_CHEST, saved_output_chest)
        Misc.SetSharedValue(KEY_TOOL_BOOK, int(_tool_book_serial))
        Misc.SetSharedValue(KEY_TRASH_CONTAINER, int(_trash_container_serial))
        Misc.SetSharedValue(KEY_CRAFT_BAG_ENABLED, 1 if saved_bag_enabled else 0)
        Misc.SetSharedValue(KEY_CRAFT_BAG, int(_craft_bag_serial))
        Misc.SetSharedValue(KEY_CRAFT_FOCUS, str(_craft_focus))
        if module:
            Misc.SetSharedValue(KEY_MODULE_ID, str(module.get("id", "")))
    except:
        pass


def load_saved_settings():
    global _target_amount, _source_mode, _craft_bag_enabled, _craft_bag_serial
    global _resource_chest_serial, _resource_shelf_serial, _reagent_shelf_serial
    global _output_chest_serial, _tool_book_serial, _trash_container_serial
    global _craft_focus, _crafting_glasses_serials, _crafting_glasses_bonus_cache
    global _crafting_template_map, _known_active_template, _last_template_command_at

    load_player_settings_json()
    core_settings = dict_value(_settings_data.get("core"))

    _target_amount = max(1, min(MAX_CRAFT_AMOUNT, int_value(core_settings.get("amount"), load_shared_int(KEY_AMOUNT, DEFAULT_CRAFT_AMOUNT))))
    saved_mode = str(core_settings.get("source_mode", load_shared_text(KEY_SOURCE_MODE, SOURCE_CHEST))).lower()
    _source_mode = saved_mode if saved_mode in (SOURCE_CHEST, SOURCE_SHELF) else SOURCE_CHEST
    _resource_chest_serial = max(0, int_value(core_settings.get("resource_chest"), load_shared_int(KEY_RESOURCE_CHEST, 0)))
    _resource_shelf_serial = max(0, int_value(core_settings.get("resource_shelf"), load_shared_int(KEY_RESOURCE_SHELF, 0)))
    _reagent_shelf_serial = max(0, int_value(core_settings.get("reagent_shelf"), load_shared_int(KEY_REAGENT_SHELF, 0)))
    _output_chest_serial = max(0, int_value(core_settings.get("output_chest"), load_shared_int(KEY_OUTPUT_CHEST, 0)))
    _tool_book_serial = max(0, int_value(core_settings.get("tool_book"), load_shared_int(KEY_TOOL_BOOK, 0)))
    _trash_container_serial = max(0, int_value(core_settings.get("trash_container"), load_shared_int(KEY_TRASH_CONTAINER, 0)))
    _craft_bag_enabled = bool(core_settings.get("craft_bag_enabled", load_shared_int(KEY_CRAFT_BAG_ENABLED, 0) > 0))
    _craft_bag_serial = max(0, int_value(core_settings.get("craft_bag"), load_shared_int(KEY_CRAFT_BAG, 0)))
    saved_focus = str(core_settings.get("craft_focus", load_shared_text(KEY_CRAFT_FOCUS, "unchanged"))).lower()
    _craft_focus = saved_focus if saved_focus in FOCUS_ORDER or saved_focus == "unchanged" else "unchanged"
    saved_glasses = dict_value(core_settings.get("crafting_glasses"))
    _crafting_glasses_serials = {}
    _crafting_glasses_bonus_cache = {}
    reset_verified_crafting_glasses()
    for profile in CRAFTING_GLASSES_PROFILES:
        profile_id = str(profile.get("id", ""))
        serial = max(0, int_value(saved_glasses.get(profile_id), 0))
        if serial > 0:
            _crafting_glasses_serials[profile_id] = serial
    saved_templates = dict_value(core_settings.get("crafting_templates"))
    _crafting_template_map = {}
    for profile in CRAFT_SKILL_PROFILES:
        profile_id = str(profile.get("id", ""))
        template_id = max(0, min(MAX_TEMPLATE_SLOT, int_value(saved_templates.get(profile_id), 0)))
        if template_id > 0:
            _crafting_template_map[profile_id] = template_id
    _known_active_template = 0
    _last_template_command_at = 0.0


# ===========================================================
# JSON / PATH HELPERS
# ===========================================================

def combine_path(*parts):
    result = ""
    for part in parts:
        if part is None or str(part) == "":
            continue
        if not result:
            result = str(part)
        else:
            result = Path.Combine(result, str(part))
    return result


def settings_identity_candidates(project_directory):
    if not project_directory:
        return []

    candidates = []
    try:
        player_serial = int_value(Player.Serial)
    except:
        player_serial = 0
    try:
        backpack_serial = int_value(Player.Backpack.Serial)
    except:
        backpack_serial = 0

    for source, serial in (("player", player_serial), ("backpack", backpack_serial)):
        if serial in (0, -1):
            continue
        serial = serial & 0xFFFFFFFF
        if serial <= 0 or any(int(candidate[1]) == serial for candidate in candidates):
            continue
        filename = "character_0x{0:08X}.json".format(serial)
        candidates.append((source, serial, combine_path(project_directory, SETTINGS_DIRECTORY, filename)))
    return candidates


def select_settings_identity(project_directory):
    candidates = settings_identity_candidates(project_directory)
    for candidate in candidates:
        if File.Exists(candidate[2]):
            return candidate
    return candidates[0] if candidates else ("", 0, "")


def add_path_candidate(candidates, value):
    if not value:
        return

    try:
        normalized = Path.GetFullPath(str(value))
    except:
        normalized = str(value)

    for existing in candidates:
        if str(existing).lower() == normalized.lower():
            return
    candidates.append(normalized)


def build_project_candidates():
    candidates = []

    if PROJECT_DIRECTORY_OVERRIDE:
        add_path_candidate(candidates, PROJECT_DIRECTORY_OVERRIDE)

    try:
        script_file = globals().get("__file__")
        if script_file:
            add_path_candidate(candidates, Path.GetDirectoryName(Path.GetFullPath(str(script_file))))
    except:
        pass

    current_dir = Misc.CurrentScriptDirectory()
    add_path_candidate(candidates, current_dir)
    add_path_candidate(candidates, combine_path(current_dir, PROJECT_FOLDER))
    add_path_candidate(candidates, combine_path(current_dir, IN_DEVELOPMENT_FOLDER, PROJECT_FOLDER))

    return candidates


def resolve_project_directory():
    for candidate in build_project_candidates():
        try:
            if Directory.Exists(combine_path(candidate, MODULE_DIRECTORY)):
                return candidate
        except:
            pass
    return ""


def json_value_to_python(value):
    if value is None:
        return None

    if isinstance(value, dict):
        converted = {}
        for key, child in value.items():
            converted[str(key)] = json_value_to_python(child)
        return converted

    is_dotnet_dictionary = False
    try:
        is_dotnet_dictionary = IDictionary is not None and isinstance(value, IDictionary)
    except:
        pass

    if is_dotnet_dictionary or (hasattr(value, "Keys") and hasattr(value, "__getitem__")):
        converted = {}
        try:
            for key in value.Keys:
                converted[str(key)] = json_value_to_python(value[key])
            return converted
        except:
            pass

    if isinstance(value, str):
        return value

    try:
        if String is not None and isinstance(value, String):
            return str(value)
    except:
        pass

    if isinstance(value, (list, tuple)):
        return [json_value_to_python(child) for child in value]

    try:
        if IEnumerable is not None and isinstance(value, IEnumerable):
            return [json_value_to_python(child) for child in value]
    except:
        pass

    return value


def read_json_file(path):
    text = File.ReadAllText(path)
    raw = _serializer.DeserializeObject(text)
    return json_value_to_python(raw)


def load_player_settings_json():
    global _settings_path, _settings_data, _settings_dirty, _settings_write_blocked

    project_directory = resolve_project_directory()
    identity_source, character_serial, selected_path = select_settings_identity(project_directory)
    _settings_path = ""
    _settings_data = {
        "format": SETTINGS_FORMAT,
        "version": 1,
        "character_serial": character_serial,
        "identity_source": identity_source,
        "core": {},
        "plugins": {},
    }
    _settings_dirty = False
    _settings_write_blocked = False

    if not selected_path:
        Misc.SendMessage("Frog Crafting settings cannot load: suite folder or player/backpack serial is unavailable.", WARN_HUE)
        return

    _settings_path = selected_path
    if not File.Exists(_settings_path):
        return

    try:
        data = read_json_file(_settings_path)
        if not isinstance(data, dict) or data.get("format") != SETTINGS_FORMAT:
            raise Exception("unsupported settings format")
        if int_value(data.get("version")) != 1 or int_value(data.get("character_serial")) != character_serial:
            raise Exception("settings version or character does not match")
        if not isinstance(data.get("core"), dict) or not isinstance(data.get("plugins"), dict):
            raise Exception("settings sections are invalid")
        _settings_data = data
    except Exception as ex:

        _settings_write_blocked = True
        Misc.SendMessage("Frog Crafting settings JSON could not load; persistence is paused: " + str(ex), BAD_HUE)


def save_player_settings_json():
    global _settings_path, _settings_dirty, _settings_write_blocked, _settings_warning_logged

    if _settings_write_blocked:
        return False

    if not _settings_path:
        project_directory = _project_directory or resolve_project_directory()
        identity_source, character_serial, candidate = select_settings_identity(project_directory)
        if candidate:
            if File.Exists(candidate):
                _settings_write_blocked = True
                Misc.SendMessage("Frog Crafting settings file appeared after startup; restart to load it before saving: " + candidate, BAD_HUE)
                return False
            _settings_path = candidate
            _settings_data["character_serial"] = character_serial
            _settings_data["identity_source"] = identity_source
            _settings_warning_logged = False

    if not _settings_path:
        if not _settings_warning_logged:
            try:
                player_serial = Player.Serial
            except:
                player_serial = "unavailable"
            try:
                backpack_serial = Player.Backpack.Serial
            except:
                backpack_serial = "unavailable"
            Misc.SendMessage("Frog Crafting settings could not save: player serial={0}, backpack serial={1}.".format(player_serial, backpack_serial), BAD_HUE)
            Misc.SendMessage("Frog Crafting settings project: " + str(_project_directory or resolve_project_directory()), BAD_HUE)
            _settings_warning_logged = True
        return False

    if not _settings_dirty and File.Exists(_settings_path):
        return True

    temporary_path = _settings_path + ".tmp"
    first_save = not File.Exists(_settings_path)
    try:
        Directory.CreateDirectory(Path.GetDirectoryName(_settings_path))
        File.WriteAllText(temporary_path, json.dumps(_settings_data, indent=2, sort_keys=True) + "\n")
        if File.Exists(_settings_path):
            File.Replace(temporary_path, _settings_path, _settings_path + ".bak")
        else:
            File.Move(temporary_path, _settings_path)
        _settings_dirty = False
        _settings_warning_logged = False
        if first_save:
            Misc.SendMessage("Frog Crafting settings saved ({0} identity): {1}".format(_settings_data.get("identity_source", "player"), _settings_path), GOOD_HUE)
        return True
    except Exception as ex:
        if not _settings_warning_logged:
            Misc.SendMessage("Frog Crafting settings JSON could not save at " + _settings_path + ": " + str(ex), BAD_HUE)
            _settings_warning_logged = True
        return False


def plugin_setting_value(key, fallback):
    global _settings_dirty

    values = dict_value(_settings_data.get("plugins"))
    if key in values:
        return values[key]
    values[key] = fallback
    _settings_data["plugins"] = values
    _settings_dirty = True
    return fallback


def save_plugin_setting(key, value):
    global _settings_dirty

    values = dict_value(_settings_data.get("plugins"))
    if values.get(key) != value:
        values[key] = value
        _settings_data["plugins"] = values
        _settings_dirty = True
    return save_player_settings_json()


def validate_module(data, path):
    if not isinstance(data, dict):
        raise Exception("module root is not an object")
    if data.get("format") != "frog-crafting-module":
        raise Exception("unsupported module format")
    if int_value(data.get("version")) != 1:
        raise Exception("unsupported module version")
    if not clean_key(data.get("id")):
        raise Exception("module id is missing or invalid")
    if not str(data.get("name", "")).strip():
        raise Exception("module name is missing")
    if int_value(data.get("craft_gump_id")) <= 0:
        raise Exception("craft_gump_id is missing")
    if not isinstance(data.get("categories"), list):
        raise Exception("categories must be a list")

    data["id"] = clean_key(data.get("id"))
    data["source_path"] = str(path)
    return data


def validate_training_profile(data, path):
    if not isinstance(data, dict):
        raise Exception("training root is not an object")
    if data.get("format") != "frog-crafting-training":
        raise Exception("unsupported training format")
    if int_value(data.get("version")) != 1:
        raise Exception("unsupported training version")

    module_id = clean_key(data.get("module_id"))
    if not module_id:
        raise Exception("module_id is missing or invalid")
    if number_value(data.get("target_skill"), None) is None:
        raise Exception("target_skill is missing")
    if not isinstance(data.get("stages"), list):
        raise Exception("stages must be a list")

    informational = bool(data.get("informational", False))
    if informational and not str(data.get("message", "")).strip():
        raise Exception("informational training requires a message")

    for index, raw_stage in enumerate(data.get("stages")):
        stage = dict_value(raw_stage)
        minimum = number_value(stage.get("min_skill"), None)
        maximum = number_value(stage.get("max_skill"), None)
        if minimum is None or maximum is None or maximum <= minimum:
            raise Exception("stage {0} has an invalid skill range".format(index + 1))
        mode = clean_key(stage.get("mode", "craft"))
        if mode not in ("craft", "npc_train"):
            raise Exception("stage {0} has invalid mode {1}".format(index + 1, mode))
        if mode == "craft" and not isinstance(stage.get("recipe_ids"), list):
            raise Exception("stage {0} recipe_ids must be a list".format(index + 1))

        disposal = dict_value(stage.get("disposal"))
        disposal_mode = clean_key(disposal.get("mode", DISPOSAL_NONE))
        valid_modes = (DISPOSAL_NONE, DISPOSAL_SAVE, DISPOSAL_TRASH) + TARGETED_DISPOSAL_MODES
        if disposal_mode not in valid_modes:
            raise Exception("stage {0} has invalid disposal mode {1}".format(index + 1, disposal_mode))

    data["module_id"] = module_id
    data["informational"] = informational
    data["source_path"] = str(path)
    return data


def load_training_profiles():
    global _training_directory_path, _training_profiles, _training_errors

    _training_directory_path = combine_path(_project_directory, TRAINING_DIRECTORY)
    _training_profiles = {}
    _training_errors = []

    try:
        if not Directory.Exists(_training_directory_path):
            _training_errors.append("Training folder was not found")
            return False
        paths = [str(path) for path in Directory.GetFiles(_training_directory_path, "*.json")]
        paths.sort(key=lambda value: value.lower())
    except Exception as ex:
        _training_errors.append("Could not enumerate Training: " + str(ex))
        return False

    valid_module_ids = [str(module.get("id", "")) for module in _modules]
    for path in paths:
        try:
            profile = validate_training_profile(read_json_file(path), path)
            module_id = str(profile.get("module_id", ""))
            if module_id not in valid_module_ids:
                raise Exception("module_id does not match a loaded craft module")
            if module_id in _training_profiles:
                raise Exception("duplicate training profile for " + module_id)
            _training_profiles[module_id] = profile
        except Exception as ex:
            _training_errors.append(Path.GetFileName(path) + ": " + str(ex))

    return bool(_training_profiles)


def load_resource_shelf_data():
    global _shelf_data, _shelf_resources

    _shelf_data = {}
    _shelf_resources = {}
    path = combine_path(_project_directory, DATA_DIRECTORY, RESOURCE_SHELF_FILE)

    try:
        data = read_json_file(path)
        if not isinstance(data, dict) or data.get("format") != "frog-resource-shelf":
            raise Exception("unsupported resource shelf data format")
        if int_value(data.get("version")) != 1:
            raise Exception("unsupported resource shelf data version")

        for resource in list_value(data.get("resources")):
            if not isinstance(resource, dict):
                continue
            key = clean_key(resource.get("id"))
            if key:
                _shelf_resources[key] = resource

        _shelf_data = data
        return True
    except Exception as ex:
        _module_errors.append("Resource shelf data: " + str(ex))
        return False


def load_reagent_shelf_data():
    global _reagent_shelf_data, _reagent_shelf_resources

    _reagent_shelf_data = {}
    _reagent_shelf_resources = {}
    path = combine_path(_project_directory, DATA_DIRECTORY, REAGENT_SHELF_FILE)

    try:
        data = read_json_file(path)
        if not isinstance(data, dict) or data.get("format") != "frog-reagent-gem-shelf":
            raise Exception("unsupported reagent shelf data format")
        if int_value(data.get("version")) != 1:
            raise Exception("unsupported reagent shelf data version")
        if int_value(data.get("gump_id")) <= 0:
            raise Exception("reagent shelf gump_id is missing")

        categories = {}
        for raw_category in list_value(data.get("categories")):
            category = dict_value(raw_category)
            category_id = clean_key(category.get("id"))
            category_button = int_value(category.get("button"))
            if not category_id or category_button <= 0:
                continue

            pages = {}
            for raw_page in list_value(category.get("pages")):
                page = dict_value(raw_page)
                page_number = int_value(page.get("number"))
                if page_number <= 0:
                    continue
                pages[page_number] = [int_value(value) for value in list_value(page.get("open_actions")) if int_value(value) > 0]

            categories[category_id] = {
                "button": category_button,
                "pages": pages,
            }

        for raw_resource in list_value(data.get("resources")):
            resource = dict_value(raw_resource)
            key = clean_key(resource.get("id"))
            category_id = clean_key(resource.get("category"))
            page_number = int_value(resource.get("page"))
            resource_button = int_value(resource.get("button"))
            string_id = int_value(resource.get("string_id"))
            category = categories.get(category_id)

            if not key:
                raise Exception("resource entry is missing id")
            if key in _reagent_shelf_resources:
                raise Exception("duplicate resource id " + key)
            if not category or page_number not in category.get("pages", {}):
                raise Exception("invalid category/page mapping for " + key)
            if resource_button <= 0 or string_id <= 0:
                raise Exception("invalid button/string mapping for " + key)

            mapped = {}
            for field, value in resource.items():
                mapped[field] = value
            actions = [int_value(category.get("button"))]
            actions.extend(list_value(category.get("pages", {}).get(page_number)))
            actions.append(resource_button)
            mapped["reagent_shelf_actions"] = actions
            mapped["reagent_shelf_string_id"] = string_id
            mapped["reagent_shelf_withdraw_amount"] = int_value(data.get("withdraw_amount"), 100)
            _reagent_shelf_resources[key] = mapped

            base = _shelf_resources.get(key)
            if not base:
                base = {
                    "id": key,
                    "name": str(resource.get("name", key)),
                    "shelf_page": None,
                    "shelf_button": None,
                    "item_id": resource.get("item_id"),
                    "hue": resource.get("hue"),
                    "item_names": [],
                }
                _shelf_resources[key] = base

            existing_names = configured_names(base)
            known = [value.lower() for value in existing_names]
            for name in configured_names(resource):
                if name.lower() not in known:
                    existing_names.append(name)
                    known.append(name.lower())
            base["item_names"] = existing_names
            base["reagent_shelf_actions"] = list(actions)
            base["reagent_shelf_string_id"] = string_id
            base["reagent_shelf_withdraw_amount"] = int_value(data.get("withdraw_amount"), 100)

        _reagent_shelf_data = data
        return True
    except Exception as ex:
        _module_errors.append("Reagent shelf data: " + str(ex))
        return False


def load_ingredient_id_data():
    path = combine_path(_project_directory, DATA_DIRECTORY, INGREDIENT_IDS_FILE)

    try:
        data = read_json_file(path)
        if not isinstance(data, dict) or data.get("format") != "frog-ingredient-identifiers":
            raise Exception("unsupported ingredient identifier format")
        if int_value(data.get("version")) != 1:
            raise Exception("unsupported ingredient identifier version")

        seen = []
        for entry in list_value(data.get("ingredients")):
            if not isinstance(entry, dict):
                _module_errors.append("Ingredient IDs: ignored a non-object entry")
                continue

            resource_key = clean_key(entry.get("resource_key"))
            if not resource_key:
                _module_errors.append("Ingredient IDs: ignored an entry with no resource_key")
                continue
            if resource_key in seen:
                _module_errors.append("Ingredient IDs: duplicate resource_key " + resource_key)
                continue
            seen.append(resource_key)

            resource = _shelf_resources.get(resource_key)
            if not resource:
                _module_errors.append("Ingredient IDs: unknown resource_key " + resource_key)
                continue

            raw_item_id = entry.get("item_id")
            if raw_item_id is not None and str(raw_item_id).strip():
                item_id = int_value(raw_item_id)
                if item_id <= 0:
                    _module_errors.append("Ingredient IDs: invalid item_id for " + resource_key)
                else:
                    resource["item_id"] = item_id

            raw_hue = entry.get("hue")
            if raw_hue is not None and str(raw_hue).strip():
                hue = int_value(raw_hue, -2)
                if hue < -1:
                    _module_errors.append("Ingredient IDs: invalid hue for " + resource_key)
                else:
                    resource["hue"] = hue

        return True
    except Exception as ex:
        _module_errors.append("Ingredient IDs: " + str(ex))
        return False


def load_modules():
    global _project_directory, _module_directory_path
    global _module_files, _modules, _module_errors, _active_module_index

    previous_id = ""
    current = active_module()
    if current:
        previous_id = str(current.get("id", ""))
    if not previous_id:
        previous_id = str(dict_value(_settings_data.get("core")).get("module_id", ""))
    if not previous_id:
        previous_id = load_shared_text(KEY_MODULE_ID, "")

    _project_directory = resolve_project_directory()
    _module_directory_path = ""
    _module_files = []
    _modules = []
    _module_errors = []
    _active_module_index = 0

    if not _project_directory:
        set_status("Could not locate the FrogCraftingCore folder.", BAD_HUE, "Load Modules")
        return False

    _module_directory_path = combine_path(_project_directory, MODULE_DIRECTORY)
    load_resource_shelf_data()
    load_reagent_shelf_data()
    load_ingredient_id_data()

    try:
        paths = [str(path) for path in Directory.GetFiles(_module_directory_path, "*.json")]
        paths.sort(key=lambda value: value.lower())
    except Exception as ex:
        set_status("Could not enumerate Modules: " + str(ex), BAD_HUE, "Load Modules")
        return False

    for path in paths:
        try:
            module = validate_module(read_json_file(path), path)
            _module_files.append(path)
            _modules.append(module)
        except Exception as ex:
            _module_errors.append(Path.GetFileName(path) + ": " + str(ex))

    if not _modules:
        set_status("No valid crafting modules found.", BAD_HUE, "Load Modules")
        return False

    load_training_profiles()

    for index, module in enumerate(_modules):
        if str(module.get("id", "")) == previous_id:
            _active_module_index = index
            break

    reset_module_view()
    save_settings()

    warning_count = len(_module_errors) + len(_training_errors)
    if warning_count:
        set_status("Loaded {0} craft and {1} training module(s); {2} warning(s).".format(len(_modules), len(_training_profiles), warning_count), WARN_HUE, "Ready")
    else:
        set_status("Loaded {0} craft and {1} training module(s).".format(len(_modules), len(_training_profiles)), GOOD_HUE, "Ready")
    return True


# ===========================================================
# CRAFTING PLUGINS
# ===========================================================

class CraftingPluginHost:
    def setting_key(self, key):
        return KEY_PREFIX + "plugin_" + clean_key(key)

    def read_int(self, key, fallback=0):
        legacy_value = load_shared_int(self.setting_key(key), fallback)
        return int_value(plugin_setting_value(str(key), legacy_value), fallback)

    def write_int(self, key, value):
        parsed = int_value(value)
        save_plugin_setting(str(key), parsed)
        try:
            Misc.SetSharedValue(self.setting_key(key), parsed)
        except:
            pass

    def read_text(self, key, fallback=""):
        legacy_value = load_shared_text(self.setting_key(key), fallback)
        return str(plugin_setting_value(str(key), legacy_value))

    def write_text(self, key, value):
        parsed = str(value)
        save_plugin_setting(str(key), parsed)
        try:
            Misc.SetSharedValue(self.setting_key(key), parsed)
        except:
            pass

    def set_status(self, message, hue=LABEL_HUE, step=None):
        set_status(message, hue, step)

    def mark_dirty(self):
        global _dirty_ui
        _dirty_ui = True

    def add_button(self, gd, x, y, button_id, label, hue=LABEL_HUE, art_up=4005, art_down=4007):
        add_button(gd, x, y, button_id, label, hue, art_up, art_down)

    def short_text(self, value, length):
        return short_text(value, length)

    def item_label(self, serial, unset_text="Not set"):
        return item_label(serial, unset_text)

    def valid_item(self, serial):
        return valid_item(serial)

    def target_container(self, prompt):
        serial = Target.PromptTarget(str(prompt))
        if int_value(serial) <= 0:
            return 0
        item = valid_item(serial)
        if not item or not bool(getattr(item, "IsContainer", False)):
            return 0
        return int(item.Serial)

    def overhead(self, message, hue=WARN_HUE):
        Player.HeadMessage(int(hue), str(message))

    def read_data(self, filename):
        path = combine_path(_project_directory, DATA_DIRECTORY, str(filename))
        if not File.Exists(path):
            raise Exception("data file is missing: " + str(filename))
        return read_json_file(path)

    def modules(self):
        return list(_modules)

    def module(self, module_id):
        return module_by_id(module_id)

    def plugin(self, plugin_id):
        return plugin_by_id(plugin_id)

    def skill_value(self, skill_name):
        return player_crafting_skill_value(skill_name, True)

    def pending_template_for_skill(self, skill_name):
        return pending_template_for_skill(skill_name)

    def craft_bag_serial(self):
        bag = craft_bag_item() if _craft_bag_enabled else None
        return int(bag.Serial) if bag else 0

    def craft_job_api_version(self):
        return 11

    def begin_craft_job(self, owner, module_id, category_id, recipe_id, amount, resource_choices=None, focus_override=None, workspace_override=None, ignore_skill_requirements=False):
        return begin_plugin_craft_job(owner, module_id, category_id, recipe_id, amount, resource_choices, focus_override, workspace_override, ignore_skill_requirements)

    def craft_job_status(self, owner):
        return plugin_craft_job_status(owner)

    def end_craft_job(self, owner, cancel=False):
        return end_plugin_craft_job(owner, cancel)

    def begin_craft_cleanup(self, owner, workspace_override=None):
        return begin_plugin_material_cleanup(owner, workspace_override)

    def craft_cleanup_active(self, owner):
        return plugin_material_cleanup_active(owner)

    def recycle_craft_bag_item(self, owner, module_id, recipe_id, item_serial, expected_item_id=0):
        return recycle_plugin_craft_bag_item(owner, module_id, recipe_id, item_serial, expected_item_id)

    def recycle_craft_bag_contents(self, owner, module_id, recipe_id, item_serials, expected_item_id=0):
        return recycle_plugin_craft_bag_contents(owner, module_id, recipe_id, item_serials, expected_item_id)

    def trash_craft_bag_item(self, owner, item_serial, expected_item_id=0):
        return trash_plugin_craft_bag_item(owner, item_serial, expected_item_id)


_plugin_host = CraftingPluginHost()


def plugin_namespace(path):
    return {
        "__file__": str(path),
        "__name__": "frog_crafting_plugin_" + clean_key(Path.GetFileNameWithoutExtension(path)),
        "Gumps": Gumps,
        "Items": Items,
        "Misc": Misc,
        "Player": Player,
        "Target": Target,
        "GOOD_HUE": GOOD_HUE,
        "WARN_HUE": WARN_HUE,
        "BAD_HUE": BAD_HUE,
        "LABEL_HUE": LABEL_HUE,
        "DIM_HUE": DIM_HUE,
        "TITLE_HUE": TITLE_HUE,
    }


def validate_plugin(plugin, path):
    required_values = ["plugin_id", "name", "version", "home_label"]
    required_methods = ["activate", "deactivate", "step", "render", "handle_button", "snapshot", "shutdown"]

    for name in required_values:
        if not hasattr(plugin, name):
            raise Exception("missing plugin value: " + name)
    for name in required_methods:
        if not callable(getattr(plugin, name, None)):
            raise Exception("missing plugin method: " + name)
    if not clean_key(plugin.plugin_id):
        raise Exception("plugin_id is invalid")

    plugin.source_path = str(path)
    return plugin


def load_plugin_file(path):
    source = File.ReadAllText(str(path))
    namespace = plugin_namespace(path)
    code = compile(str(source), str(path), "exec")
    exec(code, namespace)

    factory = namespace.get("create_plugin")
    if not callable(factory):
        raise Exception("create_plugin(host) is missing")
    return validate_plugin(factory(_plugin_host), path)


def plugin_by_id(plugin_id):
    wanted = clean_key(plugin_id)
    for plugin in _plugins:
        if clean_key(plugin.plugin_id) == wanted:
            return plugin
    return None


def active_plugin():
    return plugin_by_id(_active_plugin_id)


def shutdown_plugins():
    for plugin in _plugins:
        try:
            plugin.shutdown()
        except:
            pass


def load_plugins():
    global _plugin_directory_path, _plugins, _plugin_errors, _active_plugin_id

    previous_id = _active_plugin_id
    shutdown_plugins()
    _plugins = []
    _plugin_errors = []
    _plugin_directory_path = combine_path(_project_directory, PLUGIN_DIRECTORY)

    if not _project_directory or not Directory.Exists(_plugin_directory_path):
        _active_plugin_id = ""
        return False

    try:
        paths = [str(path) for path in Directory.GetFiles(_plugin_directory_path, "*.py")]
        paths.sort(key=lambda value: str(Path.GetFileName(value)).lower())
    except Exception as ex:
        _plugin_errors.append("Could not enumerate Plugins: " + str(ex))
        return False

    for path in paths:
        if str(Path.GetFileName(path)).startswith("_"):
            continue
        try:
            plugin = load_plugin_file(path)
            if plugin_by_id(plugin.plugin_id):
                raise Exception("duplicate plugin_id: " + str(plugin.plugin_id))
            plugin.button_base = PLUGIN_BUTTON_BASE + len(_plugins) * PLUGIN_BUTTON_STRIDE
            _plugins.append(plugin)
        except Exception as ex:
            _plugin_errors.append(Path.GetFileName(path) + ": " + str(ex))

    if previous_id and plugin_by_id(previous_id):
        _active_plugin_id = clean_key(previous_id)
    elif _plugins:
        _active_plugin_id = clean_key(_plugins[0].plugin_id)
    else:
        _active_plugin_id = ""

    for error in _plugin_errors:
        Misc.SendMessage("Frog Crafting plugin load warning: " + str(error), BAD_HUE)
    save_player_settings_json()
    return bool(_plugins)


def open_plugin_view(plugin_id):
    global _active_plugin_id, _current_view, _dirty_ui

    plugin = plugin_by_id(plugin_id)
    if not plugin:
        set_status("Crafting plugin is unavailable.", BAD_HUE, "Open Plugin")
        return
    if training_work_pending():
        set_status("Process or cancel the pending training output before opening a plugin.", BAD_HUE, "Open Plugin")
        return
    if _runtime_active or _training_active:
        stop_runtime("Crafting paused before opening plugin.", WARN_HUE)

    current = active_plugin()
    if current and current is not plugin:
        try:
            current.deactivate("Crafting plugin changed.")
        except:
            pass

    _active_plugin_id = clean_key(plugin.plugin_id)
    _current_view = VIEW_PLUGIN
    plugin.activate()
    _dirty_ui = True


def plugin_snapshot():
    plugin = active_plugin()
    if not plugin:
        return ()
    try:
        return (clean_key(plugin.plugin_id), bool(getattr(plugin, "running", False)), plugin.snapshot())
    except Exception as ex:
        return (clean_key(plugin.plugin_id), "snapshot error", str(ex))


# ===========================================================
# MODULE / SELECTION HELPERS
# ===========================================================

def active_module():
    if not _modules:
        return None
    if _active_module_index < 0 or _active_module_index >= len(_modules):
        return None
    return _modules[_active_module_index]


def module_categories():
    module = active_module()
    if not module:
        return []
    return list_value(module.get("categories"))


def selected_category():
    categories = module_categories()
    for category in categories:
        if str(category.get("id", "")) == _selected_category_id:
            return category
    return categories[0] if categories else None


def category_recipes():
    category = selected_category()
    if not category:
        return []
    return list_value(category.get("recipes"))


def selected_recipe():
    for recipe in category_recipes():
        if str(recipe.get("id", "")) == _selected_recipe_id:
            return recipe
    return None


def module_choice_groups():
    module = active_module()
    if not module:
        return []
    return list_value(module.get("resource_choice_groups"))


def choice_shared_key(module_id, group_id):
    return KEY_PREFIX + "choice_" + clean_key(module_id) + "_" + clean_key(group_id)


def initialize_choices():
    global _choice_group_index, _choice_indices

    _choice_group_index = 0
    _choice_indices = {}
    module = active_module()
    if not module:
        return

    for group in module_choice_groups():
        group_id = clean_key(group.get("id"))
        options = list_value(group.get("options"))
        if not group_id or not options:
            continue

        selected_index = 0
        default_id = str(group.get("default", ""))
        saved_id = load_shared_text(choice_shared_key(module.get("id"), group_id), default_id)

        for index, option in enumerate(options):
            if str(option.get("id", "")) == saved_id:
                selected_index = index
                break
        _choice_indices[group_id] = selected_index


def current_choice_group():
    groups = module_choice_groups()
    if not groups:
        return None
    index = max(0, min(len(groups) - 1, _choice_group_index))
    return groups[index]


def selected_choice_for_group(group_id):
    for group in module_choice_groups():
        if clean_key(group.get("id")) != clean_key(group_id):
            continue
        options = list_value(group.get("options"))
        if not options:
            return None
        index = _choice_indices.get(clean_key(group_id), 0)
        index = max(0, min(len(options) - 1, int_value(index)))
        return options[index]
    return None


def reset_module_view():
    global _selected_category_id, _selected_recipe_id
    global _category_page, _recipe_page

    categories = module_categories()
    _selected_category_id = str(categories[0].get("id", "")) if categories else ""
    for category in categories:
        if list_value(category.get("recipes")):
            _selected_category_id = str(category.get("id", ""))
            break
    _selected_recipe_id = ""
    _category_page = 0
    _recipe_page = 0
    initialize_choices()


def switch_module(delta):
    global _active_module_index, _current_view, _dirty_ui

    if not _modules:
        return
    stop_runtime("Module changed.", WARN_HUE)
    _active_module_index = (_active_module_index + int(delta)) % len(_modules)
    reset_module_view()
    save_settings()
    set_status("Module ready: " + str(active_module().get("name", "Unknown")), GOOD_HUE, "Ready")
    _current_view = VIEW_CRAFT
    _dirty_ui = True


def open_module_view(module_id):
    global _active_module_index, _current_view, _dirty_ui
    global _training_crafts, _training_start_skill, _training_session_module_id

    requested_id = str(module_id)
    requested_index = -1
    for index, module in enumerate(_modules):
        if str(module.get("id", "")) == requested_id:
            requested_index = index
            break

    if requested_index < 0:
        set_status("That crafting module is no longer available. Reload the data.", BAD_HUE, "Module Selection")
        _dirty_ui = True
        return

    if _training_active:
        stop_runtime("Training stopped; opening the workbench.", WARN_HUE)
    if training_work_pending():
        clear_training_pending_outputs()
    _training_crafts = 0
    _training_start_skill = 0.0
    _training_session_module_id = ""

    if requested_index != _active_module_index:
        stop_runtime("Module changed.", WARN_HUE)
        _active_module_index = requested_index
        reset_module_view()
        save_settings()
        set_status("Module ready: " + str(active_module().get("name", "Unknown")), GOOD_HUE, "Ready")
    elif not _runtime_active:
        initialize_choices()
        set_status("Module ready: " + str(active_module().get("name", "Unknown")), GOOD_HUE, "Ready")

    _current_view = VIEW_CRAFT
    _dirty_ui = True


def open_training_view(module_id):
    global _active_module_index, _current_view, _dirty_ui
    global _training_crafts, _training_start_skill, _training_session_module_id

    requested_id = str(module_id)
    requested_index = -1
    for index, module in enumerate(_modules):
        if str(module.get("id", "")) == requested_id:
            requested_index = index
            break

    profile = _training_profiles.get(requested_id)
    if requested_index < 0 or not profile:
        set_status("No training module is loaded for that craft skill.", BAD_HUE, "Training Selection")
        _dirty_ui = True
        return

    changing_module = requested_index != _active_module_index
    if _runtime_active or (changing_module and _training_active):
        stop_runtime("Opening training mode.", WARN_HUE)
    if changing_module and training_work_pending():
        clear_training_pending_outputs()

    if changing_module:
        _active_module_index = requested_index
        reset_module_view()
        save_settings()
        _training_crafts = 0
        _training_start_skill = 0.0
        _training_session_module_id = ""

    apply_training_choices(profile)
    _current_view = VIEW_TRAINING
    if not _training_active:
        module, _profile, skill_value, _skill_cap, goal, stage, _category, recipe, reason = training_context()
        if bool(dict_value(_profile).get("informational", False)):
            set_status(reason, GOOD_HUE, "Training Guide")
        elif skill_value >= goal:
            set_status("Training goal already reached.", GOOD_HUE, "Training Complete")
        elif stage and clean_key(stage.get("mode", "craft")) == "npc_train":
            set_status(reason, WARN_HUE, "NPC Training Required")
        elif not recipe:
            set_status(reason, BAD_HUE, "Training Mapping")
        else:
            disposal_ready, disposal_error = training_disposal_readiness(stage)
            if not disposal_ready:
                set_status(disposal_error + ".", WARN_HUE, "Training Setup")
            else:
                set_status("Training ready for " + str(module.get("name", "crafting")) + ".", GOOD_HUE, "Training Ready")
    _dirty_ui = True


def select_category(category_id):
    global _selected_category_id, _selected_recipe_id, _recipe_page, _dirty_ui

    _selected_category_id = str(category_id)
    _selected_recipe_id = ""
    _recipe_page = 0
    _dirty_ui = True


def select_recipe(recipe_id):
    global _selected_recipe_id, _dirty_ui

    _selected_recipe_id = str(recipe_id)
    recipe = selected_recipe()
    if recipe:
        ready, reason = recipe_readiness(recipe)
        if ready:
            set_status("Selected " + str(recipe.get("name", "recipe")) + ".", GOOD_HUE, "Ready")
        else:
            set_status("Template data needed: " + reason, WARN_HUE, "Recipe Setup")
    _dirty_ui = True


def selected_choice_label():
    group = current_choice_group()
    if not group:
        return "No material groups"
    option = selected_choice_for_group(group.get("id"))
    option_name = str(option.get("name", "None")) if option else "None"
    return "{0}: {1}".format(group.get("name", "Resource"), option_name)


# ===========================================================
# TRAINING MODULE HELPERS
# ===========================================================

def module_by_id(module_id):
    wanted = str(module_id)
    for module in _modules:
        if str(module.get("id", "")) == wanted:
            return module
    return None


def training_profile(module=None):
    target_module = module or active_module()
    if not target_module:
        return None
    return _training_profiles.get(str(target_module.get("id", "")))


def skill_lookup_names(skill_name):
    name = str(skill_name)
    if name.lower() in ("fletching", "bowcraft", "bowcraft/fletching", "bowcraft and fletching", "bowcraft & fletching"):
        return ("Bowcraft", "Bowcraft/Fletching", "Bowcraft and Fletching", "Bowcraft & Fletching")
    return (name,)


def player_skill_value(skill_name):
    names = skill_lookup_names(skill_name)
    for name in names:
        try:
            value = float(Player.GetRealSkillValue(name))
            if value > 0 or len(names) == 1:
                return value
        except:
            pass
        try:
            value = float(Player.GetSkillValue(name))
            if value > 0 or len(names) == 1:
                return value
        except:
            pass
    return 0.0


def player_modified_skill_value(skill_name):
    names = skill_lookup_names(skill_name)
    for name in names:
        try:
            value = float(Player.GetSkillValue(name))
            if value > 0 or len(names) == 1:
                return value
        except:
            pass
    return player_skill_value(skill_name)


def player_crafting_skill_value(skill_name, include_configured_glasses=False):
    current = player_modified_skill_value(skill_name)
    if not include_configured_glasses:
        return current
    profile = crafting_glasses_profile(skill_name)
    if not profile:
        return current
    bonus = configured_crafting_glasses_bonus(profile, 750)
    if bonus <= 0:
        return current
    return max(current, player_skill_value(skill_name) + bonus)


def player_skill_cap(skill_name):
    for name in skill_lookup_names(skill_name):
        try:
            cap = float(Player.GetSkillCap(name))
            if cap > 0:
                return cap
        except:
            pass
    return 0.0


def training_goal(profile, skill_cap):
    configured = number_value(dict_value(profile).get("target_skill"), 100.0)
    if skill_cap > 0:
        return min(float(configured), float(skill_cap))
    return float(configured)


def training_stage_for_skill(profile, skill_value):
    for raw_stage in list_value(dict_value(profile).get("stages")):
        stage = dict_value(raw_stage)
        minimum = number_value(stage.get("min_skill"), -1.0)
        maximum = number_value(stage.get("max_skill"), -1.0)
        if minimum <= float(skill_value) < maximum:
            return stage
    return None


def find_module_recipe(module, recipe_id):
    wanted = str(recipe_id)
    for category in list_value(dict_value(module).get("categories")):
        for recipe in list_value(dict_value(category).get("recipes")):
            if str(recipe.get("id", "")) == wanted:
                return category, recipe
    return None, None


# ===========================================================
# PLUGIN CRAFT-JOB BRIDGE
# ===========================================================

def restore_plugin_craft_context():
    global _plugin_craft_owner, _plugin_craft_context
    global _active_module_index, _selected_category_id, _selected_recipe_id
    global _choice_group_index, _choice_indices, _target_amount, _completed_amount
    global _output_chest_serial, _craft_bag_enabled, _dirty_ui

    context = dict_value(_plugin_craft_context)
    if context:
        _active_module_index = int_value(context.get("active_module_index"), _active_module_index)
        _selected_category_id = str(context.get("selected_category_id", ""))
        _selected_recipe_id = str(context.get("selected_recipe_id", ""))
        _choice_group_index = int_value(context.get("choice_group_index"), 0)
        _choice_indices = dict(dict_value(context.get("choice_indices")))
        _target_amount = max(1, int_value(context.get("target_amount"), DEFAULT_CRAFT_AMOUNT))
        _completed_amount = max(0, int_value(context.get("completed_amount"), 0))
        _output_chest_serial = int_value(context.get("output_chest_serial"), 0)
        _craft_bag_enabled = bool(context.get("craft_bag_enabled", _craft_bag_enabled))

    _plugin_craft_owner = ""
    _plugin_craft_context = {}
    _dirty_ui = True


def apply_plugin_resource_choices(configured_choices):
    global _choice_indices

    configured = dict_value(configured_choices)
    if not configured:
        return True, ""

    groups = {}
    for group in module_choice_groups():
        group_id = clean_key(group.get("id"))
        if group_id:
            groups[group_id] = group

    for raw_group_id, raw_option_id in configured.items():
        group_id = clean_key(raw_group_id)
        option_id = clean_key(raw_option_id)
        group = groups.get(group_id)
        if not group:
            return False, "The requested resource group is unavailable: " + str(raw_group_id)

        matched_index = -1
        for index, option in enumerate(list_value(group.get("options"))):
            if clean_key(option.get("id")) == option_id:
                matched_index = index
                break
        if matched_index < 0:
            return False, "The requested {0} material is unavailable: {1}".format(group.get("name", group_id), raw_option_id)
        _choice_indices[group_id] = matched_index
    return True, ""


def begin_plugin_craft_job(owner, module_id, category_id, recipe_id, amount, resource_choices=None, focus_override=None, workspace_override=None, ignore_skill_requirements=False):
    global _plugin_craft_owner, _plugin_craft_context
    global _active_module_index, _selected_category_id, _selected_recipe_id
    global _target_amount, _output_chest_serial, _craft_bag_enabled, _dirty_ui

    owner_key = clean_key(owner)
    requested_amount = int_value(amount)
    if not owner_key:
        return False, "Plugin craft owner is invalid."
    if requested_amount <= 0 or requested_amount > MAX_CRAFT_AMOUNT:
        return False, "Plugin craft amount is outside the supported range."
    if _plugin_craft_owner:
        return False, "Another plugin craft job is already active."
    if _runtime_active or _training_active or _cleanup_active or training_work_pending():
        return False, "FCC is already crafting or processing training output."
    requested_workspace = str(workspace_override or "").lower()
    if requested_workspace not in ("", "backpack"):
        return False, "The requested crafting workspace is invalid."
    if not _craft_bag_enabled and requested_workspace != "backpack":
        return False, "Enable and set a Craft Bag before filling BODs."
    requested_focus = str(focus_override or "").lower()
    if requested_focus and requested_focus not in FOCUS_ORDER:
        return False, "The requested crafting focus is invalid."

    requested_index = -1
    requested_module = None
    for index, module in enumerate(_modules):
        if str(module.get("id", "")) == str(module_id):
            requested_index = index
            requested_module = module
            break
    if requested_index < 0 or not requested_module:
        return False, "The requested FCC crafting module is unavailable."

    category, recipe = find_module_recipe(requested_module, recipe_id)
    if not category or not recipe:
        return False, "The requested FCC recipe is unavailable."
    if category_id and str(category.get("id", "")) != str(category_id):
        return False, "The requested FCC recipe category does not match."

    if requested_workspace == "backpack":
        workspace_ready = bool(Player.Backpack)
        workspace_error = "Player backpack is unavailable"
    else:
        workspace_ready, workspace_error = craft_workspace_readiness()
    if not workspace_ready:
        return False, workspace_error + "."

    _plugin_craft_context = {
        "active_module_index": _active_module_index,
        "selected_category_id": _selected_category_id,
        "selected_recipe_id": _selected_recipe_id,
        "choice_group_index": _choice_group_index,
        "choice_indices": dict(_choice_indices),
        "target_amount": _target_amount,
        "completed_amount": _completed_amount,
        "output_chest_serial": _output_chest_serial,
        "craft_bag_enabled": _craft_bag_enabled,
        "focus_override": requested_focus,
        "workspace_override": requested_workspace,
        "ignore_skill_requirements": bool(ignore_skill_requirements),
        "bod_book_complete": False,
        "bod_book_points": 0,
        "bod_book_progress_finished": -1,
        "bod_book_progress_total": -1,
    }
    _plugin_craft_owner = owner_key
    _active_module_index = requested_index
    initialize_choices()
    choices_ready, choices_error = apply_plugin_resource_choices(resource_choices)
    if not choices_ready:
        restore_plugin_craft_context()
        return False, choices_error
    _selected_category_id = str(category.get("id", ""))
    _selected_recipe_id = str(recipe.get("id", ""))
    _target_amount = requested_amount

    if requested_workspace == "backpack":
        _craft_bag_enabled = False
    _output_chest_serial = 0
    start_runtime()
    if not _runtime_active:
        message = _status_msg
        restore_plugin_craft_context()
        return False, message

    _dirty_ui = True
    return True, "Started {0} x{1}.".format(recipe.get("name", "recipe"), requested_amount)


def plugin_craft_job_status(owner):
    owner_key = clean_key(owner)
    if not owner_key or owner_key != _plugin_craft_owner:
        return {
            "state": "idle",
            "completed": 0,
            "target": 0,
            "bod_book_complete": False,
            "bod_book_points": 0,
            "bod_book_progress_finished": -1,
            "bod_book_progress_total": -1,
            "message": "No plugin craft job is active.",
        }

    if _runtime_active or _cleanup_active:
        state = "running"
    elif _completed_amount >= _target_amount:
        state = "complete"
    else:
        state = "stopped"
    return {
        "state": state,
        "completed": max(0, int_value(_completed_amount)),
        "target": max(0, int_value(_target_amount)),
        "bod_book_complete": bool(dict_value(_plugin_craft_context).get("bod_book_complete", False)),
        "bod_book_points": max(0, int_value(dict_value(_plugin_craft_context).get("bod_book_points"), 0)),
        "bod_book_progress_finished": int_value(dict_value(_plugin_craft_context).get("bod_book_progress_finished"), -1),
        "bod_book_progress_total": int_value(dict_value(_plugin_craft_context).get("bod_book_progress_total"), -1),
        "message": str(_status_msg),
    }


def end_plugin_craft_job(owner, cancel=False):
    owner_key = clean_key(owner)
    if not owner_key or owner_key != _plugin_craft_owner:
        return False
    if cancel:
        module = active_module()
        if _runtime_active or _cleanup_active:
            stop_runtime("Plugin craft job cancelled by player.", WARN_HUE)
        else:
            reset_make_last(True)
        try:
            Target.Cancel()
        except:
            pass
        if module:
            close_gump(int_value(module.get("craft_gump_id")))
    restore_plugin_craft_context()
    return True


def begin_plugin_material_cleanup(owner, workspace_override=None):
    global _craft_bag_enabled, _plugin_cleanup_saved_bag_enabled
    owner_key = clean_key(owner)
    if not owner_key or owner_key != clean_key(_active_plugin_id):
        return False, "The requesting FCC plugin is not active."
    if _plugin_craft_owner or _runtime_active or _training_active or _cleanup_active or training_work_pending():
        return False, "FCC is still crafting or processing another cleanup."
    requested_workspace = str(workspace_override or "").lower()
    if requested_workspace not in ("", "backpack"):
        return False, "The requested cleanup workspace is invalid."
    if requested_workspace == "backpack":
        _plugin_cleanup_saved_bag_enabled = _craft_bag_enabled
        _craft_bag_enabled = False

    begin_material_cleanup(
        "plugin_" + owner_key,
        "BOD output processed; post-combine material cleanup complete.",
        GOOD_HUE,
        "BOD Cleanup",
        "BOD material cleanup complete.",
    )
    return True, "Post-combine material cleanup started."


def plugin_material_cleanup_active(owner):
    owner_key = clean_key(owner)
    if not owner_key or owner_key != clean_key(_active_plugin_id):
        return False
    return bool(_cleanup_active)


def recycle_plugin_craft_bag_item(owner, module_id, recipe_id, item_serial, expected_item_id=0):
    global _active_module_index, _selected_category_id, _selected_recipe_id
    global _choice_group_index, _choice_indices, _target_amount, _completed_amount
    global _output_chest_serial, _dirty_ui

    owner_key = clean_key(owner)
    if not owner_key or owner_key != clean_key(_active_plugin_id):
        return "error", "The requesting FCC plugin is not active."
    if _plugin_craft_owner or _runtime_active or _training_active or _cleanup_active or training_work_pending():
        return "error", "FCC is already crafting or processing training output."

    reset_make_last(True)

    workspace_ready, workspace_error = craft_workspace_readiness()
    if not workspace_ready:
        return "error", workspace_error + "."

    bag = craft_bag_item() if _craft_bag_enabled else None
    item = valid_item(item_serial)
    if not bag or not item:
        return "complete", "Rejected output was already removed."
    try:
        if int(item.Container) != int(bag.Serial):
            return "error", "Safety stop: rejected output is no longer directly inside the Craft Bag."
        if int(item.Amount) > 1:
            return "error", "Safety stop: automatic recycling does not target an unverified stack."
        if int_value(expected_item_id) > 0 and int(item.ItemID) != int_value(expected_item_id):
            return "error", "Safety stop: rejected output no longer has the BOD's requested item graphic."
    except:
        return "error", "Could not validate the rejected Craft Bag output."

    requested_index = -1
    requested_module = None
    for index, module in enumerate(_modules):
        if str(module.get("id", "")) == str(module_id):
            requested_index = index
            requested_module = module
            break
    if requested_index < 0 or not requested_module:
        return "error", "The requested FCC recycling module is unavailable."
    _category, recipe = find_module_recipe(requested_module, recipe_id)
    if not recipe:
        return "error", "The rejected output's FCC recipe is unavailable."

    recycle_button = int_value(dict_value(requested_module.get("server_actions")).get("recycle"))
    if recycle_button <= 0:
        return "error", "Recycle is not mapped for " + str(requested_module.get("name", module_id)) + "."

    context = {
        "active_module_index": _active_module_index,
        "selected_category_id": _selected_category_id,
        "selected_recipe_id": _selected_recipe_id,
        "choice_group_index": _choice_group_index,
        "choice_indices": dict(_choice_indices),
        "target_amount": _target_amount,
        "completed_amount": _completed_amount,
        "output_chest_serial": _output_chest_serial,
    }
    craft_gump_id = int_value(requested_module.get("craft_gump_id"))
    try:
        _active_module_index = requested_index
        initialize_choices()

        tool_state, tool_result = ensure_tool(requested_module)
        if _operation_interrupted or consume_priority_control_button():
            return "cancelled", "Rejected-output recycling was interrupted."
        if tool_state == "progress":
            return "progress", "Acquiring a tool before recycling rejected output."
        if tool_state == "error":
            return "error", str(tool_result)

        Target.Cancel()
        if not open_server_craft_gump(craft_gump_id, tool_result):
            return "retry", "The crafting gump did not open for rejected-output recycling."
        if not send_server_actions(craft_gump_id, [recycle_button], "BOD Reject Recycle"):
            return "retry", "The recycle action did not open."

        target_ready = Target.WaitForTarget(TARGET_CURSOR_WAIT_MS, False)
        if consume_priority_control_button():
            Target.Cancel()
            return "cancelled", "Rejected-output recycling was interrupted."
        if not target_ready and not bool(Target.HasTarget()):
            return "retry", "No recycle target cursor appeared."

        try:
            before_amount = int(item.Amount)
        except:
            before_amount = 1
        Target.TargetExecute(int(item.Serial))
        Misc.Pause(CRAFT_RESULT_PAUSE_MS)

        remaining = valid_item(item_serial)
        if remaining:
            try:
                if int(remaining.Container) == int(bag.Serial) and int(remaining.Amount) >= before_amount:
                    return "retry", "Recycle did not consume the rejected output."
            except:
                pass
        return "complete", "Recycled one rejected " + str(recipe.get("name", "output")) + "."
    except Exception as ex:
        return "error", "Could not recycle rejected output: " + str(ex)
    finally:
        try:
            Target.Cancel()
        except:
            pass
        close_gump(craft_gump_id)
        _active_module_index = int_value(context.get("active_module_index"), _active_module_index)
        _selected_category_id = str(context.get("selected_category_id", ""))
        _selected_recipe_id = str(context.get("selected_recipe_id", ""))
        _choice_group_index = int_value(context.get("choice_group_index"), 0)
        _choice_indices = dict(dict_value(context.get("choice_indices")))
        _target_amount = max(1, int_value(context.get("target_amount"), DEFAULT_CRAFT_AMOUNT))
        _completed_amount = max(0, int_value(context.get("completed_amount"), 0))
        _output_chest_serial = int_value(context.get("output_chest_serial"), 0)
        _dirty_ui = True


def recycle_plugin_craft_bag_contents(owner, module_id, recipe_id, item_serials, expected_item_id=0):
    global _active_module_index, _selected_category_id, _selected_recipe_id
    global _choice_group_index, _choice_indices, _target_amount, _completed_amount
    global _output_chest_serial, _dirty_ui

    serials = []
    for value in list_value(item_serials):
        serial = int_value(value)
        if serial > 0 and serial not in serials:
            serials.append(serial)
    if not serials:
        return "complete", "No rejected output remains to recycle.", []

    owner_key = clean_key(owner)
    if not owner_key or owner_key != clean_key(_active_plugin_id):
        return "error", "The requesting FCC plugin is not active.", serials
    if _plugin_craft_owner or _runtime_active or _training_active or _cleanup_active or training_work_pending():
        return "error", "FCC is already crafting or processing cleanup.", serials

    reset_make_last(True)
    workspace_ready, workspace_error = craft_workspace_readiness()
    if not workspace_ready:
        return "error", workspace_error + ".", serials

    bag = craft_bag_item() if _craft_bag_enabled else None
    if not bag:
        return "error", "The configured Craft Bag is unavailable.", serials
    pending = []
    for serial in serials:
        item = valid_item(serial)
        if not item:
            continue
        try:
            if int(item.Container) != int(bag.Serial) or int(item.Amount) != 1:
                return "error", "Safety stop: a rejected output is not one item directly inside the Craft Bag.", serials
            if int_value(expected_item_id) > 0 and int(item.ItemID) != int_value(expected_item_id):
                return "error", "Safety stop: a rejected output has the wrong item graphic.", serials
        except:
            return "error", "Could not validate the rejected Craft Bag output.", serials
        pending.append(serial)
    if not pending:
        return "complete", "Rejected output was already removed.", []

    other_items = {}
    for item in direct_container_items(bag.Serial):
        try:
            serial = int(item.Serial)
            if serial not in pending:
                other_items[serial] = max(1, int(item.Amount))
        except:
            return "error", "Could not validate other Craft Bag contents before recycling.", pending

    requested_index = -1
    requested_module = None
    for index, module in enumerate(_modules):
        if str(module.get("id", "")) == str(module_id):
            requested_index = index
            requested_module = module
            break
    if requested_index < 0 or not requested_module:
        return "error", "The requested FCC recycling module is unavailable.", pending
    _category, recipe = find_module_recipe(requested_module, recipe_id)
    if not recipe:
        return "error", "The rejected output's FCC recipe is unavailable.", pending
    recycle_button = int_value(dict_value(requested_module.get("server_actions")).get("recycle"))
    if recycle_button <= 0:
        return "error", "Recycle is not mapped for " + str(requested_module.get("name", module_id)) + ".", pending

    context = {
        "active_module_index": _active_module_index,
        "selected_category_id": _selected_category_id,
        "selected_recipe_id": _selected_recipe_id,
        "choice_group_index": _choice_group_index,
        "choice_indices": dict(_choice_indices),
        "target_amount": _target_amount,
        "completed_amount": _completed_amount,
        "output_chest_serial": _output_chest_serial,
    }
    craft_gump_id = int_value(requested_module.get("craft_gump_id"))
    try:
        _active_module_index = requested_index
        initialize_choices()
        tool_state, tool_result = ensure_tool(requested_module)
        if _operation_interrupted or consume_priority_control_button():
            return "cancelled", "Rejected-output recycling was interrupted.", pending
        if tool_state == "progress":
            return "progress", "Acquiring a tool before recycling rejected output.", pending
        if tool_state == "error":
            return "error", str(tool_result), pending

        Target.Cancel()
        if not open_server_craft_gump(craft_gump_id, tool_result):
            return "retry", "The crafting gump did not open for rejected-output recycling.", pending
        Gumps.SendAction(craft_gump_id, recycle_button)
        Misc.Pause(180)
        target_ready = bool(Target.HasTarget())
        if not target_ready:
            target_ready = bool(Target.WaitForTarget(TARGET_CURSOR_WAIT_MS, False)) or bool(Target.HasTarget())
        if _operation_interrupted or consume_priority_control_button():
            Target.Cancel()
            return "cancelled", "Rejected-output recycling was interrupted.", pending
        if not target_ready:
            return "retry", "No recycle target cursor appeared.", pending

        Target.TargetExecute(int(bag.Serial))
        Misc.Pause(CRAFT_RESULT_PAUSE_MS)
        try:
            Items.WaitForContents(bag, 1500)
        except:
            pass
        for serial, amount in other_items.items():
            item = valid_item(serial)
            if not item:
                return "error", "Safety stop: bag-wide recycle also consumed an unrelated item.", pending
            try:
                if int(item.Container) != int(bag.Serial) or int(item.Amount) < amount:
                    return "error", "Safety stop: bag-wide recycle changed an unrelated item.", pending
            except:
                return "error", "Could not verify other Craft Bag contents after recycling.", pending

        remaining = []
        for serial in pending:
            item = valid_item(serial)
            if not item:
                continue
            try:
                if int(item.Container) == int(bag.Serial):
                    remaining.append(serial)
            except:
                return "error", "Could not verify rejected output after recycling.", pending
        if remaining:
            return "leftovers", "Bag-wide recycle left {0} rejected item(s).".format(len(remaining)), remaining
        return "complete", "Bag-wide recycle consumed all rejected output.", []
    except Exception as ex:
        return "retry", "Could not complete bag-wide recycle: " + str(ex), pending
    finally:
        try:
            Target.Cancel()
        except:
            pass
        close_gump(craft_gump_id)
        _active_module_index = int_value(context.get("active_module_index"), _active_module_index)
        _selected_category_id = str(context.get("selected_category_id", ""))
        _selected_recipe_id = str(context.get("selected_recipe_id", ""))
        _choice_group_index = int_value(context.get("choice_group_index"), 0)
        _choice_indices = dict(dict_value(context.get("choice_indices")))
        _target_amount = max(1, int_value(context.get("target_amount"), DEFAULT_CRAFT_AMOUNT))
        _completed_amount = max(0, int_value(context.get("completed_amount"), 0))
        _output_chest_serial = int_value(context.get("output_chest_serial"), 0)
        _dirty_ui = True


def trash_plugin_craft_bag_item(owner, item_serial, expected_item_id=0):
    owner_key = clean_key(owner)
    if not owner_key or owner_key != clean_key(_active_plugin_id):
        return "error", "The requesting FCC plugin is not active."
    if _plugin_craft_owner or _runtime_active or _training_active or _cleanup_active or training_work_pending():
        return "error", "FCC is already crafting or processing cleanup."

    bag = craft_bag_item() if _craft_bag_enabled else None
    trash = valid_item(_trash_container_serial)
    item = valid_item(item_serial)
    if not bag or not item:
        return "complete", "Rejected output was already removed."
    if not trash or not bool(getattr(trash, "IsContainer", False)):
        return "unavailable", "No valid FCC trash container is configured; the rejected output remains in the Craft Bag."
    try:
        if int(item.Container) != int(bag.Serial):
            return "error", "Safety stop: rejected output is no longer directly inside the Craft Bag."
        if int_value(expected_item_id) > 0 and int(item.ItemID) != int_value(expected_item_id):
            return "error", "Safety stop: rejected output no longer has the BOD's requested item graphic."
        before_amount = max(1, int(item.Amount))
    except:
        return "error", "Could not validate the rejected Craft Bag output before trashing."

    try:
        Items.Move(int(item.Serial), int(trash.Serial), before_amount)
        Misc.Pause(MOVE_PAUSE_MS)
    except Exception as ex:
        return "retry", "Could not move the rejected output to trash: " + str(ex)

    remaining = valid_item(item_serial)
    if remaining:
        try:
            still_in_bag = int(remaining.Container) == int(bag.Serial)
            not_reduced = int(remaining.Amount) >= before_amount
            if still_in_bag and not_reduced:
                return "retry", "Rejected output did not move to the configured trash container."
        except:
            return "retry", "Could not verify rejected-output trash movement."
    return "complete", "Moved one unrecyclable rejected output to the configured trash container."


def apply_training_choices(profile):
    global _choice_indices

    configured = dict_value(dict_value(profile).get("resource_choices"))
    if not configured:
        return

    for group in module_choice_groups():
        group_id = clean_key(group.get("id"))
        wanted_option = clean_key(configured.get(group_id))
        if not wanted_option:
            continue
        for index, option in enumerate(list_value(group.get("options"))):
            if clean_key(option.get("id")) == wanted_option:
                _choice_indices[group_id] = index
                break


def training_recipe_for_stage(stage, skill_value):
    module = active_module()
    recipe_ids = [str(value) for value in list_value(dict_value(stage).get("recipe_ids")) if str(value).strip()]
    unavailable = []

    for recipe_id in recipe_ids:
        category, recipe = find_module_recipe(module, recipe_id)
        if not recipe:
            unavailable.append(recipe_id + " missing")
            continue

        minimum = number_value(recipe.get("min_skill"), None)
        if minimum is not None and float(skill_value) < minimum:
            unavailable.append("{0} needs {1:.1f}".format(recipe.get("name", recipe_id), minimum))
            continue

        ready, reason = recipe_readiness(recipe)
        if not ready:
            unavailable.append("{0}: {1}".format(recipe.get("name", recipe_id), reason))
            continue
        return category, recipe, ""

    label = str(dict_value(stage).get("label", "training stage"))
    detail = "; ".join(unavailable) if unavailable else "no recipe_ids are configured"
    return None, None, "No usable recipe for {0}: {1}.".format(label, detail)


def training_disposal(stage):
    return dict_value(dict_value(stage).get("disposal"))


def training_disposal_label(stage):
    disposal = training_disposal(stage)
    mode = clean_key(disposal.get("mode", DISPOSAL_NONE))
    if mode == DISPOSAL_SAVE:
        return "Save to output chest" if _output_chest_serial else "Save in " + craft_workspace_label()
    if mode == DISPOSAL_TRASH:
        return "Trash output"
    if mode in TARGETED_DISPOSAL_MODES:
        return "{0} output (button {1})".format(mode.title(), int_value(disposal.get("button")))
    return "Leave output in backpack"


def training_disposal_readiness(stage):
    workspace_ready, workspace_error = craft_workspace_readiness()
    if not workspace_ready:
        return False, workspace_error

    disposal = training_disposal(stage)
    mode = clean_key(disposal.get("mode", DISPOSAL_NONE))
    if mode in (DISPOSAL_NONE, DISPOSAL_SAVE):
        return True, ""
    if mode == DISPOSAL_TRASH:
        if not valid_item(_trash_container_serial):
            return False, "Set a valid training trash container on Home / Setup"
        return True, ""
    if mode in TARGETED_DISPOSAL_MODES:
        if int_value(disposal.get("button")) <= 0:
            return False, "Set the {0} disposal button in the training JSON".format(mode)
        return True, ""
    return False, "Unsupported training disposal mode: " + mode


def training_context():
    module = active_module()
    profile = training_profile(module)
    if not module or not profile:
        return module, profile, 0.0, 0.0, 0.0, None, None, None, "Training module is not loaded."

    skill_name = str(module.get("skill_name", module.get("name", "Skill")))
    skill_value = player_skill_value(skill_name)
    skill_cap = player_skill_cap(skill_name)
    goal = training_goal(profile, skill_cap)
    stage = training_stage_for_skill(profile, skill_value)

    if bool(profile.get("informational", False)):
        message = str(profile.get("message", "Training guide only.")).strip()
        return module, profile, skill_value, skill_cap, goal, None, None, None, message

    if skill_value >= goal:
        return module, profile, skill_value, skill_cap, goal, None, None, None, "Training goal reached."
    if not stage:
        return module, profile, skill_value, skill_cap, goal, None, None, None, "No training stage covers the current skill."
    if clean_key(stage.get("mode", "craft")) == "npc_train":
        return module, profile, skill_value, skill_cap, goal, stage, None, None, "NPC train to {0:.1f}.".format(number_value(stage.get("max_skill"), skill_value))

    category, recipe, reason = training_recipe_for_stage(stage, skill_value)
    return module, profile, skill_value, skill_cap, goal, stage, category, recipe, reason


def change_choice_group():
    global _choice_group_index, _dirty_ui

    groups = module_choice_groups()
    if not groups:
        return
    _choice_group_index = (_choice_group_index + 1) % len(groups)
    _dirty_ui = True


def change_choice(delta):
    global _dirty_ui

    module = active_module()
    group = current_choice_group()
    if not module or not group:
        return

    group_id = clean_key(group.get("id"))
    options = list_value(group.get("options"))
    if not options:
        return

    index = _choice_indices.get(group_id, 0)
    index = (int(index) + int(delta)) % len(options)
    _choice_indices[group_id] = index
    selected = options[index]
    Misc.SetSharedValue(choice_shared_key(module.get("id"), group_id), str(selected.get("id", "")))
    set_status("Selected " + selected_choice_label() + ".", GOOD_HUE, "Ready")
    _dirty_ui = True


# ===========================================================
# RECIPE / RESOURCE CONTRACT
# ===========================================================

def shelf_resource(resource_key):
    return _shelf_resources.get(clean_key(resource_key))


def resolve_resource(raw_resource):
    if not isinstance(raw_resource, dict):
        return None, "resource entry is not an object"

    resource_key = clean_key(raw_resource.get("resource_key"))
    choice_group = clean_key(raw_resource.get("choice_group"))
    selected_option = None

    if choice_group:
        selected_option = selected_choice_for_group(choice_group)
        if not selected_option:
            return None, "choice group {0} has no selection".format(choice_group)
        resource_key = clean_key(selected_option.get("resource_key"))

    base = shelf_resource(resource_key) or {}
    resolved = {}

    for key, value in base.items():
        resolved[key] = value
    if selected_option:
        for key, value in selected_option.items():
            if value is not None:
                resolved[key] = value
    for key, value in raw_resource.items():
        if value is not None:
            resolved[key] = value

    resolved["resource_key"] = resource_key
    resolved["choice_group"] = choice_group
    resolved["amount"] = int_value(raw_resource.get("amount"), 0)

    item_names = configured_names(resolved)
    resolved["item_names"] = item_names

    if not resource_key and int_value(resolved.get("item_id")) <= 0 and not item_names:
        return None, "resource_key, item_id, or item_names is missing"
    if resolved["amount"] <= 0:
        return None, "resource amount is missing"
    if int_value(resolved.get("item_id")) <= 0 and not item_names:
        return None, "item ID or name is missing for {0}".format(resolved.get("name", resource_key))

    return resolved, ""


def resolve_resource_list(raw_resources):
    resolved = []
    for raw_resource in list_value(raw_resources):
        resource, error = resolve_resource(raw_resource)
        if not resource:
            return [], error
        resolved.append(resource)
    return resolved, ""


def find_category_for_recipe(recipe):
    if not recipe:
        return None
    for category in module_categories():
        for candidate in list_value(category.get("recipes")):
            if candidate is recipe:
                return category
            if str(candidate.get("id", "")) == str(recipe.get("id", "")):
                return category
    return None


def additional_skill_requirements(recipe):
    requirements = []
    for raw_requirement in list_value(recipe.get("skill_requirements")):
        requirement = dict_value(raw_requirement)
        skill_name = str(requirement.get("skill_name", "")).strip()
        minimum = number_value(requirement.get("min_skill"), None)
        if not skill_name or minimum is None:
            return [], "additional skill requirement is incomplete"
        requirements.append((skill_name, float(minimum)))
    return requirements, ""


def recipe_readiness(recipe):
    module = active_module()
    category = find_category_for_recipe(recipe)

    if not module:
        return False, "module is not loaded"
    if not recipe:
        return False, "select a recipe"
    if not bool(recipe.get("enabled", False)):
        return False, "recipe is disabled"
    if number_value(recipe.get("min_skill"), None) is None:
        return False, "minimum skill is missing"
    _skill_requirements, skill_error = additional_skill_requirements(recipe)
    if skill_error:
        return False, skill_error
    if not category or not list_value(category.get("open_actions")):
        return False, "category action mapping is missing"

    recipe_actions = list_value(recipe.get("craft_actions"))
    if not recipe_actions and int_value(recipe.get("button")) <= 0:
        return False, "recipe button mapping is missing"

    if not list_value(recipe.get("resources")):
        return False, "resource costs are missing"

    resources, error = resolve_resource_list(recipe.get("resources"))
    if not resources:
        return False, error or "resource costs are invalid"

    for resource in resources:
        group_id = clean_key(resource.get("choice_group"))
        if group_id:
            option = selected_choice_for_group(group_id)
            if not option or not list_value(option.get("craft_actions")):
                return False, "craft selection mapping is missing for {0}".format(resource.get("name", group_id))

    output_ids = output_ids_for_recipe(recipe)
    output_names = output_names_for_recipe(recipe)
    if not output_ids and not output_names:
        return False, "output item ID or name is missing"

    tool = dict_value(module.get("tool"))
    if not tool_ids(tool) and not configured_names(tool):
        return False, "tool item ID or name is missing"

    return True, "Ready"


def recipe_resource_summary(recipe):
    if not recipe:
        return "Select a recipe"
    resources, error = resolve_resource_list(recipe.get("resources"))
    if not resources:
        return "Needs data: " + (error or "resource costs")

    parts = []
    for resource in resources:
        parts.append("{0} x{1}".format(resource.get("name", resource.get("resource_key", "Resource")), resource.get("amount", 0)))
    return ", ".join(parts)


def recipe_skill_summary(recipe):
    module = active_module()
    if not recipe or not module:
        return "Skill: --"
    minimum = number_value(recipe.get("min_skill"), None)
    if minimum is None:
        return "Skill: needs data"
    parts = ["{0}: {1:.1f}+".format(module.get("skill_name", "Skill"), minimum)]
    requirements, error = additional_skill_requirements(recipe)
    if error:
        return "Skill: needs data"
    for skill_name, skill_minimum in requirements:
        parts.append("{0}: {1:.1f}+".format(skill_name, skill_minimum))
    return ", ".join(parts)


# ===========================================================
# ITEM / CONTAINER HELPERS
# ===========================================================

def count_item(container_serial, item_id, hue=-1):
    try:
        return int(Items.ContainerCount(int(container_serial), int(item_id), int(hue), True))
    except:
        return 0


def find_item(item_ids, container_serial, hue=-1):
    for item_id in item_ids:
        if int_value(item_id) <= 0:
            continue
        try:
            item = Items.FindByID(int(item_id), int(hue), int(container_serial), -1, True)
            if item:
                return item
        except:
            pass
    return None


def item_name(item):
    if not item:
        return ""
    try:
        name = str(item.Name or "").strip()
    except:
        name = ""
    if name:
        return name
    try:
        Items.WaitForProps(item, 500)
        return str(item.Name or "").strip()
    except:
        return ""


def container_items(container_serial):
    root = valid_item(container_serial)
    if not root:
        return []

    result = []
    pending = []
    visited = []
    try:
        pending.extend(list(root.Contains or []))
    except:
        return result

    while pending:
        item = pending.pop(0)
        try:
            serial = int(item.Serial)
        except:
            continue
        if serial in visited:
            continue
        visited.append(serial)
        result.append(item)
        try:
            pending.extend(list(item.Contains or []))
        except:
            pass
    return result


def direct_container_items(container_serial):
    container = valid_item(container_serial)
    if not container:
        return []
    try:
        return list(container.Contains or [])
    except:
        return []


def item_matches_descriptor(item, record, hue=-1, id_field="item_ids", name_field="item_names"):
    if not item or not isinstance(record, dict):
        return False
    try:
        if int(hue) >= 0 and int(item.Hue) != int(hue):
            return False
    except:
        return False

    ids = descriptor_item_ids(record, id_field)
    try:
        if int(item.ItemID) in ids:
            return True
    except:
        pass

    names = [normalized_item_name(name) for name in configured_names(record, name_field)]
    return normalized_item_name(item_name(item)) in names


def snapshot_direct_container(container_serial):
    snapshot = {}
    for item in direct_container_items(container_serial):
        try:
            snapshot[int(item.Serial)] = {
                "amount": int(item.Amount),
                "item_id": int(item.ItemID),
                "hue": int(item.Hue),
                "name": item_name(item),
            }
        except:
            pass
    return snapshot


def detect_new_descriptor_items(record, before_snapshot, container_serial, hue=-1, id_field="item_ids", name_field="item_names"):
    deltas = []
    for item in direct_container_items(container_serial):
        try:
            serial = int(item.Serial)
            before_record = dict_value(before_snapshot.get(serial))
            delta = int(item.Amount) - int_value(before_record.get("amount"), 0)
            if delta > 0 and item_matches_descriptor(item, record, hue, id_field, name_field):
                deltas.append((item, delta))
        except:
            pass
    return deltas


def find_item_by_names(names, container_serial, hue=-1):
    for name in names:
        try:
            item = Items.FindByName(str(name), int(hue), int(container_serial), -1, True)
            if item:
                return item
        except:
            pass

    wanted = [normalized_item_name(name) for name in names if normalized_item_name(name)]
    for item in container_items(container_serial):
        try:
            if int(hue) >= 0 and int(item.Hue) != int(hue):
                continue
        except:
            continue
        if normalized_item_name(item_name(item)) in wanted:
            return item
    return None


def descriptor_item_ids(record, field_name="item_ids"):
    if not isinstance(record, dict):
        return []
    values = list_value(record.get(field_name))
    if field_name == "item_ids" and not values:
        values = [record.get("item_id")]
    return [int_value(value) for value in values if int_value(value) > 0]


def configured_shelf_item_ids(record, fallback_ids):
    item_ids = descriptor_item_ids(record)
    if item_ids:
        return item_ids
    return [int_value(value) for value in fallback_ids if int_value(value) > 0]


def item_id_choices_label(item_ids):
    return " or ".join(["0x{0:04X}".format(int_value(value)) for value in item_ids if int_value(value) > 0])


def find_descriptor_item(record, container_serial, hue=-1, id_field="item_ids", name_field="item_names"):
    ids = descriptor_item_ids(record, id_field)
    item = find_item(ids, container_serial, hue)
    if item:
        return item
    return find_item_by_names(configured_names(record, name_field), container_serial, hue)


def count_descriptor_items(record, container_serial, hue=-1, id_field="item_ids", name_field="item_names"):
    ids = descriptor_item_ids(record, id_field)
    if ids:
        total = 0
        for item_id in ids:
            total += count_item(container_serial, item_id, hue)
        return total

    wanted = [normalized_item_name(name) for name in configured_names(record, name_field)]
    total = 0
    for item in container_items(container_serial):
        try:
            if int(hue) >= 0 and int(item.Hue) != int(hue):
                continue
            if normalized_item_name(item_name(item)) in wanted:
                total += int(item.Amount)
        except:
            pass
    return total


def count_resource(container_serial, resource):
    return count_descriptor_items(resource, container_serial, int_value(resource.get("hue"), -1))


def find_resource_item(container_serial, resource):
    return find_descriptor_item(resource, container_serial, int_value(resource.get("hue"), -1))


def open_container(serial):
    item = valid_item(serial)
    if not item:
        return False
    try:
        Items.UseItem(item)
        Items.WaitForContents(item, 1500)
        return True
    except:
        return False


def craft_bag_item():
    bag = valid_item(_craft_bag_serial)
    backpack = Player.Backpack
    if not bag or not backpack:
        return None
    try:
        if int(bag.Serial) == int(backpack.Serial):
            return None
        if not bool(bag.IsContainer):
            return None
        if int(bag.Container) != int(backpack.Serial):
            return None
    except:
        return None
    return bag


def craft_workspace_item():
    if _craft_bag_enabled:
        return craft_bag_item()
    return Player.Backpack


def craft_workspace_readiness():
    if not _craft_bag_enabled:
        if Player.Backpack:
            return True, ""
        return False, "Player backpack is unavailable"
    if not _craft_bag_serial:
        return False, "Set a Craft Bag on Home / Setup"
    bag = valid_item(_craft_bag_serial)
    if not bag:
        return False, "The configured Craft Bag is unavailable"
    try:
        if not bool(bag.IsContainer):
            return False, "The configured Craft Bag is not a container"
        if int(bag.Container) != int(Player.Backpack.Serial):
            return False, "Move the configured Craft Bag directly into the main backpack"
        if int(bag.Serial) in (int(_resource_chest_serial), int(_resource_shelf_serial), int(_reagent_shelf_serial)):
            return False, "Craft Bag cannot also be the configured resource source"
        if int(bag.Serial) == int(_trash_container_serial):
            return False, "Craft Bag cannot also be the training trash container"
    except:
        return False, "Could not validate the configured Craft Bag"
    return True, ""


def prepare_craft_workspace():
    ready, error = craft_workspace_readiness()
    if not ready:
        return False, error
    if _craft_bag_enabled and not open_container(_craft_bag_serial):
        return False, "Could not open the configured Craft Bag"
    return True, ""


def craft_workspace_label():
    return "Craft Bag" if _craft_bag_enabled else "Main Backpack"


def move_descriptor_from_main_pack_to_craft_bag(record, amount, hue=-1, id_field="item_ids", name_field="item_names"):
    if not _craft_bag_enabled or int_value(amount) <= 0:
        return 0

    bag = craft_bag_item()
    backpack = Player.Backpack
    if not bag or not backpack:
        return 0

    before = count_descriptor_items(record, bag.Serial, hue, id_field, name_field)
    remaining = int(amount)
    for item in direct_container_items(backpack.Serial):
        if remaining <= 0:
            break
        if not item_matches_descriptor(item, record, hue, id_field, name_field):
            continue
        try:
            move_amount = min(int(item.Amount), remaining)
            Items.Move(item.Serial, bag.Serial, move_amount)
            Misc.Pause(MOVE_PAUSE_MS)
            remaining -= move_amount
        except:
            pass
    after = count_descriptor_items(record, bag.Serial, hue, id_field, name_field)
    return max(0, after - before)


def move_descriptor_from_main_pack_to_container(record, amount, destination_serial, hue=-1, id_field="item_ids", name_field="item_names"):
    amount = int_value(amount)
    destination = valid_item(destination_serial)
    backpack = Player.Backpack
    if amount <= 0 or not destination or not backpack:
        return 0

    open_container(destination.Serial)
    before = count_descriptor_items(record, destination.Serial, hue, id_field, name_field)
    remaining = amount
    for item in direct_container_items(backpack.Serial):
        if remaining <= 0:
            break
        if not item_matches_descriptor(item, record, hue, id_field, name_field):
            continue
        try:
            move_amount = min(int(item.Amount), remaining)
            Items.Move(item.Serial, destination.Serial, move_amount)
            Misc.Pause(MOVE_PAUSE_MS)
            remaining -= move_amount
        except:
            pass
    after = count_descriptor_items(record, destination.Serial, hue, id_field, name_field)
    return max(0, after - before)


def move_descriptor_deltas_to_craft_bag(deltas):
    bag = craft_bag_item()
    if not bag:
        return False
    for item, delta in deltas:
        try:
            before_amount = int(item.Amount)
            before_container = int(item.Container)
            Items.Move(item.Serial, bag.Serial, int(delta))
            Misc.Pause(MOVE_PAUSE_MS)
            remaining = valid_item(item.Serial)
            if remaining:
                moved_to_bag = int(remaining.Container) == int(bag.Serial)
                reduced_at_source = int(remaining.Container) == before_container and int(remaining.Amount) <= before_amount - int(delta)
                if not moved_to_bag and not reduced_at_source:
                    return False
        except:
            return False
    return True


def set_target_serial(kind):
    global _resource_chest_serial, _resource_shelf_serial, _reagent_shelf_serial
    global _craft_bag_enabled, _craft_bag_serial
    global _output_chest_serial, _tool_book_serial, _trash_container_serial

    prompts = {
        "resource_chest": "Target the resource chest",
        "resource_shelf": "Target the Resource Shelf",
        "reagent_shelf": "Target the Reagent and Gem Storage Shelf",
        "output_chest": "Target the crafted-item chest",
        "tool_book": "Target the Crafting Tool Storage book",
        "trash_container": "Target a trash barrel or disposal container",
        "craft_bag": "Target a sub-bag directly inside your main backpack",
    }

    Target.Cancel()
    serial = Target.PromptTarget(prompts.get(kind, "Target an item"))
    item = valid_item(serial)

    if not item:
        set_status("Target cancelled or item not found.", BAD_HUE, "Target Setup")
        return

    if kind in ("resource_chest", "resource_shelf", "reagent_shelf", "trash_container") and int(serial) == int(_craft_bag_serial):
        set_status("That target is the configured Craft Bag; choose a separate container.", BAD_HUE, "Craft Bag Safety")
        return

    if kind == "resource_shelf":
        expected_ids = configured_shelf_item_ids(_shelf_data, RESOURCE_SHELF_IDS)
        if expected_ids and int_value(item.ItemID) not in expected_ids:
            set_status("That is not a Resource Shelf (expected {0}).".format(item_id_choices_label(expected_ids)), BAD_HUE, "Target Setup")
            return
        _resource_shelf_serial = int(serial)
        set_status("Resource Shelf saved; withdrawal must be set to {0}.".format(RESOURCE_SHELF_WITHDRAW_AMOUNT), GOOD_HUE, "Ready")
    elif kind == "reagent_shelf":
        expected_ids = configured_shelf_item_ids(_reagent_shelf_data, REAGENT_SHELF_IDS)
        if expected_ids and int_value(item.ItemID) not in expected_ids:
            set_status("That is not a Reagent/Gem Shelf (expected {0}).".format(item_id_choices_label(expected_ids)), BAD_HUE, "Target Setup")
            return

        shelf_gump_id = int_value(_reagent_shelf_data.get("gump_id"), 0xA8ED56C7)
        try:
            close_gump(shelf_gump_id)
            Items.UseItem(item)
            Gumps.WaitForGump(shelf_gump_id, SERVER_GUMP_WAIT_MS)
        except:
            close_gump(shelf_gump_id)
            set_status("Could not open that Reagent/Gem Shelf target.", BAD_HUE, "Target Setup")
            return
        if not gump_is_open(shelf_gump_id):
            set_status("That item did not open the Reagent/Gem Shelf gump.", BAD_HUE, "Target Setup")
            return
        close_gump(shelf_gump_id)
        _reagent_shelf_serial = int(serial)
        withdraw_amount = int_value(_reagent_shelf_data.get("withdraw_amount"), 100)
        set_status("Reagent/Gem Shelf saved; set used withdrawal entries to {0}.".format(withdraw_amount), GOOD_HUE, "Ready")
    elif kind == "resource_chest":
        _resource_chest_serial = int(serial)
        set_status("Resource chest saved.", GOOD_HUE, "Ready")
    elif kind == "output_chest":
        _output_chest_serial = int(serial)
        set_status("Crafted-item chest saved.", GOOD_HUE, "Ready")
    elif kind == "tool_book":
        _tool_book_serial = int(serial)
        set_status("Crafting Tool Storage book saved.", GOOD_HUE, "Ready")
    elif kind == "trash_container":
        _trash_container_serial = int(serial)
        set_status("Training trash container saved.", GOOD_HUE, "Ready")
    elif kind == "craft_bag":
        backpack = Player.Backpack
        try:
            is_valid_bag = bool(item.IsContainer) and backpack and int(item.Serial) != int(backpack.Serial) and int(item.Container) == int(backpack.Serial)
        except:
            is_valid_bag = False
        if not is_valid_bag:
            set_status("Craft Bag must be a container directly inside the main backpack.", BAD_HUE, "Target Setup")
            return
        if int(serial) in (int(_resource_chest_serial), int(_resource_shelf_serial), int(_reagent_shelf_serial), int(_trash_container_serial)):
            set_status("Craft Bag must be separate from resource and trash containers.", BAD_HUE, "Craft Bag Safety")
            return
        _craft_bag_serial = int(serial)
        _craft_bag_enabled = True
        open_container(_craft_bag_serial)
        set_status("Craft Bag saved and enabled.", GOOD_HUE, "Ready")

    save_settings()


# ===========================================================
# MATERIAL CLEANUP
# ===========================================================

def cleanup_resource_signature(resource):
    ids = tuple(sorted(descriptor_item_ids(resource)))
    names = tuple(sorted([normalized_item_name(name) for name in configured_names(resource) if normalized_item_name(name)]))
    return ids, names, int_value(resource.get("hue"), -1)


def reset_session_resources():
    global _session_resources

    _session_resources = []


def register_session_resources(resources):
    global _session_resources

    known = [cleanup_resource_signature(resource) for resource in _session_resources]
    for resource in list_value(resources):
        if not isinstance(resource, dict):
            continue
        signature = cleanup_resource_signature(resource)
        if signature in known:
            continue
        _session_resources.append(dict(resource))
        known.append(signature)


def reset_material_cleanup(clear_resources=False):
    global _session_resources, _craft_bag_enabled, _plugin_cleanup_saved_bag_enabled
    global _cleanup_active, _cleanup_stage, _cleanup_resources
    global _cleanup_final_message, _cleanup_final_hue, _cleanup_final_step
    global _cleanup_head_message, _cleanup_returned, _cleanup_notes
    global _cleanup_retry_count, _cleanup_skipped_serials

    _cleanup_active = False
    _cleanup_stage = ""
    _cleanup_resources = []
    _cleanup_final_message = ""
    _cleanup_final_hue = GOOD_HUE
    _cleanup_final_step = "Complete"
    _cleanup_head_message = ""
    _cleanup_returned = 0
    _cleanup_notes = []
    _cleanup_retry_count = 0
    _cleanup_skipped_serials = []
    if _plugin_cleanup_saved_bag_enabled is not None:
        _craft_bag_enabled = bool(_plugin_cleanup_saved_bag_enabled)
        _plugin_cleanup_saved_bag_enabled = None
    if clear_resources:
        _session_resources = []


def cleanup_item_matches(item):
    for resource in _cleanup_resources:
        if item_matches_descriptor(item, resource, int_value(resource.get("hue"), -1)):
            return True
    return False


def cleanup_direct_items(container_serial, include_skipped=False):
    result = []
    for item in direct_container_items(container_serial):
        try:
            if not include_skipped and int(item.Serial) in _cleanup_skipped_serials:
                continue
        except:
            continue
        if cleanup_item_matches(item):
            result.append(item)
    return result


def cleanup_direct_total(container_serial):
    total = 0
    for item in cleanup_direct_items(container_serial, True):
        try:
            total += max(1, int(item.Amount))
        except:
            total += 1
    return total


def cleanup_leftover_total():
    backpack = Player.Backpack
    if not backpack:
        return 0
    total = cleanup_direct_total(backpack.Serial)
    bag = craft_bag_item() if _craft_bag_enabled else None
    if bag:
        total += cleanup_direct_total(bag.Serial)
    return total


def add_cleanup_note(message):
    text = str(message or "").strip().rstrip(".")
    if text and text not in _cleanup_notes:
        _cleanup_notes.append(text)


def set_cleanup_stage(stage):
    global _cleanup_stage, _cleanup_retry_count, _cleanup_skipped_serials, _dirty_ui

    _cleanup_stage = str(stage)
    _cleanup_retry_count = 0
    _cleanup_skipped_serials = []
    _dirty_ui = True


def move_one_cleanup_stack(source_serial, destination_serial):
    source = valid_item(source_serial)
    destination = valid_item(destination_serial)
    if not source or not destination:
        return "unavailable", 0, 0

    items = cleanup_direct_items(source.Serial)
    if not items:
        return "done", 0, 0

    item = items[0]
    try:
        serial = int(item.Serial)
        move_amount = max(1, int(item.Amount))
    except:
        return "failed", 0, 0

    before = cleanup_direct_total(source.Serial)
    try:
        Items.Move(serial, destination.Serial, move_amount)
        Misc.Pause(MOVE_PAUSE_MS)
    except:
        return "failed", 0, serial
    after = cleanup_direct_total(source.Serial)
    moved = max(0, before - after)
    if moved <= 0:
        return "failed", 0, serial
    return "moved", moved, serial


def cleanup_move_stage(source_serial, destination_serial, next_stage, label, count_as_returned):
    global _cleanup_returned, _cleanup_retry_count

    state, moved, serial = move_one_cleanup_stack(source_serial, destination_serial)
    if state == "done":
        set_cleanup_stage(next_stage)
        return
    if state == "unavailable":
        add_cleanup_note(label + " container is unavailable")
        set_cleanup_stage(next_stage)
        return
    if state == "moved":
        _cleanup_retry_count = 0
        if count_as_returned:
            _cleanup_returned += moved
        set_status("{0}: moved {1} material{2}.".format(label, moved, "" if moved == 1 else "s"), GOOD_HUE, "Cleanup Materials")
        return

    _cleanup_retry_count += 1
    if _cleanup_retry_count <= MAX_ACTION_RETRIES:
        set_status(
            "{0} move did not verify; retry {1}/{2}.".format(label, _cleanup_retry_count, MAX_ACTION_RETRIES),
            WARN_HUE,
            "Cleanup Materials",
        )
        return

    if serial > 0 and serial not in _cleanup_skipped_serials:
        _cleanup_skipped_serials.append(serial)
    add_cleanup_note(label + " could not move one material stack")
    _cleanup_retry_count = 0
    set_status(label + " skipped one unmovable stack and continued.", WARN_HUE, "Cleanup Materials")


def deposit_resource_shelf_from_backpack():
    shelf = valid_item(_resource_shelf_serial)
    backpack = Player.Backpack
    if not shelf or not backpack:
        return False, "Resource Shelf is unavailable", 0

    expected_ids = configured_shelf_item_ids(_shelf_data, RESOURCE_SHELF_IDS)
    if expected_ids and int_value(shelf.ItemID) not in expected_ids:
        return False, "Saved Resource Shelf has the wrong item ID", 0

    shelf_gump_id = int_value(_shelf_data.get("gump_id"), 0x06ABCE12)
    fill_button = int_value(_shelf_data.get("fill_from_backpack_button"), 121)
    if fill_button <= 0:
        return False, "Resource Shelf deposit button is not mapped", 0

    before = cleanup_direct_total(backpack.Serial)
    close_gump(shelf_gump_id)
    Misc.Pause(150)
    try:
        Items.UseItem(shelf)
        Gumps.WaitForGump(shelf_gump_id, SERVER_GUMP_WAIT_MS)
    except:
        close_gump(shelf_gump_id)
        return False, "Resource Shelf gump did not open", 0
    if consume_priority_control_button():
        close_gump(shelf_gump_id)
        return False, "Resource Shelf cleanup was interrupted", 0
    if not gump_is_open(shelf_gump_id):
        return False, "Resource Shelf gump did not open", 0

    try:
        Gumps.SendAction(shelf_gump_id, fill_button)
        Misc.Pause(MOVE_PAUSE_MS)
    except:
        close_gump(shelf_gump_id)
        return False, "Resource Shelf deposit action failed", 0
    close_gump(shelf_gump_id)
    after = cleanup_direct_total(backpack.Serial)
    return True, "Resource Shelf deposit checked", max(0, before - after)


def deposit_reagent_shelf_from_backpack():
    shelf = valid_item(_reagent_shelf_serial)
    backpack = Player.Backpack
    if not shelf or not backpack:
        return False, "Reagent/Gem Shelf is unavailable", 0

    expected_ids = configured_shelf_item_ids(_reagent_shelf_data, REAGENT_SHELF_IDS)
    if expected_ids and int_value(shelf.ItemID) not in expected_ids:
        return False, "Saved Reagent/Gem Shelf has the wrong item ID", 0

    shelf_gump_id = int_value(_reagent_shelf_data.get("gump_id"), 0xA8ED56C7)
    restock_button = int_value(_reagent_shelf_data.get("restock_shelf_button"), 1790)
    requires_target = bool(_reagent_shelf_data.get("restock_requires_target", True))
    target_wait_ms = max(TARGET_CURSOR_WAIT_MS, int_value(_reagent_shelf_data.get("restock_target_wait_ms"), 5000))
    target_settle_ms = max(0, int_value(_reagent_shelf_data.get("restock_target_settle_ms"), 250))
    if restock_button <= 0:
        return False, "Reagent/Gem Shelf restock button is not mapped", 0

    before = cleanup_direct_total(backpack.Serial)
    close_gump(shelf_gump_id)
    Misc.Pause(150)
    try:
        Target.Cancel()
        Items.UseItem(shelf)
        Gumps.WaitForGump(shelf_gump_id, SERVER_GUMP_WAIT_MS)
    except:
        close_gump(shelf_gump_id)
        return False, "Reagent/Gem Shelf gump did not open", 0
    if consume_priority_control_button():
        close_gump(shelf_gump_id)
        return False, "Reagent/Gem Shelf cleanup was interrupted", 0
    if not gump_is_open(shelf_gump_id):
        return False, "Reagent/Gem Shelf gump did not open", 0

    try:
        Gumps.SendAction(shelf_gump_id, restock_button)
        if requires_target:
            Misc.Pause(target_settle_ms)
            target_ready = bool(Target.HasTarget())
            if not target_ready:
                target_ready = bool(Target.WaitForTarget(target_wait_ms, False)) or bool(Target.HasTarget())
            if consume_priority_control_button():
                Target.Cancel()
                close_gump(shelf_gump_id)
                return False, "Reagent/Gem Shelf cleanup was interrupted", 0
            if not target_ready:
                close_gump(shelf_gump_id)
                return False, "Reagent/Gem Shelf did not provide its restock target", 0
            Target.TargetExecute(Player.Serial)
        Misc.Pause(MOVE_PAUSE_MS)
    except:
        close_gump(shelf_gump_id)
        return False, "Reagent/Gem Shelf restock action failed", 0
    close_gump(shelf_gump_id)
    after = cleanup_direct_total(backpack.Serial)
    return True, "Reagent/Gem Shelf deposit checked", max(0, before - after)


def finish_material_cleanup():
    global _runtime_active, _training_active, _dirty_ui

    final_message = _cleanup_final_message
    final_hue = _cleanup_final_hue
    final_step = _cleanup_final_step
    head_message = _cleanup_head_message
    returned = _cleanup_returned
    notes = list(_cleanup_notes)
    leftovers = cleanup_leftover_total()
    if leftovers > 0:
        notes.append("{0} matching material{1} remain in the crafting inventory".format(leftovers, "" if leftovers == 1 else "s"))

    if returned > 0:
        cleanup_summary = " Cleanup returned {0} material{1} to storage.".format(returned, "" if returned == 1 else "s")
    elif _cleanup_resources:
        cleanup_summary = " Cleanup checked the configured storage."
    else:
        cleanup_summary = ""
    if notes:
        cleanup_summary += " Cleanup warning: " + "; ".join(notes) + "."
        final_hue = WARN_HUE

    _runtime_active = False
    _training_active = False
    reset_material_cleanup(True)
    set_status(final_message + cleanup_summary, final_hue, final_step)
    if head_message:
        Player.HeadMessage(final_hue, head_message if not notes else head_message + " Cleanup needs attention.")
    _dirty_ui = True


def begin_material_cleanup(kind, final_message, final_hue, final_step, head_message):
    global _cleanup_active, _cleanup_stage, _cleanup_resources
    global _cleanup_final_message, _cleanup_final_hue, _cleanup_final_step
    global _cleanup_head_message, _cleanup_returned, _cleanup_notes
    global _cleanup_retry_count, _cleanup_skipped_serials, _dirty_ui

    _cleanup_active = True
    _cleanup_resources = [dict(resource) for resource in _session_resources]
    _cleanup_final_message = str(final_message)
    _cleanup_final_hue = int(final_hue)
    _cleanup_final_step = str(final_step)
    _cleanup_head_message = str(head_message)
    _cleanup_returned = 0
    _cleanup_notes = []
    _cleanup_retry_count = 0
    _cleanup_skipped_serials = []

    preserve_plugin_handoff = str(kind).startswith("plugin_") and make_last_handoff_active()
    module = active_module()
    if module and not preserve_plugin_handoff:
        close_gump(int_value(module.get("craft_gump_id")))

    if not _cleanup_resources:
        finish_material_cleanup()
        return

    if _source_mode == SOURCE_SHELF:
        _cleanup_stage = "stage_backpack" if _craft_bag_enabled else "resource_shelf"
    else:
        _cleanup_stage = "storage_chest"
    set_status("Crafting finished; returning unused materials to storage.", WARN_HUE, "Cleanup Materials")
    _dirty_ui = True


def material_cleanup_step():
    global _cleanup_returned, _cleanup_retry_count

    if not _cleanup_active:
        return

    if _cleanup_stage == "stage_backpack":
        bag = craft_bag_item()
        backpack = Player.Backpack
        if not bag or not backpack:
            add_cleanup_note("Craft Bag could not be staged for shelf cleanup")
            set_cleanup_stage("resource_shelf")
            return
        cleanup_move_stage(bag.Serial, backpack.Serial, "resource_shelf", "Stage shelf deposit", False)
        return

    if _cleanup_stage == "resource_shelf":
        if not valid_item(_resource_shelf_serial):
            set_cleanup_stage("reagent_shelf")
            return
        ok, message, returned = deposit_resource_shelf_from_backpack()
        if not _cleanup_active or _operation_interrupted:
            return
        if ok:
            _cleanup_returned += returned
            set_status(message + ".", GOOD_HUE, "Cleanup Materials")
            set_cleanup_stage("reagent_shelf")
            return
        _cleanup_retry_count += 1
        if _cleanup_retry_count <= MAX_ACTION_RETRIES:
            set_status("{0}; retry {1}/{2}.".format(message, _cleanup_retry_count, MAX_ACTION_RETRIES), WARN_HUE, "Cleanup Materials")
            return
        add_cleanup_note(message)
        set_cleanup_stage("reagent_shelf")
        return

    if _cleanup_stage == "reagent_shelf":
        if not valid_item(_reagent_shelf_serial):
            set_cleanup_stage("fallback_chest_main")
            return
        ok, message, returned = deposit_reagent_shelf_from_backpack()
        if not _cleanup_active or _operation_interrupted:
            return
        if ok:
            _cleanup_returned += returned
            set_status(message + ".", GOOD_HUE, "Cleanup Materials")
            set_cleanup_stage("fallback_chest_main")
            return
        _cleanup_retry_count += 1
        if _cleanup_retry_count <= MAX_ACTION_RETRIES:
            set_status("{0}; retry {1}/{2}.".format(message, _cleanup_retry_count, MAX_ACTION_RETRIES), WARN_HUE, "Cleanup Materials")
            return
        add_cleanup_note(message)
        set_cleanup_stage("fallback_chest_main")
        return

    if _cleanup_stage == "fallback_chest_main":
        chest = valid_item(_resource_chest_serial)
        backpack = Player.Backpack
        if not chest or not backpack:
            set_cleanup_stage("finish")
            return
        open_container(chest.Serial)
        cleanup_move_stage(backpack.Serial, chest.Serial, "fallback_chest_bag", "Shelf fallback chest", True)
        return

    if _cleanup_stage == "fallback_chest_bag":
        chest = valid_item(_resource_chest_serial)
        bag = craft_bag_item() if _craft_bag_enabled else None
        if not chest or not bag:
            set_cleanup_stage("finish")
            return
        open_container(chest.Serial)
        cleanup_move_stage(bag.Serial, chest.Serial, "finish", "Shelf fallback chest", True)
        return

    if _cleanup_stage == "storage_chest":
        chest = valid_item(_resource_chest_serial)
        workspace = craft_workspace_item()
        if not chest or not workspace:
            add_cleanup_note("Resource chest is unavailable")
            set_cleanup_stage("finish")
            return
        open_container(chest.Serial)
        cleanup_move_stage(workspace.Serial, chest.Serial, "finish", "Resource chest cleanup", True)
        return

    finish_material_cleanup()


# ===========================================================
# RESOURCE RESTOCKING
# ===========================================================

def crafts_in_restock_chunk(crafts_remaining):
    return max(1, min(RESTOCK_CHUNK_CRAFTS, int(crafts_remaining)))


def wait_for_resource_increase(container_serial, resource, previous_count, timeout_ms=SHELF_DELIVERY_WAIT_MS):
    elapsed = 0
    current = count_resource(container_serial, resource)
    while current <= int(previous_count) and elapsed < int(timeout_ms):
        if consume_priority_control_button():
            return current
        Misc.Pause(JOURNAL_POLL_MS)
        elapsed += JOURNAL_POLL_MS
        current = count_resource(container_serial, resource)
    return current


def pull_from_chest(resource, target_count):
    chest = valid_item(_resource_chest_serial)
    if not chest:
        return False, "Set a valid resource chest."

    workspace_ready, workspace_error = craft_workspace_readiness()
    workspace = craft_workspace_item()
    if not workspace_ready or not workspace:
        return False, workspace_error + "."

    open_container(chest.Serial)
    if _craft_bag_enabled:
        open_container(workspace.Serial)
    have = count_resource(workspace.Serial, resource)
    missing = max(1, int(target_count) - have)
    source = find_resource_item(chest.Serial, resource)

    if not source:
        return False, "Out of {0} in resource chest.".format(resource.get("name", "resource"))

    try:
        move_amount = min(int(source.Amount), int(missing))
    except:
        move_amount = int(missing)

    Items.Move(source, workspace.Serial, move_amount)
    Misc.Pause(MOVE_PAUSE_MS)
    after = count_resource(workspace.Serial, resource)

    if after <= have:
        return False, "Could not move {0} from resource chest.".format(resource.get("name", "resource"))
    return True, "Restocked {0} ({1}).".format(resource.get("name", "resource"), after)


def pull_from_shelf(resource):
    shelf = valid_item(_resource_shelf_serial)
    if not shelf:
        return False, "Set a valid Resource Shelf."

    expected_ids = configured_shelf_item_ids(_shelf_data, RESOURCE_SHELF_IDS)
    if expected_ids and int_value(shelf.ItemID) not in expected_ids:
        return False, "Saved shelf is not item {0}.".format(item_id_choices_label(expected_ids))

    shelf_gump_id = int_value(_shelf_data.get("gump_id"), 0x06ABCE12)
    next_button = int_value(_shelf_data.get("next_page_button"), 123)
    shelf_page = int_value(resource.get("shelf_page"))
    shelf_button = int_value(resource.get("shelf_button"))
    if shelf_page <= 0 or shelf_button <= 0:
        return False, "Shelf button mapping is missing for {0}.".format(resource.get("name", "resource"))

    workspace_ready, workspace_error = craft_workspace_readiness()
    workspace = craft_workspace_item()
    if not workspace_ready or not workspace:
        return False, workspace_error + "."

    if _craft_bag_enabled:
        open_container(workspace.Serial)
    before = count_resource(workspace.Serial, resource)
    before_main_pack = snapshot_direct_container(Player.Backpack.Serial)
    before_main_count = count_resource(Player.Backpack.Serial, resource)
    close_gump(shelf_gump_id)
    Misc.Pause(150)
    Items.UseItem(shelf)
    Gumps.WaitForGump(shelf_gump_id, SERVER_GUMP_WAIT_MS)

    if consume_priority_control_button():
        return False, "Resource Shelf navigation interrupted."

    if not gump_is_open(shelf_gump_id):
        return False, "Resource Shelf gump did not open."

    for _page in range(1, shelf_page):
        if consume_priority_control_button():
            return False, "Resource Shelf navigation interrupted."
        Gumps.SendAction(shelf_gump_id, next_button)
        Gumps.WaitForGump(shelf_gump_id, SERVER_GUMP_WAIT_MS)
        Misc.Pause(180)
        if consume_priority_control_button():
            return False, "Resource Shelf navigation interrupted."
        if not gump_is_open(shelf_gump_id):
            close_gump(shelf_gump_id)
            return False, "Resource Shelf page navigation failed."

    if consume_priority_control_button():
        return False, "Resource Shelf withdrawal interrupted."
    Gumps.SendAction(shelf_gump_id, shelf_button)
    Gumps.WaitForGump(shelf_gump_id, SERVER_GUMP_WAIT_MS)
    Misc.Pause(MOVE_PAUSE_MS)
    close_gump(shelf_gump_id)

    delivery_container = Player.Backpack.Serial if _craft_bag_enabled else workspace.Serial
    delivery_before = before_main_count if _craft_bag_enabled else before
    wait_for_resource_increase(delivery_container, resource, delivery_before)
    if _operation_interrupted:
        return False, "Resource Shelf withdrawal interrupted."

    if _craft_bag_enabled:
        withdrawn = detect_new_descriptor_items(resource, before_main_pack, Player.Backpack.Serial, int_value(resource.get("hue"), -1))
        if withdrawn and not move_descriptor_deltas_to_craft_bag(withdrawn):
            delivered = sum([int_value(delta) for _item, delta in withdrawn])
            return True, "Shelf delivered {0} {1}; Craft Bag staging will retry.".format(delivered, resource.get("name", "resource"))

    after = count_resource(workspace.Serial, resource)
    if after <= before:
        return False, "Shelf withdrew no {0}; verify amount is locked to {1}.".format(resource.get("name", "resource"), RESOURCE_SHELF_WITHDRAW_AMOUNT)
    return True, "Shelf staged {0} {1} in {2}.".format(after - before, resource.get("name", "resource"), craft_workspace_label())


def pull_from_reagent_shelf(resource):
    shelf = valid_item(_reagent_shelf_serial)
    if not shelf:
        return False, "Set a valid Reagent/Gem Shelf."

    expected_ids = configured_shelf_item_ids(_reagent_shelf_data, REAGENT_SHELF_IDS)
    if expected_ids and int_value(shelf.ItemID) not in expected_ids:
        return False, "Saved Reagent/Gem Shelf is not item {0}.".format(item_id_choices_label(expected_ids))

    shelf_gump_id = int_value(_reagent_shelf_data.get("gump_id"), 0xA8ED56C7)
    actions = [int_value(value) for value in list_value(resource.get("reagent_shelf_actions")) if int_value(value) > 0]
    if not actions:
        return False, "Reagent/Gem Shelf mapping is missing for {0}.".format(resource.get("name", "resource"))

    workspace_ready, workspace_error = craft_workspace_readiness()
    workspace = craft_workspace_item()
    if not workspace_ready or not workspace:
        return False, workspace_error + "."

    if _craft_bag_enabled:
        open_container(workspace.Serial)
    before = count_resource(workspace.Serial, resource)
    before_main_pack = snapshot_direct_container(Player.Backpack.Serial)
    before_main_count = count_resource(Player.Backpack.Serial, resource)
    close_gump(shelf_gump_id)
    Misc.Pause(150)
    Items.UseItem(shelf)
    Gumps.WaitForGump(shelf_gump_id, SERVER_GUMP_WAIT_MS)

    if consume_priority_control_button():
        return False, "Reagent/Gem Shelf navigation interrupted."
    if not gump_is_open(shelf_gump_id):
        return False, "Reagent/Gem Shelf gump did not open."

    for index, action in enumerate(actions):
        if consume_priority_control_button():
            close_gump(shelf_gump_id)
            return False, "Reagent/Gem Shelf navigation interrupted."

        Gumps.SendAction(shelf_gump_id, action)
        Gumps.WaitForGump(shelf_gump_id, SERVER_GUMP_WAIT_MS)
        Misc.Pause(180 if index < len(actions) - 1 else MOVE_PAUSE_MS)

        if consume_priority_control_button():
            close_gump(shelf_gump_id)
            return False, "Reagent/Gem Shelf navigation interrupted."
        if index < len(actions) - 1 and not gump_is_open(shelf_gump_id):
            close_gump(shelf_gump_id)
            return False, "Reagent/Gem Shelf page navigation failed."

    close_gump(shelf_gump_id)

    delivery_container = Player.Backpack.Serial if _craft_bag_enabled else workspace.Serial
    delivery_before = before_main_count if _craft_bag_enabled else before
    wait_for_resource_increase(delivery_container, resource, delivery_before)
    if _operation_interrupted:
        return False, "Reagent/Gem Shelf withdrawal interrupted."

    if _craft_bag_enabled:
        withdrawn = detect_new_descriptor_items(resource, before_main_pack, Player.Backpack.Serial, int_value(resource.get("hue"), -1))
        if withdrawn and not move_descriptor_deltas_to_craft_bag(withdrawn):
            delivered = sum([int_value(delta) for _item, delta in withdrawn])
            return True, "Reagent/Gem Shelf delivered {0} {1}; Craft Bag staging will retry.".format(delivered, resource.get("name", "resource"))

    after = count_resource(workspace.Serial, resource)
    withdraw_amount = int_value(resource.get("reagent_shelf_withdraw_amount"), 100)
    if after <= before:
        return False, "Reagent/Gem Shelf withdrew no {0}; verify its entry is set to {1}.".format(resource.get("name", "resource"), withdraw_amount)
    return True, "Reagent/Gem Shelf staged {0} {1} in {2}.".format(after - before, resource.get("name", "resource"), craft_workspace_label())


def craft_component_resource(resource):
    global _component_recipe_stack, _component_parent_focus

    recipe_id = clean_key(resource.get("craft_recipe_id"))
    if not recipe_id:
        return "unavailable", ""

    module = active_module()
    if not module:
        return "error", "Component recipe cannot run because the active module is unavailable."
    category, recipe = find_module_recipe(module, recipe_id)
    if not category or not recipe:
        return "error", "Component recipe {0} is not mapped in {1}.".format(recipe_id, module.get("name", "the active module"))

    recipe_key = clean_key(module.get("id")) + ":" + recipe_id
    if recipe_key in _component_recipe_stack:
        return "error", "Component recipe dependency cycle detected at " + str(recipe.get("name", recipe_id)) + "."

    ready, reason = recipe_readiness(recipe)
    if not ready:
        return "error", "Component recipe {0} is not ready: {1}.".format(recipe.get("name", recipe_id), reason)

    template_state, template_message = ensure_crafting_template(module)
    if template_state != "ready":
        return template_state, template_message
    glasses_state, glasses_message = suppress_crafting_glasses_for_training() if _training_active else ensure_crafting_glasses(module)
    if glasses_state != "ready":
        return glasses_state, glasses_message

    skill_checks = [(str(module.get("skill_name", "Blacksmith")), float(recipe.get("min_skill")))]
    additional_checks, skill_error = additional_skill_requirements(recipe)
    if skill_error:
        return "error", "Component recipe {0}: {1}.".format(recipe.get("name", recipe_id), skill_error)
    skill_checks.extend(additional_checks)
    for skill_name, minimum in skill_checks:
        skill_value = player_crafting_skill_value(skill_name, not _training_active)
        if skill_value < minimum:
            return "error", "Component {0} needs {1} {2:.1f}; current {3:.1f}.".format(recipe.get("name", recipe_id), skill_name, minimum, skill_value)

    component_resources, error = resolve_resource_list(recipe.get("resources"))
    if not component_resources:
        return "error", "Component {0} resource setup error: {1}.".format(recipe.get("name", recipe_id), error)

    _component_recipe_stack.append(recipe_key)
    craft_gump_id = int_value(module.get("craft_gump_id"))
    original_focus = ""
    tool = None
    try:
        register_session_resources(component_resources)
        resource_state, resource_error = ensure_resource_list(component_resources, 1)
        if resource_state != "ready":
            return resource_state, resource_error

        tool_state, tool_result = ensure_tool(module)
        if _operation_interrupted or consume_priority_control_button():
            return "error", "Component crafting was interrupted."
        if tool_state == "progress":
            return "progress", "Acquiring a tool before crafting " + str(recipe.get("name", recipe_id)) + "."
        if tool_state == "error":
            return "error", str(tool_result)
        tool = tool_result

        workspace = craft_workspace_item()
        if not workspace:
            return "error", "Component crafting workspace is unavailable."
        before_count = count_resource(workspace.Serial, resource)
        before_snapshots = snapshot_output_locations()

        set_status("Opening {0} to craft component {1}.".format(module.get("name", "crafting"), recipe.get("name", recipe_id)), LABEL_HUE, "Craft Component")
        if not open_server_craft_gump(craft_gump_id, tool):
            return "error", "Crafting gump did not open for component " + str(recipe.get("name", recipe_id)) + "."

        original_focus = read_crafting_focus(craft_gump_id)
        if not original_focus:
            return "error", "Could not read crafting focus before making component " + str(recipe.get("name", recipe_id)) + "."
        if not _plugin_craft_owner and _craft_focus == "unchanged" and not _component_parent_focus:
            _component_parent_focus = original_focus

        focus_ready, focus_message = ensure_crafting_focus(craft_gump_id, "none")
        if not focus_ready:
            return "error", focus_message

        actions = craft_action_sequence(recipe, component_resources)
        set_status("Crafting component {0} with focus None.".format(recipe.get("name", recipe_id)), LABEL_HUE, "Craft Component")
        reset_make_last()
        sequence_complete = send_server_actions(craft_gump_id, actions, "Craft Component")
        if _operation_interrupted:
            return "error", "Component crafting was interrupted."

        Misc.Pause(CRAFT_RESULT_PAUSE_MS)
        output_hue = int_value(recipe.get("output_hue"), -1)
        output_amount = max(1, int_value(recipe.get("output_amount"), 1))
        output_deltas, actual_output = detect_craft_outputs(recipe, before_snapshots, output_hue)
        if not sequence_complete and actual_output < output_amount:
            return "error", "Component crafting button sequence did not complete."
        if actual_output < output_amount:
            return "error", "No verified {0} component output was detected.".format(recipe.get("name", recipe_id))

        staged, _staged_deltas, stage_error = stage_new_outputs_in_craft_bag(recipe, output_deltas, output_hue)
        if not staged:
            return "error", stage_error
        after_count = count_resource(workspace.Serial, resource)
        if after_count <= before_count:
            return "error", "Crafted {0}, but it did not match the parent recipe's {1} resource identity.".format(recipe.get("name", recipe_id), resource.get("name", resource.get("resource_key", "component")))

        clear_action_failures("component_" + recipe_key)
        return "progress", "Crafted {0} for {1}; the parent recipe will resume next.".format(recipe.get("name", recipe_id), resource.get("name", "component"))
    except Exception as ex:
        return "error", "Could not craft component {0}: {1}".format(recipe.get("name", recipe_id), ex)
    finally:
        if original_focus and original_focus != "none" and tool:
            try:
                if not gump_is_open(craft_gump_id):
                    open_server_craft_gump(craft_gump_id, tool)
                if gump_is_open(craft_gump_id):
                    ensure_crafting_focus(craft_gump_id, original_focus)
            except:
                pass
        close_gump(craft_gump_id)
        if _component_recipe_stack and _component_recipe_stack[-1] == recipe_key:
            _component_recipe_stack.pop()
        elif recipe_key in _component_recipe_stack:
            _component_recipe_stack.remove(recipe_key)


def ensure_resource_list(resources, crafts_remaining):
    workspace_ready, workspace_error = craft_workspace_readiness()
    workspace = craft_workspace_item()
    if not workspace_ready or not workspace:
        return "error", workspace_error + "."

    chunk_crafts = crafts_in_restock_chunk(crafts_remaining)

    for resource in resources:
        per_craft = int_value(resource.get("amount"))
        have = count_resource(workspace.Serial, resource)
        required_now = per_craft
        target_count = per_craft * chunk_crafts

        if have >= required_now:
            continue

        if _craft_bag_enabled:
            moved = move_descriptor_from_main_pack_to_craft_bag(resource, target_count - have, int_value(resource.get("hue"), -1))
            if moved > 0:
                after_move = count_resource(workspace.Serial, resource)
                set_status("Staged {0} {1} from the main backpack ({2}/{3}).".format(moved, resource.get("name", "resource"), after_move, target_count), GOOD_HUE, "Stage Craft Bag")
                return "progress", ""

        set_status("Restocking {0} for {1} crafts ({2}/{3}).".format(resource.get("name", "resource"), chunk_crafts, have, target_count), WARN_HUE, "Restock Resources")

        if _source_mode == SOURCE_SHELF:
            failures = []
            ok = False
            message = ""
            has_reagent_shelf_mapping = bool(list_value(resource.get("reagent_shelf_actions")))
            has_resource_shelf_mapping = int_value(resource.get("shelf_button")) > 0 and int_value(resource.get("shelf_page")) > 0

            if has_reagent_shelf_mapping:
                if valid_item(_reagent_shelf_serial):
                    ok, message = pull_from_reagent_shelf(resource)
                    if _operation_interrupted:
                        return "error", message
                    if not ok:
                        failures.append(message)
                else:
                    failures.append("Set a valid Reagent/Gem Shelf")

            if not ok and has_resource_shelf_mapping:
                if valid_item(_resource_shelf_serial):
                    ok, message = pull_from_shelf(resource)
                    if _operation_interrupted:
                        return "error", message
                    if not ok:
                        failures.append(message)
                else:
                    failures.append("Set a valid Resource Shelf")

            if not ok and valid_item(_resource_chest_serial):
                ok, message = pull_from_chest(resource, target_count)
                if not ok:
                    failures.append(message)
            elif not ok and not has_reagent_shelf_mapping and not has_resource_shelf_mapping:
                ok, message = pull_from_chest(resource, target_count)
                if not ok:
                    failures.append(message)

            if not ok:
                message = "; ".join([value.rstrip(".") for value in failures if value]) + "."
        else:
            ok, message = pull_from_chest(resource, target_count)

        if ok:
            set_status(message, GOOD_HUE, "Restock Resources")
            return "progress", ""
        if have >= required_now:
            return "ready", ""
        component_state, component_message = craft_component_resource(resource)
        if component_state != "unavailable":
            if component_state == "progress":
                set_status(component_message, GOOD_HUE, "Craft Component")
            return component_state, component_message
        return "error", message

    return "ready", ""


# ===========================================================
# TOOL ACQUISITION
# ===========================================================

def tool_ids(tool_config):
    return descriptor_item_ids(tool_config)


def find_tool_in_backpack(tool_config):
    workspace = craft_workspace_item()
    if not workspace:
        return None
    return find_descriptor_item(tool_config, workspace.Serial, -1)


def pull_tool_from_resource_chest(tool_config):
    chest = valid_item(_resource_chest_serial)
    if not chest:
        return False

    workspace_ready, _workspace_error = craft_workspace_readiness()
    workspace = craft_workspace_item()
    if not workspace_ready or not workspace:
        return False

    open_container(chest.Serial)
    if _craft_bag_enabled:
        open_container(workspace.Serial)
    source = find_descriptor_item(tool_config, chest.Serial, -1)
    if not source:
        return False

    Items.Move(source, workspace.Serial, 1)
    Misc.Pause(MOVE_PAUSE_MS)
    return find_tool_in_backpack(tool_config) is not None


def close_tool_book_gump():
    close_gump(TOOL_BOOK_GUMP_ID)


def pull_tool_from_book(tool_config):
    book = valid_item(_tool_book_serial)
    category_button = int_value(tool_config.get("toolbook_category_button"))
    if not book or category_button <= 0:
        return False

    workspace_ready, _workspace_error = craft_workspace_readiness()
    if not workspace_ready:
        return False

    before_main_pack = snapshot_direct_container(Player.Backpack.Serial)

    close_tool_book_gump()
    Misc.Pause(200)
    Items.UseItem(book)
    Gumps.WaitForGump(TOOL_BOOK_GUMP_ID, 10000)
    if consume_priority_control_button():
        return False
    if not gump_is_open(TOOL_BOOK_GUMP_ID):
        close_tool_book_gump()
        return False

    if consume_priority_control_button():
        return False
    Gumps.SendAdvancedAction(TOOL_BOOK_GUMP_ID, category_button, [], [TOOL_BOOK_TEXT_ENTRY_ID], [TOOL_BOOK_CATEGORY_FIELD_VALUE])
    Gumps.WaitForGump(TOOL_BOOK_GUMP_ID, 10000)
    if consume_priority_control_button():
        return False
    if not gump_is_open(TOOL_BOOK_GUMP_ID):
        close_tool_book_gump()
        return False

    if consume_priority_control_button():
        return False
    Gumps.SendAdvancedAction(TOOL_BOOK_GUMP_ID, TOOL_BOOK_RETRIEVE_BUTTON, [], [TOOL_BOOK_TEXT_ENTRY_ID], [str(DEFAULT_TOOL_BOOK_CHARGES)])
    Gumps.WaitForGump(TOOL_BOOK_GUMP_ID, 10000)

    Gumps.SendAdvancedAction(TOOL_BOOK_GUMP_ID, 0, [], [TOOL_BOOK_TEXT_ENTRY_ID], [TOOL_BOOK_CATEGORY_FIELD_VALUE])
    Misc.Pause(MOVE_PAUSE_MS)
    close_tool_book_gump()

    if _craft_bag_enabled and not find_tool_in_backpack(tool_config):
        new_tools = detect_new_descriptor_items(tool_config, before_main_pack, Player.Backpack.Serial, -1)
        if new_tools and not move_descriptor_deltas_to_craft_bag(new_tools):
            return False
    return find_tool_in_backpack(tool_config) is not None


def auto_craft_tool(module, tool_config):
    auto_config = dict_value(tool_config.get("auto_craft"))
    if not bool(auto_config.get("enabled", False)):
        return "unavailable", "auto-craft mapping is not enabled"

    skill_name = str(auto_config.get("skill_name", "Tinkering"))
    minimum = number_value(auto_config.get("min_skill"), None)
    if minimum is None:
        return "error", "tool auto-craft minimum skill is missing"

    template_state, template_message = ensure_crafting_template(None, skill_name)
    if template_state != "ready":
        return template_state, template_message
    glasses_state, glasses_message = suppress_crafting_glasses_for_training() if _training_active else ensure_crafting_glasses(None, skill_name)
    if glasses_state != "ready":
        return glasses_state, glasses_message

    skill_value = player_crafting_skill_value(skill_name, not _training_active)

    if skill_value < minimum:
        return "error", "{0} {1:.1f} is below {2:.1f}".format(skill_name, skill_value, minimum)

    workspace_ready, workspace_error = craft_workspace_readiness()
    workspace = craft_workspace_item()
    if not workspace_ready or not workspace:
        return "error", workspace_error

    crafting_tool = find_descriptor_item(auto_config, workspace.Serial, -1, "crafting_tool_item_ids", "crafting_tool_item_names")
    if not crafting_tool and _craft_bag_enabled:
        moved = move_descriptor_from_main_pack_to_craft_bag(auto_config, 1, -1, "crafting_tool_item_ids", "crafting_tool_item_names")
        if moved > 0:
            crafting_tool = find_descriptor_item(auto_config, workspace.Serial, -1, "crafting_tool_item_ids", "crafting_tool_item_names")
    if not crafting_tool and valid_item(_resource_chest_serial):
        source = find_descriptor_item(auto_config, _resource_chest_serial, -1, "crafting_tool_item_ids", "crafting_tool_item_names")
        if source:
            Items.Move(source, workspace.Serial, 1)
            Misc.Pause(MOVE_PAUSE_MS)
            crafting_tool = find_descriptor_item(auto_config, workspace.Serial, -1, "crafting_tool_item_ids", "crafting_tool_item_names")

    if not crafting_tool:
        return "error", "no {0} crafting tool is available".format(skill_name)

    resources, error = resolve_resource_list(auto_config.get("resources"))
    if not resources:
        return "error", error or "tool auto-craft resources are missing"

    resource_state, resource_error = ensure_resource_list(resources, 1)
    if resource_state != "ready":
        return resource_state, resource_error

    output_ids = [int_value(value) for value in list_value(auto_config.get("output_item_ids")) if int_value(value) > 0]
    output_names = configured_names(auto_config, "output_names", False)
    actions = list_value(auto_config.get("craft_actions"))
    gump_id = int_value(auto_config.get("craft_gump_id"), module.get("craft_gump_id"))
    if (not output_ids and not output_names) or not actions or gump_id <= 0:
        return "error", "tool auto-craft action/output mapping is incomplete"

    before_snapshots = snapshot_output_locations()
    if not open_server_craft_gump(gump_id, crafting_tool):
        return "error", "could not open {0} tool gump".format(skill_name)
    reset_make_last()
    if not send_server_actions(gump_id, actions, "Craft Replacement Tool"):
        return "error", "tool auto-craft gump sequence failed"

    Misc.Pause(CRAFT_RESULT_PAUSE_MS)
    output_deltas, actual_output = detect_craft_outputs(auto_config, before_snapshots, -1)
    if actual_output <= 0:
        return "error", "replacement tool was not created"
    staged, _staged_deltas, stage_error = stage_new_outputs_in_craft_bag(auto_config, output_deltas, -1)
    if not staged:
        return "error", stage_error
    return "progress", "Crafted replacement tool."


def ensure_tool(module):
    tool_config = dict_value(module.get("tool"))
    tool_name = str(tool_config.get("name", "crafting tool"))
    tool = find_tool_in_backpack(tool_config)
    if tool:
        return "ready", tool

    workspace_ready, workspace_error = craft_workspace_readiness()
    if not workspace_ready:
        return "error", workspace_error + "."

    if _craft_bag_enabled:
        moved = move_descriptor_from_main_pack_to_craft_bag(tool_config, 1, -1)
        if moved > 0:
            set_status("Moved " + tool_name + " into the Craft Bag.", GOOD_HUE, "Stage Craft Bag")
            return "progress", None

    set_status("Looking for " + tool_name + ".", WARN_HUE, "Acquire Tool")

    if pull_tool_from_resource_chest(tool_config):
        set_status("Pulled " + tool_name + " from resource chest.", GOOD_HUE, "Acquire Tool")
        return "progress", None

    if consume_priority_control_button():
        return "interrupted", None

    if pull_tool_from_book(tool_config):
        set_status("Pulled " + tool_name + " from Tool Storage.", GOOD_HUE, "Acquire Tool")
        return "progress", None

    if _operation_interrupted or consume_priority_control_button():
        return "interrupted", None

    state, message = auto_craft_tool(module, tool_config)
    if state == "progress":
        set_status(message, GOOD_HUE, "Acquire Tool")
        return "progress", None

    return "error", "No {0}; set Tool Storage or complete tool.auto_craft ({1}).".format(tool_name, message)


# ===========================================================
# SERVER CRAFTING / OUTPUT TRACKING
# ===========================================================

def output_ids_for_recipe(recipe):
    return [int_value(value) for value in list_value(recipe.get("output_item_ids")) if int_value(value) > 0]


def output_names_for_recipe(recipe):
    return configured_names(recipe, "output_names")


def snapshot_direct_backpack():
    backpack = Player.Backpack
    return snapshot_direct_container(backpack.Serial) if backpack else {}


def detect_new_outputs_detail(recipe, before_snapshot, hue=-1, container_serial=None):
    output_ids = output_ids_for_recipe(recipe)
    output_names = [normalized_item_name(name) for name in output_names_for_recipe(recipe)]
    matched = []
    positive = []
    container = valid_item(container_serial) if container_serial else Player.Backpack
    if not container:
        return [], 0, False

    for item in direct_container_items(container.Serial):
        try:
            serial = int(item.Serial)
            before_record = dict_value(before_snapshot.get(serial))
            delta = int(item.Amount) - int_value(before_record.get("amount"), 0)
            if delta <= 0:
                continue
            positive.append((item, delta))

            if int(hue) >= 0 and int(item.Hue) != int(hue):
                continue
            id_match = int(item.ItemID) in output_ids
            name_match = normalized_item_name(item_name(item)) in output_names
            if id_match or name_match:
                matched.append((item, delta))
        except:
            pass

    detected = matched if matched else (positive if len(positive) == 1 else [])
    total = sum(delta for _item, delta in detected)
    return detected, total, bool(matched)


def detect_new_outputs(recipe, before_snapshot, hue=-1, container_serial=None):
    detected, total, _exact_match = detect_new_outputs_detail(recipe, before_snapshot, hue, container_serial)
    return detected, total


def snapshot_output_locations():
    snapshots = {"backpack": snapshot_direct_backpack()}
    bag = craft_bag_item() if _craft_bag_enabled else None
    if bag:
        snapshots["craft_bag"] = snapshot_direct_container(bag.Serial)
    return snapshots


def merge_output_deltas(output_deltas):
    merged = {}
    order = []
    for item, delta in output_deltas:
        try:
            serial = int(item.Serial)
            amount = max(1, int(delta))
        except:
            continue
        if serial not in merged:
            merged[serial] = [item, 0]
            order.append(serial)
        merged[serial][1] += amount
    return [(merged[serial][0], merged[serial][1]) for serial in order]


def detect_craft_outputs_detail(recipe, before_snapshots, hue=-1):
    snapshots = dict_value(before_snapshots)
    detected, _total, exact_match = detect_new_outputs_detail(recipe, dict_value(snapshots.get("backpack")), hue, Player.Backpack.Serial)
    confidence = [exact_match] if detected else []

    bag = craft_bag_item() if _craft_bag_enabled else None
    if bag:
        bag_detected, _bag_total, bag_exact_match = detect_new_outputs_detail(recipe, dict_value(snapshots.get("craft_bag")), hue, bag.Serial)
        if bag_detected:
            confidence.append(bag_exact_match)
        detected.extend(bag_detected)

    detected = merge_output_deltas(detected)
    return detected, sum(delta for _item, delta in detected), bool(confidence) and all(confidence)


def detect_craft_outputs(recipe, before_snapshots, hue=-1):
    detected, total, _exact_match = detect_craft_outputs_detail(recipe, before_snapshots, hue)
    return detected, total


def stage_new_outputs_in_craft_bag(recipe, output_deltas, hue=-1):
    if not _craft_bag_enabled:
        return True, output_deltas, ""

    workspace_ready, workspace_error = craft_workspace_readiness()
    bag = craft_bag_item()
    if not workspace_ready or not bag:
        return False, [], workspace_error + "."

    expected_amount = sum(max(1, int_value(delta, 1)) for _item, delta in output_deltas)
    already_in_bag = []
    to_move = []
    backpack = Player.Backpack

    for item, delta in output_deltas:
        try:
            parent_serial = int(item.Container)
        except:
            return False, [], "Crafted output location could not be verified."
        if parent_serial == int(bag.Serial):
            already_in_bag.append((item, delta))
        elif backpack and parent_serial == int(backpack.Serial):
            to_move.append((item, delta))
        else:
            return False, [], "Safety stop: crafted output appeared outside the main backpack and Craft Bag."

    before_move = snapshot_direct_container(bag.Serial)
    try:
        for item, delta in to_move:
            Items.Move(item.Serial, bag.Serial, int(delta))
            Misc.Pause(MOVE_PAUSE_MS)
    except Exception as ex:
        return False, [], "Could not stage crafted output in the Craft Bag: " + str(ex)

    moved_into_bag, _moved_total = detect_new_outputs(recipe, before_move, hue, bag.Serial)
    staged = merge_output_deltas(already_in_bag + moved_into_bag)
    staged_amount = sum(delta for _item, delta in staged)
    if staged_amount < expected_amount:
        return False, [], "Safety stop: the new output could not be isolated inside the Craft Bag."

    for item, _delta in staged:
        try:
            if int(item.Container) != int(bag.Serial):
                return False, [], "Safety stop: verified output is not directly inside the Craft Bag."
        except:
            return False, [], "Safety stop: verified output location became unavailable."

    return True, staged, "Staged crafted output in the Craft Bag."


def is_global_quest_contribution_text(value):
    text = " ".join(str(value or "").strip().lower().split())
    return text.startswith(GLOBAL_QUEST_SUCCESS_PREFIX) and GLOBAL_QUEST_SUCCESS_SUFFIX in text


def is_weekly_quest_craft_text(value):
    text = " ".join(str(value or "").strip().lower().split())
    return text.startswith(WEEKLY_QUEST_SUCCESS_PREFIX)


def is_bod_book_craft_text(value):
    finished, total = bod_book_progress(value)
    return finished >= 0 and total > 0


def bod_book_progress(value):
    text = " ".join(str(value or "").strip().lower().split())
    match = re.search(BOD_BOOK_PROGRESS_PATTERN, text)
    if not match:
        return -1, -1
    finished = int_value(match.group(1), -1)
    total = int_value(match.group(2), -1)
    if finished < 0 or total <= 0 or finished > total:
        return -1, -1
    return finished, total


def bod_book_completion_points(value):
    text = " ".join(str(value or "").strip().lower().split())
    match = re.search(BOD_BOOK_COMPLETE_PATTERN, text)
    return int_value(match.group(1).replace(",", ""), 0) if match else -1


def is_bod_book_complete_text(value):
    return bod_book_completion_points(value) >= 0


def bod_book_batch_target(completed, target, progress_finished, progress_total):
    completed = max(0, int_value(completed))
    target = max(completed, int_value(target, completed))
    progress_finished = int_value(progress_finished, -1)
    progress_total = int_value(progress_total, -1)
    if progress_total <= 0 or progress_finished < 0 or progress_finished > progress_total:
        return target
    return min(target, completed + (progress_total - progress_finished))


def quest_success_type(value):
    if is_bod_book_complete_text(value):
        return "bod_book_complete"
    if is_bod_book_craft_text(value):
        return "bod_book"
    if is_global_quest_contribution_text(value):
        return "global"
    if is_weekly_quest_craft_text(value):
        return "weekly"
    return ""


def quest_success_focus(success_type):
    return "bod_book" if str(success_type).startswith("bod_book") else str(success_type)


def capture_journal_cursor():
    try:
        journal_entries = Journal.GetJournalEntry(0) or []
        if len(journal_entries) > 0:
            return journal_entries[len(journal_entries) - 1]
    except:
        pass
    return None


def quest_success_since(journal_cursor, expected_focus="unchanged"):
    try:
        if journal_cursor is None:
            journal_entries = Journal.GetJournalEntry(0) or []
        else:
            journal_entries = Journal.GetJournalEntry(journal_cursor) or []
    except:
        journal_entries = []

    matched_success_type = ""
    matched_completion_points = -1
    matched_progress_finished = -1
    matched_progress_total = -1

    for journal_entry in journal_entries:
        try:
            journal_text = getattr(journal_entry, "Text", "")
            success_type = quest_success_type(journal_text)
            success_focus = quest_success_focus(success_type)
            if success_type and (expected_focus == "unchanged" or success_focus == expected_focus):
                if success_type == "bod_book_complete":
                    matched_success_type = success_type
                    matched_completion_points = max(0, bod_book_completion_points(journal_text))
                elif success_type == "bod_book":
                    progress_finished, progress_total = bod_book_progress(journal_text)
                    if progress_finished >= 0 and progress_total > 0:
                        if matched_progress_total != progress_total or progress_finished >= matched_progress_finished:
                            matched_progress_finished = progress_finished
                            matched_progress_total = progress_total
                    if matched_success_type != "bod_book_complete":
                        matched_success_type = success_type
                elif not matched_success_type:
                    matched_success_type = success_type
        except:
            pass

    if _plugin_craft_owner:
        if matched_progress_finished >= 0 and matched_progress_total > 0:
            _plugin_craft_context["bod_book_progress_finished"] = matched_progress_finished
            _plugin_craft_context["bod_book_progress_total"] = matched_progress_total
        if matched_success_type == "bod_book_complete":
            _plugin_craft_context["bod_book_complete"] = True
            _plugin_craft_context["bod_book_points"] = matched_completion_points
    return matched_success_type


def wait_for_craft_result(recipe, before_snapshots, output_hue, output_amount, journal_cursor, expected_focus):
    deadline = time.time() + (float(QUEST_RESULT_WAIT_MS) / 1000.0)
    fallback_seen_at = 0.0
    output_deltas = []
    actual_output = 0
    exact_output_match = False
    while True:
        output_deltas, actual_output, exact_output_match = detect_craft_outputs_detail(recipe, before_snapshots, output_hue)
        consumed_quest_type = quest_success_since(journal_cursor, expected_focus)
        if consumed_quest_type:
            return output_deltas, output_amount, exact_output_match, consumed_quest_type
        if actual_output >= output_amount:
            if exact_output_match:
                return output_deltas, actual_output, exact_output_match, ""
            if fallback_seen_at <= 0.0:
                fallback_seen_at = time.time()
            elif time.time() - fallback_seen_at >= float(CRAFT_FALLBACK_SETTLE_MS) / 1000.0:
                return output_deltas, actual_output, exact_output_match, ""
        if time.time() >= deadline or consume_priority_control_button():
            return output_deltas, actual_output, exact_output_match, ""
        Misc.Pause(CRAFT_RESULT_POLL_MS)


def store_new_outputs(output_deltas):
    if not _output_chest_serial:
        return True, "Kept crafted item in {0}.".format(craft_workspace_label())

    output_chest = valid_item(_output_chest_serial)
    if not output_chest:
        return False, "Crafted-item chest is no longer available."
    if _craft_bag_enabled and int(output_chest.Serial) == int(_craft_bag_serial):
        return True, "Kept crafted item in Craft Bag."

    moved = 0
    for item, delta in output_deltas:
        try:
            Items.Move(item.Serial, output_chest.Serial, delta)
            Misc.Pause(MOVE_PAUSE_MS)
            moved += 1
        except:
            pass

    if moved != len(output_deltas):
        return False, "Craft succeeded, but the new output could not be isolated for storage."
    return True, "Stored crafted output."


def open_server_craft_gump(gump_id, tool):
    try:
        close_gump(gump_id)
        Misc.Pause(CRAFT_OPEN_SETTLE_MS)
        if consume_priority_control_button():
            return False
        Items.UseItem(tool)
        Gumps.WaitForGump(int(gump_id), SERVER_GUMP_WAIT_MS)
        if consume_priority_control_button():
            return False
        return gump_is_open(gump_id)
    except:
        return False


def wait_for_returned_craft_gump(gump_id):
    deadline = time.time() + (float(SERVER_GUMP_WAIT_MS) / 1000.0)
    while time.time() < deadline:
        if gump_is_open(gump_id):
            return True
        if consume_priority_control_button():
            return False
        Misc.Pause(CRAFT_GUMP_RETURN_POLL_MS)
    return gump_is_open(gump_id)


def crafting_focus_lines(gump_id):
    lines = []
    try:
        values = Gumps.GetLineList(int(gump_id), False)
        if values:
            lines.extend([" ".join(str(value).strip().lower().split()) for value in values])
    except:
        pass
    try:
        data = Gumps.GetGumpData(int(gump_id))
        lines.extend([" ".join(str(value).strip().lower().split()) for value in (getattr(data, "gumpStrings", None) or [])])
    except:
        pass
    return lines


def read_crafting_focus(gump_id):
    lines = crafting_focus_lines(gump_id)
    matches = []
    for focus_id in FOCUS_ORDER:
        expected = " ".join(FOCUS_TEXT[focus_id].lower().split())
        if any(expected in line for line in lines):
            matches.append(focus_id)
    return matches[0] if len(matches) == 1 else ""


def focus_for_current_job(training_mode=False):
    if training_mode:
        return "none"
    if _plugin_craft_owner:
        requested = str(dict_value(_plugin_craft_context).get("focus_override", ""))
        if requested in FOCUS_ORDER:
            return requested
    if _craft_focus == "unchanged" and _component_parent_focus in FOCUS_ORDER:
        return _component_parent_focus
    return _craft_focus


def ensure_crafting_focus(gump_id, wanted_focus):
    wanted = str(wanted_focus or "unchanged")
    if wanted == "unchanged":
        return True, "Crafting focus left as-is."
    if wanted not in FOCUS_ORDER:
        return False, "Unknown requested crafting focus."
    current = read_crafting_focus(gump_id)
    if not current:
        return False, "Could not read the crafting tool's focus text."
    for _attempt in range(len(FOCUS_ORDER)):
        if current == wanted:
            return True, "Crafting focus verified: " + FOCUS_LABELS[wanted] + "."
        if consume_priority_control_button():
            return False, "Crafting focus change was interrupted."
        forward = (FOCUS_ORDER.index(wanted) - FOCUS_ORDER.index(current)) % len(FOCUS_ORDER)
        backward = (FOCUS_ORDER.index(current) - FOCUS_ORDER.index(wanted)) % len(FOCUS_ORDER)
        button = FOCUS_NEXT_BUTTON if forward <= backward else FOCUS_PREVIOUS_BUTTON
        try:
            Gumps.SendAction(int(gump_id), button)
            Gumps.WaitForGump(int(gump_id), SERVER_GUMP_WAIT_MS)
            Misc.Pause(CRAFT_MENU_SETTLE_MS)
        except Exception as ex:
            return False, "Crafting focus button failed: " + str(ex)
        changed = read_crafting_focus(gump_id)
        if not changed or changed == current:
            return False, "Crafting focus did not change after button " + str(button) + "."
        current = changed
    return False, "Crafting focus did not reach " + FOCUS_LABELS[wanted] + "."


def send_server_actions(gump_id, actions, step_label):
    for index, action in enumerate(actions):
        if consume_priority_control_button():
            return False

        action_id = int_value(action)
        if action_id <= 0:
            return False

        set_status("{0}: action {1}/{2}.".format(step_label, index + 1, len(actions)), LABEL_HUE, step_label)
        try:
            Gumps.SendAction(int(gump_id), action_id)
            if index < len(actions) - 1:
                Gumps.WaitForGump(int(gump_id), SERVER_GUMP_WAIT_MS)
                Misc.Pause(CRAFT_MENU_SETTLE_MS)
                if consume_priority_control_button():
                    return False
                if not gump_is_open(gump_id):
                    return False
        except:
            return False
    return True


def clear_training_pending_recovery():
    global _training_pending_recovery
    global _training_pending_recovery_module_id, _training_pending_recovery_completion

    count = len(_training_pending_recovery)
    _training_pending_recovery = []
    _training_pending_recovery_module_id = ""
    _training_pending_recovery_completion = ""
    return count


def clear_training_pending_outputs(clear_recovery=True):
    global _training_pending_outputs, _training_pending_disposal
    global _training_pending_module_id, _training_pending_recipe_id, _training_pending_recipe_name

    count = len(_training_pending_outputs)
    _training_pending_outputs = []
    _training_pending_disposal = {}
    _training_pending_module_id = ""
    _training_pending_recipe_id = ""
    _training_pending_recipe_name = ""
    if clear_recovery:
        count += clear_training_pending_recovery()
    return count


def queue_training_outputs(output_deltas, stage, module, recipe):
    global _training_pending_outputs, _training_pending_disposal
    global _training_pending_module_id, _training_pending_recipe_id, _training_pending_recipe_name

    pending = []
    for item, delta in output_deltas:
        try:
            pending.append({
                "serial": int(item.Serial),
                "amount": max(1, int(delta)),
                "container_serial": int(item.Container),
            })
        except:
            pass

    _training_pending_outputs = pending
    _training_pending_disposal = training_disposal(stage)
    _training_pending_module_id = str(module.get("id", ""))
    _training_pending_recipe_id = str(recipe.get("id", ""))
    _training_pending_recipe_name = str(recipe.get("name", "crafted item"))


def pending_training_item():
    while _training_pending_outputs:
        record = dict_value(_training_pending_outputs[0])
        item = valid_item(record.get("serial"))
        if item:
            return record, item
        _training_pending_outputs.pop(0)
    return None, None


def pending_training_location_ready(record, item):
    expected_container = int_value(record.get("container_serial"), Player.Backpack.Serial)
    try:
        if int(item.Container) != expected_container:
            return False, "Safety stop: verified training output left its crafting container."
    except:
        return False, "Safety stop: training output location could not be verified."

    if _craft_bag_enabled and expected_container != int(_craft_bag_serial):
        return False, "Safety stop: automated disposal is restricted to the Craft Bag."
    return True, ""


def queue_recovered_training_resources(recipe, before_main_pack, module_id, completion_message):
    global _training_pending_recovery
    global _training_pending_recovery_module_id, _training_pending_recovery_completion

    if not _craft_bag_enabled or not recipe:
        return True, ""

    resources, error = resolve_resource_list(recipe.get("resources"))
    if not resources:
        recovery_error = error or "recipe resources could not be resolved"
        _training_pending_recovery = [{"error": recovery_error}]
        _training_pending_recovery_module_id = str(module_id)
        _training_pending_recovery_completion = str(completion_message)
        return False, recovery_error

    bag = craft_bag_item()
    if not bag:
        recovery_error = "the Craft Bag is unavailable"
        _training_pending_recovery = [{"error": recovery_error}]
        _training_pending_recovery_module_id = str(module_id)
        _training_pending_recovery_completion = str(completion_message)
        return False, recovery_error

    pending = []
    for resource in resources:
        recovered = detect_new_descriptor_items(resource, before_main_pack, Player.Backpack.Serial, int_value(resource.get("hue"), -1))
        recovered_amount = sum(max(1, int_value(delta, 1)) for _item, delta in recovered)
        if recovered_amount <= 0:
            continue
        pending.append({
            "resource": resource,
            "recovered_amount": recovered_amount,
            "target_count": count_resource(bag.Serial, resource) + recovered_amount,
            "name": str(resource.get("name", "resource")),
        })

    if pending:
        _training_pending_recovery = pending
        _training_pending_recovery_module_id = str(module_id)
        _training_pending_recovery_completion = str(completion_message)
    return True, ""


def process_pending_training_recovery():
    if not _training_pending_recovery:
        return "ready", "No recovered resources are waiting."

    if not _craft_bag_enabled:
        completion = _training_pending_recovery_completion
        clear_training_pending_recovery()
        return "ready", completion + "."

    bag = craft_bag_item()
    if not bag:
        return "retry", "Craft Bag is unavailable for recovered resources"

    record = dict_value(_training_pending_recovery[0])
    if record.get("error"):
        return "error", str(record.get("error"))
    resource = dict_value(record.get("resource"))
    if not resource:
        return "error", "Recovered-resource descriptor is missing"

    target_count = max(0, int_value(record.get("target_count")))
    current_count = count_resource(bag.Serial, resource)
    if current_count < target_count:
        missing = target_count - current_count
        move_descriptor_from_main_pack_to_craft_bag(resource, missing, int_value(resource.get("hue"), -1))
        current_count = count_resource(bag.Serial, resource)
        if current_count < target_count:
            return "retry", "Could not move recovered {0} into the Craft Bag ({1}/{2})".format(
                record.get("name", "resource"),
                current_count,
                target_count,
            )

    _training_pending_recovery.pop(0)
    if _training_pending_recovery:
        return "progress", "Staged recovered {0}; more recovered resources remain.".format(record.get("name", "resource"))

    completion = _training_pending_recovery_completion
    clear_training_pending_recovery()
    return "ready", completion + "; recovered resources staged."


def release_pending_training_recovery():
    resource_chest = valid_item(_resource_chest_serial)
    bag = craft_bag_item()
    returned_names = []
    backpack_names = []

    for record in list(_training_pending_recovery):
        record = dict_value(record)
        resource = dict_value(record.get("resource"))
        resource_name = str(record.get("name", "resource"))
        if not resource:
            backpack_names.append(resource_name)
            continue

        bag_count = count_resource(bag.Serial, resource) if bag else 0
        outstanding = max(0, int_value(record.get("target_count")) - bag_count)
        if outstanding <= 0:
            continue

        moved = 0
        if resource_chest:
            moved = move_descriptor_from_main_pack_to_container(
                resource,
                outstanding,
                resource_chest.Serial,
                int_value(resource.get("hue"), -1),
            )
        if moved >= outstanding:
            returned_names.append(resource_name)
        else:
            backpack_names.append(resource_name)

    clear_training_pending_recovery()

    if backpack_names:
        return "Recovery move skipped after retries; {0} may remain in the main backpack and will be swept by restocking later.".format(
            ", ".join(backpack_names)
        )
    if returned_names:
        return "Recovery move skipped after retries; returned {0} to the resource chest and continued.".format(
            ", ".join(returned_names)
        )
    return "Recovered resources were already accounted for; continuing training."


def move_pending_training_output(destination_serial, verb):
    record, item = pending_training_item()
    if not item:
        clear_training_pending_outputs()
        return "ready", verb + " output already handled."

    destination = valid_item(destination_serial)
    if not destination:
        return "error", "Training output is waiting, but the destination container is unavailable."

    location_ready, location_error = pending_training_location_ready(record, item)
    if not location_ready:
        return "error", location_error

    expected_container = int_value(record.get("container_serial"), Player.Backpack.Serial)
    if int(destination.Serial) == expected_container:
        if verb == "Stored":
            _training_pending_outputs.pop(0)
            if not _training_pending_outputs:
                clear_training_pending_outputs()
                return "ready", "Saved training output in " + craft_workspace_label() + "."
            return "progress", "Saved one training output in " + craft_workspace_label() + "."
        return "error", "Craft Bag cannot also be the training trash container."

    move_amount = int_value(record.get("amount"), 1)
    try:
        before_amount = int(item.Amount)
    except:
        before_amount = move_amount

    try:
        Items.Move(item.Serial, destination.Serial, move_amount)
        Misc.Pause(MOVE_PAUSE_MS)
    except Exception as ex:
        return "error", "Could not {0} training output: {1}".format(verb.lower(), ex)

    remaining = valid_item(item.Serial)
    if remaining:
        try:
            at_destination = int(remaining.Container) == int(destination.Serial) or int(remaining.RootContainer) == int(destination.Serial)
            reduced_in_pack = int(remaining.Amount) <= before_amount - move_amount
            if not at_destination and not reduced_in_pack:
                return "error", "Training output did not move to the configured destination."
        except:
            pass

    _training_pending_outputs.pop(0)
    if not _training_pending_outputs:
        clear_training_pending_outputs()
        return "ready", verb + " training output."
    return "progress", verb + " one training output."


def process_training_pending_outputs():
    if not _training_pending_outputs:
        return "ready", "No training output is waiting."

    mode = clean_key(_training_pending_disposal.get("mode", DISPOSAL_NONE))
    if mode == DISPOSAL_NONE:
        clear_training_pending_outputs()
        return "ready", "Left training output in " + craft_workspace_label() + "."
    if mode == DISPOSAL_SAVE:
        if not _output_chest_serial:
            clear_training_pending_outputs()
            return "ready", "Saved training output in " + craft_workspace_label() + "."
        return move_pending_training_output(_output_chest_serial, "Stored")
    if mode == DISPOSAL_TRASH:
        return move_pending_training_output(_trash_container_serial, "Trashed")
    if mode not in TARGETED_DISPOSAL_MODES:
        return "error", "Unsupported training disposal mode: " + mode

    completed_verbs = {
        DISPOSAL_SMELT: "Smelted",
        DISPOSAL_SALVAGE: "Salvaged",
        DISPOSAL_RECYCLE: "Recycled",
    }
    completion_message = "{0} {1}".format(completed_verbs.get(mode, "Processed"), _training_pending_recipe_name)

    module = module_by_id(_training_pending_module_id)
    if not module:
        return "error", "The training output's craft module is no longer loaded."

    _recipe_category, pending_recipe = find_module_recipe(module, _training_pending_recipe_id)
    if _craft_bag_enabled and not pending_recipe:
        return "error", "Safety stop: the pending training recipe could not be resolved."

    record, item = pending_training_item()
    if not item:
        clear_training_pending_outputs()
        return "ready", "Training output was already handled."

    location_ready, location_error = pending_training_location_ready(record, item)
    if not location_ready:
        return "error", location_error

    tool_state, tool_result = ensure_tool(module)
    if _operation_interrupted or consume_priority_control_button():
        return "progress", "Training disposal interrupted."
    if tool_state == "progress":
        return "progress", "Acquiring tool before " + mode + "."
    if tool_state == "error":
        return "error", str(tool_result)

    gump_id = int_value(module.get("craft_gump_id"))
    if not open_server_craft_gump(gump_id, tool_result):
        return "retry", "Disposal gump did not open for " + mode

    button = int_value(_training_pending_disposal.get("button"))
    if button <= 0:
        return "error", "Training disposal button is not mapped for " + mode + "."
    if not send_server_actions(gump_id, [button], "Training " + mode.title()):
        return "retry", "Disposal button failed for " + mode

    target_output = bool(_training_pending_disposal.get("target_output", True))
    if target_output:
        target_ready = Target.WaitForTarget(TARGET_CURSOR_WAIT_MS, False)
        if consume_priority_control_button():
            Target.Cancel()
            return "progress", "Training disposal interrupted."
        if not target_ready:
            return "retry", "No disposal target appeared for " + mode
        try:
            before_amount = int(item.Amount)
        except:
            before_amount = int_value(record.get("amount"), 1)
        if before_amount > int_value(record.get("amount"), 1):
            Target.Cancel()
            return "error", "Cannot safely {0} a stack containing older items; move existing {1} out of {2}.".format(mode, _training_pending_recipe_name, craft_workspace_label())
        before_recovery = snapshot_direct_container(Player.Backpack.Serial) if _craft_bag_enabled else {}
        Target.TargetExecute(item.Serial)
        Misc.Pause(CRAFT_RESULT_PAUSE_MS)

        remaining = valid_item(item.Serial)
        if remaining:
            try:
                still_in_pack = int(remaining.Container) == int_value(record.get("container_serial"), Player.Backpack.Serial)
                not_reduced = int(remaining.Amount) >= before_amount
                if still_in_pack and not_reduced:
                    return "retry", "{0} did not consume {1}".format(mode.title(), _training_pending_recipe_name)
            except:
                pass

        recovery_ready, recovery_error = queue_recovered_training_resources(
            pending_recipe,
            before_recovery,
            module.get("id", ""),
            completion_message,
        )
        _training_pending_outputs.pop(0)
        if not _training_pending_outputs:
            clear_training_pending_outputs(False)
        if not recovery_ready:
            return "error", completion_message + ", but " + recovery_error
        if _training_pending_recovery:
            return "progress", completion_message + "; staging recovered resources next."
        if _training_pending_outputs:
            return "progress", completion_message + "; more training output remains."
        return "ready", completion_message + "."

    _training_pending_outputs.pop(0)
    if not _training_pending_outputs:
        clear_training_pending_outputs(False)
        return "ready", completion_message + "."
    return "progress", "Processed one training output with " + mode + "."


def craft_action_sequence(recipe, resources):
    actions = []
    used_groups = []

    for resource in resources:
        group_id = clean_key(resource.get("choice_group"))
        if not group_id or group_id in used_groups:
            continue
        used_groups.append(group_id)
        option = selected_choice_for_group(group_id)
        if option:
            actions.extend(list_value(option.get("craft_actions")))

    category = find_category_for_recipe(recipe)
    if category:
        actions.extend(list_value(category.get("open_actions")))

    recipe_actions = list_value(recipe.get("craft_actions"))
    if recipe_actions:
        actions.extend(recipe_actions)
    else:
        actions.append(int_value(recipe.get("button")))

    return actions


def reset_make_last(close_server_gump=False):
    global _verified_make_last_signature, _make_last_candidate_signature
    global _make_last_confirmation_count, _make_last_gump_id

    previous_gump_id = int_value(_make_last_gump_id)
    _verified_make_last_signature = ""
    _make_last_candidate_signature = ""
    _make_last_confirmation_count = 0
    _make_last_gump_id = 0
    if close_server_gump and previous_gump_id > 0:
        close_gump(previous_gump_id)


def make_last_workspace_signature():
    if _plugin_craft_owner:
        requested = str(dict_value(_plugin_craft_context).get("workspace_override", "")).lower()
        if requested == "backpack":
            return "backpack"
    if _craft_bag_enabled:
        return "craft_bag:{0}".format(int_value(_craft_bag_serial))
    return "backpack"


def craft_make_last_signature(module, recipe, resources, wanted_focus):
    parts = [
        "owner=" + clean_key(_plugin_craft_owner or "core"),
        "workspace=" + make_last_workspace_signature(),
        clean_key(module.get("id")),
        str(int_value(module.get("craft_gump_id"))),
        clean_key(recipe.get("id")),
        clean_key(wanted_focus or "unchanged"),
    ]
    used_groups = []
    for resource in resources:
        group_id = clean_key(resource.get("choice_group"))
        if not group_id or group_id in used_groups:
            continue
        used_groups.append(group_id)
        option = selected_choice_for_group(group_id)
        parts.append(group_id + "=" + clean_key(dict_value(option).get("id")))
    return "|".join(parts)


def make_last_button(module):
    return int_value(dict_value(module.get("server_actions")).get("make_last"))


def make_last_signature_is_current(signature):
    wanted = str(signature or "")
    return bool(wanted) and wanted == _make_last_candidate_signature and _make_last_confirmation_count > 0


def make_last_handoff_active():
    return bool(_make_last_candidate_signature) and _make_last_confirmation_count > 0


def make_last_confirmations_required():
    return MAKE_LAST_CONFIRMATIONS_REQUIRED if _plugin_craft_owner else 1


def can_use_make_last(module, signature):
    required = make_last_confirmations_required()
    return (
        make_last_button(module) > 0
        and bool(signature)
        and signature == _verified_make_last_signature
        and _make_last_confirmation_count >= required
    )


def arm_make_last(signature):
    global _verified_make_last_signature, _make_last_candidate_signature
    global _make_last_confirmation_count, _make_last_gump_id

    wanted = str(signature or "")
    if not wanted:
        reset_make_last()
        return
    if wanted != _make_last_candidate_signature:
        _make_last_candidate_signature = wanted
        _make_last_confirmation_count = 0
        _verified_make_last_signature = ""
    required = make_last_confirmations_required()
    _make_last_confirmation_count = min(
        required,
        _make_last_confirmation_count + 1,
    )
    module = active_module()
    _make_last_gump_id = int_value(dict_value(module).get("craft_gump_id"))
    if _make_last_confirmation_count >= required:
        _verified_make_last_signature = wanted


def prepare_make_last_for_runtime():
    if not _plugin_craft_owner:
        reset_make_last(True)
        return

    module = active_module()
    recipe = selected_recipe()
    resources, _error = resolve_resource_list(dict_value(recipe).get("resources")) if recipe else ([], "")
    if not module or not recipe or not resources:
        reset_make_last(True)
        return

    signature = craft_make_last_signature(module, recipe, resources, focus_for_current_job(False))
    if not make_last_signature_is_current(signature):
        reset_make_last(True)


# ===========================================================
# CRAFTING STATE MACHINE
# ===========================================================

def clear_action_failures(action_key=None):
    global _action_failures

    if action_key is None:
        _action_failures = {}
        return
    _action_failures.pop(str(action_key), None)


def retry_action_or_pause(action_key, message, step_label):
    key = str(action_key)
    failure_count = int_value(_action_failures.get(key), 0) + 1
    _action_failures[key] = failure_count

    if failure_count <= MAX_ACTION_RETRIES:
        set_status(
            "{0}; retry {1}/{2}.".format(str(message).rstrip("."), failure_count, MAX_ACTION_RETRIES),
            WARN_HUE,
            step_label,
        )
        return True

    clear_action_failures(key)
    stop_runtime(
        "Paused after the initial {0} attempt plus {1} retries: {2}.".format(
            str(step_label).lower(),
            MAX_ACTION_RETRIES,
            str(message).rstrip("."),
        ),
        BAD_HUE,
    )
    return False


def retry_recovery_or_continue(message):
    key = "training_recovery"
    failure_count = int_value(_action_failures.get(key), 0) + 1
    _action_failures[key] = failure_count

    if failure_count <= MAX_ACTION_RETRIES:
        set_status(
            "{0}; retry {1}/{2}.".format(str(message).rstrip("."), failure_count, MAX_ACTION_RETRIES),
            WARN_HUE,
            "Stage Recovered Resources",
        )
        return True

    clear_action_failures(key)
    set_status(release_pending_training_recovery(), WARN_HUE, "Recovery Fallback")
    return False


def stop_runtime(message="Stopped.", hue=WARN_HUE):
    global _runtime_active, _training_active, _dirty_ui
    global _component_recipe_stack, _component_parent_focus

    _runtime_active = False
    _training_active = False
    _component_recipe_stack = []
    _component_parent_focus = ""
    reset_make_last(True)
    if _cleanup_active:
        reset_material_cleanup(False)
    set_status(message, hue, "Idle")
    _dirty_ui = True


def start_runtime():
    global _runtime_active, _training_active, _completed_amount, _consecutive_failures
    global _button_sequence_failures, _dirty_ui
    global _component_recipe_stack, _component_parent_focus

    if _cleanup_active:
        set_status("Wait for material cleanup to finish before starting another job.", WARN_HUE, "Cleanup Materials")
        return

    recipe = selected_recipe()
    ready, reason = recipe_readiness(recipe)
    if not ready:
        set_status("Cannot start: " + reason + ".", BAD_HUE, "Validation")
        return

    workspace_ready, workspace_error = prepare_craft_workspace()
    if not workspace_ready:
        set_status("Cannot start: " + workspace_error + ".", BAD_HUE, "Craft Bag Validation")
        return

    _completed_amount = 0
    _consecutive_failures = 0
    _button_sequence_failures = 0
    _component_recipe_stack = []
    _component_parent_focus = ""
    prepare_make_last_for_runtime()
    clear_action_failures()
    reset_session_resources()
    _training_active = False
    _runtime_active = True
    set_status("Starting {0} x{1}.".format(recipe.get("name", "recipe"), _target_amount), GOOD_HUE, "Validation")
    _dirty_ui = True


def finish_runtime():
    global _runtime_active, _dirty_ui, _component_parent_focus

    _runtime_active = False
    _component_parent_focus = ""
    recipe = selected_recipe()
    name = str(recipe.get("name", "recipe")) if recipe else "recipe"
    if _plugin_craft_owner:
        module = active_module()
        handoff_pending = make_last_handoff_active()
        handoff_ready = handoff_pending and can_use_make_last(module, _verified_make_last_signature)
        if not handoff_pending and module:
            close_gump(int_value(module.get("craft_gump_id")))
        if handoff_ready:
            handoff_text = " Fast handoff is ready."
        elif handoff_pending:
            handoff_text = " Craft confirmation is still calibrating."
        else:
            handoff_text = " Fast handoff was not retained."
        set_status(
            "Plugin craft output ready: {0} x{1}; waiting for the plugin to process it.{2}".format(name, _completed_amount, handoff_text),
            GOOD_HUE,
            "Plugin Output",
        )
        _dirty_ui = True
        return
    reset_make_last()
    begin_material_cleanup(
        "runtime",
        "Complete: {0} x{1}.".format(name, _completed_amount),
        GOOD_HUE,
        "Complete",
        "Frog Crafting job complete.",
    )
    _dirty_ui = True


def start_training():
    global _runtime_active, _training_active, _training_crafts
    global _training_start_skill, _training_session_module_id
    global _consecutive_failures, _button_sequence_failures
    global _selected_category_id, _selected_recipe_id, _dirty_ui

    if _cleanup_active:
        set_status("Wait for material cleanup to finish before starting training.", WARN_HUE, "Cleanup Materials")
        return

    reset_make_last()

    module = active_module()
    profile = training_profile(module)
    if not module or not profile:
        set_status("Cannot start: training module is not loaded.", BAD_HUE, "Training Validation")
        return
    if bool(profile.get("informational", False)):
        _module, profile, skill_value, _skill_cap, goal, stage, category, recipe, reason = training_context()
        _runtime_active = False
        _training_active = False
        set_status(reason, GOOD_HUE, "Training Guide")
        Misc.SendMessage(reason, GOOD_HUE)
        _dirty_ui = True
        return

    template_state, template_message = ensure_crafting_template(module)
    if template_state != "ready":
        set_status("Cannot start training: " + template_message + ".", BAD_HUE, "Activate Crafting Template")
        return

    _module, profile, skill_value, _skill_cap, goal, stage, category, recipe, reason = training_context()
    workspace_ready, workspace_error = prepare_craft_workspace()
    if not workspace_ready:
        set_status("Cannot start: " + workspace_error + ".", BAD_HUE, "Craft Bag Validation")
        return
    module_id = str(module.get("id", ""))
    pending_output_matches = _training_pending_outputs and _training_pending_module_id == module_id
    pending_recovery_matches = _training_pending_recovery and _training_pending_recovery_module_id == module_id
    if pending_output_matches or pending_recovery_matches:
        clear_action_failures()
        _runtime_active = False
        _training_active = True
        set_status("Resuming pending training cleanup.", WARN_HUE, "Training Resume")
        _dirty_ui = True
        return
    if skill_value >= goal:
        reset_session_resources()
        finish_training()
        return
    if not stage:
        set_status("Cannot start: " + reason, BAD_HUE, "Training Validation")
        return
    if clean_key(stage.get("mode", "craft")) == "npc_train":
        set_status(reason, WARN_HUE, "NPC Training Required")
        return
    if not recipe or not category:
        set_status("Cannot start: " + reason, BAD_HUE, "Training Mapping")
        return

    disposal_ready, disposal_error = training_disposal_readiness(stage)
    if not disposal_ready:
        set_status("Cannot start: " + disposal_error + ".", BAD_HUE, "Training Disposal")
        return

    if _training_session_module_id != module_id:
        clear_training_pending_outputs()
        reset_session_resources()
        _training_crafts = 0
        _training_start_skill = skill_value
        _training_session_module_id = module_id
    elif _training_crafts == 0 and not training_work_pending():
        _training_start_skill = skill_value

    _selected_category_id = str(category.get("id", ""))
    _selected_recipe_id = str(recipe.get("id", ""))
    _consecutive_failures = 0
    _button_sequence_failures = 0
    clear_action_failures()
    _runtime_active = False
    _training_active = True
    set_status("Training {0} with {1}.".format(module.get("name", "crafting"), recipe.get("name", "recipe")), GOOD_HUE, "Training Start")
    _dirty_ui = True


def finish_training():
    global _training_active, _dirty_ui

    module = active_module()
    profile = training_profile(module)
    skill_name = str(module.get("skill_name", module.get("name", "Skill"))) if module else "Skill"
    skill_value = player_skill_value(skill_name)
    skill_cap = player_skill_cap(skill_name)
    goal = training_goal(profile, skill_cap) if profile else skill_value
    _training_active = False
    reset_make_last()
    begin_material_cleanup(
        "training",
        "Training complete: {0} {1:.1f}/{2:.1f}.".format(skill_name, skill_value, goal),
        GOOD_HUE,
        "Training Complete",
        "Frog Crafting training complete.",
    )
    _dirty_ui = True


def training_step():
    global _runtime_active, _training_active
    global _selected_category_id, _selected_recipe_id, _dirty_ui

    if not _training_active:
        return

    if _training_pending_recovery:
        state, message = process_pending_training_recovery()
        if _operation_interrupted:
            return
        if state in ("retry", "error"):
            retry_recovery_or_continue(message)
        else:
            clear_action_failures("training_recovery")
            set_status(message, GOOD_HUE if state == "ready" else WARN_HUE, "Stage Recovered Resources")
        _dirty_ui = True
        return

    if _training_pending_outputs:
        state, message = process_training_pending_outputs()
        if _operation_interrupted:
            return
        if state in ("retry", "error"):
            retry_action_or_pause("training_disposal", message, "Process Training Output")
        else:
            clear_action_failures("training_disposal")
            set_status(message, GOOD_HUE if state == "ready" else WARN_HUE, "Process Training Output")
        _dirty_ui = True
        return

    template_state, template_message = ensure_crafting_template(active_module())
    if _operation_interrupted or template_state == "interrupted":
        return
    if template_state == "error":
        retry_action_or_pause("activate_crafting_template", template_message, "Activate Crafting Template")
        return
    clear_action_failures("activate_crafting_template")

    glasses_state, glasses_message = suppress_crafting_glasses_for_training()
    if _operation_interrupted or glasses_state == "interrupted":
        return
    if glasses_state == "error":
        retry_action_or_pause("suppress_training_glasses", glasses_message, "Remove Training Glasses")
        return
    clear_action_failures("suppress_training_glasses")

    profile = training_profile()
    apply_training_choices(profile)
    _module, profile, skill_value, _skill_cap, goal, stage, category, recipe, reason = training_context()

    if profile and bool(profile.get("informational", False)):
        _runtime_active = False
        _training_active = False
        set_status(reason, GOOD_HUE, "Training Guide")
        _dirty_ui = True
        return

    if skill_value >= goal:
        finish_training()
        return
    if not stage:
        stop_runtime("Training paused: " + reason, BAD_HUE)
        return
    if clean_key(stage.get("mode", "craft")) == "npc_train":
        stop_runtime(reason, WARN_HUE)
        return
    if not recipe or not category:
        stop_runtime("Training paused: " + reason, BAD_HUE)
        return

    disposal_ready, disposal_error = training_disposal_readiness(stage)
    if not disposal_ready:
        stop_runtime("Training paused: " + disposal_error + ".", BAD_HUE)
        return

    _selected_category_id = str(category.get("id", ""))
    _selected_recipe_id = str(recipe.get("id", ""))
    craft_step(stage)


def craft_step(training_stage=None):
    global _target_amount, _completed_amount, _consecutive_failures, _button_sequence_failures
    global _training_crafts, _dirty_ui

    training_mode = training_stage is not None

    if training_mode:
        if not _training_active:
            return
    elif not _runtime_active:
        return

    if focus_for_current_job(training_mode) == "guild":
        stop_runtime("Guild focus is mapped, but its consumed-craft journal success line is still unknown; no materials were spent.", WARN_HUE)
        return

    module = active_module()
    recipe = selected_recipe()
    ready, reason = recipe_readiness(recipe)
    if not ready:
        stop_runtime("Paused: " + reason + ".", BAD_HUE)
        return

    workspace_ready, workspace_error = craft_workspace_readiness()
    if not workspace_ready:
        stop_runtime("Paused: " + workspace_error + ".", BAD_HUE)
        return

    if not training_mode and _completed_amount >= _target_amount:
        finish_runtime()
        return

    resources, error = resolve_resource_list(recipe.get("resources"))
    if not resources:
        retry_action_or_pause("resolve_resources", "Resource setup error: " + error, "Resolve Resources")
        return
    clear_action_failures("resolve_resources")

    wanted_focus = focus_for_current_job(training_mode)
    make_last_signature = craft_make_last_signature(module, recipe, resources, wanted_focus)
    handoff_current = make_last_signature_is_current(make_last_signature)
    use_make_last = can_use_make_last(module, make_last_signature)

    if not handoff_current:
        template_state, template_message = ensure_crafting_template(module)
        if _operation_interrupted or template_state == "interrupted" or consume_priority_control_button():
            return
        if template_state == "error":
            retry_action_or_pause("activate_crafting_template", template_message, "Activate Crafting Template")
            return
        clear_action_failures("activate_crafting_template")

        glasses_state, glasses_message = suppress_crafting_glasses_for_training() if training_mode else ensure_crafting_glasses(module)
        if _operation_interrupted or consume_priority_control_button():
            return
        if glasses_state == "error":
            glasses_action = "suppress_training_glasses" if training_mode else "equip_crafting_glasses"
            glasses_step = "Remove Training Glasses" if training_mode else "Equip Crafting Glasses"
            retry_action_or_pause(glasses_action, glasses_message, glasses_step)
            return
        clear_action_failures("suppress_training_glasses" if training_mode else "equip_crafting_glasses")

        ignore_skill_requirements = bool(_plugin_craft_owner) and bool(dict_value(_plugin_craft_context).get("ignore_skill_requirements", False))
        if not ignore_skill_requirements:
            skill_checks = [(str(module.get("skill_name", "Blacksmith")), float(recipe.get("min_skill")))]
            additional_checks, _skill_error = additional_skill_requirements(recipe)
            skill_checks.extend(additional_checks)

            for skill_name, minimum in skill_checks:
                skill_value = player_crafting_skill_value(skill_name, not training_mode)

                if skill_value < minimum:
                    stop_runtime("Need {0} {1:.1f}; current {2:.1f}.".format(skill_name, minimum, skill_value), BAD_HUE)
                    return

    register_session_resources(resources)

    remaining = RESTOCK_CHUNK_CRAFTS if training_mode else _target_amount - _completed_amount
    resource_state, resource_error = ensure_resource_list(resources, remaining)
    if _operation_interrupted or consume_priority_control_button():
        return
    if resource_state == "progress":
        clear_action_failures("restock_resources")
        return
    if resource_state == "error":
        retry_action_or_pause("restock_resources", resource_error, "Restock Resources")
        return
    clear_action_failures("restock_resources")

    output_hue = int_value(recipe.get("output_hue"), -1)
    output_amount = max(1, int_value(recipe.get("output_amount"), 1))
    before_snapshots = snapshot_output_locations()

    craft_gump_id = int_value(module.get("craft_gump_id"))
    if handoff_current:
        if not gump_is_open(craft_gump_id):
            set_status("Waiting for the server to return the {0} menu.".format(module.get("name", "crafting")), LABEL_HUE, "Wait for Craft Gump")
        if not wait_for_returned_craft_gump(craft_gump_id):
            if _operation_interrupted:
                return
            reset_make_last()
            retry_action_or_pause(
                "return_craft_gump",
                "Crafting gump 0x{0:X} did not return; the tool will be reopened".format(craft_gump_id),
                "Wait for Craft Gump",
            )
            _dirty_ui = True
            return
        clear_action_failures("return_craft_gump")
        if use_make_last:
            set_status("Server returned the verified {0} menu; sending Make Last.".format(module.get("name", "crafting")), LABEL_HUE, "Make Last")
        else:
            set_status("Server returned the {0} menu for confirmation craft {1}/{2}.".format(module.get("name", "crafting"), _make_last_confirmation_count + 1, make_last_confirmations_required()), LABEL_HUE, "Confirm Craft")
    else:
        tool_state, tool_result = ensure_tool(module)
        if _operation_interrupted or consume_priority_control_button():
            return
        if tool_state == "progress":
            clear_action_failures("acquire_tool")
            return
        if tool_state == "error":
            retry_action_or_pause("acquire_tool", str(tool_result), "Acquire Tool")
            return
        clear_action_failures("acquire_tool")

        set_status("Opening {0} menu.".format(module.get("name", "crafting")), LABEL_HUE, "Open Craft Gump")
        if not open_server_craft_gump(craft_gump_id, tool_result):
            if _operation_interrupted:
                return
            retry_action_or_pause("open_craft_gump", "Crafting gump 0x{0:X} did not open".format(craft_gump_id), "Open Craft Gump")
            _dirty_ui = True
            return
        clear_action_failures("return_craft_gump")
    clear_action_failures("open_craft_gump")

    if not handoff_current:
        focus_ready, focus_message = ensure_crafting_focus(craft_gump_id, wanted_focus)
        if _operation_interrupted or consume_priority_control_button():
            return
        if not focus_ready:
            retry_action_or_pause("set_craft_focus", focus_message, "Craft Focus")
            return
        clear_action_failures("set_craft_focus")

    actions = [make_last_button(module)] if use_make_last else craft_action_sequence(recipe, resources)
    action_label = "Make Last" if use_make_last else "Craft Item"
    if training_mode:
        craft_progress = "training craft {0}".format(_training_crafts + 1)
    else:
        craft_progress = "{0}/{1}".format(_completed_amount + 1, _target_amount)
    method_text = " with Make Last" if use_make_last else ""
    set_status("Crafting {0}{1} ({2}).".format(recipe.get("name", "recipe"), method_text, craft_progress), LABEL_HUE, action_label)
    journal_cursor = capture_journal_cursor()
    sequence_complete = send_server_actions(craft_gump_id, actions, action_label)

    if _operation_interrupted:
        return

    output_deltas, actual_output, exact_output_match, consumed_quest_type = wait_for_craft_result(recipe, before_snapshots, output_hue, output_amount, journal_cursor, wanted_focus)
    if _operation_interrupted:
        return
    strong_output_verification = bool(exact_output_match) or (bool(consumed_quest_type) and bool(sequence_complete))

    if use_make_last and actual_output >= output_amount and not strong_output_verification:
        reset_make_last()
        _consecutive_failures += 1
        if _consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            stop_runtime("Paused after {0} unverified Make Last outputs.".format(_consecutive_failures), BAD_HUE)
            return
        set_status(
            "Make Last output did not exactly match {0}; shortcut disarmed and the full recipe sequence will be retried.".format(recipe.get("name", "recipe")),
            WARN_HUE,
            "Verify Make Last",
        )
        _dirty_ui = True
        return

    if not sequence_complete and actual_output < output_amount:
        reset_make_last()
        _button_sequence_failures += 1
        if _button_sequence_failures > MAX_BUTTON_SEQUENCE_RETRIES:
            stop_runtime(
                "Paused after the initial button-sequence attempt plus {0} retries.".format(MAX_BUTTON_SEQUENCE_RETRIES),
                BAD_HUE,
            )
            return
        set_status(
            "Button sequence incomplete; reopening tool to retry {0}/{1}.".format(
                _button_sequence_failures,
                MAX_BUTTON_SEQUENCE_RETRIES,
            ),
            WARN_HUE,
            "Retry Button Sequence",
        )
        _dirty_ui = True
        return

    _button_sequence_failures = 0

    if actual_output < output_amount:
        reset_make_last()
        _consecutive_failures += 1
        if _consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            stop_runtime("Paused after {0} unverified craft failures.".format(_consecutive_failures), BAD_HUE)
            return
        set_status("No output detected; retry {0}/{1}.".format(_consecutive_failures, MAX_CONSECUTIVE_FAILURES), WARN_HUE, "Verify Output")
        _dirty_ui = True
        return

    _consecutive_failures = 0
    if consumed_quest_type:
        stored = True
        store_message = "Contributed crafted output to {0}.".format(FOCUS_LABELS.get(quest_success_focus(consumed_quest_type), consumed_quest_type))
    else:
        while True:
            staged, staged_deltas, stage_error = stage_new_outputs_in_craft_bag(recipe, output_deltas, output_hue)
            if staged:
                output_deltas = staged_deltas
                clear_action_failures("stage_craft_output")
                break
            if not retry_action_or_pause("stage_craft_output", stage_error, "Stage Craft Output"):
                return
            Misc.Pause(MOVE_PAUSE_MS)
        if training_mode:
            queue_training_outputs(output_deltas, training_stage, module, recipe)
            stored = True
            store_message = "Crafted output is ready for " + clean_key(training_disposal(training_stage).get("mode", DISPOSAL_NONE)) + "."
        else:
            while True:
                stored, store_message = store_new_outputs(output_deltas)
                if stored:
                    clear_action_failures("store_craft_output")
                    break
                if not retry_action_or_pause("store_craft_output", store_message, "Store Craft Output"):
                    return
                Misc.Pause(MOVE_PAUSE_MS)
    if not stored:
        return

    if strong_output_verification:
        arm_make_last(make_last_signature)
    else:
        reset_make_last()

    if training_mode:
        _training_crafts += 1
        current_skill = player_skill_value(str(module.get("skill_name", module.get("name", "Skill"))))
        if not training_work_pending():
            profile = training_profile(module)
            current_goal = training_goal(profile, player_skill_cap(str(module.get("skill_name", "Skill"))))
            if current_skill >= current_goal:
                finish_training()
                return
        set_status("{0}; skill {1:.1f}; {2}".format(recipe.get("name", "Crafted"), current_skill, store_message), GOOD_HUE, "Training Output")
        _dirty_ui = True
        return

    _completed_amount += actual_output
    if _completed_amount > _target_amount:
        _completed_amount = _target_amount

    if _plugin_craft_owner and consumed_quest_type == "bod_book_complete":
        _target_amount = _completed_amount
    elif _plugin_craft_owner and consumed_quest_type == "bod_book":
        progress_finished = int_value(dict_value(_plugin_craft_context).get("bod_book_progress_finished"), -1)
        progress_total = int_value(dict_value(_plugin_craft_context).get("bod_book_progress_total"), -1)
        _target_amount = bod_book_batch_target(_completed_amount, _target_amount, progress_finished, progress_total)

    if _completed_amount >= _target_amount:
        finish_runtime()
        return

    set_status("{0} ({1}/{2}); {3}".format(recipe.get("name", "Crafted"), _completed_amount, _target_amount, store_message), GOOD_HUE, "Store Output")
    _dirty_ui = True


def run_manual_server_action(action_key, label):
    module = active_module()
    if not module:
        set_status("No crafting module loaded.", BAD_HUE, "Manual Action")
        return

    action_id = int_value(dict_value(module.get("server_actions")).get(action_key))
    if action_id <= 0:
        set_status(label + " is not mapped in this module.", BAD_HUE, "Manual Action")
        return

    workspace_ready, workspace_error = prepare_craft_workspace()
    if not workspace_ready:
        set_status(workspace_error + ".", BAD_HUE, "Craft Bag Validation")
        return

    stop_runtime("Preparing " + label + ".", WARN_HUE)
    selected_serial = 0
    bag_wide_recycle = False
    if _craft_bag_enabled:
        Target.Cancel()
        prompt = "Target an item directly inside the Craft Bag for " + label
        if action_key == "recycle":
            prompt = "Target an item inside the Craft Bag or the Craft Bag itself for Recycle"
        selected_serial = Target.PromptTarget(prompt)
        bag_wide_recycle = action_key == "recycle" and int_value(selected_serial) == int_value(_craft_bag_serial)
        if bag_wide_recycle:
            valid_selection = craft_bag_item() is not None
        else:
            selected_item = valid_item(selected_serial)
            try:
                valid_selection = selected_item and int(selected_item.Container) == int(_craft_bag_serial)
            except:
                valid_selection = False
        if not valid_selection:
            if action_key == "recycle":
                set_status("Safety stop: Recycle target must be the configured Craft Bag or an item directly inside it.", BAD_HUE, "Manual Action")
            else:
                set_status("Safety stop: " + label + " target must be directly inside the Craft Bag.", BAD_HUE, "Manual Action")
            return

    tool_state, tool_result = ensure_tool(module)

    if tool_state == "error":
        set_status(str(tool_result), BAD_HUE, "Manual Action")
        return
    if tool_state == "progress":
        tool_result = find_tool_in_backpack(dict_value(module.get("tool")))
        if not tool_result:
            set_status("Tool acquisition is still in progress; press " + label + " again.", WARN_HUE, "Manual Action")
            return

    craft_gump_id = int_value(module.get("craft_gump_id"))
    if not open_server_craft_gump(craft_gump_id, tool_result):
        set_status("Crafting gump did not open for " + label + ".", BAD_HUE, "Manual Action")
        return

    if not send_server_actions(craft_gump_id, [action_id], label):
        set_status(label + " action failed.", BAD_HUE, "Manual Action")
        return

    if _craft_bag_enabled:
        if not Target.WaitForTarget(TARGET_CURSOR_WAIT_MS, False):
            set_status(label + " did not provide a target cursor.", BAD_HUE, "Manual Action")
            return
        Target.TargetExecute(selected_serial)
        Misc.Pause(CRAFT_RESULT_PAUSE_MS)
        if bag_wide_recycle:
            set_status("Recycle sent to the Craft Bag; check its contents for leftovers.", GOOD_HUE, "Manual Action")
        else:
            set_status(label + " sent to the selected Craft Bag item.", GOOD_HUE, "Manual Action")
        return

    set_status(label + " ready; complete the target in game.", GOOD_HUE, "Manual Action")


# ===========================================================
# GUI HELPERS
# ===========================================================

def add_button(gd, x, y, button_id, label, hue=LABEL_HUE, art_up=4005, art_down=4007):
    Gumps.AddButton(gd, x, y, art_up, art_down, int(button_id), 1, 0)
    Gumps.AddLabel(gd, x + 24, y, int(hue), str(label))


def source_mode_label():
    return "Shelf + Chest" if _source_mode == SOURCE_SHELF else "Resource Chest"


def automation_source_label():
    if not _craft_bag_enabled:
        return source_mode_label()
    return ("Shelf > Craft Bag" if _source_mode == SOURCE_SHELF else "Chest > Craft Bag")


def ui_snapshot():
    module = active_module()
    recipe = selected_recipe()
    training_skill = 0.0
    if module and (_training_active or _current_view == VIEW_TRAINING):
        training_skill = round(player_skill_value(str(module.get("skill_name", module.get("name", "Skill")))), 1)
    return (
        str(module.get("id", "")) if module else "",
        str(recipe.get("id", "")) if recipe else "",
        _current_view,
        plugin_snapshot(),
        _selected_category_id,
        _category_page,
        _recipe_page,
        _choice_group_index,
        tuple(sorted(_choice_indices.items())),
        _runtime_active,
        _training_active,
        _cleanup_active,
        _cleanup_stage,
        _cleanup_returned,
        _training_crafts,
        training_skill,
        len(_training_pending_outputs),
        len(_training_pending_recovery),
        _target_amount,
        _completed_amount,
        _source_mode,
        _resource_chest_serial,
        _resource_shelf_serial,
        _reagent_shelf_serial,
        _output_chest_serial,
        _tool_book_serial,
        _trash_container_serial,
        _craft_bag_enabled,
        _craft_bag_serial,
        tuple(sorted(_crafting_glasses_serials.items())),
        tuple(sorted(_crafting_template_map.items())),
        _known_active_template,
        _craft_focus,
        _step_name,
        _status_msg,
        _status_hue,
    )


def update_ui_dirty_state():
    global _last_ui_snapshot, _dirty_ui
    snapshot = ui_snapshot()
    if snapshot != _last_ui_snapshot:
        _last_ui_snapshot = snapshot
        _dirty_ui = True


def add_status_panel(gd, y, width=650, step_chars=70, status_chars=74):
    Gumps.AddBackground(gd, 10, y, width, 52, 3000)
    Gumps.AddAlphaRegion(gd, 10, y, width, 52)
    Gumps.AddLabel(gd, 20, y + 6, TITLE_HUE, "STEP:")
    Gumps.AddLabel(gd, 72, y + 6, LABEL_HUE, short_text(_step_name, step_chars))
    Gumps.AddLabel(gd, 20, y + 26, TITLE_HUE, "STATUS:")
    Gumps.AddLabel(gd, 83, y + 26, _status_hue, short_text(_status_msg, status_chars))


def render_home_gui():
    global _dirty_ui, _module_button_map, _training_module_button_map
    global _plugin_button_map, _category_button_map, _recipe_button_map, _render_stage

    module_rows = max(1, (len(_modules) + 1) // 2)
    module_panel_y = 34
    module_panel_height = 44 + module_rows * 24
    plugin_rows = max(1, (len(_plugins) + 2) // 3)
    plugin_panel_y = module_panel_y + module_panel_height + 6
    plugin_panel_height = 35 + plugin_rows * 24
    config_y = plugin_panel_y + plugin_panel_height + 6
    config_height = 210
    status_y = config_y + config_height + 6
    home_height = status_y + 62

    _render_stage = "Create Home shell"
    close_gump(CORE_GUMP_ID)
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)
    Gumps.AddBackground(gd, 0, 0, GUMP_WIDTH, home_height, BG_ID)
    Gumps.AddAlphaRegion(gd, 0, 0, GUMP_WIDTH, home_height)

    Gumps.AddItem(gd, 8, 5, 0x2130, TITLE_HUE)
    Gumps.AddLabel(gd, 42, 8, TITLE_HUE, "FROG CRAFTING CORE " + VERSION)
    Gumps.AddButton(gd, GUMP_WIDTH - 34, 7, 4017, 4018, BTN_CLOSE, 1, 0)

    module = active_module()
    module_name = str(module.get("name", "No Module")) if module else "No Module"
    Gumps.AddLabel(gd, 210, 8, DIM_HUE, "Loaded:")
    Gumps.AddLabel(gd, 267, 8, GOOD_HUE, short_text(module_name, 22))
    add_button(gd, 535, 7, BTN_MODULE_RELOAD, "Reload", WARN_HUE)

    _render_stage = "Home module list"
    Gumps.AddBackground(gd, 10, module_panel_y, 650, module_panel_height, 3000)
    Gumps.AddAlphaRegion(gd, 10, module_panel_y, 650, module_panel_height)
    Gumps.AddLabel(gd, 20, module_panel_y + 6, TITLE_HUE, "CRAFTING SKILLS")
    Gumps.AddLabel(gd, 165, module_panel_y + 6, DIM_HUE, "Open a workbench or choose Train.")

    _module_button_map = {}
    _training_module_button_map = {}
    _plugin_button_map = {}
    _category_button_map = {}
    _recipe_button_map = {}
    active_id = str(module.get("id", "")) if module else ""
    for index, available_module in enumerate(_modules):
        button_id = BTN_MODULE_BASE + index
        module_id = str(available_module.get("id", ""))
        column = index % 2
        row = index // 2
        x = 20 + column * 320
        y = module_panel_y + 30 + row * 24
        _module_button_map[button_id] = module_id
        hue = GOOD_HUE if module_id == active_id else LABEL_HUE
        label = short_text(available_module.get("name", "Unknown Craft"), 19)
        add_button(gd, x, y, button_id, label, hue)
        if training_profile(available_module):
            training_button_id = BTN_TRAINING_MODULE_BASE + index
            _training_module_button_map[training_button_id] = module_id
            training_hue = GOOD_HUE if module_id == active_id and _training_active else WARN_HUE
            add_button(gd, x + 210, y, training_button_id, "Train", training_hue)

    _render_stage = "Home plugin list"
    Gumps.AddBackground(gd, 10, plugin_panel_y, 650, plugin_panel_height, 3000)
    Gumps.AddAlphaRegion(gd, 10, plugin_panel_y, 650, plugin_panel_height)
    Gumps.AddLabel(gd, 20, plugin_panel_y + 6, TITLE_HUE, "CRAFTING PLUGINS")
    if _plugins:
        for index, plugin in enumerate(_plugins):
            button_id = BTN_PLUGIN_BASE + index
            column = index % 3
            row = index // 3
            x = 20 + column * 210
            y = plugin_panel_y + 29 + row * 24
            _plugin_button_map[button_id] = clean_key(plugin.plugin_id)
            add_button(gd, x, y, button_id, short_text(plugin.home_label, 20), GOOD_HUE)
    else:
        Gumps.AddLabel(gd, 170, plugin_panel_y + 7, WARN_HUE, "No optional crafting plugins loaded.")

    _render_stage = "Home configuration"
    Gumps.AddBackground(gd, 10, config_y, 650, config_height, 3000)
    Gumps.AddAlphaRegion(gd, 10, config_y, 650, config_height)
    Gumps.AddLabel(gd, 20, config_y + 6, TITLE_HUE, "SETUP & STORAGE")
    add_button(gd, 20, config_y + 29, BTN_SOURCE_TOGGLE, "Source: " + source_mode_label(), GOOD_HUE)
    craft_bag_hue = GOOD_HUE if _craft_bag_enabled else DIM_HUE
    add_button(gd, 340, config_y + 29, BTN_CRAFT_BAG_TOGGLE, "Craft Bag: " + ("ON" if _craft_bag_enabled else "OFF"), craft_bag_hue)

    add_button(gd, 20, config_y + 55, BTN_SET_RESOURCE_CHEST, "Set Chest")
    Gumps.AddLabel(gd, 140, config_y + 56, LABEL_HUE, short_text(item_label(_resource_chest_serial, "Chest not set"), 25))
    add_button(gd, 20, config_y + 81, BTN_SET_RESOURCE_SHELF, "Set Shelf")
    Gumps.AddLabel(gd, 140, config_y + 82, LABEL_HUE, short_text(item_label(_resource_shelf_serial, "Shelf not set"), 25))
    add_button(gd, 20, config_y + 107, BTN_SET_REAGENT_SHELF, "Set Reagent Shelf")
    Gumps.AddLabel(gd, 170, config_y + 108, LABEL_HUE, short_text(item_label(_reagent_shelf_serial, "Reagent shelf not set"), 20))
    add_button(gd, 20, config_y + 133, BTN_SET_CRAFT_BAG, "Set Craft Bag")
    Gumps.AddLabel(gd, 160, config_y + 134, LABEL_HUE, short_text(item_label(_craft_bag_serial, "Craft bag not set"), 22))

    add_button(gd, 340, config_y + 55, BTN_SET_OUTPUT_CHEST, "Set Output")
    Gumps.AddLabel(gd, 464, config_y + 56, LABEL_HUE, short_text(item_label(_output_chest_serial, "Backpack output"), 23))
    add_button(gd, 340, config_y + 81, BTN_SET_TOOL_BOOK, "Set Tool Book")
    Gumps.AddLabel(gd, 464, config_y + 82, LABEL_HUE, short_text(item_label(_tool_book_serial, "Tool book not set"), 23))
    add_button(gd, 340, config_y + 107, BTN_SET_TRASH_CONTAINER, "Set Trash")
    Gumps.AddLabel(gd, 464, config_y + 108, LABEL_HUE, short_text(item_label(_trash_container_serial, "Trash not set"), 23))
    configured_glasses = len([serial for serial in _crafting_glasses_serials.values() if int_value(serial) > 0])
    add_button(gd, 340, config_y + 133, BTN_GLASSES_SETUP, "Crafting Glasses", GOOD_HUE if configured_glasses else WARN_HUE)
    Gumps.AddLabel(gd, 512, config_y + 134, DIM_HUE, "{0}/{1} set".format(configured_glasses, len(CRAFTING_GLASSES_PROFILES)))
    configured_templates = len([value for value in _crafting_template_map.values() if int_value(value) > 0])
    add_button(gd, 340, config_y + 159, BTN_TEMPLATES_SETUP, "Craft Templates", GOOD_HUE if configured_templates else WARN_HUE)
    Gumps.AddLabel(gd, 512, config_y + 160, DIM_HUE, "{0}/{1} set".format(configured_templates, len(CRAFT_SKILL_PROFILES)))

    Gumps.AddLabel(gd, 20, config_y + 160, TITLE_HUE, "Craft Focus:")
    Gumps.AddButton(gd, 125, config_y + 159, 4014, 4016, BTN_FOCUS_PREV, 1, 0)
    Gumps.AddLabel(gd, 154, config_y + 160, GOOD_HUE, FOCUS_LABELS.get(_craft_focus, "As-is"))
    Gumps.AddButton(gd, 300, config_y + 159, 4005, 4007, BTN_FOCUS_NEXT, 1, 0)
    Gumps.AddLabel(gd, 20, config_y + 187, DIM_HUE, "Shelf users: set and lock withdrawal values to 100, including used reagent/gem entries.")

    _render_stage = "Home status panel"
    add_status_panel(gd, status_y)

    _render_stage = "Send Home gump"
    Gumps.SendGump(CORE_GUMP_ID, Player.Serial, GUMP_X, GUMP_Y, gd.gumpDefinition, gd.gumpStrings)
    _render_stage = "Complete"
    _dirty_ui = False


def render_glasses_gui():
    global _dirty_ui, _glasses_set_button_map, _glasses_clear_button_map, _render_stage

    _render_stage = "Create Crafting Glasses shell"
    close_gump(CORE_GUMP_ID)
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)
    Gumps.AddBackground(gd, 0, 0, GUMP_WIDTH, GLASSES_GUMP_HEIGHT, BG_ID)
    Gumps.AddAlphaRegion(gd, 0, 0, GUMP_WIDTH, GLASSES_GUMP_HEIGHT)

    Gumps.AddItem(gd, 8, 5, 0x2130, TITLE_HUE)
    Gumps.AddLabel(gd, 42, 8, TITLE_HUE, "FROG CRAFTING CORE " + VERSION)
    Gumps.AddLabel(gd, 210, 8, GOOD_HUE, "Crafting Glasses")
    add_button(gd, 535, 7, BTN_GLASSES_BACK, "Setup", GOOD_HUE)
    Gumps.AddButton(gd, GUMP_WIDTH - 34, 7, 4017, 4018, BTN_CLOSE, 1, 0)

    _render_stage = "Crafting Glasses list"
    Gumps.AddBackground(gd, 10, 34, 650, 238, 3000)
    Gumps.AddAlphaRegion(gd, 10, 34, 650, 238)
    Gumps.AddLabel(gd, 20, 41, TITLE_HUE, "ARTIFICER GLASSES")
    Gumps.AddLabel(gd, 175, 41, DIM_HUE, "Click a skill, then target its glasses. Item identity is checked; skill text is optional.")

    _glasses_set_button_map = {}
    _glasses_clear_button_map = {}
    for index, profile in enumerate(CRAFTING_GLASSES_PROFILES):
        column = 0 if index < 5 else 1
        row = index if index < 5 else index - 5
        x = 20 + column * 320
        y = 72 + row * 36
        set_button = BTN_GLASSES_SET_BASE + index
        clear_button = BTN_GLASSES_CLEAR_BASE + index
        profile_id = str(profile.get("id", ""))
        _glasses_set_button_map[set_button] = profile_id
        _glasses_clear_button_map[clear_button] = profile_id
        add_button(gd, x, y, set_button, short_text(profile.get("label", "Crafting"), 17), LABEL_HUE)
        status_text, status_hue = crafting_glasses_status(profile)
        Gumps.AddLabel(gd, x + 28, y + 17, status_hue, short_text(status_text, 34))
        if configured_crafting_glasses_serial(profile) > 0:
            add_button(gd, x + 240, y, clear_button, "Clear", WARN_HUE)

    Gumps.AddLabel(gd, 20, 280, DIM_HUE, "FCC equips the configured pair before that skill crafts and keeps it equipped across batches.")
    add_status_panel(gd, 298)

    _render_stage = "Send Crafting Glasses gump"
    Gumps.SendGump(CORE_GUMP_ID, Player.Serial, GUMP_X, GUMP_Y, gd.gumpDefinition, gd.gumpStrings)
    _render_stage = "Complete"
    _dirty_ui = False


def render_templates_gui():
    global _dirty_ui, _template_minus_button_map, _template_plus_button_map, _render_stage

    _render_stage = "Create Crafting Templates shell"
    close_gump(CORE_GUMP_ID)
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)
    Gumps.AddBackground(gd, 0, 0, GUMP_WIDTH, GLASSES_GUMP_HEIGHT, BG_ID)
    Gumps.AddAlphaRegion(gd, 0, 0, GUMP_WIDTH, GLASSES_GUMP_HEIGHT)

    Gumps.AddItem(gd, 8, 5, 0x2130, TITLE_HUE)
    Gumps.AddLabel(gd, 42, 8, TITLE_HUE, "FROG CRAFTING CORE " + VERSION)
    Gumps.AddLabel(gd, 210, 8, GOOD_HUE, "Craft Templates")
    add_button(gd, 535, 7, BTN_TEMPLATES_BACK, "Setup", GOOD_HUE)
    Gumps.AddButton(gd, GUMP_WIDTH - 34, 7, 4017, 4018, BTN_CLOSE, 1, 0)

    _render_stage = "Crafting Templates list"
    Gumps.AddBackground(gd, 10, 34, 650, 238, 3000)
    Gumps.AddAlphaRegion(gd, 10, 34, 650, 238)
    Gumps.AddLabel(gd, 20, 41, TITLE_HUE, "SKILL TEMPLATE MAP")
    active_text = "Template {0}".format(_known_active_template) if _known_active_template > 0 else "Unknown"
    Gumps.AddLabel(gd, 190, 41, DIM_HUE, "Active this session:")
    Gumps.AddLabel(gd, 330, 41, GOOD_HUE if _known_active_template > 0 else WARN_HUE, active_text)
    add_button(gd, 485, 40, BTN_TEMPLATE_FORGET_ACTIVE, "Forget Active", WARN_HUE)
    Gumps.AddLabel(gd, 20, 61, DIM_HUE, "Use -/+ to assign each skill. Unassigned skills never trigger [template.")

    _template_minus_button_map = {}
    _template_plus_button_map = {}
    for index, profile in enumerate(CRAFT_SKILL_PROFILES):
        column = 0 if index < 5 else 1
        row = index if index < 5 else index - 5
        x = 20 + column * 320
        y = 84 + row * 34
        minus_button = BTN_TEMPLATE_MINUS_BASE + index
        plus_button = BTN_TEMPLATE_PLUS_BASE + index
        profile_id = str(profile.get("id", ""))
        _template_minus_button_map[minus_button] = profile_id
        _template_plus_button_map[plus_button] = profile_id
        Gumps.AddLabel(gd, x, y + 1, LABEL_HUE, short_text(profile.get("label", "Crafting"), 18))
        Gumps.AddButton(gd, x + 145, y, 4014, 4016, minus_button, 1, 0)
        template_id = configured_crafting_template(profile)
        template_text = "Template {0}".format(template_id) if template_id > 0 else "Unassigned"
        Gumps.AddLabel(gd, x + 176, y + 1, GOOD_HUE if template_id > 0 else DIM_HUE, template_text)
        Gumps.AddButton(gd, x + 282, y, 4005, 4007, plus_button, 1, 0)

    Gumps.AddLabel(gd, 20, 280, DIM_HUE, "Startup is Unknown; the first mapped craft synchronizes once, then same-template skills do not swap.")
    add_status_panel(gd, 298)

    _render_stage = "Send Crafting Templates gump"
    Gumps.SendGump(CORE_GUMP_ID, Player.Serial, GUMP_X, GUMP_Y, gd.gumpDefinition, gd.gumpStrings)
    _render_stage = "Complete"
    _dirty_ui = False


def render_crafting_gui():
    global _dirty_ui, _module_button_map, _training_module_button_map
    global _category_button_map, _recipe_button_map, _render_stage

    _render_stage = "Create shell"
    close_gump(CORE_GUMP_ID)
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)
    Gumps.AddBackground(gd, 0, 0, GUMP_WIDTH, CRAFT_GUMP_HEIGHT, BG_ID)
    Gumps.AddAlphaRegion(gd, 0, 0, GUMP_WIDTH, CRAFT_GUMP_HEIGHT)

    Gumps.AddItem(gd, 8, 5, 0x2130, TITLE_HUE)
    Gumps.AddLabel(gd, 42, 8, TITLE_HUE, "FROG CRAFTING CORE " + VERSION)
    Gumps.AddButton(gd, GUMP_WIDTH - 34, 7, 4017, 4018, BTN_CLOSE, 1, 0)

    _render_stage = "Module header"
    _module_button_map = {}
    _training_module_button_map = {}
    module = active_module()
    module_name = str(module.get("name", "No Module")) if module else "No Module"
    Gumps.AddLabel(gd, 210, 8, DIM_HUE, "Module:")
    Gumps.AddLabel(gd, 267, 8, GOOD_HUE, short_text(module_name, 20))
    add_button(gd, 430, 7, BTN_HOME, "Home / Setup", GOOD_HUE)
    add_button(gd, 535, 7, BTN_MODULE_RELOAD, "Reload", WARN_HUE)

    Gumps.AddBackground(gd, 10, 34, 205, 226, 3000)
    Gumps.AddAlphaRegion(gd, 10, 34, 205, 226)
    Gumps.AddLabel(gd, 24, 40, TITLE_HUE, "CATEGORIES")

    Gumps.AddBackground(gd, 220, 34, 440, 226, 3000)
    Gumps.AddAlphaRegion(gd, 220, 34, 440, 226)
    Gumps.AddLabel(gd, 236, 40, TITLE_HUE, "SELECTIONS")

    _render_stage = "Category list"
    _category_button_map = {}
    categories = module_categories()
    category_page_count = max(1, (len(categories) + CATEGORY_ROWS - 1) // CATEGORY_ROWS)
    start_category = _category_page * CATEGORY_ROWS
    visible_categories = categories[start_category:start_category + CATEGORY_ROWS]

    for row, category in enumerate(visible_categories):
        button_id = BTN_CATEGORY_BASE + row
        _category_button_map[button_id] = str(category.get("id", ""))
        selected = str(category.get("id", "")) == _selected_category_id
        mapped = bool(list_value(category.get("open_actions")))
        hue = GOOD_HUE if selected else (LABEL_HUE if mapped else WARN_HUE)
        add_button(gd, 22, 65 + row * 19, button_id, short_text(category.get("name", "Category"), 20), hue)

    Gumps.AddButton(gd, 24, 236, 4014, 4016, BTN_CATEGORY_PREV, 1, 0)
    Gumps.AddLabel(gd, 81, 237, DIM_HUE, "{0}/{1}".format(_category_page + 1, category_page_count))
    Gumps.AddButton(gd, 177, 236, 4005, 4007, BTN_CATEGORY_NEXT, 1, 0)

    _render_stage = "Recipe list"
    _recipe_button_map = {}
    recipes = category_recipes()
    recipe_page_count = max(1, (len(recipes) + RECIPE_ROWS - 1) // RECIPE_ROWS)
    start_recipe = _recipe_page * RECIPE_ROWS
    visible_recipes = recipes[start_recipe:start_recipe + RECIPE_ROWS]

    for row, recipe in enumerate(visible_recipes):
        button_id = BTN_RECIPE_BASE + row
        _recipe_button_map[button_id] = str(recipe.get("id", ""))
        selected = str(recipe.get("id", "")) == _selected_recipe_id
        ready, _reason = recipe_readiness(recipe)
        hue = GOOD_HUE if selected else (LABEL_HUE if ready else WARN_HUE)
        add_button(gd, 234, 65 + row * 17, button_id, short_text(recipe.get("name", "Recipe"), 35), hue)

    Gumps.AddButton(gd, 235, 236, 4014, 4016, BTN_RECIPE_PREV, 1, 0)
    Gumps.AddLabel(gd, 425, 237, DIM_HUE, "{0}/{1}".format(_recipe_page + 1, recipe_page_count))
    Gumps.AddButton(gd, 625, 236, 4005, 4007, BTN_RECIPE_NEXT, 1, 0)

    _render_stage = "Recipe details"
    recipe = selected_recipe()
    Gumps.AddBackground(gd, 10, 266, 650, 58, 3000)
    Gumps.AddAlphaRegion(gd, 10, 266, 650, 58)
    Gumps.AddLabel(gd, 20, 272, TITLE_HUE, "RECIPE")
    Gumps.AddLabel(gd, 88, 272, LABEL_HUE, recipe_skill_summary(recipe))
    Gumps.AddLabel(gd, 20, 291, LABEL_HUE, "Cost: " + short_text(recipe_resource_summary(recipe), 76))
    ready, reason = recipe_readiness(recipe)
    Gumps.AddLabel(gd, 20, 308, GOOD_HUE if ready else WARN_HUE, "Automation: " + short_text(reason, 69))

    _render_stage = "Crafting options"
    Gumps.AddBackground(gd, 10, 330, 650, 108, 3000)
    Gumps.AddAlphaRegion(gd, 10, 330, 650, 108)
    Gumps.AddLabel(gd, 20, 336, TITLE_HUE, "CRAFTING OPTIONS")
    Gumps.AddLabel(gd, 335, 336, LABEL_HUE, "Focus:")
    Gumps.AddButton(gd, 385, 335, 4014, 4016, BTN_FOCUS_PREV, 1, 0)
    Gumps.AddLabel(gd, 415, 336, GOOD_HUE, FOCUS_LABELS.get(_craft_focus, "As-is"))
    Gumps.AddButton(gd, 625, 335, 4005, 4007, BTN_FOCUS_NEXT, 1, 0)

    Gumps.AddLabel(gd, 20, 359, TITLE_HUE, "Amount:")
    Gumps.AddButton(gd, 78, 358, 4014, 4016, BTN_AMOUNT_MINUS_100, 1, 0)
    Gumps.AddLabel(gd, 104, 359, DIM_HUE, "-100")
    Gumps.AddButton(gd, 139, 358, 4014, 4016, BTN_AMOUNT_MINUS_10, 1, 0)
    Gumps.AddLabel(gd, 165, 359, DIM_HUE, "-10")
    Gumps.AddButton(gd, 192, 358, 4014, 4016, BTN_AMOUNT_MINUS_1, 1, 0)
    Gumps.AddLabel(gd, 218, 359, DIM_HUE, "-1")
    Gumps.AddLabel(gd, 249, 359, GOOD_HUE, str(_target_amount))
    Gumps.AddButton(gd, 286, 358, 4005, 4007, BTN_AMOUNT_PLUS_1, 1, 0)
    Gumps.AddLabel(gd, 312, 359, DIM_HUE, "+1")
    Gumps.AddButton(gd, 336, 358, 4005, 4007, BTN_AMOUNT_PLUS_10, 1, 0)
    Gumps.AddLabel(gd, 362, 359, DIM_HUE, "+10")
    Gumps.AddButton(gd, 390, 358, 4005, 4007, BTN_AMOUNT_PLUS_100, 1, 0)
    Gumps.AddLabel(gd, 416, 359, DIM_HUE, "+100")

    Gumps.AddButton(gd, 466, 358, 4005, 4007, BTN_CHOICE_GROUP_NEXT, 1, 0)
    Gumps.AddButton(gd, 495, 358, 4014, 4016, BTN_CHOICE_PREV, 1, 0)
    Gumps.AddLabel(gd, 524, 359, LABEL_HUE, short_text(selected_choice_label(), 13))
    Gumps.AddButton(gd, 628, 358, 4005, 4007, BTN_CHOICE_NEXT, 1, 0)

    run_label = "Cleaning..." if _cleanup_active else ("Pause" if _runtime_active else "Start")
    run_hue = WARN_HUE if (_runtime_active or _cleanup_active) else GOOD_HUE
    add_button(gd, 20, 385, BTN_TOGGLE_RUN, run_label, run_hue, 4011, 4013)
    add_button(gd, 125, 385, BTN_CANCEL, "Cancel Job", BAD_HUE, 4017, 4019)
    Gumps.AddLabel(gd, 270, 386, LABEL_HUE, "Completed: {0}/{1}".format(_completed_amount, _target_amount))
    Gumps.AddLabel(gd, 470, 386, DIM_HUE, "Using: " + automation_source_label())

    actions = dict_value(module.get("server_actions")) if module else {}
    if int_value(actions.get("smelt_item")) > 0:
        add_button(gd, 20, 412, BTN_ACTION_SMELT, "Smelt")
    if int_value(actions.get("repair_item")) > 0:
        add_button(gd, 125, 412, BTN_ACTION_REPAIR, "Repair")
    if int_value(actions.get("mark_item")) > 0:
        add_button(gd, 230, 412, BTN_ACTION_MARK, "Mark")
    if int_value(actions.get("salvage")) > 0:
        add_button(gd, 335, 412, BTN_ACTION_SALVAGE, "Salvage")
    if int_value(actions.get("recycle")) > 0:
        add_button(gd, 455, 412, BTN_ACTION_RECYCLE, "Recycle")

    _render_stage = "Status panel"
    add_status_panel(gd, 444)

    _render_stage = "Send gump"
    Gumps.SendGump(CORE_GUMP_ID, Player.Serial, GUMP_X, GUMP_Y, gd.gumpDefinition, gd.gumpStrings)
    _render_stage = "Complete"
    _dirty_ui = False


def render_training_gui():
    global _dirty_ui, _module_button_map, _training_module_button_map
    global _category_button_map, _recipe_button_map, _render_stage

    _render_stage = "Create Training shell"
    close_gump(CORE_GUMP_ID)
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)
    Gumps.AddBackground(gd, 0, 0, TRAIN_GUMP_WIDTH, TRAIN_GUMP_HEIGHT, BG_ID)
    Gumps.AddAlphaRegion(gd, 0, 0, TRAIN_GUMP_WIDTH, TRAIN_GUMP_HEIGHT)

    Gumps.AddItem(gd, 8, 5, 0x2130, TITLE_HUE)
    Gumps.AddLabel(gd, 42, 8, TITLE_HUE, "FROG CRAFTING CORE " + VERSION)
    add_button(gd, 420, 7, BTN_HOME, "Home", GOOD_HUE)
    Gumps.AddButton(gd, TRAIN_GUMP_WIDTH - 34, 7, 4017, 4018, BTN_CLOSE, 1, 0)

    _module_button_map = {}
    _training_module_button_map = {}
    _category_button_map = {}
    _recipe_button_map = {}

    module, profile, skill_value, skill_cap, goal, stage, _category, recipe, reason = training_context()
    module_name = str(module.get("name", "Unknown")) if module else "Unknown"
    skill_name = str(module.get("skill_name", module_name)) if module else "Skill"
    informational = bool(dict_value(profile).get("informational", False))
    if informational:
        stage_range = "Guide only"
        stage_label = reason
        output_label = "No automated craft cycle"
    elif stage:
        stage_range = "{0:.1f} - {1:.1f}".format(number_value(stage.get("min_skill"), 0.0), number_value(stage.get("max_skill"), goal))
        stage_label = str(stage.get("label", "Training stage"))
        output_label = training_disposal_label(stage)
    else:
        stage_range = "Complete" if skill_value >= goal else "Needs mapping"
        stage_label = reason
        output_label = "--"
    recipe_name = str(recipe.get("name", stage_label)) if recipe else stage_label
    gain = max(0.0, skill_value - _training_start_skill) if _training_session_module_id == str(dict_value(module).get("id", "")) else 0.0

    _render_stage = "Training details"
    Gumps.AddBackground(gd, 10, 34, 540, 118, 3000)
    Gumps.AddAlphaRegion(gd, 10, 34, 540, 118)
    Gumps.AddLabel(gd, 20, 41, TITLE_HUE, "TRAINING " + module_name.upper())
    Gumps.AddLabel(gd, 20, 64, LABEL_HUE, "{0}: {1:.1f} / cap {2:.1f} / goal {3:.1f}".format(skill_name, skill_value, skill_cap, goal))
    if informational:
        message_lines = wrapped_text_lines(reason, 52, 2)
        Gumps.AddLabel(gd, 20, 85, GOOD_HUE, "Guide: " + message_lines[0])
        if len(message_lines) > 1:
            Gumps.AddLabel(gd, 20, 106, GOOD_HUE, message_lines[1])
        Gumps.AddLabel(gd, 20, 128, DIM_HUE, "Information only - no automated craft cycle")
    else:
        Gumps.AddLabel(gd, 20, 85, LABEL_HUE, "Stage: " + stage_range)
        Gumps.AddLabel(gd, 185, 85, GOOD_HUE if recipe else WARN_HUE, "Crafting: " + short_text(recipe_name, 37))
        Gumps.AddLabel(gd, 20, 106, LABEL_HUE, "Output: " + short_text(output_label, 58))
        pending_text = " | recovery pending" if _training_pending_recovery else (" | output pending" if _training_pending_outputs else "")
        Gumps.AddLabel(gd, 20, 128, DIM_HUE, "Crafts this run: {0} | Skill gained: +{1:.1f}{2}".format(_training_crafts, gain, pending_text))

    _render_stage = "Training controls"
    Gumps.AddBackground(gd, 10, 158, 540, 36, 3000)
    Gumps.AddAlphaRegion(gd, 10, 158, 540, 36)
    run_label = "Show Message" if informational else ("Cleaning..." if _cleanup_active else ("Pause" if _training_active else "Start Training"))
    run_hue = WARN_HUE if (_training_active or _cleanup_active) else GOOD_HUE
    add_button(gd, 20, 165, BTN_TRAIN_TOGGLE, run_label, run_hue, 4011, 4013)
    add_button(gd, 190, 165, BTN_TRAIN_WORKBENCH, "Workbench", LABEL_HUE)
    Gumps.AddLabel(gd, 365, 166, DIM_HUE, "Glasses OFF | " + short_text(automation_source_label(), 18))

    _render_stage = "Training status panel"
    add_status_panel(gd, 200, 540, 56, 59)

    _render_stage = "Send Training gump"
    Gumps.SendGump(CORE_GUMP_ID, Player.Serial, GUMP_X, GUMP_Y, gd.gumpDefinition, gd.gumpStrings)
    _render_stage = "Complete"
    _dirty_ui = False


def render_plugin_gui():
    global _dirty_ui, _module_button_map, _training_module_button_map
    global _plugin_button_map, _category_button_map, _recipe_button_map, _render_stage

    plugin = active_plugin()
    if not plugin:
        raise Exception("active crafting plugin is unavailable")

    _render_stage = "Create Plugin shell"
    close_gump(CORE_GUMP_ID)
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)
    Gumps.AddBackground(gd, 0, 0, GUMP_WIDTH, PLUGIN_GUMP_HEIGHT, BG_ID)
    Gumps.AddAlphaRegion(gd, 0, 0, GUMP_WIDTH, PLUGIN_GUMP_HEIGHT)

    Gumps.AddItem(gd, 8, 5, 0x2130, TITLE_HUE)
    Gumps.AddLabel(gd, 42, 8, TITLE_HUE, "FROG CRAFTING CORE " + VERSION)
    Gumps.AddLabel(gd, 210, 8, DIM_HUE, "Plugin:")
    Gumps.AddLabel(gd, 267, 8, GOOD_HUE, short_text(plugin.name, 18))
    add_button(gd, 430, 7, BTN_HOME, "Home / Setup", GOOD_HUE)
    add_button(gd, 535, 7, BTN_MODULE_RELOAD, "Reload", WARN_HUE)
    Gumps.AddButton(gd, GUMP_WIDTH - 34, 7, 4017, 4018, BTN_CLOSE, 1, 0)

    _module_button_map = {}
    _training_module_button_map = {}
    _plugin_button_map = {}
    _category_button_map = {}
    _recipe_button_map = {}

    _render_stage = "Render " + str(plugin.name)
    plugin.render(gd, 10, 34, 650, 318)

    _render_stage = "Plugin status panel"
    add_status_panel(gd, 358)

    _render_stage = "Send Plugin gump"
    Gumps.SendGump(CORE_GUMP_ID, Player.Serial, GUMP_X, GUMP_Y, gd.gumpDefinition, gd.gumpStrings)
    _render_stage = "Complete"
    _dirty_ui = False


def render_gui():
    if _current_view == VIEW_HOME:
        render_home_gui()
    elif _current_view == VIEW_GLASSES:
        render_glasses_gui()
    elif _current_view == VIEW_TEMPLATES:
        render_templates_gui()
    elif _current_view == VIEW_TRAINING:
        render_training_gui()
    elif _current_view == VIEW_PLUGIN:
        render_plugin_gui()
    else:
        render_crafting_gui()


def render_error_gui(error_message):
    global _dirty_ui

    close_gump(CORE_GUMP_ID)
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)
    Gumps.AddBackground(gd, 0, 0, 520, 150, BG_ID)
    Gumps.AddAlphaRegion(gd, 0, 0, 520, 150)
    Gumps.AddItem(gd, 8, 5, 0x2130, TITLE_HUE)
    Gumps.AddLabel(gd, 42, 8, TITLE_HUE, "FROG CRAFTING CORE " + VERSION)
    Gumps.AddButton(gd, 486, 7, 4017, 4018, BTN_CLOSE, 1, 0)
    Gumps.AddLabel(gd, 18, 42, BAD_HUE, "The full interface could not be rendered.")
    Gumps.AddLabel(gd, 18, 65, WARN_HUE, "Stage: " + short_text(_render_stage, 55))
    Gumps.AddLabel(gd, 18, 86, LABEL_HUE, short_text(error_message, 68))
    add_button(gd, 18, 114, BTN_MODULE_RELOAD, "Reload data and retry", GOOD_HUE)
    Gumps.SendGump(CORE_GUMP_ID, Player.Serial, GUMP_X, GUMP_Y, gd.gumpDefinition, gd.gumpStrings)
    _dirty_ui = False


def render_gui_safe():
    try:
        render_gui()
        return True
    except Exception as ex:
        message = "GUI error in {0}: {1}".format(_render_stage, ex)
        set_status(message, BAD_HUE, "Render Error")
        Misc.SendMessage("Frog Crafting " + message, BAD_HUE)
        try:
            render_error_gui(str(ex))
        except Exception as fallback_ex:
            Misc.SendMessage("Frog Crafting fallback GUI error: " + str(fallback_ex), BAD_HUE)
        return False


# ===========================================================
# BUTTON HANDLING
# ===========================================================

def priority_control_button(button_id):
    if button_id in (BTN_CLOSE, BTN_CANCEL):
        return True
    if button_id == BTN_TOGGLE_RUN and _runtime_active:
        return True
    if button_id == BTN_TRAIN_TOGGLE and _training_active:
        return True
    plugin = active_plugin()
    if _current_view == VIEW_PLUGIN and plugin and bool(getattr(plugin, "running", False)):
        if button_id == BTN_HOME:
            return True
        try:
            local_button = int(button_id) - int(plugin.button_base)
            checker = getattr(plugin, "is_priority_button", None)
            if callable(checker) and bool(checker(local_button)):
                return True
        except:
            pass
    return False


def consume_custom_gump_button(priority_only=False, stop_toggle_controls=False):
    global _operation_interrupted

    try:
        gd = Gumps.GetGumpData(CORE_GUMP_ID)
        button_id = int_value(getattr(gd, "buttonid", 0), 0) if gd else 0
    except:
        return False

    if button_id <= 0:
        return False
    if priority_only and not priority_control_button(button_id):
        return False

    priority_response = priority_control_button(button_id)
    if stop_toggle_controls and button_id in (BTN_TOGGLE_RUN, BTN_TRAIN_TOGGLE):
        priority_response = True

    try:
        gd.buttonid = 0
    except:
        pass

    close_gump(CORE_GUMP_ID)
    if priority_response:
        _operation_interrupted = True
    if stop_toggle_controls and button_id == BTN_TOGGLE_RUN:
        stop_runtime("Paused by player.", WARN_HUE)
    elif stop_toggle_controls and button_id == BTN_TRAIN_TOGGLE:
        stop_runtime("Training paused by player.", WARN_HUE)
    else:
        handle_button(button_id)

    if priority_response:
        try:
            Target.Cancel()
        except:
            pass
        close_tool_book_gump()
        close_gump(TEMPLATE_CONFIRM_GUMP_ID)
        module = active_module()
        if module:
            close_gump(int_value(module.get("craft_gump_id")))
        close_gump(int_value(_shelf_data.get("gump_id"), 0x06ABCE12))
        close_gump(int_value(_reagent_shelf_data.get("gump_id"), 0xA8ED56C7))

    Misc.Pause(BUTTON_DEBOUNCE_MS)
    return True


def consume_priority_control_button():
    if not (_runtime_active or _training_active or _cleanup_active):
        return False
    return consume_custom_gump_button(True)


def handle_button(button_id):
    global _running, _runtime_active, _training_active, _dirty_ui
    global _target_amount, _source_mode, _craft_bag_enabled
    global _category_page, _recipe_page, _current_view
    global _craft_focus

    if button_id == BTN_CLOSE:
        _runtime_active = False
        _training_active = False
        reset_material_cleanup(False)
        _running = False
        return

    if button_id == BTN_TOGGLE_RUN:
        if _cleanup_active:
            set_status("Material cleanup is still running; use Cancel Job to stop it.", WARN_HUE, "Cleanup Materials")
            return
        if _runtime_active:
            stop_runtime("Paused by player.", WARN_HUE)
        else:
            start_runtime()
        return

    if button_id == BTN_CANCEL:
        stop_runtime("Job cancelled at {0}/{1}.".format(_completed_amount, _target_amount), WARN_HUE)
        return

    if button_id == BTN_HOME:
        plugin = active_plugin()
        if _current_view == VIEW_PLUGIN and plugin:
            try:
                plugin.deactivate("Returned to Home / Setup.")
            except:
                pass
        _current_view = VIEW_HOME
        _dirty_ui = True
        return

    if button_id == BTN_GLASSES_SETUP:
        if _runtime_active or _training_active:
            set_status("Pause active crafting before changing Artificer Glasses.", WARN_HUE, "Glasses Setup")
            return
        _current_view = VIEW_GLASSES
        set_status("Select a skill, then target its Artificer Glasses.", GOOD_HUE, "Glasses Setup")
        _dirty_ui = True
        return

    if button_id == BTN_GLASSES_BACK:
        _current_view = VIEW_HOME
        _dirty_ui = True
        return

    if button_id == BTN_TEMPLATES_SETUP:
        if _runtime_active or _training_active:
            set_status("Pause active crafting before changing template assignments.", WARN_HUE, "Template Setup")
            return
        _current_view = VIEW_TEMPLATES
        set_status("Assign each craft skill to its server template number.", GOOD_HUE, "Template Setup")
        _dirty_ui = True
        return

    if button_id == BTN_TEMPLATES_BACK:
        _current_view = VIEW_HOME
        _dirty_ui = True
        return

    if button_id == BTN_TRAIN_TOGGLE:
        if _cleanup_active:
            set_status("Material cleanup is still running; use Cancel Job to stop it.", WARN_HUE, "Cleanup Materials")
            return
        if _training_active:
            stop_runtime("Training paused by player.", WARN_HUE)
        else:
            start_training()
        return

    if _cleanup_active:
        plugin = active_plugin()
        if _current_view == VIEW_PLUGIN and plugin and bool(getattr(plugin, "running", False)):
            try:
                local_button = int(button_id) - int(plugin.button_base)
                checker = getattr(plugin, "is_priority_button", None)
                if callable(checker) and bool(checker(local_button)):
                    plugin.handle_button(local_button)
                    _dirty_ui = True
                    return
            except:
                pass
        set_status("Wait for material cleanup to finish before changing the setup.", WARN_HUE, "Cleanup Materials")
        return

    if _current_view == VIEW_GLASSES and button_id in _glasses_set_button_map:
        if _runtime_active or _training_active:
            set_status("Pause active crafting before changing Artificer Glasses.", WARN_HUE, "Glasses Setup")
            return
        target_crafting_glasses(_glasses_set_button_map[button_id])
        return

    if _current_view == VIEW_GLASSES and button_id in _glasses_clear_button_map:
        if _runtime_active or _training_active:
            set_status("Pause active crafting before changing Artificer Glasses.", WARN_HUE, "Glasses Setup")
            return
        clear_crafting_glasses(_glasses_clear_button_map[button_id])
        return

    if _current_view == VIEW_TEMPLATES and button_id == BTN_TEMPLATE_FORGET_ACTIVE:
        forget_active_template()
        return

    if _current_view == VIEW_TEMPLATES and button_id in _template_minus_button_map:
        change_crafting_template(_template_minus_button_map[button_id], -1)
        return

    if _current_view == VIEW_TEMPLATES and button_id in _template_plus_button_map:
        change_crafting_template(_template_plus_button_map[button_id], 1)
        return

    if button_id == BTN_TRAIN_WORKBENCH:
        module = active_module()
        if module:
            open_module_view(module.get("id", ""))
        return

    if button_id == BTN_MODULE_PREV:
        switch_module(-1)
        return
    if button_id == BTN_MODULE_NEXT:
        switch_module(1)
        return
    if button_id == BTN_MODULE_RELOAD:
        stop_runtime("Reloading module data.", WARN_HUE)
        load_modules()
        load_plugins()
        if _current_view == VIEW_PLUGIN and active_plugin():
            active_plugin().activate()
        _dirty_ui = True
        return

    if button_id in (BTN_FOCUS_PREV, BTN_FOCUS_NEXT):
        plugin = active_plugin()
        if _runtime_active or _training_active or (plugin and bool(getattr(plugin, "running", False))):
            set_status("Pause active crafting before changing focus.", WARN_HUE, "Craft Focus")
            return
        choices = ("unchanged",) + FOCUS_ORDER
        direction = -1 if button_id == BTN_FOCUS_PREV else 1
        _craft_focus = choices[(choices.index(_craft_focus) + direction) % len(choices)]
        save_settings()
        if _craft_focus == "guild":
            set_status("Guild focus will be set, but auto-consumed crafts need a confirmed Guild journal success line before FCC can count them.", WARN_HUE, "Craft Focus")
        else:
            set_status("Crafting focus: {0}. It will be verified when a tool opens.".format(FOCUS_LABELS[_craft_focus]), GOOD_HUE, "Craft Focus")
        return

    if _current_view == VIEW_PLUGIN:
        plugin = active_plugin()
        if plugin:
            local_button = int(button_id) - int(plugin.button_base)
            if 0 < local_button < PLUGIN_BUTTON_STRIDE:
                plugin.handle_button(local_button)
                _dirty_ui = True
                return

    if button_id == BTN_CATEGORY_PREV:
        page_count = max(1, (len(module_categories()) + CATEGORY_ROWS - 1) // CATEGORY_ROWS)
        _category_page = (_category_page - 1) % page_count
        _dirty_ui = True
        return
    if button_id == BTN_CATEGORY_NEXT:
        page_count = max(1, (len(module_categories()) + CATEGORY_ROWS - 1) // CATEGORY_ROWS)
        _category_page = (_category_page + 1) % page_count
        _dirty_ui = True
        return
    if button_id == BTN_RECIPE_PREV:
        page_count = max(1, (len(category_recipes()) + RECIPE_ROWS - 1) // RECIPE_ROWS)
        _recipe_page = (_recipe_page - 1) % page_count
        _dirty_ui = True
        return
    if button_id == BTN_RECIPE_NEXT:
        page_count = max(1, (len(category_recipes()) + RECIPE_ROWS - 1) // RECIPE_ROWS)
        _recipe_page = (_recipe_page + 1) % page_count
        _dirty_ui = True
        return

    if button_id == BTN_AMOUNT_MINUS_100:
        _target_amount = max(1, _target_amount - 100)
    elif button_id == BTN_AMOUNT_MINUS_10:
        _target_amount = max(1, _target_amount - 10)
    elif button_id == BTN_AMOUNT_MINUS_1:
        _target_amount = max(1, _target_amount - 1)
    elif button_id == BTN_AMOUNT_PLUS_1:
        _target_amount = min(MAX_CRAFT_AMOUNT, _target_amount + 1)
    elif button_id == BTN_AMOUNT_PLUS_10:
        _target_amount = min(MAX_CRAFT_AMOUNT, _target_amount + 10)
    elif button_id == BTN_AMOUNT_PLUS_100:
        _target_amount = min(MAX_CRAFT_AMOUNT, _target_amount + 100)
    else:
        pass

    if button_id in (BTN_AMOUNT_MINUS_100, BTN_AMOUNT_MINUS_10, BTN_AMOUNT_MINUS_1, BTN_AMOUNT_PLUS_1, BTN_AMOUNT_PLUS_10, BTN_AMOUNT_PLUS_100):
        save_settings()
        set_status("Craft amount set to {0}.".format(_target_amount), GOOD_HUE, "Ready")
        return

    if button_id == BTN_SOURCE_TOGGLE:
        _source_mode = SOURCE_SHELF if _source_mode == SOURCE_CHEST else SOURCE_CHEST
        save_settings()
        set_status("Resource source: " + source_mode_label() + ".", GOOD_HUE, "Ready")
        return
    if button_id == BTN_CRAFT_BAG_TOGGLE:
        if _runtime_active or _training_active or training_work_pending():
            set_status("Pause the job and finish pending training output before changing Craft Bag mode.", BAD_HUE, "Craft Bag Safety")
            return
        if _craft_bag_enabled:
            _craft_bag_enabled = False
            save_settings()
            set_status("Craft Bag mode disabled; staged items remain in the bag.", WARN_HUE, "Ready")
            return
        _craft_bag_enabled = True
        workspace_ready, workspace_error = craft_workspace_readiness()
        if not workspace_ready:
            _craft_bag_enabled = False
            set_status(workspace_error + ".", BAD_HUE, "Craft Bag Setup")
            return
        open_container(_craft_bag_serial)
        save_settings()
        set_status("Craft Bag mode enabled.", GOOD_HUE, "Ready")
        return
    if button_id == BTN_SET_RESOURCE_CHEST:
        set_target_serial("resource_chest")
        return
    if button_id == BTN_SET_RESOURCE_SHELF:
        set_target_serial("resource_shelf")
        return
    if button_id == BTN_SET_REAGENT_SHELF:
        set_target_serial("reagent_shelf")
        return
    if button_id == BTN_SET_OUTPUT_CHEST:
        set_target_serial("output_chest")
        return
    if button_id == BTN_SET_TOOL_BOOK:
        set_target_serial("tool_book")
        return
    if button_id == BTN_SET_TRASH_CONTAINER:
        set_target_serial("trash_container")
        return
    if button_id == BTN_SET_CRAFT_BAG:
        if _runtime_active or _training_active or training_work_pending():
            set_status("Pause the job and finish pending training output before changing the Craft Bag.", BAD_HUE, "Craft Bag Safety")
            return
        set_target_serial("craft_bag")
        return

    if button_id == BTN_CHOICE_GROUP_NEXT:
        change_choice_group()
        return
    if button_id == BTN_CHOICE_PREV:
        change_choice(-1)
        return
    if button_id == BTN_CHOICE_NEXT:
        change_choice(1)
        return

    if button_id == BTN_ACTION_SMELT:
        run_manual_server_action("smelt_item", "Smelt")
        return
    if button_id == BTN_ACTION_REPAIR:
        run_manual_server_action("repair_item", "Repair")
        return
    if button_id == BTN_ACTION_MARK:
        run_manual_server_action("mark_item", "Mark")
        return
    if button_id == BTN_ACTION_SALVAGE:
        run_manual_server_action("salvage", "Salvage")
        return
    if button_id == BTN_ACTION_RECYCLE:
        run_manual_server_action("recycle", "Recycle")
        return

    if button_id in _module_button_map:
        open_module_view(_module_button_map[button_id])
        return
    if button_id in _training_module_button_map:
        open_training_view(_training_module_button_map[button_id])
        return
    if button_id in _plugin_button_map:
        open_plugin_view(_plugin_button_map[button_id])
        return

    if button_id in _category_button_map:
        stop_runtime("Category changed.", WARN_HUE)
        select_category(_category_button_map[button_id])
        return
    if button_id in _recipe_button_map:
        stop_runtime("Recipe changed.", WARN_HUE)
        select_recipe(_recipe_button_map[button_id])
        return


# ===========================================================
# MAIN
# ===========================================================

def Main():
    global _dirty_ui, _operation_interrupted

    load_saved_settings()
    load_modules()
    load_plugins()
    if _settings_write_blocked:
        set_status("Settings JSON could not load; fix the file before persistence can resume.", BAD_HUE, "Settings")
    elif _settings_warning_logged:
        set_status("Settings JSON could not save; check folder permissions.", BAD_HUE, "Settings")
    update_ui_dirty_state()
    render_gui_safe()
    module_names = ", ".join([str(module.get("name", "Unknown")) for module in _modules])
    Misc.SendMessage("Frog Crafting Core {0} loaded: {1}".format(VERSION, module_names), GOOD_HUE)
    if _plugins:
        Misc.SendMessage("Crafting plugins loaded: " + ", ".join([str(plugin.name) for plugin in _plugins]), GOOD_HUE)

    while _running and Player.Connected:
        handled_button = False
        work_step_ran = False
        _operation_interrupted = False

        try:
            handled_button = consume_custom_gump_button()
        except Exception as ex:
            stop_runtime("Button error: " + str(ex), BAD_HUE)
            Misc.SendMessage("Frog Crafting button error: " + str(ex), BAD_HUE)

        if not _running:
            break

        if not handled_button:
            try:
                if _cleanup_active:
                    work_step_ran = True
                    material_cleanup_step()
                elif _training_active:
                    work_step_ran = True
                    training_step()
                elif _runtime_active:
                    work_step_ran = True
                    craft_step()
                else:
                    plugin = active_plugin()
                    if plugin and bool(getattr(plugin, "running", False)):
                        work_step_ran = True
                        plugin.step()

                if _operation_interrupted:
                    handled_button = True
                else:
                    handled_button = consume_custom_gump_button(False, work_step_ran)

                if not handled_button:
                    update_ui_dirty_state()
                    if _dirty_ui or not Gumps.GetGumpData(CORE_GUMP_ID):
                        render_gui_safe()
            except Exception as ex:
                stop_runtime("Runtime exception; core paused.", BAD_HUE)
                Misc.SendMessage("Frog Crafting runtime error: " + str(ex), BAD_HUE)
                _dirty_ui = True

        if _runtime_active and make_last_handoff_active():
            Misc.Pause(CRAFT_GUMP_RETURN_POLL_MS)
        else:
            Misc.Pause(REFRESH_MS)

    close_gump(CORE_GUMP_ID)
    shutdown_plugins()
    close_tool_book_gump()
    close_gump(TEMPLATE_CONFIRM_GUMP_ID)
    module = active_module()
    if module:
        close_gump(int_value(module.get("craft_gump_id")))
    close_gump(int_value(_shelf_data.get("gump_id"), 0x06ABCE12))
    close_gump(int_value(_reagent_shelf_data.get("gump_id"), 0xA8ED56C7))
    Misc.SendMessage("Frog Crafting Core stopped.", BAD_HUE)


Main()
