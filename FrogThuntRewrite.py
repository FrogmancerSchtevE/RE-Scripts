# Extreme Treasure Hunting Frogs Python Fork
# Original Script by NKR in C#

import re


VERSION = "0.0.5"


HIGHLIGHT_MODE = "Hue"   # "overhead" | "hue" 
BOOK_HIGHLIGHT_HUE = 1152
_SHARED_LAST_HL = "ETH:LastHLBook"

FORCE_SINGLETON_FACET_HIGHLIGHT = {
    "Tokuno": True,
    "Ter Mur": True,
    "Ilshenar": True,
}

# Gump / colors
GUMP_ID = 54321542            
GUMP_WIDTH = 310             
STYLE_BG_GFX = 30546          
STYLE_ROW_PAD = 10
STYLE_HEADER_H = 36
STYLE_STATUS_H = 28
STYLE_ACTION_H = 40
STYLE_DIVIDER_GFX = 40004     
STYLE_BAR_GFX    = 9354       
TITLE_COLOR = 0x35
TEXT_COLOR  = 0x0481
STATUS_COLOR_IDLE   = 0x067   
STATUS_COLOR_ACTIVE = 0x03F   
MSG_COLOR_PROMPT    = 0x090   
MSG_COLOR_OK        = 0x03C   
MSG_COLOR_ERR       = 0x021   
HUNT_BUTTON_GFX         = 0x9C52   
HUNT_BUTTON_LABEL_COLOR = 0x3E8    


TREASURE_MAP_ITEMID = 0x14EC
TREASURE_CHEST_ITEMIDS = [0xA308, 0xA304, 0xA306]
LOCKPICK_ITEMID = 0x14FC

FACET_NAMES = ["Felucca", "Trammel", "Ilshenar", "Malas", "Tokuno", "Ter Mur"]


import Misc, Items, Gumps, Player, Target, Journal, Statics
try:
    import CUO
except:
    class _Dummy:
        @staticmethod
        def FreeView(x): pass
    CUO = _Dummy()

_MODE = (HIGHLIGHT_MODE or "").strip().lower()

class RunebookRect(object):
    def __init__(self, serial, minx, miny, maxx, maxy):
        if minx > maxx: minx, maxx = maxx, minx
        if miny > maxy: miny, maxy = maxy, miny
        self.serial = int(serial)
        self.minx, self.miny, self.maxx, self.maxy = int(minx), int(miny), int(maxx), int(maxy)
    def contains(self, x, y):
        return (self.minx <= x <= self.maxx) and (self.miny <= y <= self.maxy)

class RunebookSet(object):
    def __init__(self):
        self.Trammel = [
            RunebookRect(0x7d6d215b, 4400, 1100, 4800, 3800),
            RunebookRect(0x7d6d3524, 3700, 1100, 4300, 3800),
            RunebookRect(0x7d6dc52e, 3100, 100, 3600, 2600),
            RunebookRect(0x7d6dcaf5, 2700, 100, 3000, 3600),
            RunebookRect(0x7d6d3419, 2400, 200, 2600, 2200),
            RunebookRect(0x7d6dc5c7, 2100, 100, 2300, 3500),
            RunebookRect(0x7d6da84d, 1900, 200, 2000, 3500),
            RunebookRect(0x7d6dafc0, 1700, 2000, 1800, 3500),
            RunebookRect(0x7d6dcb1a, 1500, 100, 1700, 1000),
            RunebookRect(0x7d6db11b, 1400, 200, 1500, 2600),
            RunebookRect(0x7d6db069, 1200, 200, 1300, 3700),
            RunebookRect(0x7d6dc4d6, 1000, 300, 1100, 3500),
            RunebookRect(0x7d6dcb4b, 700, 1800, 900, 2500),
            RunebookRect(0x7d6daffe, 100, 1500, 700, 1900),
        ]
        self.Felucca = [
            RunebookRect(0x7d6653b5, 4500, 900, 4800, 3800),
            RunebookRect(0x7d6dc5a7, 3500, 200, 4400, 3800),
            RunebookRect(0x7d6dca59, 2900, 100, 3400, 2700),
            RunebookRect(0x7d6dbe2e, 2500, 100, 2800, 3500),
            RunebookRect(0x7d6d34d2, 2100, 100, 2400, 3500),
            RunebookRect(0x7d6dbd04, 1900, 200, 2000, 3500),
            RunebookRect(0x7d6dca2e, 1700, 1400, 1800, 3500),
            RunebookRect(0x7d6dc490, 1500, 1300, 1700, 2400),
            RunebookRect(0x7d6dbd60, 1300, 2300, 1500, 2700),
            RunebookRect(0x7d6d1fda, 1200, 200, 1300, 2500),
            RunebookRect(0x7d6dca89, 1000, 302, 1110, 3500),
            RunebookRect(0x7d6d344c, 720, 2200, 926, 2600),
            RunebookRect(0x7d664874, 100, 1500, 725, 2000),
        ]
        self.Malas = [
            RunebookRect(0x7d6dbe7e, 2300, 600, 2500, 1400),
            RunebookRect(0x7d6da894, 1700, 600, 2000, 900),
            RunebookRect(0x7d6daa1c, 1400, 100, 1700, 700),
            RunebookRect(0x7d6dbdde, 600, 400, 1000, 600),
            RunebookRect(0x7d6d20a6, 2000, 700, 2300, 1300),
            RunebookRect(0x7d6d33c7, 1000, 500, 1300, 1900),
        ]
        self.Ilshenar = [ RunebookRect(0x7d6d18ec, 300, 500, 2000, 100), ]
        self.Tokuno   = [ RunebookRect(0x7d6d29f0, 100, 700, 1200, 1000), ]
        self.TerMur   = [ RunebookRect(0x7d6db5f8, 500, 3100, 1000, 3400), ]

