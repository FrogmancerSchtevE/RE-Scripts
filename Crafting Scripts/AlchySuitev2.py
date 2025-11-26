# ==================================
# ==  Alchy Suite (Frog Edition) ==
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
# Modes:
#   - Training (Poison Mastery path: Lesser/Poison/Greater Poison)
#   - Shelf Fill (craft N of each selected potion, deposit via shelf "Add")
#   - Keg Fill (keg-focused crafting; optional GM tinkering full kegs)
#   - Just Potions (craft N of each selected potion into backpack)
#
# Requirements:
#   - ClassicUO + Razor Enhanced.
#   - Potions crafted via Alchemy gump (ID 0x38920ABD).
#   - Resource container near you (reagents + bottles + boards/ingots for kegs).
#   - (Optional) Potion shelf (ItemID 0xAFC1) for Shelf Fill mode.
#   
# Notes:
#   - Training mode:
#       * Requires you to manually buy Alchemy to 50 from an NPC first.
#       * Be in Poison Mastery, or you'll die from drinking the poisons.
#       * Crafts only poison-type potions and drinks them immediately
#         to reclaim bottles. 
#   - Dictionary Format. I'll be using this format for all future crafting tools. Feel
#     free to utilize this codeblock for your own tools. The button IDS/Graphic IDS are free use
# DISCLAIMER:
#   This is a helper tool, not a license to break shard rules.
#   This is intended to use poisons and drinking them to save resources, feel free to edit the training config
#   to suit your needs, you'll need to edit drinking them though. Good luck.
#

from AutoComplete import *
from System import Int32
from System.Collections.Generic import List as CList
import time


# ===========================================================
# CONFIGURATION
# ===========================================================

GUMP_ID    = 0xA110C0DE
REFRESH_MS = 300
GUMP_X, GUMP_Y = 600, 300

ALCH_GUMP_ID      = 0x38920ABD
COMPENDIUM_GUMPID = 0x93069BD5
SHELF_ITEM_ID     = 0xAFC1
TOOL_ID = 0x0E9B # Mortar Pestal ID for reliablity 

RESOURCE_IDS = {
    "Mandrake":     0x0F86,
    "Bloodmoss":    0x0F7B,
    "Sulfurous Ash":0x0F8C,
    "Spiders Silk": 0x0F8D,
    "Garlic":       0x0F84,
    "Black Pearl":  0x0F7A,
    "Nightshade":   0x0F88,
    "Ginseng":      0x0F85,
    "Empty Bottle": 0x0F0E,
    "Wyrm's Heart": 0x0F91,
    "Eye of Newt":  0x0F87,
    "Boards":       0x1BD7,
    "Ingots":       0x1BF2,
}

POTION_GRAPHICS = {
    # Healing & Curative
    "Refresh":                0x0F0B,   
    "Greater Refreshment":    0x0F0C,   
    "Lesser Heal":            0x0F0C,   
    "Heal":                   0x0F0C,
    "greater heal":           0x0F0C,
    "lesser cure":            0x0F07,
    "Cure":                   0x0F07,
    "greater cure":           0x0F07,
    # Enhancement
    "Agility":                0x0F08,
    "Greater Agility":        0x0F08,
    "Night Sight":            0x0F06,
    "Strength":               0x0F09,
    "Greater Strength":       0x0F09,
    "Mana Potion":            0x0F09,   
    "Total Mana Potion":      0x0F09,
    "Invisibility":           0x0F0E,   
    "Elixer of Rebirth":      0x0F0E,
    # Toxic
    "Lesser Poison":          0x0F0A,
    "Poison":                 0x0F0A,
    "Greater Poison":         0x0F0A,
    "Deadly Poison":          0x0F0A,
    # Explosive
    "lesser explosion":       0x0F0D,
    "Explosion":              0x0F0D,
    "greater explosion":      0x0F0D,
    "conflagration":          0x0F0D,
    "greater conglagration":  0x0F0D,
    "confusion blast":        0x0F0D,
    "greater confusion blast":0x0F0D,
    # Strange Brew
    "smoke bomb":             0x0F0E,
}

