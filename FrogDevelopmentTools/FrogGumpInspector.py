# ============================================================
# Frog Gump Inspector 1.0
# Razor Enhanced development and gump-data capture tool
# ============================================================

import datetime
import hashlib
import json
import os
import re
import zipfile

import Gumps
import Misc
import Player


# ============================================================
# CONFIGURATION
# ============================================================

GUMP_ID = 0xF2064749
GUMP_X = 365
GUMP_Y = 125
GUMP_WIDTH = 700
GUMP_HEIGHT = 550
GUMP_REFRESH_MS = 100
BUTTON_DEBOUNCE_MS = 175
CAPTURE_NEXT_TIMEOUT_MS = 30000
MAX_GUI_ROWS = 46
MAX_REFLECTION_LIST_ITEMS = 2000

OUTPUT_FOLDER = os.path.join("FrogDevelopmentTools", "data", "gumps")

BACKGROUND_ID = 5054
TITLE_HUE = 1152
TEXT_HUE = 0x0481
VALUE_HUE = 68
MUTED_HUE = 945
ERROR_HUE = 33
SUCCESS_HUE = 68

HTML_TEXT_COLOR = "#F4E7C5"
HTML_LABEL_COLOR = "#FFD27F"
HTML_VALUE_COLOR = "#FFFFFF"
HTML_SECTION_COLOR = "#80FF80"
HTML_DETAIL_COLOR = "#87CEFA"
HTML_COMMENT_COLOR = "#B8D8A8"
HTML_ERROR_COLOR = "#FF8080"

ENTRY_GUMP_ID = 9000
BTN_CAPTURE_ID = 100
BTN_CAPTURE_CURRENT = 101
BTN_CAPTURE_NEXT = 102
BTN_REFRESH = 103
BTN_SAVE_FILE = 104
BTN_TAB_SUMMARY = 120
BTN_TAB_CONTROLS = 121
BTN_TAB_BUTTONS = 122
BTN_TAB_INPUTS = 123
BTN_TAB_TEXT = 124
BTN_TAB_RAW = 125
BTN_CLOSE = 199

CONTROL_COLUMNS = (
    "index", "command", "category", "page", "group", "x", "y",
    "width", "height", "button_id", "button_type", "button_type_name", "param", "action",
    "entry_id", "switch_id", "initial_state", "normal_art",
    "pressed_art", "gump_art", "item_id", "hue", "text_index",
    "resolved_text", "cliloc", "background", "scrollbar",
    "max_length", "tooltip_cliloc", "tooltip_args", "item_serial",
    "master_gump", "sprite_x", "sprite_y", "token_args", "nearby_label",
    "nearby_text_command", "linked_to",
    "extra_args", "args", "parse_error", "meaning", "raw"
)

COMMAND_MEANINGS = {
    "page": "Selects the page assigned to controls that follow. Page 0 is always visible.",
    "group": "Starts a radio-button group. Radios in the same group are mutually exclusive.",
    "endgroup": "Ends the current radio-button group.",
    "mastergump": "Declares a parent/master gump identifier used by some client layouts.",
    "nomove": "Prevents the player from dragging this gump.",
    "noclose": "Prevents the normal right-click close action.",
    "nodispose": "Marks the gump as non-disposable in the client.",
    "noresize": "Prevents client-side resizing.",
    "resizepic": "Draws a scalable background frame from gump artwork.",
    "checkertrans": "Draws a translucent rectangular region.",
    "button": "Clickable gump-art button. Reply buttons return button_id; Page buttons navigate locally.",
    "buttontileart": "Clickable button plus item art, hue, and an explicit art region.",
    "checkbox": "Independent on/off switch returned by switch_id when selected.",
    "radio": "Mutually exclusive switch returned by switch_id when selected.",
    "textentry": "Editable text box returned by entry_id with a string-table default.",
    "textentrylimited": "Editable text box with a maximum character count.",
    "text": "Single-line text resolved through the gump string table.",
    "croppedtext": "String-table text clipped to a rectangular region.",
    "htmlgump": "HTML-capable string-table text region with optional background and scrollbar.",
    "xmfhtmlgump": "Localized HTML region identified by a cliloc number.",
    "xmfhtmlgumpcolor": "Localized HTML region with an explicit color.",
    "xmfhtmltok": "Localized HTML region with token arguments embedded in the layout.",
    "gumppic": "Draws one gump-art image; optional tokens can supply hue or class metadata.",
    "gumppictiled": "Tiles one gump-art image across a rectangular region.",
    "picinpic": "Draws a cropped sprite from inside a larger gump-art image.",
    "tilepic": "Draws item/static artwork by item ID.",
    "tilepichue": "Draws item/static artwork with an explicit hue.",
    "tooltip": "Attaches a localized tooltip to the preceding control.",
    "itemproperty": "Associates an item serial so the client can show its property tooltip.",
}


# ============================================================
# RUNTIME STATE
# ============================================================

_running = True
_snapshot = None
_current_gump_id = 0
_last_external_gump_id = 0
_current_tab = "summary"
_id_input = ""
_status_message = "Ready. Enter a gump ID, capture an open gump, or arm CAPTURE NEXT."
_status_hue = MUTED_HUE
_gump_dirty = True
_capture_next_armed = False
_capture_next_started = None
_capture_next_baseline = set()


# ============================================================
# BASIC HELPERS
# ============================================================

def _clean_text(value):
    if value is None:
        return ""
    try:
        return str(value).replace("\x00", "").strip()
    except:
        return ""


def _runtime_type(value):
    if value is None:
        return "None"
    try:
        return _clean_text(value.GetType().FullName)
    except:
        try:
            return _clean_text(type(value).__name__)
        except:
            return "Unknown"


def _hex(value, width=8):
    try:
        mask = (1 << (width * 4)) - 1
        return "0x{0:0{1}X}".format(int(value) & mask, width)
    except:
        return "0x" + ("0" * width)


def _safe_attr(obj, name, default=None):
    try:
        return getattr(obj, name)
    except:
        return default


def _short(value, length):
    text = _clean_text(value)
    if len(text) <= length:
        return text
    return text[:max(0, length - 3)].rstrip() + "..."


def _html_escape(value):
    text = _clean_text(value)
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))


def _html_lines(lines):
    separator = "</basefont><br><basefont color={0}>".format(HTML_TEXT_COLOR)
    return "<basefont color={0}>{1}</basefont>".format(
        HTML_TEXT_COLOR, separator.join(lines)
    )


def _set_status(message, hue=MUTED_HUE):
    global _status_message
    global _status_hue
    _status_message = _clean_text(message)
    _status_hue = hue


def _output_dir():
    path = os.path.join(Misc.CurrentScriptDirectory(), OUTPUT_FOLDER)
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def _safe_filename(value):
    text = _clean_text(value) or "gump"
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
    cleaned = "".join(character if character in allowed else "_" for character in text)
    return (cleaned.strip("_") or "gump")[:48]


def _write_text(path, text):
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as stream:
        stream.write(text)
    if os.path.exists(path):
        os.remove(path)
    os.rename(temporary, path)


def _sha256_text(value):
    try:
        return hashlib.sha256((_clean_text(value)).encode("utf-8")).hexdigest()
    except:
        return ""


def _dotnet_list(value):
    if value is None:
        return []
    output = []
    try:
        for entry in value:
            output.append(_json_value(entry, 1))
            if len(output) >= MAX_REFLECTION_LIST_ITEMS:
                output.append({"truncated": True})
                break
    except Exception as error:
        output.append({"read_error": _clean_text(error)})
    return output


def _json_value(value, depth=0):
    if value is None:
        return None
    if depth > 5:
        return _clean_text(value)
    if isinstance(value, bool):
        return bool(value)
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return float(value)
    if isinstance(value, str):
        return value

    type_name = _runtime_type(value)
    simple_type = type_name.split(".")[-1]
    if simple_type == "Boolean":
        return bool(value)
    if simple_type in (
        "Byte", "SByte", "Int16", "UInt16", "Int32", "UInt32",
        "Int64", "UInt64", "BigInteger"
    ):
        try:
            return int(value)
        except:
            pass
    if simple_type in ("Single", "Double", "Decimal"):
        try:
            return float(value)
        except:
            pass
    if simple_type in ("String", "Char"):
        return _clean_text(value)
    if hasattr(value, "Keys"):
        result = {}
        try:
            for key in value.Keys:
                result[_clean_text(key)] = _json_value(value[key], depth + 1)
                if len(result) >= MAX_REFLECTION_LIST_ITEMS:
                    result["__truncated__"] = True
                    break
            return result
        except:
            pass
    if hasattr(value, "Count") or hasattr(value, "__iter__"):
        result = []
        try:
            for entry in value:
                result.append(_json_value(entry, depth + 1))
                if len(result) >= MAX_REFLECTION_LIST_ITEMS:
                    result.append({"truncated": True})
                    break
            return result
        except:
            pass
    return _clean_text(value)


