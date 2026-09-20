# =======================================================
# === Frog House Decay Logger (Razor Enhanced Script) ===
# =======================================================
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

import os
import re
import time

from System import Int32
from System.Collections.Generic import List
from System.IO import File

import Gumps
import Items
import Misc
import Player


# ===========================================================
# USER SETTINGS
# ===========================================================

CLIENT_DATA_FOLDER = r"D:\Ultima Online\Ultima Online Unchained\Data\Client"
XML_FILENAME = "House Decay.xml"

# 24 is the normal maximum world-item render distance.
SCAN_RANGE = 24
SCAN_INTERVAL_MS = 150
PROPERTY_WAIT_MS = 350

# A sign is checked once when first seen, then periodically while the
# script remains running. Restarting the script starts a fresh pass.
RECHECK_SECONDS = 300.0
FAILED_RETRY_SECONDS = 2.0

# Verified house-sign graphic from the supplied Enhanced Item Inspector.
# Add another shard-specific graphic here if one is discovered.
HOUSE_SIGN_ITEM_IDS = [0x0BD2]

# POINT.png is the smallest supplied CUO map icon.
MARKER_ICON = "Point"
SHOW_SAVED_MARKERS_IN_CHAT = True

# Healthier states are inspected but are not kept in the map pack.
MINIMUM_LOGGED_CONDITION = "Fairly Worn"


# ===========================================================
# CONFIGURATION
# ===========================================================

FACET_ID = 0
PACK_NAME = "House Decay"
XML_PATH = os.path.join(CLIENT_DATA_FOLDER, XML_FILENAME)

GUMP_ID = 0xF2064844
GUMP_X = 650
GUMP_Y = 450
GUMP_REFRESH_MS = 75
BUTTON_DEBOUNCE_MS = 175

BTN_TOGGLE = 1001
BTN_CLOSE = 1099

ACTIVE_HUE = 68
PAUSED_HUE = 53
ERROR_HUE = 33
TEXT_HUE = 0x0481

MAX_MARKER_NAME_LENGTH = 190

KNOWN_CONDITIONS = [
    ("in danger of collapsing", "In Danger of Collapsing"),
    ("critically worn", "Critically Worn"),
    ("severely weakened", "Severely Weakened"),
    ("heavily deteriorated", "Heavily Deteriorated"),
    ("extremely unstable", "Extremely Unstable"),
    ("dangerously weak", "Dangerously Weak"),
    ("nearly collapsed", "Nearly Collapsed"),
    ("crumbling rapidly", "Crumbling Rapidly"),
    ("falling apart", "Falling Apart"),
    ("imminent collapse", "Imminent Collapse"),
    ("about to fall", "About To Fall"),
    ("collapsing now", "Collapsing Now"),
    ("demolition pending", "Demolition Pending"),
    ("greatly worn", "Greatly Worn"),
    ("fairly worn", "Fairly Worn"),
    ("somewhat worn", "Somewhat Worn"),
    ("slightly worn", "Slightly Worn"),
    ("like new", "Like New"),
    ("condemned", "Condemned"),
]

# Staff-provided experimental IDOC bands. The first number is the
# earliest projected collapse and the second is the latest, measured
# from the first time this exact sign state is observed.
IDOC_WINDOWS = {
    "in danger of collapsing": ("36-27h", 27, 36),
    "critically worn": ("36-27h", 27, 36),
    "severely weakened": ("36-27h", 27, 36),
    "heavily deteriorated": ("27-18h", 18, 27),
    "extremely unstable": ("27-18h", 18, 27),
    "dangerously weak": ("27-18h", 18, 27),
    "nearly collapsed": ("18-9h", 9, 18),
    "crumbling rapidly": ("18-9h", 9, 18),
    "falling apart": ("18-9h", 9, 18),
    "imminent collapse": ("9-0h", 0, 9),
    "about to fall": ("9-0h", 0, 9),
    "collapsing now": ("9-0h", 0, 9),
}

CONDITION_RANKS = {
    "like new": 0,
    "slightly worn": 1,
    "somewhat worn": 2,
    "fairly worn": 3,
    "greatly worn": 4,
    "demolition pending": 6,
    "condemned": 6,
}


# ===========================================================
# GLOBAL STATE
# ===========================================================

_running = True
_runtime_active = True
_ready = False
_gump_dirty = True

_status_msg = "Starting..."
_nearby_count = 0
_session_updates = 0
_last_condition = "None"
_last_fall_window = "None"

_records = {}
_next_inspection = {}
_sign_filter = None
_next_scan_at = 0.0


