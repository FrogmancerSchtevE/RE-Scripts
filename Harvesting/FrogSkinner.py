# =============================================
# === FrogSkinner (Razor Enhanced Script) ===
# =============================================
# Copyright (c) Frogmancer Schteve. All rights reserved except as
# expressly permitted by the repository License.md.
#
# PERSONAL USE
# This script is provided for personal, non-commercial use.
# You may use, study, and modify it for your own use. Redistribution,
# resale, sublicensing, or incorporation into another distributed
# project is not permitted without prior permission.
#
# AI / LLM RESTRICTION
# Do NOT upload, submit, ingest, or otherwise provide this script,
# in whole or substantial part, to Large Language Models (LLMs),
# generative AI systems, AI coding assistants, machine-learning
# datasets, training/fine-tuning pipelines, retrieval systems, or
# automated code-generation systems.
#
# If you encounter a bug or compatibility issue, please submit an
# issue through the repository or contact Frogmancer Schteve directly
# rather than submitting the script to an AI service for troubleshooting.
#
# SHARD RULES
# You are responsible for ensuring your use of this script complies
# with the rules of the Ultima Online shard on which you play.
#
# This notice is only a summary. The repository License.md contains
# the complete terms governing use of this software.
#
# Use it. Learn from it. Improve it.
# Just don't feed the frogs to the robots.
# ====================================================================

import Gumps, Items, Misc, Player, Target, time
from System import Int32
from System.Collections.Generic import List

# ===========================================================
# USER SETTINGS
# ===========================================================

# Edit these if you want to scan/harvest further away, 2 or 3 works fine, more than that and it don't work so great.
SCAN_RANGE = 2
SCAVENGE_RANGE = 1  

SCALED_HIDE_IDS = []
SCALED_LEATHER_IDS = []

# ===========================================================
# CONFIGURATION
# ===========================================================

GUMP_ID = 0xF2064653
GUMP_X, GUMP_Y = 700, 500
FROG_ICON = 0x2130
FROG_HUE = 1152
LOOP_MS = 100
SCAN_MS = 650
ACTION_MS = 550
TARGET_TIMEOUT_MS = 1100
CUT_ACTION_MS = 950
CUT_TARGET_TIMEOUT_MS = 1800
CORPSE_READY_MS = 650

HIDE_ID = 0x1079
LEATHER_ID = 0x1081
SCISSORS_ID = 0x0F9F
SKINNED_CORPSE_HUE = 2466

HUES = {
    0x0000: "Regular",
    0x0283: "Spined",
    0x0227: "Horned",
    0x01C1: "Barbed",
    0x0829: "Scaled",
}

KEY_BLADE = "frogSkinnerBlade"
KEY_BAG = "frogSkinnerBag"
KEY_CRYSTAL = "frogSkinnerCrystalScissors"

BTN_CARVE = 1001
BTN_SETTINGS = 1002
BTN_BACK = 1003
BTN_CLOSE = 1004
BTN_BLADE = 1010
BTN_BAG = 1011
BTN_CRYSTAL = 1012
BTN_CLEAR_BAG = 1013
BTN_AUTO_CARVE = 1020
BTN_AUTO_CONVERT = 1021
BTN_USE_CRYSTAL = 1022
BTN_HARVESTER = 1023
BTN_DROP = 1024
BTN_KEEP_BASE = 1030

TIERS = ("Regular", "Spined", "Horned", "Barbed", "Scaled")

# ===========================================================
# STATE
# ===========================================================

_running = True
_page = 0
_dirty = True
_status = "Ready"


def load_bool(key, default):
    return bool(Misc.ReadSharedValue(key)) if Misc.CheckSharedValue(key) else default


