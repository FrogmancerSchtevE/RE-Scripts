#Spellbook Crafter by Frank Castle
#
# Instructions:
#
# Have plenty of Exceptional Scribe's Pens with makers mark on them
# Have GM Inscription.  This will not check for fails until 7th circle. 
# Have a resource container with plenty of scrolls and regs
# Have at least 100 mana
# Have a trash can within reach
# Have your spellbook in your hand.  Do not have any other spellbooks in your backpack.
# Having Meditation and a Mana Regen suit is recommended, but not necessary. 
# This is not set to loop.  It will make one spellbook at the moment. 
#           This can be changed by making the last line a while True statement

from System.Collections.Generic import List

mandrakeroot = 0x0F86
bloodmoss = 0x0F7B
sulphurousash = 0x0F8C
nightshade = 0x0F88
blackpearl = 0x0F7A
spidersilk = 0x0F86
ginseng = 0x0F85
garlic = 0x0F84
stoCont = Target.PromptTarget('Target your Storage Container')
Items.UseItem(stoCont)
Misc.Pause(2000)

regsList = [0x0F86,0x0F7B,0x0F8C,0x0F88,0x0F7A,0x0F8D,0x0F85,0x0F84,0x0EF3]
global pen
pen = Items.FindByID(0x0FBF,-1,Player.Backpack.Serial)

GFilter = Items.Filter()
GFilter.RangeMax = 5
GFilter.OnGround = True
GFilter.Enabled = True
GFilter.Movable = True
garbagecan = List[int]((0x0E77, 0x0E77))  
GFilter.Graphics = garbagecan

def getSupplies():
    for i in regsList:
        if Items.BackpackCount(i,-1) < 30:
            reg = Items.FindByID(i,-1,stoCont)
            Misc.Pause(500)
            Items.Move(reg,Player.Backpack.Serial,100)
            Misc.Pause(1100)
            
def makeSpellbook():
    getSupplies()
    Items.UseItem(pen)
    Gumps.WaitForGump(460, 1500)
    Gumps.SendAction(460, 202)
    Misc.Pause(3000)
    spellbook = Items.FindByID(0x0EFA,-1,Player.Backpack.Serial)
    if not spellbook:
        makeSpellbook()
        
def checkPen():
    curCharges = Items.FindByID(0x0FBF,-1,Player.Backpack.Serial)
    Items.WaitForProps(curCharges,2000)
    props = Items.GetPropStringList(curCharges.Serial)
    Misc.Pause(500)
    prop = props[3].split(' ')[2]
    Misc.SendMessage(prop)
    Misc.Pause(500)
    if int(prop) < 20:
        global pen
        garbagecans = Items.ApplyFilter(GFilter)
        Misc.Pause(500)
        garbagecan = Items.Select(garbagecans, 'Nearest')
        Misc.Pause(500)
        Items.Move(pen,garbagecan,0)
        Misc.Pause(1100)
        checkPen()
        pen = Items.FindByID(0x0FBF,-1,Player.Backpack.Serial)
      
    
def makeFirstCircle():
    while Player.Mana < Player.ManaMax :
        Player.UseSkill('Meditation')
        Misc.Pause(10000)
    getSupplies()
    checkPen()
    Items.UseItem(pen)
    Misc.Pause(1100)
    gumpNo = 1
    while gumpNo < 9:
        Gumps.WaitForGump(460, 1500)
        Gumps.SendAction(460, gumpNo)
        gumpNo = gumpNo + 1
        
    firstCircleList = [0x1F2E,0x1F2F,0x1F30,0x1F31,0x1F32,0x1F33,0x1F2D,0x1F34]
    Misc.Pause(1100)
    for a in firstCircleList:
        spellbook = Items.FindByID(0x0EFA,-1,Player.Backpack.Serial)
        scroll = Items.FindByID(a,-1,Player.Backpack.Serial)
        if scroll:
            Items.Move(scroll,spellbook,1)
            Misc.Pause(1100)
            