# ===========================================================
# TEXT / XML HELPERS
# ===========================================================

def _clean_text(value):
    try:
        text = str(value or "")
    except:
        return ""

    text = text.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    return " ".join(text.split())


def _xml_escape(value):
    text = _clean_text(value)
    text = text.replace("&", "&amp;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&apos;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def _xml_unescape(value):
    text = str(value or "")
    text = text.replace("&quot;", '"')
    text = text.replace("&apos;", "'")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&amp;", "&")
    return text


def _marker_key(facet, x, y):
    return (int(facet), int(x), int(y))


def _format_local_time(epoch_seconds):
    formatted = time.strftime("%m/%d/%y %I:%M %p", time.localtime(epoch_seconds))
    return re.sub(r'\s0([0-9]:)', r' \1', formatted)


def _parse_local_time(value):
    try:
        parsed = time.strptime(_clean_text(value), "%m/%d/%y %I:%M %p")
        return float(time.mktime(parsed))
    except:
        return 0.0


def _idoc_window(condition):
    return IDOC_WINDOWS.get(_clean_text(condition).lower())


def _condition_rank(condition):
    cleaned = _clean_text(condition).lower()
    if cleaned in IDOC_WINDOWS:
        return 5
    return CONDITION_RANKS.get(cleaned, -1)


def _should_log_condition(condition):
    minimum_rank = CONDITION_RANKS.get(MINIMUM_LOGGED_CONDITION.lower(), 3)
    return _condition_rank(condition) >= minimum_rank


def _projection_text(condition, observed_at):
    window = _idoc_window(condition)
    if not window or observed_at <= 0:
        return condition

    window_label, earliest_hours, latest_hours = window
    earliest_fall = observed_at + (earliest_hours * 60 * 60)
    latest_fall = observed_at + (latest_hours * 60 * 60)

    return "{0} | {1} | Found {2} | Fall {3} - {4}".format(
        condition,
        window_label,
        _format_local_time(observed_at),
        _format_local_time(earliest_fall),
        _format_local_time(latest_fall)
    )


def _fall_window_text(condition, observed_at):
    window = _idoc_window(condition)
    if not window or observed_at <= 0:
        return "No projected fall window"

    earliest_fall = observed_at + (window[1] * 60 * 60)
    latest_fall = observed_at + (window[2] * 60 * 60)
    return "{0} - {1}".format(
        _format_local_time(earliest_fall),
        _format_local_time(latest_fall)
    )


def _marker_metadata(marker_name):
    text = _clean_text(marker_name)
    lower = text.lower()
    condition = ""

    for probe, display in KNOWN_CONDITIONS:
        if (lower == display.lower() or lower.startswith(display.lower() + " |") or
                lower.startswith("[" + display.lower() + "]")):
            condition = display
            break

    if not condition:
        bracket_match = re.match(r'^\[([^\]]+)\]', text)
        if bracket_match:
            condition = _clean_text(bracket_match.group(1))

    found_match = re.search(r'\|\s*Found\s+(.+?)\s*\|\s*Fall\s+', text, re.I)
    observed_at = _parse_local_time(found_match.group(1)) if found_match else 0.0
    return condition, observed_at


def _marker_label(condition, observed_at):
    label = _projection_text(condition, observed_at)

    if len(label) > MAX_MARKER_NAME_LENGTH:
        label = label[:MAX_MARKER_NAME_LENGTH - 3].rstrip() + "..."

    return label


def _build_xml_text():
    lines = [
        '<?xml version="1.0" ?>',
        '<Pack Name="{0}" Revision="0">'.format(_xml_escape(PACK_NAME)),
    ]

    ordered = sorted(_records.values(), key=lambda record: (
        int(record["y"]), int(record["x"]), str(record["name"]).lower()))

    for record in ordered:
        lines.append(
            '<Marker Name="{0}" Facet="{1}" Icon="{2}" X="{3}" Y="{4}"/>'.format(
                _xml_escape(record["name"]),
                int(record["facet"]),
                _xml_escape(MARKER_ICON),
                int(record["x"]),
                int(record["y"])
            )
        )

    lines.append("</Pack>")
    return "\r\n".join(lines) + "\r\n"


def _write_xml_file():
    temp_path = XML_PATH + ".tmp"
    backup_path = XML_PATH + ".bak"

    try:
        if not os.path.isdir(CLIENT_DATA_FOLDER):
            return False, "Client Data folder not found"

        if File.Exists(temp_path):
            File.Delete(temp_path)

        File.WriteAllText(temp_path, _build_xml_text())

        if File.Exists(XML_PATH):
            if File.Exists(backup_path):
                File.Delete(backup_path)
            File.Replace(temp_path, XML_PATH, backup_path)
            try:
                if File.Exists(backup_path):
                    File.Delete(backup_path)
            except:
                pass
        else:
            File.Move(temp_path, XML_PATH)

        return True, ""

    except Exception as error:
        try:
            if File.Exists(temp_path):
                File.Delete(temp_path)
        except:
            pass
        return False, str(error)


def _load_xml_file():
    global _records

    _records = {}
    migration_needed = False

    if not File.Exists(XML_PATH):
        return _write_xml_file()

    try:
        xml_text = str(File.ReadAllText(XML_PATH))
        pack_match = re.search(r'<Pack\b[^>]*\bName\s*=\s*"([^"]*)"', xml_text, re.I)

        if not pack_match:
            return False, "Existing XML has no Pack element"

        if _xml_unescape(pack_match.group(1)).strip().lower() != PACK_NAME.lower():
            return False, "Existing XML is not the House Decay pack"

        for marker_match in re.finditer(r'<Marker\b([^>]*)/\s*>', xml_text, re.I):
            attributes = {}
            for attr_match in re.finditer(r'([A-Za-z]+)\s*=\s*"([^"]*)"', marker_match.group(1)):
                attributes[attr_match.group(1).lower()] = _xml_unescape(attr_match.group(2))

            if "name" not in attributes or "x" not in attributes or "y" not in attributes:
                continue

            facet = int(attributes.get("facet", FACET_ID))
            x = int(attributes["x"])
            y = int(attributes["y"])
            key = _marker_key(facet, x, y)
            condition, observed_at = _marker_metadata(attributes["name"])
            marker_name = attributes["name"]

            if not _should_log_condition(condition):
                migration_needed = True
                continue

            if condition:
                compact_name = _marker_label(condition, observed_at)
                if compact_name != marker_name:
                    marker_name = compact_name
                    migration_needed = True

            _records[key] = {
                "name": marker_name,
                "condition": condition,
                "observed_at": observed_at,
                "facet": facet,
                "x": x,
                "y": y,
            }

        if migration_needed:
            success, error = _write_xml_file()
            if not success:
                return False, "Could not compact existing marker names: {0}".format(error)

        return True, ""

    except Exception as error:
        _records = {}
        return False, "Could not read existing XML: {0}".format(str(error))


# ===========================================================
# HOUSE-SIGN INSPECTION
# ===========================================================

def _build_sign_filter():
    sign_filter = Items.Filter()
    sign_filter.Enabled = True
    sign_filter.OnGround = True
    sign_filter.RangeMax = SCAN_RANGE

    graphics = List[Int32]()
    for item_id in HOUSE_SIGN_ITEM_IDS:
        graphics.Add(Int32(item_id))
    sign_filter.Graphics = graphics

    return sign_filter


def _find_house_signs():
    global _sign_filter

    if _sign_filter is None:
        _sign_filter = _build_sign_filter()

    try:
        return [item for item in (Items.ApplyFilter(_sign_filter) or []) if item]
    except Exception as error:
        _set_status("Scan failed: {0}".format(str(error)), True)
        return []


def _distance_to_item(item):
    try:
        return max(
            abs(int(item.Position.X) - int(Player.Position.X)),
            abs(int(item.Position.Y) - int(Player.Position.Y))
        )
    except:
        return 999


def _condition_from_lines(lines):
    for line in lines:
        lower = line.lower()
        if lower.startswith("condition:"):
            raw = line.split(":", 1)[1].strip()
            raw = re.sub(r'^this\s+structure\s+is\s+', "", raw, flags=re.I)
            raw = raw.rstrip(". ")

            for probe, display in KNOWN_CONDITIONS:
                if probe in raw.lower():
                    return display

            return raw or "Unknown"

    joined = " ".join(lines).lower()
    for probe, display in KNOWN_CONDITIONS:
        if probe in joined:
            return display

    return ""


def _house_details(lines):
    has_house_details = False

    for line in lines:
        lower = line.lower()

        if lower.startswith("name:"):
            has_house_details = True
        elif "private home" in lower or "public home" in lower:
            has_house_details = True

    condition = _condition_from_lines(lines)
    has_house_details = bool(has_house_details or condition)

    if has_house_details and not condition:
        condition = "Unknown"

    return condition, has_house_details


def _read_sign(item):
    try:
        Items.WaitForProps(int(item.Serial), PROPERTY_WAIT_MS)
        lines = [_clean_text(line) for line in (Items.GetPropStringList(int(item.Serial)) or [])]
        lines = [line for line in lines if line]
    except Exception as error:
        return None, "Property read failed: {0}".format(str(error))

    condition, has_house_details = _house_details(lines)

    if not has_house_details:
        return None, "Waiting for sign properties"

    try:
        x = int(item.Position.X)
        y = int(item.Position.Y)
        observed_at = 0.0

        if _idoc_window(condition):
            existing = _records.get(_marker_key(FACET_ID, x, y))
            if existing and _clean_text(existing.get("condition", "")).lower() == condition.lower():
                observed_at = float(existing.get("observed_at", 0.0) or 0.0)

            if observed_at <= 0:
                observed_at = time.time()

        return {
            "name": _marker_label(condition, observed_at),
            "condition": condition,
            "observed_at": observed_at,
            "facet": FACET_ID,
            "x": x,
            "y": y,
        }, ""
    except Exception as error:
        return None, "Sign position unavailable: {0}".format(str(error))


def _save_house_record(record):
    global _session_updates

    key = _marker_key(record["facet"], record["x"], record["y"])
    old_record = _records.get(key)

    if old_record and old_record.get("name") == record.get("name"):
        return True, False, ""

    _records[key] = dict(record)

    success, error = _write_xml_file()
    if not success:
        if old_record is None:
            _records.pop(key, None)
        else:
            _records[key] = old_record
        return False, False, error

    _session_updates += 1
    return True, True, ""


def _remove_house_record(record):
    global _session_updates

    key = _marker_key(record["facet"], record["x"], record["y"])
    old_record = _records.get(key)

    if old_record is None:
        return True, False, ""

    _records.pop(key, None)
    success, error = _write_xml_file()

    if not success:
        _records[key] = old_record
        return False, False, error

    _session_updates += 1
    return True, True, ""


def _inspect_one_sign(sign, now):
    global _last_condition
    global _last_fall_window

    serial = int(sign.Serial)
    _next_inspection[serial] = now + RECHECK_SECONDS

    record, error = _read_sign(sign)
    if record is None:
        _next_inspection[serial] = now + FAILED_RETRY_SECONDS
        _set_status(error, True)
        return

    window = _idoc_window(record["condition"])
    _last_condition = "{0} ({1})".format(record["condition"], window[0]) if window else record["condition"]
    _last_fall_window = _fall_window_text(record["condition"], record["observed_at"])

    key = _marker_key(record["facet"], record["x"], record["y"])
    previous = _records.get(key)
    previous_condition = _clean_text(previous.get("condition", "")) if previous else ""

    if not _should_log_condition(record["condition"]):
        success, removed, error = _remove_house_record(record)
        if not success:
            _next_inspection[serial] = now + FAILED_RETRY_SECONDS
            _set_status("XML write failed: {0}".format(error), True)
            return

        _set_status("Ignored - healthier than {0}".format(MINIMUM_LOGGED_CONDITION), True)
        if removed and SHOW_SAVED_MARKERS_IN_CHAT:
            Misc.SendMessage("MAP MARKER REMOVED: {0} is below {1}".format(
                record["condition"], MINIMUM_LOGGED_CONDITION), PAUSED_HUE)
        return

    success, changed, error = _save_house_record(record)
    if not success:
        _next_inspection[serial] = now + FAILED_RETRY_SECONDS
        _set_status("XML write failed: {0}".format(error), True)
        return

    if changed:
        _set_status("Saved marker at {0}, {1}".format(record["x"], record["y"]), True)
        if SHOW_SAVED_MARKERS_IN_CHAT:
            action = "UPDATED" if previous else "ADDED"
            Misc.SendMessage("MAP MARKER {0}: {1}".format(
                action, _projection_text(record["condition"], record["observed_at"])), ACTIVE_HUE)

            if previous_condition and previous_condition.lower() != record["condition"].lower():
                Misc.SendMessage("STRUCTURE STATUS CHANGED: {0}".format(
                    _projection_text(record["condition"], record["observed_at"])), PAUSED_HUE)
    else:
        _set_status("Checked - no change", True)


def _scan_step():
    global _nearby_count
    global _next_scan_at

    now = time.time()
    if now < _next_scan_at:
        return

    _next_scan_at = now + (SCAN_INTERVAL_MS / 1000.0)
    signs = _find_house_signs()

    if len(signs) != _nearby_count:
        _nearby_count = len(signs)
        _mark_gump_dirty()

    candidates = []
    for sign in signs:
        try:
            serial = int(sign.Serial)
        except:
            continue

        if now >= _next_inspection.get(serial, 0.0):
            candidates.append(sign)

    if not candidates:
        return

    closest = min(candidates, key=_distance_to_item)
    _inspect_one_sign(closest, now)


# ===========================================================
# STATUS GUMP
# ===========================================================

def _mark_gump_dirty():
    global _gump_dirty
    _gump_dirty = True


def _set_status(message, redraw):
    global _status_msg
    _status_msg = _clean_text(message)
    if redraw:
        _mark_gump_dirty()


def _short_label(text, max_length):
    clean = _clean_text(text)
    if len(clean) <= max_length:
        return clean
    return clean[:max_length - 3].rstrip() + "..."


def _draw_gump():
    global _gump_dirty

    Gumps.CloseGump(GUMP_ID)

    gump = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gump, 0)
    Gumps.AddBackground(gump, 0, 0, 390, 126, 9270)
    Gumps.AddAlphaRegion(gump, 0, 0, 390, 126)

    Gumps.AddLabel(gump, 12, 9, 88, "House Decay Logger")
    Gumps.AddButton(gump, 360, 8, 4017, 4019, BTN_CLOSE, 1, 0)
    Gumps.AddButton(gump, 12, 34, 4005, 4007, BTN_TOGGLE, 1, 0)

    if not _ready:
        state_text = "Setup Error"
        state_hue = ERROR_HUE
    elif _runtime_active:
        state_text = "Scanning {0} tiles".format(SCAN_RANGE)
        state_hue = ACTIVE_HUE
    else:
        state_text = "Paused"
        state_hue = PAUSED_HUE

    Gumps.AddLabel(gump, 47, 35, state_hue, state_text)
    Gumps.AddLabel(gump, 245, 35, TEXT_HUE, "Near {0} / Logged {1}".format(
        _nearby_count, len(_records)))
    Gumps.AddLabel(gump, 12, 58, TEXT_HUE, "Decay: {0}".format(_short_label(_last_condition, 48)))
    Gumps.AddLabel(gump, 12, 79, TEXT_HUE, "Fall: {0}".format(_short_label(_last_fall_window, 55)))
    Gumps.AddLabel(gump, 12, 100, state_hue, _short_label(_status_msg, 43))

    Gumps.SendGump(GUMP_ID, Player.Serial, GUMP_X, GUMP_Y,
                   gump.gumpDefinition, gump.gumpStrings)
    _gump_dirty = False


