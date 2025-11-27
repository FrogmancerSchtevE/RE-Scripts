# ==================================
# ==  Leather/Scav Suite (Frog Edition) ==
# ==================================
# Author: Frogmancer Schteve
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
import Gumps, Player, Items, Target, Misc, time
from System import Int32
from System.Collections.Generic import List

# ===========================================================
# CONFIGURATION
# ===========================================================
GUMP_ID    = 0xBEEFBEEF
REFRESH_MS = 300
GUMP_X, GUMP_Y = 700, 550
SCAN_RANGE = 2

HIDE_ID     = 0x1079   # Uncut hide
LEATHER_ID  = 0x1081   # Finished leather
SCISSORS_ID = 0x0F9F   

# ===========================================================
# GLOBAL STATE
# ===========================================================
_running           = True
_auto_hide2leather = False   
_auto_loot_leather = False   
_auto_scavenge     = False   
_status_msg        = "Idle"
_last_scavenge_time = 0
_waiting_for_new_corpse = False
SCAVENGE_DELAY_MS = 1500  
SCAVENGE_COOLDOWN_MS = 1000 

_tool_serial       = Misc.ReadSharedValue("leatherSuiteTool") if Misc.CheckSharedValue("leatherSuiteTool") else 0
_container_serial  = Misc.ReadSharedValue("leatherSuiteBag") if Misc.CheckSharedValue("leatherSuiteBag") else 0

# Corpses we've fully processed (hides cut + leather looted)
_processed_corpses = set()

# ===========================================================
# BUTTON IDS
# ===========================================================
BTN_SET_TOOL            = 6001
BTN_SET_CONTAINER       = 6002
BTN_RESET               = 6003
BTN_SCAVENGE            = 6005   # manual scavenge button
BTN_TOGGLE_AUTOHIDE     = 6007
BTN_TOGGLE_AUTOLOOT     = 6008
BTN_CLOSE               = 6009
BTN_RESET_CORPSES       = 6010
BTN_TOGGLE_AUTOSCAVENGE = 6011

# ===========================================================
# HELPER FUNCTIONS
# ===========================================================
def get_tool():
    global _tool_serial
    if not _tool_serial:
        Player.HeadMessage(33, "No tool set.")
        return None
    tool = Items.FindBySerial(_tool_serial)
    if not tool:
        Player.HeadMessage(33, "Selected tool missing!")
        _tool_serial = 0
        return None
    return tool

def get_container():
    global _container_serial
    if not _container_serial:
        return None
    bag = Items.FindBySerial(_container_serial)
    if not bag:
        _container_serial = 0
        return None
    return bag

def select_tool():
    global _tool_serial
    Target.Cancel()
    Misc.SendMessage("Target your bladed tool (dagger, knife, etc.)", 55)
    serial = Target.PromptTarget("Select tool", 0x3B2)
    if serial > 0:
        _tool_serial = serial
        Misc.SetSharedValue("leatherSuiteTool", serial)
        try:
            Items.SetColor(serial, 1161)  # mark tool visually
        except:
            pass
        Player.HeadMessage(68, f"Tool stored (0x{serial:X}) and marked.")


def select_container():
    global _container_serial
    Target.Cancel()
    Misc.SendMessage("Target your leather storage container", 55)
    serial = Target.PromptTarget("Select container", 0x3B2)
    if serial > 0:
        _container_serial = serial
        Misc.SetSharedValue("leatherSuiteBag", serial)
        try:
            Items.SetColor(serial, 1161)  # mark bag visually
        except:
            pass
        Player.HeadMessage(68, f"Container stored (0x{serial:X}) and marked.")


def reset_settings():
    global _tool_serial, _container_serial
    if _tool_serial:
        try:
            Items.SetColor(_tool_serial, -1)
        except:
            pass
    if _container_serial:
        try:
            Items.SetColor(_container_serial, -1)
        except:
            pass

    _tool_serial = 0
    _container_serial = 0
    if Misc.CheckSharedValue("leatherSuiteTool"):
        Misc.RemoveSharedValue("leatherSuiteTool")
    if Misc.CheckSharedValue("leatherSuiteBag"):
        Misc.RemoveSharedValue("leatherSuiteBag")
    Player.HeadMessage(33, "Tool & Container reset (colors restored).")


