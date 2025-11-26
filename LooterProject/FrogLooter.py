# ====================================================================
# FrogLooter.py
# v0.7j — IronPython-safe, CUO-compatible, styled UI restored
# Author: UO Script Forge (for Frog)
# ====================================================================

import time
from System.IO import Path, Directory, File
import clr
clr.AddReference("System.Web.Extensions")
from System.Web.Script.Serialization import JavaScriptSerializer

# ====================================================================
# PATHS
# ====================================================================
BASE_PATH = r"D:\UO Informations\Frogge Scripts\LooterProject"
if not Directory.Exists(BASE_PATH):
    Directory.CreateDirectory(BASE_PATH)
CONFIG_FILE = Path.Combine(BASE_PATH, "FrogLooter_Config.json")

# ====================================================================
# CONFIGURATION
# ====================================================================
GUMP_ID       = 0xF11DF00
REFRESH_MS    = 300
SCAN_RANGE    = 6
MAX_LIST_ROWS = 25

_running            = True
_autoloot_enabled   = True
_ignore_enabled     = True
_loot_bag_serial    = 0
_last_items_refresh = 0.0
_items_cache        = []
_status_msg         = "Idle"
_show_items         = True

# ====================================================================
# BUTTON IDS
# ====================================================================
BTN_QUIT           = 9000
BTN_TOGGLE_AUTO    = 9001
BTN_TOGGLE_IGNORE  = 9002
BTN_SELECT_LOOTBAG = 9003
BTN_RELOAD_TABLES  = 9005
BTN_TOGGLE_ITEMS   = 9006
BTN_ADD_AUTO       = 9007
BTN_ADD_IGNORE     = 9008
BUTTON_PAGE        = 1

# ====================================================================
# VISUAL STYLE
# ====================================================================
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
PROP_COLOR       = 0x0026
VERSION_TAG      = "v0.7j"

ADD_AUTO_HUE     = 0x0590
ADD_IGNORE_HUE   = 0x0026

# ====================================================================
# CONFIG MANAGEMENT
# ====================================================================
_serializer = JavaScriptSerializer()
_config = {"AutoLoot": {}, "Ignore": {}}

_DEFAULT_CONFIG = {
    "AutoLoot": {
        "0x0EED": {"name": "Gold Coin", "props": []},
        "0x0F84": {"name": "Garlic", "props": []},
        "0x0F85": {"name": "Ginseng", "props": []},
        "0x0F86": {"name": "Mandrake Root", "props": []},
        "0x0F88": {"name": "Nightshade", "props": []},
        "0x0F8C": {"name": "Sulphurous Ash", "props": []},
        "0x0F8D": {"name": "Spider's Silk", "props": []},
        "0x0F7A": {"name": "Black Pearl", "props": []}
    },
    "Ignore": {
        "0x0E76": {"name": "Bag", "props": []},
        "0x0E77": {"name": "Pouch", "props": []}
    }
}

def log(msg, hue=68):
    try: Misc.SendMessage("[FrogLooter] " + str(msg), hue)
    except: pass

def _ensure_config_shape():
    global _config
    if not isinstance(_config, dict):
        _config = {"AutoLoot": {}, "Ignore": {}}
    if "AutoLoot" not in _config: _config["AutoLoot"] = {}
    if "Ignore" not in _config: _config["Ignore"] = {}

def create_default_config():
    global _config
    _config = _DEFAULT_CONFIG
    save_config()
    log("Created default FrogLooter_Config.json.", 68)

def save_config():
    try:
        text = _serializer.Serialize(_config)
        indent, pretty = 0, []
        for c in text:
            if c in ['{', '[']:
                pretty.append(c + '\n' + '    ' * (indent + 1))
                indent += 1
            elif c in ['}', ']']:
                indent -= 1
                pretty.append('\n' + '    ' * indent + c)
            elif c == ',':
                pretty.append(c + '\n' + '    ' * indent)
            else:
                pretty.append(c)
        File.WriteAllText(CONFIG_FILE, ''.join(pretty))
        log("Saved config → {}".format(CONFIG_FILE), 68)
    except Exception as e:
        log("Error saving config: {}".format(e), 33)

