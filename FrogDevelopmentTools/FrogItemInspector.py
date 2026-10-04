# ============================================================
# Frog Item Inspector 1.2
# Razor Enhanced development and item-data capture tool
# ============================================================

import datetime
import hashlib
import json
import os
import re

import Gumps
import Items
import Misc
import Mobiles
import Player
import Statics
import Target


# ============================================================
# CONFIGURATION
# ============================================================

GUMP_ID = 0xF206494C
GUMP_X = 440
GUMP_Y = 180
GUMP_WIDTH = 620
GUMP_HEIGHT = 505
GUMP_REFRESH_MS = 100
BUTTON_DEBOUNCE_MS = 175

PROPERTY_WAIT_MS = 1500
CONTEXT_WAIT_MS = 1000
CONTENT_LOAD_PAUSE_MS = 75
MAX_CONTENT_ITEMS = 500
MAX_CONTENT_DEPTH = 12
MAX_REFLECTION_LIST_ITEMS = 500
MAX_HISTORY = 25
MAX_GUI_INTERNAL_ROWS = 24

OUTPUT_FOLDER = os.path.join("FrogDevelopmentTools", "data", "items")
SAVE_ART_WITH_EXPORT = True
CAPTURE_CONTEXT_MENU = True

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

TILE_FLAGS = (
    "None",
    "Translucent",
    "Wall",
    "Damaging",
    "Impassable",
    "Surface",
    "Bridge",
    "Window",
    "NoShoot",
    "Foliage",
    "HoverOver",
    "Roof",
    "Door",
    "Wet",
)

PUBLIC_FIELD_COMMENTS = {
    "Amount": "Stack count currently cached by Razor Enhanced.",
    "BuyDesc": "Vendor purchase description cached for a recently listed item.",
    "Color": "Alias of Hue in the public item wrapper.",
    "Container": "Immediate parent serial. Zero normally means the item is on the ground.",
    "ContainerOpened": "Whether Razor has received and cached this container's contents.",
    "Contains": "Items currently known inside this container. Closed containers may be incomplete.",
    "CorpseNumberItems": "Razor looter cache; -1 means the corpse has not been counted yet.",
    "Deleted": "True when Razor considers this object removed from the world cache.",
    "Direction": "Direction or facing value supplied by the item update packet.",
    "Durability": "Current durability parsed from the item's OPL. Zero can mean not applicable.",
    "Graphics": "Alias of ItemID: the client artwork or graphic number.",
    "GridNum": "Container-grid slot used by clients that support grid positioning.",
    "Hue": "Client hue applied to the item's base artwork.",
    "Image": "Metadata for the client-rendered item artwork returned by Razor.",
    "IsBagOfSending": "Razor's built-in graphic/type check for a bag of sending.",
    "IsContainer": "Razor believes this graphic can contain other items.",
    "IsCorpse": "Razor identifies this item as a corpse.",
    "IsDoor": "Razor identifies this graphic as a door.",
    "IsInBank": "The containment chain currently ends in the player's bank.",
    "IsLootable": "Razor considers the item a normal lootable object rather than hair or similar equipment.",
    "IsPotion": "Razor's built-in graphic/type check for potions.",
    "IsResource": "Razor's built-in check for resources such as ore, wood, sand, stone, or fish.",
    "IsSearchable": "The item can be searched as a container by Razor's internal rules.",
    "IsTwoHanded": "Razor's weapon table marks this item as two-handed.",
    "IsVirtueShield": "Razor identifies this graphic as a virtue shield.",
    "ItemID": "Primary item graphic ID used by scripts, art, filters, and item matching.",
    "Layer": "Equipment layer when worn, or Invalid when the item is not equipped.",
    "Light": "Light-source or corpse-facing byte cached from the item packet.",
    "MaxDurability": "Maximum durability parsed from the item's OPL.",
    "Movable": "Client flag indicating whether the item can normally be picked up.",
    "Name": "Name cached on the item object. The first OPL line is often more complete.",
    "OnGround": "True when the item has no parent container or mobile.",
    "Position": "World coordinates for ground items; container coordinates for contained items.",
    "Price": "Vendor price cached for a recently listed or purchased item.",
    "Properties": "Raw object-property-list entries exposed as cliloc number and arguments.",
    "PropsUpdated": "True after Razor has received an object property list for this item.",
    "RootContainer": "Outermost containing item or mobile serial.",
    "Serial": "Unique runtime identity of this exact item instance.",
    "Updated": "For containers, indicates Razor has received a contents update.",
    "Visible": "Client visibility flag from the most recent item update.",
    "Weight": "Weight parsed from the item's OPL. Zero can mean unavailable.",
}

INTERNAL_FIELD_COMMENTS = {
    "m_Amount": "Raw amount stored by Razor before public wrapper interpretation.",
    "TrueAmount": "Raw packet amount, useful when vendor packets repurpose the normal amount field.",
    "m_Direction": "Raw direction byte cached from the item packet.",
    "m_Light": "Raw light or facing byte cached from the item packet.",
    "m_Visible": "Internal backing value for item visibility.",
    "m_Movable": "Internal backing value for the movable flag.",
    "m_PropsUpdated": "Internal marker that an OPL response has been received.",
    "m_Layer": "Internal numeric equipment layer.",
    "m_Name": "Internal cached item name.",
    "m_Parent": "Internal parent object or unresolved parent serial.",
    "m_Items": "Internal list of children currently known inside this item.",
    "m_IsNew": "Internal lifecycle flag used while Razor processes a new item.",
    "m_AutoStack": "Internal autostack state for this item.",
    "m_HousePacket": "Raw cached custom-house packet bytes, when this object represents a house multi.",
    "m_HouseRev": "Cached custom-house revision number.",
    "m_GridNum": "Raw container grid-slot byte.",
    "m_Updated": "Internal container-contents update marker.",
    "m_Serial": "Raw Assistant serial structure behind the public serial.",
    "m_TypeID": "Raw Assistant graphic/type value behind ItemID.",
    "m_Hue": "Raw Assistant hue value.",
    "m_Deleted": "Internal removed-from-world marker.",
    "m_ContextMenu": "Context-menu response IDs cached after the inspector's context request.",
    "m_ObjPropList": "Internal object-property-list object, including its server revision hash.",
    "m_Hash": "Server-supplied OPL revision hash used to detect property-list changes.",
    "m_StringNums": "Cliloc numbers used by the cached object property list.",
    "m_Content": "Internal ordered OPL entry collection.",
    "m_Owner": "Item object that owns this internal OPL cache.",
}

TILEDATA_FIELD_COMMENTS = {
    "Name": "Name stored in the client's tiledata files for this graphic.",
    "Animation": "Animation or body index associated with this graphic.",
    "Flags": "Complete client TileFlag bitfield. This is broader than Razor's named flag helper.",
    "Background": "TileData says this graphic behaves as background artwork.",
    "Bridge": "TileData says movement height is calculated as a bridge or stair.",
    "Impassable": "TileData marks this graphic as blocking movement.",
    "Surface": "TileData marks this graphic as a standable surface.",
    "Weight": "Base weight byte from client tiledata, not necessarily the OPL item weight.",
    "Quality": "Tiledata quality byte; wearable graphics commonly use it for layer information.",
    "Quantity": "Client tiledata quantity byte.",
    "Value": "Client tiledata value byte.",
    "Hue": "Base tiledata hue-related byte, separate from this instance's Hue.",
    "StackingOffset": "Artwork stacking offset used for generic stackable graphics.",
    "Height": "Raw collision/display height from tiledata.",
    "CalcHeight": "Effective movement height; bridge graphics commonly use half Height.",
    "MiscData": "Legacy miscellaneous tiledata value.",
    "Unk2": "Undocumented client tiledata byte retained for research.",
    "Unk3": "Undocumented client tiledata byte retained for research.",
}

OPL_CLILOC_COMMENTS = {
    1060639: "Durability line; Razor parses current and maximum durability from its arguments.",
    1072788: "Weight line representing a single unit of weight.",
    1072789: "Weight line whose argument contains the numeric weight.",
}

BTN_TARGET = 100
BTN_INSPECT_LAST = 101
BTN_REFRESH = 102
BTN_CLEAR_LAST = 103
BTN_LOAD_TREE = 104
BTN_SAVE_FILE = 120
BTN_TAB_SUMMARY = 130
BTN_TAB_PROPERTIES = 131
BTN_TAB_REFLECTION = 132
BTN_TAB_CONTENTS = 133
BTN_TAB_TILES = 134
BTN_CLOSE = 199


