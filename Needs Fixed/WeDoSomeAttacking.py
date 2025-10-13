import math
from System.Collections.Generic import List
from System import Byte
Journal.Clear()
 

### Add the names of the mobs you don't want to attack here
summonsToIgnore = ["a reaper", "a rising colossus", "a nature's fury","a blade spirit"] #only red summons(notority 6)will be ignored
mobsToIgnore = ["addnameshere","addnameshere2"] #pick the name from the razor enhanced inspect tool
mobileIDsToIgnore = [0x00CB,0x00CF] #sheep Pig Cat Dog
serialsToIgnore = [0x067DA5C3,0x067DA5C6] #random animals as example
 
# attack blue mobs (notoriety 1) use with care!
attack_blues = 0
 
# show overhead messages yes=1, no=0 (silent mode)
use_messages = 0

# Use Town Buff. It will check if the town buff is active
use_townbuff = 0
 
##################################################################
# Set the spells you want to use to 1 ############################
    
use_eoo = 0 # Use Chiv Enemy of One - dangerous!
use_df = 1 # Use Chiv Divine Fury
use_cw = 1 # Use Chiv Consecrate Weapon
use_honor = 0 # Use Honor.. can be used without Bushido
use_ca = 0 # Use Bushido Counter Attack
use_momentumstrike = 0 # Use Bushido Momentum Strike
use_lightningstrike = 1 # Use Bushido Lightning Strike
use_onslaught = 1 # Use Swordsmanship Onslaught
use_curseweapon = 0 #Use curse weapon when 50% or lower health
 
##################################################################
# Dont touch anything below! ####################################
##################################################################
 
use_honor_fix = 0 #clear Honor if its still exiting without mobs around
use_bandages = 0 #will be automatically actived when you have healing or vet
use_vampiricembrace = 0 #will be automatically actived when you have 99+ Necro
use_arrows = 0 #will be automatically activated when you have archery
attackrange = 5 #range of mobs that will be attacked
nearbyrange = 1  #range of mobs counted for single/multi-target special
mobdistance = 5 #range of mobs that will be honored
requiredmana = 0 #used for weapon specials mana calculation
nearestonslaught = 0 #used for onslaught
firsthitmob = 0 #used for onslaught
 
class Weapon:
    name = ''
    itemID = 0
    weaponspecial_primary = ''
    weaponspecial_secondary = ''
    singleenemyspecial = ''
    multienemyspecial = ''
 
    def __init__ ( self, name, ItemID, weaponspecial_primary, weaponspecial_secondary, singleenemyspecial, multienemyspecial):
        self.name = name
        self.ItemID = ItemID
        self.weaponspecial_primary = weaponspecial_primary
        self.weaponspecial_secondary = weaponspecial_secondary
        self.singleenemyspecial = singleenemyspecial
        self.multienemyspecial = multienemyspecial
        