RUNES = RunebookSet()

STATE_IDLE = 0
STATE_DECODING = 1
STATE_HUNTING = 2
STATE_DIGGING = 3
STATE_DUG = 4
STATE_PICKING = 5
STATE_REMOVING_TRAP = 6
STATE_OPENED = 7

BTN_CLOSE = 0
BTN_HUNT = 1
BTN_DIG = 2
BTN_OPEN = 3
BTN_CLEANUP = 4
BTN_LOOT = 5
BTN_CANCEL = 6


_selected_map_serial = -1
_selected_map_props = None  
_map_runebook = None        
_treasure_chest_item = None
_map_setup_done = False
_state = STATE_IDLE
_last_probe = None

_original_item_state = {}   
_pending_reverts = set()    
_bad_hue_serials = set()    

def _get_facet_list(name):
    if name == "Felucca": return RUNES.Felucca
    if name == "Trammel": return RUNES.Trammel
    if name == "Ilshenar": return RUNES.Ilshenar
    if name == "Malas":   return RUNES.Malas
    if name == "Tokuno":  return RUNES.Tokuno
    if name == "Ter Mur": return RUNES.TerMur
    return []

def _item_loaded(serial):
    try:
        it = Items.FindBySerial(int(serial))
        return it is not None and not getattr(it, "Deleted", False)
    except:
        return False

def _get_item(serial):
    try:
        return Items.FindBySerial(int(serial))
    except:
        return None

def _reset_all_book_hues():
    for b in RUNES.Trammel:  Items.SetColor(b.serial, -1)
    for b in RUNES.Felucca:  Items.SetColor(b.serial, -1)
    for b in RUNES.Malas:    Items.SetColor(b.serial, -1)
    for b in RUNES.Ilshenar: Items.SetColor(b.serial, -1)
    for b in RUNES.Tokuno:   Items.SetColor(b.serial, -1)
    for b in RUNES.TerMur:   Items.SetColor(b.serial, -1)
    if Misc.CheckSharedValue(_SHARED_LAST_HL):
        try:
            last = int(Misc.ReadSharedValue(_SHARED_LAST_HL))
            Items.SetColor(last, -1)
        except: pass
        Misc.RemoveSharedValue(_SHARED_LAST_HL)
    _original_item_state.clear()
    _pending_reverts.clear()

def _record_original_state(serial):
    if serial in _original_item_state:  
        return
    it = _get_item(serial)
    if not it: return
    try:
        _original_item_state[serial] = {"hue": int(getattr(it, "Hue", -1)), "itemid": int(getattr(it, "ItemID", 0))}
    except:
        _original_item_state[serial] = {"hue": -1, "itemid": 0}