# ===========================================================
# Unchained Alchemy Gump Button Category/Item IDS, (DO NOT EDIT)
# ===========================================================
POTIONS = {
    "Healing And Curative": {
        "category_id": 1,
        "potions": {
            "Refresh": {
                "button_id": 2,
                "alchemy": 0,
                "reagents": {"Empty Bottle": 1, "Black Pearl": 1},
            },
            "Greater Refreshment": {
                "button_id": 9,
                "alchemy": 25,
                "reagents": {"Empty Bottle": 1, "Black Pearl": 5},
            },
            "Lesser Heal": {
                "button_id": 16,
                "alchemy": 0,
                "reagents": {"Empty Bottle": 1, "Ginseng": 1},
            },
            "Heal": {
                "button_id": 23,
                "alchemy": 15,
                "reagents": {"Empty Bottle": 1, "Ginseng": 3},
            },
            "greater heal": {
                "button_id": 30,
                "alchemy": 55,
                "reagents": {"Empty Bottle": 1, "Ginseng": 7},
            },
            "lesser cure": {
                "button_id": 37,
                "alchemy": 0,
                "reagents": {"Empty Bottle": 1, "Garlic": 1},
            },
            "Cure": {
                "button_id": 44,
                "alchemy": 25,
                "reagents": {"Empty Bottle": 1, "Garlic": 3},
            },
            "greater cure": {
                "button_id": 51,
                "alchemy": 65,
                "reagents": {"Empty Bottle": 1, "Garlic": 6},
            },
        },
    },

    "Full Potion Kegs": {
        "category_id": 8,
        "potions": {
            "Full Total Refresh": {
                "button_id": 2,
                "alchemy": 75,
                "tinkering": 50,
                "reagents": {
                    "Empty Bottle": 100,
                    "Black Pearl": 500,
                    "Boards": 18,
                    "Ingots": 4,
                },
            },
            "Full Greater Heal": {
                "button_id": 9,
                "alchemy": 75,
                "tinkering": 50,
                "reagents": {
                    "Empty Bottle": 100,
                    "Ginseng": 700,
                    "Boards": 18,
                    "Ingots": 4,
                },
            },
            "Full Greater Cure": {
                "button_id": 16,
                "alchemy": 75,
                "tinkering": 50,
                "reagents": {
                    "Empty Bottle": 100,
                    "Garlic": 600,
                    "Boards": 18,
                    "Ingots": 4,
                },
            },
            "Full Greater Agility": {
                "button_id": 23,
                "alchemy": 75,
                "tinkering": 50,
                "reagents": {
                    "Empty Bottle": 100,
                    "Bloodmoss": 300,
                    "Boards": 18,
                    "Ingots": 4,
                },
            },
            "Full Greater Strength": {
                "button_id": 30,
                "alchemy": 75,
                "tinkering": 50,
                "reagents": {
                    "Empty Bottle": 100,
                    "Mandrake": 500,
                    "Boards": 18,
                    "Ingots": 4,
                },
            },
            "Full Total Mana": {
                "button_id": 37,
                "alchemy": 90,
                "tinkering": 50,
                "reagents": {
                    "Empty Bottle": 100,
                    "Eye of Newt": 800,  
                    "Boards": 18,
                    "Ingots": 4,
                },
            },
            "Full Greater Poison": {
                "button_id": 44,
                "alchemy": 75,
                "tinkering": 50,
                "reagents": {
                    "Empty Bottle": 100,
                    "Nightshade": 400,
                    "Boards": 18,
                    "Ingots": 4,
                },
            },
            "Full Deadly Poison": {
                "button_id": 51,
                "alchemy": 90,
                "tinkering": 50,
                "reagents": {
                    "Empty Bottle": 100,
                    "Nightshade": 800,
                    "Boards": 18,
                    "Ingots": 4,
                },
            },
            "Full Greater Explosion": {
                "button_id": 58,   
                "alchemy": 90,
                "tinkering": 50,
                "reagents": {
                    "Empty Bottle": 100,
                    "Sulfurous Ash": 1000,
                    "Boards": 18,
                    "Ingots": 4,
                },
            },
        },
    },

    "Enhancement": {
        "category_id": 15,
        "potions": {
            "Agility": {
                "button_id": 2,
                "alchemy": 15,
                "reagents": {"Empty Bottle": 1, "Bloodmoss": 1},
            },
            "Greater Agility": {
                "button_id": 9,
                "alchemy": 35,
                "reagents": {"Empty Bottle": 1, "Bloodmoss": 3},
            },
            "Night Sight": {
                "button_id": 16,
                "alchemy": 0,
                "reagents": {"Empty Bottle": 1, "Spiders Silk": 1},
            },
            "Strength": {
                "button_id": 23,
                "alchemy": 25,
                "reagents": {"Empty Bottle": 1, "Mandrake": 2},
            },
            "Greater Strength": {
                "button_id": 30,
                "alchemy": 45,
                "reagents": {"Empty Bottle": 1, "Mandrake": 5},
            },
        },
    },

    "Misc Potions": {
        "category_id": 22,
        "potions": {
            "Mana Potion": {
                "button_id": 2,
                "alchemy": 60,
                "reagents": {"Empty Bottle": 1, "Eye of Newt": 4},
            },
            "Total Mana Potion": {
                "button_id": 9,
                "alchemy": 90,
                "reagents": {"Empty Bottle": 1, "Eye of Newt": 8},
            },
            "Invisibility": {
                "button_id": 16,
                "alchemy": 80,
                "reagents": {
                    "Empty Bottle": 1,
                    "Bloodmoss": 4,
                    "Nightshade": 3,
                },
            },
            "Elixer of Rebirth": {
                "button_id": 23,
                "alchemy": 95,
                "reagents": {
                    "Empty Bottle": 1,
                    "Sulfurous Ash": 10,
                    "Wyrms Heart": 3,
                },
            },
        },
    },

    "Toxic": {
        "category_id": 29,
        "potions": {
            "Lesser Poison": {
                "button_id": 2,
                "alchemy": 0,
                "reagents": {"Empty Bottle": 1, "Nightshade": 1},
            },
            "Poison": {
                "button_id": 9,
                "alchemy": 15,
                "reagents": {"Empty Bottle": 1, "Nightshade": 2},
            },
            "Greater Poison": {
                "button_id": 16,
                "alchemy": 55,
                "reagents": {"Empty Bottle": 1, "Nightshade": 4},
            },
            "Deadly Poison": {
                "button_id": 23,
                "alchemy": 90,
                "reagents": {"Empty Bottle": 1, "Nightshade": 8},
            },
        },
    },

    "Explosive": {
        "category_id": 36,
        "potions": {
            "lesser explosion": {
                "button_id": 2,
                "alchemy": 5,
                "reagents": {"Empty Bottle": 1, "Sulfurous Ash": 3},
            },
            "Explosion": {
                "button_id": 9,
                "alchemy": 35,
                "reagents": {"Empty Bottle": 1, "Sulfurous Ash": 5},
            },
            "greater explosion": {
                "button_id": 16,
                "alchemy": 65,
                "reagents": {"Empty Bottle": 1, "Sulfurous Ash": 10},
            },
            "conflagration": {
                "button_id": 23,
                "alchemy": 55,
                "reagents": {"Empty Bottle": 1, "Sulfurous Ash": 5},
            },
            "greater conglagration": {
                "button_id": 30,
                "alchemy": 70,
                "reagents": {"Empty Bottle": 1, "Sulfurous Ash": 10},
            },
            "confusion blast": {
                "button_id": 37,
                "alchemy": 55,
                "reagents": {"Empty Bottle": 1, "Nightshade": 5},
            },
            "greater confusion blast": {
                "button_id": 44,
                "alchemy": 70,
                "reagents": {"Empty Bottle": 1, "Nightshade": 10},
            },
        },
    },

    "Strange Brew": {
        "category_id": 43,
        "potions": {
            "smoke bomb": {
                "button_id": 2,
                "alchemy": 75,
                "reagents": {"Eggs": 1, "Ginseng": 3},
            },
        },
    },
}

