/*
 * ================================================
 * Extreme Treasure Hunting
 * ================================================
 *
 * Version: 1.0.2
 * Last Updated: 2025-07-02
 * Author: nkr
 *
 * ------------------------------------------------
 * Overview:
 * This script automates and assists with locating the treasure, digging it up,
 * unlocking the chest, disarming traps, looting (via LootMaster), and post-cleanup.
 *
 * One of the core features is automatic highlighting of the runebook
 * that contains the rune closest to the TMap location you're working on.
 * This makes navigation smooth and quick.
 *
 * The script supports:
 *  - Main public runebook sets from UOAlive
 *  - Your own custom runebook set
 *
 * ------------------------------------------------
 * Features:
 * ✔️ Gump to control all treasure hunting steps
 * ✔️ Runebook highlighter based on TMap coordinates
 * ✔️ Supports both public and private/custom runebook sets
 *
 * ------------------------------------------------
 * Configuration:
 * Scroll down for the configuration section
 *
 * ------------------------------------------------
 * Changelog:
 *
 * [1.0.2] - 2025-07-02
 *   - Removed auto remove chest functionality, player now has to click the confirm button on the gump
 *   - Automatically decodes maps
 * [1.0.1] - 2025-06-20
 *   - Added missing treasure chest item ID
 * [1.0.0] - 2025-06-19
 *   - Initial release
 *
 * ================================================
 */
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using System.Threading;
using RazorEnhanced;

namespace RazorEnhancedScripts.Scripts
{
    public class ExtremeTreasureHunting
    {
        private const string Version = "1.0.2";
        
        /* ------------------------------------------------
         * Configuration:
         *  Enable Looting button (requires LootMaster): */
        const bool LootmasterLooting = false;
        /*  Select your preferred Runebook set system (SEA, Leoncio or Custom): */
        const RunebookSetSystem PreferredRunebookSetSystem = RunebookSetSystem.SEA;
        /*  If you selected custom, then set up your custom system: */
        private RunebookSet CustomRunebookSet = new RunebookSet()
        {
            Trammel = new List<Runebook>()
            {
                // Add your Trammel runebooks and then lower and upper X and Y coordinates
                //new Runebook(0x40802837, 100, 1500, 700, 800),
            },
            
            Felucca = new List<Runebook>()
            {
                // Add your Felucca runebooks and then lower and upper X and Y coordinates
                //new Runebook(0x40802837, 100, 1500, 700, 800),
            },
            
            Malas = new List<Runebook>()
            {
                // Add your Malas runebooks and then lower and upper X and Y coordinates
                //new Runebook(0x40802837, 100, 1500, 700, 800),
            },
            
            Ilshenar = new List<Runebook>()
            {
                // Add your Ilshenar runebooks and then lower and upper X and Y coordinates
                //new Runebook(0x40802837, 100, 1500, 700, 800),
            },
            
            Tokuno = new List<Runebook>()
            {
                // Add your Tokuno runebooks and then lower and upper X and Y coordinates
                //new Runebook(0x40802837, 100, 1500, 700, 800),
            },
            
            TerMur = new List<Runebook>()
            {
                // Add your Ter Mur runebooks and then lower and upper X and Y coordinates
                //new Runebook(0x40802837, 100, 1500, 700, 800),
            },
        };
        /* ------------------------------------------------ */
    
        public enum RunebookSetSystem
        {
            SEA = 0,
            Leoncio,
            Custom,
        };
    
        public struct Runebook
        {
            public uint Serial;
            private readonly int _minX, _minY, _maxX, _maxY;

            public Runebook(uint serial, int minX, int minY, int maxX, int maxY)
            {
                Serial = serial;
                _minX = minX;
                _minY = minY;
                _maxX = maxX;
                _maxY = maxY;
            }

            public bool Contains(int x, int y)
            {
                if (x < _minX || x > _maxX) return false;

                if (x < _maxX) return true;

                return x == _maxX && y <= _maxY;
            }
        }