_auto_carve = load_bool("frogSkinnerAutoCarve", False)
_auto_convert = load_bool("frogSkinnerAutoConvert", True)
_use_crystal = load_bool("frogSkinnerUseCrystal", False)
_harvester = load_bool("frogSkinnerHarvester", False)
_drop_at_feet = load_bool("frogSkinnerDrop", False)
_keep = dict((name, load_bool("frogSkinnerKeep" + name, True)) for name in TIERS)

_blade = int(Misc.ReadSharedValue(KEY_BLADE) or 0) if Misc.CheckSharedValue(KEY_BLADE) else 0
_bag = int(Misc.ReadSharedValue(KEY_BAG) or 0) if Misc.CheckSharedValue(KEY_BAG) else 0
_crystal = int(Misc.ReadSharedValue(KEY_CRYSTAL) or 0) if Misc.CheckSharedValue(KEY_CRYSTAL) else 0
_plain_scissors = 0

_corpse_filter = Items.Filter()
_corpse_filter.Enabled = True
_corpse_filter.IsCorpse = True
_corpse_filter.OnGround = True
_corpse_filter.RangeMax = SCAN_RANGE

_ground_filter = Items.Filter()
_ground_filter.Enabled = True
_ground_filter.OnGround = True
_ground_filter.RangeMax = SCAN_RANGE
_ground_graphics = List[Int32]()
for _art in set([HIDE_ID, LEATHER_ID] + SCALED_HIDE_IDS + SCALED_LEATHER_IDS):
    _ground_graphics.Add(Int32(_art))
_ground_filter.Graphics = _ground_graphics

_corpses = []
_resources = []
_seen_at = {}
_carved = set()
_opened = set()
_cut_at = {}
_moved_at = {}
_dropped = set()
_last_scan = 0
_last_resource_check = 0
_next_action = 0
_pending = None
_move_verify = None
_manual_carve = False
_status_dirty = False
_last_render = 0

# ===========================================================
# HELPERS
# ===========================================================

def set_status(message):
    global _status, _status_dirty
    if _status != message:
        _status = message
        _status_dirty = True


def item_kind(item):
    if not item:
        return None
    art = int(item.ItemID)
    if art == HIDE_ID or art in SCALED_HIDE_IDS:
        return "hide"
    if art == LEATHER_ID or art in SCALED_LEATHER_IDS:
        return "leather"
    name = (item.Name or "").lower()
    if name == "hide" or name == "hides" or name.endswith(" hide") or name.endswith(" hides"):
        return "hide"
    if name == "leather" or name.endswith(" leather"):
        return "leather"
    return None


def item_tier(item):
    tier = HUES.get(int(item.Hue))
    if tier:
        return tier
    name = (item.Name or "").lower()
    for tier in ("Scaled", "Barbed", "Horned", "Spined"):
        if tier.lower() in name:
            return tier
    return None


def selected_scissors():
    global _plain_scissors
    if _use_crystal:
        return Items.FindBySerial(_crystal) if _crystal else None
    if _plain_scissors:
        scissors = Items.FindBySerial(_plain_scissors)
        if scissors and int(scissors.ItemID) == SCISSORS_ID:
            return scissors
        _plain_scissors = 0
    scissors = Items.FindByID(SCISSORS_ID, -1, Player.Backpack.Serial, True)
    if scissors:
        _plain_scissors = int(scissors.Serial)
    return scissors


def select_item(key, label):
    global _blade, _bag, _crystal
    serial = Target.PromptTarget("Target " + label, 0x3B2)
    if serial <= 0:
        set_status("Selection cancelled")
        return
    if key != KEY_BAG and not Items.FindBySerial(serial):
        set_status(label + " unavailable")
        return
    if key == KEY_BLADE:
        _blade = serial
    elif key == KEY_BAG:
        _bag = serial
    else:
        _crystal = serial
    Misc.SetSharedValue(key, serial)
    set_status(label + " set")