# ============================================================
# RUNTIME STATE
# ============================================================

_running = True
_snapshot = None
_current_serial = 0
_current_tab = "summary"
_status_message = "Ready. Target an item to begin."
_status_hue = MUTED_HUE
_history = []
_gump_dirty = True


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


def _hex(value, width):
    try:
        mask = (1 << (width * 4)) - 1
        return "0x{0:0{1}X}".format(int(value) & mask, width)
    except:
        return "0x" + ("0" * width)


def _serial_record(value):
    try:
        number = int(value)
    except:
        number = 0
    return {
        "decimal": number,
        "hex": _hex(number, 8),
    }


def _graphic_record(value):
    try:
        number = int(value)
    except:
        number = 0
    return {
        "decimal": number,
        "hex": _hex(number, 4),
    }


def _point_record(point):
    if point is None:
        return None
    result = {}
    for name in ("X", "Y", "Z"):
        if hasattr(point, name):
            try:
                result[name.lower()] = int(getattr(point, name))
            except:
                result[name.lower()] = _clean_text(getattr(point, name))
    return result if result else _clean_text(point)


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


def _safe_attr(obj, name, default=None):
    try:
        return getattr(obj, name)
    except:
        return default


def _is_cancelled_serial(serial):
    try:
        return serial is None or int(serial) <= 0
    except:
        return True


def _output_dir():
    path = os.path.join(Misc.CurrentScriptDirectory(), OUTPUT_FOLDER)
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def _safe_filename(value):
    text = _clean_text(value) or "item"
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
    cleaned = "".join(character if character in allowed else "_" for character in text)
    cleaned = cleaned.strip("_")
    return (cleaned or "item")[:48]


def _write_text(path, text):
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as stream:
        stream.write(text)
    if os.path.exists(path):
        os.remove(path)
    os.rename(temporary, path)


def _json_text(data):
    return json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True)


def _html_escape(value):
    text = _clean_text(value)
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))


def _short(value, length):
    text = _clean_text(value)
    if len(text) <= length:
        return text
    return text[:max(0, length - 3)].rstrip() + "..."


def _set_status(message, hue=MUTED_HUE):
    global _status_message
    global _status_hue
    _status_message = _clean_text(message)
    _status_hue = hue


def _friendly_member_name(name):
    text = _clean_text(name)
    backing_match = re.match(r"^<(.+)>k__BackingField$", text)
    if backing_match:
        text = backing_match.group(1)
    if text.startswith("m_"):
        text = text[2:]
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    return text.replace("_", " ").strip()


def _field_comment(name, category="public"):
    raw_name = _clean_text(name)
    backing_match = re.match(r"^<(.+)>k__BackingField$", raw_name)
    lookup_name = backing_match.group(1) if backing_match else raw_name

    if category == "public":
        return PUBLIC_FIELD_COMMENTS.get(
            lookup_name,
            "Public value exposed by this Razor Enhanced build."
        )
    if category == "tiledata":
        return TILEDATA_FIELD_COMMENTS.get(
            lookup_name,
            "Additional client tiledata value retained for development and comparison."
        )
    if raw_name in INTERNAL_FIELD_COMMENTS:
        return INTERNAL_FIELD_COMMENTS[raw_name]
    if lookup_name in INTERNAL_FIELD_COMMENTS:
        return INTERNAL_FIELD_COMMENTS[lookup_name]
    if lookup_name in PUBLIC_FIELD_COMMENTS:
        return "Internal backing value for: " + PUBLIC_FIELD_COMMENTS[lookup_name]
    return (
        "Internal Razor cache value for {0}. Treat it as diagnostic data; "
        "the public wrapper is safer for production scripts."
    ).format(_friendly_member_name(raw_name) or "this member")


def _opl_comment(prop):
    index = int(prop.get("index", 0) or 0)
    cliloc = int(prop.get("cliloc", 0) or 0)
    if index == 0:
        return "Usually the displayed item name or title line."
    if cliloc in OPL_CLILOC_COMMENTS:
        return OPL_CLILOC_COMMENTS[cliloc]
    if prop.get("args"):
        return "Localized OPL entry. Keep both the cliloc and raw arguments for exact matching."
    return "Localized OPL entry rendered by the client from this cliloc number."


def _html_plain(text, color=HTML_TEXT_COLOR):
    return "<basefont color={0}>{1}</basefont>".format(color, _html_escape(text))


def _html_annotated_value(name, value, comment, indent=""):
    return (
        "<basefont color={0}>{1}{2}:</basefont> "
        "<basefont color={3}>{4}</basefont> "
        "<basefont color={5}>-- {6}</basefont>"
    ).format(
        HTML_LABEL_COLOR,
        _html_escape(indent),
        _html_escape(name),
        HTML_VALUE_COLOR,
        _html_escape(_short(value, 220)),
        HTML_COMMENT_COLOR,
        _html_escape(comment)
    )


# ============================================================
# VALUE SERIALIZATION
# ============================================================

def _image_metadata(image):
    if image is None:
        return None
    result = {"runtime_type": _runtime_type(image)}
    for name in ("Width", "Height", "HorizontalResolution", "VerticalResolution"):
        try:
            value = getattr(image, name)
            if name in ("Width", "Height"):
                result[name.lower()] = int(value)
            else:
                result[name.lower()] = float(value)
        except:
            pass
    for name in ("PixelFormat", "RawFormat"):
        try:
            result[name.lower()] = _clean_text(getattr(image, name))
        except:
            pass
    return result


def _property_record(prop, index):
    return {
        "index": int(index),
        "cliloc": int(_safe_attr(prop, "Number", 0) or 0),
        "cliloc_hex": _hex(_safe_attr(prop, "Number", 0), 8),
        "args": _clean_text(_safe_attr(prop, "Args", "")),
        "text": _clean_text(prop),
    }


def _json_value(value, property_name="", depth=0):
    if value is None:
        return None
    if depth > 4:
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

    if type_name in ("System.Byte[]", "System.SByte[]"):
        try:
            byte_values = [int(entry) & 0xFF for entry in value]
            raw_bytes = bytes(byte_values)
            return {
                "length": len(byte_values),
                "hex": "".join("{0:02X}".format(entry) for entry in byte_values),
                "sha256": hashlib.sha256(raw_bytes).hexdigest(),
            }
        except Exception as error:
            return {"runtime_type": type_name, "error": _clean_text(error)}

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

    if all(hasattr(value, axis) for axis in ("X", "Y")):
        return _point_record(value)

    if property_name == "Image" or "Bitmap" in type_name:
        return _image_metadata(value)

    if property_name == "Properties":
        output = []
        try:
            for index, entry in enumerate(value):
                output.append(_property_record(entry, index))
        except Exception as error:
            return {"error": _clean_text(error)}
        return output

    if property_name == "Contains":
        output = []
        try:
            for entry in value:
                output.append({
                    "serial": _serial_record(_safe_attr(entry, "Serial", 0)),
                    "item_id": _graphic_record(_safe_attr(entry, "ItemID", 0)),
                    "hue": _graphic_record(_safe_attr(entry, "Hue", 0)),
                    "name": _clean_text(_safe_attr(entry, "Name", "")),
                    "amount": int(_safe_attr(entry, "Amount", 0) or 0),
                })
                if len(output) >= MAX_REFLECTION_LIST_ITEMS:
                    break
        except Exception as error:
            return {"error": _clean_text(error)}
        return output

    if hasattr(value, "Keys"):
        output = {}
        try:
            for key in value.Keys:
                output[_clean_text(key)] = _json_value(value[key], "", depth + 1)
                if len(output) >= MAX_REFLECTION_LIST_ITEMS:
                    output["__truncated__"] = True
                    break
            return output
        except:
            pass

    if hasattr(value, "Serial") and type_name != "RazorEnhanced.Item":
        return {
            "runtime_type": type_name,
            "serial": _clean_text(_safe_attr(value, "Serial", "")),
            "text": _clean_text(value),
        }

    if hasattr(value, "Count") or hasattr(value, "__iter__"):
        output = []
        try:
            for entry in value:
                output.append(_json_value(entry, "", depth + 1))
                if len(output) >= MAX_REFLECTION_LIST_ITEMS:
                    output.append({"truncated": True})
                    break
            return output
        except:
            pass

    return _clean_text(value)


