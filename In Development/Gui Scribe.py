# ================================================================
# FrogScribe Suite v2 – Inscription GUI (Craft / Craft&Fill / Fill)
# Author: Frog + UO Script Forge
#
# Features:
#   * Suite-style GUI:
#       - Header, Status, Progress bar
#       - Resource chest + Deposit chest display and set buttons
#       - Master "Runs" control with your 2223/2224 +/- buttons
#       - Mode toggle: Craft / Craft&Fill / Fill
#       - Craft All Circles + individual 1st–8th circle buttons
#       - Fill Spellbooks button (uses deposit chest scrolls & blanks)
#
#   * Auto-restock:
#       - Reagents, blank scrolls, pens from Resource chest into backpack
#
#   * Crafting:
#       - Uses original Frogscribe circle gump/button IDs & scroll IDs
#       - Requires you to hold a full spellbook (for inscription ability)
#       - Crafts scrolls into backpack, then moves them to Deposit chest
#       - Success/failure detected via scroll count delta
#
#   * Filling:
#       - Deposit chest holds:
#           * crafted scrolls
#           * blank spellbooks (0x0EFA)
#       - Script:
#           * Moves a blank spellbook to backpack
#           * Uses scrolls from Deposit chest to add up to 64 spells
#           * Deposits filled book back into Deposit chest
#           * Repeats until no blanks or no scrolls left
#
# Notes:
#   * All status feedback is via the GUMP status line, not system messages.
#   * "Craft" mode: just crafts, deposits scrolls.
#   * "Craft&Fill" mode: crafts, deposits scrolls, then fills books.
#   * "Fill" mode: skips crafting; just fills books from deposit chest.
# ================================================================

import Misc, Gumps, Items, Player, Target
from System.Collections.Generic import List

# ------------------------------------------------
# CONFIG / CONSTANTS
# ------------------------------------------------

GUI_GUMP_ID = 0x0F0A0001       # Custom GUI gump id
SCRIBE_PEN_ID = 0x0FBF         # Scribe pen graphic
SPELLBOOK_ID = 0x0EFA          # Standard spellbook itemID

MIN_ITERATIONS = 1
MAX_ITERATIONS = 10
MAX_ATTEMPTS_PER_SCROLL = 15   # retry limit per scroll

GUMP_WIDTH = 300
GUMP_HEIGHT = 400


HEADER_HUE = 1152
LABEL_HUE = 11          # per your change
VALUE_HUE = 53
BUTTON_LABEL_HUE = 54
STATUS_HUE = 67

# Buttons
BTN_SET_RESOURCE   = 100
BTN_SET_DEPOSIT    = 101

BTN_ITER_MINUS     = 110
BTN_ITER_PLUS      = 111

BTN_MODE_TOGGLE    = 120
BTN_FILL_BOOKS     = 121

BTN_CRAFT_ALL      = 130
BTN_CRAFT_C1       = 131
BTN_CRAFT_C2       = 132
BTN_CRAFT_C3       = 133
BTN_CRAFT_C4       = 134
BTN_CRAFT_C5       = 135
BTN_CRAFT_C6       = 136
BTN_CRAFT_C7       = 137
BTN_CRAFT_C8       = 138

BTN_STOP           = 190
BTN_CLOSE          = 199

MODES = ["craft", "craftfill", "fill"]

# ------------------------------------------------
# GLOBAL STATE
# ------------------------------------------------

STATE = {
    "iterations": 1,
    "status": "Idle.",
    "progress": 0.0,          # 0.0–1.0
    "resource_chest": None,
    "deposit_chest": None,
    "mode": "craft",
    "current_circle": 0,
    "current_run": 0,
    "total_steps": 1,
    "completed_steps": 0,
    "restock_state": "Ready",
    "abort": False,
}

SCRIBE_GUMP_ID = None   # inscription gump id, discovered dynamically

