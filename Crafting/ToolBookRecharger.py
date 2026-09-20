# ==================================
# ==  Crafting Tool Retriever     ==
# ==================================
# Author: Frogmancer Schteve
#
# Razor Enhanced / ClassicUO
#

import Gumps, Items, Misc, Player, Target


# ====================================================================
# CONFIGURATION
# ====================================================================

GUI_GUMP_ID     = 0xF2065442
STORAGE_GUMP_ID = 0xC3DE2C83

GUMP_X = 600
GUMP_Y = 350

REFRESH_MS = 150

MAIN_WIDTH  = 390
MAIN_HEIGHT = 155

CONFIG_WIDTH  = 390
CONFIG_HEIGHT = 255

BG_ID = 5054

TITLE_HUE = 1152
LABEL_HUE = 0x0481
GOOD_HUE  = 68
WARN_HUE  = 53
BAD_HUE   = 33

RETRIEVE_BUTTON = 100
TEXT_ENTRY_ID   = 0

DEFAULT_TOOL_COUNT   = 10
DEFAULT_TOOL_CHARGES = 15

SYSTEM_GUMP_TIMEOUT = 10000

CATEGORY_FIELD_VALUE = "50"

BETWEEN_TOOLS_MS = 500

BUTTON_DEBOUNCE_MS = 180


# ====================================================================
# SHARED VALUE KEYS
# ====================================================================

KEY_BOOK_SERIAL  = "toolRetrieverBook"
KEY_TOOL_INDEX   = "toolRetrieverTool"
KEY_TOOL_COUNT   = "toolRetrieverCount"
KEY_TOOL_CHARGES = "toolRetrieverCharges"


# ====================================================================
# TOOL STORAGE CONFIGURATION
# ====================================================================

TOOL_OPTIONS = {
    1: {
        "skill": "Blacksmithy",
        "tool": "Smith Hammer",
        "category_button": 1,
    },

    2: {
        "skill": "Carpentry",
        "tool": "Carpentry Tool",
        "category_button": 2,
    },

    3: {
        "skill": "Tailoring",
        "tool": "Tailoring Tool",
        "category_button": 3,
    },

    4: {
        "skill": "Mining",
        "tool": "Pickaxe",
        "category_button": 4,
    },

    5: {
        "skill": "Lumberjacking",
        "tool": "Lumberjacking Tool",
        "category_button": 5,
    },

    6: {
        "skill": "Cooking",
        "tool": "Cooking Tool",
        "category_button": 6,
    },

    7: {
        "skill": "Alchemy",
        "tool": "Alchemy Tool",
        "category_button": 7,
    },

    8: {
        "skill": "Fletching",
        "tool": "Fletching Tool",
        "category_button": 8,
    },

    9: {
        "skill": "Inscription",
        "tool": "Inscription Tool",
        "category_button": 9,
    },

    10: {
        "skill": "Tinkering",
        "tool": "Tinkering Tool",
        "category_button": 10,
    },
}


# ====================================================================
# BUTTON IDS
# ====================================================================

BTN_RUN      = 1001
BTN_ABORT    = 1002
BTN_SETTINGS = 1003
BTN_CLOSE    = 1004

BTN_BACK     = 1100
BTN_SET_BOOK = 1101

BTN_COUNT_MINUS_10 = 1201
BTN_COUNT_MINUS_1  = 1202
BTN_COUNT_PLUS_1   = 1203
BTN_COUNT_PLUS_10  = 1204

BTN_CHARGES_MINUS_10 = 1211
BTN_CHARGES_MINUS_1  = 1212
BTN_CHARGES_PLUS_1   = 1213
BTN_CHARGES_PLUS_10  = 1214

BTN_TOOL_BASE = 2000


# ====================================================================
# GLOBAL STATE
# ====================================================================

_running        = True
_runtime_active = False

_current_page = "main"
_status_msg   = "Idle"

_completed = 0

_book_serial = (
    int(Misc.ReadSharedValue(KEY_BOOK_SERIAL))
    if Misc.CheckSharedValue(KEY_BOOK_SERIAL)
    else 0
)

