# ==================================
# == Frog Quest Tracker           ==
# ==================================
# Original quest logic: Mags (Avron), V66
# Frogmancer suite refactor
#
# Razor Enhanced / ClassicUO
#

import re
import time

import Gumps, Journal, Misc, Player


# ====================================================================
# USER SETTINGS
# ====================================================================

GUMP_X = 100
GUMP_Y = 100


# ====================================================================
# CONFIGURATION
# ====================================================================

GUI_GUMP_ID   = 0xF2064651
QUEST_GUMP_ID = 0xDA2ACF13

QUEST_COMMAND       = "[quest"
QUEST_NEXT_BUTTON   = 2
QUEST_PAGE_COUNT    = 7
QUEST_MAX_PAGES     = 12
QUEST_STARTUP_DELAY_MS = 1000
QUEST_OPEN_TIMEOUT  = 3000
QUEST_PAGE_TIMEOUT  = 2200
QUEST_PAGE_SETTLE_MS = 450
QUEST_PAGE_POLL_MS  = 125

REFRESH_MS         = 250
BUTTON_DEBOUNCE_MS = 180

MAIN_WIDTH = 260
MAIN_EMPTY_HEIGHT = 180
MAIN_ACTIVE_HEIGHT = 236

OVERVIEW_WIDTH = 680
OVERVIEW_HEIGHT = 302
OVERVIEW_ROW_H = 23
OVERVIEW_PAGE_SIZE = 16
OVERVIEW_BAR_W = 250
OVERVIEW_BAR_H = 18

BG_ID          = 5054
SEPARATOR_ID   = 30071
BAR_BG_ID      = 40004
BAR_FILL_ID    = 9354
FROG_ICON      = 0x2130
FROG_HUE       = 1152
GEM_BUTTON_UP  = 10741
GEM_BUTTON_DOWN = 10740

TITLE_HUE = 1152
LABEL_HUE = 0x0481
INFO_HUE  = 0x0035
GOOD_HUE  = 68
WARN_HUE  = 53
BAD_HUE   = 33

COMPLETION_PREFIX = "Congratulations! You have completed the quest:"
PROGRESS_PREFIX   = "Quest Progress -"

TREASURE_GOAL = 5
TREASURE_CHEST_ART_ID = 48292
TREASURE_CHEST_COMPLETE_HUE = 1161
TREASURE_CHEST_INCOMPLETE_HUE = 1151
TREASURE_CHEST_SPACING = 44
TREASURE_TOKEN_MARKER = str(TREASURE_CHEST_ART_ID)


# ====================================================================
# BUTTON IDS
# ====================================================================

BTN_OVERVIEW = 1001
BTN_BACK     = 1002
BTN_REFRESH  = 1003
BTN_OVERVIEW_PREV = 1004
BTN_OVERVIEW_NEXT = 1005
BTN_CLOSE    = 1099

BTN_QUEST_BASE = 2000


# ====================================================================
# GLOBAL STATE
# ====================================================================

_running = True
_dirty_ui = True
_refresh_requested = True
_refreshing = False

_current_page = "main"
_overview_page = 0
_status_msg = "Starting..."
_last_refresh_label = "Never"
_render_stage = "startup"

_quests = []
_active_quest_name = ""
_treasure_count = 0

_overview_button_map = {}
_journal_cursor = None


# ====================================================================
# HELPERS
# ====================================================================

PROGRESS_RE = re.compile(r"(\d+)\s*/\s*(\d+)")
PROGRESS_VALUE_RE = re.compile(r"^(\d+)\s*/\s*(\d+)$")
PAGE_LABEL_RE = re.compile(r"^PAGE\s+(\d+)\s+OF\s+(\d+)$", re.I)
VIAL_RE = re.compile(r"(vial kit|empty vial|emtpy vial)", re.I)

QUEST_COLUMN_LABELS = ("Quest", "Region", "Type", "Difficulty", "Progress")
QUEST_REWARD_TEXT = "Complete quests to obtain an extra reward!"


def _clean_text(value):
    return " ".join(str(value or "").strip().split())


def _strip_field_prefix(value, prefix):
    text = _clean_text(value)
    marker = prefix.lower() + ":"
    if text.lower().startswith(marker):
        return text[len(marker):].strip()
    return text


def _html_escape(value):
    text = str(value or "")
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _highlight_task(value):
    escaped = _html_escape(value)

    def replace_vial(match):
        return "<B><BASEFONT COLOR=#FF8C00>{0}</BASEFONT></B>".format(match.group(0))

    return VIAL_RE.sub(replace_vial, escaped)