def find_nearby_corpses():
    f = Items.Filter()
    f.Enabled = True
    f.IsCorpse = True
    f.OnGround = True
    f.RangeMax = SCAN_RANGE
    return list(Items.ApplyFilter(f) or [])

# ===========================================================
# MANUAL SCAVENGE (button)
# ===========================================================
def scavenge_area():
    """Use your blade on yourself for area skinning (manual button)."""
    global _status_msg
    tool = get_tool()
    if not tool:
        _status_msg = "No tool set."
        return
    _status_msg = "Scavenging nearby corpses..."
    Items.UseItem(tool)
    if Target.WaitForTarget(2000, False):
        Target.Self()
    Misc.Pause(1000)
    _status_msg = "Scavenge complete."

# ===========================================================
# AUTO LOOT LEATHER FROM GROUND
# ===========================================================
def loot_leather():
    """Auto-loot stray leather from the ground near player."""
    global _status_msg
    leathers = Items.Filter()
    leathers.Enabled = True
    leathers.OnGround = True
    leathers.Movable = True
    leathers.RangeMax = SCAN_RANGE
    leathers.Graphics = List[Int32]([LEATHER_ID])
    found = Items.ApplyFilter(leathers)

    if not found:
        return

    bag = get_container() or Player.Backpack

    for l in found:
        try:
            _status_msg = "Looting leather from ground..."
            Items.Move(l.Serial, bag.Serial, -1)
            Misc.Pause(600)
        except:
            pass

# ===========================================================
# CORPSE PROCESSING (Hides -> Leather -> Loot)
# ===========================================================
def process_corpse(corpse, scissors, bag):
    """Cut hides -> wait -> loot leather, mark corpse as processed (CUO handles open)."""
    global _status_msg

    if not corpse or corpse.Serial in _processed_corpses:
        return

    # Wait up to 2.5 s for CUO to auto-open this corpse
    waited = 0
    while (not corpse.Contains or len(corpse.Contains) == 0) and waited < 2500:
        Misc.Pause(250)
        waited += 250
        corpse = Items.FindBySerial(corpse.Serial)
    if not corpse or not corpse.Contains or len(corpse.Contains) == 0:
        _status_msg = "CUO hasn't opened corpse yet..."
        return

    hides = [i for i in corpse.Contains if i.ItemID == HIDE_ID]
    if not hides:
        return

    _status_msg = f"Processing corpse 0x{corpse.Serial:X}"

    for h in hides:
        success = False
        for attempt in range(3):  # try up to 3 times per hide
            Items.UseItem(scissors)
            if Target.WaitForTarget(1500, False):
                Target.TargetExecute(h)
                Misc.Pause(900)
                success = True
                break
            else:
                Misc.Pause(500)  # short delay before retry
        if not success:
            Player.HeadMessage(33, f"⚠️ Failed to cut hide {h.Serial:X} after 3 tries.")

    # --- Wait for conversion to complete (poll for leathers instead of fixed pause) ---
    _status_msg = "Waiting for hides to become leather..."
    start = time.time()
    leathers = []
    while time.time() - start < 1.5:  # up to ~1.5 seconds max
        corpse = Items.FindBySerial(corpse.Serial)
        if corpse and corpse.Contains:
            leathers = [i for i in corpse.Contains if i.ItemID == LEATHER_ID]
            if leathers:
                break
        Misc.Pause(300)

    # --- Loot as soon as leather detected ---
    if leathers:
        _status_msg = f"Looting {len(leathers)} leather..."
        bag = get_container() or Player.Backpack
        for l in leathers:
            try:
                Items.Move(l.Serial, bag.Serial, -1)
                Misc.Pause(250)  # shorter move delay = faster loot
            except:
                pass
        Player.HeadMessage(68, "Leather looted quickly.")
    else:
        _status_msg = "No leather detected after cut."

    # Mark corpse hue and memory
    try:
        Items.SetColor(corpse.Serial, 1161)
    except:
        pass
    _processed_corpses.add(corpse.Serial)


def turn_hides_to_leather():
    """Manual one-time run: converts hides in visible corpses and loots leather."""
    global _status_msg
    scissors = Items.FindByID(SCISSORS_ID, -1, Player.Backpack.Serial)
    if not scissors:
        _status_msg = "No scissors found."
        return

    corpses = find_nearby_corpses()
    if not corpses:
        _status_msg = "No corpses nearby."
        return

    bag = get_container() or Player.Backpack
    for corpse in corpses:
        if corpse.Serial in _processed_corpses:
            continue
        process_corpse(corpse, scissors, bag)
    _status_msg = "Manual processing complete."