_selected_tool = (
    int(Misc.ReadSharedValue(KEY_TOOL_INDEX))
    if Misc.CheckSharedValue(KEY_TOOL_INDEX)
    else 4
)

_desired_count = (
    int(Misc.ReadSharedValue(KEY_TOOL_COUNT))
    if Misc.CheckSharedValue(KEY_TOOL_COUNT)
    else DEFAULT_TOOL_COUNT
)

_tool_charges = (
    int(Misc.ReadSharedValue(KEY_TOOL_CHARGES))
    if Misc.CheckSharedValue(KEY_TOOL_CHARGES)
    else DEFAULT_TOOL_CHARGES
)


# ====================================================================
# HELPERS
# ====================================================================

def save_settings():
    Misc.SetSharedValue(KEY_BOOK_SERIAL, _book_serial)
    Misc.SetSharedValue(KEY_TOOL_INDEX, _selected_tool)
    Misc.SetSharedValue(KEY_TOOL_COUNT, _desired_count)
    Misc.SetSharedValue(KEY_TOOL_CHARGES, _tool_charges)


def selected_tool_data():
    return TOOL_OPTIONS.get(
        _selected_tool,
        TOOL_OPTIONS[4]
    )


def selected_tool_name():
    data = selected_tool_data()

    return "{0} - {1}".format(
        data["skill"],
        data["tool"]
    )


def clamp_count(value):
    return max(
        1,
        min(999, int(value))
    )


def clamp_charges(value):
    return max(
        1,
        min(9999, int(value))
    )


def book_exists():
    if not _book_serial:
        return False

    return Items.FindBySerial(
        _book_serial
    ) is not None


def close_storage_gump():
    try:
        Gumps.CloseGump(
            STORAGE_GUMP_ID
        )
    except:
        pass


def set_storage_book():
    global _book_serial
    global _status_msg

    Target.Cancel()

    Misc.SendMessage(
        "Target your Crafting Tool Storage book.",
        68
    )

    serial = Target.PromptTarget(
        "Select Crafting Tool Storage"
    )

    if serial <= 0:
        _status_msg = "Book selection cancelled."
        return

    item = Items.FindBySerial(serial)

    if not item:
        _status_msg = "Targeted item not found."
        return

    _book_serial = serial

    save_settings()

    _status_msg = "Storage book saved."

    Player.HeadMessage(
        GOOD_HUE,
        "Crafting Tool Storage saved."
    )


# ====================================================================
# STORAGE BOOK TRANSACTION
# ====================================================================
#
# This intentionally follows the recorded Razor Enhanced macro:
#
# Items.UseItem(book)
# WaitForGump
#
# SendAdvancedAction(category, [], [0], ["50"])
# WaitForGump
#
# SendAdvancedAction(100, [], [0], ["15"])
# WaitForGump
#
# SendAdvancedAction(0, [], [0], ["50"])
#
# No ResetGump.
# No CurrentGump checks.
# No custom timeout-stop logic between actions.
#