def _same_name(left, right):
    return _clean_text(left).lower() == _clean_text(right).lower()


def _find_quest(name):
    for quest in _quests:
        if _same_name(quest.get("name", ""), name):
            return quest
    return None


def _active_quest():
    quest = _find_quest(_active_quest_name)
    if quest:
        return quest
    if _quests:
        return _quests[0]
    return None


def _ensure_active_quest():
    global _active_quest_name

    quest = _active_quest()
    _active_quest_name = quest.get("name", "") if quest else ""


def _progress_values(value):
    match = PROGRESS_RE.search(str(value or ""))
    if not match:
        return 0, 0, 0.0

    current = int(match.group(1))
    maximum = int(match.group(2))
    if maximum <= 0:
        return current, maximum, 0.0

    fraction = max(0.0, min(1.0, float(current) / float(maximum)))
    return current, maximum, fraction


def _progress_hue(fraction):
    if fraction >= 1.0:
        return GOOD_HUE
    if fraction >= 0.66:
        return 68
    if fraction >= 0.33:
        return WARN_HUE
    return BAD_HUE


def _difficulty_hue(value):
    text = str(value or "").lower()
    if "easy" in text:
        return GOOD_HUE
    if "medium" in text:
        return WARN_HUE
    if "hard" in text:
        return BAD_HUE
    return LABEL_HUE


def _quest_tooltip(quest):
    current, maximum, fraction = _progress_values(quest.get("progress", ""))
    percent = int(round(fraction * 100.0))
    tooltip = (
        "<BASEFONT COLOR=#FFFF00>{0}</BASEFONT><BR />"
        "Progress: {1} ({2}%)<BR />"
        "Region: {3}<BR />"
        "Type: {4} | Difficulty: {5}<BR />"
        "Task: {6}"
    )
    return tooltip.format(_html_escape(quest.get("name", "Unknown Quest")), _html_escape(quest.get("progress", "0/0")), percent, _html_escape(_strip_field_prefix(quest.get("region", "Unknown"), "Region")), _html_escape(quest.get("type", "Unknown")), _html_escape(quest.get("diff", "Unknown")), _html_escape(quest.get("desc", "")))


def _draw_bar(gd, x, y, width, fraction, tooltip, height=14):
    fraction = max(0.0, min(1.0, float(fraction)))
    Gumps.AddImageTiled(gd, x, y, width, height, BAR_BG_ID)
    Gumps.AddTooltip(gd, tooltip)

    fill_width = int(width * fraction)
    if fill_width > 0:
        Gumps.AddImageTiled(gd, x, y, fill_width, height, BAR_FILL_ID)
        Gumps.AddTooltip(gd, tooltip)


def _capture_journal_cursor():
    try:
        entries = Journal.GetJournalEntry(0) or []
        if len(entries) > 0:
            return entries[len(entries) - 1]
    except:
        pass
    return None


# ====================================================================
# QUEST REFRESH
# ====================================================================

def _as_list(value):
    try:
        return list(value or [])
    except:
        return []


def _layout_commands(layout):
    commands = []
    for match in re.finditer(r"\{\s*([^{}]+?)\s*\}", str(layout or "")):
        command = match.group(1).strip()
        if command:
            commands.append(command)
    return commands


def _quest_page_marker(values):
    for value in values:
        match = PAGE_LABEL_RE.match(_clean_text(value))
        if match:
            current_page = int(match.group(1))
            total_pages = int(match.group(2))
            if current_page > 0 and total_pages >= current_page:
                return current_page, total_pages
    return None, None


def _quest_gump_snapshot():
    try:
        gump_data = Gumps.GetGumpData(QUEST_GUMP_ID)
    except:
        gump_data = None

    if not gump_data:
        return None

    try:
        captured_id = int(getattr(gump_data, "gumpId", QUEST_GUMP_ID))
        if captured_id != QUEST_GUMP_ID:
            return None
    except:
        pass

    layout = str(getattr(gump_data, "gumpLayout", "") or "")
    string_table = _as_list(getattr(gump_data, "stringList", None))
    data_members = _as_list(getattr(gump_data, "gumpData", None))

    try:
        is_current = int(Gumps.CurrentGump()) == QUEST_GUMP_ID
    except:
        is_current = False

    if is_current and not data_members:
        try:
            data_members = _as_list(Gumps.LastGumpGetLineList())
        except:
            pass

    if is_current and not layout:
        try:
            layout = str(Gumps.LastGumpRawData() or "")
        except:
            pass

    current_page, total_pages = _quest_page_marker(string_table + data_members)
    return {
        "layout": layout,
        "strings": string_table,
        "members": data_members,
        "page": current_page,
        "total": total_pages
    }