# ------------------------------------------------
# CIRCLE / SPELL DEFINITIONS (from Frogscribe)
# ------------------------------------------------

CIRCLE_DATA = {
    1: {
        "category_action": 1,
        "spell_actions": [2, 9, 16, 23, 30, 37, 44, 51],
        "scroll_ids":    [0x1F2E, 0x1F2F, 0x1F30, 0x1F31,
                          0x1F32, 0x1F33, 0x1F2D, 0x1F34],
    },
    2: {
        "category_action": 1,
        "spell_actions": [58, 65, 72, 79, 86, 93, 100, 107],
        "scroll_ids":    [0x1F35, 0x1F36, 0x1F37, 0x1F38,
                          0x1F39, 0x1F3A, 0x1F3B, 0x1F3C],
    },
    3: {
        "category_action": 8,
        "spell_actions": [2, 9, 16, 23, 30, 37, 44, 51],
        "scroll_ids":    [0x1F3D, 0x1F3E, 0x1F3F, 0x1F40,
                          0x1F41, 0x1F42, 0x1F43, 0x1F44],
    },
    4: {
        "category_action": 8,
        "spell_actions": [58, 65, 72, 79, 86, 93, 100, 107],
        "scroll_ids":    [0x1F45, 0x1F46, 0x1F47, 0x1F48,
                          0x1F49, 0x1F4A, 0x1F4B, 0x1F4C],
    },
    5: {
        "category_action": 15,
        "spell_actions": [2, 9, 16, 23, 30, 37, 44, 51],
        "scroll_ids":    [0x1F4D, 0x1F4E, 0x1F4F, 0x1F50,
                          0x1F51, 0x1F52, 0x1F53, 0x1F54],
    },
    6: {
        "category_action": 15,
        "spell_actions": [58, 65, 72, 79, 86, 93, 100, 107],
        "scroll_ids":    [0x1F55, 0x1F56, 0x1F57, 0x1F58,
                          0x1F59, 0x1F5A, 0x1F5B, 0x1F5C],
    },
    7: {
        "category_action": 22,
        "spell_actions": [2, 9, 16, 23, 30, 37, 44, 51],
        "scroll_ids":    [0x1F5D, 0x1F5E, 0x1F5F, 0x1F60,
                          0x1F61, 0x1F62, 0x1F63, 0x1F64],
    },
    8: {
        "category_action": 22,
        "spell_actions": [58, 65, 72, 79, 86, 93, 100, 107],
        "scroll_ids":    [0x1F65, 0x1F66, 0x1F67, 0x1F68,
                          0x1F69, 0x1F6A, 0x1F6B, 0x1F6C],
    },
}

# Flattened scroll id list for move/deposit routines
ALL_SCROLL_IDS = []
for cdata in CIRCLE_DATA.values():
    for sid in cdata["scroll_ids"]:
        if sid not in ALL_SCROLL_IDS:
            ALL_SCROLL_IDS.append(sid)

# ------------------------------------------------
# HELPERS: state / status / formatting
# ------------------------------------------------

def status_text(msg):
    STATE["status"] = str(msg)
    draw_gui()


def set_progress(current, total):
    if total <= 0:
        STATE["progress"] = 0.0
    else:
        STATE["progress"] = float(current) / float(total)
    STATE["completed_steps"] = current
    STATE["total_steps"] = total
    draw_gui()


def serial_to_str(serial):
    if not serial:
        return "Not set"
    try:
        return "0x%X" % serial
    except:
        return str(serial)


def clamp_iterations():
    if STATE["iterations"] < MIN_ITERATIONS:
        STATE["iterations"] = MIN_ITERATIONS
    if STATE["iterations"] > MAX_ITERATIONS:
        STATE["iterations"] = MAX_ITERATIONS


def get_held_spellbook():
    """Return the spellbook item in left/right hand, if any."""
    for layer in ["LeftHand", "RightHand"]:
        item = Player.GetItemOnLayer(layer)
        if item and item.ItemID == SPELLBOOK_ID:
            return item
    return None


