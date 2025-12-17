# Frogmancers Item Logger (RE Inspect)

import os, json

GUMP_ID = 0x6EDC0A11
GUMP_X, GUMP_Y = 300, 300
FILE_NAME = "item_log.json" # You can change this but be sure to end it in .json
MSG = 92
PAUSE_MS = 75
BTN_START = 1100
BTN_SET   = 1101
BTN_CLOSE = 1199
SHARED_HEADER = "RE Inspect Logger"

def _data_dir():
    base = Misc.CurrentScriptDirectory()
    p = os.path.join(base, "data")
    if not os.path.isdir(p):
        os.makedirs(p)
    return p

def _file_path():
    return os.path.join(_data_dir(), FILE_NAME)

def _load_db():
    try:
        with open(_file_path(), "r", encoding="utf-8") as f:
            d = json.load(f)
            if isinstance(d, dict) and "groups" in d:
                return d
    except:
        pass
    return {"groups": {}}

def _save_db(db):
    tmp = _file_path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4)
    try: os.remove(_file_path())
    except: pass
    os.rename(tmp, _file_path())

def _hex4(n):
    try: return "0x%04X" % (int(n) & 0xFFFF)
    except: return "0x0000"

def _item_name(itm):
    try:
        Items.WaitForProps(itm, 1000)
        props = Items.GetPropStringList(itm)
        if props and len(props) > 0:
            return str(props[0])
    except: pass
    return itm.Name or "Unknown"

def _props_list(itm):
    try:
        Items.WaitForProps(itm, 1000)
        lst = Items.GetPropStringList(itm)
        return [str(p) for p in (lst or [])]
    except:
        return []

def _log_item(header, itm):
    entry = {
        "name": _item_name(itm),
        "serial": int(itm.Serial),
        "itemID": _hex4(itm.ItemID),
        "hue": _hex4(itm.Hue),
        "properties": _props_list(itm)
    }
    db = _load_db()
    db["groups"].setdefault(header, []).append(entry)
    _save_db(db)
    Misc.SendMessage("Logged: %s → [%s] (%s, %s)"
                     % (entry["name"], header, entry["itemID"], entry["hue"]), MSG)

def _player_lines():
    try:
        lines = Journal.GetTextBySerial(Player.Serial, False) or []
        return [str(x) for x in lines]
    except:
        out = []
        try:
            entries = Journal.GetJournalEntry(0) or []
            for je in entries:
                if getattr(je, "Serial", 0) == Player.Serial:
                    out.append(str(getattr(je, "Text", "") or ""))
        except:
            pass
        return out

def _prompt_header_from_chat(timeout_ms=15000):

    before = len(_player_lines())
    Misc.SendMessage("Type your HEADER in chat now or ESC to cancel", 88)
    ticks = max(1, int(timeout_ms / 100))
    for _ in range(ticks):
        lines = _player_lines()
        n = len(lines)
        if n > before:
            try:
                candidate = (lines[before] or "").strip()  
            except:
                candidate = (lines[n - 1] if n > 0 else "").strip()
            if candidate.lower() == "cancel":
                Misc.SendMessage("Header entry cancelled.", 53)
                return None
            if candidate:
                return candidate
        Misc.Pause(100)
    Misc.SendMessage("No input detected. Retaining previous header", 53)
    return None

def _read_header():
    try:
        if Misc.CheckSharedValue(SHARED_HEADER):
            v = Misc.ReadSharedValue(SHARED_HEADER)
            if isinstance(v, str): return v
    except: pass
    return ""

def _set_header(h):
    h = (h or "").strip()
    if not h: return None
    Misc.SetSharedValue(SHARED_HEADER, h)
    Misc.SendMessage("Header set to: %s" % h, 88)
    return h

def _open_ui(current_header):
    Gumps.CloseGump(GUMP_ID)
    gd = Gumps.CreateGump(movable=True); Gumps.AddPage(gd, 0)
    W, H = 300, 120
    Gumps.AddBackground(gd, 0, 0, W, H, 30546)
    Gumps.AddAlphaRegion(gd, 0, 0, W, H)

    Gumps.AddHtml(gd, 10, 10, W-20, 18,
        "<center><basefont color=#FFFFFF>Fast RE Inspect Logger</basefont></center>", 0, 0)

    disp = current_header or "<i>none</i>"
    Gumps.AddHtml(gd, 14, 38, W-28, 18,
        f"<basefont color=#CCCCCC>Header:</basefont> <basefont color=#FFFFFF><b>{disp}</b></basefont>", 0, 0)

    Gumps.AddButton(gd, 14, 70, 4006, 4007, BTN_SET, 1, 0)
    Gumps.AddHtml(gd, 42, 68, 100, 18, "<basefont color=#E0E0FF>Set Header</basefont>", 0, 0)

    Gumps.AddButton(gd, 150, 70, 4005, 4006, BTN_START, 1, 0)
    Gumps.AddHtml(gd, 178, 68, 100, 18, "<basefont color=#80FF80>Start</basefont>", 0, 0)

    Gumps.AddButton(gd, W-25, 5, 4017, 4018, BTN_CLOSE, 1, 0)
    Gumps.SendGump(GUMP_ID, Player.Serial, GUMP_X, GUMP_Y, gd.gumpDefinition, gd.gumpStrings)

def _get_button():
    if not Gumps.WaitForGump(GUMP_ID, 30):
        return 0
    gd = Gumps.GetGumpData(GUMP_ID)
    return getattr(gd, "buttonid", 0) if gd else 0

def _target_loop(header):
    if not header:
        header = "Uncategorized"
    Misc.SendMessage("Target items for header [%s]. Press Esc to stop." % header, MSG)
    while True:
        serial = Target.PromptTarget("Target an item to log [Esc to cancel]")
        if serial is None or int(serial) < 0:
            Misc.SendMessage("Logging stopped.", 53)
            break
        itm = Items.FindBySerial(int(serial))
        if not itm:
            Misc.SendMessage("Could not resolve item (out of range/invalid).", 33)
        else:
            _log_item(header, itm)
        Misc.Pause(PAUSE_MS)

def main():
    _ = _data_dir()
    if not os.path.exists(_file_path()):
        _save_db({"groups": {}})

    current_header = _read_header()
    _open_ui(current_header)

    while Player.Connected:
        Misc.Pause(50)
        bid = _get_button()
        if bid == 0: 
            continue
        if bid == BTN_CLOSE:
            Gumps.CloseGump(GUMP_ID)
            break
        if bid == BTN_SET:
            newh = _prompt_header_from_chat(15000)  
            if newh:
                current_header = _set_header(newh) or current_header
            _open_ui(current_header)
        if bid == BTN_START:
            header = current_header
            if not header:
                newh = _prompt_header_from_chat(15000)
                if newh:
                    header = _set_header(newh) or header
                else:
                    header = "Uncategorized"
                    Misc.SetSharedValue(SHARED_HEADER, header)
            Gumps.CloseGump(GUMP_ID)
            _target_loop(header)
            _open_ui(_read_header())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        Misc.SendMessage("[FastInspect] Error: %s" % e, 33)