def _parse_uint(value):
    text = _clean_text(value)
    if not text:
        raise ValueError("Enter a decimal or 0x-prefixed hexadecimal gump ID.")
    number = int(text, 16) if text.lower().startswith("0x") else int(text, 10)
    if number < 0 or number > 0xFFFFFFFF:
        raise ValueError("Gump ID must be between 0 and 0xFFFFFFFF.")
    return number


def _open_gump_ids():
    output = []
    try:
        for value in Gumps.AllGumpIDs():
            number = int(value)
            if number != GUMP_ID:
                output.append(number)
    except:
        pass
    return output


def _remember_external_current():
    global _last_external_gump_id
    try:
        current = int(Gumps.CurrentGump())
    except:
        current = 0
    if current > 0 and current != GUMP_ID:
        _last_external_gump_id = current
    return current


def _api_probe(name, callback, errors):
    try:
        return _json_value(callback())
    except Exception as error:
        errors.append("{0}: {1}".format(name, _clean_text(error)))
        return None


# ============================================================
# .NET REFLECTION
# ============================================================

def _reflect_public_members(obj):
    result = {
        "runtime_type": _runtime_type(obj),
        "properties": {},
        "fields": {},
        "read_errors": {},
    }
    if obj is None:
        result["read_errors"]["object"] = "Object was None."
        return result
    try:
        for prop in obj.GetType().GetProperties():
            name = _clean_text(prop.Name)
            try:
                if not prop.CanRead or prop.GetIndexParameters().Length > 0:
                    continue
                result["properties"][name] = _json_value(prop.GetValue(obj, None), 1)
            except Exception as error:
                result["read_errors"]["property." + name] = _clean_text(error)
    except Exception as error:
        result["read_errors"]["GetProperties"] = _clean_text(error)
    try:
        for field in obj.GetType().GetFields():
            name = _clean_text(field.Name)
            try:
                result["fields"][name] = _json_value(field.GetValue(obj), 1)
            except Exception as error:
                result["read_errors"]["field." + name] = _clean_text(error)
    except Exception as error:
        result["read_errors"]["GetFields"] = _clean_text(error)
    return result


def _reflect_all_instance_members(obj):
    result = {
        "runtime_type": _runtime_type(obj),
        "types": [],
        "read_errors": {},
    }
    if obj is None:
        result["read_errors"]["object"] = "Object was None."
        return result
    try:
        import clr
        clr.AddReference("System")
        from System.Reflection import BindingFlags
        flags = (BindingFlags.Instance | BindingFlags.Public |
                 BindingFlags.NonPublic | BindingFlags.DeclaredOnly)
        current_type = obj.GetType()
        while current_type is not None and _clean_text(current_type.FullName) != "System.Object":
            type_name = _clean_text(current_type.FullName)
            section = {"declaring_type": type_name, "properties": {}, "fields": {}}
            try:
                properties = list(current_type.GetProperties(flags) or [])
            except Exception as error:
                properties = []
                result["read_errors"][type_name + ".GetProperties"] = _clean_text(error)
            for prop in properties:
                name = _clean_text(prop.Name)
                try:
                    if prop.GetIndexParameters().Length > 0:
                        continue
                    getter = prop.GetGetMethod(True)
                    if getter is None:
                        continue
                    section["properties"][name] = _json_value(prop.GetValue(obj, None), 1)
                except Exception as error:
                    result["read_errors"][type_name + ".property." + name] = _clean_text(error)
            try:
                fields = list(current_type.GetFields(flags) or [])
            except Exception as error:
                fields = []
                result["read_errors"][type_name + ".GetFields"] = _clean_text(error)
            for field in fields:
                name = _clean_text(field.Name)
                try:
                    section["fields"][name] = _json_value(field.GetValue(obj), 1)
                except Exception as error:
                    result["read_errors"][type_name + ".field." + name] = _clean_text(error)
            result["types"].append(section)
            current_type = current_type.BaseType
    except Exception as error:
        result["read_errors"]["reflection_setup"] = _clean_text(error)
    return result


# ============================================================
# RAW LAYOUT PARSER
# ============================================================

def _layout_bodies(layout):
    bodies = []
    text = _clean_text(layout)
    position = 0
    while position < len(text):
        begin = text.find("{", position)
        if begin < 0:
            break
        end = text.find("}", begin + 1)
        if end < 0:
            bodies.append(text[begin + 1:].strip())
            break
        bodies.append(text[begin + 1:end].strip())
        position = end + 1
    return bodies


def _layout_tokens(body):
    tokens = []
    try:
        tokens = re.findall(r"@[^@]*@|[^\s]+", body)
    except:
        tokens = body.split()
    cleaned = []
    for token in tokens:
        if len(token) >= 2 and token[0] == "@" and token[-1] == "@":
            cleaned.append(token[1:-1])
        else:
            cleaned.append(token)
    return cleaned


def _token_value(token):
    text = _clean_text(token)
    if "=" in text:
        key, value = text.split("=", 1)
        try:
            return {key.lower(): int(value, 0)}
        except:
            return {key.lower(): value}
    try:
        return int(text, 0)
    except:
        return text


def _assign_args(row, args, names):
    for index, name in enumerate(names):
        if index < len(args):
            row[name] = _token_value(args[index])
    if len(args) < len(names):
        row["parse_error"] = "Expected {0} args; received {1}.".format(len(names), len(args))
    if len(args) > len(names):
        row["extra_args"] = [_token_value(value) for value in args[len(names):]]


def _resolve_string(strings, index):
    try:
        index = int(index)
        if index < 0 or index >= len(strings):
            return None
        return strings[index]
    except:
        return None


def _parse_layout(layout, strings):
    rows = []
    current_page = 0
    current_group = None
    previous_control = None

    for index, body in enumerate(_layout_bodies(layout)):
        tokens = _layout_tokens(body)
        if not tokens:
            continue
        command = _clean_text(tokens[0]).lower()
        args = tokens[1:]
        row = {
            "index": index,
            "command": command,
            "category": "unknown",
            "page": current_page,
            "group": current_group,
            "meaning": COMMAND_MEANINGS.get(
                command, "Unrecognized layout command; raw tokens are preserved for research."
            ),
            "raw": body,
            "args": [_token_value(value) for value in args],
            "parse_error": "",
        }

        if command == "page":
            _assign_args(row, args, ("page",))
            current_page = row.get("page", current_page)
            row["category"] = "structure"
        elif command == "group":
            _assign_args(row, args, ("group",))
            current_group = row.get("group")
            row["category"] = "structure"
        elif command == "endgroup":
            row["category"] = "structure"
            current_group = None
        elif command in ("nomove", "noclose", "nodispose", "noresize"):
            row["category"] = "behavior"
        elif command == "mastergump":
            _assign_args(row, args, ("master_gump",))
            row["category"] = "behavior"
        elif command == "resizepic":
            _assign_args(row, args, ("x", "y", "gump_art", "width", "height"))
            row["category"] = "region"
        elif command == "checkertrans":
            _assign_args(row, args, ("x", "y", "width", "height"))
            row["category"] = "region"
        elif command == "button":
            _assign_args(row, args, (
                "x", "y", "normal_art", "pressed_art", "button_type",
                "param", "button_id"
            ))
            row["category"] = "button"
        elif command == "buttontileart":
            _assign_args(row, args, (
                "x", "y", "normal_art", "pressed_art", "button_type",
                "param", "button_id", "item_id", "hue", "width", "height"
            ))
            row["category"] = "button"
        elif command in ("checkbox", "radio"):
            _assign_args(row, args, (
                "x", "y", "normal_art", "pressed_art", "initial_state", "switch_id"
            ))
            row["category"] = "switch"
        elif command == "textentry":
            _assign_args(row, args, (
                "x", "y", "width", "height", "hue", "entry_id", "text_index"
            ))
            row["category"] = "input"
        elif command == "textentrylimited":
            _assign_args(row, args, (
                "x", "y", "width", "height", "hue", "entry_id", "text_index", "max_length"
            ))
            row["category"] = "input"
        elif command == "text":
            _assign_args(row, args, ("x", "y", "hue", "text_index"))
            row["category"] = "text"
        elif command == "croppedtext":
            _assign_args(row, args, ("x", "y", "width", "height", "hue", "text_index"))
            row["category"] = "text"
        elif command == "htmlgump":
            _assign_args(row, args, (
                "x", "y", "width", "height", "text_index", "background", "scrollbar"
            ))
            row["category"] = "text"
        elif command == "xmfhtmlgump":
            _assign_args(row, args, (
                "x", "y", "width", "height", "cliloc", "background", "scrollbar"
            ))
            row["category"] = "localized_text"
        elif command == "xmfhtmlgumpcolor":
            _assign_args(row, args, (
                "x", "y", "width", "height", "cliloc", "background", "scrollbar", "hue"
            ))
            row["category"] = "localized_text"
        elif command == "xmfhtmltok":
            _assign_args(row, args, (
                "x", "y", "width", "height", "background", "scrollbar", "hue", "cliloc", "token_args"
            ))
            row["category"] = "localized_text"
        elif command == "gumppic":
            _assign_args(row, args, ("x", "y", "gump_art"))
            row["category"] = "art"
            for extra in row.get("extra_args", []):
                if isinstance(extra, dict) and "hue" in extra:
                    row["hue"] = extra["hue"]
        elif command == "gumppictiled":
            _assign_args(row, args, ("x", "y", "width", "height", "gump_art"))
            row["category"] = "art"
        elif command == "picinpic":
            _assign_args(row, args, (
                "x", "y", "gump_art", "sprite_x", "sprite_y", "width", "height"
            ))
            row["category"] = "art"
        elif command == "tilepic":
            _assign_args(row, args, ("x", "y", "item_id"))
            row["category"] = "art"
        elif command == "tilepichue":
            _assign_args(row, args, ("x", "y", "item_id", "hue"))
            row["category"] = "art"
        elif command == "tooltip":
            if args:
                row["cliloc"] = _token_value(args[0])
            else:
                row["parse_error"] = "Expected a tooltip cliloc."
            if len(args) > 1:
                row["tooltip_args"] = _token_value(args[1])
            if len(args) > 2:
                row["extra_args"] = [_token_value(value) for value in args[2:]]
            row["category"] = "metadata"
            if previous_control is not None:
                row["linked_to"] = previous_control.get("index")
                previous_control["tooltip_cliloc"] = row.get("cliloc")
                previous_control["tooltip_args"] = row.get("tooltip_args", "")
        elif command == "itemproperty":
            _assign_args(row, args, ("item_serial",))
            row["category"] = "metadata"
            if previous_control is not None:
                row["linked_to"] = previous_control.get("index")

        if "button_type" in row:
            if row["button_type"] == 0:
                row["button_type_name"] = "Page"
                row["action"] = "Navigate locally to page {0}".format(row.get("param"))
            elif row["button_type"] == 1:
                row["button_type_name"] = "Reply"
                row["action"] = "Submit reply button ID {0}".format(row.get("button_id"))
            else:
                row["button_type_name"] = "Unknown"
                row["action"] = "Unknown button type {0}".format(row.get("button_type"))
        if "text_index" in row:
            row["resolved_text"] = _resolve_string(strings, row.get("text_index"))
            if row["resolved_text"] is None:
                message = "String-table index {0} is unavailable.".format(row.get("text_index"))
                row["parse_error"] = (row.get("parse_error", "") + " " + message).strip()
        rows.append(row)
        if row.get("category") not in ("metadata", "structure", "behavior"):
            previous_control = row
    return rows


