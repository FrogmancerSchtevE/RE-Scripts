# ==================================
# ==  Shop till you drop tool ==
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

import Gumps, Items, Target, Misc, Player

# ================================================================
# CONFIGURATION
# ================================================================
GUMP_ID       = 0x88FF1133
ROW_HEIGHT    = 22
ROWS_PER_PAGE = 20

BTN_RETARGET  = 9001
BTN_CLOSE     = 9002

BUY_BTN_BASE  = 30000     
SHOW_BTN_BASE = 50000     
REVEAL_BTN_BASE = 40000

PRICE_X = 260

# ================================================================
# STATE (DO NOT EDIT)
# ================================================================
_running          = True
_container_serial = None
_items_cache      = []
_current_page     = 1
_gump_open = False



# ================================================================
# HELPERS (DO NOT EDIT)
# ================================================================

def prompt_container():
    global _container_serial
    Misc.SendMessage("Target vendor backpack or container.", 68)
    serial = Target.PromptTarget("Select vendor container")

    if serial <= 0:
        Misc.SendMessage("Cancelled.", 33)
        return False

    itm = Items.FindBySerial(serial)
    if not itm:
        Misc.SendMessage("Invalid container.", 33)
        return False

    _container_serial = serial
    Items.UseItem(serial)
    Items.WaitForContents(serial, 2000)
    return True


def parse_deed_quantity(props):
    for line in props:
        if "contains:" in line.lower():
            raw = line.split(":")[1].strip()
            return raw  
    return None

def parse_price(props):
    for line in props:
        if "price" in line.lower():
            clean = line.replace(":", "").split()
            for p in clean:
                if p.isdigit():
                    return int(p)
    return 0

def parse_relic_type(props):

    for line in props:
        if "relic" in line.lower() and "ability" not in line.lower():
            return line.strip()
    return None
    

def load_items():
    global _items_cache
    lst = []

    if not _container_serial:
        _items_cache = []
        return

    cont = Items.FindBySerial(_container_serial)
    if not cont or not cont.Contains:
        _items_cache = []
        return

    for itm in cont.Contains:
        Items.WaitForProps(itm.Serial, 800)
        props = Items.GetPropStringList(itm.Serial)

        name = itm.Name if itm.Name else "<no name>"
        price = parse_price(props)

        # Commodity Deed Parser
        if name.lower() == "a commodity deed":
            qty = parse_deed_quantity(props)
            if qty:
                name = f"commodity deed ({qty})"

        # Creature Ability Relic Parser
        if "relic" in name.lower() and "ability" in name.lower():
            relic_type = parse_relic_type(props)
            if relic_type:
                short = relic_type.replace("Relic", "").strip()
                name = f"Creature Ability Relic ({short})"

        lst.append((itm.Serial, name, price))


    _items_cache = lst

# ================================================================
# MAIN FUNCTIONS (DO NOT EDIT)
# ================================================================    
    
def show_item(serial):
    itm = Items.FindBySerial(serial)
    if not itm:
        return

    Items.SingleClick(serial)
    Misc.Pause(150)

    #Timer for Re-hue. Increase if you want
    Items.SetColor(serial, 1152)
    Misc.Pause(300)
    Items.SetColor(serial, -1)
    

def buy_item(serial):

    try:
        Gumps.CloseGump(GUMP_ID)
        Misc.Pause(40)

        Items.SingleClick(serial)
        Misc.WaitForContext(serial, 5000)

        Misc.ContextReply(serial, 0)

        Player.HeadMessage(68, "Purchase attempt sent.")
        Misc.Pause(200)

    except Exception as e:
        Player.HeadMessage(33, "Buy failed.")
        
def reveal_item(serial):
    try:
        itm = Items.FindBySerial(serial)
        if not itm:
            Player.HeadMessage(33, "Item not found.")
            return

        Items.Move(serial, _container_serial, itm.Position.X, itm.Position.Y, itm.Amount)

        Player.HeadMessage(68, "Item brought to top.")

        Items.SingleClick(serial)
        Misc.Pause(80)

    except Exception as e:
        Misc.SendMessage(f"Reveal failed: {e}", 33)
        

# ================================================================
# GUI BUILDING (DO NOT EDIT)
# ================================================================