def withdraw_one_tool_transaction():
    global _status_msg

    if not book_exists():
        _status_msg = "Storage book missing."
        return False

    data = selected_tool_data()

    # --------------------------------------------------------
    # OPEN
    # --------------------------------------------------------

    close_storage_gump()

    Misc.Pause(200)

    _status_msg = "Opening storage..."

    Items.UseItem(
        _book_serial
    )

    Gumps.WaitForGump(
        STORAGE_GUMP_ID,
        SYSTEM_GUMP_TIMEOUT
    )

    # --------------------------------------------------------
    # CATEGORY
    # --------------------------------------------------------

    _status_msg = "Selecting {0}...".format(
        data["skill"]
    )

    Gumps.SendAdvancedAction(
        STORAGE_GUMP_ID,
        data["category_button"],
        [],
        [TEXT_ENTRY_ID],
        [CATEGORY_FIELD_VALUE]
    )

    Gumps.WaitForGump(
        STORAGE_GUMP_ID,
        SYSTEM_GUMP_TIMEOUT
    )

    # --------------------------------------------------------
    # RETRIEVE
    # --------------------------------------------------------

    _status_msg = "Retrieving {0} @ {1}...".format(
        data["tool"],
        _tool_charges
    )

    Gumps.SendAdvancedAction(
        STORAGE_GUMP_ID,
        RETRIEVE_BUTTON,
        [],
        [TEXT_ENTRY_ID],
        [str(_tool_charges)]
    )

    Gumps.WaitForGump(
        STORAGE_GUMP_ID,
        SYSTEM_GUMP_TIMEOUT
    )

    # --------------------------------------------------------
    # CLOSE RESPONSE
    # --------------------------------------------------------

    Gumps.SendAdvancedAction(
        STORAGE_GUMP_ID,
        0,
        [],
        [TEXT_ENTRY_ID],
        [CATEGORY_FIELD_VALUE]
    )

    Misc.Pause(BETWEEN_TOOLS_MS)

    return True


# ====================================================================
# WITHDRAW MODULE
# ====================================================================

def start_withdrawal():
    global _runtime_active
    global _completed
    global _status_msg

    if not book_exists():
        _status_msg = "Set storage book first."
        return

    _completed = 0
    _runtime_active = True

    _status_msg = "Running: 0/{0}".format(
        _desired_count
    )


def abort_withdrawal():
    global _runtime_active
    global _status_msg

    _runtime_active = False

    close_storage_gump()

    _status_msg = "Aborted: {0}/{1}".format(
        _completed,
        _desired_count
    )


def finish_withdrawal():
    global _runtime_active
    global _status_msg

    _runtime_active = False

    close_storage_gump()

    _status_msg = "Complete: {0}/{1}".format(
        _completed,
        _desired_count
    )

    Player.HeadMessage(
        GOOD_HUE,
        "Tool withdrawal complete."
    )


def withdrawal_step():
    global _runtime_active
    global _completed
    global _status_msg

    if not _runtime_active:
        return

    if _completed >= _desired_count:
        finish_withdrawal()
        return

    if not withdraw_one_tool_transaction():
        _runtime_active = False
        return

    _completed += 1

    if _completed >= _desired_count:
        finish_withdrawal()
        return

    _status_msg = "Running: {0}/{1}".format(
        _completed,
        _desired_count
    )


# ====================================================================
# GUMP / GUI FUNCTIONS
# ====================================================================