        private struct RunebookSet
        {
            public List<Runebook> Trammel;
            public List<Runebook> Felucca;
            public List<Runebook> Malas;
            public List<Runebook> Ilshenar;
            public List<Runebook> Tokuno;
            public List<Runebook> TerMur;
        };

        private static readonly string[] FacetNames =
            { "Felucca", "Trammel", "Ilshenar", "Malas", "Tokuno", "Ter Mur" };

        private const int GumpId = 54321542;
        private const int GumpWidth = 300;

        private const int TreasureMapItemId = 0x14EC;
        private static readonly int[] TreasureChestItemIds = {
            0xA308, 0xA304, 0xA306,
        };
        private const int LockpickItemId = 0x14FC;
        
        private const int GumpBackground = 1755;
        private const int StatusColorIdle = 0x67;
        private const int StatusColorHunting = 0x3F;

        private const int MessageColorPrompt = 0x90;
        private const int MessageColorSuccess = 0x3C;
        private const int MessageColorError = 0x21;

        private const int BookHighlightColor = 0x3C;

        private const int HuntButton = 0x9C52;
        private const int HuntButtonLabelColor = 0x3E8;

        private enum State
        {
            Idle = 0,
            Decoding,
            Hunting,
            Digging,
            Dug,
            PickingChest,
            RemovingTrap,
            Opened,
        };

        private enum Buttons
        {
            Close = 0,
            Hunt,
            Dig,
            Open,
            CleanUp,
            Loot,
            Cancel,
        };

        private struct MapProperties
        {
            public readonly string Level;
            public readonly string Facet;
            public readonly int X;
            public readonly int Y;

            public MapProperties(string level, string facet, int x, int y)
            {
                Level = level;
                Facet = facet;
                X = x;
                Y = y;
            }
        }
        
        private readonly Target _target = new Target();
        private readonly Journal _journal = new Journal();
        private int _selectedTreasureMapSerial = -1;
        private MapProperties? _selectedTreasureMapProperties;
        private Runebook? _mapRunebook;
        private Item _treasureChestItem;
        private bool _mapSetup;

        private State _state;

        private RunebookSet _runebookSet;
        
        public void Run()
        {
            _state = State.Idle;
            
            _runebookSet = GetRunebookSet();
            
            try
            {
                ClearSelectedTreasure();
                UpdateGump();

                while (true)
                {
                    var gumpData = Gumps.GetGumpData(GumpId);

                    switch (gumpData.buttonid)
                    {
                        case (int)Buttons.Close:
                        {
                            ClearSelectedTreasure();
                            Gumps.CloseGump(GumpId);
                            Player.TrackingArrow(0, 0, false);
                            CUO.FreeView(false);
                            return;
                        }
                        case (int)Buttons.Hunt:
                        {
                            Player.HeadMessage(MessageColorPrompt, "Target a treasure map to start your hunt!");
                            _selectedTreasureMapSerial = _target.PromptTarget("Target a treasure map!");

                            var targetItem = Items.FindBySerial(_selectedTreasureMapSerial);
                            if (targetItem == null || targetItem.ItemID != TreasureMapItemId)
                            {
                                Player.HeadMessage(MessageColorError, "Please, target a map!");
                                ClearSelectedTreasure();
                                UpdateGump();
                                break;
                            }

                            if (targetItem.Container != Player.Backpack.Serial)
                            {
                                Player.HeadMessage(MessageColorError, "The map needs to be on your backpack!");
                                ClearSelectedTreasure();
                                UpdateGump();
                                break;
                            }

                            var mapProps = targetItem.Properties;
                            if (mapProps.Count < 4)
                            {
                                if (Player.GetSkillValue("Cartography") >= 100)
                                {
                                    _state = State.Decoding;
                                }
                                else
                                {
                                    Player.HeadMessage(MessageColorError, "Hey! You need to decode this first!");
                                    ClearSelectedTreasure();
                                }
                                break;
                            }
                            
                            HuntDecodedMap();
                        } break;
                        
                        case (int)Buttons.Dig:
                        {
                            DigTreasure(); 
                            UpdateGump();
                        } break;
                        
                        case (int)Buttons.Open:
                        {
                            OpenChest();
                            UpdateGump();
                        } break;
                        
                        case (int)Buttons.CleanUp:
                        {
                            CleanChest();
                            UpdateGump();
                        } break;
                        
                        case (int)Buttons.Loot:
                        {
                            LootChest();
                            UpdateGump();
                        } break;
                        
                        case (int)Buttons.Cancel:
                        {
                            ClearSelectedTreasure();
                            UpdateGump();
                        } break;
                    }
                    
                    if (_state == State.Decoding)
                    {
                        HandleStateDecoding();
                    }

                    if (_state == State.Hunting)
                    {
                        HandleStateHunting();
                    }

                    if (_state == State.Digging)
                    {
                        HandleStateDigging();
                    }
                    
                    if (_state == State.PickingChest)
                    {
                        HandleStatePickingChest();
                    }
                    
                    if (_state == State.RemovingTrap)
                    {
                        HandleStateRemovingTrap();
                    }
                    
                    Misc.Pause(100);
                }
            }
            catch (Exception ex)
            {
                if (ex.GetType() != typeof(ThreadAbortException))
                {
                    Misc.SendMessage(ex.ToString());
                }
            }
        }