def scan(now):
    global _corpses, _resources, _last_scan
    if now - _last_scan < SCAN_MS / 1000.0:
        return
    _last_scan = now
    _corpses = list(Items.ApplyFilter(_corpse_filter) or [])
    nearby = set(int(c.Serial) for c in _corpses)
    _carved.intersection_update(nearby)
    _opened.intersection_update(nearby)
    for serial in list(_seen_at):
        if serial not in nearby:
            del _seen_at[serial]
    for corpse in _corpses:
        _seen_at.setdefault(int(corpse.Serial), now)

    resources = []
    if _auto_convert or _harvester:
        for corpse in _corpses:
            resources.extend(list(corpse.Contains or []))
        resources.extend(list(Items.ApplyFilter(_ground_filter) or []))
        if Player.Backpack:
            resources.extend(list(Player.Backpack.Contains or []))
    _resources = resources

    visible = set(int(item.Serial) for item in resources)
    for memory in (_cut_at, _moved_at):
        for serial in list(memory):
            if serial not in visible:
                del memory[serial]
    _dropped.intersection_update(visible)


def start_target(kind, tool_serial, target_serial, now):
    global _pending, _next_action
    if not free_to_act(now):
        return False
    try:
        Items.UseItem(tool_serial)
    except:
        _next_action = now + 3.0
        set_status("Tool unavailable")
        return True
    timeout = CUT_TARGET_TIMEOUT_MS if kind == "cut" and not _use_crystal else TARGET_TIMEOUT_MS
    _pending = (kind, target_serial, now + timeout / 1000.0)
    _next_action = now + ACTION_MS / 1000.0
    return True


def free_to_act(now):
    return _pending is None and _move_verify is None and now >= _next_action and not Target.HasTarget()


def finish_target(now):
    global _pending, _manual_carve, _next_action
    if not _pending:
        return False
    kind, target, deadline = _pending
    if Target.HasTarget():
        if kind == "scavenge":
            Target.Self()
            for serial in target:
                _carved.add(serial)
                if Items.FindBySerial(serial):
                    try:
                        Items.SetColor(serial, SKINNED_CORPSE_HUE)
                    except:
                        pass
            _manual_carve = False
            set_status("Scavenged nearby corpses")
        else:
            hide = Items.FindBySerial(target)
            if not hide or item_kind(hide) != "hide":
                Target.Cancel()
                _pending = None
                _next_action = now + CUT_ACTION_MS / 1000.0
                set_status("Hide unavailable")
                return True
            try:
                Target.TargetExecute(hide)
            except:
                _pending = None
                _next_action = now + 3.0
                set_status("Target disappeared")
                return True
            _cut_at[target] = now
            set_status("Cut hide")
        _pending = None
        recovery = CUT_ACTION_MS if kind == "cut" and not _use_crystal else ACTION_MS
        _next_action = now + recovery / 1000.0
    elif now >= deadline:
        _pending = None
        _next_action = now + 3.0
        set_status("Tool target timed out")
    return True


def scavenge_step(now):
    global _manual_carve
    if not (_manual_carve or _auto_carve):
        return False
    close = [c for c in _corpses if Player.DistanceTo(c) <= SCAVENGE_RANGE]
    if not close:
        if _manual_carve:
            _manual_carve = False
            set_status("No corpses in scavenge range")
        return False
    blade = Items.FindBySerial(_blade) if _blade else None
    if not blade:
        if _manual_carve:
            _manual_carve = False
        set_status("Set a scavenging tool")
        return False
    ready = [c for c in close if int(c.Serial) not in _carved and now - _seen_at.get(int(c.Serial), now) >= CORPSE_READY_MS / 1000.0]
    if not ready:
        if _manual_carve and all(int(c.Serial) in _carved for c in close):
            _manual_carve = False
            set_status("Nearby corpses already scavenged")
        return False
    serials = [int(c.Serial) for c in ready]
    return start_target("scavenge", _blade, serials, now)