def _reflect_public_data(item):
    values = {}
    errors = {}
    property_names = []
    field_names = []

    try:
        for prop in item.GetType().GetProperties():
            try:
                if not prop.CanRead or prop.GetIndexParameters().Length > 0:
                    continue
                property_names.append(_clean_text(prop.Name))
            except:
                pass
    except Exception as error:
        errors["GetProperties"] = _clean_text(error)

    fallback_names = (
        "Serial", "ItemID", "Graphics", "Hue", "Color", "Name", "Amount",
        "Container", "RootContainer", "Contains", "Position", "Direction",
        "Layer", "Light", "GridNum", "Visible", "Movable", "OnGround",
        "Deleted", "Updated", "PropsUpdated", "ContainerOpened", "Properties",
        "Weight", "Durability", "MaxDurability", "IsContainer",
        "IsBagOfSending", "IsInBank", "IsSearchable", "IsCorpse",
        "CorpseNumberItems", "IsDoor", "IsLootable", "IsResource", "IsPotion",
        "IsVirtueShield", "IsTwoHanded", "Price", "BuyDesc", "Image"
    )
    for name in fallback_names:
        if name not in property_names and hasattr(item, name):
            property_names.append(name)

    for name in sorted(set(property_names)):
        try:
            values[name] = _json_value(getattr(item, name), name)
        except Exception as error:
            errors[name] = _clean_text(error)

    try:
        for field in item.GetType().GetFields():
            field_names.append(_clean_text(field.Name))
    except Exception as error:
        errors["GetFields"] = _clean_text(error)

    fields = {}
    for name in sorted(set(field_names)):
        try:
            fields[name] = _json_value(getattr(item, name), name)
        except Exception as error:
            errors["field:" + name] = _clean_text(error)

    return {
        "runtime_type": _runtime_type(item),
        "properties": values,
        "fields": fields,
        "read_errors": errors,
    }


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
            section = {
                "declaring_type": type_name,
                "properties": {},
                "fields": {},
            }

            try:
                properties = list(current_type.GetProperties(flags) or [])
            except Exception as error:
                properties = []
                result["read_errors"][type_name + ".GetProperties"] = _clean_text(error)

            for prop in properties:
                name = _clean_text(prop.Name)
                key = type_name + ".property." + name
                try:
                    if prop.GetIndexParameters().Length > 0:
                        continue
                    getter = prop.GetGetMethod(True)
                    if getter is None:
                        continue
                    section["properties"][name] = _json_value(
                        prop.GetValue(obj, None), name, 1
                    )
                except Exception as error:
                    result["read_errors"][key] = _clean_text(error)

            try:
                fields = list(current_type.GetFields(flags) or [])
            except Exception as error:
                fields = []
                result["read_errors"][type_name + ".GetFields"] = _clean_text(error)

            for field in fields:
                name = _clean_text(field.Name)
                key = type_name + ".field." + name
                try:
                    section["fields"][name] = _json_value(
                        field.GetValue(obj), name, 1
                    )
                except Exception as error:
                    result["read_errors"][key] = _clean_text(error)

            result["types"].append(section)
            current_type = current_type.BaseType
    except Exception as error:
        result["read_errors"]["reflection_setup"] = _clean_text(error)

    return result


def _internal_item_data(item):
    result = {
        "available": False,
        "assistant_item": None,
        "object_property_list": None,
        "errors": [],
    }
    try:
        import clr
        clr.AddReference("System")
        from System.Reflection import BindingFlags

        flags = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic
        item_type = item.GetType()
        assistant_property = item_type.GetProperty("AsAssistant", flags)
        if assistant_property is None:
            result["errors"].append("RazorEnhanced.Item.AsAssistant was not found.")
            return result

        assistant_item = assistant_property.GetValue(item, None)
        if assistant_item is None:
            result["errors"].append("RazorEnhanced.Item.AsAssistant returned None.")
            return result

        result["available"] = True
        result["assistant_item"] = _reflect_all_instance_members(assistant_item)

        assistant_type = assistant_item.GetType()
        current_type = assistant_type
        opl_object = None
        while current_type is not None and opl_object is None:
            opl_property = current_type.GetProperty(
                "ObjPropList",
                flags | BindingFlags.DeclaredOnly
            )
            if opl_property is not None:
                opl_object = opl_property.GetValue(assistant_item, None)
                break
            current_type = current_type.BaseType

        if opl_object is not None:
            result["object_property_list"] = _reflect_all_instance_members(opl_object)
        else:
            result["errors"].append("Assistant UOEntity.ObjPropList was not found.")
    except Exception as error:
        result["errors"].append(_clean_text(error))

    return result


# ============================================================
# PROPERTY AND ITEM HELPERS
# ============================================================

def _get_raw_properties(item, wait_ms):
    raw = []
    errors = []
    serial = int(item.Serial)

    try:
        if hasattr(Items, "GetProperties"):
            raw = list(Items.GetProperties(serial, wait_ms) or [])
        else:
            Items.WaitForProps(serial, wait_ms)
            raw = list(item.Properties or [])
    except Exception as error:
        errors.append("GetProperties: " + _clean_text(error))
        try:
            Items.WaitForProps(serial, wait_ms)
            raw = list(item.Properties or [])
        except Exception as fallback_error:
            errors.append("Item.Properties: " + _clean_text(fallback_error))

    records = []
    for index, prop in enumerate(raw):
        try:
            records.append(_property_record(prop, index))
        except Exception as error:
            errors.append("Property {0}: {1}".format(index, _clean_text(error)))

    rendered = []
    try:
        rendered = [_clean_text(line) for line in list(Items.GetPropStringList(serial) or [])]
    except Exception as error:
        errors.append("GetPropStringList: " + _clean_text(error))

    by_index = []
    for index in range(max(len(records), len(rendered)) + 2):
        try:
            text = _clean_text(Items.GetPropStringByIndex(serial, index))
            if not text:
                if index >= max(len(records), len(rendered)):
                    break
                continue
            by_index.append({"index": index, "text": text})
        except Exception as error:
            errors.append("GetPropStringByIndex {0}: {1}".format(index, _clean_text(error)))
            break

    return {
        "raw_opl": records,
        "rendered_lines": rendered,
        "rendered_by_index": by_index,
        "errors": errors,
    }


def _context_menu_data(item):
    result = {
        "requested": bool(CAPTURE_CONTEXT_MENU),
        "entries": [],
        "error": "",
    }
    if not CAPTURE_CONTEXT_MENU:
        return result
    try:
        for index, entry in enumerate(list(Misc.WaitForContext(item, CONTEXT_WAIT_MS) or [])):
            result["entries"].append({
                "index": index,
                "text": _clean_text(_safe_attr(entry, "Entry", "")),
                "response": int(_safe_attr(entry, "Response", 0) or 0),
            })
    except Exception as error:
        result["error"] = _clean_text(error)
    return result


def _weapon_abilities(item_id):
    result = {"primary": "", "secondary": "", "error": ""}
    try:
        if not hasattr(Items, "GetWeaponAbility"):
            result["error"] = "Items.GetWeaponAbility is unavailable in this build."
            return result
        abilities = Items.GetWeaponAbility(int(item_id))
        try:
            result["primary"] = _clean_text(abilities.Item1)
            result["secondary"] = _clean_text(abilities.Item2)
        except:
            result["primary"] = _clean_text(abilities[0])
            result["secondary"] = _clean_text(abilities[1])
    except Exception as error:
        result["error"] = _clean_text(error)
    return result


def _basic_item_record(item, include_cached_properties=True):
    record = {
        "serial": _serial_record(_safe_attr(item, "Serial", 0)),
        "item_id": _graphic_record(_safe_attr(item, "ItemID", 0)),
        "hue": _graphic_record(_safe_attr(item, "Hue", 0)),
        "name": _clean_text(_safe_attr(item, "Name", "")),
        "amount": int(_safe_attr(item, "Amount", 0) or 0),
        "container": _serial_record(_safe_attr(item, "Container", 0)),
        "root_container": _serial_record(_safe_attr(item, "RootContainer", 0)),
        "position": _point_record(_safe_attr(item, "Position", None)),
        "layer": _clean_text(_safe_attr(item, "Layer", "")),
        "grid_num": int(_safe_attr(item, "GridNum", 0) or 0),
        "on_ground": bool(_safe_attr(item, "OnGround", False)),
        "visible": bool(_safe_attr(item, "Visible", False)),
        "movable": bool(_safe_attr(item, "Movable", False)),
    }
    if include_cached_properties:
        try:
            record["cached_property_lines"] = [
                _clean_text(line) for line in list(Items.GetPropStringList(int(item.Serial)) or [])
            ]
        except:
            record["cached_property_lines"] = []
    return record