def _resolved_text_controls(snapshot):
    strings = snapshot.get("strings", [])
    controls = []

    for command in _layout_commands(snapshot.get("layout", "")):
        parts = command.split()
        if len(parts) < 5 or parts[0].lower() != "text":
            continue

        try:
            x = int(parts[1])
            y = int(parts[2])
            text_index = int(parts[4])
        except:
            continue

        if text_index < 0 or text_index >= len(strings):
            continue

        controls.append((x, y, _clean_text(strings[text_index])))

    return controls


def _parse_layout_quests(snapshot):
    controls = _resolved_text_controls(snapshot)
    if not controls:
        return []

    wanted_headers = dict((label.lower(), label) for label in QUEST_COLUMN_LABELS)
    header_columns = None
    header_y = None
    controls_by_y = {}

    for x, y, text in controls:
        controls_by_y.setdefault(y, {})[x] = text

    for y in sorted(controls_by_y.keys()):
        row = controls_by_y[y]
        found = {}
        for x, text in row.items():
            key = text.lower()
            if key in wanted_headers:
                found[wanted_headers[key]] = x
        if all(label in found for label in QUEST_COLUMN_LABELS):
            header_columns = found
            header_y = y
            break

    if header_columns is None:
        return []

    quests = []
    quest_x = header_columns["Quest"]

    for y in sorted(controls_by_y.keys()):
        if y <= header_y:
            continue

        row = controls_by_y[y]
        if not all(header_columns[label] in row for label in QUEST_COLUMN_LABELS):
            continue

        progress = row[header_columns["Progress"]]
        if not PROGRESS_VALUE_RE.match(progress):
            continue

        name = row[header_columns["Quest"]]
        region = row[header_columns["Region"]]
        quest_type = _strip_field_prefix(row[header_columns["Type"]], "Type")
        difficulty = _strip_field_prefix(row[header_columns["Difficulty"]], "Difficulty")

        if not name or not region or not quest_type or not difficulty:
            continue

        description = ""
        for desc_x, desc_y, desc_text in controls:
            if desc_x == quest_x and desc_y > y and desc_y <= y + 40:
                description = desc_text
                break

        quests.append({
            "name": name,
            "progress": progress,
            "region": region,
            "type": quest_type,
            "diff": difficulty,
            "desc": description
        })

    return quests


def _parse_member_quests(values):
    lines = [_clean_text(value) for value in values]
    header_end = -1
    header_lower = [label.lower() for label in QUEST_COLUMN_LABELS]

    for index in range(max(0, len(lines) - len(header_lower) + 1)):
        candidate = [value.lower() for value in lines[index:index + len(header_lower)]]
        if candidate == header_lower:
            header_end = index + len(header_lower)
            break

    if header_end < 0:
        return []

    stop_index = len(lines)
    for index in range(header_end, len(lines)):
        if lines[index].lower() == QUEST_REWARD_TEXT.lower() or PAGE_LABEL_RE.match(lines[index]):
            stop_index = index
            break

    quests = []
    for index in range(header_end, stop_index):
        progress = lines[index]
        if not PROGRESS_VALUE_RE.match(progress):
            continue

        name_index = index - 4
        description_index = index + 1
        if name_index < header_end or description_index >= stop_index:
            continue

        name = lines[name_index]
        region = lines[index - 3]
        quest_type = _strip_field_prefix(lines[index - 2], "Type")
        difficulty = _strip_field_prefix(lines[index - 1], "Difficulty")
        description = lines[description_index]

        if not name or name.isdigit() or not region or not quest_type or not difficulty:
            continue

        quests.append({
            "name": name,
            "progress": progress,
            "region": region,
            "type": quest_type,
            "diff": difficulty,
            "desc": description
        })

    return quests


def _parse_snapshot_quests(snapshot):
    quests = _parse_layout_quests(snapshot)
    if quests:
        return quests
    return _parse_member_quests(snapshot.get("members", []))


def _snapshot_has_quest_header(snapshot):
    values = snapshot.get("strings", []) + snapshot.get("members", [])
    lowered = set(_clean_text(value).lower() for value in values)
    return all(label.lower() in lowered for label in QUEST_COLUMN_LABELS)


def _snapshot_signature(snapshot):
    quests = _parse_snapshot_quests(snapshot)
    rows = tuple((_clean_text(quest.get("name", "")).lower(), quest.get("progress", "")) for quest in quests)
    return snapshot.get("page"), snapshot.get("total"), rows


