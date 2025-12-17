# ==================================
# ==  Inscription Suite/Trainer   ==
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


from System import Int32
import time

# ===========================================================
# Settings
# ===========================================================

_target_amount = 100 #TGTAMT: Change this to desired batch craft amount
PULL_SCROLL_BUFFER = 1 # How many scrolls it'll keep stocked
PULL_REAGENT_BUFFER = 1 # AMT to keep in bag. It'll stay full
FILL_ALL_BOOKS = True  # Set to "True" to fill all books in the book container

# Training Path (Initial buy from vendor, this was designed to keep usable scrolls after training)
TRAINING_TABLE = [
    (50.0, None),
    (65.0, "Recall"),
    (85.5, "Mark"),
    (100., "Gate Travel"),
]

# Search (DRDL) if you're receiving "You must wait a moment to do that" and set the wait higher


# ===========================================================
# CONFIGURATION (DO NOT EDIT)
# ===========================================================

GUMP_ID    = 0xA110C0DF
REFRESH_MS = 300
GUMP_X, GUMP_Y = 600, 300

SCRIBE_GUMP_ID = 0x38920ABD
NEXT_PAGE_BTN  = 105

BLANK_SCROLL_ID = 0x0EF3
SCRIBE_PEN_ID   = 0x0FBF

# ===========================================================
# GLOBAL STATE
# ===========================================================

_running        = True
_runtime_craft  = False
_runtime_train  = False
_status_msg     = "Idle"
_status_hue = 0x44E

resource_chest  = 0
selected_spell  = None
craft_quantity  = 1

# ===========================================================
# REAGENT IDS
# ===========================================================

REAGENT_IDS = {
    "Garlic": 0x0F84,
    "Ginseng": 0x0F85,
    "Mandrake Root": 0x0F86,
    "Bloodmoss": 0x0F7B,
    "Spiders Silk": 0x0F8D,
    "Sulfurous Ash": 0x0F8C,
    "Nightshade": 0x0F88,
    "Black Pearl": 0x0F7A,
}

# ===========================================================
# SCROLL ITEM IDS 
# ===========================================================

SCROLL_IDS = {
    "Reactive Armor": 0x1F2D,
    "Clumsy": 0x1F2E,
    "Create Food": 0x1F2F,
    "Feeblemind": 0x1F30,
    "Heal": 0x1F31,
    "Magic Arrow": 0x1F32,
    "Night Sight": 0x1F33,
    "Weaken": 0x1F34,
    "Agility": 0x1F35,
    "Cunning": 0x1F36,
    "Cure": 0x1F37,
    "Harm": 0x1F38,
    "Magic Trap": 0x1F39,
    "Magic Untrap": 0x1F3A,
    "Protection": 0x1F3B,
    "Strength": 0x1F3C,
    "Bless": 0x1F3D,
    "Fireball": 0x1F3E,
    "Magic Lock": 0x1F3F,
    "Poison": 0x1F40,
    "Telekinesis": 0x1F41,
    "Teleport": 0x1F42,
    "Unlock": 0x1F43,
    "Wall of Stone": 0x1F44,
    "Arch Cure": 0x1F45,
    "Arch Protection": 0x1F46,
    "Curse": 0x1F47,
    "Fire Field": 0x1F48,
    "Greater Heal": 0x1F49,
    "Lightning": 0x1F4A,
    "Mana Drain": 0x1F4B,
    "Recall": 0x1F4C,
    "Blade Spirits": 0x1F4D,
    "Dispel Field": 0x1F4E,
    "Incognito": 0x1F4F,
    "Magic Reflection": 0x1F50,
    "Mind Blast": 0x1F51,
    "Paralyze": 0x1F52,
    "Poison Field": 0x1F53,
    "Summon Creature": 0x1F54,
    "Dispel": 0x1F55,
    "Energy Bolt": 0x1F56,
    "Explosion": 0x1F57,
    "Invisibility": 0x1F58,
    "Mark": 0x1F59,
    "Mass Curse": 0x1F5A,
    "Paralyze Field": 0x1F5B,
    "Reveal": 0x1F5C,
    "Chain Lightning": 0x1F5D,
    "Energy Field": 0x1F5E,
    "Flamestrike": 0x1F5F,
    "Gate Travel": 0x1F60,
    "Mana Vampire": 0x1F61,
    "Mass Dispel": 0x1F62,
    "Meteor Swarm": 0x1F63,
    "Polymorph": 0x1F64,
    "Earthquake": 0x1F65,
    "Energy Vortex": 0x1F66,
    "Resurrection": 0x1F67,
    "Summon Air Elemental": 0x1F68,
    "Summon Daemon": 0x1F69,
    "Summon Earth Elemental": 0x1F6A,
    "Summon Fire Elemental": 0x1F6B,
    "Summon Water Elemental": 0x1F6C,
}

