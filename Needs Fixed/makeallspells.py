#===============================================================================
# Razor Enhanced script: Auto-craft one of each 1st- and 2nd-circle scrolls
# with retry logic (re-press button until scroll appears in backpack).
#===============================================================================
#
# How it works:
# 1. Finds your Scribe’s Pen (by graphic ID) in your backpack and double-clicks it.
# 2. Waits for the Scribe Gump to open, then sends the “1st Circle” category action.
# 3. For each 1st-circle spell (in the order below), it:
#    a. Loops until one scroll of that spell is found in your backpack.
#    b. If the scroll is not present, sends the button action to craft it, then waits 
#       for the gump to refresh, and repeats.
# 4. After all 1st-circle spells are crafted, sends the “2nd Circle” category action.
# 5. Repeats the same loop-and-check approach for each 2nd-circle spell.
# 6. Closes the gump and stops.
#
# Replace the placeholders below before running:
# • <SCRIBE_PEN_ID>    – graphic ID of your Scribe’s Pen (e.g., 0x0F52).
# • 0x38920abd   – numeric ID of the Scribe Gump when it opens.
#   (Use Razor Enhanced’s “Open Gump” tool to confirm.)
#===============================================================================


#===============================================================================
# 1) Locate and use (double-click) the Scribe’s Pen
#===============================================================================
if finditemtype '0x0FBF' backpack -1 -1 -1 as pen
{
    # Double-click the pen to open the Scribe Gump
    Items.UseItem(pen)
    Gumps.WaitForGump(<0x38920abd>, 10000)
}
else
{
    # No pen found—halt script with a prompt
    prompt "❗ Cannot find a Scribe’s Pen (graphic <SCRIBE_PEN_ID>) in backpack."
    stop
}

#===============================================================================
# 2) Craft each 1st-Circle spell with retry
#    – Category = 1
#    – Spell list (ButtonID → ItemID):
#        • Reactive Armor   (  2 → 0x1F2D )
#        • Clumsy          (  9 → 0x1F2E )
#        • Create Food     ( 16 → 0x1F2F )
#        • Feeblemind      ( 23 → 0x1F30 )
#        • Heal            ( 30 → 0x1F31 )
#        • Magic Arrow     ( 37 → 0x1F32 )
#        • Night Sight     ( 44 → 0x1F33 )
#        • Weaken          ( 51 → 0x1F34 )
#===============================================================================

# 2.1) Select “1st Circle”
Gumps.SendAction(0x38920abd, 1)
Gumps.WaitForGump(0x38920abd, 10000)

# 2.2) Loop until “Reactive Armor” appears
craftReactiveArmor:
if not findtype 0x1F2D backpack -1 -1 -1 as scrollRA
{
    # Press the “Reactive Armor” button (2)
    Gumps.SendAction(0x38920abd, 2)
    Gumps.WaitForGump(0x38920abd, 10000)
    goto craftReactiveArmor
}

# 2.3) Loop until “Clumsy” appears
craftClumsy:
if not findtype 0x1F2E backpack -1 -1 -1 as scrollClumsy
{
    # Press the “Clumsy” button (9)
    Gumps.SendAction(0x38920abd, 9)
    Gumps.WaitForGump(0x38920abd, 10000)
    goto craftClumsy
}

# 2.4) Loop until “Create Food” appears
craftCreateFood:
if not findtype 0x1F2F backpack -1 -1 -1 as scrollFood
{
    # Press the “Create Food” button (16)
    Gumps.SendAction(0x38920abd, 16)
    Gumps.WaitForGump(0x38920abd, 10000)
    goto craftCreateFood
}

# 2.5) Loop until “Feeblemind” appears
craftFeeblemind:
if not findtype 0x1F30 backpack -1 -1 -1 as scrollFeeblemind
{
    # Press the “Feeblemind” button (23)
    Gumps.SendAction(0x38920abd, 23)
    Gumps.WaitForGump(0x38920abd, 10000)
    goto craftFeeblemind
}

# 2.6) Loop until “Heal” appears
craftHeal:
if not findtype 0x1F31 backpack -1 -1 -1 as scrollHeal
{
    # Press the “Heal” button (30)
    Gumps.SendAction(0x38920abd, 30)
    Gumps.WaitForGump(0x38920abd, 10000)
    goto craftHeal
}

# 2.7) Loop until “Magic Arrow” appears
craftMagicArrow:
if not findtype 0x1F32 backpack -1 -1 -1 as scrollMA
{
    # Press the “Magic Arrow” button (37)
    Gumps.SendAction(0x38920abd, 37)
    Gumps.WaitForGump(0x38920abd, 10000)
    goto craftMagicArrow
}