def makeSecondCircle():
    while Player.Mana < Player.ManaMax:
        Player.UseSkill('Meditation')
        Misc.Pause(10000)
    getSupplies()
    checkPen()
    Items.UseItem(pen)
    Misc.Pause(1100)
    gumpNo = 9
    while gumpNo < 17:
        Gumps.WaitForGump(460, 1500)
        Gumps.SendAction(460, gumpNo)
        gumpNo = gumpNo + 1
        
    secondCircleList = [0x1F35,0x1F36,0x1F37,0x1F38,0x1F39,0x1F3A,0x1F3B,0x1F3C]
    Misc.Pause(1100)
    for a in secondCircleList:
        spellbook = Items.FindByID(0x0EFA,-1,Player.Backpack.Serial)
        scroll = Items.FindByID(a,-1,Player.Backpack.Serial)
        if scroll:
            Items.Move(scroll,spellbook,1)
            Misc.Pause(1100)            

def checkMana(mana):
    while Player.Mana < mana:
        Player.UseSkill('Meditation')
        Misc.Pause(11500)
            
def makeThirdCircle():
    while Player.Mana < 100:
        Player.UseSkill('Meditation')
        Misc.Pause(10000)
    getSupplies()
    checkPen()
    Items.UseItem(pen)
    Misc.Pause(1100)
    gumpNo = 17
    while gumpNo < 25:
        Gumps.WaitForGump(460, 1500)
        Gumps.SendAction(460, gumpNo)
        gumpNo = gumpNo + 1
        
    thirdCircleList = [0x1F3D,0x1F3E,0x1F3F,0x1F40,0x1F41,0x1F42,0x1F43,0x1F44]
    Misc.Pause(1100)
    for a in thirdCircleList:
        spellbook = Items.FindByID(0x0EFA,-1,Player.Backpack.Serial)
        scroll = Items.FindByID(a,-1,Player.Backpack.Serial)
        if scroll:
            Items.Move(scroll,spellbook,1)
            Misc.Pause(1100)
            
def makeFourthCircle():
    while Player.Mana < Player.ManaMax:
        Player.UseSkill('Meditation')
        Misc.Pause(10000)
    getSupplies()
    checkPen()
    Items.UseItem(pen)
    Misc.Pause(1100)
    gumpNo = 25
    while gumpNo < 33:
        Gumps.WaitForGump(460, 1500)
        Gumps.SendAction(460, gumpNo)
        gumpNo = gumpNo + 1
        
    fourthCircleList = [0x1F45,0x1F46,0x1F47,0x1F48,0x1F49,0x1F4A,0x1F4B,0x1F4C]
    Misc.Pause(1100)
    for a in fourthCircleList:
        spellbook = Items.FindByID(0x0EFA,-1,Player.Backpack.Serial)
        scroll = Items.FindByID(a,-1,Player.Backpack.Serial)
        if scroll:
            Items.Move(scroll,spellbook,1)
            Misc.Pause(1100)
            
def makeFifthCircle():
    while Player.Mana < Player.ManaMax:
        Player.UseSkill('Meditation')
        Misc.Pause(10000)
    getSupplies()
    checkPen()
    Items.UseItem(pen)
    Misc.Pause(1100)
    gumpNo = 33
    while gumpNo < 41:
        checkMana(20)
        Gumps.WaitForGump(460, 1500)
        Gumps.SendAction(460, gumpNo)
        gumpNo = gumpNo + 1
        
    fifthCircleList = [0x1F4D,0x1F4E,0x1F4F,0x1F50,0x1F51,0x1F52,0x1F53,0x1F54,]
    Misc.Pause(1100)
    for a in fifthCircleList:
        spellbook = Items.FindByID(0x0EFA,-1,Player.Backpack.Serial)
        scroll = Items.FindByID(a,-1,Player.Backpack.Serial)
        if scroll:
            Items.Move(scroll,spellbook,1)
            Misc.Pause(1100)

def makeSixthCircle():
    while Player.Mana < Player.ManaMax:
        Player.UseSkill('Meditation')
        Misc.Pause(10000)
    getSupplies()
    checkPen()
    
    gumpNo = 41
    while gumpNo < 49:
        checkMana(30)
        Items.UseItem(pen)
        Misc.Pause(1100)
        Gumps.WaitForGump(460, 1500)
        Gumps.SendAction(460, gumpNo)
        gumpNo = gumpNo + 1
        Misc.Pause(1100)
        
    sixthCircleList = [0x1F55,0x1F56,0x1F57,0x1F58,0x1F59,0x1F5A,0x1F5B,0x1F5C]
    Misc.Pause(1100)
    for a in sixthCircleList:
        spellbook = Items.FindByID(0x0EFA,-1,Player.Backpack.Serial)
        scroll = Items.FindByID(a,-1,Player.Backpack.Serial)
        if scroll:
            Items.Move(scroll,spellbook,1)
            Misc.Pause(1100)
            
