# ==================================
# === SimpleMoveTool ===
# ==================================
# Author: Frogmancer Schteve
# Idea from: sos440 
#
# NOTICE:
# This script is intended for personal use and community sharing.
# It is NOT intended to be fed into machine learning models, AI
# training pipelines, or derivative automated systems.
#
# If you found this, great! Use it, learn from it, and adapt it.
# But please don’t upload, re-ingest, or recycle it into LLMs.
#
# Contribute your own creativity instead — that’s how we built this.
#

import Misc, Gumps, Target, Items, Player, Mobiles

# ====================================================================
# CONFIG / CONSTANTS
# ====================================================================
GUMP_ID     = 0x7A1C01
REFRESH_MS  = 200
GUMP_POS    = (650, 400)
GUMP_WIDTH  = 230
GUMP_HEIGHT = 150

# GUI Configs
HEADER_HUE       = 1152   
LABEL_HUE        = 11     
VALUE_HUE        = 53     
BUTTON_LABEL_HUE = 54     
STATUS_HUE       = 67    

# Button IDs
BTN_MOVE_ITEM       = 9001
BTN_MOVE_TO_GROUND  = 9002
BTN_MOVE_TO_OBJECT  = 9003
BTN_BACK            = 9004

# ====================================================================
# STATE
# ====================================================================
_running         = True
_status_msg      = "Idle"
_selected_serial = None       
_current_page    = 0          

# ====================================================================
# HELPERS
# ====================================================================
def set_status(msg):
    global _status_msg
    _status_msg = str(msg)

def prompt_item():
    set_status("Select item to move...")
    Misc.SendMessage("Select the item to move.", 0x3B2)
    serial = Target.PromptTarget("Select the item to move.", 0x3B2)
    if serial == -1:
        set_status("Cancelled.")
        return None

    item = Items.FindBySerial(serial)
    if not item:
        set_status("Invalid item.")
        Misc.SendMessage("Invalid item selected.", 0x21)
        return None

    name = item.Name or "Item"
    set_status("Selected: %s" % name)
    return serial

def prompt_ground():
    set_status("Target ground location...")
    Misc.SendMessage(
        "Now, target the location where you wish to move your item.",
        0x3B2
    )
    pos = Target.PromptGroundTarget(
        "Now, target the location where you wish to move your item.",
        0x3B2
    )

    # User cancelled
    if pos is None or pos.X == -1 or pos.Y == -1:
        Misc.SendMessage("You cancelled the process.", 0x21)
        set_status("Cancelled.")
        return None

    set_status("Ground selected.")
    return pos

def prompt_object():
    set_status("Target object/mobile...")
    Misc.SendMessage(
        "Target the object or mobile you wish to move your item onto.",
        0x3B2
    )
    serial = Target.PromptTarget(
        "Target the object you wish to move your item onto.",
        0x3B2
    )
    if serial == -1:
        set_status("Cancelled.")
        return None

    target = None
    if Misc.IsItem(serial):
        target = Items.FindBySerial(serial)
        if not target:
            set_status("Invalid item target.")
            Misc.SendMessage("Please target a valid object.", 0x21)
            return None
        if not target.OnGround:
            set_status("Object not on ground.")
            Misc.SendMessage("That object is not on ground.", 0x21)
            return None

    elif Misc.IsMobile(serial):
        target = Mobiles.FindBySerial(serial)
        if not target:
            set_status("Invalid mobile target.")
            Misc.SendMessage("Please target a valid mobile.", 0x21)
            return None
    else:
        set_status("Invalid target.")
        Misc.SendMessage("Please target a valid object.", 0x21)
        return None

    set_status("Object position selected.")
    return target.Position

def move_item(item_serial, pos):
    item = Items.FindBySerial(item_serial)
    if not item:
        set_status("Item lost.")
        Misc.SendMessage(
            "Item no longer found (it may have moved or been deleted).",
            0x21
        )
        return False

    dx = Player.Position.X - pos.X
    dy = Player.Position.Y - pos.Y
    if max(abs(dx), abs(dy)) > 2:
        set_status("Too far.")
        Misc.SendMessage("That location is too far!", 0x21)
        return False

    Items.MoveOnGround(item.Serial, -1, pos.X, pos.Y, pos.Z)
    set_status("Item moved.")
    Misc.SendMessage("Item moved successfully!", 0x5A)
    return True

def get_item_name(serial):
    item = Items.FindBySerial(serial)
    return item.Name if item else "(lost reference)"