# ===========================================================
# Training Configuration (feel free to edit) #TCEdit
# ===========================================================
GM_TINKERING       = False  # If True: use full kegs when in Keg mode
TRAINING_ENABLED   = True
TRAIN_POISON_TIERS = [
    # Format = skill_min, skill_max, potion_name, category_name
    (50.0, 53.4, "Lesser Poison", "Toxic"),
    (53.4, 65.0, "Poison",        "Toxic"),
    (65.0, 91.0, "Greater Poison", "Toxic"),
    (91.0, 200.0, "Deadly Poison", "Toxic"), # Up to Cap. We do a skill check in the script.
]

# ===========================================================
# CATEGORY PAGING (DO NOT EDIT)
# ===========================================================

# Ordered list of categories
_category_names = [
    "Healing And Curative",
    "Enhancement",
    "Explosive",
    "Toxic",
    "Misc Potions",
    "Full Potion Kegs",
    "Strange Brew",
]

_current_page   = 0  


# ===========================================================
# GLOBAL STATE (DO NOT EDIT)
# ===========================================================


MODE_TRAIN   = 1
MODE_SHELF   = 2
MODE_KEG     = 3
MODE_JUST    = 4

_running          = True
_runtime_active   = False
_current_mode     = MODE_TRAIN
_status_msg       = "Idle"
_textentry_focus_time = 0
_textentry_hold_ms = 4000 #Config as needed
_pending_restock = False
_click_cache = 0

_resource_container = Misc.ReadSharedValue("alchemyResCont") if Misc.CheckSharedValue("alchemyResCont") else 0
_shelf_serial       = Misc.ReadSharedValue("potionShelf")   if Misc.CheckSharedValue("potionShelf")   else 0

