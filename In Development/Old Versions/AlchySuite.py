# ============================================
# === Potion Frog Suite (Unchained) v1.0   ===
# ============================================
# Author: UO Script Forge + Frogmancer vibes
#
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
#       * Auto-activates Poison Mastery via [compendium.
#       * Crafts only poison-type potions and drinks them immediately
#         to reclaim bottles.
#   - All potion/category/button IDs + reagents are in POTIONS dict below;
#     edit as needed if Unchained changes.
#
# DISCLAIMER:
#   This is a helper tool, not a license to break shard rules.
#   Always check Unchained’s automation/macro policy.
#

from AutoComplete import *
from System import Int32
from System.Collections.Generic import List as CList

# ===========================================================
# CONFIGURATION
# ===========================================================

GUMP_ID    = 0xA110C0DE
REFRESH_MS = 300
GUMP_X, GUMP_Y = 600, 300

ALCH_GUMP_ID      = 0x38920ABD
COMPENDIUM_GUMPID = 0x93069BD5
SHELF_ITEM_ID     = 0xAFC1

# Resource IDs you provided
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
    "Boards":       0x1BD7,
    "Ingots":       0x1BF2,
}

# Rough OSI-style potion itemIDs – adjust for Unchained if needed
POTION_GRAPHICS = {
    # Healing & Curative
    "Refresh":                0x0F0B,   # guess
    "Greater Refreshment":    0x0F0C,   # guess
    "Lesser Heal":            0x0F0C,   # standard heal bottle IDs may overlap
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
    "Mana Potion":            0x0F09,   # these are guesses; tune per shard
    "Total Mana Potion":      0x0F09,
    "Invisibility":           0x0F0E,   # special, often same bottle
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
    # Misc / Strange Brew
    "smoke bomb":             0x0F0E,
}