def resource_step(now):
    global _next_action, _move_verify, _bag
    if _move_verify:
        return False
    skipped_leather = None
    for item in _resources:
        if item_kind(item) != "leather":
            continue
        tier = item_tier(item)
        if not tier:
            skipped_leather = "Unknown leather hue {0:04X}".format(int(item.Hue))
            continue
        if not _keep[tier]:
            skipped_leather = tier + " leather excluded"
            continue
        serial = int(item.Serial)
        if now - _moved_at.get(serial, 0) < 2.0 or serial in _dropped:
            continue
        if _drop_at_feet:
            position = Player.Position
            try:
                Items.MoveOnGround(serial, 0, position.X, position.Y, position.Z)
            except:
                set_status("Could not drop leather")
                _next_action = now + 3.0
                return False
            _dropped.add(serial)
            set_status("Dropped leather at feet")
        else:
            destination = _bag or Player.Backpack.Serial
            if int(item.Container) == destination:
                continue
            source_container = int(item.Container)
            source_on_ground = bool(item.OnGround)
            try:
                Items.Move(serial, destination, -1)
            except:
                if destination != Player.Backpack.Serial:
                    try:
                        Items.Move(serial, Player.Backpack.Serial, -1)
                    except:
                        set_status("Could not move leather")
                        _next_action = now + 3.0
                        return False
                    destination = Player.Backpack.Serial
                    _bag = 0
                    Misc.SetSharedValue(KEY_BAG, 0)
                else:
                    set_status("Could not move leather")
                    _next_action = now + 3.0
                    return False
            _move_verify = (serial, destination, source_container, source_on_ground, now + 1.0)
            set_status("Moving leather to bag" if _bag else "Moving leather to backpack")
        _moved_at[serial] = now
        _next_action = now + ACTION_MS / 1000.0
        return True

    for item in _resources:
        if item_kind(item) != "hide" or not _auto_convert:
            continue
        serial = int(item.Serial)
        if now - _cut_at.get(serial, 0) < 3.0:
            continue
        scissors = selected_scissors()
        if not scissors:
            set_status("Set crystal scissors" if _use_crystal else "Scissors missing")
            return False
        return start_target("cut", int(scissors.Serial), serial, now)
    if skipped_leather:
        set_status(skipped_leather)
    return False


def verify_move_step(now):
    global _move_verify, _bag, _next_action
    if not _move_verify:
        return False
    serial, destination, source_container, source_on_ground, due = _move_verify
    if now < due:
        return False
    _move_verify = None
    item = Items.FindBySerial(serial)
    if not item or int(item.Container) == destination:
        set_status("Leather moved to bag" if _bag else "Leather moved to backpack")
        return False
    if int(item.Container) != source_container or bool(item.OnGround) != source_on_ground:
        set_status("Leather moved")
        return False
    if destination == Player.Backpack.Serial:
        _moved_at[serial] = now
        _next_action = now + 2.0
        set_status("Leather move failed; check range")
        return True
    try:
        Items.Move(serial, Player.Backpack.Serial, -1)
    except:
        set_status("Satchel and backpack move failed")
        _next_action = now + 3.0
        return True
    _bag = 0
    Misc.SetSharedValue(KEY_BAG, 0)
    _move_verify = (serial, Player.Backpack.Serial, source_container, source_on_ground, now + 1.0)
    _next_action = now + ACTION_MS / 1000.0
    set_status("Satchel failed; trying backpack")
    return True


def open_corpse_step(now):
    global _next_action
    if not (_auto_convert or _harvester):
        return False
    for corpse in _corpses:
        serial = int(corpse.Serial)
        if serial not in _carved or serial in _opened or corpse.Contains:
            continue
        try:
            Items.UseItem(serial)
        except:
            _next_action = now + 3.0
            return True
        _opened.add(serial)
        _next_action = now + ACTION_MS / 1000.0
        return True
    return False


