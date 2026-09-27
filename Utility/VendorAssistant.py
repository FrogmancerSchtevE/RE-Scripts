# ============================================================
# Frog Vendor Explorer 2.0
# Razor Enhanced vendor-container browser and purchase helper
# ============================================================

import re
import time

import Gumps
import Items
import Misc
import Mobiles
import Player
import Target


# ============================================================
# CONFIGURATION
# ============================================================

GUMP_ID = 0xF2065641
GUMP_X = 180
GUMP_Y = 120
GUMP_WIDTH = 770
GUMP_HEIGHT = 555
GUMP_REFRESH_MS = 100
BUTTON_DEBOUNCE_MS = 175
CONTENTS_WAIT_MS = 2000
PROPERTY_WAIT_MS = 650
VENDOR_RESOLVE_WAIT_MS = 350
ROWS_PER_PAGE = 11

BUY_CONTEXT_RESPONSE = 0
REQUIRE_BUY_CONFIRMATION = True
BUY_CONFIRM_SECONDS = 4.0

FROG_ICON = 0x2130
FROG_HUE = 1152
BACKGROUND_ID = 5054
ROW_BACKGROUND_ID = 2624

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
HTML_COMMENT_COLOR = "#B8D8A8"
HTML_ERROR_COLOR = "#FF8080"

ENTRY_FILTER = 8000

BTN_TARGET = 100
BTN_REFRESH = 101
BTN_FILTER = 102
BTN_CLEAR_FILTER = 103
BTN_SORT = 104
BTN_DIRECTION = 105
BTN_PREVIOUS = 106
BTN_NEXT = 107
BTN_SHOW = 108
BTN_REVEAL = 109
BTN_BUY = 110
BTN_CLOSE = 199

SORT_MODES = ("name", "price", "item id")


# ============================================================
# RUNTIME STATE
# ============================================================

_running = True
_dirty = True
_container_serial = 0
_vendor_serial = 0
_container_source = ""
_items_cache = []
_visible_items = []
_selected_serial = 0
_current_page = 1
_filter_text = ""
_sort_mode_index = 0
_sort_ascending = True
_buy_armed_serial = 0
_buy_armed_until = 0.0
_status_message = "Target a vendor, vendor backpack, or display container to begin."
_status_hue = MUTED_HUE


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


def _short(value, length):
    text = _clean_text(value)
    if len(text) <= length:
        return text
    return text[:max(0, length - 3)].rstrip() + "..."


def _hex(value, width=8):
    try:
        mask = (1 << (width * 4)) - 1
        return "0x{0:0{1}X}".format(int(value) & mask, width)
    except:
        return "0x" + ("0" * width)


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


def _read_entry(gump_data, entry_id, default=""):
    try:
        value = Gumps.GetTextByID(gump_data, entry_id)
        if value is not None:
            return _clean_text(value)
    except:
        pass
    try:
        ids = list(gump_data.textID)
        values = list(gump_data.text)
        for index, current_id in enumerate(ids):
            if int(current_id) == int(entry_id) and index < len(values):
                return _clean_text(values[index])
    except:
        pass
    return default


def _current_sort_mode():
    return SORT_MODES[_sort_mode_index % len(SORT_MODES)]


def _selected_record():
    for record in _items_cache:
        if record["serial"] == _selected_serial:
            return record
    return None


def _mobile_backpack(mobile):
    """Return a mobile's equipped backpack, allowing for a short paperdoll refresh."""
    try:
        backpack = mobile.Backpack
    except:
        backpack = None
    if backpack is not None:
        return backpack

    # Some mobiles do not expose their equipment until the client has requested
    # the paperdoll. A use request is harmless here and gives RE a chance to
    # populate Mobile.Backpack before we report that no container was found.
    try:
        Mobiles.UseMobile(mobile.Serial)
        Misc.Pause(VENDOR_RESOLVE_WAIT_MS)
        refreshed = Mobiles.FindBySerial(mobile.Serial)
        return refreshed.Backpack if refreshed is not None else None
    except:
        return None


