# Originally Made by MeesaJarJar - http://github.com/MeesaJarJar/  -------#
# -------------------------------------------------------------#
# Edited by Frogmancer Schteve -
# If you encounter a bug or compatibility issue, please submit an
# issue through the repository or contact Frogmancer Schteve directly
# rather than submitting the script to an AI service for troubleshooting.
#
# SHARD RULES
# You are responsible for ensuring your use of this script complies
# with the rules of the Ultima Online shard on which you play.
#
# Use it. Learn from it. Improve it.
# Just don't feed the frogs to the robots.
# ====================================================================



gumpX = 1325
gumpY = 720

# True: unlock the HUD. Drag it, then click its small lock gem.
# Set this back to False after placement for future normal runs.
placementMode = False

# True: load saved item choices instead of targeting every run.
saveItemSelection = True

# One-run reset switches. Set back to False after running once.
resetSavedItems = False
resetSavedPosition = False

refreshDelay = 350
# END USER SETTINGS -------------------------------------------#

import json
import math
import os
from System import AppDomain

GUMP_ID = 0xF2064348
CIRCLE_RADIUS = 100
CIRCLE_CENTER_X = 0
CIRCLE_CENTER_Y = -40
ITEM_ANGLE_START = 45
ITEM_ANGLE_END = 180
GUMP_POSITION_OFFSET = 50
SETTINGS_FILE_NAME = "CircleHudFork.settings.json"
BUTTON_LOCK_POSITION = 9101
# Proven clickable red/green gem pair used by released RE gumps.
LOCK_GEM_NORMAL = 4029
LOCK_GEM_PRESSED = 4030
# Keep the button at positive local coordinates so it is inside the
# clickable bounds of this mostly negative-coordinate circle layout.
LOCK_GEM_X = 15
LOCK_GEM_Y = 10
POSITION_POLL_MS = 50

_settings_database = None
_player_profile = None
_gump_x = gumpX - GUMP_POSITION_OFFSET
_gump_y = gumpY - GUMP_POSITION_OFFSET
_classicuo_gumps_property = None
_classicuo_gump_type_property = None
_classicuo_server_serial_property = None
_classicuo_location_property = None
_position_reader_warning_sent = False
_position_reader_status = "not initialized"
_observed_position_available = False


def settings_file_path():
    data_directory = os.path.join(Misc.CurrentScriptDirectory(), "data")
    if not os.path.isdir(data_directory):
        os.makedirs(data_directory)
    return os.path.join(data_directory, SETTINGS_FILE_NAME)


def load_settings_database():
    path = settings_file_path()
    if not os.path.exists(path):
        return {"profiles": {}}

    try:
        with open(path, "r") as settings_file:
            database = json.load(settings_file)
        if isinstance(database, dict) and isinstance(database.get("profiles"), dict):
            return database
    except Exception as error:
        Misc.SendMessage("[Circle HUD] Could not load saved settings: " + str(error), 33)

    return {"profiles": {}}


def save_settings_database():
    if _settings_database is None:
        return False

    try:
        with open(settings_file_path(), "w") as settings_file:
            json.dump(_settings_database, settings_file, indent=2, sort_keys=True)
        return True
    except Exception as error:
        Misc.SendMessage("[Circle HUD] Could not save settings: " + str(error), 33)
        return False


def initialize_settings():
    global _settings_database, _player_profile, _gump_x, _gump_y

    _settings_database = load_settings_database()
    profiles = _settings_database["profiles"]
    player_key = "%08X" % int(Player.Serial)
    profile = profiles.get(player_key)
    if not isinstance(profile, dict):
        profile = {}
        profiles[player_key] = profile
    _player_profile = profile

    settings_changed = False
    if resetSavedItems and "items" in profile:
        profile.pop("items", None)
        settings_changed = True
        Misc.SendMessage("[Circle HUD] Saved item choices reset.", 53)

    if resetSavedPosition:
        if "gump_x" in profile or "gump_y" in profile:
            profile.pop("gump_x", None)
            profile.pop("gump_y", None)
            settings_changed = True
        Misc.SendMessage("[Circle HUD] Saved position reset to the script defaults.", 53)

    if not resetSavedPosition and "gump_x" in profile and "gump_y" in profile:
        try:
            _gump_x = int(profile["gump_x"])
            _gump_y = int(profile["gump_y"])
        except Exception:
            profile.pop("gump_x", None)
            profile.pop("gump_y", None)
            settings_changed = True

    if settings_changed:
        save_settings_database()


