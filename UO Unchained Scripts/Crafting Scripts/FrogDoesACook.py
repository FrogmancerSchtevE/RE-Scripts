import Items
import Gumps
import Misc
import Target
import Player

# CONFIG (Edit only if needed)
RAW_STEAK_ID    = 0x097A
COOKED_STEAK_ID = 0x097B
SKILLET_ID      = 0x097F
COOKING_GUMP    = 0xDA0212D3
MAKE_LAST_BTN   = 47
MOVE_DELAY_MS   = 600
COOK_DELAY_MS   = 1200
OPEN_RETRIES       = 5     
ACTION_COOLDOWN_MS = 800   
SKILL_NAME      = "Cooking"
STOP_AT         = 100.0   

# DO NOT EDIT BELOW THIS LINE
def bp(): 
    return Player.Backpack

def get_skill(sname):
    try:
        return float(Player.GetRealSkillValue(sname))
    except:
        try:
            return float(Player.GetSkillValue(sname))
        except:
            return 0.0

def choose_source_container():
    Misc.SendMessage("Target your resource container", 89)
    Target.ClearLastandQueue()
    cont = Target.PromptTarget("Target the container with raw/cooked fish steaks")
    if cont > 0:
        Misc.SendMessage("Source/Return container set: 0x%X" % cont, 68)
    else:
        Misc.SendMessage("No container selected.", 33)
    return cont

def get_skillet():
    skillet = Items.FindByID(SKILLET_ID, -1, bp().Serial)
    if not skillet:
        Misc.SendMessage("Skillet not found in backpack.", 33)
    return skillet

def pull_one_steak(source_serial):
    steak = Items.FindByID(RAW_STEAK_ID, -1, source_serial)
    if steak:
        Items.Move(steak, bp(), 50)   
        Misc.Pause(MOVE_DELAY_MS)
        return True
    return False

def cook_one():
    skillet = get_skillet()
    if not skillet:
        return False

    for attempt in range(1, OPEN_RETRIES + 1):
        Journal.Clear()
        Items.UseItem(skillet)            
        Misc.Pause(MOVE_DELAY_MS)

        if Journal.Search("You must wait to perform another action"):
            Misc.Pause(ACTION_COOLDOWN_MS)
            continue

        if Gumps.CurrentGump() != COOKING_GUMP:
            Misc.Pause(200)

        if Gumps.CurrentGump() == COOKING_GUMP:
            Gumps.SendAction(COOKING_GUMP, MAKE_LAST_BTN)
            Misc.Pause(COOK_DELAY_MS)
            return True

        Misc.Pause(150)

    Misc.SendMessage("Cooking gump not found after %d tries. Is Make Last set?" % OPEN_RETRIES, 33)
    return False


def deposit_cooked(dest_serial):
    moved = 0
    while True:
        cooked = Items.FindByID(COOKED_STEAK_ID, -1, bp().Serial)
        if not cooked:
            break
        amt = getattr(cooked, "Amount", 50)  
        Items.Move(cooked, dest_serial, amt)
        moved += amt
        Misc.Pause(MOVE_DELAY_MS)
    return moved

def main():
    source = choose_source_container()
    if source <= 0:
        return

    cooked_total = 0
    while True:
        if get_skill(SKILL_NAME) >= STOP_AT:
            Misc.SendMessage("Stopping: %s >= %.1f" % (SKILL_NAME, STOP_AT), 68)
            break

        if not pull_one_steak(source):
            Misc.SendMessage("No more raw fish steaks in source.", 68)
            break

        if not cook_one():
            break

        cooked_total += deposit_cooked(source)

    Misc.SendMessage("Done. Cooked & returned %d fish steak(s)." % cooked_total, 68)

main()