def _annotate_nearby_labels(commands):
    text_rows = []
    for row in commands:
        if row.get("category") not in ("text", "localized_text"):
            continue
        label = row.get("resolved_text")
        if label is None and row.get("cliloc") is not None:
            label = "cliloc {0}".format(row.get("cliloc"))
        if label is None or row.get("x") is None or row.get("y") is None:
            continue
        text_rows.append((row, _clean_text(label)))

    for control in commands:
        if control.get("category") not in ("button", "input", "switch"):
            continue
        if control.get("tooltip_args"):
            control["nearby_label"] = _clean_text(control.get("tooltip_args"))
            continue
        try:
            control_x = int(control.get("x"))
            control_y = int(control.get("y"))
        except:
            continue
        best = None
        for text_row, label in text_rows:
            if text_row.get("page") not in (0, control.get("page")):
                continue
            try:
                dx = int(text_row.get("x")) - control_x
                dy = int(text_row.get("y")) - control_y
            except:
                continue
            if abs(dy) > 48 or abs(dx) > 320:
                continue
            # Labels immediately to the right are the most common gump pattern.
            direction_penalty = 0 if dx >= -15 else 120
            score = abs(dy) * 5 + abs(dx) + direction_penalty
            if best is None or score < best[0]:
                best = (score, text_row, label)
        if best is not None:
            control["nearby_label"] = best[2]
            control["nearby_text_command"] = best[1].get("index")


# ============================================================
# COMMAND ANALYSIS
# ============================================================

def _duplicate_values(rows, key):
    seen = {}
    duplicates = []
    for row in rows:
        value = row.get(key)
        if value is None:
            continue
        seen[value] = seen.get(value, 0) + 1
    for value in sorted(seen.keys()):
        if seen[value] > 1:
            duplicates.append({"value": value, "count": seen[value]})
    return duplicates


def _analyze_commands(commands, strings):
    counts = {}
    categories = {}
    pages = set()
    groups = set()
    warnings = []
    max_x = None
    max_y = None

    for row in commands:
        command = row.get("command", "unknown")
        category = row.get("category", "unknown")
        counts[command] = counts.get(command, 0) + 1
        categories[category] = categories.get(category, 0) + 1
        if row.get("page") is not None:
            pages.add(row.get("page"))
        if row.get("group") is not None:
            groups.add(row.get("group"))
        if row.get("parse_error"):
            warnings.append("Command {0}: {1}".format(row.get("index"), row.get("parse_error")))
        try:
            right = int(row.get("x", 0)) + int(row.get("width", 0) or 0)
            max_x = right if max_x is None else max(max_x, right)
        except:
            pass
        try:
            bottom = int(row.get("y", 0)) + int(row.get("height", 0) or 0)
            max_y = bottom if max_y is None else max(max_y, bottom)
        except:
            pass

    buttons = [row for row in commands if row.get("category") == "button"]
    inputs = [row for row in commands if row.get("category") == "input"]
    switches = [row for row in commands if row.get("category") == "switch"]
    text_controls = [row for row in commands if row.get("category") in ("text", "localized_text")]
    art_controls = [row for row in commands if row.get("category") == "art"]
    unknown = [row for row in commands if row.get("category") == "unknown"]

    duplicate_button_ids = _duplicate_values(buttons, "button_id")
    duplicate_entry_ids = _duplicate_values(inputs, "entry_id")
    duplicate_switch_ids = _duplicate_values(switches, "switch_id")
    if duplicate_button_ids:
        warnings.append("Duplicate button IDs: " + _clean_text(duplicate_button_ids))
    if duplicate_entry_ids:
        warnings.append("Duplicate text-entry IDs: " + _clean_text(duplicate_entry_ids))
    if duplicate_switch_ids:
        warnings.append("Duplicate switch IDs: " + _clean_text(duplicate_switch_ids))
    if unknown:
        warnings.append("{0} unrecognized layout command(s) were retained raw.".format(len(unknown)))

    return {
        "command_count": len(commands),
        "command_counts": counts,
        "category_counts": categories,
        "pages": sorted(pages),
        "groups": sorted(groups),
        "estimated_bounds": {"width": max_x, "height": max_y},
        "buttons": buttons,
        "inputs": inputs,
        "switches": switches,
        "text_controls": text_controls,
        "art_controls": art_controls,
        "unknown_commands": unknown,
        "duplicate_button_ids": duplicate_button_ids,
        "duplicate_entry_ids": duplicate_entry_ids,
        "duplicate_switch_ids": duplicate_switch_ids,
        "string_count": len(strings),
        "warnings": warnings,
    }


# ============================================================
# GUMP CAPTURE
# ============================================================

def _trim_string_table(values):
    output = list(values)
    while output and output[-1] is None:
        output.pop()
    return output


def _known_gump_fields(gump_data):
    names = (
        "gumpId", "serial", "x", "y", "gumpDefinition", "gumpStrings",
        "hasResponse", "buttonid", "switches", "text", "textID",
        "gumpLayout", "gumpText", "gumpData", "layoutPieces", "stringList"
    )
    result = {}
    for name in names:
        try:
            result[name] = _json_value(getattr(gump_data, name))
        except Exception as error:
            result[name] = {"read_error": _clean_text(error)}
    return result


