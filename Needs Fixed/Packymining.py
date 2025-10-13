usePackHorses = True
useFireBeetle = False
noTools = False
forgeFlag = True
resetPackHorses = False  # Set this to True to reset pack horses
miningTools = [ 0x0E86, 0x0E85, 0x0FB4, 0x0F39 ]

class myItem:
    name = None
    itemID = None
    color = None
    def __init__ ( self, name, itemID, color ):
        self.name = name
        self.itemID = itemID
        self.color = color

ores = {
    'agapite ore': myItem( 'agapite ore', 0x19B9, 0x0979 ),
    'bronze ore': myItem( 'bronze ore', 0x19B9, 0x0972 ),
    'copper ore': myItem( 'copper ore', 0x19B9, 0x096D ),
    'dull copper ore': myItem( 'dull copper ore', 0x19B9, 0x0973 ),
    'golden ore': myItem( 'golden ore', 0x19B9, 0x08a5 ),
    'iron ore': myItem( 'iron ore', 0x19B9, 0x0000 ),
    'shadow iron ore': myItem( 'shadow iron ore', 0x19B9, 0x0966 ),
    'verite ore': myItem( 'verite ore', 0x19B9, 0x089f ),
    'valorite ore': myItem( 'valorite ore', 0x19B9, 0x08ab ),
    'azurite ore': myItem( 'azurite ore', 0x19B9, 0x0829 ),
    'stone': myItem( 'stone', 0x1779, 0x0000 ),
    'bronze stone': myItem( 'bronze stone', 0x1779, 0x0972 ),
    'dull copper stone': myItem( 'dull copper stone', 0x1779, 0x0973 ),
    'shadow iron stone': myItem( 'shadow iron stone', 0x1779, 0x0966 ),
    'copper stone': myItem( 'copper stone', 0x1779, 0x096D ),
    'bronze stone': myItem( 'bronze stone', 0x1779, 0x0972 ),
    'golden stone': myItem( 'golden stone', 0x1779, 0x08a5 ),
    'verite stone': myItem( 'verite stone', 0x1779, 0x089f ),
    'valorite stone': myItem( 'valorite stone', 0x1779, 0x08ab ),
}

packHorses = []
currentHorseIndex = 0

def selectTool():
    rightHand = Player.GetItemOnLayer("RightHand")
    if rightHand and rightHand.ItemID in miningTools:
        return rightHand
    
    leftHand = Player.GetItemOnLayer("LeftHand")
    if leftHand and leftHand.ItemID in miningTools:
        return leftHand
    
    for miningTool in miningTools:
        tool = Items.FindByID( miningTool, -1, Player.Backpack.Serial )
        if tool != None:
            return tool

def findNearbyForge(maxDistance=3):
    """Find a forge static within the specified distance"""
    playerX = Player.Position.X
    playerY = Player.Position.Y
    
    for x in range(playerX - maxDistance, playerX + maxDistance + 1):
        for y in range(playerY - maxDistance, playerY + maxDistance + 1):
            distance = max(abs(playerX - x), abs(playerY - y))  # Chebyshev distance (UO standard)
            
            if distance <= maxDistance:
                try:
                    statics = Statics.GetStaticsTileInfo(x, y, Player.Map)
                    for static in statics:
                        if static.StaticID == 0x0FB1:  # Forge static ID
                            return static, distance, x, y
                except:
                    continue  
    
    return False, 999, 0, 0

def resetPackHorseMemory():
    """Delete all saved pack horse serials"""
    for i in range(5):
        if Misc.CheckSharedValue(f'packHorse{i+1}'):
            Misc.RemoveSharedValue(f'packHorse{i+1}')
            Player.HeadMessage(38, f'Removed Pack Horse #{i+1} from memory')
    
    if Misc.CheckSharedValue('petFireBeetle1'):
        Misc.RemoveSharedValue('petFireBeetle1')
        Player.HeadMessage(38, 'Removed Fire Beetle from memory')
    
    Player.HeadMessage(88, 'All pack horse memory cleared!')
    """Set up all 5 pack horses via prompts"""
    global packHorses
    packHorses = []
    
    if Player.Mount != None:
        Mobiles.UseMobile( Player.Serial )
        Misc.Pause( 800 )
    
    for i in range(5):
        Player.HeadMessage(88, f'Select Pack Horse #{i+1}')
        horseSerial = Target.PromptTarget( f'Select Pack Horse #{i+1} for ore storage', 90 )
        horse = Mobiles.FindBySerial(horseSerial)
        if horse:
            packHorses.append(horse)
            Misc.SetSharedValue( f'packHorse{i+1}', horseSerial )
            Player.HeadMessage(68, f'Pack Horse #{i+1} set: {horse.Name}')
        else:
            Player.HeadMessage(38, f'Failed to find Pack Horse #{i+1}!')
        Misc.Pause(500)
    
    Player.HeadMessage(88, f'All {len(packHorses)} pack horses initialized!')

