# ==================================
# ==      Frog Player Catcher     ==
# ==================================
# Author: Frogmancer Schteve

import Gumps, Items, Misc, Mobiles, Player, Target


# ===========================================================
# USER SETTINGS
# ===========================================================

BOX_ITEM_IDS = (0x0E7D, 0x09AA)
BOX_HUE = -1
DROP_DELAY_MS = 650
MAX_DROP_RANGE = 2
ABORT_IF_TARGET_MOVES = True


# ===========================================================
# CONFIGURATION
# ===========================================================

GUMP_ID = 0xF2064258
GUMP_X = 560
GUMP_Y = 380
REFRESH_MS = 100
BUTTON_DEBOUNCE_MS = 180

CARDINAL_OFFSETS = (
    ("North", 0, -1),
    ("South", 0, 1),
    ("East", 1, 0),
    ("West", -1, 0),
)

HUE_ERROR = 33
HUE_WARNING = 53
HUE_SUCCESS = 68
HUE_TEXT = 0x480


# ===========================================================
# GLOBAL STATE
# ===========================================================

_running = True
_dirty_ui = True
_status_msg = "Ready."
_status_hue = HUE_TEXT


# ===========================================================
# BUTTON IDS
# ===========================================================

BTN_DROP_TILE = 1001
BTN_CAGE_TARGET = 1002
BTN_CLOSE = 1099


# ===========================================================
# HELPERS
# ===========================================================

def set_status(message, hue=HUE_TEXT):
    global _status_msg
    global _status_hue
    global _dirty_ui

    _status_msg = message
    _status_hue = hue
    _dirty_ui = True
    Misc.SendMessage("Player Catcher: " + message, hue)


def get_backpack():
    backpack = Player.Backpack

    if not backpack:
        set_status("Backpack was not found.", HUE_ERROR)
        return None

    return backpack


def count_boxes():
    backpack = Player.Backpack

    if not backpack:
        return 0

    total = 0

    for item_id in BOX_ITEM_IDS:
        total += Items.ContainerCount(backpack.Serial, item_id, BOX_HUE, True)

    return total


def find_box():
    backpack = get_backpack()

    if not backpack:
        return None

    for item_id in BOX_ITEM_IDS:
        box = Items.FindByID(item_id, BOX_HUE, backpack.Serial, True, False)

        if box:
            return box

    return None


def tile_distance_from_player(x, y):
    return max(abs(int(Player.Position.X) - int(x)), abs(int(Player.Position.Y) - int(y)))


def point_was_cancelled(point):
    if not point:
        return True

    return int(point.X) <= 0 and int(point.Y) <= 0


def target_stayed_at(mobile_serial, x, y, z):
    mobile = Mobiles.FindBySerial(mobile_serial)

    if not mobile:
        return False

    return (
        int(mobile.Position.X) == int(x)
        and int(mobile.Position.Y) == int(y)
        and int(mobile.Position.Z) == int(z)
    )


def box_drop_confirmed(box_serial, x, y):
    box = Items.FindBySerial(box_serial)

    if not box or not box.OnGround:
        return False

    return int(box.Position.X) == int(x) and int(box.Position.Y) == int(y)


def drop_box_at(x, y, z):
    if tile_distance_from_player(x, y) > MAX_DROP_RANGE:
        set_status("Destination is out of drop range.", HUE_WARNING)
        return False

    box = find_box()

    if not box:
        set_status("No wooden catcher box in backpack.", HUE_ERROR)
        return False

    box_serial = box.Serial

    try:
        Items.MoveOnGround(box_serial, 0, int(x), int(y), int(z))
    except Exception as error:
        set_status("Drop call failed: " + str(error), HUE_ERROR)
        return False

    Misc.Pause(DROP_DELAY_MS)

    if not box_drop_confirmed(box_serial, x, y):
        set_status("Server did not confirm the box drop.", HUE_WARNING)
        return False

    return True


# ===========================================================
# DROP ACTIONS
# ===========================================================

def drop_at_targeted_tile():
    if count_boxes() < 1:
        set_status("No wooden catcher box in backpack.", HUE_ERROR)
        return

    set_status("Target the tile for one box.")
    point = Target.PromptGroundTarget("Target the tile for one wooden box")

    if point_was_cancelled(point):
        set_status("Tile target cancelled.", HUE_WARNING)
        return

    if drop_box_at(point.X, point.Y, point.Z):
        set_status("Box dropped at targeted tile.", HUE_SUCCESS)