def _capture_gump(gump_id):
    errors = []
    gump_data = None
    try:
        gump_data = Gumps.GetGumpData(gump_id)
    except Exception as error:
        errors.append("GetGumpData: " + _clean_text(error))
    if gump_data is None:
        raise ValueError(
            "Gump {0} is not present in Razor Enhanced's open-gump cache.".format(_hex(gump_id))
        )

    known = _known_gump_fields(gump_data)
    api_raw_layout = _api_probe(
        "GetGumpRawLayout", lambda: Gumps.GetGumpRawLayout(gump_id), errors
    )
    member_layout = known.get("gumpLayout") or known.get("gumpDefinition") or ""
    raw_layout = api_raw_layout or member_layout

    raw_string_table = known.get("stringList") or known.get("gumpStrings") or []
    if not isinstance(raw_string_table, list):
        raw_string_table = []
    string_table = _trim_string_table(raw_string_table)
    commands = _parse_layout(raw_layout, string_table)
    _annotate_nearby_labels(commands)
    analysis = _analyze_commands(commands, string_table)

    api = {
        "all_gump_ids_at_capture": _api_probe("AllGumpIDs", Gumps.AllGumpIDs, errors),
        "current_gump_at_capture": _api_probe("CurrentGump", Gumps.CurrentGump, errors),
        "has_gump_by_id": _api_probe("HasGump(id)", lambda: Gumps.HasGump(gump_id), errors),
        "line_list_all": _api_probe(
            "GetLineList(all)", lambda: Gumps.GetLineList(gump_id, False), errors
        ),
        "line_list_data_only": _api_probe(
            "GetLineList(dataOnly)", lambda: Gumps.GetLineList(gump_id, True), errors
        ),
        "gump_text_translated_clilocs": _api_probe(
            "GetGumpText", lambda: Gumps.GetGumpText(gump_id), errors
        ),
        "api_named_raw_text": _api_probe(
            "GetGumpRawText", lambda: Gumps.GetGumpRawText(gump_id), errors
        ),
        "resolved_string_pieces": _api_probe(
            "GetResolvedStringPieces", lambda: Gumps.GetResolvedStringPieces(gump_id), errors
        ),
        "raw_layout": api_raw_layout,
    }

    current_id = int(api.get("current_gump_at_capture") or 0)
    current_only = {
        "qualified": current_id == gump_id,
        "warning": "These LastGump values are only trusted when CurrentGump matched the target ID.",
        "last_gump_raw_layout": None,
        "last_gump_lines": None,
        "last_gump_tiles": None,
    }
    if current_only["qualified"]:
        current_only["last_gump_raw_layout"] = _api_probe(
            "LastGumpRawLayout", Gumps.LastGumpRawLayout, errors
        )
        current_only["last_gump_lines"] = _api_probe(
            "LastGumpGetLineList", Gumps.LastGumpGetLineList, errors
        )
        current_only["last_gump_tiles"] = _api_probe(
            "LastGumpTile", Gumps.LastGumpTile, errors
        )

    response = {
        "has_response": bool(known.get("hasResponse", False)),
        "button_id": known.get("buttonid"),
        "switch_ids": known.get("switches") or [],
        "text_entry_ids": known.get("textID") or [],
        "text_entry_values": known.get("text") or [],
    }
    response["text_entries"] = []
    for index, entry_id in enumerate(response["text_entry_ids"]):
        value = response["text_entry_values"][index] if index < len(response["text_entry_values"]) else None
        response["text_entries"].append({"entry_id": entry_id, "value": value})

    if not raw_layout:
        analysis["warnings"].append("No raw layout was returned; controls could not be mapped.")
    if errors:
        analysis["warnings"].extend(errors)

    captured_at = datetime.datetime.now()
    return {
        "tool": {
            "name": "Frog Gump Inspector",
            "version": "1.0",
            "captured_at_local": captured_at.isoformat(),
            "razor_notes": [
                "stringList is the closest exposed copy of the incoming raw string table.",
                "GetGumpRawText is deprecated/misnamed in this Razor build and returns translated gumpText.",
                "LastGump values are included only when CurrentGump matched the inspected ID.",
                "Estimated bounds are derived from controls with explicit dimensions; artwork can extend farther.",
            ],
        },
        "identity": {
            "gump_id": int(gump_id),
            "gump_id_hex": _hex(gump_id),
            "serial": int(known.get("serial") or 0),
            "serial_hex": _hex(known.get("serial") or 0),
            "x": known.get("x"),
            "y": known.get("y"),
            "runtime_type": _runtime_type(gump_data),
        },
        "hashes": {
            "layout_sha256": _sha256_text(raw_layout),
            "string_table_sha256": _sha256_text(json.dumps(string_table, ensure_ascii=False)),
            "layout_and_strings_sha256": _sha256_text(
                raw_layout + "\n" + json.dumps(string_table, ensure_ascii=False)
            ),
        },
        "raw": {
            "layout": raw_layout,
            "layout_from_api": api_raw_layout,
            "layout_from_member": member_layout,
            "layout_pieces_from_razor": known.get("layoutPieces") or [],
            "string_table_raw_with_razor_slack": raw_string_table,
            "string_table_effective": string_table,
            "gump_strings_member": known.get("gumpStrings") or [],
            "gump_text_member": known.get("gumpText") or [],
            "gump_data_member": known.get("gumpData") or [],
        },
        "commands": commands,
        "analysis": analysis,
        "response": response,
        "api_probes": api,
        "current_only_probes": current_only,
        "known_gump_data_fields": known,
        "public_reflection": _reflect_public_members(gump_data),
        "deep_reflection": _reflect_all_instance_members(gump_data),
        "capture_errors": errors,
    }


def _inspect_gump(gump_id):
    global _snapshot
    global _current_gump_id
    global _id_input
    try:
        snapshot = _capture_gump(int(gump_id))
        _snapshot = snapshot
        _current_gump_id = int(gump_id)
        _id_input = snapshot["identity"]["gump_id_hex"]
        analysis = snapshot["analysis"]
        _set_status(
            "Captured {0}: {1} commands, {2} buttons, {3} inputs/switches.".format(
                snapshot["identity"]["gump_id_hex"],
                analysis["command_count"],
                len(analysis["buttons"]),
                len(analysis["inputs"]) + len(analysis["switches"])
            ),
            SUCCESS_HUE
        )
        return True
    except Exception as error:
        _set_status("Capture failed: " + _clean_text(error), ERROR_HUE)
        return False


# ============================================================
# ANNOTATED RAW EXPORTS
# ============================================================

def _format_control(row):
    values = []
    for key in CONTROL_COLUMNS:
        value = row.get(key)
        if value is not None and value != "":
            values.append("{0}={1}".format(key, _clean_text(value)))
    return " | ".join(values)


def _human_report(snapshot):
    identity = snapshot["identity"]
    analysis = snapshot["analysis"]
    response = snapshot["response"]
    lines = [
        "FROG GUMP INSPECTOR - ANNOTATED CAPTURE",
        "=" * 78,
        "Captured: {0}".format(snapshot["tool"]["captured_at_local"]),
        "Gump ID: {0} / {1}".format(identity["gump_id_hex"], identity["gump_id"]),
        "Serial: {0} / {1}".format(identity["serial_hex"], identity["serial"]),
        "Screen origin: x={0}, y={1}".format(identity["x"], identity["y"]),
        "Runtime type: {0}".format(identity["runtime_type"]),
        "Layout SHA-256: {0}".format(snapshot["hashes"]["layout_sha256"]),
        "Layout+strings SHA-256: {0}".format(snapshot["hashes"]["layout_and_strings_sha256"]),
        "",
        "WHAT THE CAPTURE FOUND",
        "-" * 78,
        "Commands: {0}".format(analysis["command_count"]),
        "Command types: {0}".format(json.dumps(analysis["command_counts"], sort_keys=True)),
        "Pages: {0}".format(analysis["pages"]),
        "Radio groups: {0}".format(analysis["groups"]),
        "Buttons: {0}".format(len(analysis["buttons"])),
        "Text inputs: {0}".format(len(analysis["inputs"])),
        "Switches: {0}".format(len(analysis["switches"])),
        "Text controls: {0}".format(len(analysis["text_controls"])),
        "Art controls: {0}".format(len(analysis["art_controls"])),
        "Effective string-table entries: {0}".format(analysis["string_count"]),
        "Estimated bounds: {0}".format(analysis["estimated_bounds"]),
        "",
    ]

    if analysis["warnings"]:
        lines.extend(["WARNINGS", "-" * 78])
        for warning in analysis["warnings"]:
            lines.append("- " + _clean_text(warning))
        lines.append("")

    lines.extend([
        "BUTTON MAP",
        "-" * 78,
        "button_type 0 = local Page navigation; button_type 1 = server/script Reply.",
        "nearby_label is a geometric inference from text on the same visible page, not packet metadata.",
    ])
    if not analysis["buttons"]:
        lines.append("No button commands were parsed.")
    for row in analysis["buttons"]:
        lines.append(_format_control(row))

    lines.extend(["", "INPUT MAP", "-" * 78])
    if not analysis["inputs"] and not analysis["switches"]:
        lines.append("No textentry, checkbox, or radio commands were parsed.")
    for row in analysis["inputs"] + analysis["switches"]:
        lines.append(_format_control(row))

    lines.extend(["", "RESPONSE STATE", "-" * 78])
    lines.append(json.dumps(response, indent=2, ensure_ascii=False, sort_keys=True))
    lines.extend(["", "ALL PARSED LAYOUT COMMANDS", "-" * 78])
    for row in snapshot["commands"]:
        lines.append(_format_control(row))

    lines.extend(["", "STRING TABLE", "-" * 78])
    for index, value in enumerate(snapshot["raw"]["string_table_effective"]):
        lines.append("[{0}] {1}".format(index, _clean_text(value)))

    lines.extend(["", "RAZOR API PROBES", "-" * 78])
    lines.append(json.dumps(snapshot["api_probes"], indent=2, ensure_ascii=False, sort_keys=True))
    lines.extend(["", "CURRENT-ONLY PROBES", "-" * 78])
    lines.append(json.dumps(snapshot["current_only_probes"], indent=2, ensure_ascii=False, sort_keys=True))
    lines.extend(["", "KNOWN GUMPDATA FIELDS", "-" * 78])
    lines.append(json.dumps(snapshot["known_gump_data_fields"], indent=2, ensure_ascii=False, sort_keys=True))
    lines.extend(["", "DEEP .NET REFLECTION", "-" * 78])
    lines.append(json.dumps(snapshot["deep_reflection"], indent=2, ensure_ascii=False, sort_keys=True))
    lines.extend(["", "RAW LAYOUT", "-" * 78, snapshot["raw"]["layout"]])
    return "\n".join(lines) + "\n"