def _handle_button(button_id):
    global _running
    global _runtime_active

    if button_id == BTN_CLOSE:
        _running = False
        return

    if button_id == BTN_TOGGLE and _ready:
        _runtime_active = not _runtime_active
        _set_status("Scanning" if _runtime_active else "Paused", True)


# ===========================================================
# MAIN
# ===========================================================

def Main():
    global _ready

    success, error = _load_xml_file()
    _ready = success

    if success:
        _set_status("Ready - XML loaded", True)
        Misc.SendMessage("House Decay Logger ready ({0} and worse): {1}".format(
            MINIMUM_LOGGED_CONDITION, XML_PATH), ACTIVE_HUE)
    else:
        _set_status(error, True)
        Misc.SendMessage("House Decay Logger setup failed: {0}".format(error), ERROR_HUE)

    try:
        while _running and Player.Connected:
            handled_button = False
            gump = Gumps.GetGumpData(GUMP_ID)
            button_id = int(getattr(gump, "buttonid", 0)) if gump else 0

            if button_id > 0:
                try:
                    gump.buttonid = 0
                except:
                    pass

                Gumps.CloseGump(GUMP_ID)
                _handle_button(button_id)
                handled_button = True
                Misc.Pause(BUTTON_DEBOUNCE_MS)

            if not _running:
                break

            if not handled_button:
                if _ready and _runtime_active:
                    _scan_step()

                if _gump_dirty or Gumps.GetGumpData(GUMP_ID) is None:
                    _draw_gump()

            Misc.Pause(GUMP_REFRESH_MS)

    except Exception as error:
        Misc.SendMessage("House Decay Logger stopped: {0}".format(str(error)), ERROR_HUE)

    finally:
        Gumps.CloseGump(GUMP_ID)
        Misc.SendMessage("House Decay Logger stopped. {0} marker update(s) saved.".format(
            _session_updates), PAUSED_HUE)


Main()