def render_gump():
    global _current_page

    Gumps.CloseGump(GUMP_ID)
    Misc.Pause(20)

    gd = Gumps.CreateGump(movable=True)
    gd.gumpId = GUMP_ID
    gd.serial = Player.Serial

    Gumps.AddPage(gd, 0)

    width  = 450
    height = 150 + ROWS_PER_PAGE * ROW_HEIGHT

    Gumps.AddBackground(gd, 0, 0, width, height, 5054)
    Gumps.AddAlphaRegion(gd, 0, 0, width, height)

    Gumps.AddLabel(gd, 10, 10, 68, f"Frogs' Vendor Item Browser   [Page {_current_page}]")
    Gumps.AddLabel(gd, width-20, 11, 33, "X")

    Gumps.AddLabel(gd, 20, 75, 1152, "Item")
    Gumps.AddLabel(gd, PRICE_X, 75, 1152, "Price")
    Gumps.AddLabel(gd, 330, 75, 1152, "Show")
    Gumps.AddLabel(gd, 370, 75, 1152, "Lift")
    Gumps.AddLabel(gd, 410, 75, 1152, "Buy")

    Gumps.AddPage(gd, 1)

    Gumps.AddButton(gd, width-40, 10, 4017, 4019, BTN_CLOSE, 1, 1)

    Gumps.AddButton(gd, 10, 40, 4011, 4013, BTN_RETARGET, 1, 0)
    Gumps.AddLabel(gd, 45, 42, 1152, "Retarget Container")

    if _container_serial is None:
        Gumps.AddLabel(gd, 20, 100, 33, "No container selected.")
        Gumps.AddLabel(gd, 20, 125, 53, "Click 'Retarget Container' to begin.")
        Gumps.SendGump(gd, 180, 180)
        return

    # Paging
    total = len(_items_cache)
    max_page = max(1, (total + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)
    if _current_page > max_page:
        _current_page = max_page

    start = (_current_page - 1) * ROWS_PER_PAGE
    end   = min(total, start + ROWS_PER_PAGE)

    y = 100
    for i in range(start, end):
        serial, name, price = _items_cache[i]

        Gumps.AddLabel(gd, 20, y, 55, name)

        Gumps.AddLabel(gd, PRICE_X, y, 68, f"{price:,}")

        Gumps.AddButton(gd, 330, y, 4005, 4007, SHOW_BTN_BASE + i, 1, 0)
        
        Gumps.AddButton(gd, 370, y, 4005, 4007, REVEAL_BTN_BASE + i, 1, 0)

        Gumps.AddButton(gd, 410, y, 4005, 4007, BUY_BTN_BASE + i, 1, 0)

        y += ROW_HEIGHT

    # Paging buttons
    if _current_page > 1:
        Gumps.AddButton(gd, 20, height-30, 4014, 4016, 99001, 1, 0)
        Gumps.AddLabel(gd, 50, height-28, 53, "Prev")

    if _current_page < max_page:
        Gumps.AddButton(gd, 120, height-30, 4005, 4007, 99002, 1, 0)
        Gumps.AddLabel(gd, 150, height-28, 53, "Next")

    Gumps.SendGump(gd, 180, 180)

# ================================================================
# BUTTON HANDLING (DO NOT EDIT)
# ================================================================

def handle_buttons():
    global _running, _current_page

    gd = Gumps.GetGumpData(GUMP_ID)
    if not gd or gd.buttonid == 0:
        return False

    btn = gd.buttonid

    if btn == BTN_CLOSE:
        _running = False
        return True

    if btn == BTN_RETARGET:
        prompt_container()
        load_items()
        return True

    if btn == 99001:
        _current_page = max(1, _current_page - 1)
        return True

    if btn == 99002:
        total = len(_items_cache)
        max_page = max(1, (total + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)
        _current_page = min(max_page, _current_page + 1)
        return True
        
    if SHOW_BTN_BASE <= btn < SHOW_BTN_BASE + 5000:
        index = btn - SHOW_BTN_BASE
        if 0 <= index < len(_items_cache):
            serial = _items_cache[index][0]
            show_item(serial)
        return True
        
    if REVEAL_BTN_BASE <= btn < REVEAL_BTN_BASE + 5000:
        index = btn - REVEAL_BTN_BASE
        if 0 <= index < len(_items_cache):
            serial = _items_cache[index][0]
            reveal_item(serial)
        return True
    
               
    if BUY_BTN_BASE <= btn < BUY_BTN_BASE + 10000:
        index = btn - BUY_BTN_BASE
        if 0 <= index < len(_items_cache):
            serial = _items_cache[index][0]
            buy_item(serial)
            return True

    return False


# ================================================================
# MAIN LOOP (DO NOT EDIT)
# ================================================================
Misc.Pause(50)
render_gump()

while _running and Player.Connected:
    
    acted = handle_buttons()
    if acted:
        load_items()
        render_gump()
    Misc.Pause(80)