# Main potion dictionary with categories, button IDs, reagents, skill requirements
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
                    "Eye of Newt": 800,  # logical name; not in RESOURCE_IDS
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
                # the sheet called this "Greater Explo" in text row
                "button_id": 58,   # mapped from "Greater Explo" row
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
                "button_id": 23,
                "alchemy": 55,
                "reagents": {"Empty Bottle": 1, "Nightshade": 4},
            },
            "Deadly Poison": {
                "button_id": 30,
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

# Training configuration
GM_TINKERING       = False  # if True: use full kegs when in Keg mode
TRAINING_ENABLED   = True
TRAIN_POISON_TIERS = [
    # skill_min, skill_max, potion_name, category_name
    (50.0, 75.0, "Lesser Poison", "Toxic"),
    (75.0, 90.0, "Poison",        "Toxic"),
    (90.0, 200.0, "Greater Poison", "Toxic"),  # up to cap
]

# ===========================================================
# GLOBAL STATE
# ===========================================================

MODE_TRAIN   = 1
MODE_SHELF   = 2
MODE_KEG     = 3
MODE_JUST    = 4

_running          = True
_runtime_active   = False
_current_mode     = MODE_TRAIN
_status_msg       = "Idle"

_resource_container = Misc.ReadSharedValue("alchemyResCont") if Misc.CheckSharedValue("alchemyResCont") else 0
_shelf_serial       = Misc.ReadSharedValue("potionShelf")   if Misc.CheckSharedValue("potionShelf")   else 0

# selected potions for shelf/just/keg
_selected_potions = {}  # name -> bool
_target_amount    = 100  # shared amount for each selected potion

_poison_mastery_done = False

# crafting progress
_craft_queue = []   # list of (category_name, potion_name, remaining)
_current_job = None # current tuple or None

# ===========================================================
# BUTTON IDS
# ===========================================================

BTN_CLOSE          = 9000
BTN_MODE_TRAIN     = 9001
BTN_MODE_SHELF     = 9002
BTN_MODE_KEG       = 9003
BTN_MODE_JUST      = 9004
BTN_TOGGLE_RUN     = 9005
BTN_SET_RES_CONT   = 9006
BTN_SET_SHELF      = 9007

BTN_POTION_BASE    = 10000  # + index per potion in listing
# We’ll store a mapping index->(category, potion)
_potion_button_map = {}

# ===========================================================
# SMALL HELPERS
# ===========================================================

def safe_get_skill_cap():
    try:
        return Skills.Alchemy.Cap
    except:
        return 100.0

def safe_get_skill_value():
    try:
        return Skills.Alchemy.Value
    except:
        return 0.0

def ensure_selected_potions_init():
    global _selected_potions, _potion_button_map
    if _selected_potions:
        return
    idx = 0
    for cat_name, cat_data in POTIONS.items():
        for p_name in cat_data["potions"].keys():
            if p_name not in _selected_potions:
                _selected_potions[p_name] = False
            _potion_button_map[BTN_POTION_BASE + idx] = (cat_name, p_name)
            idx += 1

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
    # Close all gumps except our suite gump and Alchemy & Compendium
    try:
        if Gumps.HasGump():
            # We don't have direct enumeration, but safe to close unknown IDs by Reset / CloseCurrent pattern
            # We'll keep our gump by re-sending after.
            pass
    except:
        pass

# ===========================================================
# RESOURCE MANAGEMENT
# ===========================================================

def have_reagents_for(potion_name, category_name, batch=1):
    cat = POTIONS.get(category_name, {})
    pdata = cat.get("potions", {}).get(potion_name)
    if not pdata:
        return False
    reqs = pdata.get("reagents", {})
    for reg_name, amount in reqs.items():
        if reg_name not in RESOURCE_IDS:
            # unknown type (Eye of Newt, Wyrms Heart, Eggs etc.)
            # assume user provided separately; try to find by name in properties
            # we can't handle this generically without IDs, so just assume present
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
# ALCHEMY / COMPENDIUM HELPERS
# ===========================================================

def ensure_alch_gump_open():
    # if Alchemy gump is open already, done
    if Gumps.CurrentGump() == ALCH_GUMP_ID:
        return True
    # try to find mortar/pestle in backpack
    for g in (0x0E9B, 0x0F0E, 0x0EFB):  # typical tool IDs, adjust as needed
        tool = Items.FindByID(g, -1, Player.Backpack.Serial, -1, True)
        if tool:
            Items.UseItem(tool)
            if Gumps.WaitForGump(ALCH_GUMP_ID, 3000):
                return True
    # fallback: if gump opens some other way (hotkey, etc.)
    if Gumps.WaitForGump(ALCH_GUMP_ID, 1000):
        return True
    return False

def send_alch_action(category_id, button_id):
    if not ensure_alch_gump_open():
        return False
    # select category, then specific potion button
    Gumps.SendAction(ALCH_GUMP_ID, category_id)
    Gumps.WaitForGump(ALCH_GUMP_ID, 1500)
    Misc.Pause(250)
    Gumps.SendAction(ALCH_GUMP_ID, button_id)
    Gumps.WaitForGump(ALCH_GUMP_ID, 1500)
    Misc.Pause(600)
    return True

def ensure_poison_mastery():
    global _poison_mastery_done, _status_msg
    if _poison_mastery_done:
        return
    _status_msg = "Switching mastery to Poison..."
    try:
        Player.ChatSay(0, "[compendium")
    except:
        Player.HeadMessage(33, "Unable to send [compendium. Set mastery manually.")
        _poison_mastery_done = True
        return
    if not Gumps.WaitForGump(COMPENDIUM_GUMPID, 5000):
        _status_msg = "Compendium gump not found; set mastery manually."
        _poison_mastery_done = True
        return
    # button 2 = Alchemy page, button 8 = Poison Mastery (per your notes)
    Gumps.SendAction(COMPENDIUM_GUMPID, 2)
    Gumps.WaitForGump(COMPENDIUM_GUMPID, 2000)
    Misc.Pause(300)
    Gumps.SendAction(COMPENDIUM_GUMPID, 8)
    Gumps.WaitForGump(COMPENDIUM_GUMPID, 2000)
    Misc.Pause(300)
    Gumps.CloseGump(COMPENDIUM_GUMPID)
    _status_msg = "Poison Mastery enabled (immune to poison)."
    _poison_mastery_done = True

# ===========================================================
# TRAINING MODE
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
    # Try to drink by assumed graphic ID first
    graphic = POTION_GRAPHICS.get(potion_name, 0)
    bottle = None
    if graphic:
        bottle = Items.FindByID(graphic, -1, Player.Backpack.Serial, -1, True)
    if not bottle:
        # fallback: drink any potion in backpack
        f = Items.Filter()
        f.Enabled = True
        f.IsPotion = True
        f.OnGround = False
        f.RangeMax = 0
        potions = Items.ApplyFilter(f)
        for it in potions:
            bottle = it
            break
    if bottle:
        Misc.DoubleClick(bottle.Serial)
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

    ensure_poison_mastery()

    cat_name, p_name = pick_training_potion()
    if not cat_name:
        _status_msg = "No training tier for this skill."
        return

    cat = POTIONS.get(cat_name, {})
    pdata = cat.get("potions", {}).get(p_name)
    if not pdata:
        _status_msg = "Config error for training potion."
        return

    # Pull reagents
    if not pull_reagents_for(p_name, cat_name, batch=1):
        # pull_reagents_for sets status_msg
        return

    # Craft one
    _status_msg = "[{0:.1f}] Training: {1}".format(skill, p_name)
    if not send_alch_action(cat["category_id"], pdata["button_id"]):
        _status_msg = "Alchemy gump/tool not found."
        return

    # Drink it immediately to reclaim bottle
    drink_recent_potion(p_name)

# ===========================================================
# SHELF / KEG / JUST POTIONS MODE CORE
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

def add_to_shelf():
    shelf = get_shelf()
    if not shelf:
        return False
    shelf_item = Items.FindBySerial(shelf)
    if not shelf_item:
        return False
    # open context menu "Add" then target a potion in backpack
    Misc.ContextReply(shelf_item.Serial, "Add")
    if not Target.WaitForTarget(2000, False):
        return False
    # target any potion
    f = Items.Filter()
    f.Enabled = True
    f.IsPotion = True
    f.OnGround = False
    f.RangeMax = 0
    pots = Items.ApplyFilter(f)
    if not pots:
        return False
    Target.TargetExecute(pots[0].Serial)
    Misc.Pause(600)
    return True

def shelf_fill_step():
    global _status_msg
    if not _craft_queue:
        rebuild_craft_queue()
    job = get_next_job()
    if not job:
        _status_msg = "Shelf Fill: done."
        return
    cat_name, p_name, remaining = job
    if not generic_craft_one(cat_name, p_name):
        return
    # move crafted potion(s) into shelf using context "Add"
    add_to_shelf()
    decrement_job()
    _status_msg = "Shelf: {0} ({1} left)".format(p_name, remaining - 1)

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
    # Minimal implementation: craft batch into backpack, rely on shard’s keg behavior
    if GM_TINKERING:
        # Use Full Potion Kegs recipes when available
        if not _craft_queue:
            rebuild_craft_queue()
        job = get_next_job()
        if not job:
            _status_msg = "Keg Fill (GM): done."
            return
        cat_name, p_name, remaining = job
        if cat_name != "Full Potion Kegs":
            # skip non-keg entries if selected
            decrement_job()
            return
        if not generic_craft_one(cat_name, p_name):
            return
        decrement_job()
        _status_msg = "Full keg: {0} ({1} left)".format(p_name, remaining - 1)
    else:
        # Non-GM tinkering: we just make 100 of each selected single potion,
        # relying on having a keg in backpack so Unchained auto-fills it.
        just_potions_step()
        _status_msg = "KegFill (bottle -> keg): {0}".format(_status_msg)

# ===========================================================
# GUI
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

    # flatten potion names for grid
    pot_names = sorted(_selected_potions.keys(), key=str.lower)

    Gumps.CloseGump(GUMP_ID)
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)

    width  = 420
    height = 340
    Gumps.AddBackground(gd, 0, 0, width, height, 5054)
    Gumps.AddAlphaRegion(gd, 0, 0, width, height)
    Gumps.AddLabel(gd, 120, 5, 68, "Potion Frog Suite v1")

    # Status + skill
    alch_val = safe_get_skill_value()
    alch_cap = safe_get_skill_cap()
    Gumps.AddLabel(gd, 15, 30, 0x480,
                   "Mode: {0}  Run: {1}".format(mode_label, run_label))
    Gumps.AddLabel(gd, 15, 50, 0x44E,
                   "Alchemy: {0:.1f}/{1:.1f}".format(alch_val, alch_cap))
    Gumps.AddLabel(gd, 15, 70, 0x44E, "Status: {0}".format(_status_msg[:40]))

    # Top control buttons
    Gumps.AddButton(gd, 320, 30, 4011, 4012, BTN_TOGGLE_RUN, 1, 0)
    Gumps.AddLabel(gd, 345, 30, 68, "Start/Stop")

    Gumps.AddButton(gd, 320, 55, 4005, 4007, BTN_CLOSE, 1, 0)
    Gumps.AddLabel(gd, 345, 55, 33, "Close")

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

    # Target amount entry
    Gumps.AddLabel(gd, 320, 120, 0x44E, "Amt:")
    Gumps.AddTextEntry(gd, 350, 118, 50, 20, 0x480, 1, str(_target_amount))

    # Potion selection grid
    start_x = 15
    start_y = 150
    col_width = 190
    row_height = 18
    max_rows = 8

    idx = 0
    for name in pot_names:
        col = idx // max_rows
        row = idx % max_rows
        x = start_x + col * col_width
        y = start_y + row * row_height
        btn_id = [k for k, v in _potion_button_map.items() if v[1] == name]
        if btn_id:
            bid = btn_id[0]
        else:
            bid = BTN_POTION_BASE + idx
            _potion_button_map[bid] = ("", name)
        label_hue = 68 if _selected_potions.get(name, False) else 0x44E
        Gumps.AddButton(gd, x, y, 4005, 4007, bid, 1, 0)
        Gumps.AddLabel(gd, x + 25, y, label_hue, proper_case(name))
        idx += 1

    Gumps.SendGump(GUMP_ID, Player.Serial, GUMP_X, GUMP_Y, gd.gumpDefinition, gd.gumpStrings)