def auto_hide_to_leather_tick():
    """Automatically convert hides to leather and loot, waiting for CUO to open corpses."""
    global _status_msg

    scissors = Items.FindByID(SCISSORS_ID, -1, Player.Backpack.Serial)
    if not scissors:
        _status_msg = "No scissors found."
        return

    corpses = find_nearby_corpses()
    if not corpses:
        _status_msg = "No corpses nearby."
        return

    bag = get_container() or Player.Backpack

    for corpse in corpses:
        if corpse.Serial in _processed_corpses:
            continue

        # Give CUO time to open before we skip
        waited = 0
        while (not corpse.Contains or len(corpse.Contains) == 0) and waited < 2500:
            Misc.Pause(250)
            waited += 250
            corpse = Items.FindBySerial(corpse.Serial)

        if not corpse or not corpse.Contains or len(corpse.Contains) == 0:
            continue

        process_corpse(corpse, scissors, bag)
        break  # one per tick

    Misc.Pause(500)    


# ===========================================================
# AUTO SCAVENGE TICK
# ===========================================================
def auto_scavenge_tick():
    """Auto-use blade on self when a new corpse is within 1 tile (with cooldown + delay)."""
    global _status_msg, _last_scavenge_time, _waiting_for_new_corpse

    now = time.time() * 1000  # ms clock

    # Enforce cooldown between actions
    if now - _last_scavenge_time < SCAVENGE_COOLDOWN_MS:
        _status_msg = "Waiting for cooldown..."
        return

    corpses = find_nearby_corpses()
    if not corpses:
        _waiting_for_new_corpse = False
        _status_msg = "Idle."
        return

    # Look for any unprocessed corpses within 1 tile
    close_corpses = [c for c in corpses if Player.DistanceTo(c) <= 1 and c.Serial not in _processed_corpses]
    if not close_corpses:
        _status_msg = "Waiting for new corpse..."
        return

    # If we've already handled this batch, just wait for new ones
    if _waiting_for_new_corpse:
        _status_msg = "Waiting for new corpse..."
        return

    # --- Delay before firing to let CUO handle auto-open ---
    _status_msg = "Corpse detected, waiting for CUO..."
    Misc.Pause(SCAVENGE_DELAY_MS)

    # Recheck that corpse still exists and close
    close_corpses = [c for c in find_nearby_corpses() if Player.DistanceTo(c) <= 1 and c.Serial not in _processed_corpses]
    if not close_corpses:
        _status_msg = "Corpse gone."
        return

    tool = get_tool()
    if not tool:
        _status_msg = "No tool set for auto-scavenge."
        return

    _status_msg = "Auto-skinning nearby corpse..."
    Items.UseItem(tool)

    # Give time for target cursor to appear
    Misc.Pause(350)
    for _ in range(5):
        if Target.HasTarget():
            Target.Self()
            break
        Misc.Pause(400)

    # Hue-mark and mark processed
    for c in close_corpses:
        try:
            Items.SetColor(c.Serial, 1161)
            _processed_corpses.add(c.Serial)
        except:
            pass

    _last_scavenge_time = time.time() * 1000
    _waiting_for_new_corpse = True
    _status_msg = "Waiting for new corpse..."


    
# ===========================================================
# BUTTON HANDLER
# ===========================================================
def handle_button(btn):
    global _auto_hide2leather, _auto_loot_leather, _auto_scavenge, _processed_corpses

    if btn == BTN_SET_TOOL:
        select_tool()
    elif btn == BTN_SET_CONTAINER:
        select_container()
    elif btn == BTN_RESET:
        reset_settings()
    elif btn == BTN_SCAVENGE:
        scavenge_area()
    elif btn == BTN_TOGGLE_AUTOHIDE:
        _auto_hide2leather = not _auto_hide2leather
        Misc.SendMessage(
            f"Auto Hide→Leather {'ON' if _auto_hide2leather else 'OFF'}",
            68 if _auto_hide2leather else 33
        )
    elif btn == BTN_TOGGLE_AUTOLOOT:
        _auto_loot_leather = not _auto_loot_leather
        Misc.SendMessage(
            f"Auto Loot Leather {'ON' if _auto_loot_leather else 'OFF'}",
            68 if _auto_loot_leather else 33
        )
    elif btn == BTN_TOGGLE_AUTOSCAVENGE:
        _auto_scavenge = not _auto_scavenge
        Misc.SendMessage(
            f"Auto Scavenge {'ON' if _auto_scavenge else 'OFF'}",
            68 if _auto_scavenge else 33
        )
    elif btn == BTN_RESET_CORPSES:
        _processed_corpses.clear()
        Misc.SendMessage("Cleared corpse memory.", 55)
    elif btn == BTN_CLOSE:
        Misc.ScriptStop("LeatherSuite")