def load_config():
    global _config
    try:
        if not File.Exists(CONFIG_FILE):
            create_default_config()
        else:
            text = File.ReadAllText(CONFIG_FILE)
            _config = _serializer.DeserializeObject(text)
            _ensure_config_shape()
            log("Loaded config ({} AutoLoot, {} Ignore).".format(
                len(_config["AutoLoot"]), len(_config["Ignore"])), 68)
    except Exception as e:
        log("Error loading config: {}".format(e), 33)
        create_default_config()

# ====================================================================
# CONFIG UPDATERS
# ====================================================================
def add_item_to_config(section):
    global _status_msg
    try:
        target = Target.PromptTarget("Target item to add to {}".format(section))
        item = Items.FindBySerial(target)
        if not item:
            _status_msg = "No item found."; return
        iid = "0x{0:04X}".format(item.ItemID)
        name = item.Name or "Unknown"
        props = []
        try: props = list(Items.GetPropStringList(item))
        except: pass
        if iid in _config[section]:
            _status_msg = "Already in {}".format(section); return
        _config[section][iid] = {"name": name, "props": props}
        save_config()
        _status_msg = "Added {} ({}) to {}".format(name, iid, section)
    except Exception as e:
        log("Add failed: {}".format(e), 33)

# ====================================================================
# HELPERS
# ====================================================================
_MAGIC_PROPS = [
    "vanquishing", "power", "force", "might", "ruin",
    "fortified", "indestructible", "exceptional",
    "spell channeling", "blessed"
]

def to_hex(i): 
    try: return "0x{0:04X}".format(int(i))
    except: return str(i)

def has_desired_property(item):
    try:
        props = Items.GetPropString(item)
        if not props: return False
        return any(k in props.lower() for k in _MAGIC_PROPS)
    except: return False

def should_autoloot(item):
    if not _autoloot_enabled: return False
    return to_hex(item.ItemID) in _config["AutoLoot"]

def should_ignore(item):
    if not _ignore_enabled: return False
    return to_hex(item.ItemID) in _config["Ignore"]

def move_to_lootbag(item):
    global _status_msg
    if _loot_bag_serial <= 0:
        _status_msg = "⚠ No loot bag selected!"
        Misc.SendMessage("[FrogLooter] No loot bag selected.", 33)
        return False
    try:
        Items.Move(item.Serial, _loot_bag_serial, -1)
        Misc.Pause(250)
        return True
    except Exception as e:
        log("Move error: {}".format(e), 33)
        return False

def distance_ok(item):
    try: return Player.DistanceTo(item) <= SCAN_RANGE
    except: return False

# ====================================================================
# FIXED CONTAINER LOOTER (CUO SAFE)
# ====================================================================
def loot_visible_containers():
    """Scans nearby visible containers/corpses and loots matching items."""
    if not _autoloot_enabled or _loot_bag_serial <= 0:
        return
    try:
        f = Items.Filter()
        f.Enabled = True
        f.IsContainer = True
        f.RangeMax = SCAN_RANGE
        found = Items.ApplyFilter(f)
        for cont in found:
            if not cont or not cont.IsContainer or not cont.Visible:
                continue
            if cont.RootContainer in (Player.Serial, Player.Backpack.Serial):
                continue
            if not cont.Contains:
                continue
            for ci in list(cont.Contains):
                if not ci or not ci.Movable: continue
                if should_ignore(ci): continue
                if should_autoloot(ci) or has_desired_property(ci):
                    move_to_lootbag(ci)
                    Misc.Pause(150)
    except Exception as e:
        log("Loot container error: {}".format(e), 33)

# ====================================================================
# GROUND SCANNER
# ====================================================================
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
        if not it or not it.Visible or not it.Movable: continue
        if should_ignore(it): continue
        if _autoloot_enabled and _loot_bag_serial > 0 and should_autoloot(it):
            if move_to_lootbag(it): continue
        prop_match = has_desired_property(it)
        dist = Player.DistanceTo(it)
        newlist.append((it, dist, prop_match))
    newlist.sort(key=lambda d: d[1])
    _items_cache = newlist
    _last_items_refresh = now
    return newlist