        private void HuntDecodedMap()
        {
            var item = Items.FindBySerial(_selectedTreasureMapSerial);
            var mapProps = item.Properties;
            
            var level = item.Name.Split(' ').Last();
            var facet = mapProps[3].ToString().Split(' ').Last();
            if (facet == "Mur") facet = "Ter Mur";
            else if (facet == "Islands") facet = "Tokuno";

            var locationMatch = Regex.Match(mapProps[4].ToString(), @"Location: \((\d+), (\d+)\)");
            var coordsX = int.Parse(locationMatch.Groups[1].Value);
            var coordsY = int.Parse(locationMatch.Groups[2].Value);
                            
            _selectedTreasureMapProperties = new MapProperties(level, facet, coordsX, coordsY);
            _state = State.Hunting;
            UpdateGump();
        }
        
        private void HandleStateDecoding()
        {
            UpdateGump();
            _journal.Clear();
            Misc.UseContextMenu(_selectedTreasureMapSerial, "Decode Map", 1000);
            Misc.Pause(2000);
            if (_journal.Search("You successfully decode a treasure map!"))
            {
                HuntDecodedMap();
            }
        }

        private void HandleStateHunting()
        {
            HighlightRunebook();
            if (FacetNames[Player.Map] == _selectedTreasureMapProperties?.Facet)
            {
                SetupMapAndTracking();
                CheckDigLocationDistance();
            }
        }
        
        private void HandleStateDigging()
        {
            _treasureChestItem = Items.FindByID(TreasureChestItemIds.ToList(), -1, -1, 4);
            if (_treasureChestItem == null || Player.Paralized) return;
            
            Player.HeadMessage(MessageColorSuccess, "Chest dug!!");
            _state = State.Dug;
            UpdateGump();
        }
        
        private void HandleStatePickingChest()
        {
            var lockpicks = Items.FindByID(LockpickItemId, -1, Player.Backpack.Serial, 1);
            if (lockpicks == null) return;
            
            _journal.Clear();
            Items.UseItem(lockpicks);
            Target.WaitForTarget(5000, true);
            Target.TargetExecute(_treasureChestItem);
            Misc.Pause(2000);

            if (_journal.Search("The lock quickly yields to your skill."))
            {
                _state = State.RemovingTrap;
                UpdateGump();
            }
        }
        
        private void HandleStateRemovingTrap()
        {
            Player.UseSkill("Remove Trap", _treasureChestItem);
            Misc.Pause(2000);
            if (!_journal.Search("You successfully disarm the trap!")) return;
            
            _state = State.Opened;
            UpdateGump();
        }

