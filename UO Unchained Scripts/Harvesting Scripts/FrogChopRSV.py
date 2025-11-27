from System.Collections.Generic import List
from System import Int32

# === USER CONFIGURATION ===
STORAGE_MODE = "beetle"  # Options: "shelf", "satchel", "beetle"

# === CONSTANTS ===
HATCHET_ID = 0x0F43
LOG_ID = 0x1BDD
BOARD_ID = 0x1BD7

# Resource Shelf
RESOURCE_SHELF_ID = 0x71FC
RESOURCE_SHELF_GUMP_ID = 0x6abce12
FILL_FROM_BACKPACK_BUTTON = 141

# Beetle
BEETLE_TYPE = 0x317

# Satchel
RESOURCE_SATCHEL_IDS = [0x1576, 0x5576]

# === UTILITY ===
Journal.Clear()

def find_hatchet():
    for layer in ['LeftHand', 'RightHand']:
        item = Player.GetItemOnLayer(layer)
        if item and item.ItemID == HATCHET_ID:
            return item
    return Items.FindByID(HATCHET_ID, -1, Player.Backpack.Serial)

def is_overweight():
    return Player.Weight >= Player.MaxWeight

def check_no_wood():
    if Journal.Search("There's not enough wood here to harvest."):
        Journal.Clear()
        return True
    return False

# === TREE + LOGGING ===
def cut_tree():
    hatchet = find_hatchet()
    if not hatchet:
        Misc.SendMessage("No hatchet found!", 33)
        return False

    if not Player.GetItemOnLayer('LeftHand') and not Player.GetItemOnLayer('RightHand'):
        Player.EquipItem(hatchet)
        Misc.Pause(600)

    Items.UseItem(hatchet)
    Target.WaitForTarget(1200, False)
    Target.TargetExecute(Player.Serial)
    Misc.Pause(600)
    return True

def cut_logs():
    hatchet = find_hatchet()
    if not hatchet:
        return False

    found_logs = False
    for item in Player.Backpack.Contains:
        if item.ItemID == LOG_ID:
            found_logs = True
            Items.UseItem(hatchet)
            Target.WaitForTarget(1500, False)
            Target.TargetExecute(item)
            Misc.Pause(1800)
    return found_logs

# === STORAGE: SHELF ===
def transfer_boards_to_shelf():
    shelf = Items.FindByID(RESOURCE_SHELF_ID, -1, Player.Backpack.Serial)
    if not shelf:
        Misc.SendMessage("Shelf not found. Skipping transfer.", 33)
        return False

    Items.UseItem(shelf)
    if not Gumps.WaitForGump(RESOURCE_SHELF_GUMP_ID, 5000):
        Misc.SendMessage("Shelf gump not found. Skipping transfer.", 33)
        return False

    Gumps.SendAction(RESOURCE_SHELF_GUMP_ID, FILL_FROM_BACKPACK_BUTTON)
    Misc.Pause(600)
    Gumps.CloseGump(RESOURCE_SHELF_GUMP_ID)
    Misc.SendMessage("Transferred to shelf and closed gump.", 68)
    return True

# === STORAGE: SATCHEL ===
def find_resource_satchel():
    waist_item = Player.GetItemOnLayer('Waist')
    if waist_item and waist_item.ItemID in RESOURCE_SATCHEL_IDS:
        return waist_item
    for sid in RESOURCE_SATCHEL_IDS:
        item = Items.FindByID(sid, -1, Player.Backpack.Serial)
        if item:
            return item
    return None

def transfer_boards_to_satchel():
    satchel = find_resource_satchel()
    if not satchel:
        Misc.SendMessage("No satchel found.", 33)
        return False

    moved = False
    for item in Player.Backpack.Contains:
        if item.ItemID == BOARD_ID:
            Items.Move(item, satchel, 0)
            Misc.Pause(400)
            moved = True
    if moved:
        Misc.SendMessage("Boards moved to satchel.", 68)
    return moved

# === STORAGE: BEETLE ===
def find_beetle():
    f = Mobiles.Filter()
    f.RangeMax = 10
    f.Bodies = List[Int32]([BEETLE_TYPE])
    result = Mobiles.ApplyFilter(f)
    return result[0] if result else None

def transfer_boards_to_beetle():
    beetle = find_beetle()
    if not beetle:
        Misc.SendMessage("No beetle nearby!", 33)
        return False

    if Player.Mount:
        Mobiles.UseMobile(Player.Serial)
        Misc.Pause(1000)
        if Player.Mount:
            Misc.SendMessage("Failed to dismount.", 33)
            return False

    moved = False
    while True:
        found = False
        for item in Player.Backpack.Contains:
            if item.ItemID == BOARD_ID:
                Items.Move(item, beetle.Backpack, 0)
                Misc.Pause(400)
                found = moved = True
                break
        if not found:
            break

    if moved:
        Misc.SendMessage("Boards moved to beetle.", 68)
    return moved

# === DISPATCHER ===
def transfer_boards_to_storage():
    if STORAGE_MODE == "shelf":
        return transfer_boards_to_shelf()
    elif STORAGE_MODE == "satchel":
        return transfer_boards_to_satchel()
    elif STORAGE_MODE == "beetle":
        return transfer_boards_to_beetle()
    else:
        Misc.SendMessage(f"Invalid STORAGE_MODE: {STORAGE_MODE}", 33)
        return False

# === MAIN LOOP ===
def main():
    Misc.SendMessage(f"Starting Lumberjack - Using {STORAGE_MODE.upper()} for storage.", 68)
    try:
        while True:
            if check_no_wood():
                Misc.Pause(500)
                continue

            if is_overweight():
                Misc.SendMessage("Overweight - Processing backpack contents...", 65)

                # Only cut logs if the shelf isn't doing it for us
                if STORAGE_MODE != "shelf":
                    cut_logs()
                    Misc.Pause(600)

                transfer_boards_to_storage()
                Misc.Pause(600)
                continue

            cut_tree()
            Misc.Pause(800)

    except Exception as e:
        Misc.SendMessage(f"Script interrupted: {e}", 33)
        raise

if __name__ == "__main__":
    main()