def _container_chain(item):
    chain = []
    seen = set()
    parent_serial = int(_safe_attr(item, "Container", 0) or 0)

    for depth in range(MAX_CONTENT_DEPTH + 4):
        if parent_serial <= 0 or parent_serial in seen:
            break
        seen.add(parent_serial)

        if parent_serial == int(Player.Serial):
            chain.append({
                "depth": depth,
                "kind": "player",
                "serial": _serial_record(parent_serial),
                "name": _clean_text(Player.Name),
            })
            break

        parent_item = Items.FindBySerial(parent_serial)
        if parent_item:
            entry = _basic_item_record(parent_item, True)
            entry["depth"] = depth
            entry["kind"] = "item"
            chain.append(entry)
            parent_serial = int(_safe_attr(parent_item, "Container", 0) or 0)
            continue

        parent_mobile = Mobiles.FindBySerial(parent_serial)
        if parent_mobile:
            chain.append({
                "depth": depth,
                "kind": "mobile",
                "serial": _serial_record(parent_serial),
                "name": _clean_text(_safe_attr(parent_mobile, "Name", "")),
                "body": _graphic_record(_safe_attr(parent_mobile, "Body", 0)),
                "hue": _graphic_record(_safe_attr(parent_mobile, "Hue", 0)),
                "position": _point_record(_safe_attr(parent_mobile, "Position", None)),
            })
            break

        chain.append({
            "depth": depth,
            "kind": "unresolved",
            "serial": _serial_record(parent_serial),
        })
        break

    return chain


def _content_tree(item):
    root = {
        "root_serial": _serial_record(item.Serial),
        "items": [],
        "total_seen": 0,
        "truncated": False,
        "max_items": MAX_CONTENT_ITEMS,
        "max_depth": MAX_CONTENT_DEPTH,
    }
    pending = []
    seen = set([int(item.Serial)])

    try:
        for child in list(item.Contains or []):
            pending.append((child, 1))
    except:
        return root

    while pending:
        child, depth = pending.pop(0)
        try:
            serial = int(child.Serial)
        except:
            continue
        if serial in seen:
            continue
        seen.add(serial)

        entry = _basic_item_record(child, True)
        entry["depth"] = depth
        root["items"].append(entry)
        root["total_seen"] += 1

        if root["total_seen"] >= MAX_CONTENT_ITEMS:
            root["truncated"] = bool(pending)
            break
        if depth >= MAX_CONTENT_DEPTH:
            try:
                if len(list(child.Contains or [])) > 0:
                    root["truncated"] = True
            except:
                pass
            continue

        try:
            for nested in list(child.Contains or []):
                pending.append((nested, depth + 1))
        except:
            pass

    return root


def _load_container_tree(item):
    if not item or not (bool(_safe_attr(item, "IsContainer", False)) or
                        bool(_safe_attr(item, "IsCorpse", False))):
        return {
            "loaded": 0,
            "failed": 0,
            "errors": ["The current item is not a container or corpse."],
        }

    result = {"loaded": 0, "failed": 0, "errors": []}
    pending = [(item, 0)]
    seen = set()

    while pending and len(seen) < MAX_CONTENT_ITEMS:
        container, depth = pending.pop(0)
        try:
            serial = int(container.Serial)
        except:
            continue
        if serial in seen:
            continue
        seen.add(serial)

        try:
            if Items.WaitForContents(container, PROPERTY_WAIT_MS):
                result["loaded"] += 1
            else:
                result["failed"] += 1
                result["errors"].append(
                    "Timed out loading {0}.".format(_hex(serial, 8))
                )
        except Exception as error:
            result["failed"] += 1
            result["errors"].append(
                "{0}: {1}".format(_hex(serial, 8), _clean_text(error))
            )

        if depth < MAX_CONTENT_DEPTH:
            try:
                for child in list(container.Contains or []):
                    if bool(_safe_attr(child, "IsContainer", False)) or bool(_safe_attr(child, "IsCorpse", False)):
                        pending.append((child, depth + 1))
            except Exception as error:
                result["errors"].append(
                    "Could not enumerate {0}: {1}".format(_hex(serial, 8), _clean_text(error))
                )

        Misc.Pause(CONTENT_LOAD_PAUSE_MS)

    if pending:
        result["errors"].append("Container loading stopped at the configured item limit.")
    return result


# ============================================================
# TILE AND MAP HELPERS
# ============================================================

def _flag_record(static_id, land=False):
    flags = {}
    errors = {}
    for flag in TILE_FLAGS:
        try:
            if land:
                flags[flag] = bool(Statics.GetLandFlag(int(static_id), flag))
            else:
                flags[flag] = bool(Statics.GetTileFlag(int(static_id), flag))
        except Exception as error:
            errors[flag] = _clean_text(error)
    return {"values": flags, "errors": errors}


def _item_tiledata(item_id):
    result = {
        "item_id": _graphic_record(item_id),
        "name": "",
        "height": None,
        "flags": {},
        "raw_item_data": None,
        "errors": [],
    }
    try:
        if hasattr(Statics, "GetItemData"):
            result["raw_item_data"] = _reflect_all_instance_members(
                Statics.GetItemData(int(item_id))
            )
    except Exception as error:
        result["errors"].append("GetItemData: " + _clean_text(error))
    try:
        result["name"] = _clean_text(Statics.GetTileName(int(item_id)))
    except Exception as error:
        result["errors"].append("GetTileName: " + _clean_text(error))
    try:
        result["height"] = int(Statics.GetTileHeight(int(item_id)))
    except Exception as error:
        result["errors"].append("GetTileHeight: " + _clean_text(error))
    flag_data = _flag_record(item_id, False)
    result["flags"] = flag_data["values"]
    if flag_data["errors"]:
        result["flag_errors"] = flag_data["errors"]
    return result


def _tile_info_record(tile):
    static_id = int(_safe_attr(tile, "StaticID", _safe_attr(tile, "ID", 0)) or 0)
    result = {
        "static_id": _graphic_record(static_id),
        "hue": _graphic_record(_safe_attr(tile, "StaticHue", _safe_attr(tile, "Hue", 0))),
        "z": int(_safe_attr(tile, "StaticZ", _safe_attr(tile, "Z", 0)) or 0),
        "runtime_type": _runtime_type(tile),
        "name": "",
        "height": None,
    }
    try:
        result["name"] = _clean_text(Statics.GetTileName(static_id))
    except:
        pass
    try:
        result["height"] = int(Statics.GetTileHeight(static_id))
    except:
        pass
    result["flags"] = _flag_record(static_id, False)["values"]
    return result


def _world_tile_context(item):
    on_ground = bool(_safe_attr(item, "OnGround", False))
    if not on_ground:
        return {
            "available": False,
            "reason": "Item is not on the ground; its world position belongs to a parent entity.",
        }

    try:
        world_position = item.GetWorldPosition()
        x = int(world_position.X)
        y = int(world_position.Y)
        z = int(world_position.Z)
        facet = int(Player.Map)
    except Exception as error:
        return {
            "available": False,
            "reason": "World-position lookup failed.",
            "error": _clean_text(error),
        }
    result = {
        "available": True,
        "position": {"x": x, "y": y, "z": z},
        "facet": facet,
        "facet_source": "Player.Map",
        "private_house_tile": None,
        "land": None,
        "statics": [],
        "errors": [],
    }

    try:
        result["private_house_tile"] = bool(Statics.CheckDeedHouse(x, y))
    except Exception as error:
        result["errors"].append("CheckDeedHouse: " + _clean_text(error))

    try:
        land = Statics.GetStaticsLandInfo(x, y, facet)
        land_id = int(_safe_attr(land, "StaticID", _safe_attr(land, "ID", 0)) or 0)
        result["land"] = {
            "land_id": _graphic_record(land_id),
            "hue": _graphic_record(_safe_attr(land, "StaticHue", _safe_attr(land, "Hue", 0))),
            "z": int(_safe_attr(land, "StaticZ", _safe_attr(land, "Z", 0)) or 0),
            "name": _clean_text(Statics.GetLandName(land_id)),
            "flags": _flag_record(land_id, True)["values"],
        }
    except Exception as error:
        result["errors"].append("GetStaticsLandInfo: " + _clean_text(error))
        try:
            land_id = int(Statics.GetLandID(x, y, facet))
            result["land"] = {
                "land_id": _graphic_record(land_id),
                "z": int(Statics.GetLandZ(x, y, facet)),
                "name": _clean_text(Statics.GetLandName(land_id)),
                "flags": _flag_record(land_id, True)["values"],
            }
        except Exception as fallback_error:
            result["errors"].append("Land fallback: " + _clean_text(fallback_error))

    try:
        for tile in list(Statics.GetStaticsTileInfo(x, y, facet) or []):
            result["statics"].append(_tile_info_record(tile))
    except Exception as error:
        result["errors"].append("GetStaticsTileInfo: " + _clean_text(error))

    return result