        private RunebookSet GetRunebookSet()
        {
#pragma warning disable CS0162
            switch (PreferredRunebookSetSystem)
            {
                case RunebookSetSystem.SEA:
                    return SEARunebookSet;
                case RunebookSetSystem.Leoncio:
                    return LeoncioRunebookSet;
                case RunebookSetSystem.Custom:
                    return CustomRunebookSet;
                default:
                    throw new ArgumentOutOfRangeException();
            }
#pragma warning restore CS0162
        }

        private List<Runebook> GetFacetRunebooks(string facet)
        {
            switch (facet)
            {
                case "Felucca":
                    return _runebookSet.Felucca;
                case "Trammel":
                    return _runebookSet.Trammel;
                case "Ilshenar":
                    return _runebookSet.Ilshenar;
                case "Malas":
                    return _runebookSet.Malas;
                case "Tokuno":
                    return _runebookSet.Tokuno;
                case "Ter Mur":
                    return _runebookSet.TerMur;
                default:
                    throw new ArgumentOutOfRangeException();
            }
        }
        
        private void HighlightRunebook()
        {
            if (_mapRunebook == null && _selectedTreasureMapProperties != null)
            {
                _mapRunebook = GetFacetRunebooks(_selectedTreasureMapProperties.Value.Facet).FirstOrDefault(b => b.Contains(_selectedTreasureMapProperties.Value.X, _selectedTreasureMapProperties.Value.Y));
            }

            if (_mapRunebook == null) return;

            Items.SetColor((int)_mapRunebook.Value.Serial, -1);
            Items.Message((int)_mapRunebook.Value.Serial, BookHighlightColor, "!!   BOOK HERE !!");
            Items.Message((int)_mapRunebook.Value.Serial, BookHighlightColor, "        ||       ");
            Items.Message((int)_mapRunebook.Value.Serial, BookHighlightColor, "        \\/       ");
        }

        private void SetupMapAndTracking()
        {
            if (_selectedTreasureMapProperties == null || _mapSetup) return;

            var coordsX = _selectedTreasureMapProperties.Value.X;
            var coordsY = _selectedTreasureMapProperties.Value.Y;
            
            var mapTileHeight = Statics.GetLandZ(coordsX, coordsY, Player.Map);
            var zoffset = Math.Round(mapTileHeight / 10.0f) + 1;
            var trackingX = coordsX - zoffset;
            var trackingY = coordsY - zoffset;
                
            Player.TrackingArrow((ushort)trackingX, (ushort)trackingY, true);

            _mapSetup = true;
        }

        private void CheckDigLocationDistance()
        {
            var digCoordsX = _selectedTreasureMapProperties.Value.X;
            var digCoordsY = _selectedTreasureMapProperties.Value.Y;
            
            var playerCoordsX = Player.Position.X;
            var playerCoordsY = Player.Position.Y;
            
            var tileDistance = Math.Max(Math.Abs(playerCoordsX - digCoordsX), Math.Abs(playerCoordsY - digCoordsY));
            var maxDigDistance = 1;

            var playerCartographySkill = Player.GetSkillValue("Cartography");
            if (playerCartographySkill >= 100)
            {
                maxDigDistance = 4;
            }
            else if (playerCartographySkill >= 81)
            {
                maxDigDistance = 3;
            }
            else if (playerCartographySkill >= 51)
            {
                maxDigDistance = 2;
            }

            if (tileDistance <= maxDigDistance)
            {
                Player.HeadMessage(MessageColorSuccess, "Hey, you're close enough to dig!");
            }
        }

        private void ClearSelectedTreasure()
        {
            _state = State.Idle;
            _selectedTreasureMapSerial = -1;
            _selectedTreasureMapProperties = null;
            _mapRunebook = null;
            _treasureChestItem = null;
            _mapSetup = false;
            Player.TrackingArrow(0, 0, false);
        }

        private void DigTreasure()
        {
            if (Misc.UseContextMenu(_selectedTreasureMapSerial, "Dig For Treasure", 1000))
            {
                var coordsX = _selectedTreasureMapProperties.Value.X;
                var coordsY = _selectedTreasureMapProperties.Value.Y;
                var mapTileHeight = Statics.GetLandZ(coordsX, coordsY, Player.Map);
                
                Target.WaitForTarget(1000);
                Target.TargetExecute(_selectedTreasureMapProperties.Value.X,
                    _selectedTreasureMapProperties.Value.Y, mapTileHeight);
                Target.Self();
                _state = State.Digging;
            }
        }

