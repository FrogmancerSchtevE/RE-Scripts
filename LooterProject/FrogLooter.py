# FrogLooter.py
# v0.5 — JSON config, Add-to-AutoLoot/Ignore buttons
# Author: UO Script Forge (for Frog)

import time
from System.IO import File, Path, StreamReader, StreamWriter
import clr
clr.AddReference("System.Web.Extensions")
from System.Web.Script.Serialization import JavaScriptSerializer


# ====================================================================
# CONFIGURATION
# ====================================================================
GUMP_ID       = 0xF11DF00
REFRESH_MS    = 300
SCAN_RANGE    = 6
MAX_LIST_ROWS = 25

_running            = True
_use_external_files = True
_autoloot_enabled   = True
_ignore_enabled     = True
_loot_bag_serial    = 0
_last_items_refresh = 0.0
_items_cache        = []
_status_msg         = "Idle"
_show_items         = True

# Button IDs
BTN_QUIT           = 9000
BTN_TOGGLE_AUTO    = 9001
BTN_TOGGLE_IGNORE  = 9002
BTN_SELECT_LOOTBAG = 9003
BTN_TOGGLE_SOURCE  = 9004
BTN_RELOAD_TABLES  = 9005
BTN_TOGGLE_ITEMS   = 9006
BTN_ADD_AUTO       = 9007
BTN_ADD_IGNORE     = 9008

BUTTON_PAGE = 1

# === VISUAL STYLE ===
FROG_ICON        = 0x2130
FROG_HUE         = 0x09E8
GEM_ICON         = 0x0F19
GEM_ON_HUE       = 0x084A
GEM_OFF_HUE      = 0x0386
STYLE_BG_GFX     = 30546
STYLE_BORDER_GFX = 2620
TITLE_COLOR      = 0x35
TEXT_COLOR       = 0x0481
LOOTABLE_COLOR   = 0x0450
DISTANT_COLOR    = 0x03E9
VERSION_TAG      = "v0.5"

ADD_AUTO_HUE     = 0x0590  # green
ADD_IGNORE_HUE   = 0x0026  # red

# Paths
try:
    SCRIPT_DIR = Path.GetDirectoryName(Scripts.CurrentScriptPath)
except:
    SCRIPT_DIR = "."
CONFIG_FILE = Path.Combine(SCRIPT_DIR, "FrogLooter_Config.json")

# ====================================================================
# CONFIG MANAGEMENT (JSON)
# ====================================================================
_config = {"AutoLoot": {}, "Ignore": {}}
_serializer = JavaScriptSerializer()

def log(msg, hue=68):
    try: Misc.SendMessage("[FrogLooter] " + str(msg), hue)
    except: pass

def save_config():
    try:
        text = _serializer.Serialize(_config)
        w = StreamWriter(CONFIG_FILE, False)
        w.Write(text)
        w.Close()
        log("Config saved.")
    except Exception as e:
        log("Error saving config: {}".format(e), 33)

def load_config():
    global _config
    if not File.Exists(CONFIG_FILE):
        log("No config found. Creating new FrogLooter_Config.json.")
        save_config()
        return
    try:
        reader = StreamReader(CONFIG_FILE)
        content = reader.ReadToEnd()
        reader.Close()
        data = _serializer.DeserializeObject(content)
        if isinstance(data, dict):
            _config = data
            log("Config loaded ({} auto, {} ignore).".format(len(_config["AutoLoot"]), len(_config["Ignore"])))
    except Exception as e:
        log("Error reading config: {} — resetting.".format(e), 33)
        _config = {"AutoLoot": {}, "Ignore": {}}
        save_config()

# ====================================================================
# HELPERS
# ====================================================================
def to_hex(i):
    try: return "0x{0:04X}".format(int(i))
    except: return str(i)

def item_display_name(it, dist):
    return "{} ({}) [{}]".format(it.Name or "?", to_hex(it.ItemID), dist)

def move_to_lootbag(item):
    global _status_msg
    if _loot_bag_serial <= 0:
        _status_msg = "No loot bag selected"
        return False
    try:
        Items.Move(item.Serial, _loot_bag_serial, -1)
        Misc.Pause(250)
        return True
    except:
        return False

def distance_ok(item):
    try: return Player.DistanceTo(item) <= SCAN_RANGE
    except: return False

def should_autoloot(item):
    if not _autoloot_enabled: return False
    return to_hex(item.ItemID) in _config["AutoLoot"]

def should_ignore(item):
    if not _ignore_enabled: return False
    return to_hex(item.ItemID) in _config["Ignore"]

def is_visible_lootable(item):
    if not item or not item.IsLootable or not item.Movable or not item.Visible:
        return False
    if item.IsInBank: return False
    if item.RootContainer in (Player.Serial, Player.Backpack.Serial):
        return False
    if item.OnGround and not distance_ok(item):
        return False
    return True