def render_main():
    Gumps.CloseGump(
        GUI_GUMP_ID
    )

    gd = Gumps.CreateGump(
        movable=True
    )

    Gumps.AddPage(
        gd,
        0
    )

    Gumps.AddBackground(
        gd,
        0,
        0,
        MAIN_WIDTH,
        MAIN_HEIGHT,
        BG_ID
    )

    Gumps.AddAlphaRegion(
        gd,
        0,
        0,
        MAIN_WIDTH,
        MAIN_HEIGHT
    )

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    Gumps.AddLabel(
        gd,
        12,
        10,
        TITLE_HUE,
        "Frog Tool Retriever"
    )

    Gumps.AddButton(
        gd,
        300,
        8,
        4029,
        4030,
        BTN_SETTINGS,
        1,
        0
    )

    Gumps.AddLabel(
        gd,
        322,
        10,
        LABEL_HUE,
        "Config"
    )

    Gumps.AddButton(
        gd,
        367,
        8,
        4017,
        4018,
        BTN_CLOSE,
        1,
        0
    )

    # --------------------------------------------------------
    # TOOL
    # --------------------------------------------------------

    Gumps.AddLabel(
        gd,
        12,
        38,
        LABEL_HUE,
        "Tool:"
    )

    Gumps.AddLabel(
        gd,
        55,
        38,
        GOOD_HUE,
        selected_tool_name()
    )

    Gumps.AddLabel(
        gd,
        270,
        38,
        LABEL_HUE,
        "Charges:"
    )

    Gumps.AddLabel(
        gd,
        335,
        38,
        WARN_HUE,
        str(_tool_charges)
    )

    # --------------------------------------------------------
    # AMOUNT / PROGRESS
    # --------------------------------------------------------

    Gumps.AddLabel(
        gd,
        12,
        62,
        LABEL_HUE,
        "Amount:"
    )

    Gumps.AddLabel(
        gd,
        70,
        62,
        GOOD_HUE,
        str(_desired_count)
    )

    Gumps.AddLabel(
        gd,
        145,
        62,
        LABEL_HUE,
        "Progress:"
    )

    Gumps.AddLabel(
        gd,
        215,
        62,
        GOOD_HUE,
        "{0}/{1}".format(
            _completed,
            _desired_count
        )
    )

    Gumps.AddLabel(
        gd,
        290,
        62,
        LABEL_HUE,
        "Book:"
    )

    Gumps.AddLabel(
        gd,
        335,
        62,
        GOOD_HUE if _book_serial else BAD_HUE,
        "Set" if _book_serial else "None"
    )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    Gumps.AddLabel(
        gd,
        12,
        87,
        LABEL_HUE,
        "Status:"
    )

    Gumps.AddLabel(
        gd,
        65,
        87,
        GOOD_HUE if _runtime_active else WARN_HUE,
        _status_msg[:47]
    )

    # --------------------------------------------------------
    # RUN / ABORT
    # --------------------------------------------------------

    if _runtime_active:

        Gumps.AddButton(
            gd,
            12,
            117,
            4017,
            4019,
            BTN_ABORT,
            1,
            0
        )

        Gumps.AddLabel(
            gd,
            38,
            119,
            BAD_HUE,
            "Abort"
        )

    else:

        Gumps.AddButton(
            gd,
            12,
            117,
            4005,
            4007,
            BTN_RUN,
            1,
            0
        )

        Gumps.AddLabel(
            gd,
            38,
            119,
            GOOD_HUE,
            "Run"
        )

    Gumps.SendGump(
        GUI_GUMP_ID,
        Player.Serial,
        GUMP_X,
        GUMP_Y,
        gd.gumpDefinition,
        gd.gumpStrings
    )