        private void OpenChest()
        {
            _journal.Clear();
            _state = State.PickingChest;
        }
        
        private void LootChest()
        {
            Misc.SetSharedValue("Lootmaster:DirectContainer", _treasureChestItem.Serial);
        }
        
        private void CleanChest()
        {
            Misc.UseContextMenu(_treasureChestItem.Serial, "Remove Chest", 1000);
            Misc.Pause(1000);
            ClearSelectedTreasure();
        }

        private void UpdateGump()
        {
            var gump = Gumps.CreateGump();
            gump.x = 300;
            gump.y = 300;
            Gumps.AddPage(ref gump, 0);
            
            const int leftPadding = 12;
            const int topPadding = 12;
            
            int cursorX = leftPadding;
            int cursorY = topPadding;
            
            // Header
            Gumps.AddBackground(ref gump, 0, 0, GumpWidth, 40, GumpBackground);
            Gumps.AddLabel(ref gump, cursorX, cursorY, 0x90, $"Extreme Treasure Hunting v{Version}");
            cursorY += 23;
            
            // Status
            Gumps.AddBackground(ref gump, 0, cursorY, GumpWidth, 40, GumpBackground);
            cursorY += topPadding;
            var statusText = "Status: Idle";
            var statusColor = StatusColorIdle;
            switch (_state)
            {
                case State.Idle:
                    break;
                case State.Decoding:
                {
                    statusText = $"Status: Decoding map...";
                    statusColor = StatusColorHunting;
                    break;
                }
                case State.Hunting:
                {
                    statusText = $"Status: Hunting {_selectedTreasureMapProperties?.Level} in {_selectedTreasureMapProperties?.Facet} ({_selectedTreasureMapProperties?.X},{_selectedTreasureMapProperties?.Y})";
                    statusColor = StatusColorHunting;
                    break;
                }
                case State.Digging:
                {
                    statusText = "Status: Digging..."; 
                    statusColor = StatusColorHunting;
                    break;
                }
                case State.Dug:
                {
                    statusText = "Status: Dug"; 
                    statusColor = StatusColorHunting;
                    break;
                }
                case State.PickingChest:
                    statusText = "Status: Picking chest..."; 
                    statusColor = StatusColorHunting;
                    break;
                case State.RemovingTrap:
                    statusText = "Status: Removing trap..."; 
                    statusColor = StatusColorHunting;
                    break;
                case State.Opened:
                {
                    statusText = "Status: Opened"; 
                    statusColor = StatusColorHunting;
                    break;
                }
                default:
                    throw new ArgumentOutOfRangeException();
            }
            Gumps.AddLabel(ref gump, cursorX, cursorY, statusColor, statusText);
            cursorY += 23;
            
            // Controls
            Gumps.AddBackground(ref gump, 0, cursorY, GumpWidth, 47, GumpBackground);
            cursorY += topPadding;
            switch (_state)
            {
                case State.Idle:
                    Gumps.AddButton(ref gump, cursorX, cursorY, HuntButton, HuntButton, (int)Buttons.Hunt, 1, 0);
                    Gumps.AddLabel(ref gump, cursorX + 16, cursorY + 2, HuntButtonLabelColor, "Hunt!");
                    break;
                case State.Hunting:
                    Gumps.AddButton(ref gump, cursorX, cursorY, HuntButton, HuntButton, (int)Buttons.Dig, 1, 0);
                    Gumps.AddLabel(ref gump, cursorX + 20, cursorY + 2, HuntButtonLabelColor, "Dig!");
                    break;
                case State.Dug:
                    Gumps.AddButton(ref gump, cursorX, cursorY, HuntButton, HuntButton, (int)Buttons.Open, 1, 0);
                    Gumps.AddLabel(ref gump, cursorX + 16, cursorY + 2, HuntButtonLabelColor, "Open!");
                    break;
                case State.Opened:
#pragma warning disable CS0162
                    if (LootmasterLooting)
                    {
                        Gumps.AddButton(ref gump, cursorX, cursorY, HuntButton, HuntButton, (int)Buttons.Loot, 1, 0);
                        Gumps.AddLabel(ref gump, cursorX + 12, cursorY + 2, HuntButtonLabelColor, "Loot!");
                        cursorX += 70;
                    }
#pragma warning restore CS0162
                    Gumps.AddButton(ref gump, cursorX, cursorY, HuntButton, HuntButton, (int)Buttons.CleanUp, 1, 0);
                    Gumps.AddLabel(ref gump, cursorX + 5, cursorY + 2, HuntButtonLabelColor, "Clean Up!");
                    cursorX = leftPadding;
                    break;
            }

            if (_state != State.Idle)
            {
                cursorX += 210;
                Gumps.AddButton(ref gump, cursorX, cursorY, HuntButton, HuntButton, (int)Buttons.Cancel, 1, 0);
                Gumps.AddLabel(ref gump, cursorX + 14, cursorY + 2, HuntButtonLabelColor, "Cancel");
            }
            
            Gumps.CloseGump(GumpId);
            gump.serial = (uint)Player.Serial;
            gump.gumpId = GumpId;
            Gumps.SendGump(gump, 150, 150);
        }