# ------------------------------------------------
# RESTOCK ROUTINE
# ------------------------------------------------

def restock_from_chest():
    """
    Restock reagents, blank scrolls and pens from resource chest to backpack.
    Returns True if chest is set and checked, False if chest missing.
    """
    if not STATE["resource_chest"]:
        STATE["restock_state"] = "No chest"
        draw_gui()
        return False

    chest = Items.FindBySerial(STATE["resource_chest"])
    if not chest:
        STATE["restock_state"] = "Chest missing"
        draw_gui()
        return False

    STATE["restock_state"] = "Running..."
    draw_gui()

    # Ensure chest is open
    Items.UseItem(chest)
    Misc.Pause(600)

    restock_table = [
        (0x0F7A, 100),  # Black Pearl
        (0x0F7B, 100),  # Bloodmoss
        (0x0F84, 100),  # Garlic
        (0x0F85, 100),  # Ginseng
        (0x0F86, 100),  # Mandrake Root
        (0x0F88, 100),  # Nightshade
        (0x0F8C, 100),  # Sulfurous Ash
        (0x0F8D, 100),  # Spiders' Silk
        (0x0EF3, 200),  # Blank Scroll
        (0x0FBF, 2),    # Pen
    ]

    for (item_id, desired) in restock_table:
        have = Items.BackpackCount(item_id, -1)
        if have >= desired:
            continue

        need = desired - have

        # Pull from chest in multiple stacks if needed
        while need > 0:
            stack = Items.FindByID(item_id, -1, chest.Serial)
            if not stack:
                break
            move_amount = need if stack.Amount >= need else stack.Amount
            status_text("Restocking %d of %s" % (move_amount, hex(item_id)))
            Items.Move(stack, Player.Backpack.Serial, move_amount)
            Misc.Pause(700)
            have += move_amount
            need = desired - have

    STATE["restock_state"] = "Ready"
    draw_gui()
    return True


# ------------------------------------------------
# INSCRIPTION GUMP / CRAFTING
# ------------------------------------------------

def ensure_scribe_gump():
    """Use pen and open the inscription gump, caching its gump id."""
    global SCRIBE_GUMP_ID

    spellbook = get_held_spellbook()
    if not spellbook:
        status_text("Hold your full spellbook in hand before crafting.")
        return False

    pen = Items.FindByID(SCRIBE_PEN_ID, -1, Player.Backpack.Serial)
    if not pen:
        status_text("No scribe pen found in backpack.")
        return False

    Items.UseItem(pen)
    # Wait for any gump
    Gumps.WaitForGump(0, 5000)
    if not Gumps.HasGump():
        status_text("Failed to open inscription gump.")
        return False

    SCRIBE_GUMP_ID = Gumps.CurrentGump()
    return True