_selected_potions = {}  
_target_amount    = 25 # TGTAMT (Use this to find this field quickly) Default: 100

_poison_mastery_done = False # Probably unneeded now left in incase I can get that shit to work
_poison_mastery_warned = False 

_craft_queue = []   
_current_job = None 

# ===========================================================
# BUTTON IDS (DO NOT EDIT)
# ===========================================================

BTN_CLOSE          = 9000
BTN_MODE_TRAIN     = 9001
BTN_MODE_SHELF     = 9002
BTN_MODE_KEG       = 9003
BTN_MODE_JUST      = 9004
BTN_TOGGLE_RUN     = 9005
BTN_SET_RES_CONT   = 9006
BTN_SET_SHELF      = 9007

BTN_PAGE_PREV      = 9100
BTN_PAGE_NEXT      = 9101

BTN_POTION_BASE    = 10000
_potion_button_map = {}



# ===========================================================
# SMALL HELPERS (DO NOT EDIT)
# ===========================================================

def safe_get_skill_cap():
    try:
        val = Player.GetSkillCap("Alchemy")
        if val is not None:
            return float(val)
    except:
        pass
    return 100.0

def safe_get_skill_value():
    try:
        val = Player.GetRealSkillValue("Alchemy")
        if val is not None:
            return float(val)
    except:
        pass

    try:
        val = Player.GetSkillValue("Alchemy")
        if val is not None:
            return float(val)
    except:
        pass

    return 0.0

def ensure_selected_potions_init():
    global _selected_potions, _potion_button_map
    if _selected_potions:
        return
    _potion_button_map = {}
    for cat_name, cat_data in POTIONS.items():
        for p_name in cat_data["potions"].keys():
            if p_name not in _selected_potions:
                _selected_potions[p_name] = False


def get_res_container():
    global _resource_container
    if _resource_container and Items.FindBySerial(_resource_container):
        return _resource_container
    return 0

def get_shelf():
    global _shelf_serial
    if _shelf_serial and Items.FindBySerial(_shelf_serial):
        return _shelf_serial
    return 0

def proper_case(text):
    return " ".join(w.capitalize() for w in (text or "").split())

def close_non_suite_gumps():
    try:
        if Gumps.HasGump():
            pass
    except:
        pass

# ===========================================================
# RESOURCE MANAGEMENT (DO NOT EDIT)
# ===========================================================

def have_reagents_for(potion_name, category_name, batch=1):
    cat = POTIONS.get(category_name, {})
    pdata = cat.get("potions", {}).get(potion_name)
    if not pdata:
        return False
    reqs = pdata.get("reagents", {})
    for reg_name, amount in reqs.items():
        if reg_name not in RESOURCE_IDS:
            continue
        itemid = RESOURCE_IDS[reg_name]
        need = amount * batch
        have = Items.BackpackCount(itemid, -1)
        if have < need:
            return False
    return True

def pull_reagents_for(potion_name, category_name, batch=1):
    global _status_msg
    cont_serial = get_res_container()
    if not cont_serial:
        _status_msg = "Set resource container first."
        return False

    cat = POTIONS.get(category_name, {})
    pdata = cat.get("potions", {}).get(potion_name)
    if not pdata:
        _status_msg = "Potion config missing."
        return False
    reqs = pdata.get("reagents", {})
    for reg_name, amount in reqs.items():
        if reg_name not in RESOURCE_IDS:
            continue
        itemid = RESOURCE_IDS[reg_name]
        need = amount * batch
        have = Items.BackpackCount(itemid, -1)
        if have >= need:
            continue
        missing = need - have
        src = Items.FindByID(itemid, -1, cont_serial, -1, True)
        if not src:
            _status_msg = "Out of {0}".format(reg_name)
            return False
        move_amount = missing
        Items.Move(src, Player.Backpack.Serial, move_amount)
        Misc.Pause(600)
    return True

    
    
# ===========================================================
# ALCHEMY / COMPENDIUM HELPERS (DO NOT EDIT)
# ===========================================================

def ensure_alch_gump_open():
    global _status_msg, _runtime_active

    tool = find_alch_tool()
    if not tool:
        _status_msg = "No Mortar & Pestle found! Add one to backpack or resource chest."
        Misc.SendMessage(_status_msg, 33)
        _runtime_active = False
        return False

    if Gumps.CurrentGump() == ALCH_GUMP_ID:
        return True

    Items.UseItem(tool)
    if Gumps.WaitForGump(ALCH_GUMP_ID, 3000):
        return True

    for g in (0x0E9B, 0x0EFB, 0x0F0E):  #Morter and Pestal Variants backup
        alt = Items.FindByID(g, -1, Player.Backpack.Serial, -1, True)
        if alt:
            Items.UseItem(alt)
            if Gumps.WaitForGump(ALCH_GUMP_ID, 3000):
                return True

    _status_msg = "Failed to open Alchemy gump — no usable tool."
    Misc.SendMessage(_status_msg, 33)
    _runtime_active = False
    return False