        private RunebookSet SEARunebookSet = new RunebookSet()
        {
            Trammel = new List<Runebook>()
            {
                new Runebook(0x40802837, 100, 1500, 700, 800),
                new Runebook(0x40802F84, 700, 1900, 1000, 800),
                new Runebook(0x408027C9, 1000, 900, 1200, 800),
                new Runebook(0x40802F60, 1200, 900, 1400, 900),
                new Runebook(0x40802FA7, 1400, 1000, 1500, 3100),
                
                new Runebook(0x40802ECE, 1500, 3200, 1700, 2400),
                new Runebook(0x40802E85, 1700, 2500, 1900, 1500),
                new Runebook(0x40802925, 1900, 2100, 2100, 1300),
                new Runebook(0x40802999, 2100, 2000, 2500, 400),
                new Runebook(0x408028B8, 2500, 500, 2800, 2000),
                
                new Runebook(0x4080277B, 2800, 2100, 3300, 700),
                new Runebook(0x4080257D, 3400, 200, 4100, 300),
                new Runebook(0x4080267F, 4100, 400, 4600, 1200),
                new Runebook(0x40802702, 4600, 1300, 4800, 3800),
            },
            
            Felucca = new List<Runebook>()
            {
                new Runebook(0x4082A561, 100, 1500, 700, 800),
                new Runebook(0x4082A601, 700, 1900, 1000, 800),
                new Runebook(0x4082A648, 1000, 900, 1200, 800),
                new Runebook(0x4082A4E8, 1200, 900, 1400, 900),
                new Runebook(0x4082A686, 1400, 1000, 1500, 3100),
            
                new Runebook(0x4082A72B, 1500, 3200, 1700, 2400),
                new Runebook(0x4082A6F6, 1700, 2500, 1900, 1500),
                new Runebook(0x40802E41, 1900, 2100, 2100, 1300),
                new Runebook(0x40802EB2, 2100, 2000, 2500, 400),
                new Runebook(0x40802E9F, 2500, 500, 2800, 2000),
            
                new Runebook(0x40802F1C, 2800, 2100, 3300, 700),
                new Runebook(0x4082A6B6, 3400, 200, 4100, 300),
                new Runebook(0x4082A59A, 4100, 400, 4600, 1200),
                new Runebook(0x4082A761, 4600, 1300, 4800, 3800),
            },
            
            Malas = new List<Runebook>()
            {
                new Runebook(0x4082E2CD, 600, 600, 1000, 400),
                new Runebook(0x4082E326, 1000, 500, 1300, 1900),
                new Runebook(0x4082E1EB, 1400, 100, 1700, 700),
            
                new Runebook(0x4082E43F, 1700, 900, 2000, 600),
                new Runebook(0x4082E3D9, 2000, 700, 2300, 1300),
                new Runebook(0x4082E399, 2300, 1400, 2500, 600),
            },
            
            Ilshenar = new List<Runebook>()
            {
                new Runebook(0x4082E2AE, 300, 500, 2000, 100),
            },
            
            Tokuno = new List<Runebook>()
            {
                new Runebook(0x4082E412, 100, 700, 1200, 1000),
            },
            
            TerMur = new List<Runebook>()
            {
                new Runebook(0x4082E230, 500, 3100, 1000, 3400),
            },
        };
        