def craft_circle_internal(circle_num, runs):
    """Core crafting loop for a single circle."""
    if circle_num not in CIRCLE_DATA:
        status_text("Unknown circle %d." % circle_num)
        return

    if not ensure_scribe_gump():
        return

    data = CIRCLE_DATA[circle_num]
    category_action = data["category_action"]
    spell_actions = data["spell_actions"]
    scroll_ids = data["scroll_ids"]

    total_spells = len(spell_actions) * runs
    step = 0

    STATE["current_circle"] = circle_num
    STATE["current_run"] = 0

    for run in range(runs):
        if STATE["abort"]:
            status_text("Aborted.")
            break

        STATE["current_run"] = run + 1

        # Select circle on left
        status_text("Circle %d – selecting (run %d/%d)" %
                    (circle_num, run + 1, runs))
        Gumps.SendAction(SCRIBE_GUMP_ID, category_action)
        Gumps.WaitForGump(SCRIBE_GUMP_ID, 2000)
        Misc.Pause(200)

        for idx in range(len(spell_actions)):
            if STATE["abort"]:
                status_text("Aborted.")
                break

            step += 1
            spell_action = spell_actions[idx]
            scroll_id = scroll_ids[idx]

            spell_status = "Circle %d spell %d/%d (run %d/%d)" % (
                circle_num, idx + 1, len(spell_actions),
                run + 1, runs
            )
            status_text("Crafting " + spell_status)
            set_progress(step, total_spells)

            attempts = 0
            created = False
            while attempts < MAX_ATTEMPTS_PER_SCROLL:
                attempts += 1
                pre_count = Items.BackpackCount(scroll_id, -1)
                Gumps.SendAction(SCRIBE_GUMP_ID, spell_action)
                Gumps.WaitForGump(SCRIBE_GUMP_ID, 2000)
                Misc.Pause(300)
                post_count = Items.BackpackCount(scroll_id, -1)
                if post_count > pre_count:
                    created = True
                    break

            if not created:
                status_text("Failed scroll %s (circle %d). Check mana/regs." %
                            (hex(scroll_id), circle_num))
                STATE["current_circle"] = 0
                STATE["current_run"] = 0
                return

        if STATE["abort"]:
            break

    STATE["current_circle"] = 0
    STATE["current_run"] = 0
    set_progress(total_spells, total_spells)
    status_text("Finished circle %d (%d run(s))." % (circle_num, runs))


def craft_all_circles_internal(runs):
    """Craft all circles 1–8."""
    if not ensure_scribe_gump():
        return

    total_steps = runs * len(CIRCLE_DATA) * 8
    current_step = 0

    for circle_num in sorted(CIRCLE_DATA.keys()):
        data = CIRCLE_DATA[circle_num]
        category_action = data["category_action"]
        spell_actions = data["spell_actions"]
        scroll_ids = data["scroll_ids"]

        for run in range(runs):
            if STATE["abort"]:
                status_text("Aborted.")
                STATE["current_circle"] = 0
                STATE["current_run"] = 0
                return

            STATE["current_circle"] = circle_num
            STATE["current_run"] = run + 1

            status_text("Circle %d – selecting (run %d/%d)" %
                        (circle_num, run + 1, runs))
            Gumps.SendAction(SCRIBE_GUMP_ID, category_action)
            Gumps.WaitForGump(SCRIBE_GUMP_ID, 2000)
            Misc.Pause(200)

            for idx in range(len(spell_actions)):
                if STATE["abort"]:
                    status_text("Aborted.")
                    STATE["current_circle"] = 0
                    STATE["current_run"] = 0
                    return

                current_step += 1
                spell_action = spell_actions[idx]
                scroll_id = scroll_ids[idx]

                spell_status = "Circle %d spell %d/%d (run %d/%d)" % (
                    circle_num, idx + 1, len(spell_actions),
                    run + 1, runs
                )
                status_text("Crafting " + spell_status)
                set_progress(current_step, total_steps)

                attempts = 0
                created = False
                while attempts < MAX_ATTEMPTS_PER_SCROLL:
                    attempts += 1
                    pre_count = Items.BackpackCount(scroll_id, -1)
                    Gumps.SendAction(SCRIBE_GUMP_ID, spell_action)
                    Gumps.WaitForGump(SCRIBE_GUMP_ID, 2000)
                    Misc.Pause(300)
                    post_count = Items.BackpackCount(scroll_id, -1)
                    if post_count > pre_count:
                        created = True
                        break

                if not created:
                    status_text("Failed scroll %s (circle %d). Check mana/regs." %
                                (hex(scroll_id), circle_num))
                    STATE["current_circle"] = 0
                    STATE["current_run"] = 0
                    return

    STATE["current_circle"] = 0
    STATE["current_run"] = 0
    set_progress(total_steps, total_steps)
    status_text("Finished all circles (%d run(s))." % runs)