def _wait_for_quest_snapshot(previous_snapshot=None):
    deadline = time.time() + (QUEST_PAGE_TIMEOUT / 1000.0)
    previous_signature = _snapshot_signature(previous_snapshot) if previous_snapshot else None

    while time.time() < deadline:
        snapshot = _quest_gump_snapshot()
        if snapshot:
            if previous_snapshot is None:
                return snapshot

            current_page = snapshot.get("page")
            previous_page = previous_snapshot.get("page")
            if current_page is not None and previous_page is not None and current_page != previous_page:
                return snapshot

            if (current_page is None or previous_page is None) and _snapshot_signature(snapshot) != previous_signature:
                return snapshot

        Misc.Pause(QUEST_PAGE_POLL_MS)

    return None


def _reward_token_count(snapshot):
    layout_commands = _layout_commands(snapshot.get("layout", ""))
    saw_reward_base = False
    overlay_count = 0

    for command in layout_commands:
        parts = command.split()
        if len(parts) < 4:
            continue

        command_name = parts[0].lower()
        try:
            art_id = int(parts[3])
        except:
            continue

        if command_name == "tilepichue" and art_id == TREASURE_CHEST_ART_ID:
            saw_reward_base = True
        elif command_name == "tilepic" and art_id == TREASURE_CHEST_ART_ID:
            overlay_count += 1

    if saw_reward_base:
        return max(0, min(TREASURE_GOAL, overlay_count))

    marker_count = 0
    for value in snapshot.get("members", []):
        if _clean_text(value) == TREASURE_TOKEN_MARKER:
            marker_count += 1
    return max(0, min(TREASURE_GOAL, marker_count))


def _merge_quest_rows(destination, page_quests):
    known = dict((_clean_text(quest.get("name", "")).lower(), quest) for quest in destination)
    for quest in page_quests:
        key = _clean_text(quest.get("name", "")).lower()
        if not key:
            continue
        if key in known:
            known[key].update(quest)
        else:
            destination.append(quest)
            known[key] = quest

def _commit_refreshed_quests(new_quests, reward_tokens):
    global _quests
    global _active_quest_name
    global _treasure_count
    global _last_refresh_label

    previous_active = _active_quest_name
    _quests = new_quests
    _treasure_count = reward_tokens

    if previous_active and _find_quest(previous_active):
        _active_quest_name = previous_active
    else:
        _active_quest_name = ""
        _ensure_active_quest()

    _last_refresh_label = time.strftime("%H:%M:%S")


def refresh_quests():
    global _refreshing
    global _status_msg
    global _dirty_ui

    _refreshing = True
    _status_msg = "Refreshing quest data..."

    # Preserve Mags' proven open-and-page workflow, but identify rows from the
    # captured quest layout instead of relying on incidental list offsets alone.
    try:
        Gumps.CloseGump(GUI_GUMP_ID)
        Gumps.CloseGump(QUEST_GUMP_ID)
        Player.HeadMessage(63, "Refreshing Quest Goals...")
        Player.ChatSay(QUEST_COMMAND)

        if not Gumps.WaitForGump(QUEST_GUMP_ID, QUEST_OPEN_TIMEOUT):
            Player.HeadMessage(BAD_HUE, "Error: Quest window never opened!")
            _status_msg = "Refresh failed: quest window did not open."
            return

        # The server replaces this gump on every page reply. Preserve the
        # original tracker cadence so several scripts do not hammer the
        # client's shared gump cache at the same time.
        Misc.Pause(QUEST_PAGE_SETTLE_MS)
        snapshot = _wait_for_quest_snapshot()
        if not snapshot or not _snapshot_has_quest_header(snapshot):
            raise RuntimeError("quest gump data was incomplete")
        if snapshot.get("page") is not None and snapshot.get("page") != 1:
            raise RuntimeError("quest gump did not open on page 1")

        new_data = []
        reward_tokens = _reward_token_count(snapshot)
        visited_pages = set()
        pages_scanned = 0

        while snapshot:
            current_page = snapshot.get("page")
            total_pages = snapshot.get("total")

            if total_pages is not None and total_pages > QUEST_MAX_PAGES:
                raise RuntimeError("quest gump reported too many pages")

            signature = _snapshot_signature(snapshot)
            if signature in visited_pages:
                raise RuntimeError("quest page did not advance")
            visited_pages.add(signature)

            _merge_quest_rows(new_data, _parse_snapshot_quests(snapshot))
            pages_scanned += 1

            if current_page is not None and total_pages is not None:
                if current_page >= total_pages:
                    break
            elif pages_scanned >= QUEST_PAGE_COUNT:
                break

            if pages_scanned >= QUEST_MAX_PAGES:
                raise RuntimeError("quest page safety limit reached")

            previous_snapshot = snapshot
            Gumps.SendAction(QUEST_GUMP_ID, QUEST_NEXT_BUTTON)
            Misc.Pause(QUEST_PAGE_SETTLE_MS)
            snapshot = _wait_for_quest_snapshot(previous_snapshot)
            if not snapshot:
                raise RuntimeError("timed out waiting for the next quest page")
            if not _snapshot_has_quest_header(snapshot):
                raise RuntimeError("next quest page was incomplete")
            if previous_snapshot.get("page") is not None and snapshot.get("page") is not None:
                if snapshot.get("page") != previous_snapshot.get("page") + 1:
                    raise RuntimeError("quest pages advanced out of sequence")

        _commit_refreshed_quests(new_data, reward_tokens)
        _status_msg = "Refreshed {0} quest{1} across {2} page{3}.".format(len(new_data), "" if len(new_data) == 1 else "s", pages_scanned, "" if pages_scanned == 1 else "s")
        Player.HeadMessage(63, "Goals Refreshed. Treasure Progress: {0}/{1}".format(_treasure_count, TREASURE_GOAL))

    except Exception as error:
        _status_msg = "Refresh failed; kept previous data: {0}".format(str(error))
        Player.HeadMessage(BAD_HUE, "Quest refresh failed; previous data kept.")
    finally:
        Gumps.CloseGump(QUEST_GUMP_ID)
        _refreshing = False
        _dirty_ui = True