def send_alch_action(category_id, button_id):
    if not ensure_alch_gump_open():
        return False
    Gumps.SendAction(ALCH_GUMP_ID, category_id)
    Gumps.WaitForGump(ALCH_GUMP_ID, 1500)
    Misc.Pause(250)
    Gumps.SendAction(ALCH_GUMP_ID, button_id)
    Gumps.WaitForGump(ALCH_GUMP_ID, 1500)
    Misc.Pause(600)
    return True
    
def find_alch_tool():
    tool = Items.FindByID(TOOL_ID, -1, Player.Backpack.Serial)
    if tool:

        return tool

    if _resource_container:
        tool = Items.FindByID(TOOL_ID, -1, _resource_container)
        if tool:
            Items.Move(tool, Player.Backpack.Serial, 1)
            Misc.Pause(600)
            tool = Items.FindByID(TOOL_ID, -1, Player.Backpack.Serial)
            if tool:
                _status_msg = "Fetched Mortar & Pestle from resource chest."
                Misc.SendMessage(_status_msg, 68)
                return tool

    return None

def ensure_alch_tool():
    """
    Ensures there’s a valid Mortar & Pestle available before crafting.
    Returns the tool serial if available, else None.
    """
    tool = find_alch_tool()
    if not tool:
        _status_msg = "No Mortar & Pestle found! Please add one to chest."
        Misc.SendMessage(_status_msg, 33)
        _runtime_active = False
        return None
    return tool    

# ===========================================================
# TRAINING MODE (DO NOT EDIT)
# ===========================================================

def pick_training_potion():
    skill = safe_get_skill_value()
    cap   = safe_get_skill_cap()
    if skill < 50.0:
        return None, None
    for smin, smax, p_name, cat_name in TRAIN_POISON_TIERS:
        if skill >= smin and skill < min(smax, cap + 0.01):
            return cat_name, p_name
    return None, None

def drink_recent_potion(potion_name):
    graphic = POTION_GRAPHICS.get(potion_name, 0)
    bottle = None
    if graphic:
        bottle = Items.FindByID(graphic, -1, Player.Backpack.Serial, -1, True)
    if not bottle:
        f = Items.Filter()
        f.Enabled = True
        f.OnGround = False
        f.RangeMax = 0
        potions = Items.ApplyFilter(f)
        for it in potions:
            bottle = it
            break
    if bottle:
        Items.UseItem(bottle.Serial)
        Misc.Pause(500)

def training_step():
    global _status_msg
    if not TRAINING_ENABLED:
        _status_msg = "Training disabled in config."
        return
    skill = safe_get_skill_value()
    cap   = safe_get_skill_cap()
    if skill < 50.0:
        Player.HeadMessage(33, "Train Alchemy to 50 at an Alchemist NPC first.")
        _status_msg = "Need NPC training to 50."
        return
    if skill >= cap:
        _status_msg = "Alchemy at cap ({0:.1f}).".format(cap)
        return


    global _poison_mastery_warned
    if not _poison_mastery_warned:
        _status_msg = "Training mode active — ensure Poison Mastery is enabled!"
        Misc.SendMessage(_status_msg, 33)
        _poison_mastery_warned = True

    cat_name, p_name = pick_training_potion()
    if not cat_name:
        _status_msg = "No training tier for this skill."
        return

    cat = POTIONS.get(cat_name, {})
    pdata = cat.get("potions", {}).get(p_name)
    if not pdata:
        _status_msg = "Config error for training potion."
        return

    if not pull_reagents_for(p_name, cat_name, batch=1):
        return

    _status_msg = "[{0:.1f}] Training: {1}".format(skill, p_name)
    if not send_alch_action(cat["category_id"], pdata["button_id"]):
        _status_msg = "Alchemy gump/tool not found."
        return

    drink_recent_potion(p_name)

# ===========================================================
# CRAFTING MODE CORE (DO NOT EDIT)
# ===========================================================

def rebuild_craft_queue():
    global _craft_queue, _current_job
    _craft_queue = []
    for cat_name, cat in POTIONS.items():
        for p_name, pdata in cat["potions"].items():
            if not _selected_potions.get(p_name, False):
                continue
            _craft_queue.append([cat_name, p_name, _target_amount])
    _current_job = None