# ===========================================================
# SPELL DEFINITIONS FOR GUMP INTERACTION
# ===========================================================

SELECTION_BUTTONS = [2, 9, 16, 23, 30, 37, 44, 51, 58, 65, 72, 79, 86, 93, 100, 107]

CATEGORY_NAMES = [
    "First - Second Circle",
    "Third - Fourth Circle",
    "Fifth - Sixth Circle",
    "Seventh - Eighth Circle",
]

CATEGORY_IDS = {
    "First - Second Circle": 1,
    "Third - Fourth Circle": 8,
    "Fifth - Sixth Circle": 15,
    "Seventh - Eighth Circle": 22,
}

# Ingredients per spell
SPELL_REAGENTS = {
    # Circles 1-2
    "Reactive Armor": {"Garlic":1, "Spiders Silk":1, "Sulfurous Ash":1},
    "Clumsy": {"Bloodmoss":1, "Nightshade":1},
    "Create Food": {"Garlic":1, "Ginseng":1, "Mandrake Root":1},
    "Feeblemind": {"Nightshade":1, "Ginseng":1},
    "Heal": {"Garlic":1, "Ginseng":1, "Spiders Silk":1},
    "Magic Arrow": {"Sulfurous Ash":1},
    "Night Sight": {"Spiders Silk":1, "Sulfurous Ash":1},
    "Weaken": {"Garlic":1, "Nightshade":1},
    "Agility": {"Bloodmoss":1, "Mandrake Root":1},
    "Cunning": {"Nightshade":1, "Mandrake Root":1},
    "Cure": {"Garlic":1, "Ginseng":1},
    "Harm": {"Nightshade":1, "Spiders Silk":1},
    "Magic Trap": {"Garlic":1, "Spiders Silk":1, "Sulfurous Ash":1},
    "Magic Untrap": {"Bloodmoss":1, "Sulfurous Ash":1},
    "Protection": {"Garlic":1, "Ginseng":1, "Sulfurous Ash":1},
    "Strength": {"Mandrake Root":1, "Nightshade":1},

    # Circles 3-4
    "Bless": {"Garlic":1, "Mandrake Root":1},
    "Fireball": {"Black Pearl":1},
    "Magic Lock": {"Bloodmoss":1, "Garlic":1, "Sulfurous Ash":1},
    "Poison": {"Nightshade":1},
    "Telekinesis": {"Bloodmoss":1, "Mandrake Root":1},
    "Teleport": {"Bloodmoss":1, "Mandrake Root":1},
    "Unlock": {"Bloodmoss":1, "Sulfurous Ash":1},
    "Wall of Stone": {"Bloodmoss":1, "Garlic":1},
    "Arch Cure": {"Garlic":1, "Ginseng":1, "Mandrake Root":1},
    "Arch Protection": {"Garlic":1, "Ginseng":1, "Mandrake Root":1, "Sulfurous Ash":1},
    "Curse": {"Garlic":1, "Nightshade":1, "Sulfurous Ash":1},
    "Fire Field": {"Black Pearl":1, "Spiders Silk":1, "Sulfurous Ash":1},
    "Greater Heal": {"Garlic":1, "Ginseng":1, "Mandrake Root":1, "Spiders Silk":1},
    "Lightning": {"Mandrake Root":1, "Sulfurous Ash":1},
    "Mana Drain": {"Black Pearl":1, "Mandrake Root":1, "Spiders Silk":1},
    "Recall": {"Black Pearl":1, "Bloodmoss":1, "Mandrake Root":1},

    # Circles 5-6
    "Blade Spirits": {"Black Pearl":1, "Mandrake Root":1, "Nightshade":1},
    "Dispel Field": {"Black Pearl":1, "Garlic":1, "Spiders Silk":1, "Sulfurous Ash":1},
    "Incognito": {"Bloodmoss":1, "Garlic":1, "Nightshade":1},
    "Magic Reflection": {"Garlic":1, "Mandrake Root":1, "Spiders Silk":1},
    "Mind Blast": {"Black Pearl":1, "Mandrake Root":1, "Nightshade":1, "Sulfurous Ash":1},
    "Paralyze": {"Garlic":1, "Mandrake Root":1, "Spiders Silk":1},
    "Poison Field": {"Black Pearl":1, "Nightshade":1, "Spiders Silk":1},
    "Summon Creature": {"Bloodmoss":1, "Mandrake Root":1, "Spiders Silk":1},
    "Dispel": {"Garlic":1, "Mandrake Root":1, "Sulfurous Ash":1},
    "Energy Bolt": {"Black Pearl":1, "Nightshade":1},
    "Explosion": {"Bloodmoss":1, "Mandrake Root":1},
    "Invisibility": {"Bloodmoss":1, "Nightshade":1},
    "Mark": {"Black Pearl":1, "Bloodmoss":1, "Mandrake Root":1},
    "Mass Curse": {"Garlic":1, "Mandrake Root":1, "Nightshade":1, "Sulfurous Ash":1},
    "Paralyze Field": {"Black Pearl":1, "Ginseng":1, "Spiders Silk":1},
    "Reveal": {"Bloodmoss":1, "Sulfurous Ash":1},

    # Circles 7-8
    "Chain Lightning": {"Black Pearl":1, "Bloodmoss":1, "Mandrake Root":1, "Sulfurous Ash":1},
    "Energy Field": {"Black Pearl":1, "Mandrake Root":1, "Spiders Silk":1, "Sulfurous Ash":1},
    "Flamestrike": {"Spiders Silk":1, "Sulfurous Ash":1},
    "Gate Travel": {"Black Pearl":1, "Mandrake Root":1, "Sulfurous Ash":1},
    "Mana Vampire": {"Black Pearl":1, "Bloodmoss":1, "Mandrake Root":1, "Spiders Silk":1},
    "Mass Dispel": {"Black Pearl":1, "Garlic":1, "Mandrake Root":1, "Sulfurous Ash":1},
    "Meteor Swarm": {"Bloodmoss":1, "Mandrake Root":1, "Spiders Silk":1, "Sulfurous Ash":1},
    "Polymorph": {"Bloodmoss":1, "Mandrake Root":1, "Spiders Silk":1},
    "Earthquake": {"Bloodmoss":1, "Ginseng":1, "Mandrake Root":1, "Sulfurous Ash":1},
    "Energy Vortex": {"Black Pearl":1, "Bloodmoss":1, "Mandrake Root":1, "Nightshade":1},
    "Resurrection": {"Bloodmoss":1, "Ginseng":1, "Garlic":1},
    "Summon Air Elemental": {"Bloodmoss":1, "Mandrake Root":1, "Spiders Silk":1},
    "Summon Daemon": {"Bloodmoss":1, "Mandrake Root":1, "Spiders Silk":1, "Sulfurous Ash":1},
    "Summon Earth Elemental": {"Bloodmoss":1, "Mandrake Root":1, "Spiders Silk":1},
    "Summon Fire Elemental": {"Bloodmoss":1, "Mandrake Root":1, "Spiders Silk":1, "Sulfurous Ash":1},
    "Summon Water Elemental": {"Bloodmoss":1, "Mandrake Root":1, "Spiders Silk":1},
}

