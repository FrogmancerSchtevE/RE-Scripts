# ==================================
# ===      WeaponSwapper         ===
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
import Gumps, Items, Misc, Player, Target

# ======================================================================
# CONFIG
# ======================================================================
GUMP_ID = 0xF00F1234
GUMP_X, GUMP_Y = 550, 300
REFRESH_MS = 200

WIDTH  = 300
HEIGHT = 210

BG_ID = 5054  

FROG_ICON = 0x2130
FROG_HUE  = 1152

TITLE_HUE = 1152
LABEL_HUE = 0x0481

ROW_H = 18

# ======================================================================
# SHARED VALUE KEYS
# ======================================================================
SET_KEYS = {
    1: ("weaponSet1_L", "weaponSet1_R"),
    2: ("weaponSet2_L", "weaponSet2_R"),
    3: ("weaponSet3_L", "weaponSet3_R"),
}

# ======================================================================
# BUTTON IDS
# ======================================================================
BTN_SET1 = 101
BTN_SET2 = 102
BTN_SET3 = 103
BTN_UNARM = 110

BTN_SETTINGS = 150
BTN_CLOSE = 199

BTN_SET_L1 = 201
BTN_SET_R1 = 202
BTN_SET_L2 = 203
BTN_SET_R2 = 204
BTN_SET_L3 = 205
BTN_SET_R3 = 206

BTN_RESET_ALL = 230
BTN_BACK = 250

# ======================================================================
# HELPERS
# ======================================================================
def load_serial(key):
    if Misc.CheckSharedValue(key):
        return Misc.ReadSharedValue(key)
    return 0

def save_serial(key, serial):
    Misc.SetSharedValue(key, serial)

def clear_all_sets():
    for n in (1,2,3):
        L_key, R_key = SET_KEYS[n]
        if Misc.CheckSharedValue(L_key):
            Misc.RemoveSharedValue(L_key)
        if Misc.CheckSharedValue(R_key):
            Misc.RemoveSharedValue(R_key)

def detect_wand_type(props):
    for p in props:
        if "charges" in p.lower():
            return p.split("Charges")[0].strip()
    return "Wand"

def is_spellbook(itm):
    if not itm:
        return False
    nm = (itm.Name or "").lower()
    return ("book" in nm) or ("spellbook" in nm)

def drag_equip(serial):
    Items.Move(serial, Player.Serial, -1)
    Misc.Pause(500)

def equip_item(serial):
    itm = Items.FindBySerial(serial)
    if not itm:
        return

    name = (itm.Name or "").lower()

    if "spellbook" in name or name.endswith("book") or "book" in name:
        try:
            Player.EquipItem(serial)
            Misc.Pause(500)
            return
        except:
            Items.Move(serial, Player.Serial, 2)  
            Misc.Pause(350)
            return

    try:
        Items.UseItem(serial)
        Misc.Pause(500)
        return
    except:
        try:
            Player.EquipItem(serial)
            Misc.Pause(500)
        except:
            Misc.SendMessage("Equip failed", 33)

def unarm():
    for layer in ("LeftHand", "RightHand"):
        itm = Player.GetItemOnLayer(layer)
        if itm:
            Items.Move(itm.Serial, Player.Backpack.Serial, 0)
            Misc.Pause(500)

def item_name_by_serial(serial):
    if serial <= 0:
        return "—"

    itm = Items.FindBySerial(serial)
    if not itm:
        return "Missing"

    Items.WaitForProps(serial, 500)
    nm = itm.Name or "Item"

    if "wand" in nm.lower():
        props = Items.GetPropStringList(serial)
        spell = detect_wand_type(props)
        return f"Wand ({spell})"

    return nm

def equip_set(n):
    L_key, R_key = SET_KEYS[n]
    L = load_serial(L_key)
    R = load_serial(R_key)

    unarm()

    if L:
        equip_item(L)
    if R:
        equip_item(R)

def set_slot(key, set_num, side):
    Misc.SendMessage(f"Target item for Set {set_num} {side}.", 68)
    serial = Target.PromptTarget("Target item", 0x3B2)

    if serial > 0:
        save_serial(key, serial)
        itm = Items.FindBySerial(serial)
        nm = itm.Name if itm else "Unknown"
        Player.HeadMessage(68, f"Set {set_num} {side}: {nm}")
        Misc.SendMessage(f"[Weapon Suite] Set {set_num} {side} = {nm}", 68)
    else:
        Player.HeadMessage(33, "Cancelled.")
        Misc.SendMessage("[Weapon Suite] Cancelled.", 33)

# ======================================================================
# GUI RENDERING
# ======================================================================
_current_page = "main"

