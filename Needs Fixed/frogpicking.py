import sys

LOCKPICKS_ID = 0x14FC
LOCKPICK_TRAINER_ID = 0x09AA

COLOR_RED = 38
COLOR_GREENISH = 85

DEFAULT_SCRIPT_DELAY = 250
ITEM_INTERACTION_DELAY = 650
LOCKPICK_DELAY = 1000

if Player.GetRealSkillValue("Lockpicking") < 50:
    Player.HeadMessage(COLOR_RED, "Skill too low, buy from NPC")
    sys.exit(99)

lockpickTrainer = Items.FindByID(LOCKPICK_TRAINER_ID, -1, Player.Backpack.Serial, True);
if not lockpickTrainer:
    Player.HeadMessage(COLOR_RED, "No lockpick trainer found in backpack.")
    sys.exit(99)

while Player.Connected and Player.GetRealSkillValue("Lockpicking") < Player.GetSkillCap("Lockpicking"):
    if not Items.FindByID(LOCKPICKS_ID, -1, Player.Backpack.Serial, True):
        Player.HeadMessage(COLOR_RED, "No lockpicks found in backpack.")
        sys.exit(99)

    # Reset lockpick trainer to current skill level
    Items.UseItem(lockpickTrainer.Serial)
    Misc.Pause(ITEM_INTERACTION_DELAY)

    if not Timer.Check("LOCKPICK_COOLDOWN"):
        Items.UseItemByID(LOCKPICKS_ID, -1)
        Target.WaitForTarget(1000)
        Target.TargetExecute(lockpickTrainer.Serial)
        Timer.Create("LOCKPICK_COOLDOWN", LOCKPICK_DELAY)
        Misc.Pause(DEFAULT_SCRIPT_DELAY)
    
    Misc.Pause(DEFAULT_SCRIPT_DELAY)

Player.HeadMessage(COLOR_GREENISH, "Skill maxed")