# ===========================================================
# SPELLS BY CIRCLE (FOR PAGINATION)
# ===========================================================

SPELLS_BY_CIRCLE = {
    1: ["Reactive Armor","Clumsy","Create Food","Feeblemind","Heal","Magic Arrow","Night Sight","Weaken"],
    2: ["Agility","Cunning","Cure","Harm","Magic Trap","Magic Untrap","Protection","Strength"],
    3: ["Bless","Fireball","Magic Lock","Poison","Telekinesis","Teleport","Unlock","Wall of Stone"],
    4: ["Arch Cure","Arch Protection","Curse","Fire Field","Greater Heal","Lightning","Mana Drain","Recall"],
    5: ["Blade Spirits","Dispel Field","Incognito","Magic Reflection","Mind Blast","Paralyze","Poison Field","Summon Creature"],
    6: ["Dispel","Energy Bolt","Explosion","Invisibility","Mark","Mass Curse","Paralyze Field","Reveal"],
    7: ["Chain Lightning","Energy Field","Flamestrike","Gate Travel","Mana Vampire","Mass Dispel","Meteor Swarm","Polymorph"],
    8: ["Earthquake","Energy Vortex","Resurrection","Summon Air Elemental","Summon Daemon","Summon Earth Elemental","Summon Fire Elemental","Summon Water Elemental"],
}