def _map_item_info(serial):
    try:
        info = Misc.GetMapInfo(int(serial))
        return {
            "serial": _serial_record(_safe_attr(info, "Serial", serial)),
            "facet": int(_safe_attr(info, "Facet", 0) or 0),
            "pin_position": _point_record(_safe_attr(info, "PinPosition", None)),
            "map_origin": _point_record(_safe_attr(info, "MapOrigin", None)),
            "map_end": _point_record(_safe_attr(info, "MapEnd", None)),
            "runtime_type": _runtime_type(info),
        }
    except Exception as error:
        return {"error": _clean_text(error)}


# ============================================================
# SNAPSHOT CAPTURE
# ============================================================

def _capture_item(serial):
    item = Items.FindBySerial(int(serial))
    if not item:
        raise Exception("The serial is not an item in Razor Enhanced memory.")

    capture_errors = []
    try:
        Items.SingleClick(item)
    except Exception as error:
        capture_errors.append("SingleClick: " + _clean_text(error))

    properties = _get_raw_properties(item, PROPERTY_WAIT_MS)
    context_menu = _context_menu_data(item)
    world_position = None
    try:
        world_position = _point_record(item.GetWorldPosition())
    except Exception as error:
        capture_errors.append("GetWorldPosition: " + _clean_text(error))

    player_distance = None
    try:
        item_world_position = item.GetWorldPosition()
        player_distance = max(
            abs(int(item_world_position.X) - int(Player.Position.X)),
            abs(int(item_world_position.Y) - int(Player.Position.Y))
        )
    except Exception as error:
        capture_errors.append("Distance to player: " + _clean_text(error))

    backpack_serial = int(Player.Backpack.Serial) if Player.Backpack else 0
    root_serial = int(_safe_attr(item, "RootContainer", 0) or 0)
    container_serial = int(_safe_attr(item, "Container", 0) or 0)

    name = _clean_text(_safe_attr(item, "Name", ""))
    rendered = properties.get("rendered_lines", [])
    if rendered and rendered[0]:
        name = rendered[0]

    public_reflection = _reflect_public_data(item)
    internal_reflection = _internal_item_data(item)
    on_ignore_list = None
    try:
        on_ignore_list = bool(Misc.CheckIgnoreObject(item))
    except Exception as error:
        capture_errors.append("CheckIgnoreObject: " + _clean_text(error))
    is_target_last = None
    try:
        is_target_last = int(Target.GetLast() or 0) == int(item.Serial)
    except Exception as error:
        capture_errors.append("GetLast target: " + _clean_text(error))

    snapshot = {
        "schema": "frog-item-inspector.snapshot.v1",
        "captured_at_local": datetime.datetime.now().isoformat(),
        "capture_source": "Razor Enhanced Python API",
        "item": {
            "name": name,
            "serial": _serial_record(item.Serial),
            "item_id": _graphic_record(item.ItemID),
            "hue": _graphic_record(item.Hue),
            "amount": int(_safe_attr(item, "Amount", 0) or 0),
            "position": _point_record(_safe_attr(item, "Position", None)),
            "world_position": world_position,
            "container": _serial_record(container_serial),
            "root_container": _serial_record(root_serial),
            "layer": _clean_text(_safe_attr(item, "Layer", "")),
            "direction": _clean_text(_safe_attr(item, "Direction", "")),
            "distance_to_player": player_distance,
            "to_string": _clean_text(item),
        },
        "derived": {
            "in_player_backpack": root_serial in (backpack_serial, int(Player.Serial)),
            "directly_in_backpack": container_serial == backpack_serial,
            "equipped_by_player": container_serial == int(Player.Serial),
            "is_target_last": is_target_last,
            "on_razor_ignore_list": on_ignore_list,
        },
        "object_property_list": properties,
        "context_menu": context_menu,
        "reflection": public_reflection,
        "internal_reflection": internal_reflection,
        "container_chain": _container_chain(item),
        "contents": _content_tree(item),
        "tiledata_for_item_graphic": _item_tiledata(item.ItemID),
        "weapon_abilities_for_item_graphic": _weapon_abilities(item.ItemID),
        "world_tile_context": _world_tile_context(item),
        "map_item_info": _map_item_info(item.Serial),
        "capture_context": {
            "player_serial": _serial_record(Player.Serial),
            "player_name": _clean_text(Player.Name),
            "player_position": _point_record(Player.Position),
            "player_map": int(Player.Map),
            "property_wait_ms": PROPERTY_WAIT_MS,
        },
        "commentary": {
            "public_fields": dict(PUBLIC_FIELD_COMMENTS),
            "internal_fields": dict(INTERNAL_FIELD_COMMENTS),
            "tiledata_fields": dict(TILEDATA_FIELD_COMMENTS),
            "opl_clilocs": dict(OPL_CLILOC_COMMENTS),
            "note": (
                "Descriptions are development guidance inferred from Razor Enhanced 0.8.2.245 "
                "source and API behavior. Undocumented internal values may change between builds."
            ),
        },
        "capture_errors": capture_errors,
    }
    return snapshot


def _inspect_serial(serial):
    global _snapshot
    global _current_serial
    global _history

    if _is_cancelled_serial(serial):
        _set_status("Target cancelled.", MUTED_HUE)
        return False

    try:
        _set_status("Inspecting {0}...".format(_hex(serial, 8)), MUTED_HUE)
        snapshot = _capture_item(int(serial))
        _snapshot = snapshot
        _current_serial = int(serial)
        _history.append({
            "captured_at_local": snapshot["captured_at_local"],
            "serial": snapshot["item"]["serial"],
            "item_id": snapshot["item"]["item_id"],
            "hue": snapshot["item"]["hue"],
            "name": snapshot["item"]["name"],
        })
        if len(_history) > MAX_HISTORY:
            _history = _history[-MAX_HISTORY:]

        property_count = len(snapshot["object_property_list"]["raw_opl"])
        reflected_count = len(snapshot["reflection"]["properties"])
        _set_status(
            "Captured {0} OPL entries and {1} public properties.".format(
                property_count, reflected_count
            ),
            SUCCESS_HUE
        )
        try:
            Items.Message(int(serial), SUCCESS_HUE, "Fully inspected")
        except:
            pass
        return True
    except Exception as error:
        _set_status("Inspect failed: " + _clean_text(error), ERROR_HUE)
        Misc.SendMessage("[Frog Item Inspector] " + _status_message, ERROR_HUE)
        return False


# ============================================================
# FILE EXPORT HELPERS
# ============================================================

def _script_constants(snapshot):
    item = snapshot["item"]
    name = item["name"].replace("\\", "\\\\").replace('"', '\\"')
    lines = [
        "# Generated by Frog Item Inspector",
        "ITEM_NAME = \"{0}\"".format(name),
        "ITEM_SERIAL = {0}".format(item["serial"]["hex"]),
        "ITEM_ID = {0}".format(item["item_id"]["hex"]),
        "ITEM_HUE = {0}".format(item["hue"]["hex"]),
        "ITEM_AMOUNT = {0}".format(item["amount"]),
        "ITEM_CONTAINER = {0}".format(item["container"]["hex"]),
        "ITEM_ROOT_CONTAINER = {0}".format(item["root_container"]["hex"]),
        "",
        "# Common reusable lookup:",
        "item = Items.FindByID(ITEM_ID, ITEM_HUE, Player.Backpack.Serial, True)",
    ]
    return "\n".join(lines) + "\n"


def _properties_text(snapshot):
    lines = []
    for prop in snapshot["object_property_list"]["raw_opl"]:
        lines.append("[{0}] cliloc={1} args={2!r} text={3}".format(
            prop["index"], prop["cliloc"], prop["args"], prop["text"]
        ))
        lines.append("    Meaning: " + _opl_comment(prop))
    return "\n".join(lines)