# ====================================================================
# JOURNAL TRACKING
# ====================================================================

def _remove_completed_quest(name):
    global _quests
    global _active_quest_name

    remaining = []
    removed = False

    for quest in _quests:
        if _same_name(quest.get("name", ""), name):
            removed = True
        else:
            remaining.append(quest)

    if not removed:
        return False

    _quests = remaining
    if _same_name(_active_quest_name, name):
        _active_quest_name = ""
        _ensure_active_quest()
    return True


def _apply_progress(name, progress):
    global _active_quest_name

    quest = _find_quest(name)
    if not quest:
        return False

    changed = quest.get("progress", "") != progress
    active_changed = not _same_name(_active_quest_name, quest.get("name", ""))

    quest["progress"] = progress
    _active_quest_name = quest.get("name", "")
    return changed or active_changed


def process_journal():
    global _journal_cursor
    global _treasure_count
    global _status_msg
    global _dirty_ui
    global _refresh_requested

    try:
        if _journal_cursor is None:
            entries = Journal.GetJournalEntry(0) or []
        else:
            entries = Journal.GetJournalEntry(_journal_cursor) or []
    except:
        entries = []

    if not entries:
        return

    for entry in entries:
        _journal_cursor = entry
        text = str(getattr(entry, "Text", "") or "").strip()

        if COMPLETION_PREFIX in text:
            quest_name = text.split(COMPLETION_PREFIX, 1)[1].strip()

            if _remove_completed_quest(quest_name):
                _treasure_count += 1
                if _treasure_count >= TREASURE_GOAL:
                    _treasure_count = 0
                    Player.HeadMessage(GOOD_HUE, "YAY YOU COMPLETED 5 DAILY QUESTS")

                _status_msg = "Completed: {0}".format(quest_name)
                _dirty_ui = True
            else:
                _status_msg = "Completion seen; refresh recommended."
                _dirty_ui = True

            continue

        if PROGRESS_PREFIX in text:
            content = text.split(PROGRESS_PREFIX, 1)[1].strip()
            if ":" not in content:
                continue

            quest_name, progress = content.rsplit(":", 1)
            quest_name = quest_name.strip()
            progress = progress.strip()

            if _apply_progress(quest_name, progress):
                _status_msg = "Tracking: {0}".format(quest_name)
                _dirty_ui = True
            elif not _find_quest(quest_name):
                _status_msg = "New quest detected; refreshing..."
                _refresh_requested = True
                _dirty_ui = True


# ====================================================================
# GUMP / GUI FUNCTIONS
# ====================================================================

def _add_header(gd, width, title, page_button, page_label):
    Gumps.AddItem(gd, 5, 5, FROG_ICON, FROG_HUE)
    Gumps.AddLabel(gd, 40, 8, TITLE_HUE, title)

    if page_button:
        Gumps.AddButton(gd, width - 108, 7, 4029, 4030, page_button, 1, 0)
        Gumps.AddLabel(gd, width - 85, 9, LABEL_HUE, page_label)

    Gumps.AddButton(gd, width - 45, 7, 4017, 4018, BTN_CLOSE, 1, 0)
    Gumps.AddImageTiled(gd, 10, 33, width - 20, 2, SEPARATOR_ID)