# ------------------------------------------------
# MOVE SCROLLS TO DEPOSIT
# ------------------------------------------------

def move_all_scrolls_to_deposit():
    """Move all crafted scrolls from backpack to deposit chest, if set."""
    if not STATE["deposit_chest"]:
        return

    chest = Items.FindBySerial(STATE["deposit_chest"])
    if not chest:
        status_text("Deposit chest not found.")
        return

    status_text("Moving scrolls to deposit chest...")
    Items.UseItem(chest)
    Misc.Pause(600)

    for scroll_id in ALL_SCROLL_IDS:
        while True:
            scroll = Items.FindByID(scroll_id, -1, Player.Backpack.Serial)
            if not scroll:
                break
            Items.Move(scroll, chest.Serial, 0)
            Misc.Pause(600)

    status_text("Scrolls moved to deposit chest.")


# ------------------------------------------------
# FILLING SPELLBOOKS FROM DEPOSIT
# ------------------------------------------------

def deposit_has_any_scrolls(deposit_serial):
    """Quick check: does deposit chest have any scrolls at all?"""
    for sid in ALL_SCROLL_IDS:
        found = Items.FindByID(sid, -1, deposit_serial)
        if found:
            return True
    return False


def fill_one_book(deposit):
    """
    Fill ONE blank spellbook from scrolls in deposit.
    Returns True if a book was filled, False if no blank or no scrolls.
    """
    # Find a blank spellbook in deposit
    blank = Items.FindByID(SPELLBOOK_ID, -1, deposit.Serial)
    if not blank:
        return False

    # Quick check for scrolls available
    if not deposit_has_any_scrolls(deposit.Serial):
        return False

    status_text("Filling a spellbook from deposit chest...")
    # Move blank book to backpack
    Items.Move(blank, Player.Backpack.Serial, 1)
    Misc.Pause(700)

    # Re-acquire it in backpack
    book = Items.FindByID(SPELLBOOK_ID, -1, Player.Backpack.Serial)
    if not book:
        status_text("Moved blank book but cannot find it in backpack.")
        return False

    # Try to add up to 64 spells, one per scroll
    added = 0
    total_possible = 64

    for circle in sorted(CIRCLE_DATA.keys()):
        cdata = CIRCLE_DATA[circle]
        for scroll_id in cdata["scroll_ids"]:
            if added >= total_possible:
                break
            # Find scroll in deposit
            scroll = Items.FindByID(scroll_id, -1, deposit.Serial)
            if not scroll:
                continue

            # Move scroll to backpack
            Items.Move(scroll, Player.Backpack.Serial, 1)
            Misc.Pause(500)

            # Use scroll and target this book
            scroll_in_pack = Items.FindByID(scroll_id, -1, Player.Backpack.Serial)
            if not scroll_in_pack:
                continue

            Items.UseItem(scroll_in_pack)
            Target.WaitForTarget(2000, True)
            Target.TargetExecute(book)
            Misc.Pause(600)

            added += 1
            set_progress(added, total_possible)
            status_text("Filling book: %d/%d spells" % (added, total_possible))

        if added >= total_possible:
            break

    status_text("Filled a spellbook with %d spell(s)." % added)

    # Move finished book back to deposit chest
    Items.Move(book, deposit.Serial, 0)
    Misc.Pause(700)

    return added > 0


def fill_spellbooks_from_deposit():
    """
    Fill as many blank spellbooks as possible using scrolls from deposit chest.
    """
    if not STATE["deposit_chest"]:
        status_text("Deposit chest not set.")
        return

    deposit = Items.FindBySerial(STATE["deposit_chest"])
    if not deposit:
        status_text("Deposit chest not found.")
        return

    Items.UseItem(deposit)
    Misc.Pause(600)

    books_filled = 0
    while True:
        if STATE["abort"]:
            status_text("Aborted while filling spellbooks.")
            break

        if not fill_one_book(deposit):
            break
        books_filled += 1

    if books_filled > 0:
        status_text("Completed filling %d spellbook(s)." % books_filled)
    else:
        status_text("No blank books or no scrolls available to fill.")