def work_step(now):
    global _last_resource_check
    if finish_target(now):
        return
    if Target.HasTarget():
        return
    if verify_move_step(now):
        return
    if not free_to_act(now):
        return
    scan(now)
    if scavenge_step(now):
        return
    if not free_to_act(now):
        return
    if free_to_act(now) and (_auto_convert or _harvester) and now - _last_resource_check >= 0.5:
        _last_resource_check = now
        if resource_step(now):
            return
    if free_to_act(now):
        open_corpse_step(now)

# ===========================================================
# GUI
# ===========================================================

def toggle_label(gd, y, button, text, enabled):
    Gumps.AddButton(gd, 18, y, 4005, 4007, button, 1, 0)
    Gumps.AddLabel(gd, 50, y, 68 if enabled else 33, text + (" ON" if enabled else " OFF"))


def render_gui():
    global _dirty, _status_dirty, _last_render
    Gumps.CloseGump(GUMP_ID)
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)
    width, height = (280, 123) if _page == 0 else (320, 362)
    Gumps.AddBackground(gd, 0, 0, width, height, 5054)
    Gumps.AddAlphaRegion(gd, 0, 0, width, height)
    Gumps.AddItem(gd, 5, 5, FROG_ICON, FROG_HUE)
    Gumps.AddLabel(gd, 42, 9, 0x480, "FrogSkinner")
    Gumps.AddButton(gd, width - 40, 8, 4017, 4019, BTN_CLOSE, 1, 0)

    if _page == 0:
        Gumps.AddLabel(gd, 14, 30, 0x47E, _status[:31])
        Gumps.AddButton(gd, 14, 53, 4011, 4013, BTN_CARVE, 1, 0)
        Gumps.AddLabel(gd, 46, 53, 68, "Scavenge")
        Gumps.AddButton(gd, 166, 53, 4005, 4007, BTN_SETTINGS, 1, 0)
        Gumps.AddLabel(gd, 198, 53, 0x480, "Settings")
        Gumps.AddLabel(gd, 14, 82, 0x44E, "Auto Scavenge: " + ("ON" if _auto_carve else "OFF"))
        Gumps.AddLabel(gd, 164, 82, 0x44E, "Convert: " + ("ON" if _auto_convert else "OFF"))
        Gumps.AddLabel(gd, 14, 101, 0x44E, "Loot: " + ("Ground" if _drop_at_feet else "Satchel" if _bag else "Backpack"))
    else:
        Gumps.AddLabel(gd, 20, 36, 0x47E, "Automation")
        toggle_label(gd, 58, BTN_AUTO_CARVE, "Auto Scavenge", _auto_carve)
        toggle_label(gd, 80, BTN_AUTO_CONVERT, "Auto Convert Hides", _auto_convert)
        toggle_label(gd, 102, BTN_USE_CRYSTAL, "Crystal Scissors", _use_crystal)
        toggle_label(gd, 124, BTN_HARVESTER, "Harvester's Blade", _harvester)
        toggle_label(gd, 146, BTN_DROP, "Drop at Feet", _drop_at_feet)

        Gumps.AddLabel(gd, 20, 176, 0x47E, "Keep Leather")
        for index, tier in enumerate(TIERS):
            col = index % 2
            row = index // 2
            x, y = 18 + col * 150, 198 + row * 22
            Gumps.AddButton(gd, x, y, 4005, 4007, BTN_KEEP_BASE + index, 1, 0)
            Gumps.AddLabel(gd, x + 32, y, 68 if _keep[tier] else 33, tier + (" ON" if _keep[tier] else " OFF"))

        Gumps.AddButton(gd, 18, 271, 4005, 4007, BTN_BLADE, 1, 0)
        Gumps.AddLabel(gd, 50, 271, 0x44E, "Set Tool" + (" *" if _blade else ""))
        Gumps.AddButton(gd, 160, 271, 4005, 4007, BTN_BAG, 1, 0)
        Gumps.AddLabel(gd, 192, 271, 0x44E, "Set Loot Bag" + (" *" if _bag else ""))
        Gumps.AddButton(gd, 18, 293, 4005, 4007, BTN_CRYSTAL, 1, 0)
        Gumps.AddLabel(gd, 50, 293, 0x44E, "Set Crystal Scissors" + (" *" if _crystal else ""))
        Gumps.AddButton(gd, 18, 316, 4014, 4015, BTN_BACK, 1, 0)
        Gumps.AddLabel(gd, 50, 316, 0x480, "Back")
        Gumps.AddButton(gd, 160, 316, 4005, 4007, BTN_CLEAR_BAG, 1, 0)
        Gumps.AddLabel(gd, 192, 316, 0x44E, "Use Backpack")

    Gumps.SendGump(GUMP_ID, Player.Serial, GUMP_X, GUMP_Y, gd.gumpDefinition, gd.gumpStrings)
    _dirty = False
    _status_dirty = False
    _last_render = time.time()