# ====================================================================
# GUI / GUMP
# ====================================================================
def draw_gui():
    try:
        Gumps.CloseGump(GUMP_ID)
    except:
        pass

    gd = Gumps.CreateGump(True)

    # Frame
    Gumps.AddBackground(gd, 0, 0, GUMP_WIDTH, GUMP_HEIGHT, 9270)
    Gumps.AddAlphaRegion(gd, 10, 10, GUMP_WIDTH - 20, GUMP_HEIGHT - 20)

    x = 20
    y = 20

    # Header
    Gumps.AddLabel(gd, x, y, HEADER_HUE, "Simple Move Tool")
    y += 20

    # ------------ PAGE 0: MAIN MENU ------------
    if _current_page == 0:
        Gumps.AddLabel(gd, x, y, LABEL_HUE, "Ready to move an item.")
        y += 20

        Gumps.AddButton(gd, x, y, 4005, 4007, BTN_MOVE_ITEM, 1, 0)
        Gumps.AddLabel(gd, x + 25, y + 2, BUTTON_LABEL_HUE, "Move Item")
        y += 26

        # Status
        status = _status_msg
        if len(status) > 40:
            status = status[:37] + "..."
        Gumps.AddLabel(gd, x, y, STATUS_HUE, "Status:")
        Gumps.AddLabel(gd, x + 55, y, VALUE_HUE, status)

    # ------------ PAGE 1: MOVE OPTIONS ------------
    elif _current_page == 1:
        name = get_item_name(_selected_serial)
        Gumps.AddLabel(gd, x, y, LABEL_HUE, "Selected:")
        Gumps.AddLabel(gd, x + 70, y, VALUE_HUE, name)
        y += 20

        Gumps.AddButton(gd, x, y, 4005, 4007, BTN_MOVE_TO_GROUND, 1, 0)
        Gumps.AddLabel(gd, x + 25, y + 2, BUTTON_LABEL_HUE, "Move To Ground")
        y += 22

        Gumps.AddButton(gd, x, y, 4005, 4007, BTN_MOVE_TO_OBJECT, 1, 0)
        Gumps.AddLabel(gd, x + 25, y + 2, BUTTON_LABEL_HUE, "Move To Object")
        y += 22

        Gumps.AddButton(gd, x, y, 4014, 4016, BTN_BACK, 1, 0)
        Gumps.AddLabel(gd, x + 25, y + 2, BUTTON_LABEL_HUE, "Back")

    Gumps.SendGump(
        GUMP_ID,
        Player.Serial,
        GUMP_POS[0],
        GUMP_POS[1],
        gd.gumpDefinition,
        gd.gumpStrings
    )

# ====================================================================
# BUTTON HANDLER
# ====================================================================
def handle_button(button_id):
    """Suite-style button dispatcher."""
    global _current_page, _selected_serial, _running

    if button_id == 0:
        return False  

    # -------- PAGE 0: MAIN --------
    if _current_page == 0:
        if button_id == BTN_MOVE_ITEM:
            sel = prompt_item()
            if sel:
                _selected_serial = sel
                _current_page = 1
            return True  

    # -------- PAGE 1: MOVE OPTIONS --------
    elif _current_page == 1:
        if button_id == BTN_MOVE_TO_GROUND:
            pos = prompt_ground()
            if pos:
                move_item(_selected_serial, pos)
            return True

        if button_id == BTN_MOVE_TO_OBJECT:
            pos = prompt_object()
            if pos:
                move_item(_selected_serial, pos)
            return True

        if button_id == BTN_BACK:
            _selected_serial = None
            _current_page = 0
            set_status("Idle")
            Misc.Pause(150)  
            return True

    return False  


# ====================================================================
# MAIN
# ====================================================================
def main():
    global _running, _selected_serial, _current_page

    _running = True
    _selected_serial = None
    _current_page = 0
    set_status("Idle")

    while _running and Player.Connected:
        gd = Gumps.GetGumpData(GUMP_ID)
        redrawn = False

        if gd and gd.buttonid:
            handled = handle_button(gd.buttonid)
            if handled:
                redrawn = True

        if not redrawn:
            draw_gui()

        Misc.Pause(REFRESH_MS)

    try:
        Gumps.CloseGump(GUMP_ID)
    except:
        pass
    Misc.SendMessage("Simple Move Tool closed.", 0x3B2)

# ====================================================================
# EXECUTION
# ====================================================================
if __name__ == "__main__":
    main()
