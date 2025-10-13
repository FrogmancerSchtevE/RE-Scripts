DEBUG_MODE = False  # Set to False to disable debug messages

# gump ID= 4294967295  = the max value , randomly select a high number gump so its unique
GUMP_ID = 4294967001

SHOW_HEALTH_NUMBERS = False

class Monitor:
    def __init__(self):
        self.followers = {}
        self.gump_id = GUMP_ID
        self.update_interval = 2000
        self.last_update = None
        self.gump_x = 700
        self.gump_y = 700
        
        self.out_of_range_timeout = 3
        
        self.colors = {
            'title': 0x0035,      # Bright gold
            'healthy': 0x0044,    # Green
            'damaged': 0x0021,    # Orange
            'critical': 0x0025,   # Red
            'background': 0x053,  # Dark gray
            'debug': 0x03B2,      # Light blue
            'text': 0x0481        # Bright white
        }
        
        if DEBUG_MODE:
            Misc.SendMessage("Monitor initialized", self.colors['debug'])

    def debug_message(self, msg):
        """Send a debug message to the game client"""
        if DEBUG_MODE:
            Misc.SendMessage("[Debug] " + str(msg), self.colors['debug'])
   
    def clean_name(self, name):
        """Remove status effects and normalize name for comparison"""
        name = name.lower()
        # Remove "a " prefix if present
        if name.startswith("a "):
            name = name[2:]
            
        return name.strip()

    def find_followers(self):
        try:
            self.debug_message("Searching for followers...")
            
            # Check if player has any followers
            followers_count = Player.Followers
            followers_max = Player.FollowersMax
            self.debug_message(f"Player followers: {followers_count}/{followers_max}")
            
            if followers_count == 0:
                self.debug_message("No followers detected, skipping search")
                # Mark all tracked followers as out of range
                for serial in self.followers:
                    self.followers[serial]['out_of_range'] = True
                    self.followers[serial]['out_of_range_count'] = self.followers[serial].get('out_of_range_count', 0) + 1
                    self.followers[serial]['max_hits'] = 0
                return
                
            filter = Mobiles.Filter()
            filter.Enabled = True
            filter.RangeMax = 30  
            filter.CheckLineOfSight = False
            
            # Set notoriety to find friendly (2) creatures
            filter.Notorieties.Add(2)  # 2 = green/friend
            
            # Debug current player position
            self.debug_message(f"Player position: {Player.Position.X}, {Player.Position.Y}")
            
            # Look for creatures with specific names
            mobiles = Mobiles.ApplyFilter(filter)
            
            # Update followers dictionary
            current_serials = []
            found_count = 0
            
            if mobiles:
                for mobile in mobiles:
                    if mobile and mobile.Name:
                        found_count += 1
                        current_serials.append(mobile.Serial)
                        if mobile.Serial not in self.followers:
                                self.debug_message(f"New follower found: {mobile.Name} (HP: {mobile.Hits}/{mobile.HitsMax})")
                                self.followers[mobile.Serial] = {
                                    'name': mobile.Name,
                                    'max_hits': mobile.HitsMax,
                                    'last_hits': mobile.Hits,
                                    'out_of_range': False,
                                    'out_of_range_count': 0
                                }
                        else:
                            # Update last hits and name (in case status changed)
                            self.followers[mobile.Serial]['last_hits'] = mobile.Hits
                            self.followers[mobile.Serial]['name'] = mobile.Name
                            self.followers[mobile.Serial]['max_hits'] = mobile.HitsMax
                            self.followers[mobile.Serial]['out_of_range'] = False
                            self.followers[mobile.Serial]['out_of_range_count'] = 0
                            self.debug_message(f"Updated follower: {mobile.Name} (HP: {mobile.Hits}/{mobile.HitsMax})")
            
            self.debug_message(f"Found {found_count} matching followers")
            
            # Mark followers that are out of range
            for serial in self.followers:
                if serial not in current_serials:
                    self.followers[serial]['out_of_range'] = True
                    self.followers[serial]['out_of_range_count'] = self.followers[serial].get('out_of_range_count', 0) + 1
                    self.followers[serial]['max_hits'] = 0
            
            # Close gump if we have no followers
            if len(self.followers) == 0:
                self.debug_message("No followers found, closing gump but will check again in 5 seconds")
                Gumps.CloseGump(self.gump_id)
            
        except Exception as e:
            Misc.SendMessage(f"Error in find_followers: {str(e)}", self.colors['critical'])
        
    def get_true_name(self, mobile):
        """Extract the true name from mobile properties"""
        try:
            if mobile.PropsUpdated:
                # First property is usually the true name
                for prop in mobile.Properties:
                    prop_text = str(prop).strip()
                    if prop_text.startswith('a ') or prop_text.startswith('an '):
                        return prop_text
            return mobile.Name
        except Exception as e:
            self.debug_message(f"Error getting true name: {str(e)}")
            return mobile.name
            
    def get_weight(self, mobile):
        if mobile:
            return Mobiles.GetPropValue(mobile, "Weight")
        else:
            return 0
        
    def get_health_color(self, current, maximum):
        """Get color based on health percentage"""
        try:
            if maximum <= 0:
                return self.colors['critical']
            
            percentage = (current * 100) / maximum
            if percentage > 75:
                return self.colors['healthy']
            elif percentage > 25:
                return self.colors['damaged']
            else:
                return self.colors['critical']
        except:
            return self.colors['critical']
        
    def create_gump(self):
        """Create a compact health bar gump with unified background and bars (single gump, like ARPG UI)"""
        try:
            width = 212
            ARPG_SEGMENT_HEIGHT = 16
            height = max(25, len(self.followers) * ARPG_SEGMENT_HEIGHT + 6)  # 2px top/bottom pad + 2px gap
            gd = Gumps.CreateGump(movable=True)
            Gumps.AddPage(gd, 0)
            Gumps.AddBackground(gd, 0, 0, width, height, 30546)
            Gumps.AddAlphaRegion(gd, 0, 0, width, height)
            ARPG_BAR_ART = 5210  # 12x16 pixel bar segment
            ARPG_SEGMENT_WIDTH = 12
            ARPG_SEGMENT_HEIGHT = 16
            ARPG_BAR_WIDTH = 72
            y_offset = 2
            for serial, follower in self.followers.items():
                # If out of range, display as 25/0 or 0/0
                if follower.get('out_of_range', False):
                    current_hits = follower['last_hits']
                    max_hits = 0
                    color = 38  # Bright red for out of range
                    true_name = follower['name'] + " (out of range)"
                else:
                    mobile = Mobiles.FindBySerial(serial)
                    if mobile:
                        true_name = self.get_true_name(mobile) + " > " + str(self.get_weight(mobile))
                    else:
                        true_name = follower['name']
                    current_hits = follower['last_hits']
                    max_hits = follower['max_hits']
                    # Color logic as before
                    health_percent = (current_hits / max_hits) if max_hits > 0 else 0
                    if health_percent >= 0.7:
                        color = 168  # Bright green
                    elif health_percent >= 0.4:
                        color = 53   # Yellow
                    elif health_percent >= 0.2:
                        color = 33   # Red
                    else:
                        color = 38   # Bright red
                num_segments = ARPG_BAR_WIDTH // ARPG_SEGMENT_WIDTH
                filled_segments = int((current_hits / max_hits) * num_segments) if max_hits > 0 else 0
                bar_x = 135
                bar_y = y_offset + 2
                for i in range(num_segments):
                    Gumps.AddImage(gd, bar_x + i * ARPG_SEGMENT_WIDTH, bar_y, ARPG_BAR_ART, 2999)
                for i in range(filled_segments):
                    Gumps.AddImage(gd, bar_x + i * ARPG_SEGMENT_WIDTH, bar_y, ARPG_BAR_ART, color)
                Gumps.AddLabel(gd, 20, y_offset + 2, color, true_name)
                Gumps.AddButton(gd,0, y_offset + 2, 9903, 9904, serial, 1, 0)
                if SHOW_HEALTH_NUMBERS:
                    health_text = f"{current_hits}/{max_hits}"
                    Gumps.AddLabel(gd, bar_x + ARPG_BAR_WIDTH + 8, bar_y, color, health_text)
                y_offset += ARPG_SEGMENT_HEIGHT
            Gumps.SendGump(self.gump_id, Player.Serial, self.gump_x, self.gump_y, gd.gumpDefinition, gd.gumpStrings)
            self.debug_message("Unified gump created and sent")
        except Exception as e:
            Misc.SendMessage(f"Error creating gump: {str(e)}", self.colors['critical'])

    def open_pack(self, serial):
        Mobiles.SingleClick(serial);
        Mobiles.WaitForStats(serial, 400)
        Mobiles.UseMobile(serial)
        
    def handle_button(self):
        Gumps.WaitForGump(GUMP_ID, 60000)
        Gumps.CloseGump(GUMP_ID)
        gd = Gumps.GetGumpData(GUMP_ID)
        if gd.buttonid > 0:
            self.open_pack(gd.buttonid)
            
    def update(self):
        """Update the follower monitor"""
        try:
            # removed datetime update check
            self.debug_message("Running update cycle...")
            self.find_followers()
            if len(self.followers) > 0:
                self.create_gump()
            else:
                self.debug_message("No followers found, skipping gump creation")
                Gumps.CloseGump(self.gump_id)  # Close gump if no followers
            self.last_update = 0  # Set to dummy value, not used

        except Exception as e:
            Misc.SendMessage("Error in update: " + str(e), self.colors['critical'])
            
def main():
    try:
        Misc.SendMessage("Starting Follower Monitor...", 0x44)
        monitor = Monitor()
        # Force immediate first update to show existing followers
        monitor.update()
        while True:
            monitor.update()
            monitor.handle_button()
            # If no followers, wait 5 seconds; otherwise, 1 second
            pause_time = 5000 if len(monitor.followers) == 0 else 1000
            Misc.Pause(pause_time)
            
    except Exception as e:
        Misc.SendMessage("Error in main: " + str(e), 0x25)
        raise e

if __name__ == '__main__':
    main()            