weapons = {
    'bladedstaff': Weapon( 'Bladed Staff', 0x26BD, "Armor Ignore", None, "primary", "primary"),
    'doubleaxe': Weapon( 'Double Axe', 0x0F4B, "Double Strike", "Whirlwind", "primary", "secondary"), 
    'largebattleaxe': Weapon( 'Large Battle Axe', 0x13FB, "Whirlwind", None, "primary", "primary"),
    'longsword': Weapon( 'Longsword', 0x0F61, "Armor Ignore", None, "primary", "primary"),
    'broadsword': Weapon( 'Broadsword', 0x0F5E, None, "Armor Ignore",  "secondary", "secondary"),
    'radiantscimitar': Weapon( 'Radiant Scimitar', 0x2D33, "Whirlwind", None, "primary", "primary"),
    'bladedwhip': Weapon( 'Bladed Whip', 0xA28B, None, "Whirlwind", "secondary", "secondary"),
    'barbedwhip': Weapon( 'Barbed Whip', 0xA289, None, "Whirlwind", "secondary", "secondary"),
    'hammerpick': Weapon( 'Hammer Pick', 0x143D, "Armor Ignore", None, "primary", "primary"),
    'waraxe': Weapon( 'War Axe', 0x1439, "Armor Ignore", None, "primary", "primary"),   
    'warhammer': Weapon( 'War Hammer', 0x1439, "Whirlwind", "Crushing Blow", "secondary", "primary"), 
    'gargishwarhammer': Weapon( 'Gargish War Hammer', 0x48C0, "Whirlwind", "Crushing Blow", "secondary", "primary"),
    'gnarledstaff': Weapon( 'Gnarled Staff', 0x13F8, None, "Force of Nature", "secondary", "secondary"),
    'gargishkryss': Weapon( 'Gargish Kryss', 0x48BC, "Armor Ignore", None, "primary", "primary"),
    'shortblade': Weapon( 'Shortblade', 0x0907, "Armor Ignore", None, "primary", "primary"),  
    'bloodblade': Weapon( 'Bloodblade', 0x08FE, None, "Paralyzing Blow", "secondary", "secondary"),
    'compositebow': Weapon( 'Composite Bow', 0x26C2, "Armor Ignore", None, "primary", "primary"),
    'soulglaive': Weapon( 'Soul Glaive', 0x090A, "Armor Ignore", None, "primary", "primary"),   
    'repeatingcrossbow': Weapon( 'Repeating Crossbow', 0x26C3, "Double Shot", None, "primary", "primary"),
    'yumi': Weapon( 'Yumi', 0x27A5, None, "Double Shot", "secondary", "secondary"),
    'elvencompositebow': Weapon( 'Elven Composite Bow', 0x2D1E, "Force Arrow", None, "primary", "primary") 
}
  
 
def mobs_list (range):
    fil = Mobiles.Filter()
    fil.Enabled = True
    fil.RangeMax = range
    if attack_blues == 0:
        fil.Notorieties = List[Byte](bytes([3,4,5,6]))
    elif attack_blues == 1:
        fil.Notorieties = List[Byte](bytes([1,3,4,5,6]))
    fil.IsGhost = False
    fil.CheckIgnoreObject = True
    fil.IgnorePets = True
    #fil.CheckLineOfSight = True
    fil.Friend = False
    mobs = Mobiles.ApplyFilter(fil)    
    mobsTemp = mobs[:]
    for mob in mobs:
        prop = mob.Properties
        if mob.Name in mobsToIgnore:
            mobsTemp.Remove( mob )
        elif mob.Name in summonsToIgnore and mob.Notoriety == 6:
            mobsTemp.Remove( mob )
        elif mob.MobileID in mobileIDsToIgnore:
            mobsTemp.Remove( mob )  
        elif mob.Serial in serialsToIgnore:
            mobsTemp.Remove( mob )  
        else:
            for p in prop:
                c = str(p)
                if "healer" in c and mob.Notoriety == 6:
                    mobsTemp.Remove( mob )
                if "priest of mondain" in c and mob.Notoriety == 6:
                    mobsTemp.Remove( mob )
    mobs = mobsTemp
    return mobs 
 
    
equippedweapon = Player.GetItemOnLayer('FirstValid')
if not equippedweapon:
    equippedweapon = Player.GetItemOnLayer('LeftHand')
 
if equippedweapon:    
    for weapon in weapons:
        if weapons[ weapon ].ItemID == equippedweapon.ItemID:
            Player.HeadMessage(60,"%s"% weapons[ weapon ].name)
            if weapons[ weapon ].singleenemyspecial == "primary":    
                Player.HeadMessage(70,"Single Target: %s"% weapons[ weapon ].weaponspecial_primary)
            elif weapons[ weapon ].singleenemyspecial == "secondary":    
                Player.HeadMessage(70,"Single Target: %s"% weapons[ weapon ].weaponspecial_secondary)
            if weapons[ weapon ].multienemyspecial == "primary":    
                Player.HeadMessage(70,"Muli Target: %s"% weapons[ weapon ].weaponspecial_primary)
            elif weapons[ weapon ].multienemyspecial == "secondary":    
                Player.HeadMessage(70,"Multi Target: %s"% weapons[ weapon ].weaponspecial_secondary)    
            weapon_set = weapon
            
else:
    Player.HeadMessage(60,"No weapon!")
    
 
### Set the options if you dont have the skills
if not Player.BuffsExist("Saving Throw") or not Player.GetSkillValue('Swordsmanship') >= 90:
    use_onslaught = 0
 
if Player.GetSkillValue('Chivalry') < 60:
    use_eoo = 0
    use_df = 0
    use_cw = 0
 
if Player.GetSkillValue('Bushido') < 50:
    use_ca = 0
    use_lightningstrike = 0
    
if Player.GetSkillValue('Bushido') < 70:
    use_momentumstrike = 0
 
if Player.GetSkillValue('Parry') < 60 and Player.GetSkillValue('Bushido') < 60:
    use_ca = 0
    