def _restore_original_state(serial):
    serial = int(serial)
    info = _original_item_state.get(serial, None)
    if not _item_loaded(serial):
        _pending_reverts.add(serial)
        if Misc.CheckSharedValue(_SHARED_LAST_HL): Misc.RemoveSharedValue(_SHARED_LAST_HL)
        return

    if _MODE == "hue":
        try:
            if info and "hue" in info and info["hue"] >= 0:
                Items.SetColor(serial, int(info["hue"]))
            else:
                Items.SetColor(serial, -1)
        except:
            pass

    _original_item_state.pop(serial, None)
    _pending_reverts.discard(serial)
    if Misc.CheckSharedValue(_SHARED_LAST_HL): Misc.RemoveSharedValue(_SHARED_LAST_HL)

def _apply_highlight(serial):
    if not serial: return
    serial = int(serial)

    if Misc.CheckSharedValue(_SHARED_LAST_HL):
        try:
            prev = int(Misc.ReadSharedValue(_SHARED_LAST_HL))
            if prev != serial:
                _restore_original_state(prev)
        except:
            pass

    if not _item_loaded(serial):
        Misc.SetSharedValue(_SHARED_LAST_HL, serial)
        return

    _record_original_state(serial)

    if serial in _bad_hue_serials or _MODE != "hue":
        Items.Message(serial, BOOK_HIGHLIGHT_HUE, "◄ book")
        Misc.SetSharedValue(_SHARED_LAST_HL, serial)
        return

    it_before = _get_item(serial)
    before_id = int(getattr(it_before, "ItemID", 0)) if it_before else 0
    try:
        Items.SetColor(serial, BOOK_HIGHLIGHT_HUE)
    except:
        Items.Message(serial, BOOK_HIGHLIGHT_HUE, "◄ book")
        Misc.SetSharedValue(_SHARED_LAST_HL, serial)
        return

    Misc.SetSharedValue(_SHARED_LAST_HL, serial)

    it_after = _get_item(serial)
    after_id = int(getattr(it_after, "ItemID", 0)) if it_after else 0
    if after_id and before_id and after_id != before_id:
        _restore_original_state(serial)
        _bad_hue_serials.add(serial)
        Items.Message(serial, BOOK_HIGHLIGHT_HUE, "Pick Me!")

def _clear_highlight():
    if Misc.CheckSharedValue(_SHARED_LAST_HL):
        try:
            last = int(Misc.ReadSharedValue(_SHARED_LAST_HL))
            _restore_original_state(last)
        except:
            pass
        if Misc.CheckSharedValue(_SHARED_LAST_HL):
            Misc.RemoveSharedValue(_SHARED_LAST_HL)

def _clear_selected_treasure():
    global _state, _selected_map_serial, _selected_map_props, _map_runebook
    global _treasure_chest_item, _map_setup_done, _last_probe
    _state = STATE_IDLE
    _selected_map_serial = -1
    _selected_map_props = None
    _map_runebook = None
    _treasure_chest_item = None
    _map_setup_done = False
    _last_probe = None
    try: Player.TrackingArrow(0, 0, False)
    except: pass
    _clear_highlight()

def _hunt_decoded_map():
    global _selected_map_props, _state
    item = Items.FindBySerial(_selected_map_serial)
    if not item:
        Player.HeadMessage(MSG_COLOR_ERR, "Map not found anymore.")
        _clear_selected_treasure()
        _update_gump()
        return
    try:
        Items.WaitForProps(item, 1000)
        prop_lines = [str(s) for s in Items.GetPropStringList(item)]
    except:
        prop_lines = []

    level = (item.Name or "").split(' ')[-1]
    try: facet = prop_lines[3].split(' ')[-1]
    except: facet = FACET_NAMES[Player.Map] if 0 <= Player.Map < len(FACET_NAMES) else "Trammel"
    if facet == "Mur": facet = "Ter Mur"
    elif facet == "Islands": facet = "Tokuno"

    coordsX = coordsY = 0
    try:
        m = re.search(r"Location:\s*\((\d+),\s*(\d+)\)", prop_lines[4])
        if m: coordsX, coordsY = int(m.group(1)), int(m.group(2))
    except: pass

    _selected_map_props = (level, facet, coordsX, coordsY)
    _state = STATE_HUNTING
    _update_gump()

def _resolve_runebook(facet, x, y):
    flist = _get_facet_list(facet)
    for rb in flist:
        if rb.contains(x, y):
            return rb
    if FORCE_SINGLETON_FACET_HIGHLIGHT.get(facet, False) and len(flist) == 1:
        return flist[0]
    return None