def _resolve_vendor_target(serial):
    """Resolve either a container item or a vendor mobile to a container item."""
    item = Items.FindBySerial(serial)
    if item is not None:
        return item, 0, "targeted container"

    mobile = Mobiles.FindBySerial(serial)
    if mobile is None:
        return None, 0, ""

    backpack = _mobile_backpack(mobile)
    if backpack is None:
        return None, int(mobile.Serial), ""
    return backpack, int(mobile.Serial), "vendor backpack"


# ============================================================
# VENDOR DATA PARSING
# ============================================================

def _parse_price(properties):
    for line in properties:
        text = _clean_text(line)
        if "price" not in text.lower():
            continue
        match = re.search(r"price\s*:?\s*(\d[\d,]*)", text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1).replace(",", ""))
            except:
                pass
    return 0


def _parse_deed_quantity(properties):
    for line in properties:
        text = _clean_text(line)
        match = re.search(r"contains\s*:\s*(.+)$", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def _parse_relic_type(properties):
    for line in properties:
        text = _clean_text(line)
        if "relic" in text.lower() and "ability" not in text.lower():
            return text
    return ""


def _display_name(item, properties):
    name = _clean_text(item.Name) or "<unnamed>"
    if name.lower() == "a commodity deed":
        quantity = _parse_deed_quantity(properties)
        if quantity:
            return "Commodity deed ({0})".format(quantity)
    lowered = name.lower()
    if "relic" in lowered and "ability" in lowered:
        relic_type = _parse_relic_type(properties)
        if relic_type:
            return "Creature Ability Relic ({0})".format(
                relic_type.replace("Relic", "").strip()
            )
    return name


def _item_properties(item):
    try:
        if not bool(getattr(item, "PropsUpdated", False)):
            Items.WaitForProps(item.Serial, PROPERTY_WAIT_MS)
    except:
        pass
    try:
        return [_clean_text(line) for line in Items.GetPropStringList(item.Serial)]
    except:
        return []


def _item_record(item):
    properties = _item_properties(item)
    position = getattr(item, "Position", None)
    return {
        "serial": int(item.Serial),
        "name": _display_name(item, properties),
        "raw_name": _clean_text(item.Name) or "<unnamed>",
        "price": _parse_price(properties),
        "amount": int(getattr(item, "Amount", 0) or 0),
        "item_id": int(getattr(item, "ItemID", 0) or 0),
        "hue": int(getattr(item, "Hue", 0) or 0),
        "x": int(getattr(position, "X", 0) or 0) if position is not None else 0,
        "y": int(getattr(position, "Y", 0) or 0) if position is not None else 0,
        "properties": properties,
    }


def _record_matches(record, query):
    if not query:
        return True
    haystack = " ".join((
        record["name"].lower(),
        record["raw_name"].lower(),
        str(record["price"]),
        str(record["amount"]),
        str(record["item_id"]),
        _hex(record["item_id"], 4).lower(),
        str(record["hue"]),
        _hex(record["hue"], 4).lower(),
        " ".join(record["properties"]).lower(),
    ))
    return query.lower() in haystack


def _sort_key(record):
    mode = _current_sort_mode()
    if mode == "price":
        return (record["price"], record["name"].lower(), record["serial"])
    if mode == "item id":
        return (record["item_id"], record["hue"], record["name"].lower())
    return (record["name"].lower(), record["price"], record["serial"])


def _rebuild_visible_items():
    global _visible_items
    global _current_page
    matches = [record for record in _items_cache if _record_matches(record, _filter_text)]
    matches.sort(key=_sort_key, reverse=not _sort_ascending)
    _visible_items = matches
    total_pages = max(1, (len(_visible_items) + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)
    _current_page = min(max(1, _current_page), total_pages)


def _refresh_inventory(success_message="Refreshed vendor inventory"):
    global _items_cache
    global _selected_serial
    if _container_serial <= 0:
        _items_cache = []
        _rebuild_visible_items()
        _set_status("Target a vendor container first.", ERROR_HUE)
        return False
    container = Items.FindBySerial(_container_serial)
    if container is None:
        _items_cache = []
        _rebuild_visible_items()
        _set_status("The vendor container is no longer available.", ERROR_HUE)
        return False

    try:
        Items.UseItem(_container_serial)
        Items.WaitForContents(_container_serial, CONTENTS_WAIT_MS)
    except:
        pass
    container = Items.FindBySerial(_container_serial)
    records = []
    try:
        for item in list(container.Contains or []):
            records.append(_item_record(item))
    except Exception as error:
        _set_status("Could not read vendor contents: " + _clean_text(error), ERROR_HUE)
        return False

    _items_cache = records
    if _selected_serial and not any(record["serial"] == _selected_serial for record in records):
        _selected_serial = 0
    _rebuild_visible_items()
    _set_status("{0} ({1} item(s)).".format(success_message, len(records)), SUCCESS_HUE)
    return True


def _target_vendor_container():
    global _container_serial
    global _vendor_serial
    global _container_source
    global _selected_serial
    global _current_page
    try:
        serial = int(Target.PromptTarget(
            "Target vendor, vendor backpack, or display container", MUTED_HUE
        ) or 0)
    except:
        serial = 0
    if serial <= 0:
        _set_status("Vendor targeting cancelled.", MUTED_HUE)
        return

    container, vendor_serial, source = _resolve_vendor_target(serial)
    if container is None:
        if vendor_serial:
            _set_status(
                "That mobile has no readable backpack. Open its paperdoll and try again.",
                ERROR_HUE
            )
        else:
            _set_status("That target is not an available vendor or container.", ERROR_HUE)
        return

    _container_serial = int(container.Serial)
    _vendor_serial = vendor_serial
    _container_source = source
    _selected_serial = 0
    _current_page = 1
    if vendor_serial:
        loaded_message = "Resolved vendor {0} to backpack {1}".format(
            _hex(vendor_serial), _hex(_container_serial)
        )
    else:
        loaded_message = "Loaded targeted vendor container"
    _refresh_inventory(loaded_message)


# ============================================================
# SELECTED ITEM ACTIONS
# ============================================================

def _select_item(serial):
    global _selected_serial
    global _buy_armed_serial
    global _buy_armed_until
    item = Items.FindBySerial(serial)
    if item is None:
        _set_status("That vendor item is no longer available.", ERROR_HUE)
        _refresh_inventory()
        return
    _selected_serial = int(serial)
    _buy_armed_serial = 0
    _buy_armed_until = 0.0
    record = _selected_record()
    _set_status("Selected " + (record["name"] if record else _hex(serial)), VALUE_HUE)


def _show_selected():
    record = _selected_record()
    if record is None:
        _set_status("Select an item first.", ERROR_HUE)
        return
    Items.SingleClick(record["serial"])
    _set_status("Requested the selected item's client display.", SUCCESS_HUE)


def _reveal_selected():
    record = _selected_record()
    item = Items.FindBySerial(record["serial"]) if record else None
    if record is None or item is None:
        _set_status("Select an available item first.", ERROR_HUE)
        return
    try:
        # Correct Razor Enhanced overload order: source, destination, amount, x, y.
        Items.Move(
            item.Serial, _container_serial, max(1, int(item.Amount)),
            int(item.Position.X), int(item.Position.Y)
        )
        Misc.Pause(200)
        Items.SingleClick(item.Serial)
        _set_status("Reveal request sent for the selected item.", SUCCESS_HUE)
    except Exception as error:
        _set_status("Reveal failed: " + _clean_text(error), ERROR_HUE)


def _buy_selected():
    global _buy_armed_serial
    global _buy_armed_until
    record = _selected_record()
    if record is None:
        _set_status("Select an item first.", ERROR_HUE)
        return

    now = time.time()
    if REQUIRE_BUY_CONFIRMATION:
        if _buy_armed_serial != record["serial"] or now > _buy_armed_until:
            _buy_armed_serial = record["serial"]
            _buy_armed_until = now + BUY_CONFIRM_SECONDS
            _set_status(
                "Confirm purchase: click BUY again within {0:.0f}s for {1}.".format(
                    BUY_CONFIRM_SECONDS, record["name"]
                ),
                VALUE_HUE
            )
            return

    try:
        Items.SingleClick(record["serial"])
        context = Misc.WaitForContext(record["serial"], 5000, False)
        if context is None or len(list(context)) == 0:
            _set_status("No purchase context menu was returned.", ERROR_HUE)
            return
        Misc.ContextReply(record["serial"], BUY_CONTEXT_RESPONSE)
        _buy_armed_serial = 0
        _buy_armed_until = 0.0
        Player.HeadMessage(SUCCESS_HUE, "Purchase request sent.")
        Misc.Pause(300)
        _refresh_inventory("Purchase request sent; refreshed inventory")
    except Exception as error:
        _set_status("Purchase failed: " + _clean_text(error), ERROR_HUE)


def _expire_buy_confirmation():
    global _buy_armed_serial
    global _buy_armed_until
    global _dirty
    if _buy_armed_serial and time.time() > _buy_armed_until:
        _buy_armed_serial = 0
        _buy_armed_until = 0.0
        _set_status("Purchase confirmation expired; no purchase was sent.", MUTED_HUE)
        _dirty = True


# ============================================================
# GUMP CONTENT
# ============================================================

def _details_html():
    record = _selected_record()
    lines = []
    if record is None:
        lines.append("<basefont color={0}>Vendor overview</basefont>".format(HTML_SECTION_COLOR))
        if _container_serial <= 0:
            lines.extend([
                "Use TARGET on the vendor, its backpack, or a display container.",
                "A vendor mobile is automatically resolved to its equipped backpack.",
                "Rows select items; purchasing is always a separate fixed action.",
                "The default safety setting requires a second BUY click within four seconds.",
            ])
        else:
            total_price = sum(record["price"] for record in _visible_items)
            lines.extend([
                "Source: {0}".format(_container_source or "container"),
                "Vendor: {0} / {1}".format(_hex(_vendor_serial), _vendor_serial)
                    if _vendor_serial else "Vendor: direct container target",
                "Container: {0} / {1}".format(_hex(_container_serial), _container_serial),
                "Inventory items: {0}; filter matches: {1}".format(
                    len(_items_cache), len(_visible_items)
                ),
                "Known listed-price total for matches: {0:,}".format(total_price),
                "<basefont color={0}>Workflow</basefont>".format(HTML_SECTION_COLOR),
                "Select a row to inspect its entire cached property list.",
                "SHOW requests a single-click display without changing item hue.",
                "REVEAL resends the item at its current vendor-container coordinates.",
                "BUY uses context response {0}; change BUY_CONTEXT_RESPONSE if your shard differs.".format(
                    BUY_CONTEXT_RESPONSE
                ),
            ])
        return _html_lines(lines)

    lines.extend([
        "<basefont color={0}>Selected listing</basefont>".format(HTML_SECTION_COLOR),
        "<basefont color={0}>Name:</basefont> <basefont color={1}>{2}</basefont>".format(
            HTML_LABEL_COLOR, HTML_VALUE_COLOR, _html_escape(record["name"])
        ),
        "Raw name: " + _html_escape(record["raw_name"]),
        "Serial: {0} / {1}".format(_hex(record["serial"]), record["serial"]),
        "Item ID: {0} / {1}".format(_hex(record["item_id"], 4), record["item_id"]),
        "Hue: {0} / {1}".format(_hex(record["hue"], 4), record["hue"]),
        "Amount: {0}".format(record["amount"]),
        "Parsed price: {0:,}".format(record["price"]),
        "Container coordinates: {0},{1}".format(record["x"], record["y"]),
        "<basefont color={0}>Object property list</basefont>".format(HTML_SECTION_COLOR),
    ])
    if record["properties"]:
        for index, line in enumerate(record["properties"]):
            lines.append("[{0}] {1}".format(index, _html_escape(line)))
    else:
        lines.append("No property lines were returned.")
    lines.append("<basefont color={0}>Price parsing is best-effort; verify the listing before purchase.</basefont>".format(
        HTML_COMMENT_COLOR
    ))
    return _html_lines(lines)


def _add_button(gump, x, y, button_id, label, hue=TEXT_HUE):
    Gumps.AddButton(gump, x, y, 4005, 4007, button_id, 1, 0)
    Gumps.AddLabel(gump, x + 28, y, hue, label)


def _draw_gump():
    global _dirty
    Gumps.CloseGump(GUMP_ID)
    gump = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gump, 0)
    Gumps.AddBackground(gump, 0, 0, GUMP_WIDTH, GUMP_HEIGHT, BACKGROUND_ID)
    Gumps.AddAlphaRegion(gump, 0, 0, GUMP_WIDTH, GUMP_HEIGHT)

    Gumps.AddItem(gump, 7, 4, FROG_ICON, FROG_HUE)
    Gumps.AddLabel(gump, 48, 12, TITLE_HUE, "Frog Vendor Explorer")
    if _container_serial > 0:
        Gumps.AddLabel(gump, 248, 12, VALUE_HUE, "Container " + _hex(_container_serial))
    Gumps.AddButton(gump, GUMP_WIDTH - 28, 8, 4017, 4019, BTN_CLOSE, 1, 0)

    _add_button(gump, 16, 43, BTN_TARGET, "TARGET VENDOR/BAG", SUCCESS_HUE)
    _add_button(gump, 183, 43, BTN_REFRESH, "REFRESH", TEXT_HUE)

    Gumps.AddLabel(gump, 16, 77, TEXT_HUE, "Find")
    Gumps.AddTextEntry(gump, 58, 75, 155, 22, TEXT_HUE, ENTRY_FILTER, _filter_text)
    _add_button(gump, 225, 75, BTN_FILTER, "APPLY", SUCCESS_HUE)
    _add_button(gump, 324, 75, BTN_CLEAR_FILTER, "CLEAR", MUTED_HUE)
    _add_button(gump, 422, 75, BTN_SORT, "SORT: " + _current_sort_mode().upper(), VALUE_HUE)
    _add_button(gump, 590, 75, BTN_DIRECTION, "ASC" if _sort_ascending else "DESC", TEXT_HUE)

    Gumps.AddAlphaRegion(gump, 12, 108, 424, 354)
    Gumps.AddLabel(gump, 18, 112, TITLE_HUE, "Vendor item")
    Gumps.AddLabel(gump, 300, 112, TITLE_HUE, "Price")
    Gumps.AddLabel(gump, 373, 112, TITLE_HUE, "ID")

    start = (_current_page - 1) * ROWS_PER_PAGE
    page_items = _visible_items[start:start + ROWS_PER_PAGE]
    y = 138
    for record in page_items:
        selected = record["serial"] == _selected_serial
        if selected:
            Gumps.AddImageTiled(gump, 16, y - 3, 412, 28, ROW_BACKGROUND_ID)
        Gumps.AddItem(gump, 18, y - 7, record["item_id"], record["hue"])
        Gumps.AddButton(gump, 54, y, 4005, 4007, record["serial"], 1, 0)
        Gumps.AddLabel(
            gump, 81, y, SUCCESS_HUE if selected else VALUE_HUE,
            _short(record["name"], 30)
        )
        Gumps.AddLabel(gump, 300, y, TEXT_HUE, "{0:,}".format(record["price"]))
        Gumps.AddLabel(gump, 373, y, MUTED_HUE, _hex(record["item_id"], 4))
        y += 29

    total_pages = max(1, (len(_visible_items) + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)
    if _current_page > 1:
        _add_button(gump, 18, 468, BTN_PREVIOUS, "PREV", TEXT_HUE)
    Gumps.AddLabel(gump, 175, 470, MUTED_HUE, "Page {0}/{1} | {2} shown".format(
        _current_page, total_pages, len(_visible_items)
    ))
    if _current_page < total_pages:
        _add_button(gump, 350, 468, BTN_NEXT, "NEXT", TEXT_HUE)

    Gumps.AddAlphaRegion(gump, 446, 108, 312, 354)
    Gumps.AddHtml(gump, 454, 116, 296, 338, _details_html(), False, True)
    _add_button(gump, 452, 468, BTN_SHOW, "SHOW", TEXT_HUE)
    _add_button(gump, 548, 468, BTN_REVEAL, "REVEAL", VALUE_HUE)
    buy_hue = ERROR_HUE if _buy_armed_serial == _selected_serial and time.time() <= _buy_armed_until else SUCCESS_HUE
    _add_button(gump, 650, 468, BTN_BUY, "BUY", buy_hue)

    Gumps.AddLabel(gump, 16, 520, _status_hue, _short(_status_message, 105))
    Gumps.SendGump(
        GUMP_ID, Player.Serial, GUMP_X, GUMP_Y,
        gump.gumpDefinition, gump.gumpStrings
    )
    _dirty = False


# ============================================================
# BUTTON HANDLING
# ============================================================

def _handle_button(button_id, filter_value):
    global _running
    global _dirty
    global _filter_text
    global _current_page
    global _sort_mode_index
    global _sort_ascending

    if button_id == 0 or button_id == BTN_CLOSE:
        _running = False
        return
    if button_id == BTN_TARGET:
        _target_vendor_container()
    elif button_id == BTN_REFRESH:
        _refresh_inventory()
    elif button_id == BTN_FILTER:
        _filter_text = filter_value
        _current_page = 1
        _rebuild_visible_items()
        _set_status("Filter applied: " + (_filter_text or "all listings"), SUCCESS_HUE)
    elif button_id == BTN_CLEAR_FILTER:
        _filter_text = ""
        _current_page = 1
        _rebuild_visible_items()
        _set_status("Filter cleared.", MUTED_HUE)
    elif button_id == BTN_SORT:
        _sort_mode_index = (_sort_mode_index + 1) % len(SORT_MODES)
        _rebuild_visible_items()
        _set_status("Sorted by " + _current_sort_mode() + ".", VALUE_HUE)
    elif button_id == BTN_DIRECTION:
        _sort_ascending = not _sort_ascending
        _rebuild_visible_items()
        _set_status("Sort direction: " + ("ascending" if _sort_ascending else "descending"), VALUE_HUE)
    elif button_id == BTN_PREVIOUS:
        _current_page = max(1, _current_page - 1)
    elif button_id == BTN_NEXT:
        total_pages = max(1, (len(_visible_items) + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)
        _current_page = min(total_pages, _current_page + 1)
    elif button_id == BTN_SHOW:
        _show_selected()
    elif button_id == BTN_REVEAL:
        _reveal_selected()
    elif button_id == BTN_BUY:
        _buy_selected()
    elif button_id > 0:
        _select_item(button_id)
    _dirty = True


# ============================================================
# MAIN
# ============================================================

def Main():
    global _running
    global _dirty
    _draw_gump()
    try:
        while _running and Player.Connected:
            _expire_buy_confirmation()
            gump_data = Gumps.GetGumpData(GUMP_ID)
            has_response = bool(getattr(gump_data, "hasResponse", False)) if gump_data else False
            button_id = int(getattr(gump_data, "buttonid", 0)) if gump_data else 0
            if has_response or button_id > 0:
                filter_value = _read_entry(gump_data, ENTRY_FILTER, _filter_text)
                try:
                    gump_data.buttonid = 0
                    gump_data.hasResponse = False
                except:
                    pass
                Gumps.CloseGump(GUMP_ID)
                _handle_button(button_id, filter_value)
                Misc.Pause(BUTTON_DEBOUNCE_MS)
            if _dirty and _running:
                _draw_gump()
            Misc.Pause(GUMP_REFRESH_MS)
    except Exception as error:
        Misc.SendMessage("[Frog Vendor Explorer] Stopped: " + _clean_text(error), ERROR_HUE)
    finally:
        Gumps.CloseGump(GUMP_ID)


Main()