def _annotated_public_text(snapshot):
    lines = []
    values = snapshot.get("reflection", {}).get("properties", {})
    for name in sorted(values.keys()):
        lines.append("{0} = {1}".format(name, _clean_text(values[name])))
        lines.append("    Meaning: " + _field_comment(name, "public"))
    return lines


def _annotated_internal_text(snapshot):
    lines = []
    internal = snapshot.get("internal_reflection", {})
    assistant_data = internal.get("assistant_item") or {}
    for section in assistant_data.get("types", []):
        lines.append("[{0}]".format(section.get("declaring_type", "Unknown type")))
        for name in sorted(section.get("properties", {}).keys()):
            lines.append("property {0} = {1}".format(
                name, _clean_text(section["properties"][name])
            ))
            lines.append("    Meaning: " + _field_comment(name, "internal"))
        for name in sorted(section.get("fields", {}).keys()):
            lines.append("field {0} = {1}".format(
                name, _clean_text(section["fields"][name])
            ))
            lines.append("    Meaning: " + _field_comment(name, "internal"))

    opl_data = internal.get("object_property_list") or {}
    for section in opl_data.get("types", []):
        lines.append("[{0}]".format(section.get("declaring_type", "Internal OPL")))
        for name in sorted(section.get("properties", {}).keys()):
            lines.append("property {0} = {1}".format(
                name, _clean_text(section["properties"][name])
            ))
            lines.append("    Meaning: " + _field_comment(name, "internal"))
        for name in sorted(section.get("fields", {}).keys()):
            lines.append("field {0} = {1}".format(
                name, _clean_text(section["fields"][name])
            ))
            lines.append("    Meaning: " + _field_comment(name, "internal"))
    return lines


def _annotated_tiledata_text(snapshot):
    lines = []
    raw_item_data = snapshot.get("tiledata_for_item_graphic", {}).get("raw_item_data") or {}
    for section in raw_item_data.get("types", []):
        lines.append("[{0}]".format(section.get("declaring_type", "Ultima.ItemData")))
        for name in sorted(section.get("properties", {}).keys()):
            lines.append("{0} = {1}".format(name, _clean_text(section["properties"][name])))
            lines.append("    Meaning: " + _field_comment(name, "tiledata"))
        for name in sorted(section.get("fields", {}).keys()):
            lines.append("field {0} = {1}".format(name, _clean_text(section["fields"][name])))
            lines.append("    Meaning: " + _field_comment(name, "tiledata"))
    return lines


def _human_text(snapshot):
    item = snapshot["item"]
    lines = [
        "FROG ITEM INSPECTOR - ANNOTATED REPORT",
        "Captured: " + snapshot["captured_at_local"],
        "",
        "QUICK SUMMARY",
        "-------------",
        "Name: " + item["name"],
        "Serial: {0} ({1})".format(item["serial"]["hex"], item["serial"]["decimal"]),
        "Item ID: {0} ({1})".format(item["item_id"]["hex"], item["item_id"]["decimal"]),
        "Hue: {0} ({1})".format(item["hue"]["hex"], item["hue"]["decimal"]),
        "Amount: " + str(item["amount"]),
        "Position: " + _clean_text(item["position"]),
        "World Position: " + _clean_text(item["world_position"]),
        "Container: " + item["container"]["hex"],
        "Root Container: " + item["root_container"]["hex"],
        "Layer: " + item["layer"],
        "",
        "PUBLIC RAZOR ITEM DATA - ANNOTATED",
        "----------------------------------",
    ]
    lines.extend(_annotated_public_text(snapshot))
    lines.extend([
        "",
        "OBJECT PROPERTY LIST - ANNOTATED",
        "--------------------------------",
        _properties_text(snapshot),
        "",
        "CONTEXT MENU",
        "------------",
    ])
    for entry in snapshot.get("context_menu", {}).get("entries", []):
        lines.append("[{0}] response={1}: {2}".format(
            entry["index"], entry["response"], entry["text"]
        ))
    if not snapshot.get("context_menu", {}).get("entries"):
        lines.append("No context-menu entries were returned.")
    lines.extend([
        "",
        "RAZOR INTERNAL ITEM STATE - ANNOTATED",
        "-------------------------------------",
    ])
    lines.extend(_annotated_internal_text(snapshot))
    lines.extend([
        "",
        "CLIENT TILEDATA - ANNOTATED",
        "---------------------------",
    ])
    lines.extend(_annotated_tiledata_text(snapshot))
    lines.extend([
        "",
        "FULL STRUCTURED SNAPSHOT",
        "------------------------",
        _json_text(snapshot),
    ])
    return "\n".join(lines) + "\n"


def _save_art(snapshot, path):
    metadata = {"saved": False, "path": path}
    try:
        import clr
        clr.AddReference("System.Drawing")
        from System.Drawing.Imaging import ImageFormat

        item = snapshot["item"]
        image = Items.GetImage(item["item_id"]["decimal"], item["hue"]["decimal"])
        if image is None:
            metadata["error"] = "Items.GetImage returned None."
            return metadata
        image.Save(path, ImageFormat.Png)
        metadata["saved"] = True
        metadata["width"] = int(image.Width)
        metadata["height"] = int(image.Height)
        with open(path, "rb") as stream:
            metadata["sha256"] = hashlib.sha256(stream.read()).hexdigest()
        return metadata
    except Exception as error:
        metadata["error"] = _clean_text(error)
        return metadata


def _save_bundle(snapshot, prefix, include_art):
    folder = _output_dir()
    paths = {
        "json": os.path.join(folder, prefix + "_raw.json"),
        "text": os.path.join(folder, prefix + "_report.txt"),
        "script": os.path.join(folder, prefix + "_constants.py"),
    }
    if include_art:
        art_path = os.path.join(folder, prefix + "_art.png")
        paths["art"] = _save_art(snapshot, art_path)
        snapshot["art_export"] = paths["art"]
    _write_text(paths["json"], _json_text(snapshot) + "\n")
    _write_text(paths["text"], _human_text(snapshot))
    _write_text(paths["script"], _script_constants(snapshot))
    return paths


def _export_snapshot(snapshot):
    item = snapshot["item"]
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    prefix = "{0}_{1}_{2}".format(
        stamp,
        item["serial"]["hex"].replace("0x", ""),
        _safe_filename(item["name"])
    )
    return _save_bundle(snapshot, prefix, SAVE_ART_WITH_EXPORT)


# ============================================================
# GUMP CONTENT HELPERS
# ============================================================

def _summary_lines(snapshot):
    item = snapshot["item"]
    reflection = snapshot["reflection"]["properties"]
    position = item["position"] or {}
    world = item["world_position"] or {}
    return [
        ("Name", item["name"]),
        ("Serial", "{0} / {1}".format(item["serial"]["hex"], item["serial"]["decimal"])),
        ("Item ID", "{0} / {1}".format(item["item_id"]["hex"], item["item_id"]["decimal"])),
        ("Hue", "{0} / {1}".format(item["hue"]["hex"], item["hue"]["decimal"])),
        ("Amount", item["amount"]),
        ("Position", "{0}, {1}, {2}".format(position.get("x"), position.get("y"), position.get("z"))),
        ("World", "{0}, {1}, {2}".format(world.get("x"), world.get("y"), world.get("z"))),
        ("Container", item["container"]["hex"]),
        ("Root", item["root_container"]["hex"]),
        ("Layer / Direction", "{0} / {1}".format(item["layer"], item["direction"])),
        ("Distance", item["distance_to_player"]),
        ("Flags", "container={0}, corpse={1}, door={2}, movable={3}, ground={4}".format(
            reflection.get("IsContainer"), reflection.get("IsCorpse"),
            reflection.get("IsDoor"), reflection.get("Movable"), reflection.get("OnGround")
        )),
        ("State", "updated={0}, props={1}, visible={2}, deleted={3}".format(
            reflection.get("Updated"), reflection.get("PropsUpdated"),
            reflection.get("Visible"), reflection.get("Deleted")
        )),
        ("Durability", "{0}/{1}; weight={2}".format(
            reflection.get("Durability"), reflection.get("MaxDurability"), reflection.get("Weight")
        )),
        ("Capture", "{0} OPL, {1} reflected, {2} contents".format(
            len(snapshot["object_property_list"]["raw_opl"]),
            len(reflection), snapshot["contents"]["total_seen"]
        )),
        ("Context menu", "{0} entries; error={1}".format(
            len(snapshot.get("context_menu", {}).get("entries", [])),
            bool(snapshot.get("context_menu", {}).get("error", ""))
        )),
        ("Internal", "available={0}, errors={1}".format(
            snapshot.get("internal_reflection", {}).get("available", False),
            len(snapshot.get("internal_reflection", {}).get("errors", []))
        )),
    ]