def _highlight_runebook():
    global _map_runebook, _last_probe
    if not _selected_map_props:
        _clear_highlight()
        _map_runebook, _last_probe = None, None
        return

    level, facet, x, y = _selected_map_props
    probe = (facet, x, y)
    changed = (_map_runebook is None) or (_last_probe != probe) or (not _map_runebook.contains(x, y))
    if changed:
        new_rb = _resolve_runebook(facet, x, y)
        _last_probe = probe
        if new_rb is None:
            _clear_highlight()
            _map_runebook = None
            return
        if (_map_runebook is None) or (_map_runebook.serial != new_rb.serial):
            _clear_highlight()
            _apply_highlight(new_rb.serial)
        _map_runebook = new_rb
    else:
        if _map_runebook:
            _apply_highlight(_map_runebook.serial)

def _maintain_highlight():
    if not _pending_reverts:
        return
    to_clear = []
    for s in list(_pending_reverts):
        if _item_loaded(s):
            _restore_original_state(s)
            to_clear.append(s)
    for s in to_clear:
        _pending_reverts.discard(s)

def _debug_probe(x, y, facet=None):
    if facet is None:
        facet = FACET_NAMES[Player.Map] if 0 <= Player.Map < len(FACET_NAMES) else "Trammel"
    rb = _resolve_runebook(facet, int(x), int(y))
    if rb:
        Misc.SendMessage("Book for {} ({},{}): 0x{:X}".format(facet, x, y, rb.serial), 68)
    else:
        Misc.SendMessage("No book configured for {} ({},{}).".format(facet, x, y), 33)

def _setup_map_and_tracking():
    global _map_setup_done
    if not _selected_map_props or _map_setup_done: return
    _, _, x, y = _selected_map_props
    try: z = Statics.GetLandZ(x, y, Player.Map)
    except: z = 0
    zoffset = int(round(z / 10.0)) + 1
    Player.TrackingArrow(int(x - zoffset), int(y - zoffset), True)
    _map_setup_done = True

def _check_dig_distance_hint():
    if not _selected_map_props: return
    _, _, dx, dy = _selected_map_props
    px, py = Player.Position.X, Player.Position.Y
    dist = max(abs(px - dx), abs(py - dy))
    maxdig = 1
    try:
        cart = Player.GetSkillValue("Cartography")
        if cart >= 100: maxdig = 4
        elif cart >= 81: maxdig = 3
        elif cart >= 51: maxdig = 2
    except: pass
    if dist <= maxdig:
        Player.HeadMessage(MSG_COLOR_OK, "Hey, you're close enough to dig!")

def _dig_treasure():
    global _state
    if _selected_map_serial <= 0 or not _selected_map_props: return
    if Misc.UseContextMenu(_selected_map_serial, "Dig For Treasure", 1000):
        _, _, x, y = _selected_map_props
        try: z = Statics.GetLandZ(x, y, Player.Map)
        except: z = 0
        Target.WaitForTarget(1000)
        Target.TargetExecute(int(x), int(y), int(z))
        try: Target.Self()
        except: pass
        _state = STATE_DIGGING

def _open_chest():
    global _state
    Journal.Clear()
    _state = STATE_PICKING

def _clean_chest():
    global _treasure_chest_item
    if _treasure_chest_item:
        Misc.UseContextMenu(_treasure_chest_item.Serial, "Remove Chest", 1000)
        Misc.Pause(1000)
    _clear_selected_treasure()
    _update_gump()

def _handle_decoding():
    global _state
    _update_gump()
    Journal.Clear()
    Misc.UseContextMenu(_selected_map_serial, "Decode Map", 1000)
    Misc.Pause(2000)
    if Journal.Search("You successfully decode a treasure map!"):
        _hunt_decoded_map()

def _handle_hunting():
    _highlight_runebook()
    if not _selected_map_props: return
    try: cur_facet = FACET_NAMES[Player.Map]
    except: cur_facet = None
    if cur_facet == _selected_map_props[1]:
        _setup_map_and_tracking()
        _check_dig_distance_hint()

def _handle_digging():
    global _treasure_chest_item, _state
    try:
        _treasure_chest_item = Items.FindByID(TREASURE_CHEST_ITEMIDS, -1, -1, 4)
    except:
        _treasure_chest_item = None
        for iid in TREASURE_CHEST_ITEMIDS:
            c = Items.FindByID(iid, -1, -1, 4)
            if c: _treasure_chest_item = c; break
    if not _treasure_chest_item or Player.Paralized: return
    Player.HeadMessage(MSG_COLOR_OK, "Chest dug!!")
    _state = STATE_DUG
    _update_gump()