def cage_target():
    box_total = count_boxes()

    if box_total < 4:
        set_status("Need 4 boxes; backpack has {0}.".format(box_total), HUE_ERROR)
        return

    set_status("Target the player to cage.")
    mobile_serial = Target.PromptTarget("Target the player to cage with four boxes")

    if mobile_serial <= 0:
        set_status("Player target cancelled.", HUE_WARNING)
        return

    if mobile_serial == Player.Serial:
        set_status("Refusing to cage yourself.", HUE_WARNING)
        return

    mobile = Mobiles.FindBySerial(mobile_serial)

    if not mobile:
        set_status("Target must be a visible player/mobile.", HUE_ERROR)
        return

    center_x = int(mobile.Position.X)
    center_y = int(mobile.Position.Y)
    center_z = int(mobile.Position.Z)
    destinations = []

    for direction, offset_x, offset_y in CARDINAL_OFFSETS:
        x = center_x + offset_x
        y = center_y + offset_y

        if tile_distance_from_player(x, y) > MAX_DROP_RANGE:
            set_status("Move closer; all four tiles must be in range.", HUE_WARNING)
            return

        destinations.append((direction, x, y, center_z))

    dropped = 0

    for direction, x, y, z in destinations:
        if ABORT_IF_TARGET_MOVES and not target_stayed_at(mobile_serial, center_x, center_y, center_z):
            set_status("Target moved; stopped after {0}/4 boxes.".format(dropped), HUE_WARNING)
            return

        set_status("Dropping {0} box ({1}/4)...".format(direction, dropped + 1))

        if not drop_box_at(x, y, z):
            set_status("Cage stopped after {0}/4 confirmed boxes.".format(dropped), HUE_WARNING)
            return

        dropped += 1

    set_status("Cardinal cage complete: 4/4 boxes.", HUE_SUCCESS)


# ===========================================================
# GUI
# ===========================================================

def render_gui():
    global _dirty_ui

    Gumps.CloseGump(GUMP_ID)

    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)
    Gumps.AddBackground(gd, 0, 0, 300, 155, 5054)
    Gumps.AddAlphaRegion(gd, 8, 8, 284, 139)

    Gumps.AddLabel(gd, 15, 12, HUE_SUCCESS, "Frog Player Catcher")
    Gumps.AddLabel(gd, 205, 12, HUE_TEXT, "Boxes: {0}".format(count_boxes()))

    Gumps.AddButton(gd, 15, 42, 4005, 4007, BTN_DROP_TILE, 1, 0)
    Gumps.AddLabel(gd, 50, 44, HUE_TEXT, "Drop 1 at targeted tile")

    Gumps.AddButton(gd, 15, 72, 4005, 4007, BTN_CAGE_TARGET, 1, 0)
    Gumps.AddLabel(gd, 50, 74, HUE_TEXT, "Cage target: N / S / E / W")

    Gumps.AddLabel(gd, 15, 105, _status_hue, "Status: " + _status_msg)

    Gumps.AddButton(gd, 246, 122, 4017, 4019, BTN_CLOSE, 1, 0)
    Gumps.AddLabel(gd, 215, 124, HUE_TEXT, "Close")

    Gumps.SendGump(GUMP_ID, Player.Serial, GUMP_X, GUMP_Y, gd.gumpDefinition, gd.gumpStrings)
    _dirty_ui = False


# ===========================================================
# BUTTON HANDLING
# ===========================================================

def handle_button(button_id):
    global _running
    global _dirty_ui

    Gumps.CloseGump(GUMP_ID)

    if button_id == BTN_CLOSE:
        _running = False
        return

    if button_id == BTN_DROP_TILE:
        drop_at_targeted_tile()
        _dirty_ui = True
        return

    if button_id == BTN_CAGE_TARGET:
        cage_target()
        _dirty_ui = True
        return


# ===========================================================
# MAIN
# ===========================================================

def Main():
    global _dirty_ui

    set_status("Ready. Keep four boxes handy.")

    while _running and Player.Connected:
        handled_button = False
        gd = Gumps.GetGumpData(GUMP_ID)
        button_id = int(getattr(gd, "buttonid", 0)) if gd else 0

        if button_id > 0:
            try:
                gd.buttonid = 0
            except:
                pass

            handle_button(button_id)
            handled_button = True
            Misc.Pause(BUTTON_DEBOUNCE_MS)

        if not _running:
            break

        if not handled_button and _dirty_ui:
            render_gui()

        Misc.Pause(REFRESH_MS)

    Gumps.CloseGump(GUMP_ID)


Main()
