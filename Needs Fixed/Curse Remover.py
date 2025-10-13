import Player
import Spells
import Target
import Misc
import time

# CONFIGURATION 
CHECK_INTERVAL = 1000  # ms between checks

# Debuff Settings (Format: "Buff Name": (auto_cast_enabled))
DEBUFFS = {
    "Curse": 1,
    "Blood Oath (curse)": 1, # This appears incorrect, trying to find real value
    "Strangle": 0,
    "Corpse Skin": 0,
    "Mind Rot": 0,
    "Evil Omen": 0,
    "Mortal Strike": 0,
}

# Track which debuffs have already been reported
active_debuffs = {}

while True:
    for debuff_name, autocast in DEBUFFS.items():
        if Player.BuffsExist(debuff_name):
            if not active_debuffs.get(debuff_name, False):
                Player.HeadMessage(33, f"Cursed: {debuff_name}!")
                active_debuffs[debuff_name] = True

                if autocast:
                    if Player.Mana >= 10:
                        Player.HeadMessage(80, f"Auto-casting Remove Curse for {debuff_name}!")
                        Spells.CastChivalry("Remove Curse")
                        Target.WaitForTarget(4000, True)
                        Target.Self()
                    else:
                        Player.HeadMessage(33, "Not enough mana to cast Remove Curse.")
        else:
            if active_debuffs.get(debuff_name, False):
                Player.HeadMessage(88, f"{debuff_name} faded.")
                active_debuffs[debuff_name] = False

    Misc.Pause(CHECK_INTERVAL)
    
    #Debug Portion

for buff in Player.GetBuffIcons():
    Misc.SendMessage(f"Active Buff: {buff}", 65)