# ------------------------------------------------
# GUI / GUMP
# ------------------------------------------------

def draw_gui():
    """Build and send the main GUI gump."""
    try:
        Gumps.CloseGump(GUI_GUMP_ID)
    except:
        pass

    gd = Gumps.CreateGump(True)

    Gumps.AddBackground(gd, 0, 0, GUMP_WIDTH, GUMP_HEIGHT, 9270)
    Gumps.AddAlphaRegion(gd, 10, 10, GUMP_WIDTH - 20, GUMP_HEIGHT - 20)

    x = 20
    y = 20

    # Header
    Gumps.AddLabel(gd, x, y, HEADER_HUE, "FrogScribe Suite")
    y += 22

    # Status line
    status = STATE["status"]
    if len(status) > 55:
        status = status[:52] + "..."
    Gumps.AddLabel(gd, x, y, STATUS_HUE, "Status:")
    Gumps.AddLabel(gd, x + 60, y, VALUE_HUE, status)
    y += 18

    # Progress bar
    progress = STATE["progress"]
    pct = int(progress * 100.0 + 0.5)
    bars_total = 16
    filled = int(bars_total * progress)
    bar_str = "[" + "#" * filled + "-" * (bars_total - filled) + "]"
    Gumps.AddLabel(gd, x, y, LABEL_HUE, "Progress:")
    Gumps.AddLabel(gd, x + 70, y, VALUE_HUE,
                   "%s %3d%%" % (bar_str, pct))
    y += 18

    # Restock state
    Gumps.AddLabel(gd, x, y, LABEL_HUE, "Restock:")
    Gumps.AddLabel(gd, x + 70, y, VALUE_HUE, STATE["restock_state"])
    y += 22

    # Chest info
    Gumps.AddLabel(gd, x, y, LABEL_HUE, "Resource chest:")
    Gumps.AddLabel(gd, x + 110, y, VALUE_HUE,
                   serial_to_str(STATE["resource_chest"]))
    y += 16

    Gumps.AddLabel(gd, x, y, LABEL_HUE, "Deposit chest:")
    Gumps.AddLabel(gd, x + 110, y, VALUE_HUE,
                   serial_to_str(STATE["deposit_chest"]))
    y += 22

    # Set chest buttons
    Gumps.AddButton(gd, x, y, 4005, 4007, BTN_SET_RESOURCE, 1, 0)
    Gumps.AddLabel(gd, x + 25, y + 2, BUTTON_LABEL_HUE, "Set Resource")

    Gumps.AddButton(gd, x + 140, y, 4005, 4007, BTN_SET_DEPOSIT, 1, 0)
    Gumps.AddLabel(gd, x + 165, y + 2, BUTTON_LABEL_HUE, "Set Deposit")
    y += 26

    # Runs control
    Gumps.AddLabel(gd, x, y, LABEL_HUE, "Runs:")
    # [-] button (your art 2223)
    Gumps.AddButton(gd, x + 50, y - 2, 2223, 2223, BTN_ITER_MINUS, 1, 0)
    # value
    Gumps.AddLabel(gd, x + 80, y, VALUE_HUE, str(STATE["iterations"]))
    # [+] button (your art 2224)
    Gumps.AddButton(gd, x + 110, y - 2, 2224, 2224, BTN_ITER_PLUS, 1, 0)
    y += 22

    # Mode toggle
    Gumps.AddLabel(gd, x, y, LABEL_HUE, "Mode:")
    Gumps.AddButton(gd, x + 50, y - 2, 4005, 4007, BTN_MODE_TOGGLE, 1, 0)
    Gumps.AddLabel(gd, x + 80, y + 2, BUTTON_LABEL_HUE,
                   STATE["mode"].title())
    y += 22

    # Fill Spellbooks button
    Gumps.AddButton(gd, x, y, 4005, 4007, BTN_FILL_BOOKS, 1, 0)
    Gumps.AddLabel(gd, x + 25, y + 2, BUTTON_LABEL_HUE, "Fill Spellbooks")
    y += 26

    # Craft All button
    Gumps.AddButton(gd, x, y, 4005, 4007, BTN_CRAFT_ALL, 1, 0)
    Gumps.AddLabel(gd, x + 25, y + 2, BUTTON_LABEL_HUE,
                   "Craft All Circles")
    y += 26

    # Per-circle buttons (two columns)
    btn_y = y
    col1_x = x
    col2_x = x + 150

    Gumps.AddButton(gd, col1_x, btn_y, 4005, 4007, BTN_CRAFT_C1, 1, 0)
    Gumps.AddLabel(gd, col1_x + 25, btn_y + 2, BUTTON_LABEL_HUE,
                   "1st Circle")
    btn_y += 22

    Gumps.AddButton(gd, col1_x, btn_y, 4005, 4007, BTN_CRAFT_C2, 1, 0)
    Gumps.AddLabel(gd, col1_x + 25, btn_y + 2, BUTTON_LABEL_HUE,
                   "2nd Circle")
    btn_y += 22

    Gumps.AddButton(gd, col1_x, btn_y, 4005, 4007, BTN_CRAFT_C3, 1, 0)
    Gumps.AddLabel(gd, col1_x + 25, btn_y + 2, BUTTON_LABEL_HUE,
                   "3rd Circle")
    btn_y += 22

    Gumps.AddButton(gd, col1_x, btn_y, 4005, 4007, BTN_CRAFT_C4, 1, 0)
    Gumps.AddLabel(gd, col1_x + 25, btn_y + 2, BUTTON_LABEL_HUE,
                   "4th Circle")

    btn_y = y
    Gumps.AddButton(gd, col2_x, btn_y, 4005, 4007, BTN_CRAFT_C5, 1, 0)
    Gumps.AddLabel(gd, col2_x + 25, btn_y + 2, BUTTON_LABEL_HUE,
                   "5th Circle")
    btn_y += 22

    Gumps.AddButton(gd, col2_x, btn_y, 4005, 4007, BTN_CRAFT_C6, 1, 0)
    Gumps.AddLabel(gd, col2_x + 25, btn_y + 2, BUTTON_LABEL_HUE,
                   "6th Circle")
    btn_y += 22

    Gumps.AddButton(gd, col2_x, btn_y, 4005, 4007, BTN_CRAFT_C7, 1, 0)
    Gumps.AddLabel(gd, col2_x + 25, btn_y + 2, BUTTON_LABEL_HUE,
                   "7th Circle")
    btn_y += 22

    Gumps.AddButton(gd, col2_x, btn_y, 4005, 4007, BTN_CRAFT_C8, 1, 0)
    Gumps.AddLabel(gd, col2_x + 25, btn_y + 2, BUTTON_LABEL_HUE,
                   "8th Circle")

    # Stop / Close at bottom
    Gumps.AddButton(gd, x, GUMP_HEIGHT - 40, 4017, 4019, BTN_STOP, 1, 0)
    Gumps.AddLabel(gd, x + 25, GUMP_HEIGHT - 38, BUTTON_LABEL_HUE, "Stop")

    Gumps.AddButton(gd, GUMP_WIDTH - 70, GUMP_HEIGHT - 40,
                    4017, 4019, BTN_CLOSE, 1, 0)
    Gumps.AddLabel(gd, GUMP_WIDTH - 45, GUMP_HEIGHT - 38,
                   BUTTON_LABEL_HUE, "Close")

    Gumps.SendGump(GUI_GUMP_ID, Player.Serial, 50, 50,
                   gd.gumpDefinition, gd.gumpStrings)