def makeSeventhCircle():
    while Player.Mana < Player.ManaMax:
        Player.UseSkill('Meditation')
        Misc.Pause(10000)
    getSupplies()
    checkPen()
    spellbook = Items.FindByID(0x0EFA,-1,Player.Backpack.Serial)
    def makechain():
        checkMana(50)
        Items.UseItem(pen)
        Misc.Pause(1100)
        Gumps.WaitForGump(460, 1500)
        Gumps.SendAction(460, 49)
        Misc.Pause(2000)
        scroll = Items.FindByID(0x1F5D,-1,Player.Backpack.Serial)
        if scroll:
            Items.Move(scroll,spellbook,1)
            Misc.Pause(1100)
        else:
            makechain()
    def makeenergy():
        checkMana(50)
        Items.UseItem(pen)
        Misc.Pause(1100)
        Gumps.WaitForGump(460, 1500)
        Gumps.SendAction(460, 50)
        Misc.Pause(2000)
        scroll = Items.FindByID(0x1F5E,-1,Player.Backpack.Serial)
        if scroll:
            Items.Move(scroll,spellbook,1)
            Misc.Pause(1100)
        else:
            makeenergy()            
    def makeflame():
        checkMana(50)
        Items.UseItem(pen)
        Misc.Pause(1100)
        Gumps.WaitForGump(460, 1500)
        Gumps.SendAction(460, 51)
        Misc.Pause(2000)
        scroll = Items.FindByID(0x1F5F,-1,Player.Backpack.Serial)
        if scroll:
            Items.Move(scroll,spellbook,1)
            Misc.Pause(1100)
        else:
            makeflame()            
    def makegate():
        checkMana(50)
        Items.UseItem(pen)
        Misc.Pause(1100)
        Gumps.WaitForGump(460, 1500)
        Gumps.SendAction(460, 52)
        Misc.Pause(2000)
        scroll = Items.FindByID(0x1F60,-1,Player.Backpack.Serial)
        if scroll:
            Items.Move(scroll,spellbook,1)
            Misc.Pause(1100)
        else:
            makegate()        
    def makemanaV():
        checkMana(50)
        Items.UseItem(pen)
        Misc.Pause(1100)
        Gumps.WaitForGump(460, 1500)
        Gumps.SendAction(460, 53)
        Misc.Pause(2000)
        scroll = Items.FindByID(0x1F61,-1,Player.Backpack.Serial)
        if scroll:
            Items.Move(scroll,spellbook,1)
            Misc.Pause(1100)
        else:
            makemanaV()    
    def makemass():
        checkMana(50)
        Items.UseItem(pen)
        Misc.Pause(1100)
        Gumps.WaitForGump(460, 1500)
        Gumps.SendAction(460, 54)
        Misc.Pause(2000)
        scroll = Items.FindByID(0x1F62,-1,Player.Backpack.Serial)
        if scroll:
            Items.Move(scroll,spellbook,1)
            Misc.Pause(1100)
        else:
            makemass()    
    def makemeteor():
        checkMana(50)
        Items.UseItem(pen)
        Misc.Pause(1100)
        Gumps.WaitForGump(460, 1500)
        Gumps.SendAction(460, 55)
        Misc.Pause(2000)
        scroll = Items.FindByID(0x1F63,-1,Player.Backpack.Serial)
        if scroll:
            Items.Move(scroll,spellbook,1)
            Misc.Pause(1100)
        else:
            makemeteor()
    def makepoly():
        checkMana(50)
        Items.UseItem(pen)
        Misc.Pause(1100)
        Gumps.WaitForGump(460, 1500)
        Gumps.SendAction(460, 56)
        Misc.Pause(2000)
        scroll = Items.FindByID(0x1F64,-1,Player.Backpack.Serial)
        if scroll:
            Items.Move(scroll,spellbook,1)
            Misc.Pause(1100)
        else:
            makepoly()
    makechain()
    makeenergy()
    makeflame()
    makegate()
    makemanaV()
    makemass()
    makemeteor()
    makepoly()
       