def scan_ground_items(throttle_ms=900):
    global _last_items_refresh, _items_cache
    now = time.time() * 1000.0
    if (now - _last_items_refresh) < throttle_ms:
        return _items_cache
    f = Items.Filter()
    f.Enabled = True
    f.RangeMax = SCAN_RANGE
    found = Items.ApplyFilter(f) or []
    newlist = []
    for it in found:
        if not is_visible_lootable(it): continue
        if should_ignore(it): continue
        if should_autoloot(it) and _loot_bag_serial > 0:
            if move_to_lootbag(it): continue
        dist = Player.DistanceTo(it)
        newlist.append((it, dist))
    newlist.sort(key=lambda d: d[1])
    _items_cache = newlist
    _last_items_refresh = now
    return newlist

# ====================================================================
# CONFIG UPDATE HANDLERS
# ====================================================================
def add_item_to_config(section):
    global _status_msg
    try:
        target = Target.PromptTarget("Target item to add to {}".format(section))
        item = Items.FindBySerial(target)
        if not item:
            _status_msg = "No item found."
            return
        iid = to_hex(item.ItemID)
        name = item.Name or "Unknown"
        props = []
        try: props = list(Items.GetPropStringList(item))
        except: pass
        if iid in _config[section]:
            _status_msg = "Already in {}".format(section)
            return
        _config[section][iid] = {"name": name, "props": props}
        save_config()
        _status_msg = "Added {} ({}) to {}".format(name, iid, section)
    except Exception as e:
        log("Add to config failed: {}".format(e), 33)