# ------------------------------------------------
# BUTTON HANDLER
# ------------------------------------------------

def handle_button(button_id):
    if button_id == 0:
        return None

    # Set chests
    if button_id == BTN_SET_RESOURCE:
        status_text("Target resource chest...")
        serial = Target.PromptTarget("Target your resource chest")
        STATE["resource_chest"] = serial
        status_text("Resource chest set.")
        return None

    if button_id == BTN_SET_DEPOSIT:
        status_text("Target deposit chest...")
        serial = Target.PromptTarget("Target your deposit chest")
        STATE["deposit_chest"] = serial
        status_text("Deposit chest set.")
        return None

    # Runs
    if button_id == BTN_ITER_MINUS:
        STATE["iterations"] -= 1
        clamp_iterations()
        status_text("Runs set to %d." % STATE["iterations"])
        return None

    if button_id == BTN_ITER_PLUS:
        STATE["iterations"] += 1
        clamp_iterations()
        status_text("Runs set to %d." % STATE["iterations"])
        return None

    # Mode toggle
    if button_id == BTN_MODE_TOGGLE:
        idx = MODES.index(STATE["mode"])
        STATE["mode"] = MODES[(idx + 1) % len(MODES)]
        status_text("Mode: %s" % STATE["mode"].title())
        return None

    # Fill Spellbooks
    if button_id == BTN_FILL_BOOKS:
        STATE["abort"] = False
        fill_spellbooks_from_deposit()
        return None

    # Stop / Close
    if button_id == BTN_STOP:
        STATE["abort"] = True
        status_text("Abort requested...")
        return None

    if button_id == BTN_CLOSE:
        STATE["abort"] = True
        status_text("Closing FrogScribe Suite.")
        Gumps.CloseGump(GUI_GUMP_ID)
        return "exit"

    # Crafting actions
    runs = STATE["iterations"]

    # Restock before any crafting
    def do_craft_circle(cnum):
        STATE["abort"] = False
        if not restock_from_chest():
            return
        craft_circle_internal(cnum, runs)
        if not STATE["abort"]:
            move_all_scrolls_to_deposit()
            if STATE["mode"] == "craftfill":
                fill_spellbooks_from_deposit()

    def do_craft_all():
        STATE["abort"] = False
        if not restock_from_chest():
            return
        craft_all_circles_internal(runs)
        if not STATE["abort"]:
            move_all_scrolls_to_deposit()
            if STATE["mode"] == "craftfill":
                fill_spellbooks_from_deposit()

    if button_id == BTN_CRAFT_ALL:
        do_craft_all()
        return None

    if button_id == BTN_CRAFT_C1:
        do_craft_circle(1)
        return None
    if button_id == BTN_CRAFT_C2:
        do_craft_circle(2)
        return None
    if button_id == BTN_CRAFT_C3:
        do_craft_circle(3)
        return None
    if button_id == BTN_CRAFT_C4:
        do_craft_circle(4)
        return None
    if button_id == BTN_CRAFT_C5:
        do_craft_circle(5)
        return None
    if button_id == BTN_CRAFT_C6:
        do_craft_circle(6)
        return None
    if button_id == BTN_CRAFT_C7:
        do_craft_circle(7)
        return None
    if button_id == BTN_CRAFT_C8:
        do_craft_circle(8)
        return None

    return None


# ------------------------------------------------
# MAIN
# ------------------------------------------------

def main():
    clamp_iterations()
    STATE["abort"] = False
    status_text("FrogScribe Suite ready.")

    running = True
    while running and Player.Connected:
        draw_gui()
        Gumps.WaitForGump(GUI_GUMP_ID, 0)
        gd = Gumps.GetGumpData(GUI_GUMP_ID)
        if gd is None:
            Misc.Pause(100)
            continue
        result = handle_button(gd.buttonid)
        if result == "exit":
            running = False
        Misc.Pause(100)


main()