# 2.8) Loop until “Night Sight” appears
craftNightSight:
if not findtype 0x1F33 backpack -1 -1 -1 as scrollNS
{
    # Press the “Night Sight” button (44)
    Gumps.SendAction(0x38920abd, 44)
    Gumps.WaitForGump(0x38920abd, 10000)
    goto craftNightSight
}

# 2.9) Loop until “Weaken” appears
craftWeaken:
if not findtype 0x1F34 backpack -1 -1 -1 as scrollWeaken
{
    # Press the “Weaken” button (51)
    Gumps.SendAction(0x38920abd, 51)
    Gumps.WaitForGump(0x38920abd, 10000)
    goto craftWeaken
}

#===============================================================================
# 3) Switch to 2nd-Circle category and repeat the retry logic
#    – Category = 8
#    – Spell list (ButtonID → ItemID):
#        • Agility         ( 58 → 0x1F35 )
#        • Cunning         ( 65 → 0x1F36 )
#        • Cure            ( 72 → 0x1F37 )
#        • Harm            ( 79 → 0x1F38 )
#        • Magic Trap      ( 86 → 0x1F39 )
#        • Magic Untrap    ( 93 → 0x1F3A )
#        • Protection      (100 → 0x1F3B )
#        • Strength        (107 → 0x1F3C )
#===============================================================================

# 3.1) Select “2nd Circle”
Gumps.SendAction(0x38920abd, 8)
Gumps.WaitForGump(0x38920abd, 10000)

# 3.2) Loop until “Agility” appears
craftAgility:
if not findtype 0x1F35 backpack -1 -1 -1 as scrollAgility
{
    # Press the “Agility” button (58)
    Gumps.SendAction(0x38920abd, 58)
    Gumps.WaitForGump(0x38920abd, 10000)
    goto craftAgility
}

# 3.3) Loop until “Cunning” appears
craftCunning:
if not findtype 0x1F36 backpack -1 -1 -1 as scrollCunning
{
    # Press the “Cunning” button (65)
    Gumps.SendAction(0x38920abd, 65)
    Gumps.WaitForGump(0x38920abd, 10000)
    goto craftCunning
}

# 3.4) Loop until “Cure” appears
craftCure:
if not findtype 0x1F37 backpack -1 -1 -1 as scrollCure
{
    # Press the “Cure” button (72)
    Gumps.SendAction(0x38920abd, 72)
    Gumps.WaitForGump(0x38920abd, 10000)
    goto craftCure
}

# 3.5) Loop until “Harm” appears
craftHarm:
if not findtype 0x1F38 backpack -1 -1 -1 as scrollHarm
{
    # Press the “Harm” button (79)
    Gumps.SendAction(0x38920abd, 79)
    Gumps.WaitForGump(0x38920abd, 10000)
    goto craftHarm
}

# 3.6) Loop until “Magic Trap” appears
craftMagicTrap:
if not findtype 0x1F39 backpack -1 -1 -1 as scrollMT
{
    # Press the “Magic Trap” button (86)
    Gumps.SendAction(0x38920abd, 86)
    Gumps.WaitForGump(0x38920abd, 10000)
    goto craftMagicTrap
}

# 3.7) Loop until “Magic Untrap” appears
craftMagicUntrap:
if not findtype 0x1F3A backpack -1 -1 -1 as scrollMU
{
    # Press the “Magic Untrap” button (93)
    Gumps.SendAction(0x38920abd, 93)
    Gumps.WaitForGump(0x38920abd, 10000)
    goto craftMagicUntrap
}

# 3.8) Loop until “Protection” appears
craftProtection:
if not findtype 0x1F3B backpack -1 -1 -1 as scrollProt
{
    # Press the “Protection” button (100)
    Gumps.SendAction(0x38920abd, 100)
    Gumps.WaitForGump(0x38920abd, 10000)
    goto craftProtection
}

# 3.9) Loop until “Strength” appears
craftStrength:
if not findtype 0x1F3C backpack -1 -1 -1 as scrollStr
{
    # Press the “Strength” button (107)
    Gumps.SendAction(0x38920abd, 107)
    Gumps.WaitForGump(0x38920abd, 10000)
    goto craftStrength
}

#===============================================================================
# 4) All spells crafted—close the Gump and finish
#===============================================================================
Gumps.CloseGump(0x38920abd)
wait ping
say "All 1st- and 2nd-circle scrolls crafted."
stop