# ====================================================================
# GUI (FULL BORDER RESTORED)
# ====================================================================
def item_display_name(it, dist):
    return "{} ({}) [{}]".format(it.Name or "?", to_hex(it.ItemID), dist)

def render_gui():
    Gumps.CloseGump(GUMP_ID)
    gd = Gumps.CreateGump(True)
    Gumps.AddPage(gd, 0)
    width = 360
    main_h = 130
    item_rows_h = (20 * len(_items_cache)) + 30 if _show_items else 0

    # === Main Panel ===
    Gumps.AddBackground(gd, 0, 0, width, main_h, STYLE_BG_GFX)
    Gumps.AddAlphaRegion(gd, 0, 0, width, main_h)
    for x in (0, main_h - 5):
        Gumps.AddImageTiled(gd, 0, x, width, 5, STYLE_BORDER_GFX)
    for x in (0, width - 5):
        Gumps.AddImageTiled(gd, x, 0, 5, main_h, STYLE_BORDER_GFX)

    # === Title ===
    Gumps.AddItem(gd, 8, 6, FROG_ICON, FROG_HUE)
    Gumps.AddLabel(gd, (width // 2) - 30, 10, TITLE_COLOR, "FrogLooter")

    # === Buttons ===
    Gumps.AddButton(gd, width - 65, 6, 4005, 4006, BTN_RELOAD_TABLES, BUTTON_PAGE, 0)
    Gumps.AddLabel(gd, width - 47, 8, 68, "↻")
    Gumps.AddButton(gd, width - 35, 6, 4017, 4018, BTN_QUIT, BUTTON_PAGE, 0)
    Gumps.AddLabel(gd, width - 17, 8, 33, "✖")

    # === Controls ===
    Gumps.AddLabel(gd, 10, 36, TEXT_COLOR,
        "Auto:{} Ignore:{} Src:JSON".format(
        "ON" if _autoloot_enabled else "OFF",
        "ON" if _ignore_enabled else "OFF"))
    Gumps.AddButton(gd, 10, 54, 9903, 9904, BTN_TOGGLE_AUTO, BUTTON_PAGE, 0)
    Gumps.AddLabel(gd, 30, 54, TEXT_COLOR, "[AutoLoot]")
    Gumps.AddButton(gd, 120, 54, 9903, 9904, BTN_TOGGLE_IGNORE, BUTTON_PAGE, 0)
    Gumps.AddLabel(gd, 140, 54, TEXT_COLOR, "[Ignore]")
    Gumps.AddButton(gd, 220, 54, 9903, 9904, BTN_SELECT_LOOTBAG, BUTTON_PAGE, 0)
    Gumps.AddLabel(gd, 240, 54, TEXT_COLOR, "[Loot Bag]")

    # === Bag + Status ===
    bag_txt = "Bag: {}".format(hex(_loot_bag_serial)) if _loot_bag_serial > 0 else "Bag: (none)"
    Gumps.AddLabel(gd, 10, 96, TEXT_COLOR, bag_txt)
    Gumps.AddLabel(gd, 10, 112, TEXT_COLOR, "Status: {}".format(_status_msg))

    # === Bottom Buttons + Version ===
    yb = main_h - 25
    Gumps.AddButton(gd, width - 90, yb, 9903, 9904, BTN_ADD_AUTO, BUTTON_PAGE, 0)
    Gumps.AddLabel(gd, width - 73, yb + 2, ADD_AUTO_HUE, "[+A]")
    Gumps.AddButton(gd, width - 60, yb, 9903, 9904, BTN_ADD_IGNORE, BUTTON_PAGE, 0)
    Gumps.AddLabel(gd, width - 43, yb + 2, ADD_IGNORE_HUE, "[+I]")
    Gumps.AddLabel(gd, width - 28, yb + 4, TEXT_COLOR, VERSION_TAG)

    # === Item List ===
    if _show_items:
        sy = main_h + 4
        Gumps.AddBackground(gd, 0, sy, width, item_rows_h, STYLE_BG_GFX)
        Gumps.AddAlphaRegion(gd, 0, sy, width, item_rows_h)
        for x in (0, sy + item_rows_h - 5):
            Gumps.AddImageTiled(gd, 0, x, width, 5, STYLE_BORDER_GFX)
        for x in (0, width - 5):
            Gumps.AddImageTiled(gd, x, sy, 5, item_rows_h, STYLE_BORDER_GFX)
        for y in (sy, sy + item_rows_h - 5):
            Gumps.AddImageTiled(gd, 0, y, 5, 5, STYLE_BORDER_GFX)
            Gumps.AddImageTiled(gd, width - 5, y, 5, 5, STYLE_BORDER_GFX)
        Gumps.AddLabel(gd, 10, sy + 8, TEXT_COLOR, "Nearby Items:")
        Gumps.AddItem(gd, width - 25, sy + 6, GEM_ICON, GEM_ON_HUE)
        y = sy + 28
        for it, dist, prop_match in _items_cache[:MAX_LIST_ROWS]:
            color = PROP_COLOR if prop_match else (LOOTABLE_COLOR if dist <= 1 else DISTANT_COLOR)
            Gumps.AddButton(gd, 10, y, 9903, 9904, int(it.Serial), BUTTON_PAGE, 0)
            Gumps.AddLabel(gd, 30, y, color, item_display_name(it, dist))
            y += 20

    Gumps.SendGump(GUMP_ID, Player.Serial, 30, 380, gd.gumpDefinition, gd.gumpStrings)

# ====================================================================
# BUTTON HANDLER
# ====================================================================
def handle_button(bid):
    global _running, _autoloot_enabled, _ignore_enabled, _loot_bag_serial, _status_msg
    if bid == BTN_QUIT: _running = False; return
    if bid == BTN_TOGGLE_AUTO: _autoloot_enabled = not _autoloot_enabled; _status_msg = "AutoLoot {}".format("ON" if _autoloot_enabled else "OFF"); return
    if bid == BTN_TOGGLE_IGNORE: _ignore_enabled = not _ignore_enabled; _status_msg = "Ignore {}".format("ON" if _ignore_enabled else "OFF"); return
    if bid == BTN_SELECT_LOOTBAG:
        s = Target.PromptTarget("Select Loot Bag")
        if s: _loot_bag_serial = s; _status_msg = "Bag set."; return
    if bid == BTN_RELOAD_TABLES: load_config(); _status_msg = "Config reloaded"; return
    if bid == BTN_ADD_AUTO: add_item_to_config("AutoLoot"); return
    if bid == BTN_ADD_IGNORE: add_item_to_config("Ignore"); return
    item = Items.FindBySerial(bid)
    if item:
        dist = Player.DistanceTo(item)
        if dist <= 1: ok = move_to_lootbag(item); _status_msg = "Moved {}".format(item.Name) if ok else "Move failed"
        else: _status_msg = "Too far to loot ({})".format(dist)

# ====================================================================
# MAIN LOOP
# ====================================================================
def main():
    log("Config path: {}".format(CONFIG_FILE), 68)
    load_config()
    render_gui()
    Misc.Pause(500)  # small startup delay for CUO to stabilize

    while _running and Player.Connected:
        try:
            # Auto reopen GUI if closed
            g = Gumps.GetGumpData(GUMP_ID)
            if not g or not g.gumpDefinition:
                render_gui()

            # Handle button clicks
            if g and g.buttonid and int(g.buttonid) > 0:
                handle_button(int(g.buttonid))
                Misc.Pause(120)

            # === LOOT OPERATIONS ===
            # Loot open/nearby containers
            loot_visible_containers()

            # Scan + auto-loot ground items that match config
            nearby = scan_ground_items()
            if nearby:
                for it, dist, prop_match in nearby:
                    # Auto-loot if configured and close enough
                    if (
                        _autoloot_enabled
                        and _loot_bag_serial > 0
                        and should_autoloot(it)
                        and dist <= 2
                    ):
                        move_to_lootbag(it)
                        Misc.Pause(150)

            # Refresh GUI and loop timing
            render_gui()
            Misc.Pause(REFRESH_MS)

        except Exception as e:
            log("Error: {}".format(e), 33)
            Misc.Pause(500)

    # Clean exit
    Gumps.CloseGump(GUMP_ID)
    log("FrogLooter stopped.", 33)


# ====================================================================
# SCRIPT ENTRYPOINT
# ====================================================================
main()

