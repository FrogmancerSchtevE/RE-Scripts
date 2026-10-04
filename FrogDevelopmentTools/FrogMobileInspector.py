# ============================================================
# Frog Mobile Inspector 1.0
# Razor Enhanced mobile, creature, player, and equipment capture tool
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

GUMP_ID = 0xF2064D4F
GUMP_X = 405
GUMP_Y = 145
GUMP_WIDTH = 700
GUMP_HEIGHT = 535
GUMP_REFRESH_MS = 100
BUTTON_DEBOUNCE_MS = 175

PROPERTY_WAIT_MS = 1500
STATS_WAIT_MS = 1500
EQUIPMENT_PROPERTY_WAIT_MS = 650
CONTEXT_WAIT_MS = 1000
MAX_REFLECTION_LIST_ITEMS = 750
MAX_HISTORY = 25
MAX_GUI_INTERNAL_ROWS = 34
MAX_CACHED_BACKPACK_ITEMS = 500

OUTPUT_FOLDER = os.path.join("FrogDevelopmentTools", "data", "mobiles")
CAPTURE_CONTEXT_MENU = True
CAPTURE_EQUIPMENT_INTERNALS = True
CAPTURE_KNOWN_BACKPACK_CONTENTS = True
CAPTURE_SELF_SKILLS = True

FROG_ICON = 0x2130
FROG_HUE = 1152
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

BTN_TARGET = 100
BTN_INSPECT_LAST = 101
BTN_REFRESH = 102
BTN_CLEAR_LAST = 103
BTN_SAVE_FILE = 104
BTN_TAB_SUMMARY = 120
BTN_TAB_PROPERTIES = 121
BTN_TAB_EQUIPMENT = 122
BTN_TAB_API = 123
BTN_TAB_INTERNALS = 124
BTN_CLOSE = 199

EQUIPMENT_LAYERS = (
    "RightHand", "LeftHand", "Shoes", "Pants", "Shirt", "Head",
    "Gloves", "Ring", "Talisman", "Neck", "Hair", "Waist",
    "InnerTorso", "Bracelet", "FacialHair", "MiddleTorso",
    "Earrings", "Arms", "Cloak", "OuterTorso", "OuterLegs",
    "InnerLegs",
)

SPECIAL_EQUIPMENT_SLOTS = ("Backpack", "Quiver", "Mount")

NOTORIETY_NAMES = {
    0: "unknown",
    1: "innocent / blue",
    2: "friend / green",
    3: "attackable / gray",
    4: "criminal / gray",
    5: "enemy / orange",
    6: "murderer / red",
    7: "invulnerable / yellow",
}

SELF_PLAYER_FIELDS = (
    "Name", "Serial", "Body", "MobileID", "Position", "Direction", "Map",
    "Notoriety", "Female", "IsGhost", "Poisoned", "YellowHits", "Visible",
    "WarMode", "Paralized", "Hits", "HitsMax", "Stam", "StamMax", "Mana",
    "ManaMax", "Str", "Dex", "Int", "StatCap", "AR", "FireResistance",
    "ColdResistance", "PoisonResistance", "EnergyResistance", "Gold", "Luck",
    "Weight", "MaxWeight", "Followers", "FollowersMax", "HitChanceIncrease",
    "SwingSpeedIncrease", "DamageChanceIncrease", "LowerReagentCost",
    "HitPointsRegeneration", "StaminaRegeneration", "ManaRegeneration",
    "ReflectPhysicalDamage", "EnhancePotions", "DefenseChanceIncrease",
    "SpellDamageIncrease", "FasterCastRecovery", "FasterCasting", "LowerManaCost",
    "StrengthIncrease", "DexterityIncrease", "IntelligenceIncrease",
    "HitPointsIncrease", "StaminaIncrease", "ManaIncrease",
    "MaximumHitPointsIncrease", "MaximumStaminaIncrease", "HasSpecial",
    "HasPrimarySpecial", "HasSecondarySpecial", "PrimarySpecial", "SecondarySpecial",
    "StaticMount", "Connected", "Buffs", "BuffsInfo", "Pets", "Corpses",
    "Backpack", "Bank", "Quiver", "Mount",
)

STANDARD_SKILLS = (
    "Alchemy", "Anatomy", "Animal Lore", "Item ID", "Arms Lore", "Parrying",
    "Begging", "Blacksmith", "Bowcraft", "Peacemaking", "Camping", "Carpentry",
    "Cartography", "Cooking", "Detect Hidden", "Discordance", "Eval Int",
    "Healing", "Fishing", "Forensics", "Herding", "Hiding", "Provocation",
    "Inscription", "Lockpicking", "Magery", "Magic Resist", "Tactics",
    "Snooping", "Musicianship", "Poisoning", "Archery", "Spirit Speak",
    "Stealing", "Tailoring", "Animal Taming", "Taste ID", "Tinkering",
    "Tracking", "Veterinary", "Swordsmanship", "Mace Fighting", "Fencing",
    "Wrestling", "Lumberjacking", "Mining", "Meditation", "Stealth",
    "Remove Trap", "Necromancy", "Focus", "Chivalry", "Bushido", "Ninjitsu",
    "Spell Weaving", "Mysticism", "Imbuing", "Throwing",
)

PUBLIC_FIELD_COMMENTS = {
    "Name": "Name currently cached for this mobile; OPL line zero can be more complete.",
    "Serial": "Unique runtime identity of this mobile while it exists in the world cache.",
    "Body": "Mobile body or animation model ID. MobileID, Graphics, and ItemID are aliases.",
    "MobileID": "Mobile body or animation model ID used by filters and body matching.",
    "Graphics": "Alias of the mobile body ID.",
    "ItemID": "Compatibility alias of the mobile body ID; this is not a worn item graphic.",
    "Color": "Alias of Hue in the public mobile wrapper.",
    "Hue": "Hue applied to the mobile body artwork.",
    "Position": "Last world X, Y, and Z coordinates cached by Razor Enhanced.",
    "Direction": "Facing direction decoded from the cached movement direction byte.",
    "Map": "Facet/map number cached for the mobile.",
    "DistanceTo": "Callable API method; calculated relationship data is stored separately.",
    "Fame": "Approximate fame range inferred by Razor from the title/profile data.",
    "Karma": "Approximate karma range inferred by Razor from the title/profile data.",
    "KarmaTitle": "Title string cached from profile/title data.",
    "Hits": "Current hit-point value or server-provided health ratio component.",
    "HitsMax": "Maximum hit-point value or server-provided health ratio denominator.",
    "Stam": "Current stamina when the server permits this status data.",
    "StamMax": "Maximum stamina when the server permits this status data.",
    "Mana": "Current mana when the server permits this status data.",
    "ManaMax": "Maximum mana when the server permits this status data.",
    "Visible": "Visibility flag from the most recent mobile packet.",
    "Poisoned": "Poison flag from the mobile status packet.",
    "YellowHits": "Razor's Blessed flag; normally shown as a yellow health bar.",
    "Paralized": "Razor's public misspelling of the paralyzed status flag.",
    "Flying": "Flying-state flag, primarily used by gargoyles.",
    "IsHuman": "True when the body ID is in Razor's built-in human-body list; NPCs can also be human-bodied.",
    "IsGhost": "True when the body ID is in Razor's built-in ghost-body list.",
    "WarMode": "War-mode state from the most recent mobile update.",
    "Female": "Sex flag from the mobile body/status data.",
    "Notoriety": "Numeric client notoriety category used for highlight color and targeting.",
    "CanRename": "Server/client flag commonly associated with controlled pets or summons.",
    "InParty": "Whether Razor's current party cache contains this serial.",
    "PropsUpdated": "Whether Razor has received an object property list for the mobile.",
    "Contains": "Items Razor currently associates with the mobile's paperdoll/equipment list.",
    "Properties": "Raw localized object-property-list entries for the mobile.",
    "Backpack": "Equipped backpack item if that slot is visible in the client cache.",
    "Quiver": "Equipped quiver item if present and cached.",
    "Mount": "Item assigned to the mount layer if present and cached.",
}