CATEGORY_SPELLS = {
    "First - Second Circle": SPELLS_BY_CIRCLE[1] + SPELLS_BY_CIRCLE[2],
    "Third - Fourth Circle": SPELLS_BY_CIRCLE[3] + SPELLS_BY_CIRCLE[4],
    "Fifth - Sixth Circle": SPELLS_BY_CIRCLE[5] + SPELLS_BY_CIRCLE[6],
    "Seventh - Eighth Circle": SPELLS_BY_CIRCLE[7] + SPELLS_BY_CIRCLE[8],
}

SPELL_CATEGORIES = {}
for cat_name, spells in CATEGORY_SPELLS.items():
    SPELL_CATEGORIES[cat_name] = {"category_id": CATEGORY_IDS[cat_name], "spells": {}}
    for i, spell_name in enumerate(spells):
        SPELL_CATEGORIES[cat_name]["spells"][spell_name] = {
            "button": SELECTION_BUTTONS[i],
            "reagents": SPELL_REAGENTS.get(spell_name, {}),
        }

# ===========================================================
# HELPER FUNCTIONS (THE GOODS)
# ===========================================================

def count_item(container, itemid):
    return Items.ContainerCount(container, itemid, -1, True)

def ensure_scribe_gump():
    global SCRIBE_GUMP_ID
    pen = Items.FindByID(SCRIBE_PEN_ID, -1, Player.Backpack.Serial)
    if not pen:
        if not pull_from_resource_chest(SCRIBE_PEN_ID, 1):
            _status_msg = "No scribe pen found"
            _status_hue = 33
            return False
        pen = Items.FindByID(SCRIBE_PEN_ID, -1, Player.Backpack.Serial)
        if not pen:
            return False
    Items.UseItem(pen)
    if Gumps.WaitForGump(0, 1500):
        SCRIBE_GUMP_ID = Gumps.CurrentGump()
        return True
    return False

def craft_spell(spell_name, spell_def, qty):
    global _status_msg, _status_hue

    scroll_id = SCROLL_IDS[spell_name]

    category_id = None
    for cat in SPELL_CATEGORIES.values():
        if spell_name in cat["spells"]:
            category_id = cat["category_id"]
            break

    if category_id is None:
        _status_msg = f"No category for {spell_name}"
        _status_hue = 33
        return False

    for _ in range(qty):
        pre = count_item(Player.Backpack.Serial, scroll_id)

        if not ensure_scribe_gump():
            return False

        for _i in range(2):
            Gumps.SendAction(SCRIBE_GUMP_ID, category_id)
            Gumps.WaitForGump(SCRIBE_GUMP_ID, 1500)
            Misc.Pause(350)

        Gumps.SendAction(SCRIBE_GUMP_ID, spell_def["button"])
        Gumps.WaitForGump(SCRIBE_GUMP_ID, 2000)
        Misc.Pause(450)

        gd = Gumps.GetGumpData(SCRIBE_GUMP_ID)
        gump_text = " ".join([s.lower() for s in gd.gumpStrings]) if gd and gd.gumpStrings else ""

        post = count_item(Player.Backpack.Serial, scroll_id)

        success = False

        if post > pre:
            success = True
        else:
            if "inscribe the spell" in gump_text:
                success = True
            elif "fail to inscribe" in gump_text:
                success = False
            else:
                Misc.Pause(400)
                post2 = count_item(Player.Backpack.Serial, scroll_id)
                if post2 > pre:
                    success = True

        if success:
            scroll = Items.FindByID(scroll_id, -1, Player.Backpack.Serial)
            if scroll and _current_mode != MODE_FULLBOOK:
                Items.Move(scroll, resource_chest, 0)
            _status_msg = f"Crafted {spell_name}"
            _status_hue = 68
        else:
            _status_msg = f"Failed {spell_name}"
            _status_hue = 33
            Gumps.CloseGump(SCRIBE_GUMP_ID)
            Misc.Pause(250)
            return False

        Gumps.CloseGump(SCRIBE_GUMP_ID)
        Misc.Pause(250)

    return True