def loadPackHorsesFromMemory():
    """Load previously set pack horses from shared values"""
    global packHorses
    packHorses = []
    
    for i in range(5):
        horseSerial = Misc.ReadSharedValue(f'packHorse{i+1}')
        if horseSerial:
            horse = Mobiles.FindBySerial(horseSerial)
            if horse:
                packHorses.append(horse)
                Player.HeadMessage(68, f'Loaded Pack Horse #{i+1}: {horse.Name}')
            else:
                Player.HeadMessage(38, f'Could not find Pack Horse #{i+1}!')
        else:
            Player.HeadMessage(38, f'No Pack Horse #{i+1} in memory!')

def getNextAvailableHorse():
    """Find the next pack horse that can accept items"""
    global currentHorseIndex
    
    if not packHorses:
        Player.HeadMessage(38, 'No pack horses available!')
        return None
    
    startIndex = currentHorseIndex
    
    for attempt in range(len(packHorses)):
        horse = packHorses[currentHorseIndex]
        
        if horse and Player.DistanceTo(horse) <= 3:
            Player.HeadMessage(68, f'Using Pack Horse #{currentHorseIndex + 1}')
            return horse
        
        currentHorseIndex = (currentHorseIndex + 1) % len(packHorses)
        
        if currentHorseIndex == startIndex:
            break
    
    Player.HeadMessage(38, 'All pack horses may be full or out of range! Need to forge ores.')
    return None

def ForgeOres():
    global forgeFlag
    global packHorses
    forgeFlag = True
    
    while forgeFlag == True:
        oreCount = 0
        Player.HeadMessage( 1100, 'You\'re overweight, go to a Forge' )
        Misc.Pause(200)
        
        if useFireBeetle == True:
            if Player.Mount != None:
                Mobiles.UseMobile( Player.Serial )
                Misc.Pause( 800 )
            
            for ore in ores:
                playerOre = Items.FindByID( ores[ ore ].itemID, ores[ ore ].color, Player.Backpack.Serial, True, True )
                if playerOre:
                    Misc.Pause(600)
                    Items.UseItem(playerOre)
                    Target.WaitForTarget(500,1)
                    Target.TargetExecute(petFire)
            
            if usePackHorses:
                for i, horse in enumerate(packHorses):
                    if horse and Player.DistanceTo(horse) <= 3:
                        Player.HeadMessage(88, f'Processing ores from Pack Horse #{i+1}')
                        for ore in ores:
                            oreStack = Items.FindByID( ores[ ore ].itemID, ores[ ore ].color, horse.Backpack.Serial, True, True )
                            if oreStack:
                                Misc.Pause(600)
                                Items.UseItem(oreStack)
                                Target.WaitForTarget(500,1)
                                Target.TargetExecute(petFire)
        else:
            forgeFound, forgeDistance, forgeX, forgeY = findNearbyForge(3)
            if forgeFound:
                Player.HeadMessage(68, f'Found forge at distance {forgeDistance}')
                    
                for ore in ores:
                    playerOre = Items.FindByID( ores[ ore ].itemID, ores[ ore ].color, Player.Backpack.Serial, True, True )
                    if playerOre:
                        Misc.Pause(600)
                        Items.UseItem(playerOre)
                        Target.WaitForTarget(500,1)
                        Target.TargetExecute(forgeX,forgeY,10,0x0FB1)
                
                if usePackHorses:
                    for i, horse in enumerate(packHorses):
                        if horse and Player.DistanceTo(horse) <= 3:
                            Player.HeadMessage(88, f'Processing ores from Pack Horse #{i+1}')
                            for ore in ores:
                                Mobiles.UseMobile(horse)
                                Misc.Pause(650)
                                oreStack = Items.FindByID( ores[ ore ].itemID, ores[ ore ].color, horse.Backpack.Serial, True, True )
                                if oreStack:
                                    Items.UseItem(oreStack)
                                    Target.WaitForTarget(500,1)
                                    Target.TargetExecute(forgeX,forgeY,10,0x0FB1)  # Target ground at forge location
                                    Misc.Pause(200)
            else:
                Player.HeadMessage(38, 'No forge found nearby! Move closer to a forge.')
        
        for ore in ores:
            oreCheck = Items.FindByID( ores[ ore ].itemID, ores[ ore ].color, Player.Backpack.Serial )
            if oreCheck:
                oreCount += 1
            
            if usePackHorses:
                for horse in packHorses:
                    if horse:
                        horseOre = Items.FindByID( ores[ ore ].itemID, ores[ ore ].color, horse.Backpack.Serial )
                        if horseOre:
                            oreCount += 1
            Misc.Pause(200)
        
        if oreCount == 0:
            forgeFlag = False
            break