# ============================================================
# SELF-CONTAINED XLSX WRITER
# ============================================================

def _xml_escape(value):
    text = _clean_text(value)
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))


def _excel_text(value):
    text = _clean_text(value)
    if len(text) > 32700:
        text = text[:32620] + " [truncated here; full value is in raw JSON]"
    return text


def _excel_column_name(number):
    output = ""
    value = int(number)
    while value > 0:
        value, remainder = divmod(value - 1, 26)
        output = chr(65 + remainder) + output
    return output


def _cell_xml(row_number, column_number, value, style_id=0):
    reference = _excel_column_name(column_number) + str(row_number)
    style = " s=\"{0}\"".format(style_id) if style_id else ""
    if value is None:
        return "<c r=\"{0}\"{1}/>".format(reference, style)
    if isinstance(value, bool):
        return "<c r=\"{0}\" t=\"b\"{1}><v>{2}</v></c>".format(
            reference, style, 1 if value else 0
        )
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return "<c r=\"{0}\"{1}><v>{2}</v></c>".format(reference, style, value)
    text = _xml_escape(_excel_text(value))
    return (
        "<c r=\"{0}\" t=\"inlineStr\"{1}><is><t xml:space=\"preserve\">"
        "{2}</t></is></c>"
    ).format(reference, style, text)


def _column_widths(rows):
    count = max([len(row) for row in rows] or [1])
    widths = []
    for column in range(count):
        maximum = 8
        for row in rows[:1000]:
            value = row[column] if column < len(row) else ""
            text = _clean_text(value).replace("\n", " ")
            maximum = max(maximum, min(len(text) + 2, 60))
        widths.append(maximum)
    return widths


def _sheet_xml(rows, header_rows, freeze_rows, auto_filter_row=None):
    widths = _column_widths(rows)
    columns = []
    for index, width in enumerate(widths):
        columns.append(
            "<col min=\"{0}\" max=\"{0}\" width=\"{1}\" customWidth=\"1\"/>".format(
                index + 1, width
            )
        )
    sheet_rows = []
    for row_index, row in enumerate(rows):
        excel_row = row_index + 1
        cells = []
        if excel_row == 1 and excel_row not in header_rows:
            style_id = 1
        elif excel_row in header_rows:
            style_id = 2
        else:
            style_id = 0
        for column_index, value in enumerate(row):
            cells.append(_cell_xml(excel_row, column_index + 1, value, style_id))
        sheet_rows.append("<row r=\"{0}\">{1}</row>".format(excel_row, "".join(cells)))

    panes = ""
    if freeze_rows:
        panes = (
            "<pane ySplit=\"{0}\" topLeftCell=\"A{1}\" activePane=\"bottomLeft\" "
            "state=\"frozen\"/>"
        ).format(freeze_rows, freeze_rows + 1)
    auto_filter = ""
    if auto_filter_row and len(rows) >= auto_filter_row:
        max_col = max([len(row) for row in rows] or [1])
        auto_filter = "<autoFilter ref=\"A{0}:{1}{2}\"/>".format(
            auto_filter_row, _excel_column_name(max_col), len(rows)
        )
    dimension = "A1:{0}{1}".format(
        _excel_column_name(max([len(row) for row in rows] or [1])), max(len(rows), 1)
    )
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
        "<dimension ref=\"{0}\"/><sheetViews><sheetView workbookViewId=\"0\" "
        "showGridLines=\"0\">{1}</sheetView></sheetViews>"
        "<sheetFormatPr defaultRowHeight=\"15\"/><cols>{2}</cols><sheetData>{3}</sheetData>{4}"
        "</worksheet>"
    ).format(dimension, panes, "".join(columns), "".join(sheet_rows), auto_filter)


def _flatten_json(value, prefix="", rows=None, depth=0):
    if rows is None:
        rows = []
    if depth > 8:
        rows.append([prefix, _clean_text(value), _runtime_type(value)])
        return rows
    if isinstance(value, dict):
        for key in sorted(value.keys()):
            child = (prefix + "." + _clean_text(key)).strip(".")
            _flatten_json(value[key], child, rows, depth + 1)
    elif isinstance(value, list):
        for index, entry in enumerate(value):
            _flatten_json(entry, "{0}[{1}]".format(prefix, index), rows, depth + 1)
    else:
        rows.append([prefix, value, _runtime_type(value)])
    return rows


def _overview_rows(snapshot):
    identity = snapshot["identity"]
    analysis = snapshot["analysis"]
    fields = [
        ["Frog Gump Inspector Capture", "", ""],
        ["", "", ""],
        ["Field", "Value", "What it means"],
        ["Captured", snapshot["tool"]["captured_at_local"], "Local time when Razor's cached gump state was sampled."],
        ["Gump ID", identity["gump_id_hex"], "Layout/type ID used to identify this gump."],
        ["Gump ID decimal", identity["gump_id"], "Same gump ID in decimal for API calls."],
        ["Serial", identity["serial_hex"], "Owner/context serial sent with the gump packet; it may be a player, item, or zero."],
        ["Origin X", identity["x"], "Client screen X position supplied by the gump packet."],
        ["Origin Y", identity["y"], "Client screen Y position supplied by the gump packet."],
        ["Commands", analysis["command_count"], "Number of braced layout commands parsed."],
        ["Pages", len(analysis["pages"]), "Distinct page contexts discovered in the layout."],
        ["Buttons", len(analysis["buttons"]), "button and buttontileart controls."],
        ["Text inputs", len(analysis["inputs"]), "textentry and textentrylimited controls."],
        ["Switches", len(analysis["switches"]), "checkbox and radio controls."],
        ["Text controls", len(analysis["text_controls"]), "String-table and cliloc-backed text regions."],
        ["Art controls", len(analysis["art_controls"]), "Gump-art and item-art commands."],
        ["String entries", analysis["string_count"], "Effective incoming string table after Razor allocation slack is removed."],
        ["Estimated width", analysis["estimated_bounds"].get("width"), "Largest x + explicit width; art without dimensions may exceed it."],
        ["Estimated height", analysis["estimated_bounds"].get("height"), "Largest y + explicit height; art without dimensions may exceed it."],
        ["Layout SHA-256", snapshot["hashes"]["layout_sha256"], "Stable fingerprint for raw layout comparison."],
        ["Layout + strings SHA-256", snapshot["hashes"]["layout_and_strings_sha256"], "Fingerprint that changes when layout or string-table data changes."],
    ]
    for index, warning in enumerate(analysis["warnings"]):
        fields.append(["Warning {0}".format(index + 1), warning, "Capture/parser diagnostic; inspect raw JSON before scripting around it."])
    return fields


def _control_rows(snapshot, selected=None):
    rows = [list(CONTROL_COLUMNS)]
    source = snapshot["commands"] if selected is None else selected
    for command in source:
        rows.append([command.get(column) for column in CONTROL_COLUMNS])
    return rows