def _add_footer(gd, width, height, compact=False):
    Gumps.AddImageTiled(gd, 10, height - 39, width - 20, 2, SEPARATOR_ID)
    Gumps.AddButton(gd, 12, height - 29, 4005, 4007, BTN_REFRESH, 1, 0)
    Gumps.AddLabel(gd, 36, height - 27, GOOD_HUE, "Refresh")

    if compact:
        Gumps.AddTooltip(gd, _status_msg)
        Gumps.AddLabel(gd, 96, height - 27, LABEL_HUE, "{0} quests".format(len(_quests)))
        Gumps.AddLabel(gd, width - 64, height - 27, INFO_HUE, _last_refresh_label)
        return

    status = _status_msg
    max_status_chars = max(12, int((width - 215) / 7))
    if len(status) > max_status_chars:
        status = status[:max_status_chars - 3] + "..."
    Gumps.AddLabel(gd, 92, height - 27, LABEL_HUE, status)

    Gumps.AddLabel(gd, width - 105, height - 27, INFO_HUE, _last_refresh_label)


def _render_main_page(gd):
    global _render_stage

    quest = _active_quest()
    height = MAIN_ACTIVE_HEIGHT if quest else MAIN_EMPTY_HEIGHT

    _render_stage = "main background"
    Gumps.AddBackground(gd, 0, 0, MAIN_WIDTH, height, BG_ID)
    Gumps.AddAlphaRegion(gd, 0, 0, MAIN_WIDTH, height)
    _add_header(gd, MAIN_WIDTH, "Frog Quests", BTN_OVERVIEW, "All")

    _render_stage = "main quest"

    if not quest:
        Gumps.AddLabel(gd, 18, 45, GOOD_HUE, "All daily goals complete!")
        Gumps.AddLabel(gd, 18, 65, LABEL_HUE, "Refresh after accepting a quest.")
        chest_label_y = 86
        chest_y = 102
    else:
        current, maximum, fraction = _progress_values(quest.get("progress", ""))
        percent = int(round(fraction * 100.0))
        tooltip = _quest_tooltip(quest)

        name = quest.get("name", "Unknown Quest")
        if len(name) > 22:
            name = name[:19] + "..."

        Gumps.AddLabel(gd, 14, 43, TITLE_HUE, "Current Quest")
        Gumps.AddLabel(gd, 210, 43, _progress_hue(fraction), "{0}%".format(percent))

        _draw_bar(gd, 15, 63, 230, fraction, tooltip, 18)
        Gumps.AddLabel(gd, 20, 62, LABEL_HUE, name)
        Gumps.AddTooltip(gd, tooltip)
        Gumps.AddLabel(gd, 202, 62, INFO_HUE, quest.get("progress", "0/0"))
        Gumps.AddTooltip(gd, tooltip)

        region = _strip_field_prefix(quest.get("region", "Unknown"), "Region")
        metadata = "{0} | {1} | {2}".format(region, quest.get("type", "Unknown"), quest.get("diff", "Unknown"))
        Gumps.AddLabel(gd, 15, 85, INFO_HUE, metadata[:38])
        Gumps.AddTooltip(gd, tooltip)

        task_html = "<BASEFONT COLOR=#7FFFFF>{0}</BASEFONT>".format(_highlight_task(quest.get("desc", "")))
        Gumps.AddHtml(gd, 15, 104, 230, 34, task_html, False, False)
        chest_label_y = 143
        chest_y = 159

    _render_stage = "main treasure"
    treasure_tooltip = "Daily reward progress: {0}/{1}".format(_treasure_count, TREASURE_GOAL)
    Gumps.AddLabel(gd, 12, chest_label_y, GOOD_HUE, "Complete quests to obtain an extra reward!")

    chest_row_width = TREASURE_GOAL * TREASURE_CHEST_SPACING
    chest_start_x = (MAIN_WIDTH - chest_row_width) // 2

    for chest_index in range(TREASURE_GOAL):
        chest_hue = TREASURE_CHEST_COMPLETE_HUE if chest_index < _treasure_count else TREASURE_CHEST_INCOMPLETE_HUE
        Gumps.AddItem(gd, chest_start_x + (chest_index * TREASURE_CHEST_SPACING), chest_y, TREASURE_CHEST_ART_ID, chest_hue)
        Gumps.AddTooltip(gd, treasure_tooltip)

    _render_stage = "main footer"
    _add_footer(gd, MAIN_WIDTH, height, True)