INTERNAL_FIELD_COMMENTS = {
    "m_AssistantMobile": "Private Assistant.Mobile object wrapped by RazorEnhanced.Mobile.",
    "m_Serial": "Raw Assistant serial structure behind the public serial.",
    "m_TypeID": "Raw body/type ID cached from mobile packets.",
    "m_Hue": "Raw mobile hue cached from packets.",
    "m_Position": "Raw cached world position.",
    "m_Direction": "Raw direction byte, including running/flying flag bits.",
    "m_Name": "Internal cached name.",
    "m_Notoriety": "Internal numeric notoriety value.",
    "m_Hits": "Internal current hit-point or health-ratio value.",
    "m_HitsMax": "Internal maximum hit-point or health-ratio value.",
    "m_Stam": "Internal stamina cache.",
    "m_StamMax": "Internal maximum stamina cache.",
    "m_Mana": "Internal mana cache.",
    "m_ManaMax": "Internal maximum mana cache.",
    "m_StatsUpdated": "Whether a status response has populated the internal stats cache.",
    "m_PropsUpdated": "Whether an OPL response has populated the properties cache.",
    "m_Items": "Internal collection of paperdoll/equipment items associated with the mobile.",
    "m_Visible": "Internal visibility flag.",
    "m_Poisoned": "Internal poisoned flag.",
    "m_Blessed": "Internal blessed/yellow-hits flag.",
    "m_Paralized": "Internal paralyzed flag.",
    "m_Warmode": "Internal war-mode flag.",
    "m_Female": "Internal sex flag.",
    "m_Flying": "Internal flying-state flag.",
    "m_CanRename": "Internal renameable/pet flag.",
    "m_ContextMenu": "Cached context-menu response IDs and cliloc entries.",
    "m_ObjPropList": "Internal object property list including its revision hash.",
    "m_Hash": "Server-supplied OPL revision hash.",
    "m_StringNums": "Cliloc numbers present in the cached OPL.",
    "m_Content": "Internal ordered OPL entry collection.",
}


# ============================================================
# RUNTIME STATE
# ============================================================

_running = True
_snapshot = None
_current_serial = 0
_current_tab = "summary"
_status_message = "Ready. Target a monster, NPC, pet, or player to begin."
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


def _hex(value, width=8):
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
    return {"decimal": number, "hex": _hex(number, 8)}


def _graphic_record(value):
    try:
        number = int(value)
    except:
        number = 0
    return {"decimal": number, "hex": _hex(number, 4)}


def _point_record(point):
    if point is None:
        return None
    result = {}
    for name in ("X", "Y", "Z"):
        try:
            result[name.lower()] = int(getattr(point, name))
        except:
            pass
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


def _output_dir():
    path = os.path.join(Misc.CurrentScriptDirectory(), OUTPUT_FOLDER)
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def _safe_filename(value):
    text = _clean_text(value) or "mobile"
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
    cleaned = "".join(character if character in allowed else "_" for character in text)
    return (cleaned.strip("_") or "mobile")[:48]


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
            lookup_name, "Public value exposed by this Razor Enhanced build."
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


def _html_annotated_value(name, value, comment, indent=""):
    return (
        "<basefont color={0}>{1}{2}:</basefont> "
        "<basefont color={3}>{4}</basefont> "
        "<basefont color={5}>-- {6}</basefont>"
    ).format(
        HTML_LABEL_COLOR, _html_escape(indent), _html_escape(name),
        HTML_VALUE_COLOR, _html_escape(_short(value, 220)),
        HTML_COMMENT_COLOR, _html_escape(comment)
    )


def _property_record(prop, index):
    return {
        "index": int(index),
        "cliloc": int(_safe_attr(prop, "Number", 0) or 0),
        "cliloc_hex": _hex(_safe_attr(prop, "Number", 0), 8),
        "args": _clean_text(_safe_attr(prop, "Args", "")),
        "text": _clean_text(prop),
    }


def _notoriety_record(value):
    try:
        number = int(value)
    except:
        number = 0
    return {"value": number, "name": NOTORIETY_NAMES.get(number, "unrecognized")}


# ============================================================
# VALUE SERIALIZATION AND REFLECTION
# ============================================================

def _image_metadata(image):
    if image is None:
        return None
    result = {"runtime_type": _runtime_type(image)}
    for name in ("Width", "Height", "HorizontalResolution", "VerticalResolution"):
        try:
            value = getattr(image, name)
            result[name.lower()] = int(value) if name in ("Width", "Height") else float(value)
        except:
            pass
    for name in ("PixelFormat", "RawFormat"):
        try:
            result[name.lower()] = _clean_text(getattr(image, name))
        except:
            pass
    return result