# ===========================================================
# GUI RENDER
# ===========================================================
def render_gui():
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)
    Gumps.AddBackground(gd, 0, 0, 280, 230, 5054)
    Gumps.AddAlphaRegion(gd, 0, 0, 280, 230)
    title = "Frogs Leather Suite"
    title_x = (280 - (len(title) * 8)) // 2  # approximate width, 8px per char
    Gumps.AddLabel(gd, title_x, 10, 0x480, title)

    Gumps.AddLabel(gd, 20, 30, 0x47E, f"Status: {_status_msg}")

    # Row 1: tool / container
    Gumps.AddButton(gd, 20, 55, 4005, 4007, BTN_SET_TOOL, 1, 0)
    Gumps.AddLabel(gd, 55, 55, 0x44, "Set Tool")

    Gumps.AddButton(gd, 20, 75, 4005, 4007, BTN_SET_CONTAINER, 1, 0)
    Gumps.AddLabel(gd, 55, 75, 0x44, "Set Container")

    # Row 2: manual scavenge + auto scavenge toggle
    Gumps.AddButton(gd, 20, 95, 4011, 4013, BTN_SCAVENGE, 1, 0)
    Gumps.AddLabel(gd, 55, 95, 0x44, "Scavenge Area")

    Gumps.AddButton(gd, 20, 115, 4005, 4007, BTN_TOGGLE_AUTOSCAVENGE, 1, 0)
    Gumps.AddLabel(gd, 55, 115, 0x44, f"Auto Scavenge: {'ON' if _auto_scavenge else 'OFF'}")

    # Row 3: auto hide->leather / auto loot
    Gumps.AddButton(gd, 20, 135, 4005, 4007, BTN_TOGGLE_AUTOHIDE, 1, 0)
    Gumps.AddLabel(gd, 55, 135, 0x44,
                   f"Auto Hide>Leather: {'ON' if _auto_hide2leather else 'OFF'}")

    Gumps.AddButton(gd, 20, 155, 4005, 4007, BTN_TOGGLE_AUTOLOOT, 1, 0)
    Gumps.AddLabel(gd, 55, 155, 0x44,
                   f"Auto Loot: {'ON' if _auto_loot_leather else 'OFF'}")

    # Row 4: reset buttons + close
    Gumps.AddButton(gd, 20, 175, 4017, 4019, BTN_RESET, 1, 0)
    Gumps.AddLabel(gd, 55, 175, 0x66D, "Reset (Clear Tool & Bag)")

    Gumps.AddButton(gd, 20, 195, 4017, 4019, BTN_RESET_CORPSES, 1, 0)
    Gumps.AddLabel(gd, 55, 195, 0x34, "Reset Corpse Memory")

    Gumps.AddButton(gd, 200, 195, 4017, 4019, BTN_CLOSE, 1, 0)
    Gumps.AddLabel(gd, 235, 195, 0x21, "Close")

    Gumps.SendGump(GUMP_ID, Player.Serial, GUMP_X, GUMP_Y,
                   gd.gumpDefinition, gd.gumpStrings)

# ===========================================================
# MAIN LOOP
# ===========================================================
def main():
    global _status_msg
    while _running and Player.Connected:
        gd = Gumps.GetGumpData(GUMP_ID)
        if gd and gd.buttonid > 0:
            handle_button(gd.buttonid)
            Misc.Pause(200)

        # Auto systems
        if _auto_scavenge:
            auto_scavenge_tick()
        if _auto_hide2leather:
            auto_hide_to_leather_tick()
        if _auto_loot_leather:
            loot_leather()

        render_gui()
        Misc.Pause(REFRESH_MS)

# ===========================================================
# INIT
# ===========================================================
if __name__ == "__main__":
    Gumps.CloseGump(GUMP_ID)
    Misc.SendMessage("Leather Suite started.", 68)
    main()