def MoveOreToPackHorses():
    """Move ore to the next available pack horse"""
    global currentHorseIndex
    
    if not packHorses:
        Player.HeadMessage( 1100, 'No pack horses available!' )
        return False
    
    targetHorse = getNextAvailableHorse()
    if not targetHorse:
        return False
    
    horseNumber = packHorses.index(targetHorse) + 1
    moved_any = False
    successful_moves = 0
    failed_moves = 0
    
    for ore in ores:
        oreStack = Items.FindByID( ores[ ore ].itemID, ores[ ore ].color, Player.Backpack.Serial)
        while oreStack != None:
            originalSerial = oreStack.Serial
            Misc.SendMessage( f'Moving stack of {ores[ ore ].name} to Pack Horse #{horseNumber}' )
            
            # Attempt to move the ore
            Items.Move( oreStack, targetHorse.Backpack, 0 )
            Misc.Pause(650)
            
            # Check if the move was successful
            movedStack = Items.FindBySerial(originalSerial)
            if movedStack and movedStack.Container == Player.Backpack.Serial:
                # Move failed - horse is probably full
                failed_moves += 1
                Player.HeadMessage(38, f'Pack Horse #{horseNumber} appears to be full!')
                
                # Try next horse
                currentHorseIndex = (currentHorseIndex + 1) % len(packHorses)
                nextHorse = getNextAvailableHorse()
                
                if failed_moves >= 6:
                    return False
                    
                if nextHorse and nextHorse != targetHorse:
                    targetHorse = nextHorse
                    horseNumber = packHorses.index(targetHorse) + 1
                    Player.HeadMessage(68, f'Switching to Pack Horse #{horseNumber}')
                    continue  # Try moving to the new horse
                else:
                    # No other horses available or we've tried them all
                    if Player.Weight > Player.MaxWeight:
                        Items.DropItemGroundSelf( oreStack, 1)
                        Player.HeadMessage( 65, 'Dropped ore to allow you to move - all horses full!' )
                    return False
            else:
                # Successfully moved to horse
                moved_any = True
                successful_moves += 1
                oreStack = Items.FindByID( ores[ ore ].itemID, ores[ ore ].color, Player.Backpack.Serial)
            
            Misc.Pause(200)
    
    if moved_any:
        Player.HeadMessage(68, f'Moved {successful_moves} ore stacks to Pack Horse #{horseNumber}')
        if failed_moves > 0:
            Player.HeadMessage(38, f'{failed_moves} moves failed - horse may be getting full')
    
    return successful_moves > 0