def _workbook_sheets(snapshot):
    analysis = snapshot["analysis"]
    strings = snapshot["raw"]["string_table_effective"]
    raw_strings = snapshot["raw"]["string_table_raw_with_razor_slack"]
    string_rows = [["Index", "Effective text", "Raw slot", "Notes"]]
    maximum = max(len(strings), len(raw_strings))
    for index in range(maximum):
        effective = strings[index] if index < len(strings) else None
        raw = raw_strings[index] if index < len(raw_strings) else None
        note = "Razor allocation slack" if index >= len(strings) else "String-table value"
        string_rows.append([index, effective, raw, note])

    response_rows = [["Field", "Value", "Meaning"]]
    response = snapshot["response"]
    response_rows.extend([
        ["has_response", response["has_response"], "True when this GumpData has received a reply."],
        ["button_id", response["button_id"], "Button ID returned by the latest reply."],
        ["switch_ids", json.dumps(response["switch_ids"]), "Selected checkbox/radio IDs in the reply."],
    ])
    for entry in response["text_entries"]:
        response_rows.append([
            "text entry " + _clean_text(entry.get("entry_id")),
            entry.get("value"),
            "Submitted value paired from GumpData.textID and GumpData.text."
        ])

    api_rows = [["Path", "Value", "Runtime type"]]
    _flatten_json({
        "api_probes": snapshot["api_probes"],
        "current_only_probes": snapshot["current_only_probes"],
        "known_gump_data_fields": snapshot["known_gump_data_fields"],
        "public_reflection": snapshot["public_reflection"],
        "deep_reflection": snapshot["deep_reflection"],
    }, "", api_rows)

    raw_rows = [["Command index", "Page", "Group", "Command", "Raw command"]]
    for row in snapshot["commands"]:
        raw_rows.append([
            row.get("index"), row.get("page"), row.get("group"),
            row.get("command"), row.get("raw")
        ])

    return [
        {"name": "Overview", "rows": _overview_rows(snapshot), "headers": [3], "freeze": 3, "filter": 3},
        {"name": "Controls", "rows": _control_rows(snapshot), "headers": [1], "freeze": 1, "filter": 1},
        {"name": "Buttons", "rows": _control_rows(snapshot, analysis["buttons"]), "headers": [1], "freeze": 1, "filter": 1},
        {"name": "Inputs", "rows": _control_rows(snapshot, analysis["inputs"]), "headers": [1], "freeze": 1, "filter": 1},
        {"name": "Switches", "rows": _control_rows(snapshot, analysis["switches"]), "headers": [1], "freeze": 1, "filter": 1},
        {"name": "Strings", "rows": string_rows, "headers": [1], "freeze": 1, "filter": 1},
        {"name": "Response", "rows": response_rows, "headers": [1], "freeze": 1, "filter": 1},
        {"name": "API Probes", "rows": api_rows, "headers": [1], "freeze": 1, "filter": 1},
        {"name": "Raw Layout", "rows": raw_rows, "headers": [1], "freeze": 1, "filter": 1},
    ]


def _write_xlsx(snapshot, path):
    sheets = _workbook_sheets(snapshot)
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    content_overrides = []
    workbook_sheets = []
    relationships = []
    app_titles = []
    for index, sheet in enumerate(sheets):
        number = index + 1
        content_overrides.append(
            "<Override PartName=\"/xl/worksheets/sheet{0}.xml\" "
            "ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>".format(number)
        )
        workbook_sheets.append(
            "<sheet name=\"{0}\" sheetId=\"{1}\" r:id=\"rId{1}\"/>".format(
                _xml_escape(sheet["name"]), number
            )
        )
        relationships.append(
            "<Relationship Id=\"rId{0}\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" "
            "Target=\"worksheets/sheet{0}.xml\"/>".format(number)
        )
        app_titles.append("<vt:lpstr>{0}</vt:lpstr>".format(_xml_escape(sheet["name"])))
    relationships.append(
        "<Relationship Id=\"rId{0}\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles\" "
        "Target=\"styles.xml\"/>".format(len(sheets) + 1)
    )

    content_types = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
        "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>"
        "<Default Extension=\"xml\" ContentType=\"application/xml\"/>"
        "<Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>"
        "<Override PartName=\"/xl/styles.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml\"/>"
        "<Override PartName=\"/docProps/core.xml\" ContentType=\"application/vnd.openxmlformats-package.core-properties+xml\"/>"
        "<Override PartName=\"/docProps/app.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.extended-properties+xml\"/>"
        "{0}</Types>"
    ).format("".join(content_overrides))
    root_rels = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
        "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"xl/workbook.xml\"/>"
        "<Relationship Id=\"rId2\" Type=\"http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties\" Target=\"docProps/core.xml\"/>"
        "<Relationship Id=\"rId3\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties\" Target=\"docProps/app.xml\"/>"
        "</Relationships>"
    )
    workbook = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" "
        "xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">"
        "<sheets>{0}</sheets></workbook>"
    ).format("".join(workbook_sheets))
    workbook_rels = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
        "{0}</Relationships>"
    ).format("".join(relationships))
    styles = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<styleSheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
        "<fonts count=\"3\"><font><sz val=\"10\"/><name val=\"Arial\"/></font>"
        "<font><b/><sz val=\"14\"/><color rgb=\"FF1F4E3D\"/><name val=\"Arial\"/></font>"
        "<font><b/><sz val=\"10\"/><color rgb=\"FFFFFFFF\"/><name val=\"Arial\"/></font></fonts>"
        "<fills count=\"3\"><fill><patternFill patternType=\"none\"/></fill>"
        "<fill><patternFill patternType=\"gray125\"/></fill>"
        "<fill><patternFill patternType=\"solid\"><fgColor rgb=\"FF355E4A\"/><bgColor indexed=\"64\"/></patternFill></fill></fills>"
        "<borders count=\"2\"><border><left/><right/><top/><bottom/><diagonal/></border>"
        "<border><left/><right/><top/><bottom style=\"thin\"><color rgb=\"FFD9E2DC\"/></bottom><diagonal/></border></borders>"
        "<cellStyleXfs count=\"1\"><xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"0\"/></cellStyleXfs>"
        "<cellXfs count=\"3\"><xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"0\" xfId=\"0\" applyAlignment=\"1\"><alignment vertical=\"center\"/></xf>"
        "<xf numFmtId=\"0\" fontId=\"1\" fillId=\"0\" borderId=\"0\" xfId=\"0\" applyFont=\"1\"/>"
        "<xf numFmtId=\"0\" fontId=\"2\" fillId=\"2\" borderId=\"1\" xfId=\"0\" applyFont=\"1\" applyFill=\"1\" applyBorder=\"1\" applyAlignment=\"1\"><alignment horizontal=\"center\" vertical=\"center\"/></xf></cellXfs>"
        "<cellStyles count=\"1\"><cellStyle name=\"Normal\" xfId=\"0\" builtinId=\"0\"/></cellStyles>"
        "</styleSheet>"
    )
    core = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<cp:coreProperties xmlns:cp=\"http://schemas.openxmlformats.org/package/2006/metadata/core-properties\" "
        "xmlns:dc=\"http://purl.org/dc/elements/1.1/\" xmlns:dcterms=\"http://purl.org/dc/terms/\" "
        "xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">"
        "<dc:title>Frog Gump Inspector Capture</dc:title><dc:creator>Frog Gump Inspector</dc:creator>"
        "<dcterms:created xsi:type=\"dcterms:W3CDTF\">{0}</dcterms:created>"
        "</cp:coreProperties>"
    ).format(timestamp)
    app = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<Properties xmlns=\"http://schemas.openxmlformats.org/officeDocument/2006/extended-properties\" "
        "xmlns:vt=\"http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes\">"
        "<Application>Frog Gump Inspector</Application><TitlesOfParts><vt:vector size=\"{0}\" baseType=\"lpstr\">{1}</vt:vector></TitlesOfParts>"
        "</Properties>"
    ).format(len(sheets), "".join(app_titles))

    temporary = path + ".tmp"
    # ZIP_STORED avoids depending on a native zlib module inside IronPython.
    archive = zipfile.ZipFile(temporary, "w", zipfile.ZIP_STORED)
    try:
        archive.writestr("[Content_Types].xml", content_types.encode("utf-8"))
        archive.writestr("_rels/.rels", root_rels.encode("utf-8"))
        archive.writestr("xl/workbook.xml", workbook.encode("utf-8"))
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels.encode("utf-8"))
        archive.writestr("xl/styles.xml", styles.encode("utf-8"))
        archive.writestr("docProps/core.xml", core.encode("utf-8"))
        archive.writestr("docProps/app.xml", app.encode("utf-8"))
        for index, sheet in enumerate(sheets):
            xml = _sheet_xml(
                sheet["rows"], sheet["headers"], sheet["freeze"], sheet["filter"]
            )
            archive.writestr(
                "xl/worksheets/sheet{0}.xml".format(index + 1), xml.encode("utf-8")
            )
    finally:
        archive.close()
    if os.path.exists(path):
        os.remove(path)
    os.rename(temporary, path)


def _export_snapshot(snapshot):
    identity = snapshot["identity"]
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    prefix = "{0}_{1}_gump".format(stamp, identity["gump_id_hex"].replace("0x", ""))
    folder = _output_dir()
    paths = {
        "json": os.path.join(folder, prefix + "_raw.json"),
        "text": os.path.join(folder, prefix + "_report.txt"),
        "layout": os.path.join(folder, prefix + "_layout.txt"),
        "xlsx": os.path.join(folder, prefix + ".xlsx"),
    }
    _write_text(paths["json"], json.dumps(
        snapshot, indent=2, ensure_ascii=False, sort_keys=True
    ) + "\n")
    _write_text(paths["text"], _human_report(snapshot))
    _write_text(paths["layout"], snapshot["raw"]["layout"] + "\n")
    _write_xlsx(snapshot, paths["xlsx"])
    return paths


# ============================================================
# GUMP DISPLAY
# ============================================================

