# ============================================================
# Frog Container Explorer 2.2
# Razor Enhanced container browser with safe item actions
# ============================================================

import Gumps
import Items
import Misc
import Mobiles
import Player
import Target


# ============================================================
# CONFIGURATION
# ============================================================

GUMP_ID = 0xF2064345
GUMP_X = 180
GUMP_Y = 120
GUMP_WIDTH = 770
GUMP_HEIGHT = 555
GUMP_REFRESH_MS = 100
BUTTON_DEBOUNCE_MS = 175
CONTENTS_WAIT_MS = 1800
PROPERTY_WAIT_MS = 700
MOVE_WAIT_MS = 2500
MOVE_POLL_MS = 100
ROWS_PER_PAGE = 11

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
BTN_BACKPACK = 101
BTN_REFRESH = 102
BTN_BACK = 103
BTN_FILTER = 104
BTN_CLEAR_FILTER = 105
BTN_SORT = 106
BTN_DIRECTION = 107
BTN_PREVIOUS = 108
BTN_NEXT = 109
BTN_SHOW = 110
BTN_OPEN = 111
BTN_TAKE = 112
BTN_CLOSE = 199
ROW_SELECT_BUTTON_BASE = 1000

SORT_MODES = ("name", "amount", "item id", "hue")


# ============================================================
# RUNTIME STATE
# ============================================================

_running = True
_dirty = True
_container_serial = 0
_container_stack = []
_items_cache = []
_visible_items = []
_selected_serial = 0
_selected_properties = []
_row_select_targets = {}
_current_page = 1
_filter_text = ""
_sort_mode_index = 0
_sort_ascending = True
_status_message = "Choose TARGET or BACKPACK to begin."
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


def _container_name(serial):
    item = Items.FindBySerial(serial)
    if item is None:
        return "container"
    return _clean_text(item.Name) or "container"


def _selected_item():
    if _selected_serial <= 0:
        return None
    return Items.FindBySerial(_selected_serial)


def _player_backpack():
    """Resolve the backpack across Razor Enhanced's available wrapper paths."""
    try:
        backpack = Player.Backpack
        if backpack is not None:
            return backpack
    except:
        pass
    try:
        backpack = Player.GetItemOnLayer("Backpack")
        if backpack is not None:
            return backpack
    except:
        pass
    try:
        player_mobile = Mobiles.FindBySerial(Player.Serial)
        if player_mobile is not None:
            return player_mobile.Backpack
    except:
        pass
    return None


def _item_parent_serial(item):
    try:
        return int(item.Container)
    except:
        return 0


def _wait_for_item_to_leave(serial, source_serial):
    """Wait for the drag/drop queue to move or merge the selected stack."""
    elapsed = 0
    while elapsed < MOVE_WAIT_MS:
        current = Items.FindBySerial(serial)
        if current is None or _item_parent_serial(current) != int(source_serial):
            return True
        Misc.Pause(MOVE_POLL_MS)
        elapsed += MOVE_POLL_MS
    return False


def _current_sort_mode():
    return SORT_MODES[_sort_mode_index % len(SORT_MODES)]


# ============================================================
# CONTAINER AND ITEM DATA
# ============================================================

def _item_record(item):
    position = getattr(item, "Position", None)
    return {
        "serial": int(item.Serial),
        "name": _clean_text(item.Name) or "<unnamed>",
        "amount": int(getattr(item, "Amount", 0) or 0),
        "item_id": int(getattr(item, "ItemID", 0) or 0),
        "hue": int(getattr(item, "Hue", 0) or 0),
        "is_container": bool(getattr(item, "IsContainer", False)),
        "x": int(getattr(position, "X", 0) or 0) if position is not None else 0,
        "y": int(getattr(position, "Y", 0) or 0) if position is not None else 0,
        "grid": int(getattr(item, "GridNum", 0) or 0),
    }


def _record_matches(record, query):
    if not query:
        return True
    haystack = " ".join((
        record["name"].lower(),
        str(record["amount"]),
        str(record["item_id"]),
        _hex(record["item_id"], 4).lower(),
        str(record["hue"]),
        _hex(record["hue"], 4).lower(),
        str(record["serial"]),
        _hex(record["serial"]).lower(),
    ))
    return query.lower() in haystack


def _sort_key(record):
    mode = _current_sort_mode()
    if mode == "amount":
        return (record["amount"], record["name"].lower(), record["serial"])
    if mode == "item id":
        return (record["item_id"], record["hue"], record["name"].lower())
    if mode == "hue":
        return (record["hue"], record["item_id"], record["name"].lower())
    return (record["name"].lower(), record["item_id"], record["serial"])