def get_next_job():
    global _craft_queue, _current_job
    while _craft_queue:
        cat_name, p_name, remaining = _craft_queue[0]
        if remaining <= 0:
            _craft_queue.pop(0)
            continue
        _current_job = _craft_queue[0]
        return _current_job
    _current_job = None
    return None

def decrement_job():
    global _current_job
    if not _current_job:
        return
    _current_job[2] -= 1

def generic_craft_one(cat_name, p_name):
    global _status_msg
    cat = POTIONS.get(cat_name, {})
    pdata = cat.get("potions", {}).get(p_name)
    if not pdata:
        _status_msg = "Config error for {0}".format(p_name)
        return False
    if not pull_reagents_for(p_name, cat_name, batch=1):
        return False
    _status_msg = "Crafting {0}".format(p_name)
    return send_alch_action(cat["category_id"], pdata["button_id"])

def add_to_shelf_restock():
    SHELF_GUMP_ID = 0xA8ED56C7
    RESTOCK_BUTTON_ID = 1790
    global _status_msg

    shelf = get_shelf()
    if not shelf:
        _status_msg = "No shelf set."
        return False

    shelf_item = Items.FindBySerial(shelf)
    if not shelf_item:
        _status_msg = "Shelf item missing."
        return False

    potion_ids = list(set(POTION_GRAPHICS.values()))
    potion_target = None
    for pid in potion_ids:
        found = Items.FindByID(pid, -1, Player.Backpack.Serial, -1, True)
        if found:
            potion_target = found
            break
    if not potion_target:
        return False  #

    opened = False
    for attempt in range(3):
        Items.UseItem(shelf_item)
        if Gumps.WaitForGump(SHELF_GUMP_ID, 2500):
            opened = True
            break
        Misc.Pause(100)
    if not opened:
        return False

    restock_ready = False
    for attempt in range(3):
        Gumps.SendAction(SHELF_GUMP_ID, RESTOCK_BUTTON_ID)
        Misc.Pause(200)
        if Target.HasTarget():
            restock_ready = True
            break
        Misc.Pause(100)
    if not restock_ready:
        return False

    Journal.Clear()
    Target.TargetExecute(potion_target.Serial)
    Misc.Pause(100)

    success_text = "You pour the potion into a bottle"
    success = False
    start = time.time()
    while time.time() - start < 2.5:
        if Journal.Search(success_text):
            success = True
            break
        Misc.Pause(150)

    if success:
        Misc.SendMessage(f"Deposited {potion_target.Name}.", 68)
        return True
    return False


def shelf_fill_step():
    global _status_msg

    if not _craft_queue:
        rebuild_craft_queue()

    job = get_next_job()
    if not job:
        _status_msg = "Shelf Fill: done."
        return

    cat_name, p_name, remaining = job

    add_to_shelf_restock()

    if not generic_craft_one(cat_name, p_name):
        return

    decrement_job()
    _status_msg = f"Shelf Fill: {p_name} ({remaining - 1} left)"

def just_potions_step():
    global _status_msg
    if not _craft_queue:
        rebuild_craft_queue()
    job = get_next_job()
    if not job:
        _status_msg = "Just Potions: done."
        return
    cat_name, p_name, remaining = job
    if not generic_craft_one(cat_name, p_name):
        return
    decrement_job()
    _status_msg = "Backpack: {0} ({1} left)".format(p_name, remaining - 1)

def keg_fill_step():
    global _status_msg
    if GM_TINKERING:
        if not _craft_queue:
            rebuild_craft_queue()
        job = get_next_job()
        if not job:
            _status_msg = "Keg Fill (GM): done."
            return
        cat_name, p_name, remaining = job
        if cat_name != "Full Potion Kegs":
            decrement_job()
            return
        if not generic_craft_one(cat_name, p_name):
            return
        decrement_job()
        _status_msg = "Full keg: {0} ({1} left)".format(p_name, remaining - 1)
    else:
        just_potions_step()
        _status_msg = "KegFill (bottle -> keg): {0}".format(_status_msg)

# ===========================================================
# GUI (DO NOT EDIT) (SERIOUSLY DONT) Matter of fact don't even look at it, you'll break it. probably
# ===========================================================

