# PackieMon Monitor – SummonMonitors/Darkpassage Style
# Layout-only refactor. Button handling and functionality unchanged.

DEBUG_MODE = False  # Set to False to disable debug messages

# gump ID= 4294967295  = the max value , randomly select a high number gump so its unique
GUMP_ID = 4294967001

SHOW_HEALTH_NUMBERS = False

# =========================
# === UI CONFIG (Style) ===
# =========================
GUMP_POS_X = 700
GUMP_POS_Y = 700

ROW_HEIGHT = 18
PADDING_X  = 8
PADDING_Y  = 6
GUMP_MIN_W = 260

# Art choices similar to SummonMonitors compact style
BG_ART_ID        = 30546
ROW_DIVIDER_HUE  = 0x038    # subtle gray line
NAME_HUE_ACTIVE  = 0x0481   # bright white
NAME_HUE_DIM     = 0x0455   # dim white/gray when OOR
HP_TEXT_HUE      = 0x0481

# Segmented HP bar (safe across shards)
SEG_ART_ID       = 5210     # small 12x16 tile you used
SEG_W            = 12
SEG_H            = 16
BAR_W            = 96       # total width of segmented bar
BAR_H_PAD        = 1        # vertical pad to center the 16px tile in 18px row

# Row button on the far-right (uses serial as buttonid)
ROW_BTN_UP       = 9903
ROW_BTN_DOWN     = 9904
ROW_BTN_W        = 20