def pull_from_resource_chest(item_id, amount, retries=6):
    if not resource_chest:
        return False

    for attempt in range(1, retries + 1):
        Items.UseItem(resource_chest)
        Misc.Pause(500)

        have = Items.ContainerCount(Player.Backpack.Serial, item_id, -1, True)
        refill_threshold = max(1, amount // 2)
        if have >= refill_threshold:
            return True

        need = amount - have
        src = Items.FindByID(item_id, -1, resource_chest)
        if not src:
            Misc.Pause(500)
            continue

        move_amt = min(src.Amount, need)
        Items.Move(src, Player.Backpack.Serial, move_amt)
        Misc.Pause(900)  # item drag delay (DRDL)

        if Items.ContainerCount(Player.Backpack.Serial, item_id, -1, True) >= amount:
            return True

        Misc.Pause(500)

    return False

# ===========================================================
# BATCH CRAFTING LOGIC
# ===========================================================

def run_batch_crafting():
    global _status_msg

    if not resource_chest:
        _status_msg = "No resource chest set."
        return

    spells = [s for s in SPELLS_BY_CIRCLE.get(_current_circle, []) if _selected_spells.get(s)]
    if not spells:
        _status_msg = "No spells selected."
        return

    for spell in spells:
        spell_def = None
        for cat in SPELL_CATEGORIES.values():
            if spell in cat["spells"]:
                spell_def = cat["spells"][spell]
                break

        for i in range(_target_amount):
            if not pull_from_resource_chest(BLANK_SCROLL_ID, PULL_SCROLL_BUFFER):
                _status_msg = "Out of blank scrolls."
                return

            for reg, amt in spell_def["reagents"].items():
                reg_id = REAGENT_IDS.get(reg)
                if not reg_id:
                    continue
                if not pull_from_resource_chest(reg_id, max(amt, PULL_REAGENT_BUFFER)):
                    _status_msg = f"Out of {reg}."
                    return

            _status_msg = f"Crafting {spell} ({i+1}/{_target_amount})"
            craft_spell(spell, spell_def, 1)

    _status_msg = "Batch complete."

# ===========================================================
# TRAINING PATH LOGIC
# ===========================================================

def get_training_entry(skill_val):
    for cap, spell in TRAINING_TABLE:
        if skill_val < cap:
            return cap, spell
    return None, None

def run_training():
    global _status_msg, _status_hue, _runtime_active

    if not resource_chest:
        _status_msg = "No resource chest set."
        _status_hue = 33
        return

    skill_before = Player.GetSkillValue("Inscription")
    cap, spell_name = get_training_entry(skill_before)

    if spell_name is None:
        _status_msg = "Train to 50 at the NPC, Bring 500 gp."
        _status_hue = 33
        _runtime_active = False
        return

    spell_def = None
    for cat in SPELL_CATEGORIES.values():
        if spell_name in cat["spells"]:
            spell_def = cat["spells"][spell_name]
            break

    if not spell_def:
        _status_msg = f"Training spell not found: {spell_name}"
        _status_hue = 33
        _runtime_active = False
        return

    if not pull_from_resource_chest(BLANK_SCROLL_ID, PULL_SCROLL_BUFFER):
        _status_msg = "Out of blank scrolls."
        _status_hue = 33
        _runtime_active = False
        return  

    for reg, amt in spell_def["reagents"].items():
        reg_id = REAGENT_IDS.get(reg)
        if not reg_id:
            continue
        if not pull_from_resource_chest(reg_id, max(amt, PULL_REAGENT_BUFFER)):
            _status_msg = f"Out of {reg}."
            _status_hue = 33
            _runtime_active = False
            return

    craft_spell(spell_name, spell_def, 1)

    skill_after = Player.GetSkillValue("Inscription")

    _status_msg = f"Training {spell_name}: {skill_before:.1f} -> {skill_after:.1f} / {cap:.1f}"
    _status_hue = 68 if skill_after > skill_before else 33

    if skill_after >= cap:
        _status_msg = f"Advanced training tier at {skill_after:.1f}. Set new spell."
        _status_hue = 68

# ===========================================================
# FULL BOOK LOGIC
# ===========================================================

empty_book_container = 0
_active_spellbook = 0

MAX_FULLBOOK_RETRIES = 5

def get_spell_count(book):
    props = Items.GetPropStringList(book)
    for line in props:
        l = line.lower()
        if "spell" in l:
            digits = ''.join(c for c in l if c.isdigit())
            if digits:
                return int(digits)
    return 0

def find_target_spellbook():
    if not empty_book_container:
        return None

    books = Items.FindAllByID(0x0EFA, -1, empty_book_container, True)
    best = None
    best_count = 999

    for book in books:
        count = get_spell_count(book)
        if count < 64 and count < best_count:
            best = book
            best_count = count

    return best

def insert_scroll_into_book(scroll, book):
    before = get_spell_count(book)
    Items.Move(scroll, book, 0)
    Misc.Pause(700)
    after = get_spell_count(book)
    return after > before

def craft_single_spell_with_retry(spell_name, spell_def):
    success = craft_spell(spell_name, spell_def, 1)
    if not success:
        return None

    scroll_id = SCROLL_IDS[spell_name]
    return Items.FindByID(scroll_id, -1, Player.Backpack.Serial)

def run_full_spellbook():
    global _status_msg, _status_hue, _runtime_active, _active_spellbook

    while True:
        if not resource_chest:
            _status_msg = "Set resource container first."
            _status_hue = 33
            _runtime_active = False
            return

        if not empty_book_container:
            _status_msg = "Set empty book container first."
            _status_hue = 33
            _runtime_active = False
            return

        # Acquire next spellbook
        if not _active_spellbook or not Items.FindBySerial(_active_spellbook):
            book = find_target_spellbook()
            if not book:
                _status_msg = "All spellbooks completed." if FILL_ALL_BOOKS else "No valid spellbook found."
                _status_hue = 68
                _runtime_active = False
                return

            _active_spellbook = book.Serial
            Items.Move(book, Player.Backpack.Serial, 0)
            Misc.Pause(800)

        book = Items.FindBySerial(_active_spellbook)

        for circle in range(1, 9):
            for spell in SPELLS_BY_CIRCLE[circle]:
                if get_spell_count(book) >= 64:
                    break

                spell_def = None
                for cat in SPELL_CATEGORIES.values():
                    if spell in cat["spells"]:
                        spell_def = cat["spells"][spell]
                        break
                if not spell_def:
                    continue

                before_count = get_spell_count(book)
                completed = False
                script_failures = 0

                while not completed:
                    if script_failures >= MAX_FULLBOOK_RETRIES:
                        _status_msg = f"Failed {spell} after retries."
                        _status_hue = 33
                        _runtime_active = False
                        return

                    if not pull_from_resource_chest(BLANK_SCROLL_ID, PULL_SCROLL_BUFFER):
                        script_failures += 1
                        Misc.Pause(600)
                        continue

                    reagent_fail = False
                    for reg, amt in spell_def["reagents"].items():
                        reg_id = REAGENT_IDS.get(reg)
                        if reg_id and not pull_from_resource_chest(reg_id, max(amt, PULL_REAGENT_BUFFER)):
                            reagent_fail = True
                            break

                    if reagent_fail:
                        script_failures += 1
                        Misc.Pause(600)
                        continue

                    _status_msg = f"Full Book: {spell} ({before_count}/64)"
                    _status_hue = 68

                    scroll = craft_single_spell_with_retry(spell, spell_def)
                    if not scroll:
                        Misc.Pause(500)
                        continue

                    Items.Move(scroll, book, 0)
                    Misc.Pause(800)

                    after_count = get_spell_count(book)
                    if after_count > before_count:
                        completed = True
                    else:
                        script_failures += 1
                        Misc.Pause(600)

        _status_msg = "Spellbook complete."
        _status_hue = 68
        
        if resource_chest:
            Items.Move(book, resource_chest, 0)
            Misc.Pause(800)
            
        _active_spellbook = 0

        if not FILL_ALL_BOOKS:
            _runtime_active = False
            return

# ===========================================================
# GUI SETTINGS/CONFIGURATION (DO NOT EDIT)
# ===========================================================

MODE_BATCH    = 1
MODE_FULLBOOK = 2
MODE_TRAIN    = 3

_current_mode     = MODE_BATCH
_runtime_active   = False
_status_msg       = "Idle"

_current_circle = 1  

_selected_spells = {}
_spell_button_map = {}

# Button IDs
BTN_CLOSE        = 9000
BTN_MODE_BATCH   = 9001
BTN_MODE_FULL    = 9002
BTN_MODE_TRAIN   = 9003
BTN_TOGGLE_RUN   = 9004
BTN_SET_RES_CONT = 9005
BTN_SET_BOOK_CONT = 9006

BTN_PAGE_PREV    = 9100
BTN_PAGE_NEXT    = 9101

BTN_SPELL_BASE   = 10000


def ensure_selected_spells_init():
    global _selected_spells
    if _selected_spells:
        return
    for spell_list in SPELLS_BY_CIRCLE.values():
        for s in spell_list:
            _selected_spells[s] = False


def render_gui():
    ensure_selected_spells_init()

    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)

    width, height = 420, 340
    Gumps.AddBackground(gd, 0, 0, width, height, 5054)
    Gumps.AddAlphaRegion(gd, 0, 0, width, height)

    # Title
    Gumps.AddLabel(gd, 120, 5, 68, "Frogge's Inscription Suite v1")

    # Status
    mode_name = {MODE_BATCH:"Batch", MODE_FULLBOOK:"Full Book", MODE_TRAIN:"Training"}.get(_current_mode, "?")
    Gumps.AddLabel(gd, 15, 30, 0x480, f"Mode: {mode_name}  Run: {_runtime_active}")

    # Skill display 
    inskill = Player.GetSkillValue("Inscription")
    incap = Player.GetSkillCap("Inscription")
    Gumps.AddLabel(gd, 15, 45, 0x44E, f"Inscription: {inskill:.1f}/{incap:.1f}")
    Gumps.AddLabel(gd, 15, 65, _status_hue, f"Status: {_status_msg[:40]}")

    # Start / Stop (top-right)
    Gumps.AddButton(gd, 380, 30, 4011, 4013, BTN_TOGGLE_RUN, 1, 0)
    Gumps.AddLabel(gd, 330, 32, 68, "Start/Stop")

    # Close (under Start/Stop)
    Gumps.AddButton(gd, 380, 55, 4017, 4019, BTN_CLOSE, 1, 0)
    Gumps.AddLabel(gd, 340, 57, 33, "Close")
    
    # Mode buttons 
    Gumps.AddButton(gd, 15, 85, 4005, 4007, BTN_MODE_BATCH, 1, 0)
    Gumps.AddLabel(gd, 40, 85, 68, "Batch")

    # Resource chest select 
    Gumps.AddButton(gd, 15, 105, 4005, 4007, BTN_SET_RES_CONT, 1, 0)
    Gumps.AddLabel(gd, 40, 105, 68, "Resource Chest")

    Gumps.AddButton(gd, 195, 105, 4005, 4007, BTN_SET_BOOK_CONT, 1, 0)
    Gumps.AddLabel(gd, 220, 105, 68, "Book Container")

    Gumps.AddButton(gd, 195, 85, 4005, 4007, BTN_MODE_FULL, 1, 0)
    Gumps.AddLabel(gd, 220, 85, 68, "Full Book")

    Gumps.AddButton(gd, 95, 85, 4005, 4007, BTN_MODE_TRAIN, 1, 0)
    Gumps.AddLabel(gd, 120, 85, 68, "Training")

    # Batch amount display
    if _current_mode == MODE_BATCH:
        Gumps.AddLabel(gd, 275, 85, 0x44E, f"Amt: {_target_amount}")

    # Circle header
    Gumps.AddLabel(gd, 15, 130, 0x44E, f"Circle: {_current_circle}") 

    # Page arrows
    Gumps.AddButton(gd, 345, 85, 4014, 4016, BTN_PAGE_PREV, 1, 0)
    Gumps.AddButton(gd, 375, 85, 4005, 4007, BTN_PAGE_NEXT, 1, 0)

    # Spell list 
    global _spell_button_map
    _spell_button_map = {}

    start_x, start_y = 15, 160
    row_h = 18

    spells = SPELLS_BY_CIRCLE.get(_current_circle, [])
    for idx, spell in enumerate(spells):
        btn = BTN_SPELL_BASE + idx
        _spell_button_map[btn] = spell
        hue = 68 if _selected_spells.get(spell) else 0x44E
        y = start_y + idx * row_h
        Gumps.AddButton(gd, start_x, y, 4005, 4007, btn, 1, 0)
        Gumps.AddLabel(gd, start_x + 25, y, hue, spell)

    Gumps.SendGump(
        GUMP_ID,
        Player.Serial,
        GUMP_X,
        GUMP_Y,
        gd.gumpDefinition,
        gd.gumpStrings
    )