def _handle_picking():
    global _state
    lockpicks = Items.FindByID(LOCKPICK_ITEMID, -1, Player.Backpack.Serial, 1)
    if not lockpicks or not _treasure_chest_item: return
    Journal.Clear()
    Items.UseItem(lockpicks)
    Target.WaitForTarget(5000, True)
    Target.TargetExecute(_treasure_chest_item)
    Misc.Pause(2000)
    if Journal.Search("The lock quickly yields to your skill."):
        _state = STATE_REMOVING_TRAP
        _update_gump()

def _handle_remove_trap():
    global _state
    if not _treasure_chest_item: return
    Player.UseSkill("Remove Trap", _treasure_chest_item)
    Misc.Pause(2000)
    if Journal.Search("You successfully disarm the trap!"):
        _state = STATE_OPENED
        _update_gump()

# GUMP
def _update_gump():
    body_h = STYLE_HEADER_H + STYLE_STATUS_H + STYLE_ACTION_H + (STYLE_ROW_PAD * 4)

    Gumps.CloseGump(GUMP_ID)
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)

    Gumps.AddBackground(gd, 0, 0, GUMP_WIDTH, body_h, STYLE_BG_GFX)
    Gumps.AddAlphaRegion(gd, 0, 0, GUMP_WIDTH, body_h)

    cursor_x = STYLE_ROW_PAD
    cursor_y = STYLE_ROW_PAD

    Gumps.AddLabel(gd, cursor_x, cursor_y + 2, TITLE_COLOR,
                   "ETH Frog Python Fork v{}".format(VERSION))
    Gumps.AddImageTiled(gd, STYLE_ROW_PAD, cursor_y + STYLE_HEADER_H - 6,
                        GUMP_WIDTH - (STYLE_ROW_PAD * 2), 1, STYLE_DIVIDER_GFX)
    cursor_y += STYLE_HEADER_H

    status_text, status_color = "Status: Idle", STATUS_COLOR_IDLE
    if _state == STATE_DECODING:
        status_text, status_color = "Status: Decoding map...", STATUS_COLOR_ACTIVE
    elif _state == STATE_HUNTING:
        if _selected_map_props:
            lvl, fac, x, y = _selected_map_props
            status_text = "Status: Hunting {} in {} ({}, {})".format(lvl, fac, x, y)
        else:
            status_text = "Status: Hunting..."
        status_color = STATUS_COLOR_ACTIVE
    elif _state == STATE_DIGGING:
        status_text, status_color = "Status: Digging...", STATUS_COLOR_ACTIVE
    elif _state == STATE_DUG:
        status_text, status_color = "Status: Dug", STATUS_COLOR_ACTIVE
    elif _state == STATE_PICKING:
        status_text, status_color = "Status: Picking chest...", STATUS_COLOR_ACTIVE
    elif _state == STATE_REMOVING_TRAP:
        status_text, status_color = "Status: Removing trap...", STATUS_COLOR_ACTIVE
    elif _state == STATE_OPENED:
        status_text, status_color = "Status: Opened", STATUS_COLOR_ACTIVE

    pill_x = cursor_x
    pill_w = GUMP_WIDTH - (STYLE_ROW_PAD * 2)
    pill_h = STYLE_STATUS_H - 6
    Gumps.AddImageTiled(gd, pill_x, cursor_y + 2, pill_w, pill_h, STYLE_DIVIDER_GFX)
    Gumps.AddImageTiled(gd, pill_x, cursor_y + 2, pill_w, pill_h, STYLE_BAR_GFX)
    Gumps.AddLabel(gd, pill_x + 8, cursor_y + 3, status_color, status_text)
    cursor_y += STYLE_STATUS_H


    Gumps.AddImageTiled(gd, STYLE_ROW_PAD, cursor_y - 3,
                        GUMP_WIDTH - (STYLE_ROW_PAD * 2), 1, STYLE_DIVIDER_GFX)

    cursor_y += STYLE_ROW_PAD
    bx = cursor_x
    by = cursor_y

    if _state == STATE_IDLE:
        Gumps.AddButton(gd, bx, by, HUNT_BUTTON_GFX, HUNT_BUTTON_GFX, BTN_HUNT, 1, 0)
        Gumps.AddLabel(gd, bx + 18, by + 2, HUNT_BUTTON_LABEL_COLOR, "Hunt!")
    elif _state == STATE_HUNTING:
        Gumps.AddButton(gd, bx, by, HUNT_BUTTON_GFX, HUNT_BUTTON_GFX, BTN_DIG, 1, 0)
        Gumps.AddLabel(gd, bx + 18, by + 2, HUNT_BUTTON_LABEL_COLOR, "Dig!")
    elif _state == STATE_DUG:
        Gumps.AddButton(gd, bx, by, HUNT_BUTTON_GFX, HUNT_BUTTON_GFX, BTN_OPEN, 1, 0)
        Gumps.AddLabel(gd, bx + 18, by + 2, HUNT_BUTTON_LABEL_COLOR, "Open!")
    elif _state == STATE_OPENED:
        Gumps.AddButton(gd, bx, by, HUNT_BUTTON_GFX, HUNT_BUTTON_GFX, BTN_CLEANUP, 1, 0)
        Gumps.AddLabel(gd, bx + 6, by + 2, HUNT_BUTTON_LABEL_COLOR, "Clean Up!")

    if _state != STATE_IDLE:
        cx = GUMP_WIDTH - STYLE_ROW_PAD - 84
        Gumps.AddButton(gd, cx, by, HUNT_BUTTON_GFX, HUNT_BUTTON_GFX, BTN_CANCEL, 1, 0)
        Gumps.AddLabel(gd, cx + 14, by + 2, HUNT_BUTTON_LABEL_COLOR, "Cancel")

    Gumps.SendGump(GUMP_ID, Player.Serial, 150, 150, gd.gumpDefinition, gd.gumpStrings)