def makeEighthCircle():
    while Player.Mana < Player.ManaMax:
        Player.UseSkill('Meditation')
        Misc.Pause(10000)
    getSupplies()
    checkPen()
    spellbook = Items.FindByID(0x0EFA,-1,Player.Backpack.Serial)
    def makequake():
        checkMana(50)
        Items.UseItem(pen)
        Misc.Pause(1100)
        Gumps.WaitForGump(460, 1500)
        Gumps.SendAction(460, 57)
        Misc.Pause(2000)
        scroll = Items.FindByID(0x1F65,-1,Player.Backpack.Serial)
        if scroll:
            Items.Move(scroll,spellbook,1)
            Misc.Pause(1100)
        else:
            makequake()
    def makevortex():
        checkMana(50)
        Items.UseItem(pen)
        Misc.Pause(1100)
        Gumps.WaitForGump(460, 1500)
        Gumps.SendAction(460, 58)
        Misc.Pause(2000)
        scroll = Items.FindByID(0x1F66,-1,Player.Backpack.Serial)
        if scroll:
            Items.Move(scroll,spellbook,1)
            Misc.Pause(1100)
        else:
            makevortex()            
    def makeres():
        checkMana(50)
        Items.UseItem(pen)
        Misc.Pause(1100)
        Gumps.WaitForGump(460, 1500)
        Gumps.SendAction(460, 59)
        Misc.Pause(2000)
        scroll = Items.FindByID(0x1F67,-1,Player.Backpack.Serial)
        if scroll:
            Items.Move(scroll,spellbook,1)
            Misc.Pause(1100)
        else:
            makeres()            
    def makeair():
        checkMana(50)
        Items.UseItem(pen)
        Misc.Pause(1100)
        Gumps.WaitForGump(460, 1500)
        Gumps.SendAction(460, 60)
        Misc.Pause(2000)
        scroll = Items.FindByID(0x1F68,-1,Player.Backpack.Serial)
        if scroll:
            Items.Move(scroll,spellbook,1)
            Misc.Pause(1100)
        else:
            makeair()        
    def makedemon():
        checkMana(50)
        Items.UseItem(pen)
        Misc.Pause(1100)
        Gumps.WaitForGump(460, 1500)
        Gumps.SendAction(460, 61)
        Misc.Pause(2000)
        scroll = Items.FindByID(0x1F69,-1,Player.Backpack.Serial)
        if scroll:
            Items.Move(scroll,spellbook,1)
            Misc.Pause(1100)
        else:
            makedemon()    
    def makeearth():
        checkMana(50)
        Items.UseItem(pen)
        Misc.Pause(1100)
        Gumps.WaitForGump(460, 1500)
        Gumps.SendAction(460, 62)
        Misc.Pause(2000)
        scroll = Items.FindByID(0x1F6A,-1,Player.Backpack.Serial)
        if scroll:
            Items.Move(scroll,spellbook,1)
            Misc.Pause(1100)
        else:
            makeearth()    
    def makefireE():
        checkMana(50)
        Items.UseItem(pen)
        Misc.Pause(1100)
        Gumps.WaitForGump(460, 1500)
        Gumps.SendAction(460, 63)
        Misc.Pause(2000)
        scroll = Items.FindByID(0x1F6B,-1,Player.Backpack.Serial)
        if scroll:
            Items.Move(scroll,spellbook,1)
            Misc.Pause(1100)
        else:
            makefireE()
    def makewater():
        checkMana(50)
        Items.UseItem(pen)
        Misc.Pause(1100)
        Gumps.WaitForGump(460, 1500)
        Gumps.SendAction(460, 64)
        Misc.Pause(2000)
        scroll = Items.FindByID(0x1F6C,-1,Player.Backpack.Serial)
        if scroll:
            Items.Move(scroll,spellbook,1)
            Misc.Pause(1100)
        else:
            makewater()
    makequake()
    makevortex()
    makeres()
    makeair()
    makedemon()
    makeearth()
    makefireE()
    makewater()
    Items.Move(spellbook,stoCont,0)
        
def makeBook():
    makeSpellbook()
    makeFirstCircle()
    makeSecondCircle()
    makeThirdCircle()
    makeFourthCircle()
    makeFifthCircle()
    makeSixthCircle()
    makeSeventhCircle()
    makeEighthCircle()

makeBook()    
            



    
    