def _simple_entity_record(value):
    return {
        "runtime_type": _runtime_type(value),
        "serial": _serial_record(_safe_attr(value, "Serial", 0)),
        "name": _clean_text(_safe_attr(value, "Name", "")),
        "item_id": _graphic_record(_safe_attr(value, "ItemID", 0)),
        "hue": _graphic_record(_safe_attr(value, "Hue", 0)),
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
                if len(output) >= MAX_REFLECTION_LIST_ITEMS:
                    break
        except Exception as error:
            return {"error": _clean_text(error)}
        return output
    if property_name in ("Contains", "Items", "Equipment"):
        output = []
        try:
            for entry in value:
                output.append(_simple_entity_record(entry))
                if len(output) >= MAX_REFLECTION_LIST_ITEMS:
                    output.append({"truncated": True})
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
    if hasattr(value, "Serial"):
        return _simple_entity_record(value)
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


def _reflect_public_data(obj, fallback_names):
    values = {}
    fields = {}
    errors = {}
    property_names = []
    field_names = []

    try:
        for prop in obj.GetType().GetProperties():
            try:
                if not prop.CanRead or prop.GetIndexParameters().Length > 0:
                    continue
                property_names.append(_clean_text(prop.Name))
            except:
                pass
    except Exception as error:
        errors["GetProperties"] = _clean_text(error)

    for name in fallback_names:
        try:
            getattr(obj, name)
            property_names.append(name)
        except:
            pass

    for name in sorted(set(property_names)):
        try:
            values[name] = _json_value(getattr(obj, name), name)
        except Exception as error:
            errors[name] = _clean_text(error)

    try:
        for field in obj.GetType().GetFields():
            field_names.append(_clean_text(field.Name))
    except Exception as error:
        errors["GetFields"] = _clean_text(error)

    for name in sorted(set(field_names)):
        try:
            fields[name] = _json_value(getattr(obj, name), name)
        except Exception as error:
            errors["field:" + name] = _clean_text(error)

    return {
        "runtime_type": _runtime_type(obj),
        "properties": values,
        "fields": fields,
        "read_errors": errors,
    }


def _reflect_all_instance_members(obj):
    result = {"runtime_type": _runtime_type(obj), "types": [], "read_errors": {}}
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
                    section["properties"][name] = _json_value(
                        prop.GetValue(obj, None), name, 1
                    )
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
                    section["fields"][name] = _json_value(field.GetValue(obj), name, 1)
                except Exception as error:
                    result["read_errors"][type_name + ".field." + name] = _clean_text(error)
            result["types"].append(section)
            current_type = current_type.BaseType
    except Exception as error:
        result["read_errors"]["reflection_setup"] = _clean_text(error)
    return result


def _find_property_object(obj, property_name):
    try:
        import clr
        clr.AddReference("System")
        from System.Reflection import BindingFlags

        flags = (BindingFlags.Instance | BindingFlags.Public |
                 BindingFlags.NonPublic | BindingFlags.DeclaredOnly)
        current_type = obj.GetType()
        while current_type is not None:
            prop = current_type.GetProperty(property_name, flags)
            if prop is not None:
                return prop.GetValue(obj, None)
            current_type = current_type.BaseType
    except:
        pass
    return None


def _internal_mobile_data(mobile):
    result = {
        "available": False,
        "assistant_mobile": None,
        "object_property_list": None,
        "errors": [],
    }
    try:
        import clr
        clr.AddReference("System")
        from System.Reflection import BindingFlags

        flags = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic
        field = mobile.GetType().GetField("m_AssistantMobile", flags)
        if field is None:
            result["errors"].append("RazorEnhanced.Mobile.m_AssistantMobile was not found.")
            return result
        assistant_mobile = field.GetValue(mobile)
        if assistant_mobile is None:
            result["errors"].append("m_AssistantMobile returned None.")
            return result
        result["available"] = True
        result["assistant_mobile"] = _reflect_all_instance_members(assistant_mobile)
        opl_object = _find_property_object(assistant_mobile, "ObjPropList")
        if opl_object is not None:
            result["object_property_list"] = _reflect_all_instance_members(opl_object)
        else:
            result["errors"].append("Assistant UOEntity.ObjPropList was not found.")
    except Exception as error:
        result["errors"].append(_clean_text(error))
    return result


def _internal_item_data(item):
    result = {"available": False, "assistant_item": None, "errors": []}
    if not CAPTURE_EQUIPMENT_INTERNALS:
        result["errors"].append("Equipment internal reflection is disabled in configuration.")
        return result
    try:
        import clr
        clr.AddReference("System")
        from System.Reflection import BindingFlags

        flags = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic
        prop = item.GetType().GetProperty("AsAssistant", flags)
        if prop is None:
            result["errors"].append("RazorEnhanced.Item.AsAssistant was not found.")
            return result
        assistant_item = prop.GetValue(item, None)
        if assistant_item is None:
            result["errors"].append("Item.AsAssistant returned None.")
            return result
        result["available"] = True
        result["assistant_item"] = _reflect_all_instance_members(assistant_item)
    except Exception as error:
        result["errors"].append(_clean_text(error))
    return result


# ============================================================
# MOBILE, OPL, CONTEXT, AND RELATIONSHIP HELPERS
# ============================================================

MOBILE_FALLBACK_FIELDS = (
    "Name", "Serial", "Fame", "Karma", "KarmaTitle", "Body", "MobileID",
    "Position", "Color", "Hue", "Graphics", "ItemID", "PropsUpdated",
    "Visible", "Poisoned", "YellowHits", "Paralized", "Flying", "IsHuman",
    "IsGhost", "WarMode", "Female", "Notoriety", "CanRename", "HitsMax",
    "Hits", "StamMax", "Stam", "ManaMax", "Mana", "Map", "InParty",
    "Mount", "Direction", "Backpack", "Quiver", "Contains", "Properties",
)

ITEM_FALLBACK_FIELDS = (
    "Serial", "ItemID", "Graphics", "Hue", "Color", "Name", "Amount",
    "Container", "RootContainer", "Contains", "Position", "Direction",
    "Layer", "Light", "GridNum", "Visible", "Movable", "OnGround",
    "Deleted", "Updated", "PropsUpdated", "ContainerOpened", "Properties",
    "Weight", "Durability", "MaxDurability", "IsContainer", "IsCorpse",
    "IsLootable", "IsResource", "IsPotion", "IsTwoHanded", "Image",
)


def _mobile_opl(mobile):
    errors = []
    try:
        if not bool(_safe_attr(mobile, "PropsUpdated", False)):
            Mobiles.WaitForProps(mobile.Serial, PROPERTY_WAIT_MS)
    except Exception as error:
        errors.append("WaitForProps: " + _clean_text(error))
    records = []
    try:
        for index, prop in enumerate(list(_safe_attr(mobile, "Properties", []) or [])):
            records.append(_property_record(prop, index))
    except Exception as error:
        errors.append("Properties: " + _clean_text(error))
    rendered = []
    try:
        rendered = [_clean_text(line) for line in Mobiles.GetPropStringList(mobile.Serial)]
    except Exception as error:
        errors.append("GetPropStringList: " + _clean_text(error))
    by_index = []
    for index in range(max(len(records), len(rendered)) + 2):
        try:
            text = _clean_text(Mobiles.GetPropStringByIndex(mobile.Serial, index))
            if not text:
                if index >= len(records) and index >= len(rendered):
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


def _item_opl(item):
    errors = []
    try:
        if not bool(_safe_attr(item, "PropsUpdated", False)):
            Items.WaitForProps(item.Serial, EQUIPMENT_PROPERTY_WAIT_MS)
    except Exception as error:
        errors.append("WaitForProps: " + _clean_text(error))
    records = []
    try:
        for index, prop in enumerate(list(_safe_attr(item, "Properties", []) or [])):
            records.append(_property_record(prop, index))
    except Exception as error:
        errors.append("Properties: " + _clean_text(error))
    rendered = []
    try:
        rendered = [_clean_text(line) for line in Items.GetPropStringList(item.Serial)]
    except Exception as error:
        errors.append("GetPropStringList: " + _clean_text(error))
    return {"raw_opl": records, "rendered_lines": rendered, "errors": errors}


def _context_menu_data(mobile):
    result = {"requested": bool(CAPTURE_CONTEXT_MENU), "entries": [], "error": ""}
    if not CAPTURE_CONTEXT_MENU:
        return result
    try:
        entries = list(Misc.WaitForContext(mobile.Serial, CONTEXT_WAIT_MS, False) or [])
        for index, entry in enumerate(entries):
            result["entries"].append({
                "index": index,
                "text": _clean_text(_safe_attr(entry, "Entry", "")),
                "response": int(_safe_attr(entry, "Response", 0) or 0),
            })
    except Exception as error:
        result["error"] = _clean_text(error)
    return result


def _relationship_data(mobile):
    position = _point_record(_safe_attr(mobile, "Position", None)) or {}
    player_position = _point_record(_safe_attr(Player, "Position", None)) or {}
    distance = None
    try:
        distance = int(Player.DistanceTo(mobile.Serial))
    except:
        try:
            distance = max(
                abs(int(position.get("x", 0)) - int(player_position.get("x", 0))),
                abs(int(position.get("y", 0)) - int(player_position.get("y", 0)))
            )
        except:
            pass
    is_friend = None
    try:
        import Friend
        is_friend = bool(Friend.IsFriend(mobile.Serial))
    except:
        pass
    ignored = None
    try:
        ignored = bool(Misc.CheckIgnoreObject(mobile.Serial))
    except:
        pass
    try:
        last_target = int(Target.GetLast() or 0)
    except:
        last_target = 0
    try:
        last_attack = int(Target.GetLastAttack() or 0)
    except:
        last_attack = 0
    try:
        player_map = int(Player.Map)
    except:
        player_map = None
    mobile_map = _safe_attr(mobile, "Map", None)
    try:
        mobile_map = int(mobile_map)
    except:
        pass
    return {
        "distance_to_player": distance,
        "same_map_as_player": player_map == mobile_map if player_map is not None else None,
        "player_position": player_position,
        "player_map": player_map,
        "is_self": int(mobile.Serial) == int(_safe_attr(Player, "Serial", 0) or 0),
        "in_party": bool(_safe_attr(mobile, "InParty", False)),
        "in_friend_list": is_friend,
        "on_ignore_list": ignored,
        "is_last_target": int(mobile.Serial) == last_target,
        "is_last_attack": int(mobile.Serial) == last_attack,
        "last_target": _serial_record(last_target),
        "last_attack": _serial_record(last_attack),
    }


def _self_player_snapshot(mobile):
    result = {
        "available": int(mobile.Serial) == int(_safe_attr(Player, "Serial", 0) or 0),
        "fields": {},
        "skills": {},
        "area": "",
        "zone": "",
        "read_errors": {},
        "note": "Only populated when the inspected mobile is the logged-in player.",
    }
    if not result["available"]:
        return result

    for name in SELF_PLAYER_FIELDS:
        try:
            result["fields"][name] = _json_value(getattr(Player, name), name)
        except Exception as error:
            result["read_errors"][name] = _clean_text(error)
    try:
        result["area"] = _clean_text(Player.Area())
    except Exception as error:
        result["read_errors"]["Area"] = _clean_text(error)
    try:
        result["zone"] = _clean_text(Player.Zone())
    except Exception as error:
        result["read_errors"]["Zone"] = _clean_text(error)

    if CAPTURE_SELF_SKILLS:
        for skill_name in STANDARD_SKILLS:
            try:
                result["skills"][skill_name] = {
                    "value": float(Player.GetSkillValue(skill_name)),
                    "base": float(Player.GetRealSkillValue(skill_name)),
                    "cap": float(Player.GetSkillCap(skill_name)),
                    "lock": int(Player.GetSkillStatus(skill_name)),
                }
            except Exception as error:
                result["read_errors"]["skill:" + skill_name] = _clean_text(error)
    return result


def _tiledata_snapshot(item_id):
    result = {"item_id": _graphic_record(item_id), "available": False, "reflection": None, "error": ""}
    try:
        data = Statics.GetItemData(int(item_id))
        result["available"] = data is not None
        if data is not None:
            result["reflection"] = _reflect_public_data(data, (
                "Name", "Animation", "Flags", "Weight", "Quality", "Quantity",
                "Value", "Hue", "StackingOffset", "Height", "CalcHeight",
                "MiscData", "Unk2", "Unk3",
            ))
    except Exception as error:
        result["error"] = _clean_text(error)
    return result


def _weapon_abilities(item_id):
    result = {"primary": "", "secondary": "", "error": ""}
    try:
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


# ============================================================
# EQUIPMENT CAPTURE
# ============================================================

def _cached_item_record(item):
    return {
        "serial": _serial_record(_safe_attr(item, "Serial", 0)),
        "item_id": _graphic_record(_safe_attr(item, "ItemID", 0)),
        "hue": _graphic_record(_safe_attr(item, "Hue", 0)),
        "name": _clean_text(_safe_attr(item, "Name", "")),
        "amount": int(_safe_attr(item, "Amount", 0) or 0),
        "layer": _clean_text(_safe_attr(item, "Layer", "")),
        "container": _serial_record(_safe_attr(item, "Container", 0)),
        "position": _point_record(_safe_attr(item, "Position", None)),
    }


def _equipment_item_snapshot(item, sources, layer_hints):
    basic = _cached_item_record(item)
    public = _reflect_public_data(item, ITEM_FALLBACK_FIELDS)
    return {
        "sources": sorted(set(sources)),
        "layer_hints": sorted(set(layer_hints)),
        "item": basic,
        "object_property_list": _item_opl(item),
        "public_reflection": public,
        "internal_reflection": _internal_item_data(item),
        "tiledata": _tiledata_snapshot(basic["item_id"]["decimal"]),
        "weapon_abilities": _weapon_abilities(basic["item_id"]["decimal"]),
    }


def _equipment_snapshot(mobile):
    candidates = {}
    errors = []
    layer_probe_results = {}
    special_slots = {}

    def add_item(item, source, layer_hint):
        if item is None:
            return
        try:
            serial = int(item.Serial)
        except:
            return
        if serial not in candidates:
            candidates[serial] = {"item": item, "sources": [], "layer_hints": []}
        candidates[serial]["sources"].append(source)
        if layer_hint:
            candidates[serial]["layer_hints"].append(layer_hint)

    try:
        contains = list(mobile.Contains or [])
        for item in contains:
            add_item(item, "Mobile.Contains", _clean_text(_safe_attr(item, "Layer", "")))
    except Exception as error:
        contains = []
        errors.append("Mobile.Contains: " + _clean_text(error))

    for layer_name in EQUIPMENT_LAYERS:
        try:
            item = mobile.GetItemOnLayer(layer_name)
            layer_probe_results[layer_name] = _serial_record(item.Serial) if item is not None else None
            add_item(item, "GetItemOnLayer", layer_name)
        except Exception as error:
            layer_probe_results[layer_name] = {"error": _clean_text(error)}

    special_objects = {}
    for slot_name in SPECIAL_EQUIPMENT_SLOTS:
        try:
            item = getattr(mobile, slot_name)
            special_objects[slot_name] = item
            special_slots[slot_name] = _serial_record(item.Serial) if item is not None else None
            add_item(item, "Mobile." + slot_name, slot_name)
        except Exception as error:
            special_objects[slot_name] = None
            special_slots[slot_name] = {"error": _clean_text(error)}

    equipment = []
    for serial in sorted(candidates.keys()):
        candidate = candidates[serial]
        try:
            equipment.append(_equipment_item_snapshot(
                candidate["item"], candidate["sources"], candidate["layer_hints"]
            ))
        except Exception as error:
            errors.append("Equipment {0}: {1}".format(_hex(serial), _clean_text(error)))

    layer_order = dict((name, index) for index, name in enumerate(
        SPECIAL_EQUIPMENT_SLOTS + EQUIPMENT_LAYERS
    ))
    equipment.sort(key=lambda entry: (
        min([layer_order.get(name, 999) for name in entry["layer_hints"]] or [999]),
        entry["item"]["name"].lower(),
        entry["item"]["serial"]["decimal"],
    ))

    backpack_contents = []
    backpack = special_objects.get("Backpack")
    if CAPTURE_KNOWN_BACKPACK_CONTENTS and backpack is not None:
        try:
            for item in list(backpack.Contains or []):
                backpack_contents.append(_cached_item_record(item))
                if len(backpack_contents) >= MAX_CACHED_BACKPACK_ITEMS:
                    break
        except Exception as error:
            errors.append("Cached backpack contents: " + _clean_text(error))

    return {
        "paperdoll_contains_count": len(contains),
        "unique_equipment_count": len(equipment),
        "items": equipment,
        "layer_probes": layer_probe_results,
        "special_slots": special_slots,
        "cached_backpack_contents": backpack_contents,
        "cached_backpack_contents_truncated": len(backpack_contents) >= MAX_CACHED_BACKPACK_ITEMS,
        "errors": errors,
        "note": (
            "Equipment is client-cache data merged from Mobile.Contains, named layer probes, "
            "and Backpack/Quiver/Mount. Other players' backpack contents are normally private."
        ),
    }


# ============================================================
# COMPLETE SNAPSHOT CAPTURE
# ============================================================

def _mobile_summary(mobile):
    return {
        "name": _clean_text(_safe_attr(mobile, "Name", "")) or "<unnamed mobile>",
        "serial": _serial_record(_safe_attr(mobile, "Serial", 0)),
        "body": _graphic_record(_safe_attr(mobile, "MobileID", _safe_attr(mobile, "Body", 0))),
        "hue": _graphic_record(_safe_attr(mobile, "Hue", 0)),
        "position": _point_record(_safe_attr(mobile, "Position", None)),
        "direction": _clean_text(_safe_attr(mobile, "Direction", "")),
        "map": _safe_attr(mobile, "Map", None),
        "notoriety": _notoriety_record(_safe_attr(mobile, "Notoriety", 0)),
        "fame": _safe_attr(mobile, "Fame", None),
        "karma": _safe_attr(mobile, "Karma", None),
        "karma_title": _clean_text(_safe_attr(mobile, "KarmaTitle", "")),
        "stats": {
            "hits": _safe_attr(mobile, "Hits", None),
            "hits_max": _safe_attr(mobile, "HitsMax", None),
            "stam": _safe_attr(mobile, "Stam", None),
            "stam_max": _safe_attr(mobile, "StamMax", None),
            "mana": _safe_attr(mobile, "Mana", None),
            "mana_max": _safe_attr(mobile, "ManaMax", None),
        },
        "flags": {
            "visible": _safe_attr(mobile, "Visible", None),
            "poisoned": _safe_attr(mobile, "Poisoned", None),
            "yellow_hits": _safe_attr(mobile, "YellowHits", None),
            "paralyzed": _safe_attr(mobile, "Paralized", None),
            "flying": _safe_attr(mobile, "Flying", None),
            "human_body": _safe_attr(mobile, "IsHuman", None),
            "ghost_body": _safe_attr(mobile, "IsGhost", None),
            "war_mode": _safe_attr(mobile, "WarMode", None),
            "female": _safe_attr(mobile, "Female", None),
            "can_rename": _safe_attr(mobile, "CanRename", None),
            "in_party": _safe_attr(mobile, "InParty", None),
            "props_updated": _safe_attr(mobile, "PropsUpdated", None),
        },
    }


def _capture_mobile(serial):
    mobile = Mobiles.FindBySerial(int(serial))
    if mobile is None:
        raise ValueError("Target is not an available mobile in Razor Enhanced's cache.")

    errors = []
    try:
        Mobiles.SingleClick(mobile.Serial)
    except Exception as error:
        errors.append("SingleClick: " + _clean_text(error))
    try:
        if not Mobiles.WaitForStats(mobile.Serial, STATS_WAIT_MS):
            errors.append("WaitForStats timed out or the server withheld status data.")
    except Exception as error:
        errors.append("WaitForStats: " + _clean_text(error))
    try:
        if not Mobiles.WaitForProps(mobile.Serial, PROPERTY_WAIT_MS):
            errors.append("WaitForProps timed out or OPL is unavailable.")
    except Exception as error:
        errors.append("WaitForProps: " + _clean_text(error))

    refreshed = Mobiles.FindBySerial(int(serial))
    if refreshed is not None:
        mobile = refreshed

    captured_at = datetime.datetime.now()
    summary = _mobile_summary(mobile)
    snapshot = {
        "tool": {
            "name": "Frog Mobile Inspector",
            "version": "1.0",
            "captured_at_local": captured_at.isoformat(),
            "capture_source": "Razor Enhanced Python API and reflected client cache",
        },
        "mobile": summary,
        "relationships": _relationship_data(mobile),
        "self_player_api": _self_player_snapshot(mobile),
        "object_property_list": _mobile_opl(mobile),
        "context_menu": _context_menu_data(mobile),
        "equipment": _equipment_snapshot(mobile),
        "public_reflection": _reflect_public_data(mobile, MOBILE_FALLBACK_FIELDS),
        "internal_reflection": _internal_mobile_data(mobile),
        "capture_errors": errors,
        "interpretation_notes": [
            "A human body does not prove the mobile is a player; human-bodied NPCs exist.",
            "Non-self stats are limited by what the server sends and may be ratios or zeros.",
            "Equipment and backpack data only include objects already exposed to the client.",
            "The inspector does not double-click or attack the target to populate paperdoll data.",
            "Internal reflected names can change between Razor Enhanced builds.",
        ],
    }
    return snapshot


def _inspect_serial(serial):
    global _snapshot
    global _current_serial
    global _history
    try:
        serial = int(serial or 0)
    except:
        serial = 0
    if serial <= 0:
        _set_status("Mobile targeting cancelled.", MUTED_HUE)
        return False
    if Mobiles.FindBySerial(serial) is None:
        _set_status("That target is not an available mobile.", ERROR_HUE)
        return False
    try:
        _set_status("Inspecting mobile {0}...".format(_hex(serial)), MUTED_HUE)
        snapshot = _capture_mobile(serial)
        _snapshot = snapshot
        _current_serial = serial
        _history.append({
            "captured_at_local": snapshot["tool"]["captured_at_local"],
            "serial": snapshot["mobile"]["serial"],
            "body": snapshot["mobile"]["body"],
            "name": snapshot["mobile"]["name"],
        })
        if len(_history) > MAX_HISTORY:
            _history = _history[-MAX_HISTORY:]
        _set_status(
            "Captured {0} public fields, {1} OPL lines, and {2} equipped item(s).".format(
                len(snapshot["public_reflection"]["properties"]),
                len(snapshot["object_property_list"]["raw_opl"]),
                snapshot["equipment"]["unique_equipment_count"],
            ),
            SUCCESS_HUE
        )
        try:
            Mobiles.Message(serial, SUCCESS_HUE, "Fully inspected", False)
        except:
            pass
        return True
    except Exception as error:
        _set_status("Inspect failed: " + _clean_text(error), ERROR_HUE)
        Misc.SendMessage("[Frog Mobile Inspector] " + _status_message, ERROR_HUE)
        return False


# ============================================================
# FILE EXPORT HELPERS
# ============================================================

def _script_constants(snapshot):
    mobile = snapshot["mobile"]
    equipment = snapshot["equipment"]["items"]
    name = mobile["name"].replace("\\", "\\\\").replace('"', '\\"')
    lines = [
        "# Generated by Frog Mobile Inspector",
        "MOBILE_NAME = \"{0}\"".format(name),
        "MOBILE_SERIAL = {0}".format(mobile["serial"]["hex"]),
        "MOBILE_BODY = {0}".format(mobile["body"]["hex"]),
        "MOBILE_HUE = {0}".format(mobile["hue"]["hex"]),
        "MOBILE_NOTORIETY = {0}".format(mobile["notoriety"]["value"]),
        "",
        "EQUIPMENT = {",
    ]
    for entry in equipment:
        layer = (entry["layer_hints"][0] if entry["layer_hints"] else
                 entry["item"].get("layer", "Unknown") or "Unknown")
        lines.append("    {0!r}: {{'serial': {1}, 'item_id': {2}, 'hue': {3}}},".format(
            layer,
            entry["item"]["serial"]["hex"],
            entry["item"]["item_id"]["hex"],
            entry["item"]["hue"]["hex"],
        ))
    lines.append("}")
    return "\n".join(lines) + "\n"


def _human_report(snapshot):
    mobile = snapshot["mobile"]
    relations = snapshot["relationships"]
    opl = snapshot["object_property_list"]
    equipment = snapshot["equipment"]
    lines = [
        "FROG MOBILE INSPECTOR - ANNOTATED REPORT",
        "Captured: " + snapshot["tool"]["captured_at_local"],
        "",
        "QUICK SUMMARY",
        "-------------",
        "Name: " + mobile["name"],
        "Serial: {0} ({1})".format(mobile["serial"]["hex"], mobile["serial"]["decimal"]),
        "Body: {0} ({1})".format(mobile["body"]["hex"], mobile["body"]["decimal"]),
        "Hue: {0} ({1})".format(mobile["hue"]["hex"], mobile["hue"]["decimal"]),
        "Position: " + _clean_text(mobile["position"]),
        "Direction / Map: {0} / {1}".format(mobile["direction"], mobile["map"]),
        "Notoriety: {0} - {1}".format(mobile["notoriety"]["value"], mobile["notoriety"]["name"]),
        "Distance: " + _clean_text(relations["distance_to_player"]),
        "Stats: hits {0}/{1}, stam {2}/{3}, mana {4}/{5}".format(
            mobile["stats"]["hits"], mobile["stats"]["hits_max"],
            mobile["stats"]["stam"], mobile["stats"]["stam_max"],
            mobile["stats"]["mana"], mobile["stats"]["mana_max"],
        ),
        "Flags: " + _json_text(mobile["flags"]),
        "Relationships: " + _json_text(relations),
        "",
        "OBJECT PROPERTY LIST",
        "--------------------",
    ]
    for prop in opl["raw_opl"]:
        lines.append("[{0}] cliloc={1} args={2!r}".format(
            prop["index"], prop["cliloc"], prop["args"]
        ))
        lines.append("    " + prop["text"])
    if not opl["raw_opl"]:
        lines.append("No raw OPL entries were returned.")
    lines.extend(["", "CONTEXT MENU", "------------"])
    for entry in snapshot["context_menu"]["entries"]:
        lines.append("[{0}] response={1}: {2}".format(
            entry["index"], entry["response"], entry["text"]
        ))
    if not snapshot["context_menu"]["entries"]:
        lines.append("No context-menu entries were returned.")
    lines.extend(["", "EQUIPMENT", "---------", equipment["note"]])
    for entry in equipment["items"]:
        item = entry["item"]
        lines.append("{0} | {1} | {2} hue {3} | {4}".format(
            ", ".join(entry["layer_hints"]) or item["layer"],
            item["serial"]["hex"], item["item_id"]["hex"],
            item["hue"]["hex"], item["name"],
        ))
        lines.append("    sources: " + ", ".join(entry["sources"]))
        for prop_line in entry["object_property_list"]["rendered_lines"]:
            lines.append("    " + prop_line)
    lines.extend(["", "PUBLIC MOBILE API - ANNOTATED", "-----------------------------"])
    for name in sorted(snapshot["public_reflection"]["properties"].keys()):
        lines.append("{0}: {1}".format(name, snapshot["public_reflection"]["properties"][name]))
        lines.append("    Meaning: " + _field_comment(name, "public"))
    self_data = snapshot.get("self_player_api", {})
    if self_data.get("available"):
        lines.extend(["", "SELF-ONLY PLAYER API", "--------------------"])
        lines.append("Area / zone: {0} / {1}".format(self_data["area"], self_data["zone"]))
        for name in sorted(self_data["fields"].keys()):
            lines.append("{0}: {1}".format(name, self_data["fields"][name]))
        lines.append("Skills: " + _json_text(self_data["skills"]))
    lines.extend(["", "INTERNAL RAZOR CACHE", "--------------------"])
    internal = snapshot["internal_reflection"].get("assistant_mobile") or {}
    for section in internal.get("types", []):
        lines.append("[" + section.get("declaring_type", "") + "]")
        for kind in ("properties", "fields"):
            for name in sorted(section.get(kind, {}).keys()):
                lines.append("  {0} {1}: {2}".format(kind[:-1], name, section[kind][name]))
                lines.append("    Meaning: " + _field_comment(name, "internal"))
    lines.extend(["", "FULL STRUCTURED SNAPSHOT", "------------------------", _json_text(snapshot)])
    return "\n".join(lines) + "\n"


def _save_bundle(snapshot):
    folder = _output_dir()
    mobile = snapshot["mobile"]
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    prefix = "{0}_{1}_{2}".format(
        stamp, mobile["serial"]["hex"].replace("0x", ""),
        _safe_filename(mobile["name"])
    )
    paths = {
        "json": os.path.join(folder, prefix + "_raw.json"),
        "text": os.path.join(folder, prefix + "_report.txt"),
        "script": os.path.join(folder, prefix + "_constants.py"),
    }
    _write_text(paths["json"], _json_text(snapshot) + "\n")
    _write_text(paths["text"], _human_report(snapshot))
    _write_text(paths["script"], _script_constants(snapshot))
    _write_text(os.path.join(folder, "latest.json"), _json_text(snapshot) + "\n")
    _write_text(os.path.join(folder, "latest.txt"), _human_report(snapshot))
    _write_text(os.path.join(folder, "latest_constants.py"), _script_constants(snapshot))
    return paths


# ============================================================
# GUMP CONTENT HELPERS
# ============================================================

def _summary_lines(snapshot):
    mobile = snapshot["mobile"]
    relation = snapshot["relationships"]
    stats = mobile["stats"]
    flags = mobile["flags"]
    position = mobile["position"] or {}
    return [
        ("Name", mobile["name"]),
        ("Serial", "{0} / {1}".format(mobile["serial"]["hex"], mobile["serial"]["decimal"])),
        ("Body", "{0} / {1}".format(mobile["body"]["hex"], mobile["body"]["decimal"])),
        ("Hue", "{0} / {1}".format(mobile["hue"]["hex"], mobile["hue"]["decimal"])),
        ("Position", "{0}, {1}, {2} | map {3} | {4}".format(
            position.get("x"), position.get("y"), position.get("z"),
            mobile["map"], mobile["direction"]
        )),
        ("Distance", "{0}; same map={1}".format(
            relation["distance_to_player"], relation["same_map_as_player"]
        )),
        ("Notoriety", "{0}: {1}".format(
            mobile["notoriety"]["value"], mobile["notoriety"]["name"]
        )),
        ("Hits", "{0}/{1}".format(stats["hits"], stats["hits_max"])),
        ("Stamina", "{0}/{1}".format(stats["stam"], stats["stam_max"])),
        ("Mana", "{0}/{1}".format(stats["mana"], stats["mana_max"])),
        ("Identity hints", "self={0}, human body={1}, ghost body={2}, female={3}".format(
            relation["is_self"], flags["human_body"], flags["ghost_body"], flags["female"]
        )),
        ("State", "visible={0}, war={1}, poisoned={2}, paralyzed={3}, flying={4}".format(
            flags["visible"], flags["war_mode"], flags["poisoned"],
            flags["paralyzed"], flags["flying"]
        )),
        ("Relations", "party={0}, friend={1}, ignored={2}, renameable={3}".format(
            relation["in_party"], relation["in_friend_list"],
            relation["on_ignore_list"], flags["can_rename"]
        )),
        ("Targeting", "last target={0}, last attack={1}".format(
            relation["is_last_target"], relation["is_last_attack"]
        )),
        ("Fame / karma", "{0} / {1}; {2}".format(
            mobile["fame"], mobile["karma"], mobile["karma_title"]
        )),
        ("Capture", "{0} public fields, {1} OPL, {2} equipment, {3} context entries".format(
            len(snapshot["public_reflection"]["properties"]),
            len(snapshot["object_property_list"]["raw_opl"]),
            snapshot["equipment"]["unique_equipment_count"],
            len(snapshot["context_menu"]["entries"]),
        )),
    ]


def _internal_rows(reflection):
    rows = []
    for section in reflection.get("types", []):
        declaring_type = section.get("declaring_type", "")
        for kind in ("properties", "fields"):
            for name, value in section.get(kind, {}).items():
                lookup = re.sub(r"^<(.+)>k__BackingField$", r"\1", name)
                priority = 0 if name in INTERNAL_FIELD_COMMENTS or lookup in INTERNAL_FIELD_COMMENTS else 1
                if name.startswith("m_"):
                    priority = min(priority, 1)
                rows.append((priority, declaring_type, kind[:-1], name, value))
    rows.sort(key=lambda row: (row[0], row[1], row[3]))
    return rows


def _tab_html(snapshot, tab_name):
    if not snapshot:
        return "<basefont color={0}>Target a monster, NPC, pet, or player to capture its available data.</basefont>".format(
            HTML_COMMENT_COLOR
        )
    lines = []
    if tab_name == "summary":
        for label, value in _summary_lines(snapshot):
            lines.append("<basefont color={0}>{1}:</basefont> <basefont color={2}>{3}</basefont>".format(
                HTML_LABEL_COLOR, _html_escape(label), HTML_VALUE_COLOR, _html_escape(value)
            ))
        lines.append("<basefont color={0}>Interpretation limits</basefont>".format(HTML_SECTION_COLOR))
        for note in snapshot["interpretation_notes"]:
            lines.append("- " + _html_escape(note))
        warnings = list(snapshot["capture_errors"])
        warnings.extend(snapshot["object_property_list"].get("errors", []))
        warnings.extend(snapshot["equipment"].get("errors", []))
        if snapshot["context_menu"].get("error"):
            warnings.append("Context menu: " + snapshot["context_menu"]["error"])
        if warnings:
            lines.append("<basefont color={0}>Capture warnings</basefont>".format(HTML_ERROR_COLOR))
            lines.extend(_html_escape(error) for error in warnings)

    elif tab_name == "properties":
        opl = snapshot["object_property_list"]
        lines.append("<basefont color={0}>Raw localized OPL entries</basefont>".format(HTML_SECTION_COLOR))
        if not opl["raw_opl"]:
            lines.append("No raw OPL entries were returned.")
        for prop in opl["raw_opl"]:
            lines.append("<basefont color={0}>[{1}] cliloc {2} / {3}</basefont>".format(
                HTML_LABEL_COLOR, prop["index"], prop["cliloc"], prop["cliloc_hex"]
            ))
            lines.append("  text: " + _html_escape(prop["text"]))
            lines.append("  args: " + _html_escape(repr(prop["args"])))
        lines.append("<basefont color={0}>Rendered property strings</basefont>".format(HTML_SECTION_COLOR))
        for index, line in enumerate(opl["rendered_lines"]):
            lines.append("[{0}] {1}".format(index, _html_escape(line)))
        context = snapshot["context_menu"]
        lines.append("<basefont color={0}>Context menu</basefont>".format(HTML_SECTION_COLOR))
        for entry in context["entries"]:
            lines.append("[{0}] response={1}: {2}".format(
                entry["index"], entry["response"], _html_escape(entry["text"])
            ))
        if not context["entries"]:
            lines.append("No context-menu entries were returned.")

    elif tab_name == "equipment":
        equipment = snapshot["equipment"]
        lines.append("<basefont color={0}>Merged equipment and paperdoll capture</basefont>".format(
            HTML_SECTION_COLOR
        ))
        lines.append(_html_escape(equipment["note"]))
        lines.append("Paperdoll list={0}; unique equipment={1}; cached backpack contents={2}".format(
            equipment["paperdoll_contains_count"], equipment["unique_equipment_count"],
            len(equipment["cached_backpack_contents"])
        ))
        for entry in equipment["items"]:
            item = entry["item"]
            layer = ", ".join(entry["layer_hints"]) or item["layer"] or "Unknown layer"
            lines.append("<basefont color={0}>{1}</basefont> <basefont color={2}>{3}</basefont>".format(
                HTML_LABEL_COLOR, _html_escape(layer), HTML_VALUE_COLOR, _html_escape(item["name"])
            ))
            lines.append("  serial {0}; ID {1}; hue {2}; amount {3}".format(
                item["serial"]["hex"], item["item_id"]["hex"], item["hue"]["hex"], item["amount"]
            ))
            lines.append("  source: " + _html_escape(", ".join(entry["sources"])))
            abilities = entry["weapon_abilities"]
            if abilities["primary"] or abilities["secondary"]:
                lines.append("  abilities: {0} / {1}".format(
                    _html_escape(abilities["primary"]), _html_escape(abilities["secondary"])
                ))
            for prop in entry["object_property_list"]["rendered_lines"]:
                lines.append("    " + _html_escape(prop))
        if not equipment["items"]:
            lines.append("No equipment was present in Razor's current cache.")
        if equipment["cached_backpack_contents"]:
            lines.append("<basefont color={0}>Already-cached backpack contents</basefont>".format(
                HTML_SECTION_COLOR
            ))
            for item in equipment["cached_backpack_contents"]:
                lines.append("  {0} {1} hue {2} x{3} {4}".format(
                    item["serial"]["hex"], item["item_id"]["hex"], item["hue"]["hex"],
                    item["amount"], _html_escape(item["name"])
                ))

    elif tab_name == "api":
        reflection = snapshot["public_reflection"]
        lines.append("<basefont color={0}>Razor Enhanced public mobile wrapper</basefont>".format(
            HTML_SECTION_COLOR
        ))
        for name in sorted(reflection["properties"].keys()):
            lines.append(_html_annotated_value(
                name, reflection["properties"][name], _field_comment(name, "public")
            ))
        for name in sorted(reflection["fields"].keys()):
            lines.append(_html_annotated_value(
                "field " + name, reflection["fields"][name], _field_comment(name, "public")
            ))
        for name in sorted(reflection["read_errors"].keys()):
            lines.append("<basefont color={0}>{1}: {2}</basefont>".format(
                HTML_ERROR_COLOR, _html_escape(name), _html_escape(reflection["read_errors"][name])
            ))
        self_data = snapshot.get("self_player_api", {})
        if self_data.get("available"):
            lines.append("<basefont color={0}>Self-only Player API</basefont>".format(
                HTML_SECTION_COLOR
            ))
            lines.append("Area={0}; zone={1}; skills={2}".format(
                _html_escape(self_data["area"]), _html_escape(self_data["zone"]),
                len(self_data["skills"])
            ))
            for name in sorted(self_data["fields"].keys()):
                lines.append("<basefont color={0}>{1}:</basefont> {2}".format(
                    HTML_LABEL_COLOR, _html_escape(name),
                    _html_escape(_short(self_data["fields"][name], 220))
                ))
            lines.append("<basefont color={0}>Skills</basefont>".format(HTML_SECTION_COLOR))
            for name in sorted(self_data["skills"].keys()):
                skill = self_data["skills"][name]
                lines.append("{0}: value={1}; base={2}; cap={3}; lock={4}".format(
                    _html_escape(name), skill["value"], skill["base"],
                    skill["cap"], skill["lock"]
                ))

    elif tab_name == "internals":
        internal = snapshot["internal_reflection"]
        lines.append("<basefont color={0}>Assistant.Mobile internal client cache</basefont>".format(
            HTML_SECTION_COLOR
        ))
        lines.append("available={0}".format(internal["available"]))
        rows = _internal_rows(internal.get("assistant_mobile") or {})
        for _, declaring_type, kind, name, value in rows[:MAX_GUI_INTERNAL_ROWS]:
            lines.append(_html_annotated_value(
                "{0}.{1} {2}".format(declaring_type.split(".")[-1], kind, name),
                value, _field_comment(name, "internal")
            ))
        if len(rows) > MAX_GUI_INTERNAL_ROWS:
            lines.append("<basefont color={0}>Showing {1} of {2} values. SAVE BUNDLE retains all reflected data.</basefont>".format(
                HTML_COMMENT_COLOR, MAX_GUI_INTERNAL_ROWS, len(rows)
            ))
        for error in internal.get("errors", []):
            lines.append("<basefont color={0}>{1}</basefont>".format(
                HTML_ERROR_COLOR, _html_escape(error)
            ))
        lines.append("<basefont color={0}>Equipment internal reflection</basefont>".format(
            HTML_SECTION_COLOR
        ))
        for entry in snapshot["equipment"]["items"]:
            reflected = entry["internal_reflection"]
            lines.append("{0}: available={1}; reflected types={2}; errors={3}".format(
                entry["item"]["serial"]["hex"], reflected["available"],
                len((reflected.get("assistant_item") or {}).get("types", [])),
                len(reflected.get("errors", []))
            ))

    separator = "</basefont><br><basefont color={0}>".format(HTML_TEXT_COLOR)
    return "<basefont color={0}>{1}</basefont>".format(
        HTML_TEXT_COLOR, separator.join(lines)
    )


# ============================================================
# GUMP / GUI FUNCTIONS
# ============================================================

def _add_button(gump, x, y, button_id, label, hue=TEXT_HUE):
    Gumps.AddButton(gump, x, y, 4005, 4007, button_id, 1, 0)
    Gumps.AddLabel(gump, x + 28, y, hue, label)


def _draw_gump():
    global _gump_dirty
    Gumps.CloseGump(GUMP_ID)
    gump = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gump, 0)
    Gumps.AddBackground(gump, 0, 0, GUMP_WIDTH, GUMP_HEIGHT, BACKGROUND_ID)
    Gumps.AddAlphaRegion(gump, 0, 0, GUMP_WIDTH, GUMP_HEIGHT)

    Gumps.AddItem(gump, 7, 4, FROG_ICON, FROG_HUE)
    Gumps.AddLabel(gump, 48, 12, TITLE_HUE, "Frog Mobile Inspector")
    if _snapshot:
        mobile = _snapshot["mobile"]
        title = "{0} | {1} | body {2}".format(
            _short(mobile["name"], 39), mobile["serial"]["hex"], mobile["body"]["hex"]
        )
        Gumps.AddLabel(gump, 230, 12, VALUE_HUE, title)
    Gumps.AddButton(gump, GUMP_WIDTH - 28, 8, 4017, 4019, BTN_CLOSE, 1, 0)

    _add_button(gump, 16, 42, BTN_TARGET, "TARGET", SUCCESS_HUE)
    _add_button(gump, 125, 42, BTN_INSPECT_LAST, "RE LAST", TEXT_HUE)
    _add_button(gump, 235, 42, BTN_REFRESH, "REFRESH", TEXT_HUE)
    _add_button(gump, 345, 42, BTN_CLEAR_LAST, "CLEAR LAST", ERROR_HUE)
    _add_button(gump, 480, 42, BTN_SAVE_FILE, "SAVE BUNDLE", VALUE_HUE)

    tab_data = (
        (BTN_TAB_SUMMARY, "summary", "Summary", 16),
        (BTN_TAB_PROPERTIES, "properties", "OPL / Context", 135),
        (BTN_TAB_EQUIPMENT, "equipment", "Equipment", 285),
        (BTN_TAB_API, "api", "API Data", 420),
        (BTN_TAB_INTERNALS, "internals", "Internals", 540),
    )
    for button_id, tab_name, label, x in tab_data:
        hue = SUCCESS_HUE if _current_tab == tab_name else MUTED_HUE
        _add_button(gump, x, 78, button_id, label, hue)

    Gumps.AddAlphaRegion(gump, 12, 108, GUMP_WIDTH - 24, 344)
    Gumps.AddHtml(
        gump, 18, 114, GUMP_WIDTH - 36, 330,
        _tab_html(_snapshot, _current_tab), False, True
    )
    Gumps.AddLabel(gump, 16, 464, _status_hue, _short(_status_message, 98))
    Gumps.AddLabel(
        gump, 16, 496, MUTED_HUE,
        "Saves: Scripts/FrogDevelopmentTools/data/mobiles | Captures this run: {0}".format(len(_history))
    )
    Gumps.SendGump(
        GUMP_ID, Player.Serial, GUMP_X, GUMP_Y,
        gump.gumpDefinition, gump.gumpStrings
    )
    _gump_dirty = False


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
    global _current_tab
    if button_id == BTN_CLOSE:
        _running = False
        return
    if button_id == BTN_TARGET:
        serial = Target.PromptTarget("Target a monster, NPC, pet, or player", MUTED_HUE)
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
            _set_status("Nothing to refresh. Target a mobile first.", ERROR_HUE)
        return
    if button_id == BTN_CLEAR_LAST:
        _clear_last()
        return
    if button_id == BTN_SAVE_FILE:
        if not _snapshot:
            _set_status("Nothing to save. Target a mobile first.", ERROR_HUE)
            return
        try:
            paths = _save_bundle(_snapshot)
            _set_status("Saved mobile bundle: " + paths["json"], SUCCESS_HUE)
        except Exception as error:
            _set_status("Save failed: " + _clean_text(error), ERROR_HUE)
        return
    tabs = {
        BTN_TAB_SUMMARY: "summary",
        BTN_TAB_PROPERTIES: "properties",
        BTN_TAB_EQUIPMENT: "equipment",
        BTN_TAB_API: "api",
        BTN_TAB_INTERNALS: "internals",
    }
    if button_id in tabs:
        _current_tab = tabs[button_id]


# ============================================================
# MAIN
# ============================================================

def Main():
    global _running
    global _gump_dirty
    _draw_gump()
    try:
        while _running and Player.Connected:
            gump_data = Gumps.GetGumpData(GUMP_ID)
            has_response = bool(getattr(gump_data, "hasResponse", False)) if gump_data else False
            button_id = int(getattr(gump_data, "buttonid", 0)) if gump_data else 0
            if has_response or button_id > 0:
                try:
                    gump_data.buttonid = 0
                    gump_data.hasResponse = False
                except:
                    pass
                Gumps.CloseGump(GUMP_ID)
                _handle_button(button_id)
                _gump_dirty = True
                Misc.Pause(BUTTON_DEBOUNCE_MS)
            if _gump_dirty and _running:
                _draw_gump()
            Misc.Pause(GUMP_REFRESH_MS)
    except Exception as error:
        Misc.SendMessage("[Frog Mobile Inspector] Stopped: " + _clean_text(error), ERROR_HUE)
    finally:
        Gumps.CloseGump(GUMP_ID)


Main()