def load_saved_items():
    if not saveItemSelection or resetSavedItems or "items" not in _player_profile:
        return None

    raw_items = _player_profile.get("items")
    if not isinstance(raw_items, list):
        return None

    tracked_items = []
    tracked_keys = set()
    for raw_item in raw_items:
        try:
            if len(raw_item) != 2:
                continue
            item_key = (int(raw_item[0]), int(raw_item[1]))
            if item_key[0] <= 0 or item_key in tracked_keys:
                continue
            tracked_keys.add(item_key)
            tracked_items.append(item_key)
        except Exception:
            continue

    if raw_items and not tracked_items:
        Misc.SendMessage("[Circle HUD] Saved item choices were invalid; select them again.", 33)
        return None

    return tracked_items


def save_tracked_items(tracked_items):
    if not saveItemSelection:
        return

    _player_profile["items"] = [[item_id, item_hue] for item_id, item_hue in tracked_items]
    if save_settings_database():
        Misc.SendMessage("[Circle HUD] Item choices saved.", 68)


def initialize_position_reader():
    global _classicuo_gumps_property
    global _classicuo_gump_type_property
    global _classicuo_server_serial_property
    global _classicuo_location_property
    global _position_reader_status

    if (_classicuo_gumps_property is not None and
            _classicuo_gump_type_property is not None and
            _classicuo_server_serial_property is not None and
            _classicuo_location_property is not None):
        return True

    try:
        for assembly in AppDomain.CurrentDomain.GetAssemblies():
            classicuo_client_type = assembly.GetType("Assistant.ClassicUOClient")
            if classicuo_client_type is None:
                continue

            cuo_assembly_property = classicuo_client_type.GetProperty("CUOAssembly")
            if cuo_assembly_property is None:
                continue

            classicuo_assembly = cuo_assembly_property.GetValue(None, None)
            if classicuo_assembly is None:
                continue

            ui_manager_type = classicuo_assembly.GetType("ClassicUO.Game.Managers.UIManager")
            gump_type = classicuo_assembly.GetType("ClassicUO.Game.UI.Gumps.Gump")
            if ui_manager_type is None or gump_type is None:
                continue

            _classicuo_gumps_property = ui_manager_type.GetProperty("Gumps")
            _classicuo_gump_type_property = gump_type.GetProperty("GumpType")
            _classicuo_server_serial_property = gump_type.GetProperty("ServerSerial")
            _classicuo_location_property = gump_type.GetProperty("Location")
            break

        if (_classicuo_gumps_property is not None and
                _classicuo_gump_type_property is not None and
                _classicuo_server_serial_property is not None and
                _classicuo_location_property is not None):
            _position_reader_status = "ready"
            return True
    except Exception as error:
        _position_reader_status = "ClassicUO bridge error: " + str(error)
        _classicuo_gumps_property = None
        _classicuo_gump_type_property = None
        _classicuo_server_serial_property = None
        _classicuo_location_property = None
        return False

    _position_reader_status = "Razor Enhanced could not provide its active ClassicUO assembly."
    return False


def current_gump_position():
    global _position_reader_warning_sent, _position_reader_status

    if not initialize_position_reader():
        if placementMode and not _position_reader_warning_sent:
            Misc.SendMessage("[Circle HUD] " + _position_reader_status, 33)
            _position_reader_warning_sent = True
        return None

    try:
        open_gumps = _classicuo_gumps_property.GetValue(None, None)
        for gump in open_gumps:
            try:
                gump_type = int(_classicuo_gump_type_property.GetValue(gump, None))
                server_serial = int(_classicuo_server_serial_property.GetValue(gump, None))
                if gump_type != 0 or server_serial != GUMP_ID:
                    continue
                location = _classicuo_location_property.GetValue(gump, None)
                _position_reader_status = "ready"
                return int(location.X), int(location.Y)
            except Exception:
                continue

        _position_reader_status = "Circle HUD was not found in ClassicUO's open gump list."
    except Exception as error:
        _position_reader_status = "Could not read the ClassicUO gump list: " + str(error)
        if placementMode and not _position_reader_warning_sent:
            Misc.SendMessage("[Circle HUD] " + _position_reader_status, 33)
            _position_reader_warning_sent = True

    return None