def render_gui():
    ensure_selected_potions_init()

    mode_label = {
        MODE_TRAIN: "Training",
        MODE_SHELF: "Shelf Fill",
        MODE_KEG:   "Keg Fill",
        MODE_JUST:  "Just Potions",
    }.get(_current_mode, "Unknown")

    run_label = "ON" if _runtime_active else "OFF"

    alch_val = safe_get_skill_value()
    alch_cap = safe_get_skill_cap()

    global _potion_button_map
    if not _category_names:
        return
    page_count = len(_category_names)
    current_cat_name = _category_names[_current_page % page_count]
    current_cat = POTIONS[current_cat_name]
    _potion_button_map = {}  

    Gumps.CloseGump(GUMP_ID)
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)

    width  = 420
    height = 340
    Gumps.AddBackground(gd, 0, 0, width, height, 5054)
    Gumps.AddAlphaRegion(gd, 0, 0, width, height)
    Gumps.AddLabel(gd, 130, 5, 68, "Potion Frog Suite v1")

    # Status + skill
    Gumps.AddLabel(gd, 15, 30, 0x480,
                   "Mode: {0}  Run: {1}".format(mode_label, run_label))
    Gumps.AddLabel(gd, 15, 50, 0x44E,
                   "Alchemy: {0:.1f}/{1:.1f}".format(alch_val, alch_cap))
    Gumps.AddLabel(gd, 15, 70, 0x44E,
                   "Status: {0}".format(_status_msg[:40]))

    # Top control buttons
    Gumps.AddButton(gd, 320, 30, 4011, 4012, BTN_TOGGLE_RUN, 1, 0)
    Gumps.AddLabel(gd, 345, 30, 68, "Start/Stop")

    Gumps.AddButton(gd, 320, 55, 4005, 4007, BTN_CLOSE, 1, 0)
    Gumps.AddLabel(gd, 345, 55, 33, "Close")

    # Mode buttons
    Gumps.AddButton(gd, 15, 95, 4005, 4007, BTN_MODE_TRAIN, 1, 0)
    Gumps.AddLabel(gd, 40, 95, 68, "Training")

    Gumps.AddButton(gd, 110, 95, 4005, 4007, BTN_MODE_SHELF, 1, 0)
    Gumps.AddLabel(gd, 135, 95, 68, "Shelf Fill")

    Gumps.AddButton(gd, 220, 95, 4005, 4007, BTN_MODE_KEG, 1, 0)
    Gumps.AddLabel(gd, 245, 95, 68, "Keg Fill")

    Gumps.AddButton(gd, 320, 95, 4005, 4007, BTN_MODE_JUST, 1, 0)
    Gumps.AddLabel(gd, 345, 95, 68, "Just Potions")

    # Resource and shelf buttons
    Gumps.AddButton(gd, 15, 120, 4011, 4012, BTN_SET_RES_CONT, 1, 0)
    Gumps.AddLabel(gd, 45, 120, 68, "Resource Cont")

    Gumps.AddButton(gd, 200, 120, 4011, 4012, BTN_SET_SHELF, 1, 0)
    Gumps.AddLabel(gd, 230, 120, 68, "Shelf")

    # Target amount display only 
    Gumps.AddLabel(gd, 340, 120, 0x44E, "Amt: {0}".format(_target_amount))

    # Category + page controls
    page_label = "Category: {0} ({1}/{2})".format(
        current_cat_name, _current_page + 1, page_count
    )
    Gumps.AddLabel(gd, 15, 145, 0x44E, page_label)

    # page arrows
    Gumps.AddButton(gd, 320, 142, 4014, 4016, BTN_PAGE_PREV, 1, 0)
    Gumps.AddLabel(gd, 340, 145, 0x44E, "<")
    Gumps.AddButton(gd, 360, 142, 4005, 4007, BTN_PAGE_NEXT, 1, 0)
    Gumps.AddLabel(gd, 380, 145, 0x44E, ">")

    # Potion selection grid for current category only
    start_x = 15
    start_y = 170
    row_height = 18
    max_rows = 10

    idx = 0
    for p_name in current_cat["potions"].keys():
        row = idx % max_rows
        col = idx // max_rows  # Not Super needed, fallback/safety net, remove in future update
        x = start_x + col * 190
        y = start_y + row * row_height

        btn_id = BTN_POTION_BASE + idx
        _potion_button_map[btn_id] = (current_cat_name, p_name)

        label_hue = 68 if _selected_potions.get(p_name, False) else 0x44E
        Gumps.AddButton(gd, x, y, 4005, 4007, btn_id, 1, 0)
        Gumps.AddLabel(gd, x + 25, y, label_hue, proper_case(p_name))

        idx += 1

    Gumps.SendGump(GUMP_ID, Player.Serial, GUMP_X, GUMP_Y,
                   gd.gumpDefinition, gd.gumpStrings)


# ===========================================================
# BUTTON HANDLING (DO NOT EDIT)
# ===========================================================

