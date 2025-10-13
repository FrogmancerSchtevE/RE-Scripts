using RazorEnhanced;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace Project
{
    internal class ScriptProject
    {
        private enum ReservedGumpButtonIdType
        {
            None,
            ApplicationRunning,
            Ground,
            Auto,
            Ignore,
            ReturnToMain,
            Active,
            ManualRemoveItem
        }

        private enum MainMenuType
        {
            None,
            GroundLoot,
            AutoLoot,
            IgnoreLoot
        }

        private enum SubMenuType
        {
            None,
            GroundSelected,
            AutoSelected,
            IgnoreSelected
        }

        private const int buttonIdStartCount = 100;
        private const string filePath = @"H:\Random Stuff\ER-UO\LooterProject";


        private List<Mobile> mobileList;
        private List<Item> itemsList;

        private bool isRunning;
        private Gumps.GumpData gump;
        private const uint gumpId = 694201001;
        private MainMenuType mainMenuType;
        private SubMenuType subMenuGroundLootType;

        private SubMenuType subMenuAutoLootType;
        private Dictionary<int, string> autoLootItemIdDictionary;
        private bool isAutoLootActive;

        private SubMenuType subMenuIgnoreLootType;
        private Dictionary<int, string> ignoreLootItemIdDictionary;
        private bool isIgnoreLootActive;

        private int serialLootBag;



        private void Run()
        {
            this.mobileList = new List<Mobile>();
            this.itemsList = new List<Item>();

            this.autoLootItemIdDictionary = this.ReadHexListFromFile("AutoLoot.txt");
            this.ignoreLootItemIdDictionary = this.ReadHexListFromFile("IgnoreLoot.txt");
            this.Log(this.autoLootItemIdDictionary.Count);
            this.Log(this.ignoreLootItemIdDictionary.Count);
            this.isRunning = true;

            this.isAutoLootActive = true;
            this.isIgnoreLootActive = true;
            this.mainMenuType = MainMenuType.GroundLoot;
            this.subMenuGroundLootType = SubMenuType.GroundSelected;
            this.CreateMenuInstance();

            while (this.isRunning == true)
            {
                Misc.Pause(1);
                //Misc.Pause(5000);

                if (this.serialLootBag > 0)
                {
                    if (this.mainMenuType == MainMenuType.GroundLoot)
                    {
                        var hasItemUpdate = this.UpdateItemsList();
                        if (hasItemUpdate == true)
                        {
                            this.CreateMenuInstance();
                        }

                        //var hasMobileUpdate = this.UpdateMobileList();
                        //if (hasMobileUpdate == true)
                        //{
                        //    this.CreateMenuInstance();
                        //}
                    }
                }

                this.EventListeners();
            }
        }

        private bool UpdateMobileList()
        {
            var placeHolder = 0;
            if (placeHolder == 0)
            { return false; }

            var filter = new Mobiles.Filter();
            filter.Enabled = false;

            this.mobileList = Mobiles.ApplyFilter(filter);

            return true;
        }

        private long timer;
        private bool UpdateItemsList()
        {
            if (UnixTime() - this.timer < 1500)
            { return false; }
            this.timer = UnixTime();

            var filter = new Items.Filter();
            filter.Enabled = false;

            this.itemsList = Items.ApplyFilter(filter);

            return true;
        }

        private static long UnixTime()
        {
            return (long)(DateTime.UtcNow - new DateTime(1970, 1, 1)).TotalMilliseconds;
        }

        private void Log(object messageString)
        {
            Misc.SendMessage(messageString, 201);
        }

        private List<Item> GetFilteredItemsList()
        {
            var filteredItemsList = new List<Item>();

            var count = 0;
            for (var i = 0; i < this.itemsList.Count; i++)
            {
                if (count > 17)
                {
                    break;
                }

                var item = this.itemsList[i];

                if (item.Image == null)
                { continue; }

                if (item.RootContainer == Player.Backpack.Serial)
                { continue; }

                if (item.RootContainer == Player.Serial)
                { continue; }

                if (item.IsLootable == false)
                { continue; }

                if (item.Movable == false)
                { continue; }

                if (item.Visible == false)
                { continue; }

                if (item.IsInBank == true)
                { continue; }

                if (item.OnGround == false)
                {
                    var groundContainer = Items.FindBySerial(item.RootContainer);
                    if (groundContainer?.RootContainer != 0)
                    { continue; }


                    var mobile = Mobiles.FindBySerial(item.RootContainer);
                    if (mobile?.Serial == item.RootContainer)
                    { continue; }


                    if (item.RootContainer == Player.Backpack.Serial)
                    {
                        continue;
                    }
                }
                else
                {
                    var distanceToItem = Player.DistanceTo(item);
                    if (distanceToItem > 2)
                    { continue; }
                }

                if (this.isAutoLootActive == true)
                {
                    if (this.autoLootItemIdDictionary.ContainsKey(item.ItemID))
                    {
                        if (Player.Visible == false)
                        { continue; }

                        if (item.RootContainer == this.serialLootBag)
                        { continue; }

                        Items.Move(item.Serial, this.serialLootBag, -1);
                        Misc.Pause(250);

                        continue;
                    }
                }

                if (this.isIgnoreLootActive == true)
                {
                    var ignoreLootItemFound = this.ignoreLootItemIdDictionary.ContainsKey(item.ItemID);
                    if (ignoreLootItemFound == true)
                    { continue; }
                }


                //this.Log(item.RootContainer.ToString("X4") + " - " + item.RootContainer.ToString("X4") + " - " + item.Serial.ToString("X8") + " - " + item.Name + " D:" + Player.DistanceTo(item));


                count++;
                filteredItemsList.Add(item);
            }

            return filteredItemsList;
        }

        #region MENUS
        private void ImageButtonMenuPositioner(int posX, int posY, ReservedGumpButtonIdType reservedGumpButtonIdType, bool isSelected, int imageId, int imageHue)
        {
            var itemImage = Items.GetImage(imageId);
            var iWidth = itemImage.Size.Width;
            var iHeight = itemImage.Size.Height;

            var iPosX = (110 / 2) - (iWidth / 2) - 25;
            var iPosY = (62 / 2) - (iHeight / 2);

            if (isSelected == true)
            {
                Gumps.AddImageTiled(ref this.gump, posX + 6, posY + 6, 110 - 64, 62 - 24, 5058);
            }
            else
            {
                Gumps.AddImageTiled(ref this.gump, posX + 6, posY + 6, 110 - 64, 62 - 24, 3604);
            }

            Gumps.AddImageTiledButton(ref this.gump, posX, posY, 82, 82, (int)reservedGumpButtonIdType, Gumps.GumpButtonType.Reply, 0, imageId, imageHue, iPosX, iPosY);
        }

        private void ImageButtonPositioner(int posX, int posY, int buttonId, int itemId)
        {
            try
            {
                var item = Items.FindByID(itemId, -1, -1);

                var iWidth = item.Image.Size.Width;
                var iHeight = item.Image.Size.Height;

                var iPosX = (110 / 2) - (iWidth / 2);
                var iPosY = (62 / 2) - (iHeight / 2);

                Gumps.AddImageTiled(ref this.gump, posX + 3, posY + 3, 110 - 6, 62 - 6, 3604);

                Gumps.AddImageTiledButton(ref this.gump, posX, posY, 82, 82, buttonId, Gumps.GumpButtonType.Reply, -1, itemId, item.Hue, iPosX, iPosY);
            }
            catch
            {
                this.Log("> Error -> ImageButtonPositioner " + itemId);
            }
        }

        private void CreateMenuInstance()
        {
            Gumps.CloseGump(gumpId);

            this.gump = Gumps.CreateGump(true, false, true, false);
            this.gump.gumpId = gumpId;
            this.gump.serial = (uint)Player.Serial;
            Gumps.AddPage(ref this.gump, 0);

            Gumps.AddBackground(ref this.gump, 0, 0, 375, 480, 5054);
            Gumps.AddImageTiled(ref this.gump, 10, 10, 355, 50, 3004);
            Gumps.AddAlphaRegion(ref this.gump, 10, 10, 355, 460);

            Gumps.AddButton(ref this.gump, 347, -2, 4017, 4018, (int)ReservedGumpButtonIdType.ApplicationRunning, (int)Gumps.GumpButtonType.Reply, 0);

            if (this.serialLootBag > 0)
            {
                var lootBag = Items.FindBySerial(this.serialLootBag);
                if (lootBag == null)
                {
                    this.serialLootBag = 0;
                    this.mainMenuType = MainMenuType.GroundLoot;
                    this.subMenuGroundLootType = SubMenuType.GroundSelected;
                }
            }

            if (this.mainMenuType == MainMenuType.GroundLoot)
            {
                this.MainMenuGroundLoot();
            }
            else if (this.mainMenuType == MainMenuType.AutoLoot)
            {
                this.MainMenuAutoLoot();
            }
            else if (this.mainMenuType == MainMenuType.IgnoreLoot)
            {
                this.MainMenuIgnoreLoot();
            }

            Gumps.SendGump(this.gump.gumpId, this.gump.serial, 0, 0, this.gump.gumpDefinition, this.gump.gumpStrings);
        }

        private void MainMenuGroundLoot()
        {
            if (this.serialLootBag == 0)
            {
                this.ImageButtonMenuPositioner(10, 10, ReservedGumpButtonIdType.Ground, true, 0x0E75, 37);
            }
            else
            {
                Gumps.AddItem(ref this.gump, 10, 23, 0x0E75);

                var isGroundSelected = false;
                var isAutoSelected = false;
                var isIgnoreSelected = false;
                if (this.subMenuGroundLootType == SubMenuType.GroundSelected) { isGroundSelected = true; }
                else if (this.subMenuGroundLootType == SubMenuType.AutoSelected) { isAutoSelected = true; }
                else if (this.subMenuGroundLootType == SubMenuType.IgnoreSelected) { isIgnoreSelected = true; }

                this.ImageButtonMenuPositioner(55, 10, ReservedGumpButtonIdType.Ground, isGroundSelected, 0x0E75, 0);
                this.ImageButtonMenuPositioner(105, 10, ReservedGumpButtonIdType.Auto, isAutoSelected, 0x1B53, 0);
                this.ImageButtonMenuPositioner(155, 10, ReservedGumpButtonIdType.Ignore, isIgnoreSelected, 0x0E7F, 0);
            }

            var posX = 17;
            var posY = 67;
            var buttonIdCount = buttonIdStartCount;
            var filteredItemsList = this.GetFilteredItemsList();
            for (var i = 0; i < filteredItemsList.Count; i++)
            {
                var item = filteredItemsList[i];
                this.ImageButtonPositioner(posX, posY, buttonIdCount++, item.ItemID);

                posX += 110 + 5;
                if (posX > 330 + 15)
                {
                    posX = 17;
                    posY += 62 + 5;
                }
            }
        }

        private void MainMenuAutoLoot()
        {
            Gumps.AddItem(ref this.gump, 15, 23, 0x1B53);

            Gumps.AddImageTiled(ref this.gump, 65, 15, 40, 40, 3604);
            Gumps.AddButton(ref this.gump, 74, 23, 9909, 9910, (int)ReservedGumpButtonIdType.ReturnToMain, (int)Gumps.GumpButtonType.Reply, 0);

            if (this.isAutoLootActive == true)
            {
                Gumps.AddImageTiled(ref this.gump, 112, 15, 40, 40, 3604);
                Gumps.AddButton(ref this.gump, 117, 20, 2153, 2153, (int)ReservedGumpButtonIdType.Active, (int)Gumps.GumpButtonType.Reply, 0);
            }
            else
            {
                Gumps.AddImageTiled(ref this.gump, 112, 15, 40, 40, 3604);
                Gumps.AddButton(ref this.gump, 118, 20, 2472, 2472, (int)ReservedGumpButtonIdType.Active, (int)Gumps.GumpButtonType.Reply, 0);
            }


            Gumps.AddImageTiled(ref this.gump, 160, 15, 120, 40, 3604);
            Gumps.AddImageTiled(ref this.gump, 170, 22, 58, 25, 2604);
            Gumps.AddTextEntry(ref this.gump, 175, 25, 50, 25, 1150, 1, "");
            Gumps.AddButton(ref this.gump, 240, 19, 10850, 10850, (int)ReservedGumpButtonIdType.ManualRemoveItem, (int)Gumps.GumpButtonType.Reply, 0);

            var sortedItemList = this.autoLootItemIdDictionary.ToList();
            sortedItemList.Sort((x, y) => x.Value.CompareTo(y.Value));

            var htmlString = "";
            foreach (var sortedItem in sortedItemList)
            {
                var hexString = "0x" + sortedItem.Key.ToString("X4");
                htmlString += hexString + " - " + sortedItem.Value + "</BR>";
            }

            Gumps.AddHtml(ref this.gump, 15, 65, 340, 395, htmlString, false, true);
        }

        private void MainMenuIgnoreLoot()
        {
            Gumps.AddItem(ref this.gump, 15, 23, 0x0E7F);

            Gumps.AddImageTiled(ref this.gump, 65, 15, 40, 40, 3604);
            Gumps.AddButton(ref this.gump, 74, 23, 9909, 9910, (int)ReservedGumpButtonIdType.ReturnToMain, (int)Gumps.GumpButtonType.Reply, 0);

            if (this.isAutoLootActive == true)
            {
                Gumps.AddImageTiled(ref this.gump, 112, 15, 40, 40, 3604);
                Gumps.AddButton(ref this.gump, 117, 20, 2153, 2153, (int)ReservedGumpButtonIdType.Active, (int)Gumps.GumpButtonType.Reply, 0);
            }
            else
            {
                Gumps.AddImageTiled(ref this.gump, 112, 15, 40, 40, 3604);
                Gumps.AddButton(ref this.gump, 118, 20, 2472, 2472, (int)ReservedGumpButtonIdType.Active, (int)Gumps.GumpButtonType.Reply, 0);
            }


            Gumps.AddImageTiled(ref this.gump, 160, 15, 120, 40, 3604);
            Gumps.AddImageTiled(ref this.gump, 170, 22, 58, 25, 2604);
            Gumps.AddTextEntry(ref this.gump, 175, 25, 200, 25, 1150, 1, "");
            Gumps.AddButton(ref this.gump, 240, 19, 10850, 10850, (int)ReservedGumpButtonIdType.ManualRemoveItem, (int)Gumps.GumpButtonType.Reply, 0);






            var sortedItemList = this.ignoreLootItemIdDictionary.ToList();
            sortedItemList.Sort((x, y) => x.Value.CompareTo(y.Value));

            var htmlString = "";
            foreach (var sortedItem in sortedItemList)
            {
                var hexString = "0x" + sortedItem.Key.ToString("X4");
                htmlString += hexString + " - " + sortedItem.Value + "</BR>";
            }

            Gumps.AddHtml(ref this.gump, 15, 65, 340, 395, htmlString, false, true);
        }
        #endregion

        #region EVENT LISTENERS
        private void EventListeners()
        {
            var gumpData = Gumps.GetGumpData(gumpId);

            this.EventListenerMainMenu(gumpData);
            this.EventListenerItemSelect(gumpData);
        }

        private void EventListenerMainMenu(Gumps.GumpData gumpData)
        {
            if (gumpData.buttonid >= 100)
            { return; }

            if (gumpData.buttonid == (int)ReservedGumpButtonIdType.ApplicationRunning)
            {
                this.isRunning = false;
            }
            else if (gumpData.buttonid == (int)ReservedGumpButtonIdType.Ground)
            {
                if (this.subMenuGroundLootType == SubMenuType.GroundSelected)
                {
                    this.mainMenuType = MainMenuType.GroundLoot;

                    while (true)
                    {
                        var target = new Target();
                        var serialSelectedItem = target.PromptTarget("Select lootbag");
                        var item = Items.FindBySerial(serialSelectedItem);
                        if (item.IsContainer == false)
                        { continue; }
                        else
                        {
                            this.serialLootBag = serialSelectedItem;
                            break;
                        }
                    }
                }

                this.subMenuGroundLootType = SubMenuType.GroundSelected;

                this.CreateMenuInstance();
            }
            else if (gumpData.buttonid == (int)ReservedGumpButtonIdType.Auto)
            {
                // Main Menu GroundLoot
                if (this.mainMenuType == MainMenuType.GroundLoot)
                {
                    if (this.subMenuGroundLootType == SubMenuType.AutoSelected)
                    {
                        this.mainMenuType = MainMenuType.AutoLoot;
                    }

                    this.subMenuGroundLootType = SubMenuType.AutoSelected;
                }


                this.CreateMenuInstance();
            }
            else if (gumpData.buttonid == (int)ReservedGumpButtonIdType.Ignore)
            {
                // Main Menu GroundLoot
                if (this.mainMenuType == MainMenuType.GroundLoot)
                {
                    if (this.subMenuGroundLootType == SubMenuType.IgnoreSelected)
                    {
                        this.mainMenuType = MainMenuType.IgnoreLoot;
                    }

                    this.subMenuGroundLootType = SubMenuType.IgnoreSelected;
                }

                this.CreateMenuInstance();
            }
            else if (gumpData.buttonid == (int)ReservedGumpButtonIdType.ReturnToMain)
            {
                this.mainMenuType = MainMenuType.GroundLoot;
                this.subMenuGroundLootType = SubMenuType.GroundSelected;

                this.CreateMenuInstance();
            }
            else if (gumpData.buttonid == (int)ReservedGumpButtonIdType.Active)
            {
                if (this.mainMenuType == MainMenuType.AutoLoot)
                {
                    if (this.isAutoLootActive == true)
                    {
                        this.isAutoLootActive = false;
                    }
                    else
                    {
                        this.isAutoLootActive = true;
                    }
                }
                else if (this.mainMenuType == MainMenuType.IgnoreLoot)
                {
                    if (this.isIgnoreLootActive == true)
                    {
                        this.isIgnoreLootActive = false;
                    }
                    else
                    {
                        this.isIgnoreLootActive = true;
                    }
                }

                this.CreateMenuInstance();
            }
            if (gumpData.buttonid == (int)ReservedGumpButtonIdType.ManualRemoveItem)
            {
                var isValid = int.TryParse(gumpData.text[0], System.Globalization.NumberStyles.HexNumber, null, out var parsedValue);
                if (isValid == true)
                {
                    if (this.mainMenuType == MainMenuType.AutoLoot)
                    {
                        this.autoLootItemIdDictionary.Remove(parsedValue);

                        this.WriteHexListToFile(this.autoLootItemIdDictionary, "AutoLoot.txt");

                    }
                    else if (this.mainMenuType == MainMenuType.IgnoreLoot)
                    {
                        this.ignoreLootItemIdDictionary.Remove(parsedValue);

                        this.WriteHexListToFile(this.ignoreLootItemIdDictionary, "IgnoreLoot.txt");
                    }
                }

                this.CreateMenuInstance();
            }
        }

        private void EventListenerItemSelect(Gumps.GumpData gumpData)
        {
            if (gumpData.buttonid < 100)
            { return; }

            if (this.mainMenuType == MainMenuType.GroundLoot)
            {
                var buttonIdCount = buttonIdStartCount;
                var filteredItemsList = this.GetFilteredItemsList();
                var selectedItem = filteredItemsList[gumpData.buttonid - buttonIdCount];

                if (this.subMenuGroundLootType == SubMenuType.GroundSelected)
                {
                    Items.Move(selectedItem.Serial, this.serialLootBag, -1);

                    this.CreateMenuInstance();
                }
                else if (this.subMenuGroundLootType == SubMenuType.AutoSelected)
                {
                    var inputString = selectedItem.Name;
                    var indexOfParenthesis = inputString.IndexOf('(');

                    if (indexOfParenthesis != -1)
                    { inputString = inputString.Substring(0, indexOfParenthesis).Trim(); }

                    this.autoLootItemIdDictionary.Add(selectedItem.ItemID, inputString);

                    this.WriteHexListToFile(this.autoLootItemIdDictionary, "AutoLoot.txt");

                    this.CreateMenuInstance();
                }
                else if (this.subMenuGroundLootType == SubMenuType.IgnoreSelected)
                {
                    var inputString = selectedItem.Name;
                    var indexOfParenthesis = inputString.IndexOf('(');

                    if (indexOfParenthesis != -1)
                    { inputString = inputString.Substring(0, indexOfParenthesis).Trim(); }

                    this.ignoreLootItemIdDictionary.Add(selectedItem.ItemID, inputString);

                    this.WriteHexListToFile(this.ignoreLootItemIdDictionary, "IgnoreLoot.txt");

                    this.CreateMenuInstance();
                }
            }
        }
        #endregion

        #region READWRITE FILES
        private void WriteHexListToFile(Dictionary<int, string> hexList, string filename)
        {
            using (var writer = new StreamWriter(filePath + filename))
            {
                foreach (var kvp in hexList)
                {
                    var hexValue = kvp.Key;
                    var stringValue = kvp.Value;

                    writer.WriteLine($"0x{hexValue:X4}, {stringValue}");
                }
            }
        }

        private Dictionary<int, string> ReadHexListFromFile(string filename)
        {
            var hexValueStringPairs = new Dictionary<int, string>();

            if (File.Exists(filePath + filename))
            {
                var lines = File.ReadAllLines(filePath + filename);

                foreach (var line in lines)
                {
                    if (line.StartsWith("0x") && line.Length >= 8 && int.TryParse(line.Substring(2, 4), System.Globalization.NumberStyles.HexNumber, null, out var hexValue))
                    {
                        var stringValue = line.Substring(8);
                        hexValueStringPairs[hexValue] = stringValue;
                    }
                }
            }

            return hexValueStringPairs;
        }

        #endregion
    }
}