def render_main():
    Gumps.CloseGump(GUMP_ID)
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)

    Gumps.AddBackground(gd, 0, 0, WIDTH, HEIGHT, BG_ID)
    Gumps.AddAlphaRegion(gd, 0, 0, WIDTH, HEIGHT)

    Gumps.AddItem(gd, 5, 5, FROG_ICON, FROG_HUE)
    Gumps.AddLabel(gd, 40, 8, TITLE_HUE, "Frog Weapon Suite 1.0")

    Gumps.AddButton(gd, WIDTH - 65, 5, 4029, 4030, BTN_SETTINGS, 1, 0)
    Gumps.AddButton(gd, WIDTH - 25, 5, 4017, 4018, BTN_CLOSE, 1, 0)

    y = 35

    for idx, n in enumerate((1,2,3)):
        L_key, R_key = SET_KEYS[n]
        label = f"Set {n}: {item_name_by_serial(load_serial(L_key))} / {item_name_by_serial(load_serial(R_key))}"

        Gumps.AddButton(gd, 10, y, 4014, 4015, BTN_SET1 + (n - 1), 1, 0)
        Gumps.AddLabel(gd, 40, y, LABEL_HUE, label)
        y += ROW_H

    y += 4
    Gumps.AddLabel(gd, 10, y, LABEL_HUE, "--------------------------------")
    y += 18

    Gumps.AddButton(gd, 10, y, 4014, 4015, BTN_UNARM, 1, 0)
    Gumps.AddLabel(gd, 40, y, LABEL_HUE, "Unarm")

    Gumps.SendGump(GUMP_ID, Player.Serial, GUMP_X, GUMP_Y, gd.gumpDefinition, gd.gumpStrings)

def render_settings():
    Gumps.CloseGump(GUMP_ID)
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)

    H = 260

    Gumps.AddBackground(gd, 0, 0, WIDTH, H, BG_ID)
    Gumps.AddAlphaRegion(gd, 0, 0, WIDTH, H)

    Gumps.AddItem(gd, 5, 5, FROG_ICON, FROG_HUE)
    Gumps.AddLabel(gd, 40, 8, TITLE_HUE, "Weapon Settings")

    Gumps.AddButton(gd, WIDTH - 65, 5, 4029, 4030, BTN_BACK, 1, 0)
    Gumps.AddButton(gd, WIDTH - 25, 5, 4017, 4018, BTN_CLOSE, 1, 0)

    y = 40
    for n in (1,2,3):
        L_key, R_key = SET_KEYS[n]

        Gumps.AddLabel(gd, 10, y, LABEL_HUE, f"Set {n}:")
        Gumps.AddButton(gd, 120, y, 4005, 4006, BTN_SET_L1 + 2*(n-1), 1, 0)
        Gumps.AddLabel(gd, 145, y, LABEL_HUE, "Left")

        Gumps.AddButton(gd, 120, y+20, 4005, 4006, BTN_SET_R1 + 2*(n-1), 1, 0)
        Gumps.AddLabel(gd, 145, y+20, LABEL_HUE, "Right")

        y += 55

    Gumps.AddLabel(gd, 10, y, LABEL_HUE, "--------------------------------")
    y += 20

    Gumps.AddButton(gd, 10, y, 4014, 4015, BTN_RESET_ALL, 1, 0)
    Gumps.AddLabel(gd, 40, y, LABEL_HUE, "Reset All Weapon Sets")

    Gumps.SendGump(GUMP_ID, Player.Serial, GUMP_X, GUMP_Y, gd.gumpDefinition, gd.gumpStrings)

# ======================================================================
# MAIN LOOP
# ======================================================================
render_main()

while Player.Connected:
    gd = Gumps.GetGumpData(GUMP_ID)

    if gd and gd.buttonid:
        bid = gd.buttonid
        gd.buttonid = 0

        if _current_page == "main":
            if bid == BTN_SET1: equip_set(1)
            elif bid == BTN_SET2: equip_set(2)
            elif bid == BTN_SET3: equip_set(3)
            elif bid == BTN_UNARM: unarm()
            elif bid == BTN_SETTINGS:
                _current_page = "settings"
                render_settings()
                Misc.Pause(150)
                continue
            elif bid == BTN_CLOSE:
                break

            render_main()
            Misc.Pause(250)
            continue

        if _current_page == "settings":
            if bid == BTN_BACK:
                _current_page = "main"
                render_main()
                Misc.Pause(150)
                continue

            if bid == BTN_CLOSE:
                break

            if bid == BTN_RESET_ALL:
                clear_all_sets()
                render_settings()
                Misc.Pause(250)
                continue

            button_to_slot = {
                BTN_SET_L1: (1, "Left"),
                BTN_SET_R1: (1, "Right"),
                BTN_SET_L2: (2, "Left"),
                BTN_SET_R2: (2, "Right"),
                BTN_SET_L3: (3, "Left"),
                BTN_SET_R3: (3, "Right"),
            }

            if bid in button_to_slot:
                set_num, side = button_to_slot[bid]
                key = SET_KEYS[set_num][0] if side == "Left" else SET_KEYS[set_num][1]
                set_slot(key, set_num, side)
                render_settings()
                Misc.Pause(150)
                continue

    Misc.Pause(REFRESH_MS)