def _internal_gui_rows(reflection):
    rows = []
    for section in reflection.get("types", []):
        declaring_type = section.get("declaring_type", "")
        for kind in ("properties", "fields"):
            singular = "property" if kind == "properties" else "field"
            for name, value in section.get(kind, {}).items():
                backing_match = re.match(r"^<(.+)>k__BackingField$", name)
                lookup_name = backing_match.group(1) if backing_match else name
                if name in INTERNAL_FIELD_COMMENTS or lookup_name in INTERNAL_FIELD_COMMENTS:
                    priority = 0
                elif lookup_name in PUBLIC_FIELD_COMMENTS:
                    priority = 1
                elif name.startswith("m_"):
                    priority = 2
                else:
                    priority = 3
                rows.append((
                    priority,
                    declaring_type,
                    singular,
                    name,
                    value,
                ))
    rows.sort(key=lambda row: (row[0], row[1], row[3]))
    return rows


def _tab_html(snapshot, tab_name):
    if not snapshot:
        return _html_plain("Target an item to capture its complete snapshot.", HTML_COMMENT_COLOR)

    lines = []
    if tab_name == "summary":
        for label, value in _summary_lines(snapshot):
            lines.append("<basefont color={0}>{1}:</basefont> <basefont color={2}>{3}</basefont>".format(
                HTML_LABEL_COLOR, _html_escape(label), HTML_VALUE_COLOR, _html_escape(value)
            ))

        if snapshot["container_chain"]:
            lines.append("<basefont color={0}>Container chain</basefont>".format(HTML_SECTION_COLOR))
            for entry in snapshot["container_chain"]:
                serial = entry.get("serial", {}).get("hex", "")
                lines.append("  {0}: {1} {2} {3}".format(
                    entry.get("depth"), entry.get("kind"), serial, _html_escape(entry.get("name", ""))
                ))

        context_menu = snapshot.get("context_menu", {})
        if context_menu.get("entries"):
            lines.append("<basefont color={0}>Context menu</basefont>".format(HTML_SECTION_COLOR))
            for entry in context_menu["entries"]:
                lines.append("  [{0}] response={1}: {2}".format(
                    entry["index"], entry["response"], _html_escape(entry["text"])
                ))

        all_errors = list(snapshot.get("capture_errors", []))
        all_errors.extend(snapshot["object_property_list"].get("errors", []))
        if all_errors:
            lines.append("<basefont color={0}>Capture warnings</basefont>".format(HTML_ERROR_COLOR))
            lines.extend(_html_escape(error) for error in all_errors)

    elif tab_name == "properties":
        raw = snapshot["object_property_list"]["raw_opl"]
        if not raw:
            lines.append("No OPL entries were returned.")
        for prop in raw:
            lines.append("<basefont color={0}>[{1}] cliloc {2}</basefont>".format(
                HTML_SECTION_COLOR, prop["index"], prop["cliloc"]
            ))
            lines.append("  text: " + _html_escape(prop["text"]))
            lines.append("  args: " + _html_escape(repr(prop["args"])))
            lines.append("<basefont color={0}>  meaning: {1}</basefont>".format(
                HTML_COMMENT_COLOR, _html_escape(_opl_comment(prop))
            ))

    elif tab_name == "reflection":
        lines.append("<basefont color={0}>Razor Enhanced public item wrapper</basefont>".format(
            HTML_SECTION_COLOR
        ))
        lines.append("<basefont color={0}>Each line includes our best description of what Razor is exposing.</basefont>".format(
            HTML_COMMENT_COLOR
        ))
        for name in sorted(snapshot["reflection"]["properties"].keys()):
            value = snapshot["reflection"]["properties"][name]
            lines.append(_html_annotated_value(
                name, value, _field_comment(name, "public")
            ))
        for name in sorted(snapshot["reflection"]["fields"].keys()):
            value = snapshot["reflection"]["fields"][name]
            lines.append(_html_annotated_value(
                "field " + name, value, _field_comment(name, "public")
            ))
        for name in sorted(snapshot["reflection"]["read_errors"].keys()):
            lines.append("<basefont color={0}>{1}: {2}</basefont>".format(
                HTML_ERROR_COLOR, _html_escape(name),
                _html_escape(snapshot["reflection"]["read_errors"][name])
            ))

        internal = snapshot.get("internal_reflection", {})
        lines.append("<basefont color={0}>Assistant internal item state</basefont>".format(
            HTML_SECTION_COLOR
        ))
        lines.append("available=" + _html_escape(internal.get("available", False)))
        assistant_data = internal.get("assistant_item") or {}
        internal_rows = _internal_gui_rows(assistant_data)
        for row in internal_rows[:MAX_GUI_INTERNAL_ROWS]:
            _, declaring_type, kind, name, value = row
            lines.append(_html_annotated_value(
                "{0}.{1} {2}".format(declaring_type.split(".")[-1], kind, name),
                value,
                _field_comment(name, "internal")
            ))
        if len(internal_rows) > MAX_GUI_INTERNAL_ROWS:
            lines.append("<basefont color={0}>Showing {1} of {2} internal values here. SAVE FILE includes the complete annotated list.</basefont>".format(
                HTML_COMMENT_COLOR, MAX_GUI_INTERNAL_ROWS, len(internal_rows)
            ))
        for name in sorted(assistant_data.get("read_errors", {}).keys()):
            lines.append("<basefont color={0}>{1}: {2}</basefont>".format(
                HTML_ERROR_COLOR, _html_escape(name),
                _html_escape(assistant_data["read_errors"][name])
            ))

        opl_internal = internal.get("object_property_list") or {}
        if opl_internal:
            lines.append("<basefont color={0}>Assistant internal OPL state</basefont>".format(
                HTML_SECTION_COLOR
            ))
            for section in opl_internal.get("types", []):
                for name in sorted(section.get("properties", {}).keys()):
                    lines.append(_html_annotated_value(
                        "property " + name,
                        section["properties"][name],
                        _field_comment(name, "internal"),
                        "  "
                    ))
                for name in sorted(section.get("fields", {}).keys()):
                    lines.append(_html_annotated_value(
                        "field " + name,
                        section["fields"][name],
                        _field_comment(name, "internal"),
                        "  "
                    ))
        for error in internal.get("errors", []):
            lines.append("<basefont color={0}>{1}</basefont>".format(
                HTML_ERROR_COLOR, _html_escape(error)
            ))

    elif tab_name == "contents":
        content = snapshot["contents"]
        lines.append("Known contents: {0}; truncated={1}".format(
            content["total_seen"], content["truncated"]
        ))
        lines.append("<basefont color={0}>Only client-known items appear here. Use LOAD CONTAINER TREE to request nested contents.</basefont>".format(
            HTML_COMMENT_COLOR
        ))
        for entry in content["items"]:
            indent = "  " * max(0, int(entry.get("depth", 1)) - 1)
            lines.append("{0}[d{1}] {2} {3} hue {4} x{5} {6}".format(
                indent,
                entry.get("depth"),
                entry["serial"]["hex"],
                entry["item_id"]["hex"],
                entry["hue"]["hex"],
                entry["amount"],
                _html_escape(entry["name"])
            ))
            for prop in entry.get("cached_property_lines", []):
                lines.append(indent + "  " + _html_escape(prop))

    elif tab_name == "tiles":
        tile = snapshot["tiledata_for_item_graphic"]
        lines.append("<basefont color={0}>Item graphic TileData</basefont>".format(
            HTML_SECTION_COLOR
        ))
        lines.append("ID {0}; name={1}; height={2}".format(
            tile["item_id"]["hex"], _html_escape(tile["name"]), tile["height"]
        ))
        enabled = [name for name, value in tile["flags"].items() if value]
        lines.append("Enabled flags: " + (", ".join(enabled) if enabled else "none"))
        lines.append("All flags: " + _html_escape(tile["flags"]))
        abilities = snapshot.get("weapon_abilities_for_item_graphic", {})
        lines.append("Weapon abilities: {0} / {1}".format(
            _html_escape(abilities.get("primary", "")),
            _html_escape(abilities.get("secondary", ""))
        ))
        raw_item_data = tile.get("raw_item_data") or {}
        for section in raw_item_data.get("types", []):
            for name in sorted(section.get("properties", {}).keys()):
                lines.append(_html_annotated_value(
                    "TileData property " + name,
                    section["properties"][name],
                    _field_comment(name, "tiledata")
                ))
        lines.append("<basefont color={0}>Compiler backing fields are omitted from this tab; SAVE FILE retains them.</basefont>".format(
            HTML_COMMENT_COLOR
        ))

        world = snapshot["world_tile_context"]
        lines.append("<basefont color={0}>World tile context</basefont>".format(
            HTML_SECTION_COLOR
        ))
        if not world.get("available"):
            lines.append(_html_escape(world.get("reason", "Unavailable")))
        else:
            lines.append("Facet {0}; position {1}; private-house tile={2}".format(
                world["facet"], _html_escape(world["position"]), world["private_house_tile"]
            ))
            lines.append("Land: " + _html_escape(world.get("land")))
            for entry in world.get("statics", []):
                enabled = [name for name, value in entry.get("flags", {}).items() if value]
                lines.append("Static {0} hue {1} z={2} h={3} {4} [{5}]".format(
                    entry["static_id"]["hex"], entry["hue"]["hex"], entry["z"],
                    entry["height"], _html_escape(entry["name"]), ", ".join(enabled)
                ))
            for error in world.get("errors", []):
                lines.append("<basefont color={0}>{1}</basefont>".format(
                    HTML_ERROR_COLOR, _html_escape(error)
                ))

    separator = "</basefont><br><basefont color={0}>".format(HTML_TEXT_COLOR)
    return "<basefont color={0}>{1}</basefont>".format(
        HTML_TEXT_COLOR,
        separator.join(lines)
    )


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

    Gumps.AddLabel(gump, 16, 10, TITLE_HUE, "Frog Item Inspector")
    if _snapshot:
        title = "{0} | {1} | {2}/{3}".format(
            _short(_snapshot["item"]["name"], 44),
            _snapshot["item"]["serial"]["hex"],
            _snapshot["item"]["item_id"]["hex"],
            _snapshot["item"]["hue"]["hex"]
        )
        Gumps.AddLabel(gump, 175, 10, VALUE_HUE, title)
    Gumps.AddButton(gump, GUMP_WIDTH - 28, 8, 4017, 4019, BTN_CLOSE, 1, 0)

    _add_button(gump, 16, 38, BTN_TARGET, "TARGET", SUCCESS_HUE)
    _add_button(gump, 125, 38, BTN_INSPECT_LAST, "RE LAST", TEXT_HUE)
    _add_button(gump, 235, 38, BTN_REFRESH, "REFRESH", TEXT_HUE)
    _add_button(gump, 345, 38, BTN_CLEAR_LAST, "CLEAR LAST", ERROR_HUE)
    _add_button(gump, 470, 38, BTN_SAVE_FILE, "SAVE TO FILE", VALUE_HUE)

    _add_button(gump, 16, 70, BTN_LOAD_TREE, "LOAD CONTAINER TREE", VALUE_HUE)

    tab_data = (
        (BTN_TAB_SUMMARY, "summary", "Summary", 16),
        (BTN_TAB_PROPERTIES, "properties", "OPL", 125),
        (BTN_TAB_REFLECTION, "reflection", "API Data", 218),
        (BTN_TAB_CONTENTS, "contents", "Contents", 335),
        (BTN_TAB_TILES, "tiles", "TileData", 455),
    )
    for button_id, tab_name, label, x in tab_data:
        hue = SUCCESS_HUE if _current_tab == tab_name else MUTED_HUE
        _add_button(gump, x, 102, button_id, label, hue)

    Gumps.AddAlphaRegion(gump, 12, 130, GUMP_WIDTH - 24, 302)
    Gumps.AddHtml(
        gump, 18, 136, GUMP_WIDTH - 36, 288,
        _tab_html(_snapshot, _current_tab),
        False, True
    )

    Gumps.AddLabel(gump, 16, 442, _status_hue, _short(_status_message, 86))
    Gumps.AddLabel(gump, 16, 474, MUTED_HUE,
                   "Save folder: Scripts/FrogDevelopmentTools/data/items | Inspected this run: {0}".format(len(_history)))

    Gumps.SendGump(
        GUMP_ID, Player.Serial, GUMP_X, GUMP_Y,
        gump.gumpDefinition, gump.gumpStrings
    )
    _gump_dirty = False