# ===========================================================
# BUTTON HANDLING 
# ===========================================================

def handle_button(btn):
    global _running, _current_mode, _runtime_active, _status_hue
    global _current_circle, _status_msg, resource_chest, empty_book_container

    if btn == BTN_CLOSE:
        _running = False
        return

    if btn == BTN_MODE_BATCH:
        _current_mode = MODE_BATCH
        _runtime_active = False
        _status_msg = "Batch mode selected."
        return

    if btn == BTN_MODE_FULL:
        _current_mode = MODE_FULLBOOK
        _runtime_active = False
        _status_msg = "Full Book mode selected."
        return

    if btn == BTN_MODE_TRAIN:
        _current_mode = MODE_TRAIN
        _runtime_active = False
        _status_msg = "Training mode selected."
        return

    if btn == BTN_TOGGLE_RUN:
        if not resource_chest:
            _status_msg = "Set resource container first."
            _status_hue = 33
            return
        _runtime_active = not _runtime_active
        _status_msg = "Running..." if _runtime_active else "Stopped."
        _status_hue = 68
        return

    if btn == BTN_SET_RES_CONT:
        Target.Cancel()
        s = Target.PromptTarget("Target resource chest")
        if s > 0 and Items.FindBySerial(s):
            resource_chest = s
            _status_msg = "Resource chest set."
            _status_hue = 68
        else:
            _status_msg = "Invalid container."
            _status_hue = 33
        return

    if btn == BTN_SET_BOOK_CONT:
        Target.Cancel()
        s = Target.PromptTarget("Target empty book container")
        if s > 0 and Items.FindBySerial(s):
            empty_book_container = s
            _status_msg = "Empty book container set."
            _status_hue = 68
        else:
            _status_msg = "Invalid container."
            _status_hue = 33
        return

    if btn == BTN_PAGE_PREV:
        _current_circle = max(1, _current_circle - 1)
        return

    if btn == BTN_PAGE_NEXT:
        _current_circle = min(8, _current_circle + 1)
        return

    ensure_selected_spells_init()
    if btn in _spell_button_map:
        spell = _spell_button_map[btn]
        _selected_spells[spell] = not _selected_spells.get(spell)
        return

# ===========================================================
# MAIN LOOP 
# ===========================================================

Misc.SendMessage("Inscription Suite starting...", 68)
Misc.Pause(200)

render_gui()

_last_button = 0

while _running and Player.Connected:
    gd = Gumps.GetGumpData(GUMP_ID)
    
    if not gd:
        render_gui()
        Misc.Pause(200)
        continue
        
    if gd and gd.buttonid and gd.buttonid != _last_button:
        _last_button = gd.buttonid
        handle_button(gd.buttonid)
        Misc.Pause(120)
        if _running:
            render_gui()

    if _runtime_active and _current_mode == MODE_BATCH:
        run_batch_crafting()
        _runtime_active = False
        render_gui()

    if _runtime_active and _current_mode == MODE_TRAIN:
        run_training()
        render_gui()

    if _runtime_active and _current_mode == MODE_FULLBOOK:
        run_full_spellbook()
        _runtime_active = False
        render_gui()

    Misc.Pause(REFRESH_MS)

Gumps.CloseGump(GUMP_ID)
Misc.SendMessage("Inscription Suite stopped.", 33)