# ===========================================================
# BUTTON HANDLING
# ===========================================================

def handle_button(btn):
    global _running, _current_mode, _runtime_active
    global _resource_container, _shelf_serial, _target_amount
    global _craft_queue, _current_job, _status_msg

    # Reset craft queue when changing modes or toggles
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

    # Potion toggles
    ensure_selected_potions_init()
    if btn in _potion_button_map:
        cat_name, p_name = _potion_button_map[btn]
        if p_name in _selected_potions:
            _selected_potions[p_name] = not _selected_potions[p_name]
            _craft_queue = []
            _current_job = None
        return

    # TextEntry for target amount
    gd = Gumps.GetGumpData(GUMP_ID)
    if gd:
        entries = []
        if hasattr(gd, "textentries"):
            entries = gd.textentries
        elif hasattr(gd, "textentry"):
            entries = gd.textentry
        elif hasattr(gd, "TextEntries"):
            entries = gd.TextEntries
        for te in entries:
            try:
                entry_id = getattr(te, "entryID", getattr(te, "EntryID", 0))
                text_val = getattr(te, "text", getattr(te, "Text", ""))
                if entry_id == 1:
                    val = int(text_val)
                    if val > 0:
                        _target_amount = val
                    break
            except:
                continue

# ===========================================================
# MAIN LOOP
# ===========================================================

Misc.SendMessage("Potion Frog Suite v1 starting...", 68)
Misc.Pause(200)
Gumps.ResetGump()
ensure_selected_potions_init()
render_gui()

while _running and Player.Connected:
    gd = Gumps.GetGumpData(GUMP_ID)
    btn = gd.buttonid if gd else 0

    if btn:
        Gumps.ResetGump()
        handle_button(btn)
        Misc.Pause(200)

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

    render_gui()
    Misc.Pause(REFRESH_MS)

Gumps.CloseGump(GUMP_ID)
Misc.SendMessage("Potion Frog Suite stopped.", 33)