def Mine():
    global usePackHorses
    global noTools
    global packHorses
    
    if Player.Mount != None:
        # We need to dismount to be able to mine
        Mobiles.UseMobile( Player.Serial )
        Misc.Pause( 600 )
        
    Journal.Clear()
    while ( not Journal.SearchByName( 'There is no metal here to mine.', 'System' ) and
            not Journal.SearchByName( 'Target cannot be seen.', 'System' ) and
            not Journal.SearchByName( 'You can\'t mine there.', 'System' ) and 
            noTools == False ):
        if Player.Weight <= Player.MaxWeight-12:
            tool = selectTool()
            if tool == None:
                Player.HeadMessage( 1100, 'You\'re out of tools!' )
                if Player.GetRealSkillValue("Tinkering") > 40:
                    Gumps.CloseGump(  2653346093)
                    while Items.BackpackCount(0x1EB8,-1) < 2:
                        Items.UseItem(Items.FindByID(0x1EB8,-1,Player.Backpack.Serial))
                        Gumps.WaitForGump(  949095101,500)
                        Gumps.SendAction(  949095101, 36)
                        Gumps.WaitForGump(  949095101,500)
                        Gumps.SendAction(  949095101, 23)
                        Gumps.WaitForGump(  949095101,500)
                        Gumps.CloseGump(  949095101)
                    while Items.BackpackCount(0x0E86,-1) < 3:
                        Items.UseItem(Items.FindByID(0x1EB8,-1,Player.Backpack.Serial))
                        Gumps.WaitForGump(  949095101,500)
                        Gumps.SendAction(  949095101, 36)
                        Gumps.WaitForGump(  949095101,500)
                        Gumps.SendAction(  949095101, 114)
                        Gumps.WaitForGump(  949095101,500)
                        Gumps.CloseGump(  949095101)
                tool = selectTool()
                Misc.Pause(200)
                if tool == None:
                    noTools = True
                    break

            ore_deposits = [0x1365, 0x1364, 0x1362, 0x1367]
            
            for deposit_id in ore_deposits:
                while Items.FindByID(deposit_id,-1,-1,3):
                    Items.UseItem(tool)
                    Target.WaitForTarget(650,1)
                    Target.TargetExecute(Items.FindByID(deposit_id,-1,-1,3))
                    Misc.Pause(1700)  # 1.5 second delay + 200ms buffer
                    
                    if usePackHorses and Player.Weight > Player.MaxWeight-12:
                        Misc.SendMessage( 'Player overweight! Moving ore to pack horses.', 90 )
                        movedAllOre = MoveOreToPackHorses()
                        if movedAllOre == False:
                            ForgeOres()
                    if useFireBeetle and Player.Weight > Player.MaxWeight-12:
                        ForgeOres()
            
            Target.TargetResource(tool,0)

            Misc.Pause( 500 )
            if Journal.SearchByType( 'Target cannot be seen.', 'Regular' ):
                Journal.Clear()
                break

            if usePackHorses and Player.Weight > Player.MaxWeight-12:
                Misc.SendMessage( 'Player overweight! Moving ore to pack horses.', 90 )
                movedAllOre = MoveOreToPackHorses()
                if movedAllOre == False:
                    ForgeOres()
            elif Player.Weight > Player.MaxWeight-12:
                ForgeOres()
                    
        else:                   
            if usePackHorses and Player.Weight > Player.MaxWeight-12:
                Misc.SendMessage( 'Player overweight! Moving ore to pack horses.', 90 )
                movedAllOre = MoveOreToPackHorses()
                if movedAllOre == False:
                    ForgeOres()
            elif Player.Weight > Player.MaxWeight-12:
                ForgeOres()


    Player.HeadMessage( 1100, 'No more ore to mine here!' )


if resetPackHorses:
    resetPackHorseMemory()
    Player.HeadMessage(88, 'Pack horses reset! Change resetPackHorses to False and restart.')
    exit()

if usePackHorses:
    savedHorses = 0
    for i in range(5):
        if Misc.CheckSharedValue(f'packHorse{i+1}'):
            savedHorses += 1
    
    if savedHorses < 5:
        Player.HeadMessage(88, 'Setting up pack horses...')
        resetPackHorseMemory()
    else:
        Player.HeadMessage(88, 'Loading pack horses from memory...')
        loadPackHorsesFromMemory()
    
if useFireBeetle:
    if not Misc.CheckSharedValue( 'petFireBeetle1' ):
        if Player.Mount != None:
            Mobiles.UseMobile( Player.Serial )
            Misc.Pause(800)
        petFireTarget = Target.PromptTarget( 'Select your Fire Beetle', 90 )    
        Misc.SetSharedValue( 'petFireBeetle1', petFireTarget )
    petFire = Mobiles.FindBySerial( Misc.ReadSharedValue( 'petFireBeetle1' ) )

while noTools == False:
    Mine()