def _overview_quests():
    active = _active_quest()
    if not active:
        quests = list(_quests)
    else:
        quests = [quest for quest in _quests if not _same_name(quest.get("name", ""), active.get("name", ""))]

    return sorted(quests, key=lambda quest: (-_progress_values(quest.get("progress", ""))[2], _clean_text(quest.get("name", "")).lower()))


def _overview_page_count(quest_count):
    return max(1, (quest_count + OVERVIEW_PAGE_SIZE - 1) // OVERVIEW_PAGE_SIZE)


def _render_overview_page(gd):
    global _overview_button_map
    global _overview_page
    global _render_stage

    quests = _overview_quests()
    page_count = _overview_page_count(len(quests))
    _overview_page = max(0, min(_overview_page, page_count - 1))
    start_index = _overview_page * OVERVIEW_PAGE_SIZE
    page_quests = quests[start_index:start_index + OVERVIEW_PAGE_SIZE]
    _overview_button_map = {}

    _render_stage = "overview background"
    Gumps.AddBackground(gd, 0, 0, OVERVIEW_WIDTH, OVERVIEW_HEIGHT, BG_ID)
    Gumps.AddAlphaRegion(gd, 0, 0, OVERVIEW_WIDTH, OVERVIEW_HEIGHT)
    _add_header(gd, OVERVIEW_WIDTH, "Frog Quest Progress", BTN_BACK, "Back")

    Gumps.AddLabel(gd, 14, 43, TITLE_HUE, "Other Quests ({0}) - Highest First".format(len(quests)))

    if _overview_page > 0:
        Gumps.AddButton(gd, 520, 42, 4014, 4015, BTN_OVERVIEW_PREV, 1, 0)
        Gumps.AddTooltip(gd, "Previous quest page")

    Gumps.AddLabel(gd, 546, 43, LABEL_HUE, "Page {0}/{1}".format(_overview_page + 1, page_count))

    if _overview_page < page_count - 1:
        Gumps.AddButton(gd, 638, 42, 4005, 4007, BTN_OVERVIEW_NEXT, 1, 0)
        Gumps.AddTooltip(gd, "Next quest page")

    if not quests:
        Gumps.AddLabel(gd, 22, 72, GOOD_HUE, "No other active quests.")

    _render_stage = "overview rows"
    for index, quest in enumerate(page_quests):
        column = index % 2
        row = index // 2
        x = 14 + (column * 333)
        y = 68 + (row * OVERVIEW_ROW_H)

        button_id = BTN_QUEST_BASE + index
        _overview_button_map[button_id] = quest.get("name", "")

        current, maximum, fraction = _progress_values(quest.get("progress", ""))
        percent = int(round(fraction * 100.0))
        tooltip = _quest_tooltip(quest)

        name = quest.get("name", "Unknown Quest")
        if len(name) > 22:
            name = name[:19] + "..."

        Gumps.AddButton(gd, x, y + 2, GEM_BUTTON_UP, GEM_BUTTON_DOWN, button_id, 1, 0)
        Gumps.AddTooltip(gd, "Show this quest on the landing page.")

        bar_x = x + 18
        _draw_bar(gd, bar_x, y, OVERVIEW_BAR_W, fraction, tooltip, OVERVIEW_BAR_H)
        Gumps.AddLabel(gd, bar_x + 5, y - 1, LABEL_HUE, name)
        Gumps.AddTooltip(gd, tooltip)
        Gumps.AddLabel(gd, bar_x + 190, y - 1, INFO_HUE, quest.get("progress", "0/0"))
        Gumps.AddTooltip(gd, tooltip)
        Gumps.AddLabel(gd, bar_x + OVERVIEW_BAR_W + 6, y - 1, _progress_hue(fraction), "{0}%".format(percent))

    _render_stage = "overview footer"
    _add_footer(gd, OVERVIEW_WIDTH, OVERVIEW_HEIGHT)


def render_gui():
    global _dirty_ui
    global _render_stage

    _render_stage = "create gump"
    Gumps.CloseGump(GUI_GUMP_ID)
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)

    if _current_page == "overview":
        _render_overview_page(gd)
    else:
        _render_main_page(gd)

    _render_stage = "send gump"
    Gumps.SendGump(GUI_GUMP_ID, Player.Serial, GUMP_X, GUMP_Y, gd.gumpDefinition, gd.gumpStrings)
    _dirty_ui = False