def _summary_html(snapshot):
    if not snapshot:
        open_ids = [_hex(value) for value in _open_gump_ids()]
        return _html_lines([
            "<basefont color={0}>No gump captured yet.</basefont>".format(HTML_SECTION_COLOR),
            "Enter an ID as decimal or 0xHEX, or use CAPTURE NEXT before opening the target gump.",
            "Open external IDs: " + _html_escape(", ".join(open_ids) if open_ids else "none"),
            "CAPTURE OPEN uses the most recent non-inspector gump Razor has observed.",
        ])
    identity = snapshot["identity"]
    analysis = snapshot["analysis"]
    lines = [
        "<basefont color={0}>Identity</basefont>".format(HTML_SECTION_COLOR),
        "<basefont color={0}>Gump ID:</basefont> <basefont color={1}>{2} / {3}</basefont>".format(
            HTML_LABEL_COLOR, HTML_VALUE_COLOR, identity["gump_id_hex"], identity["gump_id"]
        ),
        "<basefont color={0}>Serial:</basefont> <basefont color={1}>{2} / {3}</basefont>".format(
            HTML_LABEL_COLOR, HTML_VALUE_COLOR, identity["serial_hex"], identity["serial"]
        ),
        "Origin: {0}, {1}; runtime={2}".format(identity["x"], identity["y"], identity["runtime_type"]),
        "<basefont color={0}>Mapped structure</basefont>".format(HTML_SECTION_COLOR),
        "{0} commands; pages={1}; groups={2}".format(
            analysis["command_count"], analysis["pages"], analysis["groups"]
        ),
        "{0} buttons; {1} text inputs; {2} switches; {3} text; {4} art".format(
            len(analysis["buttons"]), len(analysis["inputs"]), len(analysis["switches"]),
            len(analysis["text_controls"]), len(analysis["art_controls"])
        ),
        "Strings={0}; estimated bounds={1}".format(
            analysis["string_count"], _html_escape(analysis["estimated_bounds"])
        ),
        "Layout hash: " + snapshot["hashes"]["layout_sha256"],
    ]
    if analysis["warnings"]:
        lines.append("<basefont color={0}>Warnings</basefont>".format(HTML_ERROR_COLOR))
        for warning in analysis["warnings"][:12]:
            lines.append(_html_escape(warning))
    return _html_lines(lines)


def _controls_html(snapshot):
    if not snapshot:
        return _summary_html(snapshot)
    lines = [
        "<basefont color={0}>All parsed layout commands</basefont>".format(HTML_SECTION_COLOR),
        "Each command retains its raw text, page/group context, mapped fields, and our interpretation.",
    ]
    for row in snapshot["commands"][:MAX_GUI_ROWS]:
        lines.append(
            "<basefont color={0}>[{1}] p{2} g{3} {4}</basefont> "
            "<basefont color={5}>{6}</basefont>".format(
                HTML_LABEL_COLOR, row.get("index"), row.get("page"), row.get("group"),
                _html_escape(row.get("command")), HTML_VALUE_COLOR,
                _html_escape(_short(_format_control(row), 260))
            )
        )
        lines.append("<basefont color={0}>  -- {1}</basefont>".format(
            HTML_COMMENT_COLOR, _html_escape(row.get("meaning"))
        ))
    if len(snapshot["commands"]) > MAX_GUI_ROWS:
        lines.append("SAVE BUNDLE contains all {0} commands.".format(len(snapshot["commands"])))
    return _html_lines(lines)


def _buttons_html(snapshot):
    if not snapshot:
        return _summary_html(snapshot)
    buttons = snapshot["analysis"]["buttons"]
    lines = [
        "<basefont color={0}>Button map</basefont>".format(HTML_SECTION_COLOR),
        "Page buttons navigate locally. Reply buttons submit button_id to the server/script.",
        "The nearby label is an explicitly marked spatial guess from adjacent text.",
    ]
    if not buttons:
        lines.append("No button or buttontileart commands found.")
    for row in buttons[:MAX_GUI_ROWS]:
        lines.append(
            "<basefont color={0}>ID {1}</basefont> at {2},{3} | {4} | param={5} | art={6}/{7} | page={8} group={9} | label={10}".format(
                HTML_LABEL_COLOR, row.get("button_id"), row.get("x"), row.get("y"),
                row.get("button_type_name", row.get("button_type")), row.get("param"),
                row.get("normal_art"), row.get("pressed_art"), row.get("page"), row.get("group"),
                _html_escape(row.get("nearby_label", ""))
            )
        )
        lines.append("  action: " + _html_escape(row.get("action", "")))
        if row.get("tooltip_cliloc"):
            lines.append("  tooltip cliloc={0} args={1}".format(
                row.get("tooltip_cliloc"), _html_escape(row.get("tooltip_args"))
            ))
    return _html_lines(lines)


def _inputs_html(snapshot):
    if not snapshot:
        return _summary_html(snapshot)
    analysis = snapshot["analysis"]
    lines = [
        "<basefont color={0}>Inputs and switches</basefont>".format(HTML_SECTION_COLOR),
        "entry_id identifies submitted text; switch_id identifies selected checkbox/radio values.",
    ]
    for row in analysis["inputs"]:
        lines.append(
            "<basefont color={0}>{1} entry {2}</basefont> at {3},{4} size {5}x{6} hue={7} default[{8}]={9} max={10} label={11}".format(
                HTML_LABEL_COLOR, row.get("command"), row.get("entry_id"), row.get("x"), row.get("y"),
                row.get("width"), row.get("height"), row.get("hue"), row.get("text_index"),
                _html_escape(_short(row.get("resolved_text"), 120)), row.get("max_length"),
                _html_escape(row.get("nearby_label", ""))
            )
        )
    for row in analysis["switches"]:
        lines.append(
            "<basefont color={0}>{1} switch {2}</basefont> at {3},{4} initial={5} art={6}/{7} page={8} group={9} label={10}".format(
                HTML_LABEL_COLOR, row.get("command"), row.get("switch_id"), row.get("x"), row.get("y"),
                row.get("initial_state"), row.get("normal_art"), row.get("pressed_art"),
                row.get("page"), row.get("group"), _html_escape(row.get("nearby_label", ""))
            )
        )
    response = snapshot["response"]
    lines.append("<basefont color={0}>Cached response state</basefont>".format(HTML_SECTION_COLOR))
    lines.append(_html_escape(json.dumps(response, ensure_ascii=False, sort_keys=True)))
    return _html_lines(lines)


def _text_html(snapshot):
    if not snapshot:
        return _summary_html(snapshot)
    lines = [
        "<basefont color={0}>Effective raw string table</basefont>".format(HTML_SECTION_COLOR),
        "Indices are what text, croppedtext, htmlgump, and textentry commands reference.",
    ]
    for index, value in enumerate(snapshot["raw"]["string_table_effective"][:MAX_GUI_ROWS]):
        lines.append("<basefont color={0}>[{1}]</basefont> {2}".format(
            HTML_LABEL_COLOR, index, _html_escape(_short(value, 240))
        ))
    lines.append("<basefont color={0}>Translated cliloc/API text</basefont>".format(HTML_SECTION_COLOR))
    for index, value in enumerate((snapshot["api_probes"].get("line_list_all") or [])[:MAX_GUI_ROWS]):
        lines.append("line[{0}] {1}".format(index, _html_escape(_short(value, 240))))
    return _html_lines(lines)


def _raw_html(snapshot):
    if not snapshot:
        return _summary_html(snapshot)
    lines = [
        "<basefont color={0}>Raw layout</basefont>".format(HTML_SECTION_COLOR),
        _html_escape(_short(snapshot["raw"]["layout"], 9000)),
        "<basefont color={0}>Capture notes</basefont>".format(HTML_SECTION_COLOR),
    ]
    for note in snapshot["tool"]["razor_notes"]:
        lines.append("-- " + _html_escape(note))
    lines.append("<basefont color={0}>Public GumpData fields</basefont>".format(HTML_SECTION_COLOR))
    for name in sorted(snapshot["public_reflection"]["fields"].keys()):
        lines.append("{0}: {1}".format(
            _html_escape(name), _html_escape(_short(snapshot["public_reflection"]["fields"][name], 220))
        ))
    lines.append("SAVE BUNDLE includes the unabridged JSON, layout, annotated report, and XLSX workbook.")
    return _html_lines(lines)


def _tab_html(snapshot, tab_name):
    if tab_name == "controls":
        return _controls_html(snapshot)
    if tab_name == "buttons":
        return _buttons_html(snapshot)
    if tab_name == "inputs":
        return _inputs_html(snapshot)
    if tab_name == "text":
        return _text_html(snapshot)
    if tab_name == "raw":
        return _raw_html(snapshot)
    return _summary_html(snapshot)


def _add_button(gump, x, y, button_id, label, hue=TEXT_HUE):
    Gumps.AddButton(gump, x, y, 4005, 4007, button_id, 1, 0)
    Gumps.AddLabel(gump, x + 30, y, hue, label)