def handle_button(btn):
    global _running, _current_mode, _runtime_active
    global _resource_container, _shelf_serial, _target_amount
    global _craft_queue, _current_job, _status_msg
    global _current_page, _textentry_focus_time

    if btn == BTN_CLOSE:
        _running = False
        return

    if btn == BTN_MODE_TRAIN:
        _current_mode = MODE_TRAIN
        _runtime_active = False
        _craft_queue = []
        _current_job = None
        _status_msg = "Training mode selected."
        return

    if btn == BTN_MODE_SHELF:
        _current_mode = MODE_SHELF
        _runtime_active = False
        _craft_queue = []
        _current_job = None
        _status_msg = "Shelf Fill mode selected."
        return

    if btn == BTN_MODE_KEG:
        _current_mode = MODE_KEG
        _runtime_active = False
        _craft_queue = []
        _current_job = None
        _status_msg = "Keg Fill mode selected."
        return

    if btn == BTN_MODE_JUST:
        _current_mode = MODE_JUST
        _runtime_active = False
        _craft_queue = []
        _current_job = None
        _status_msg = "Just Potions mode selected."
        return

    if btn == BTN_TOGGLE_RUN:
        if not _resource_container or not Items.FindBySerial(_resource_container):
            _runtime_active = False
            _status_msg = "Select a resource container before running!"
            Misc.SendMessage(_status_msg, 33)
            return

        _runtime_active = not _runtime_active
        if _runtime_active:
            _status_msg = "Running..."
            _craft_queue = []
            _current_job = None
        else:
            _status_msg = "Stopped."
        return

    if btn == BTN_SET_RES_CONT:
        Target.Cancel()
        Misc.SendMessage("Target resource container (reagents + bottles).", 55)
        s = Target.PromptTarget("Resource container", 0x3B2)
        if s > 0 and Items.FindBySerial(s):
            _resource_container = s
            Misc.SetSharedValue("alchemyResCont", s)
            _status_msg = "Resource container set."
        else:
            _status_msg = "Invalid container."
        return

    if btn == BTN_SET_SHELF:
        Target.Cancel()
        Misc.SendMessage("Target the potion shelf (0xAFC1).", 55)
        s = Target.PromptTarget("Potion Shelf", 0x3B2)
        it = Items.FindBySerial(s) if s > 0 else None
        if it and it.ItemID == SHELF_ITEM_ID:
            _shelf_serial = s
            Misc.SetSharedValue("potionShelf", s)
            _status_msg = "Shelf set."
        else:
            _status_msg = "Not a valid shelf."
        return

    if btn == BTN_PAGE_PREV:
        if _category_names:
            _current_page = (_current_page - 1) % len(_category_names)
        return

    if btn == BTN_PAGE_NEXT:
        if _category_names:
            _current_page = (_current_page + 1) % len(_category_names)
        return

    ensure_selected_potions_init()
    if btn in _potion_button_map:
        cat_name, p_name = _potion_button_map[btn]
        if p_name in _selected_potions:
            _selected_potions[p_name] = not _selected_potions[p_name]
            _craft_queue = []
            _current_job = None
        return

# ===========================================================
# MAIN LOOP (DO NOT EDIT)
# ===========================================================

Misc.SendMessage("Potion Frog Suite v1 starting...", 68)
Misc.Pause(200)
Gumps.ResetGump()
ensure_selected_potions_init()
render_gui()

_last_button = 0
_click_cache = 0

while _running and Player.Connected:
    gd = Gumps.GetGumpData(GUMP_ID)
    current_button = 0
    if gd and gd.buttonid:
        current_button = gd.buttonid

    if current_button and current_button != _last_button:
        _click_cache = current_button
        Misc.SetSharedValue("AlchySuite_Click", current_button)
        _last_button = current_button

    if Misc.CheckSharedValue("AlchySuite_Click"):
        cached_btn = Misc.ReadSharedValue("AlchySuite_Click")
        if cached_btn:
            Gumps.ResetGump()
            handle_button(cached_btn)
            Misc.RemoveSharedValue("AlchySuite_Click")
            Misc.Pause(150)
            continue

    if _runtime_active:
        if _current_mode == MODE_TRAIN:
            training_step()
        elif _current_mode == MODE_SHELF:
            shelf_fill_step()
        elif _current_mode == MODE_KEG:
            keg_fill_step()
        elif _current_mode == MODE_JUST:
            just_potions_step()
        else:
            _status_msg = "Unknown mode."
    else:
        if _current_mode == MODE_TRAIN and safe_get_skill_value() < 50.0:
            _status_msg = "Train to 50 at NPC first."
        elif not _status_msg:
            _status_msg = "Idle."

    now_ms = int(time.time() * 1000)
    if now_ms - _textentry_focus_time > _textentry_hold_ms:
        render_gui()

    Misc.Pause(REFRESH_MS)

Gumps.CloseGump(GUMP_ID)
Misc.SendMessage("Potion Frog Suite stopped.", 33)