def observe_moved_position():
    global _gump_x, _gump_y, _observed_position_available

    position = current_gump_position()
    if position is None:
        return False

    _gump_x, _gump_y = position
    _observed_position_available = True
    return True


def save_observed_position():
    global _position_reader_status

    # A reply button may close the client gump before its event is read.
    # Prefer the live location, but retain the last pre-click observation.
    observe_moved_position()
    if not _observed_position_available:
        return False

    _player_profile["gump_x"] = _gump_x
    _player_profile["gump_y"] = _gump_y
    if save_settings_database():
        return True

    _position_reader_status = "Position was read, but the settings file could not be written."
    return False


def read_gump_button():
    gump_data = Gumps.GetGumpData(GUMP_ID)
    if gump_data is None:
        return 0
    try:
        button_id = int(gump_data.buttonid)
        gump_data.buttonid = 0
        return button_id
    except Exception:
        return 0


def handle_gump_button(button_id):
    global placementMode

    if button_id != BUTTON_LOCK_POSITION:
        return False

    saved = save_observed_position()
    Gumps.CloseGump(GUMP_ID)
    if saved:
        placementMode = False
        Misc.SendMessage("[Circle HUD] Position saved and HUD locked.", 68)
    else:
        Misc.SendMessage("[Circle HUD] Position unavailable: " + _position_reader_status, 33)
    return True


def run_placement_mode(items_to_track):
    # Leave one gump instance open while the player drags and clicks it.
    # Redrawing here can replace the gump before RE exposes its button reply.
    updateGump(items_to_track)
    while placementMode and Player.Connected:
        observe_moved_position()
        if handle_gump_button(read_gump_button()):
            Misc.Pause(200)
            if placementMode:
                updateGump(items_to_track)
            continue
        Misc.Pause(POSITION_POLL_MS)

def draw_circle(radius):
    points = set()
    x = radius
    y = 0
    err = 0

    while x >= y:
        points.add((x, y))
        points.add((y, x))
        points.add((-y, x))
        points.add((-x, y))
        points.add((-x, -y))
        points.add((-y, -x))
        points.add((y, -x))
        points.add((x, -y))

        if err <= 0:
            y += 1
            err += 2*y + 1
        if err > 0:
            x -= 1
            err -= 2*x + 1

    return points
    
def calculate_hue(player_hits, player_hits_max):
    hue_green = 371
    hue_red = 331

    if player_hits_max is None or player_hits_max <= 0:
        return hue_red

    safe_hits = max(0, min(player_hits, player_hits_max))
    percentage_missing = float(player_hits_max - safe_hits) / float(player_hits_max)
    return int(hue_green + (hue_red - hue_green) * percentage_missing)


def calculate_item_angles(item_count):
    if item_count <= 0:
        return []
    if item_count == 1:
        return [(ITEM_ANGLE_START + ITEM_ANGLE_END) / 2.0]

    angle_step = float(ITEM_ANGLE_END - ITEM_ANGLE_START) / float(item_count - 1)
    return [ITEM_ANGLE_START + index * angle_step for index in range(item_count)]


def select_items_to_track():
    tracked_items = []
    tracked_keys = set()

    while Player.Connected:
        prompt = "Select items for the Circle HUD. Press ESC when finished."
        Player.HeadMessage(1150, prompt)
        serial = Target.PromptTarget(prompt, 1150)

        if serial is None or int(serial) < 0:
            break

        item = Items.FindBySerial(serial)
        if item is None:
            Player.HeadMessage(33, "That was not an item. Select an item or press ESC.")
            continue

        item_key = (int(item.ItemID), int(item.Hue))
        if item_key in tracked_keys:
            Player.HeadMessage(53, "That item type and hue is already tracked.")
            continue

        tracked_keys.add(item_key)
        tracked_items.append(item_key)
        Player.HeadMessage(68, "Added item 0x%04X, hue 0x%04X." % item_key)

    return tracked_items