def render_settings():
    Gumps.CloseGump(
        GUI_GUMP_ID
    )

    gd = Gumps.CreateGump(
        movable=True
    )

    Gumps.AddPage(
        gd,
        0
    )

    Gumps.AddBackground(
        gd,
        0,
        0,
        CONFIG_WIDTH,
        CONFIG_HEIGHT,
        BG_ID
    )

    Gumps.AddAlphaRegion(
        gd,
        0,
        0,
        CONFIG_WIDTH,
        CONFIG_HEIGHT
    )

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    Gumps.AddLabel(
        gd,
        12,
        10,
        TITLE_HUE,
        "Tool Retriever Config"
    )

    Gumps.AddButton(
        gd,
        310,
        8,
        4014,
        4015,
        BTN_BACK,
        1,
        0
    )

    Gumps.AddLabel(
        gd,
        332,
        10,
        LABEL_HUE,
        "Back"
    )

    Gumps.AddButton(
        gd,
        367,
        8,
        4017,
        4018,
        BTN_CLOSE,
        1,
        0
    )

    # --------------------------------------------------------
    # STORAGE BOOK
    # --------------------------------------------------------

    Gumps.AddLabel(
        gd,
        12,
        40,
        LABEL_HUE,
        "Storage Book:"
    )

    Gumps.AddButton(
        gd,
        105,
        38,
        4005,
        4007,
        BTN_SET_BOOK,
        1,
        0
    )

    Gumps.AddLabel(
        gd,
        130,
        40,
        GOOD_HUE,
        "Set / Retarget"
    )

    if _book_serial:
        book_text = "0x{0:X}".format(
            _book_serial
        )
    else:
        book_text = "Not Set"

    Gumps.AddLabel(
        gd,
        270,
        40,
        GOOD_HUE if _book_serial else BAD_HUE,
        book_text
    )

    # --------------------------------------------------------
    # TOOL AMOUNT
    # --------------------------------------------------------

    Gumps.AddLabel(
        gd,
        12,
        68,
        LABEL_HUE,
        "Tool Amount:"
    )

    Gumps.AddButton(
        gd,
        100,
        66,
        4014,
        4015,
        BTN_COUNT_MINUS_10,
        1,
        0
    )

    Gumps.AddLabel(
        gd,
        122,
        68,
        LABEL_HUE,
        "-10"
    )

    Gumps.AddButton(
        gd,
        150,
        66,
        4014,
        4015,
        BTN_COUNT_MINUS_1,
        1,
        0
    )

    Gumps.AddLabel(
        gd,
        172,
        68,
        LABEL_HUE,
        "-1"
    )

    Gumps.AddLabel(
        gd,
        210,
        68,
        GOOD_HUE,
        str(_desired_count)
    )

    Gumps.AddButton(
        gd,
        245,
        66,
        4005,
        4007,
        BTN_COUNT_PLUS_1,
        1,
        0
    )

    Gumps.AddLabel(
        gd,
        267,
        68,
        LABEL_HUE,
        "+1"
    )

    Gumps.AddButton(
        gd,
        300,
        66,
        4005,
        4007,
        BTN_COUNT_PLUS_10,
        1,
        0
    )

    Gumps.AddLabel(
        gd,
        322,
        68,
        LABEL_HUE,
        "+10"
    )

    # --------------------------------------------------------
    # TOOL CHARGES
    # --------------------------------------------------------

    Gumps.AddLabel(
        gd,
        12,
        96,
        LABEL_HUE,
        "Tool Charges:"
    )

    Gumps.AddButton(
        gd,
        100,
        94,
        4014,
        4015,
        BTN_CHARGES_MINUS_10,
        1,
        0
    )

    Gumps.AddLabel(
        gd,
        122,
        96,
        LABEL_HUE,
        "-10"
    )

    Gumps.AddButton(
        gd,
        150,
        94,
        4014,
        4015,
        BTN_CHARGES_MINUS_1,
        1,
        0
    )

    Gumps.AddLabel(
        gd,
        172,
        96,
        LABEL_HUE,
        "-1"
    )

    Gumps.AddLabel(
        gd,
        210,
        96,
        WARN_HUE,
        str(_tool_charges)
    )

    Gumps.AddButton(
        gd,
        245,
        94,
        4005,
        4007,
        BTN_CHARGES_PLUS_1,
        1,
        0
    )

    Gumps.AddLabel(
        gd,
        267,
        96,
        LABEL_HUE,
        "+1"
    )

    Gumps.AddButton(
        gd,
        300,
        94,
        4005,
        4007,
        BTN_CHARGES_PLUS_10,
        1,
        0
    )

    Gumps.AddLabel(
        gd,
        322,
        96,
        LABEL_HUE,
        "+10"
    )

    # --------------------------------------------------------
    # TOOL SELECTION
    # --------------------------------------------------------

    Gumps.AddLabel(
        gd,
        12,
        126,
        TITLE_HUE,
        "Tool:"
    )

    for index in range(1, 11):

        if index <= 5:
            col = 0
            row = index - 1
        else:
            col = 1
            row = index - 6

        x = 12 + (col * 190)
        y = 150 + (row * 19)

        Gumps.AddButton(
            gd,
            x,
            y,
            4005,
            4007,
            BTN_TOOL_BASE + index,
            1,
            0
        )

        hue = (
            GOOD_HUE
            if index == _selected_tool
            else LABEL_HUE
        )

        Gumps.AddLabel(
            gd,
            x + 23,
            y,
            hue,
            TOOL_OPTIONS[index]["skill"]
        )

    Gumps.SendGump(
        GUI_GUMP_ID,
        Player.Serial,
        GUMP_X,
        GUMP_Y,
        gd.gumpDefinition,
        gd.gumpStrings
    )


def render_gui():
    if _current_page == "settings":
        render_settings()
    else:
        render_main()


# ====================================================================
# BUTTON HANDLING
# ====================================================================