if Player.GetSkillValue('Archery') >= 50 or Player.GetSkillValue('Throwing') >= 50:
    attackrange = 14 
    nearbyrange = 10
    mobdistance = 10
    
if Player.GetSkillValue('Healing') > 50 or Player.GetSkillValue('Veterinary') > 50:
    use_bandages = 1
 
if Player.GetSkillValue('Necromancy') >= 99:    
    use_vampiricembrace = 1
    
if Player.GetSkillValue('Archery') >= 50:   
    use_arrows = 1
 
    
####################################
    
lmc = (min(40,Player.LowerManaCost))/100
 
def get_weaponabilitiesmanacost(basemana):
    manareduction = 0
    manacostscalar = 1
    totalskills = Player.GetSkillValue('Swordsmanship') + \
    Player.GetSkillValue('Tactics') + Player.GetSkillValue('Macing') + \
    Player.GetSkillValue('Fencing') + Player.GetSkillValue('Archery') + \
    Player.GetSkillValue('Parry') + Player.GetSkillValue('Lumberjacking') + \
    Player.GetSkillValue('Stealth') + Player.GetSkillValue('Throwing') + \
    Player.GetSkillValue('Poisoning') + Player.GetSkillValue('Bushido') + \
    Player.GetSkillValue('Ninjitsu')
    if totalskills >= 300:
        manareduction = 10
    elif totalskills >= 200:
        manareduction = 5
    else:
        manareduction = 0
    #Player.HeadMessage(50,"Total Skills: %i" % totalskills) 
    
    if Player.BuffsExist("Mind Rot"):
        manacostscalar += .25
    manacostscalar = manacostscalar - lmc  
    requiredmana = int((basemana - manareduction) * manacostscalar)
    if Timer.Check("weaponspecial") == True:
        requiredmana *= 2
    #Player.HeadMessage(50,"requiredmana: %s" % requiredmana)
    return requiredmana
 
 
def calc_castpause():
    adjust = 100 #Adjustable correction delay for lag or things going too fast and misbehaving    
    castrecovery = 1750 #Universal spell recovery time
    fcr = Player.FasterCastRecovery * 250
    castpause = castrecovery - fcr + adjust
    if castpause < 0: castpause = adjust
    if Player.FasterCastRecovery >= 6:
        castpause = adjust
    return castpause
            
            
def check_townbuff():
    if use_townbuff ==1 and Timer.Check("towncheck") == False:
        if not Player.BuffsExist ("City Trade Deal Buff"):
            Player.HeadMessage(20,"NO Town Bonus!")
            Timer.Create("towncheck",4000)
 
def counterattack():
    if use_ca == 1:
        if not Player.BuffsExist('Confidence') and not Player.BuffsExist('Evasion'):
            if not Player.BuffsExist('Counter Attack') and Player.Hits >= Player.HitsMax * 0.50 and Player.Mana >= (5 - (5 * lmc)) and not Player.Paralized:
                if use_messages == 1:
                    Player.HeadMessage(80,"Counter Attack!") 
                Spells.CastBushido("Counter Attack")
 
def onslaught():
    global nearestonslaught
    
    if Journal.Search("You deliver an onslaught"):
        nearestonslaught = nearest.Serial
        Timer.Create('onslaught',6200)
        Timer.Create('blockspecials',50)
        Journal.Clear()
        Misc.Pause(50)
        
    if not Player.SpellIsEnabled("Onslaught") and Timer.Check('onslaught') == True:
        if nearest.Serial != nearestonslaught: 
            if Player.Hits >= Player.HitsMax * 0.50 and Player.Mana >= (20 - (20 * lmc)):
                Spells.CastMastery('Onslaught')
                Timer.Create('onslaught',1400)
                Timer.Create('blockspecials',1400)
                Misc.Pause(150)
    
    if not Player.SpellIsEnabled("Onslaught") and Timer.Check('onslaught') == False:
        if Player.Hits >= Player.HitsMax * 0.50 and Player.Mana >= (20 - (20 * lmc)):
            Spells.CastMastery('Onslaught')
            Timer.Create('onslaught',1400)
            Timer.Create('blockspecials',1400)
            Misc.Pause(150)
 