circlePoints = []
for ringRadius in range(75, 80):
    circlePoints.extend(draw_circle(ringRadius))


def updateGump(items_to_track):
    gd = Gumps.CreateGump(placementMode, True, True, False)
    Gumps.AddPage(gd, 0)
    health_hue = calculate_hue(Player.Hits, Player.HitsMax)

    for point in circlePoints:
        Gumps.AddImage(gd, int(point[0] + CIRCLE_CENTER_X), int(point[1] + CIRCLE_CENTER_Y), 6001, health_hue)

    item_angles = calculate_item_angles(len(items_to_track))
    for index, trackable in enumerate(items_to_track):
        item_id, item_hue = trackable
        angle_rad = math.radians(item_angles[index])
        item_x = CIRCLE_CENTER_X + CIRCLE_RADIUS * math.cos(angle_rad)
        item_y = CIRCLE_CENTER_Y + CIRCLE_RADIUS * math.sin(angle_rad)
        item_count = Items.BackpackCount(item_id, item_hue) or 0

        Gumps.AddLabel(gd, int(item_x), int(item_y), 1152, str(item_count))
        Gumps.AddImage(gd, int(item_x), int(item_y - 20), 11400 if item_count > 5 else 11410)
        Gumps.AddItem(gd, int(item_x - 10), int(item_y - 38), item_id, item_hue)

    if placementMode:
        Gumps.AddButton(gd, LOCK_GEM_X, LOCK_GEM_Y, LOCK_GEM_NORMAL, LOCK_GEM_PRESSED, BUTTON_LOCK_POSITION, 1, 0)
        Gumps.AddTooltip(gd, "Save and lock Circle HUD position")

    Gumps.SendGump(GUMP_ID, Player.Serial, _gump_x, _gump_y, gd.gumpDefinition, gd.gumpStrings)
    if not placementMode:
        CUO.MoveGump(GUMP_ID, _gump_x, _gump_y)


def update_target_health_bar(previous_serial):
    target_serial = Target.GetLastAttack()
    if target_serial is None or int(target_serial) <= 0:
        if previous_serial:
            CUO.CloseMobileHealthBar(previous_serial)
        return 0

    target_serial = int(target_serial)
    mobile = Mobiles.FindBySerial(target_serial)
    if mobile is None or mobile.Deleted:
        if previous_serial:
            CUO.CloseMobileHealthBar(previous_serial)
        return 0

    if previous_serial and previous_serial != target_serial:
        CUO.CloseMobileHealthBar(previous_serial)

    health_bar_x = _gump_x + GUMP_POSITION_OFFSET
    health_bar_y = _gump_y + GUMP_POSITION_OFFSET + 150
    CUO.OpenMobileHealthBar(target_serial, health_bar_x, health_bar_y, False)
    return target_serial


initialize_settings()
itemTypesToTrack = load_saved_items()
if itemTypesToTrack is None:
    itemTypesToTrack = select_items_to_track()
    save_tracked_items(itemTypesToTrack)
else:
    Misc.SendMessage("[Circle HUD] Loaded %d saved item selection(s)." % len(itemTypesToTrack), 68)

if placementMode:
    Misc.SendMessage("[Circle HUD] PLACEMENT MODE: drag the ring, then click the small red gem inside it to save and lock.", 53)
else:
    Misc.SendMessage("[Circle HUD] Position locked for play.", 68)

lastHealthBarSerial = 0
try:
    if placementMode:
        run_placement_mode(itemTypesToTrack)

    if Player.Connected:
        updateGump(itemTypesToTrack)
        Misc.Pause(200)

    while Player.Connected:
        try:
            lastHealthBarSerial = update_target_health_bar(lastHealthBarSerial)
            Misc.Pause(refreshDelay)
            updateGump(itemTypesToTrack)
        except Exception as error:
            Misc.SendMessage("[Circle HUD] Error: " + str(error), 33)
            Misc.Pause(1000)
finally:
    Gumps.CloseGump(GUMP_ID)
    if lastHealthBarSerial:
        CUO.CloseMobileHealthBar(lastHealthBarSerial)