def handle_button(button_id):
    global _running
    global _runtime_active
    global _current_page
    global _status_msg
    global _selected_tool
    global _desired_count
    global _tool_charges

    if button_id == BTN_CLOSE:
        _runtime_active = False
        _running = False
        return

    # --------------------------------------------------------
    # MAIN PAGE
    # --------------------------------------------------------

    if button_id == BTN_SETTINGS:

        if _runtime_active:
            _status_msg = "Abort before changing config."
            return

        _current_page = "settings"
        return

    if button_id == BTN_RUN:
        start_withdrawal()
        return

    if button_id == BTN_ABORT:
        abort_withdrawal()
        return

    # --------------------------------------------------------
    # CONFIG PAGE
    # --------------------------------------------------------

    if button_id == BTN_BACK:
        _current_page = "main"
        return

    if button_id == BTN_SET_BOOK:
        set_storage_book()
        return

    # --------------------------------------------------------
    # TOOL AMOUNT
    # --------------------------------------------------------

    if button_id == BTN_COUNT_MINUS_10:

        _desired_count = clamp_count(
            _desired_count - 10
        )

        save_settings()
        return

    if button_id == BTN_COUNT_MINUS_1:

        _desired_count = clamp_count(
            _desired_count - 1
        )

        save_settings()
        return

    if button_id == BTN_COUNT_PLUS_1:

        _desired_count = clamp_count(
            _desired_count + 1
        )

        save_settings()
        return

    if button_id == BTN_COUNT_PLUS_10:

        _desired_count = clamp_count(
            _desired_count + 10
        )

        save_settings()
        return

    # --------------------------------------------------------
    # TOOL CHARGES
    # --------------------------------------------------------

    if button_id == BTN_CHARGES_MINUS_10:

        _tool_charges = clamp_charges(
            _tool_charges - 10
        )

        save_settings()
        return

    if button_id == BTN_CHARGES_MINUS_1:

        _tool_charges = clamp_charges(
            _tool_charges - 1
        )

        save_settings()
        return

    if button_id == BTN_CHARGES_PLUS_1:

        _tool_charges = clamp_charges(
            _tool_charges + 1
        )

        save_settings()
        return

    if button_id == BTN_CHARGES_PLUS_10:

        _tool_charges = clamp_charges(
            _tool_charges + 10
        )

        save_settings()
        return

    # --------------------------------------------------------
    # TOOL SELECTION
    # --------------------------------------------------------

    tool_index = (
        button_id - BTN_TOOL_BASE
    )

    if tool_index in TOOL_OPTIONS:

        _selected_tool = tool_index

        save_settings()

        _status_msg = "Selected {0}.".format(
            selected_tool_name()
        )

        return


# ====================================================================
# MAIN
# ====================================================================

render_gui()

while _running and Player.Connected:

    handled_button = False

    # --------------------------------------------------------
    # READ CUSTOM GUI BEFORE REDRAW
    # --------------------------------------------------------

    try:
        gd = Gumps.GetGumpData(
            GUI_GUMP_ID
        )
    except:
        gd = None

    if gd and gd.buttonid:

        button_id = gd.buttonid

        try:
            gd.buttonid = 0
        except:
            pass

        handle_button(
            button_id
        )

        handled_button = True

        if not _running:
            break

        render_gui()

        Misc.Pause(
            BUTTON_DEBOUNCE_MS
        )

    # --------------------------------------------------------
    # RUNTIME
    # --------------------------------------------------------

    if _runtime_active:

        withdrawal_step()

        render_main()

    # --------------------------------------------------------
    # RESTORE CUSTOM GUI IF CLOSED
    # --------------------------------------------------------

    elif not handled_button:

        try:
            if not Gumps.GetGumpData(
                GUI_GUMP_ID
            ):
                render_gui()

        except:
            render_gui()

    Misc.Pause(
        REFRESH_MS
    )


# ====================================================================
# CLEANUP
# ====================================================================

_runtime_active = False

Gumps.CloseGump(
    GUI_GUMP_ID
)

close_storage_gump()