def _rebuild_visible_items():
    global _visible_items
    global _current_page
    matches = [record for record in _items_cache if _record_matches(record, _filter_text)]
    matches.sort(key=_sort_key, reverse=not _sort_ascending)
    _visible_items = matches
    total_pages = max(1, (len(_visible_items) + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)
    _current_page = min(max(1, _current_page), total_pages)


def _load_selected_properties():
    global _selected_properties
    item = _selected_item()
    if item is None:
        _selected_properties = []
        return
    try:
        Items.WaitForProps(item.Serial, PROPERTY_WAIT_MS)
    except:
        pass
    try:
        _selected_properties = [_clean_text(line) for line in Items.GetPropStringList(item.Serial)]
    except:
        _selected_properties = []


def _open_container(serial, push_history=True):
    global _container_serial
    global _container_stack
    global _selected_serial
    global _selected_properties
    global _current_page

    item = Items.FindBySerial(serial)
    if item is None or not bool(getattr(item, "IsContainer", False)):
        _set_status("The selected object is not an available container.", ERROR_HUE)
        return False

    try:
        Items.UseItem(serial)
        Items.WaitForContents(serial, CONTENTS_WAIT_MS)
    except Exception as error:
        _set_status("Open request failed: " + _clean_text(error), ERROR_HUE)
        return False

    if push_history:
        if not _container_stack or _container_stack[-1] != int(serial):
            _container_stack.append(int(serial))
    _container_serial = int(serial)
    _selected_serial = 0
    _selected_properties = []
    _current_page = 1
    return _refresh_items("Opened " + _container_name(serial))


def _refresh_items(success_message="Refreshed container contents."):
    global _items_cache
    global _selected_serial
    if _container_serial <= 0:
        _items_cache = []
        _rebuild_visible_items()
        _set_status("Choose a container first.", ERROR_HUE)
        return False

    container = Items.FindBySerial(_container_serial)
    if container is None:
        _items_cache = []
        _rebuild_visible_items()
        _set_status("The current container is no longer available.", ERROR_HUE)
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
        _set_status("Could not read contents: " + _clean_text(error), ERROR_HUE)
        return False

    _items_cache = records
    if _selected_serial and not any(record["serial"] == _selected_serial for record in records):
        _selected_serial = 0
    _rebuild_visible_items()
    _set_status("{0} ({1} direct item(s)).".format(success_message, len(records)), SUCCESS_HUE)
    return True


def _target_container():
    try:
        serial = int(Target.PromptTarget("Target a container to explore", MUTED_HUE) or 0)
    except:
        serial = 0
    if serial <= 0:
        _set_status("Container targeting cancelled.", MUTED_HUE)
        return
    _container_stack[:] = []
    _open_container(serial, True)


def _use_backpack():
    backpack = _player_backpack()
    if backpack is None:
        _set_status("Player backpack is unavailable.", ERROR_HUE)
        return
    _container_stack[:] = []
    _open_container(int(backpack.Serial), True)


def _go_back():
    global _container_serial
    if len(_container_stack) <= 1:
        _set_status("There is no earlier container in this explorer session.", MUTED_HUE)
        return
    _container_stack.pop()
    previous = _container_stack[-1]
    _container_serial = int(previous)
    _open_container(previous, False)


def _select_item(serial):
    global _selected_serial
    item = Items.FindBySerial(serial)
    if item is None:
        _set_status("That item is no longer available.", ERROR_HUE)
        _refresh_items()
        return
    _selected_serial = int(serial)
    _load_selected_properties()
    _set_status("Selected " + (_clean_text(item.Name) or _hex(serial)), VALUE_HUE)


def _show_selected():
    item = _selected_item()
    if item is None:
        _set_status("Select an item first.", ERROR_HUE)
        return
    Items.SingleClick(item.Serial)
    _set_status("Requested the selected item's name/property display.", SUCCESS_HUE)


def _open_selected():
    item = _selected_item()
    if item is None:
        _set_status("Select a container item first.", ERROR_HUE)
        return
    if not bool(getattr(item, "IsContainer", False)):
        _set_status("The selected item is not a container.", ERROR_HUE)
        return
    _open_container(int(item.Serial), True)


def _take_item(serial):
    global _selected_serial
    global _selected_properties

    item = Items.FindBySerial(serial)
    backpack = _player_backpack()
    if item is None:
        _refresh_items("Item was no longer available; refreshed the container")
        _set_status("That item is no longer available. Container refreshed.", ERROR_HUE)
        return False
    if backpack is None:
        _refresh_items("Backpack unavailable; refreshed container contents")
        _set_status(
            "Razor Enhanced did not expose the player backpack. Container refreshed.",
            ERROR_HUE
        )
        return False

    parent_serial = _item_parent_serial(item)
    if parent_serial == int(backpack.Serial):
        _refresh_items("Refreshed container contents")
        _set_status("The selected item is already in your backpack.", MUTED_HUE)
        return False

    item_name = _clean_text(item.Name) or _hex(serial)
    amount = max(1, int(getattr(item, "Amount", 0) or 0))
    source_serial = int(_container_serial)
    try:
        Items.Move(item.Serial, backpack.Serial, amount)
        moved = _wait_for_item_to_leave(item.Serial, source_serial)
    except Exception as error:
        _refresh_items("Move failed; refreshed container contents")
        _set_status("Move failed: " + _clean_text(error), ERROR_HUE)
        return False

    if moved:
        if _selected_serial == int(serial):
            _selected_serial = 0
            _selected_properties = []
        _refresh_items("Moved {0} to your backpack".format(item_name))
        return True

    _refresh_items("Move was not confirmed; refreshed container contents")
    _set_status(
        "Move was not confirmed for {0}. Container refreshed.".format(item_name),
        ERROR_HUE
    )
    return False


def _take_selected():
    if _selected_serial <= 0:
        _set_status("Select an item with its left arrow, or use its TAKE arrow.", ERROR_HUE)
        return False
    return _take_item(_selected_serial)


# ============================================================
# GUMP CONTENT
# ============================================================

def _details_html():
    lines = []
    item = _selected_item()
    if item is None:
        lines.append("<basefont color={0}>Container overview</basefont>".format(HTML_SECTION_COLOR))
        if _container_serial <= 0:
            lines.extend([
                "Choose TARGET to inspect a visible container.",
                "Choose BACKPACK to browse your main backpack.",
                "The left row arrow selects an item for details or OPEN.",
                "The right TAKE arrow moves that row and refreshes the container.",
            ])
        else:
            lines.extend([
                "<basefont color={0}>Name:</basefont> <basefont color={1}>{2}</basefont>".format(
                    HTML_LABEL_COLOR, HTML_VALUE_COLOR, _html_escape(_container_name(_container_serial))
                ),
                "Serial: {0} / {1}".format(_hex(_container_serial), _container_serial),
                "Direct contents: {0}; matching filter: {1}".format(
                    len(_items_cache), len(_visible_items)
                ),
                "History depth: {0}".format(len(_container_stack)),
                "<basefont color={0}>Workflow</basefont>".format(HTML_SECTION_COLOR),
                "Use a row's left arrow to inspect its complete property list here.",
                "Use its right arrow to take it immediately and refresh the source.",
                "OPEN enters a selected nested container. BACK returns one level.",
                "TAKE STACK moves only the selected stack to your backpack.",
            ])
        return _html_lines(lines)

    record = _item_record(item)
    lines.extend([
        "<basefont color={0}>Selected item</basefont>".format(HTML_SECTION_COLOR),
        "<basefont color={0}>Name:</basefont> <basefont color={1}>{2}</basefont>".format(
            HTML_LABEL_COLOR, HTML_VALUE_COLOR, _html_escape(record["name"])
        ),
        "Serial: {0} / {1}".format(_hex(record["serial"]), record["serial"]),
        "Item ID: {0} / {1}".format(_hex(record["item_id"], 4), record["item_id"]),
        "Hue: {0} / {1}".format(_hex(record["hue"], 4), record["hue"]),
        "Amount: {0}".format(record["amount"]),
        "Container={0}; grid={1}; position={2},{3}".format(
            record["is_container"], record["grid"], record["x"], record["y"]
        ),
        "<basefont color={0}>Object property list</basefont>".format(HTML_SECTION_COLOR),
    ])
    if _selected_properties:
        for index, line in enumerate(_selected_properties):
            lines.append("[{0}] {1}".format(index, _html_escape(line)))
    else:
        lines.append("No property lines were returned.")
    lines.append("<basefont color={0}>Note: row labels and this pane reflect Razor's current client cache.</basefont>".format(
        HTML_COMMENT_COLOR
    ))
    return _html_lines(lines)


def _add_button(gump, x, y, button_id, label, hue=TEXT_HUE):
    Gumps.AddButton(gump, x, y, 4005, 4007, button_id, 1, 0)
    Gumps.AddLabel(gump, x + 28, y, hue, label)


def _draw_gump():
    global _dirty
    global _row_select_targets
    _row_select_targets = {}
    Gumps.CloseGump(GUMP_ID)
    gump = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gump, 0)
    Gumps.AddBackground(gump, 0, 0, GUMP_WIDTH, GUMP_HEIGHT, BACKGROUND_ID)
    Gumps.AddAlphaRegion(gump, 0, 0, GUMP_WIDTH, GUMP_HEIGHT)

    Gumps.AddItem(gump, 7, 4, FROG_ICON, FROG_HUE)
    Gumps.AddLabel(gump, 48, 12, TITLE_HUE, "Frog Container Explorer")
    if _container_serial > 0:
        Gumps.AddLabel(gump, 255, 12, VALUE_HUE, _short(_container_name(_container_serial), 42))
    Gumps.AddButton(gump, GUMP_WIDTH - 28, 8, 4017, 4019, BTN_CLOSE, 1, 0)

    _add_button(gump, 16, 43, BTN_TARGET, "TARGET", SUCCESS_HUE)
    _add_button(gump, 122, 43, BTN_BACKPACK, "BACKPACK", TEXT_HUE)
    _add_button(gump, 254, 43, BTN_REFRESH, "REFRESH", TEXT_HUE)
    _add_button(gump, 370, 43, BTN_BACK, "BACK", MUTED_HUE)

    Gumps.AddLabel(gump, 16, 77, TEXT_HUE, "Find")
    Gumps.AddTextEntry(gump, 58, 75, 155, 22, TEXT_HUE, ENTRY_FILTER, _filter_text)
    _add_button(gump, 225, 75, BTN_FILTER, "APPLY", SUCCESS_HUE)
    _add_button(gump, 324, 75, BTN_CLEAR_FILTER, "CLEAR", MUTED_HUE)
    _add_button(gump, 422, 75, BTN_SORT, "SORT: " + _current_sort_mode().upper(), VALUE_HUE)
    _add_button(gump, 590, 75, BTN_DIRECTION, "ASC" if _sort_ascending else "DESC", TEXT_HUE)

    Gumps.AddAlphaRegion(gump, 12, 108, 424, 354)
    Gumps.AddLabel(gump, 18, 112, TITLE_HUE, "Item / select")
    Gumps.AddLabel(gump, 282, 112, TITLE_HUE, "Amount")
    Gumps.AddLabel(gump, 347, 112, TITLE_HUE, "ID")
    Gumps.AddLabel(gump, 398, 112, TITLE_HUE, "Take")

    start = (_current_page - 1) * ROWS_PER_PAGE
    page_items = _visible_items[start:start + ROWS_PER_PAGE]
    y = 138
    for row_index, record in enumerate(page_items):
        selected = record["serial"] == _selected_serial
        if selected:
            Gumps.AddImageTiled(gump, 16, y - 3, 412, 28, ROW_BACKGROUND_ID)
        Gumps.AddItem(gump, 18, y - 7, record["item_id"], record["hue"])
        select_button = ROW_SELECT_BUTTON_BASE + row_index
        _row_select_targets[select_button] = record["serial"]
        Gumps.AddButton(gump, 54, y, 4005, 4007, select_button, 1, 0)
        name_hue = SUCCESS_HUE if selected else VALUE_HUE
        marker = "+ " if record["is_container"] else ""
        Gumps.AddLabel(gump, 81, y, name_hue, marker + _short(record["name"], 27))
        Gumps.AddLabel(gump, 294, y, TEXT_HUE, str(record["amount"]))
        Gumps.AddLabel(gump, 347, y, MUTED_HUE, _hex(record["item_id"], 4))
        Gumps.AddButton(gump, 407, y, 4005, 4007, record["serial"], 1, 0)
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
    _add_button(gump, 548, 468, BTN_OPEN, "OPEN", VALUE_HUE)
    _add_button(gump, 642, 468, BTN_TAKE, "TAKE STACK", SUCCESS_HUE)

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
        _target_container()
    elif button_id == BTN_BACKPACK:
        _use_backpack()
    elif button_id == BTN_REFRESH:
        _refresh_items()
        _load_selected_properties()
    elif button_id == BTN_BACK:
        _go_back()
    elif button_id == BTN_FILTER:
        _filter_text = filter_value
        _current_page = 1
        _rebuild_visible_items()
        _set_status("Filter applied: " + (_filter_text or "all items"), SUCCESS_HUE)
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
    elif button_id == BTN_OPEN:
        _open_selected()
    elif button_id == BTN_TAKE:
        _take_selected()
    elif button_id in _row_select_targets:
        _select_item(_row_select_targets[button_id])
    elif button_id > 0:
        _take_item(button_id)
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
        Misc.SendMessage("[Frog Container Explorer] Stopped: " + _clean_text(error), ERROR_HUE)
    finally:
        Gumps.CloseGump(GUMP_ID)


Main()