# ====================================================================
# GUMP UI
# ====================================================================
def render_gui():
    Gumps.CloseGump(GUMP_ID)
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)
    width = 360
    main_h = 130
    item_rows_h = (20 * len(_items_cache)) + 30 if _show_items else 0

    # === Main Panel ===
    Gumps.AddBackground(gd, 0, 0, width, main_h, STYLE_BG_GFX)
    Gumps.AddAlphaRegion(gd, 0, 0, width, main_h)
    Gumps.AddImageTiled(gd, 0, 0, width, 5, STYLE_BORDER_GFX)
    Gumps.AddImageTiled(gd, 0, main_h - 5, width, 5, STYLE_BORDER_GFX)
    Gumps.AddImageTiled(gd, 0, 0, 5, main_h, STYLE_BORDER_GFX)
    Gumps.AddImageTiled(gd, width - 5, 0, 5, main_h, STYLE_BORDER_GFX)

    Gumps.AddItem(gd, 8, 6, FROG_ICON, FROG_HUE)
    Gumps.AddLabel(gd, (width // 2) - 30, 10, TITLE_COLOR, "FrogLooter")

    # Add buttons beside version
    Gumps.AddButton(gd, width - 90, 6, 9903, 9904, BTN_ADD_AUTO, BUTTON_PAGE, 0)
    Gumps.AddLabel(gd, width - 73, 8, ADD_AUTO_HUE, "[+A]")
    Gumps.AddButton(gd, width - 60, 6, 9903, 9904, BTN_ADD_IGNORE, BUTTON_PAGE, 0)
    Gumps.AddLabel(gd, width - 43, 8, ADD_IGNORE_HUE, "[+I]")
    Gumps.AddLabel(gd, width - 28, 10, TEXT_COLOR, VERSION_TAG)

    # Reload / Quit
    Gumps.AddButton(gd, width - 65, main_h - 25, 4005, 4006, BTN_RELOAD_TABLES, BUTTON_PAGE, 0)
    Gumps.AddLabel(gd, width - 47, main_h - 24, 68, "↻")
    Gumps.AddButton(gd, width - 35, main_h - 25, 4017, 4018, BTN_QUIT, BUTTON_PAGE, 0)
    Gumps.AddLabel(gd, width - 17, main_h - 24, 33, "✖")

    src = "JSON"
    mode = "Auto:{} Ignore:{} Src:{}".format(
        "ON" if _autoloot_enabled else "OFF",
        "ON" if _ignore_enabled else "OFF",
        src)
    Gumps.AddLabel(gd, 10, 36, TEXT_COLOR, mode)

    # Controls
    Gumps.AddButton(gd, 10, 54, 9903, 9904, BTN_TOGGLE_AUTO, BUTTON_PAGE, 0)
    Gumps.AddLabel(gd, 30, 54, TEXT_COLOR, "[AutoLoot]")
    Gumps.AddButton(gd, 120, 54, 9903, 9904, BTN_TOGGLE_IGNORE, BUTTON_PAGE, 0)
    Gumps.AddLabel(gd, 140, 54, TEXT_COLOR, "[Ignore]")
    Gumps.AddButton(gd, 220, 54, 9903, 9904, BTN_SELECT_LOOTBAG, BUTTON_PAGE, 0)
    Gumps.AddLabel(gd, 240, 54, TEXT_COLOR, "[Loot Bag]")

    bag_txt = "Bag: {}".format(hex(_loot_bag_serial)) if _loot_bag_serial > 0 else "Bag: (none)"
    Gumps.AddLabel(gd, 10, 96, TEXT_COLOR, bag_txt)
    Gumps.AddLabel(gd, 10, 112, TEXT_COLOR, "Status: {}".format(_status_msg))

    # === Items Panel ===
    if _show_items:
        start_y = main_h + 4
        Gumps.AddBackground(gd, 0, start_y, width, item_rows_h, STYLE_BG_GFX)
        Gumps.AddAlphaRegion(gd, 0, start_y, width, item_rows_h)
        Gumps.AddImageTiled(gd, 0, start_y, width, 5, STYLE_BORDER_GFX)
        Gumps.AddImageTiled(gd, 0, start_y + item_rows_h - 5, width, 5, STYLE_BORDER_GFX)
        Gumps.AddImageTiled(gd, 0, start_y, 5, item_rows_h, STYLE_BORDER_GFX)
        Gumps.AddImageTiled(gd, width - 5, start_y, 5, item_rows_h, STYLE_BORDER_GFX)

        Gumps.AddLabel(gd, 10, start_y + 8, TEXT_COLOR, "Nearby Items:")
        Gumps.AddButton(gd, width - 26, start_y + 4, 9903, 9904, BTN_TOGGLE_ITEMS, BUTTON_PAGE, 0)
        Gumps.AddItem(gd, width - 25, start_y + 6, GEM_ICON, GEM_ON_HUE if _show_items else GEM_OFF_HUE)
        y = start_y + 28
        for it, dist in _items_cache:
            color = LOOTABLE_COLOR if dist <= 1 else DISTANT_COLOR
            Gumps.AddButton(gd, 10, y, 9903, 9904, int(it.Serial), BUTTON_PAGE, 0)
            Gumps.AddLabel(gd, 30, y, color, item_display_name(it, dist))
            y += 20

    Gumps.SendGump(GUMP_ID, Player.Serial, 30, 380, gd.gumpDefinition, gd.gumpStrings)

# ====================================================================
# BUTTON HANDLER + MAIN LOOP
# ====================================================================
CONTROL_IDS = {
    BTN_QUIT, BTN_TOGGLE_AUTO, BTN_TOGGLE_IGNORE, BTN_SELECT_LOOTBAG,
    BTN_TOGGLE_SOURCE, BTN_RELOAD_TABLES, BTN_TOGGLE_ITEMS,
    BTN_ADD_AUTO, BTN_ADD_IGNORE
}

def handle_button(bid):
    global _running, _autoloot_enabled, _ignore_enabled, _loot_bag_serial, _status_msg, _show_items
    if bid == BTN_QUIT: _running = False; return
    if bid == BTN_TOGGLE_AUTO: _autoloot_enabled = not _autoloot_enabled; _status_msg = "AutoLoot {}".format("ON" if _autoloot_enabled else "OFF"); return
    if bid == BTN_TOGGLE_IGNORE: _ignore_enabled = not _ignore_enabled; _status_msg = "Ignore {}".format("ON" if _ignore_enabled else "OFF"); return
    if bid == BTN_SELECT_LOOTBAG:
        log("Target your loot bag.")
        s = Target.PromptTarget("Select Loot Bag")
        if s: _loot_bag_serial = s; _status_msg = "Bag set."; return
    if bid == BTN_RELOAD_TABLES: load_config(); _status_msg = "Config reloaded"; return
    if bid == BTN_TOGGLE_ITEMS: _show_items = not _show_items; _status_msg = "Items {}".format("Visible" if _show_items else "Hidden"); return
    if bid == BTN_ADD_AUTO: add_item_to_config("AutoLoot"); return
    if bid == BTN_ADD_IGNORE: add_item_to_config("Ignore"); return

    item = Items.FindBySerial(bid)
    if item:
        dist = Player.DistanceTo(item)
        if dist <= 1:
            ok = move_to_lootbag(item)
            _status_msg = "Moved {}".format(item.Name) if ok else "Move failed"
        else:
            _status_msg = "Too far to loot ({})".format(dist)

def main():
    load_config()
    while _running and Player.Connected:
        g = Gumps.GetGumpData(GUMP_ID)
        if g and g.buttonid and int(g.buttonid) > 0:
            handle_button(int(g.buttonid))
            Misc.Pause(120)
        scan_ground_items()
        render_gui()
        Misc.Pause(REFRESH_MS)
    Gumps.CloseGump(GUMP_ID)

main()