def _set_tab(name):
    global _current_tab
    _current_tab = name


def _clear_last():
    global _snapshot
    global _current_serial
    try:
        Target.ClearLastandQueue()
    except:
        try:
            Target.ClearLast()
        except:
            pass
    _snapshot = None
    _current_serial = 0
    _set_status("Current snapshot and Razor Enhanced last target cleared.", MUTED_HUE)


def _handle_button(button_id):
    global _running

    if button_id == BTN_CLOSE:
        _running = False
        return

    if button_id == BTN_TARGET:
        serial = Target.PromptTarget("Target an item for full inspection", MUTED_HUE)
        _inspect_serial(serial)
        return

    if button_id == BTN_INSPECT_LAST:
        try:
            serial = int(Target.GetLast() or 0)
        except:
            serial = 0
        if serial <= 0:
            _set_status("Razor Enhanced has no last target.", ERROR_HUE)
        else:
            _inspect_serial(serial)
        return

    if button_id == BTN_REFRESH:
        if _current_serial > 0:
            _inspect_serial(_current_serial)
        else:
            _set_status("Nothing to refresh. Target an item first.", ERROR_HUE)
        return

    if button_id == BTN_CLEAR_LAST:
        _clear_last()
        return

    if button_id == BTN_LOAD_TREE:
        if _current_serial <= 0:
            _set_status("Target a container first.", ERROR_HUE)
            return
        current_item = Items.FindBySerial(_current_serial)
        load_result = _load_container_tree(current_item)
        if load_result["loaded"] <= 0:
            _set_status(
                load_result["errors"][0] if load_result["errors"] else "No containers loaded.",
                ERROR_HUE
            )
            return
        _inspect_serial(_current_serial)
        _set_status(
            "Loaded {0} container(s), {1} timeout/error(s), then recaptured.".format(
                load_result["loaded"], load_result["failed"]
            ),
            SUCCESS_HUE if load_result["failed"] == 0 else MUTED_HUE
        )
        return

    tabs = {
        BTN_TAB_SUMMARY: "summary",
        BTN_TAB_PROPERTIES: "properties",
        BTN_TAB_REFLECTION: "reflection",
        BTN_TAB_CONTENTS: "contents",
        BTN_TAB_TILES: "tiles",
    }
    if button_id in tabs:
        _set_tab(tabs[button_id])
        return

    if not _snapshot:
        _set_status("Target an item first.", ERROR_HUE)
        return

    if button_id == BTN_SAVE_FILE:
        try:
            paths = _export_snapshot(_snapshot)
            art = paths.get("art", {})
            art_note = " + art" if art.get("saved") else ""
            _set_status("Saved annotated report, raw JSON, constants{0}.".format(art_note), SUCCESS_HUE)
            Misc.SendMessage("[Frog Item Inspector] Saved files to " + _output_dir(), SUCCESS_HUE)
        except Exception as error:
            _set_status("Save failed: " + _clean_text(error), ERROR_HUE)


# ============================================================
# MAIN
# ============================================================

def Main():
    global _running
    global _gump_dirty
    _output_dir()
    _draw_gump()

    try:
        while _running and Player.Connected:
            gump_data = Gumps.GetGumpData(GUMP_ID)
            button_id = int(getattr(gump_data, "buttonid", 0)) if gump_data else 0

            if button_id > 0:
                try:
                    gump_data.buttonid = 0
                except:
                    pass
                Gumps.CloseGump(GUMP_ID)
                _handle_button(button_id)
                _gump_dirty = True
                Misc.Pause(BUTTON_DEBOUNCE_MS)
            elif _gump_dirty or gump_data is None:
                _draw_gump()

            Misc.Pause(GUMP_REFRESH_MS)
    except Exception as error:
        Misc.SendMessage("[Frog Item Inspector] Stopped: " + _clean_text(error), ERROR_HUE)
    finally:
        Gumps.CloseGump(GUMP_ID)


Main()