def _render_fallback(error):
    Gumps.CloseGump(GUI_GUMP_ID)
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)
    Gumps.AddBackground(gd, 0, 0, 390, 112, BG_ID)
    Gumps.AddAlphaRegion(gd, 0, 0, 390, 112)
    Gumps.AddLabel(gd, 12, 10, BAD_HUE, "Frog Quest Tracker render error")
    Gumps.AddLabel(gd, 12, 36, LABEL_HUE, "Stage: {0}".format(_render_stage)[:48])
    Gumps.AddLabel(gd, 12, 58, BAD_HUE, str(error)[:52])
    Gumps.AddButton(gd, 12, 84, 4005, 4007, BTN_REFRESH, 1, 0)
    Gumps.AddLabel(gd, 36, 86, GOOD_HUE, "Retry")
    Gumps.AddButton(gd, 365, 8, 4017, 4018, BTN_CLOSE, 1, 0)
    Gumps.SendGump(GUI_GUMP_ID, Player.Serial, GUMP_X, GUMP_Y, gd.gumpDefinition, gd.gumpStrings)


def render_gui_safe():
    global _dirty_ui
    global _status_msg

    try:
        render_gui()
    except Exception as error:
        _status_msg = "Render error at {0}".format(_render_stage)
        _dirty_ui = False
        _render_fallback(error)


# ====================================================================
# BUTTON HANDLING
# ====================================================================

def handle_button(button_id):
    global _running
    global _current_page
    global _overview_page
    global _active_quest_name
    global _refresh_requested
    global _status_msg
    global _dirty_ui

    if button_id == BTN_CLOSE:
        _running = False
        return

    if button_id == BTN_OVERVIEW:
        _current_page = "overview"
        _overview_page = 0
        _dirty_ui = True
        return

    if button_id == BTN_BACK:
        _current_page = "main"
        _dirty_ui = True
        return

    if button_id == BTN_OVERVIEW_PREV:
        if _overview_page > 0:
            _overview_page -= 1
            _dirty_ui = True
        return

    if button_id == BTN_OVERVIEW_NEXT:
        page_count = _overview_page_count(len(_overview_quests()))
        if _overview_page < page_count - 1:
            _overview_page += 1
            _dirty_ui = True
        return

    if button_id == BTN_REFRESH:
        if not _refreshing:
            _refresh_requested = True
            _status_msg = "Refresh requested..."
            _dirty_ui = True
        return

    if button_id in _overview_button_map:
        quest_name = _overview_button_map[button_id]
        if _find_quest(quest_name):
            _active_quest_name = quest_name
            _current_page = "main"
            _status_msg = "Focused: {0}".format(quest_name)
            _dirty_ui = True


# ====================================================================
# MAIN
# ====================================================================

def Main():
    global _journal_cursor
    global _refresh_requested
    global _dirty_ui

    _journal_cursor = _capture_journal_cursor()
    Gumps.CloseGump(GUI_GUMP_ID)

    # FroggeSuite can launch several gump-owning cores together. Let their
    # initial custom gumps settle before opening and paging the server tracker.
    Misc.Pause(QUEST_STARTUP_DELAY_MS)

    while _running and Player.Connected:
        handled_button = False
        gump_data = Gumps.GetGumpData(GUI_GUMP_ID)
        button_id = int(getattr(gump_data, "buttonid", 0)) if gump_data else 0

        if button_id > 0:
            try:
                gump_data.buttonid = 0
            except:
                pass

            Gumps.CloseGump(GUI_GUMP_ID)
            handle_button(button_id)
            handled_button = True
            Misc.Pause(BUTTON_DEBOUNCE_MS)

        if not _running:
            break

        if handled_button:
            Misc.Pause(REFRESH_MS)
            continue

        process_journal()
        did_refresh = False

        if _refresh_requested and not _refreshing:
            _refresh_requested = False
            refresh_quests()
            did_refresh = True

        # Reuse the top-of-loop snapshot during idle cycles. GetGumpData uses
        # Razor's shared gump cache, so avoiding a second read every cycle
        # matters when the combat and loot cores are polling it too.
        visible_gump = gump_data
        if did_refresh or _dirty_ui or visible_gump is None:
            visible_gump = Gumps.GetGumpData(GUI_GUMP_ID)

        pending_button = int(getattr(visible_gump, "buttonid", 0)) if visible_gump else 0

        # A click may arrive while a server-gump refresh is running. Leave this
        # custom gump untouched so the next iteration can consume the reply.
        if pending_button > 0:
            Misc.Pause(REFRESH_MS)
            continue

        if visible_gump is None:
            _dirty_ui = True

        if _dirty_ui:
            render_gui_safe()

        Misc.Pause(REFRESH_MS)

    Gumps.CloseGump(QUEST_GUMP_ID)
    Gumps.CloseGump(GUI_GUMP_ID)
    Misc.SendMessage("Frog Quest Tracker stopped.", WARN_HUE)


Main()