        private RunebookSet LeoncioRunebookSet = new RunebookSet()
        {
            Trammel = new List<Runebook>()
            {
                new Runebook(0x40D6BD13, 100, 1500, 700, 1800),
                new Runebook(0x40D6BD70, 700, 1900, 900, 2500),
                new Runebook(0x40D6BC75, 1000, 300, 1100, 3500),
                new Runebook(0x40D6BCC7, 1200, 200, 1300, 3700),
                new Runebook(0x40D6BBAF, 1400, 200, 1500, 2600),
                
                new Runebook(0x40D6BC24, 1500, 2700, 1700, 1600),
                new Runebook(0x40D6B586, 3100, 100, 3600, 2600),
                new Runebook(0x40D6B4F1, 1900, 200, 2000, 3500),
                new Runebook(0x40D6BA9F, 2100, 100, 2300, 3500),
                new Runebook(0x40D6B9EC, 2400, 200, 2600, 2200),
                
                new Runebook(0x40D6B7C1, 2700, 100, 3000, 3600),
                new Runebook(0x40D6B982, 3100, 100, 3600, 2600),
                new Runebook(0x40D6B3A3, 3600, 1100, 4300, 3800),
                new Runebook(0x40D6B466, 4400, 1100, 4800, 3800),
            },
            
            Felucca = new List<Runebook>()
            {
                new Runebook(0x409393B8, 225, 750, 800, 1100),
                new Runebook(0x40939A48, 800, 1200, 1000, 1600),
                new Runebook(0x4093996E, 1000, 1700, 1200, 800),
                new Runebook(0x40939893, 1200, 900, 1300, 2500),
            
                new Runebook(0x40939718, 1300, 2570, 1500, 2200),
                new Runebook(0x40939631, 1500, 2300, 1700, 800),
                new Runebook(0x4093980B, 1700, 900, 1800, 3000),
                new Runebook(0x409398F4, 1800, 3100, 1900, 3484),
                new Runebook(0x403C967B, 2000, 100, 2160, 3630),
            
                new Runebook(0x403C9788, 2200, 300, 2500, 1100),
                new Runebook(0x403C99D2, 2500, 1200, 2800, 800),
                new Runebook(0x403C9FD7, 2800, 900, 3411, 2500),
                new Runebook(0x403C9813, 3400, 2600, 4424, 1400),
                new Runebook(0x403C9BD6, 4415, 1500, 4800, 3813),
            },
            
            Malas = new List<Runebook>()
            {
                new Runebook(0x40BB1560, 600, 600, 900, 1500),
                new Runebook(0x40BB1378, 1000, 100, 1200, 1400),
                new Runebook(0x40BB15BA, 1300, 100, 1500, 1800),
            
                new Runebook(0x40BB14F2, 1600, 100, 1800, 1800),
                new Runebook(0x40BB14A0, 1900, 100, 2100, 1800),
                new Runebook(0x40BB15E3, 2200, 100, 2400, 1500),
            },
            
            Ilshenar = new List<Runebook>()
            {
                new Runebook(0x40536A27, 300, 500, 2000, 100),
            },
            
            Tokuno = new List<Runebook>()
            {
                new Runebook(0x40536AB2, 100, 700, 1200, 1000),
            },
            
            TerMur = new List<Runebook>()
            {
                new Runebook(0x405369A9, 500, 3100, 1000, 3400),
            },
        };
    }
}