# =========================
# ======  Monitor  ========
# =========================
class Monitor:
    def __init__(self):
        self.followers = {}
        self.gump_id = GUMP_ID
        self.update_interval = 2000
        self.last_update = None
        self.gump_x = GUMP_POS_X
        self.gump_y = GUMP_POS_Y

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
        if DEBUG_MODE:
            Misc.SendMessage("[Debug] " + str(msg), self.colors['debug'])

    def clean_name(self, name):
        name = name.lower()
        if name.startswith("a "):
            name = name[2:]
        return name.strip()

    def find_followers(self):
        try:
            self.debug_message("Searching for followers...")

            followers_count = Player.Followers
            followers_max = Player.FollowersMax
            self.debug_message(f"Player followers: {followers_count}/{followers_max}")

            if followers_count == 0:
                self.debug_message("No followers detected, skipping search")
                for serial in self.followers:
                    self.followers[serial]['out_of_range'] = True
                    self.followers[serial]['out_of_range_count'] = self.followers[serial].get('out_of_range_count', 0) + 1
                    self.followers[serial]['max_hits'] = 0
                return

            filter = Mobiles.Filter()
            filter.Enabled = True
            filter.RangeMax = 30
            filter.CheckLineOfSight = False
            filter.Notorieties.Add(2)  # green/friend

            self.debug_message(f"Player position: {Player.Position.X}, {Player.Position.Y}")

            mobiles = Mobiles.ApplyFilter(filter)

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
                            self.followers[mobile.Serial]['last_hits'] = mobile.Hits
                            self.followers[mobile.Serial]['name'] = mobile.Name
                            self.followers[mobile.Serial]['max_hits'] = mobile.HitsMax
                            self.followers[mobile.Serial]['out_of_range'] = False
                            self.followers[mobile.Serial]['out_of_range_count'] = 0
                            self.debug_message(f"Updated follower: {mobile.Name} (HP: {mobile.Hits}/{mobile.HitsMax})")

            self.debug_message(f"Found {found_count} matching followers")

            for serial in list(self.followers.keys()):
                if serial not in current_serials:
                    self.followers[serial]['out_of_range'] = True
                    self.followers[serial]['out_of_range_count'] = self.followers[serial].get('out_of_range_count', 0) + 1
                    self.followers[serial]['max_hits'] = 0

            if len(self.followers) == 0:
                self.debug_message("No followers found, closing gump but will check again in 5 seconds")
                Gumps.CloseGump(self.gump_id)

        except Exception as e:
            Misc.SendMessage(f"Error in find_followers: {str(e)}", self.colors['critical'])

    def get_true_name(self, mobile):
        try:
            if mobile.PropsUpdated:
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
        return 0

    def _health_hue(self, current, maximum):
        if maximum <= 0:
            return self.colors['critical']
        pct = (current * 100) / float(maximum)
        if pct >= 75:
            return self.colors['healthy']
        elif pct >= 40:
            return self.colors['damaged']
        else:
            return self.colors['critical']

    # =========================
    # GUMP (style-only changes)
    # =========================
    def create_gump(self):
        try:
            num_rows = len(self.followers)
            if num_rows <= 0:
                Gumps.CloseGump(self.gump_id)
                return

            # Layout metrics
            header_h = 20
            body_h   = num_rows * ROW_HEIGHT
            g_w      = max(GUMP_MIN_W, PADDING_X*2 + 120 + 8 + BAR_W + 8 + ROW_BTN_W)
            g_h      = header_h + body_h + PADDING_Y

            gd = Gumps.CreateGump(movable=True)
            Gumps.AddPage(gd, 0)
            Gumps.AddBackground(gd, 0, 0, g_w, g_h, BG_ART_ID)
            Gumps.AddAlphaRegion(gd, 0, 0, g_w, g_h)

            # Header
            Gumps.AddLabel(gd, PADDING_X, 2, self.colors['title'], "Followers")
            # subtle divider
            Gumps.AddImage(gd, 0, header_h - 2, 0x0E14, ROW_DIVIDER_HUE)  # tiny 1px-ish line art; harmless if shard remaps

            # Column anchors
            name_x = PADDING_X
            bar_x  = PADDING_X + 120     # bar starts after name column
            nums_x = bar_x + BAR_W + 6   # numbers (optional)
            btn_x  = g_w - PADDING_X - ROW_BTN_W

            y = header_h

            # Use a stable order (by serial) to avoid row jitter
            for serial in sorted(self.followers.keys()):
                follower = self.followers[serial]

                # Read state
                oor = follower.get('out_of_range', False)
                cur = follower.get('last_hits', 0)
                mx  = follower.get('max_hits', 0)

                # Name + weight (uses properties when available)
                if oor:
                    name_hue = NAME_HUE_DIM
                    display_name = f"{follower['name']} (out of range)"
                else:
                    mob = Mobiles.FindBySerial(serial)
                    if mob:
                        true_name = self.get_true_name(mob)
                        w = self.get_weight(mob)
                        display_name = f"{true_name} > {int(w)}"
                    else:
                        display_name = follower['name']
                    name_hue = NAME_HUE_ACTIVE

                # HP color + segments
                hp_hue = self._health_hue(cur, mx)
                segs_total = int(BAR_W // SEG_W)
                segs_fill  = int((float(cur) / mx) * segs_total) if mx > 0 else 0

                # Row: name (left)
                # vertically center label roughly in row
                Gumps.AddLabel(gd, name_x, y - 1, name_hue, display_name[:28])

                # Row: HP bar (center) — draw empty track then filled
                bar_y = y - (SEG_H - ROW_HEIGHT)//2 + BAR_H_PAD
                for i in range(segs_total):
                    Gumps.AddImage(gd, bar_x + i * SEG_W, bar_y, SEG_ART_ID, 2999)  # neutral track
                for i in range(segs_fill):
                    Gumps.AddImage(gd, bar_x + i * SEG_W, bar_y, SEG_ART_ID, hp_hue)

                # Optional numbers just before the button
                if SHOW_HEALTH_NUMBERS:
                    hp_txt = f"{cur}/{mx}" if mx > 0 else "0/0"
                    Gumps.AddLabel(gd, nums_x, y - 1, HP_TEXT_HUE, hp_txt)

                # Row: action button (right) — uses SERIAL as buttonid (unchanged behavior)
                Gumps.AddButton(gd, btn_x, y - 1, ROW_BTN_UP, ROW_BTN_DOWN, serial, 1, 0)

                y += ROW_HEIGHT

            # Send gump
            Gumps.SendGump(self.gump_id, Player.Serial, self.gump_x, self.gump_y, gd.gumpDefinition, gd.gumpStrings)
            self.debug_message("Compact gump created and sent")
        except Exception as e:
            Misc.SendMessage(f"Error creating gump: {str(e)}", self.colors['critical'])

    # =========
    # Actions
    # =========
    def open_pack(self, serial):
        Mobiles.SingleClick(serial)
        Mobiles.WaitForStats(serial, 400)
        Mobiles.UseMobile(serial)

    def handle_button(self):
        Gumps.WaitForGump(GUMP_ID, 60000)
        Gumps.CloseGump(GUMP_ID)
        gd = Gumps.GetGumpData(GUMP_ID)
        if gd.buttonid > 0:
            self.open_pack(gd.buttonid)

    def update(self):
        try:
            self.debug_message("Running update cycle...")
            self.find_followers()
            if len(self.followers) > 0:
                self.create_gump()
            else:
                self.debug_message("No followers found, skipping gump creation")
                Gumps.CloseGump(self.gump_id)
            self.last_update = 0
        except Exception as e:
            Misc.SendMessage("Error in update: " + str(e), self.colors['critical'])

def main():
    try:
        Misc.SendMessage("Starting Follower Monitor...", 0x44)
        monitor = Monitor()
        monitor.update()
        while True:
            monitor.update()
            monitor.handle_button()
            pause_time = 5000 if len(monitor.followers) == 0 else 1000
            Misc.Pause(pause_time)
    except Exception as e:
        Misc.SendMessage("Error in main: " + str(e), 0x25)
        raise e

if __name__ == '__main__':
    main()