def _draw_gump():
    global _gump_dirty
    Gumps.CloseGump(GUMP_ID)
    gump = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gump, 0)
    Gumps.AddBackground(gump, 0, 0, GUMP_WIDTH, GUMP_HEIGHT, BACKGROUND_ID)
    Gumps.AddAlphaRegion(gump, 0, 0, GUMP_WIDTH, GUMP_HEIGHT)

    Gumps.AddLabel(gump, 16, 10, TITLE_HUE, "Frog Gump Inspector")
    if _snapshot:
        Gumps.AddLabel(gump, 210, 10, VALUE_HUE, "{0} | serial {1}".format(
            _snapshot["identity"]["gump_id_hex"], _snapshot["identity"]["serial_hex"]
        ))
    Gumps.AddButton(gump, GUMP_WIDTH - 28, 8, 4017, 4019, BTN_CLOSE, 1, 0)

    Gumps.AddLabel(gump, 16, 42, TEXT_HUE, "Gump ID (0xHEX or decimal)")
    Gumps.AddTextEntry(gump, 205, 40, 165, 24, 0, ENTRY_GUMP_ID, _id_input)
    _add_button(gump, 385, 40, BTN_CAPTURE_ID, "CAPTURE ID", SUCCESS_HUE)

    _add_button(gump, 16, 72, BTN_CAPTURE_CURRENT, "CAPTURE OPEN", TEXT_HUE)
    _add_button(gump, 170, 72, BTN_CAPTURE_NEXT, "CAPTURE NEXT", VALUE_HUE)
    _add_button(gump, 325, 72, BTN_REFRESH, "REFRESH", TEXT_HUE)
    _add_button(gump, 435, 72, BTN_SAVE_FILE, "SAVE BUNDLE", SUCCESS_HUE)

    tab_data = (
        (BTN_TAB_SUMMARY, "summary", "Summary", 16),
        (BTN_TAB_CONTROLS, "controls", "Controls", 123),
        (BTN_TAB_BUTTONS, "buttons", "Buttons", 235),
        (BTN_TAB_INPUTS, "inputs", "Inputs", 340),
        (BTN_TAB_TEXT, "text", "Text", 440),
        (BTN_TAB_RAW, "raw", "Raw/API", 530),
    )
    for button_id, tab_name, label, x in tab_data:
        hue = SUCCESS_HUE if _current_tab == tab_name else MUTED_HUE
        _add_button(gump, x, 108, button_id, label, hue)

    Gumps.AddAlphaRegion(gump, 12, 138, GUMP_WIDTH - 24, 340)
    Gumps.AddHtml(
        gump, 18, 144, GUMP_WIDTH - 36, 326,
        _tab_html(_snapshot, _current_tab), False, True
    )
    Gumps.AddLabel(gump, 16, 488, _status_hue, _short(_status_message, 96))
    Gumps.AddLabel(
        gump, 16, 520, MUTED_HUE,
        "Exports: Scripts/FrogDevelopmentTools/data/gumps | Open IDs: {0}".format(len(_open_gump_ids()))
    )
    Gumps.SendGump(
        GUMP_ID, Player.Serial, GUMP_X, GUMP_Y,
        gump.gumpDefinition, gump.gumpStrings
    )
    _gump_dirty = False


# ============================================================
# CAPTURE-NEXT AND BUTTON HANDLING
# ============================================================

def _arm_capture_next():
    global _capture_next_armed
    global _capture_next_started
    global _capture_next_baseline
    _capture_next_baseline = set(_open_gump_ids())
    _capture_next_started = datetime.datetime.now()
    _capture_next_armed = True
    _set_status("Capture-next armed. Trigger the target gump within 30 seconds.", VALUE_HUE)
    Misc.SendMessage(
        "[Frog Gump Inspector] Armed for the next gump. Trigger it now.", VALUE_HUE
    )


def _capture_next_elapsed_ms():
    if _capture_next_started is None:
        return 0
    delta = datetime.datetime.now() - _capture_next_started
    return int(delta.total_seconds() * 1000)


def _poll_capture_next():
    global _capture_next_armed
    global _gump_dirty
    if not _capture_next_armed:
        return

    current = _remember_external_current()
    candidates = []
    if current > 0 and current != GUMP_ID:
        candidates.append(current)
    for gump_id in _open_gump_ids():
        if gump_id not in _capture_next_baseline and gump_id not in candidates:
            candidates.append(gump_id)

    if candidates:
        target = candidates[0]
        _capture_next_armed = False
        _inspect_gump(target)
        _gump_dirty = True
        Misc.SendMessage(
            "[Frog Gump Inspector] Captured next gump " + _hex(target), SUCCESS_HUE
        )
        return

    if _capture_next_elapsed_ms() >= CAPTURE_NEXT_TIMEOUT_MS:
        _capture_next_armed = False
        _set_status("Capture-next timed out after 30 seconds.", ERROR_HUE)
        _gump_dirty = True
        Misc.SendMessage("[Frog Gump Inspector] Capture-next timed out.", ERROR_HUE)


def _read_entry_text(gump_data):
    try:
        value = Gumps.GetTextByID(gump_data, ENTRY_GUMP_ID)
        if value is not None:
            return _clean_text(value)
    except:
        pass
    try:
        ids = list(gump_data.textID)
        values = list(gump_data.text)
        for index, entry_id in enumerate(ids):
            if int(entry_id) == ENTRY_GUMP_ID and index < len(values):
                return _clean_text(values[index])
    except:
        pass
    return _id_input


def _handle_button(button_id, entry_text):
    global _running
    global _current_tab
    global _id_input
    _id_input = entry_text

    if button_id == BTN_CLOSE:
        _running = False
        return
    if button_id == BTN_CAPTURE_ID:
        try:
            target = _parse_uint(entry_text)
            if target == GUMP_ID:
                raise ValueError("That is the inspector's own gump ID.")
            _inspect_gump(target)
        except Exception as error:
            _set_status("Invalid or unavailable ID: " + _clean_text(error), ERROR_HUE)
        return
    if button_id == BTN_CAPTURE_CURRENT:
        target = _last_external_gump_id
        open_ids = _open_gump_ids()
        if target <= 0 or target not in open_ids:
            target = open_ids[-1] if open_ids else 0
        if target <= 0:
            _set_status("No external gump is currently cached. Use CAPTURE NEXT.", ERROR_HUE)
        else:
            _inspect_gump(target)
        return
    if button_id == BTN_CAPTURE_NEXT:
        _arm_capture_next()
        return
    if button_id == BTN_REFRESH:
        if _current_gump_id > 0:
            _inspect_gump(_current_gump_id)
        else:
            _set_status("Capture a gump before refreshing.", ERROR_HUE)
        return
    if button_id == BTN_SAVE_FILE:
        if not _snapshot:
            _set_status("Capture a gump before saving.", ERROR_HUE)
            return
        try:
            _export_snapshot(_snapshot)
            _set_status("Saved XLSX, raw JSON, annotated report, and raw layout.", SUCCESS_HUE)
            Misc.SendMessage(
                "[Frog Gump Inspector] Saved bundle to " + _output_dir(), SUCCESS_HUE
            )
        except Exception as error:
            _set_status("Save failed: " + _clean_text(error), ERROR_HUE)
        return

    tabs = {
        BTN_TAB_SUMMARY: "summary",
        BTN_TAB_CONTROLS: "controls",
        BTN_TAB_BUTTONS: "buttons",
        BTN_TAB_INPUTS: "inputs",
        BTN_TAB_TEXT: "text",
        BTN_TAB_RAW: "raw",
    }
    if button_id in tabs:
        _current_tab = tabs[button_id]


# ============================================================
# MAIN
# ============================================================

def Main():
    global _running
    global _gump_dirty
    _output_dir()
    _remember_external_current()
    _draw_gump()

    try:
        while _running and Player.Connected:
            _remember_external_current()
            if _capture_next_armed:
                _poll_capture_next()
                Misc.Pause(GUMP_REFRESH_MS)
                continue

            gump_data = Gumps.GetGumpData(GUMP_ID)
            button_id = int(getattr(gump_data, "buttonid", 0)) if gump_data else 0
            if button_id > 0:
                entry_text = _read_entry_text(gump_data)
                try:
                    gump_data.buttonid = 0
                except:
                    pass
                Gumps.CloseGump(GUMP_ID)
                _handle_button(button_id, entry_text)
                _gump_dirty = not _capture_next_armed
                Misc.Pause(BUTTON_DEBOUNCE_MS)
            elif _gump_dirty or gump_data is None:
                _draw_gump()
            Misc.Pause(GUMP_REFRESH_MS)
    except Exception as error:
        Misc.SendMessage("[Frog Gump Inspector] Stopped: " + _clean_text(error), ERROR_HUE)
    finally:
        Gumps.CloseGump(GUMP_ID)


Main()