def curseweapon(): 
    if use_curseweapon == 1 and Player.Hits < Player.HitsMax * 0.50 and Player.Mana >= (7 - (7 * lmc)) and Timer.Check('spells') == False and not Player.Paralized:
        pigiron = Items.FindByID(0x0F8A,0x0000,Player.Backpack.Serial,-1,True)
        if lrc > 90:
            if not Player.BuffsExist("Curse Weapon"):
                if use_messages == 1:
                    Player.HeadMessage(90,"Curse Weapon")
                Spells.CastNecro("Curse Weapon")
                Timer.Create('spells',calc_castpause())
        elif pigiron and pigiron.Amount > 0:
            if not Player.BuffsExist("Curse Weapon"):
                if use_messages == 1:
                    Player.HeadMessage(90,"Curse Weapon")
                Spells.CastNecro("Curse Weapon")
                Timer.Create('spells',calc_castpause())
                
def check_vamp():
    if use_vampiricembrace == 1 and Timer.Check("vampcheck") == False:
        if not Player.BuffsExist ("Vampiric Embrace"):
            #Spells.CastNecro ("Vampiric Embrace")
            Player.HeadMessage(20,"NO VAMPIRIC EMBRACE!")
            Timer.Create("vampcheck",4000)
                
def check_bandages():
    if use_bandages == 1 and Timer.Check("bandagecheck") == False:   
        bandagesamount = Items.ContainerCount(Player.Backpack.Serial,0x0E21,0,True)
        if bandagesamount < 5:
            firstaidbelt = Items.FindByName("First Aid Belt",-1,Player.Backpack.Serial,-1,False)
            if firstaidbelt:
                Items.UseItem(firstaidbelt)
            Player.HeadMessage(30,"Warning: %s Bandages left" % bandagesamount)
        Timer.Create("bandagecheck",4000)
 
def check_arrows():
    if use_arrows == 1 and Timer.Check("arrowcheck") == False:
        arrowamount = Items.ContainerCount(Player.Backpack.Serial,0x0F3F,0,True)
        quiver = Player.GetItemOnLayer('Cloak')
        if quiver and quiver.ItemID == 0x2B02:
            arrowamount2 = Items.ContainerCount(quiver,0x0F3F,0,False)
            if not arrowamount2:
                if use_messages == 1:
                    Player.HeadMessage(50,"Quiver is empty, refill!")
                arrows = Items.FindByID(0x0F3F,-1,Player.Backpack.Serial,-1,False)
                if arrows:
                    Items.Move(arrows,quiver,500)
                Misc.Pause(500)            
            arrowamount = arrowamount + arrowamount2
            
        if arrowamount < 100:
            Player.HeadMessage(30,"Warning: %s arrows left" % arrowamount)
        Timer.Create("arrowcheck",4000)
        
 