def handle_button(button):
    global _running, _page, _dirty, _manual_carve, _bag, _last_scan, _move_verify
    global _auto_carve, _auto_convert, _use_crystal, _harvester, _drop_at_feet
    if button == BTN_CLOSE:
        _running = False
    elif button == BTN_SETTINGS:
        _page = 1
    elif button == BTN_BACK:
        _page = 0
    elif button == BTN_CARVE:
        _manual_carve = True
        _carved.clear()
        _last_scan = 0
        set_status("Scavenging nearby corpses")
    elif button == BTN_BLADE:
        select_item(KEY_BLADE, "skinning knife or dagger")
    elif button == BTN_BAG:
        _move_verify = None
        select_item(KEY_BAG, "loot bag or worn satchel")
    elif button == BTN_CLEAR_BAG:
        _move_verify = None
        _bag = 0
        Misc.SetSharedValue(KEY_BAG, 0)
        set_status("Using backpack")
    elif button == BTN_CRYSTAL:
        select_item(KEY_CRYSTAL, "crystal scissors")
    elif button == BTN_AUTO_CARVE:
        _auto_carve = not _auto_carve
        Misc.SetSharedValue("frogSkinnerAutoCarve", _auto_carve)
    elif button == BTN_AUTO_CONVERT:
        _auto_convert = not _auto_convert
        Misc.SetSharedValue("frogSkinnerAutoConvert", _auto_convert)
    elif button == BTN_USE_CRYSTAL:
        _use_crystal = not _use_crystal
        Misc.SetSharedValue("frogSkinnerUseCrystal", _use_crystal)
    elif button == BTN_HARVESTER:
        _harvester = not _harvester
        Misc.SetSharedValue("frogSkinnerHarvester", _harvester)
    elif button == BTN_DROP:
        _move_verify = None
        _drop_at_feet = not _drop_at_feet
        Misc.SetSharedValue("frogSkinnerDrop", _drop_at_feet)
    elif BTN_KEEP_BASE <= button < BTN_KEEP_BASE + len(TIERS):
        tier = TIERS[button - BTN_KEEP_BASE]
        _keep[tier] = not _keep[tier]
        Misc.SetSharedValue("frogSkinnerKeep" + tier, _keep[tier])
    _dirty = True


def main():
    global _running
    Gumps.CloseGump(GUMP_ID)
    render_gui()
    while _running and Player.Connected:
        handled = False
        gd = Gumps.GetGumpData(GUMP_ID)
        button = int(getattr(gd, "buttonid", 0)) if gd else 0
        if button > 0:
            try:
                gd.buttonid = 0
            except:
                pass
            Gumps.CloseGump(GUMP_ID)
            handle_button(button)
            handled = True
        if not _running:
            break
        if not handled:
            work_step(time.time())
            if _dirty or (_status_dirty and time.time() - _last_render >= 2.0) or Gumps.GetGumpData(GUMP_ID) is None:
                render_gui()
        Misc.Pause(LOOP_MS)
    Gumps.CloseGump(GUMP_ID)


main()