def main():
    global _state, _selected_map_serial

    _reset_all_book_hues()      
    _clear_selected_treasure()
    _update_gump()

    try:
        while True:
            if Gumps.WaitForGump(GUMP_ID, 50):
                gd = Gumps.GetGumpData(GUMP_ID)
                btn = getattr(gd, "buttonid", 0) if gd else 0

                if btn == BTN_HUNT:
                    Player.HeadMessage(MSG_COLOR_PROMPT, "Target a treasure map to start your hunt")
                    _selected_map_serial = Target.PromptTarget("Target a treasure map!")
                    tgt = Items.FindBySerial(_selected_map_serial)
                    if not tgt or tgt.ItemID != TREASURE_MAP_ITEMID:
                        Player.HeadMessage(MSG_COLOR_ERR, "Please target a map")
                        _clear_selected_treasure()
                        _update_gump()
                    elif tgt.Container != Player.Backpack.Serial:
                        Player.HeadMessage(MSG_COLOR_ERR, "The map needs to be in your backpack!")
                        _clear_selected_treasure()
                        _update_gump()
                    else:
                        Items.WaitForProps(tgt, 1000)
                        prop_lines = [str(s) for s in Items.GetPropStringList(tgt)]
                        if len(prop_lines) < 4:
                            if Player.GetSkillValue("Cartography") >= 100:
                                _state = STATE_DECODING
                            else:
                                Player.HeadMessage(MSG_COLOR_ERR, "You need to decode this first!")
                                _clear_selected_treasure()
                                _state = STATE_IDLE
                            _update_gump()
                        else:
                            _hunt_decoded_map()

                elif btn == BTN_DIG:
                    _dig_treasure(); _update_gump()

                elif btn == BTN_OPEN:
                    _open_chest(); _update_gump()

                elif btn == BTN_CLEANUP:
                    _clean_chest()  

                elif btn == BTN_CANCEL or btn == BTN_CLOSE:
                    _clear_selected_treasure()
                    _update_gump()
                    continue

            if   _state == STATE_DECODING:       _handle_decoding()
            elif _state == STATE_HUNTING:        _handle_hunting()
            elif _state == STATE_DIGGING:        _handle_digging()
            elif _state == STATE_PICKING:        _handle_picking()
            elif _state == STATE_REMOVING_TRAP:  _handle_remove_trap()

            _maintain_highlight()

            Misc.Pause(100)

    except Exception as ex:
        Misc.SendMessage(str(ex), MSG_COLOR_ERR)
    finally:
        try: Player.TrackingArrow(0, 0, False)
        except: pass
        _clear_highlight()

if __name__ == "__main__":
    main()