def fighting(nearest): 
    
    global firsthitmob
    #Misc.SendMessage ('Attack: {}'.format(nearest.Name))
    
    if not Player.BuffsExist('Enemy Of One')and use_eoo == 1 and Timer.Check('spells') == False and Player.Mana >= (20 - (20 * lmc)) and not Player.Paralized:
        if use_messages == 1:
            Player.HeadMessage(80,"Enemy Of One!")
        Spells.CastChivalry('Enemy Of One')
        Timer.Create('spells',calc_castpause())
    if not Player.BuffsExist('Divine Fury') and use_df == 1 and Timer.Check('spells') == False and Player.Mana >= (15 - (15 * lmc)) and not Player.Paralized:
        if use_messages == 1:
            Player.HeadMessage(80,"Divine Fury!")
        Spells.CastChivalry('Divine Fury')
        Timer.Create('spells',calc_castpause())
    if not Player.BuffsExist('Consecrate Weapon') and use_cw == 1 and Timer.Check('spells') == False and Player.Mana >= (10 - (10 * lmc)) and not Player.Paralized:
        if use_messages == 1:
            Player.HeadMessage(80,"Consecrate Weapon!")
        Spells.CastChivalry('Consecrate Weapon')
        Timer.Create('spells',calc_castpause())
        
    counterattack()
    
    if use_onslaught == 1 and Player.DistanceTo(nearest) <= 1:
        if firsthitmob != nearest.Serial or firsthitmob == 0:
            firsthitmob = nearest.Serial
            Timer.Create("hit",2000)
 
    Player.Attack(nearest)
    
    if nearby_enemies_len == 1:
 
        if use_onslaught == 1:
            if Timer.Check("hit") == False and firsthitmob == nearest.Serial and not Player.Paralized:
                onslaught()
        
        if Player.SpellIsEnabled( "Onslaught" ) == False or Timer.Check('blockspecials') == False:
        
            if not Player.HasSpecial and Player.Mana >= get_weaponabilitiesmanacost(30):
                
                if weapons[ weapon_set ].singleenemyspecial == "primary":
                    if use_messages == 1:
                        Player.HeadMessage(70,"%s"% weapons[ weapon_set ].weaponspecial_primary)
                    Player.WeaponPrimarySA()
                    if Timer.Check("weaponspecial") == False:
                            Timer.Create("weaponspecial",3000)
                elif weapons[ weapon_set ].singleenemyspecial == "secondary":
                    if use_messages == 1:
                        Player.HeadMessage(70,"%s"% weapons[ weapon_set ].weaponspecial_secondary)
                    Player.WeaponSecondarySA()
                    if Timer.Check("weaponspecial") == False:
                            Timer.Create("weaponspecial",3000)
 
                else:
                    if use_messages == 1:
                        Player.HeadMessage(80,"Primary Attack!")
                    Player.WeaponPrimarySA()
                    if Timer.Check("weaponspecial") == False:
                        Timer.Create("weaponspecial",3000) 
 
                Misc.Pause(200)
                                    
            elif not Player.HasSpecial and use_lightningstrike == 1 and not Player.BuffsExist('Lightning Strike') and Player.Mana >= (10 - (10 * lmc)):
                if use_messages == 1:
                    Player.HeadMessage(80,"Lightning Strike")
                Spells.CastBushido('Lightning Strike')
                Misc.Pause(200)  
                
    elif nearby_enemies_len >= 2:
        
        if weapons[ weapon_set ].weaponspecial_primary == "Whirlwind" or weapons[ weapon_set ].weaponspecial_secondary == "Whirlwind":
            requiredmana = 15 
        else:
            requiredmana = 30 
    
        if not Player.HasSpecial and Player.Mana >= get_weaponabilitiesmanacost(requiredmana):
 
            if weapons[ weapon_set ].multienemyspecial == "primary":
                if use_messages == 1:
                    Player.HeadMessage(70,"%s"% weapons[ weapon_set ].weaponspecial_primary)
                Player.WeaponPrimarySA()
                if Timer.Check("weaponspecial") == False:
                    Timer.Create("weaponspecial",3000)
            elif weapons[ weapon_set ].multienemyspecial == "secondary":
                if use_messages == 1:
                    Player.HeadMessage(70,"%s"% weapons[ weapon_set ].weaponspecial_secondary)
                Player.WeaponSecondarySA()
                if Timer.Check("weaponspecial") == False:
                    Timer.Create("weaponspecial",3000)    
            
            else:
                if use_messages == 1:
                    Player.HeadMessage(80,"Secondary Attack!")
                Player.WeaponSecondarySA()
                if Timer.Check("weaponspecial") == False:
                    Timer.Create("weaponspecial",3000)
                
            Misc.Pause(200)
 
        elif not Player.HasSpecial and use_momentumstrike == 1 and not Player.BuffsExist('Momentum Strike') and Player.Mana >= (10 - (10 * lmc)):
            if use_messages == 1:
                Player.HeadMessage(80,"Momentum Strike")
            Spells.CastBushido('Momentum Strike')
            Misc.Pause(200)
 
            
while not Player.IsGhost and Player.Visible:
    
    curseweapon()
    check_bandages()
    check_arrows()
    check_vamp()
    check_townbuff()
    
    victims = mobs_list(attackrange)
    
    if len(victims) > 0:
        
        nearest = Mobiles.Select(victims, 'Nearest')
        
        if len(mobs_list(1)) > 1:
            nearest = Mobiles.Select(mobs_list(1), 'Weakest')
        
        if use_honor == 1 and nearest.Hits == nearest.HitsMax and Player.DistanceTo(nearest) <= mobdistance:
            if Timer.Check('spamhonor') == False and use_messages == 1:  
                Player.HeadMessage(55,"Honor mob: {}".format(nearest.Name))
                Timer.Create('spamhonor',1500)
            Player.InvokeVirtue("Honor")
            Target.WaitForTarget(300, True)
            Target.TargetExecute(nearest)
            use_honor_fix = 0
 
        nearby_enemies_len = len(mobs_list(nearbyrange))
        fighting(nearest)
        
        Misc.Pause(100)
            
    else:
        
        if use_honor == 1:
            if Player.BuffsExist('Honored') == True:
                use_honor_fix = 1
                
        Misc.Pause(100)
        
    Misc.Pause(100)