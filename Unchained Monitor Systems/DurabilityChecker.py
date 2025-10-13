import re


REFRESH_DURATION = 1000  # in milliseconds
ROW_HEIGHT = 20
GUMP_ID = 0xBEEFDADE


layers = [
    "RightHand",
    "LeftHand",
    "Shoes",
    "Pants",
    "Shirt",
    "Head",
    "Gloves",
    "Ring",
    "Neck",
    "Waist",
    "InnerTorso",
    "Bracelet",
    "MiddleTorso",
    "Earrings",
    "Arms",
    "Cloak",
    "OuterTorso",
    "OuterLegs",
    "InnerLegs",
    "Talisman",
]


def proper_case(text: str) -> str:
    return " ".join(word.capitalize() for word in text.split())


def get_durability():
    """
    Obtain the durability for each of the equipped items.

    Returns
    -------
        tuple[str, int, int, str] : A list of tuples containing the layer name, current durability, max durability, and the name.
    """
    res = []
    for layer in layers:
        item = Player.GetItemOnLayer(layer)
        if item is None:
            continue
        Items.WaitForProps(item.Serial, 1000)
        for line in Items.GetPropStringList(item.Serial):
            match = re.search(r"durability (\d+) / (\d+)", line.lower())
            if match is None:
                continue
            res.append((layer, int(match.group(1)), int(match.group(2)), proper_case(item.Name or "???")))
            break
    return res


prev_durability = None
while Player.Connected:
    gump_closed = Gumps.WaitForGump(GUMP_ID, REFRESH_DURATION)
    durability = get_durability()

    if not gump_closed and durability == prev_durability:
        continue

    prev_durability = durability
    durability = sorted(durability, key=lambda x: x[1] / x[2])
    num_entries = len(durability)

    Gumps.CloseGump(GUMP_ID)
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)

    Gumps.AddBackground(gd, 0, 0, 230, 10 + ROW_HEIGHT * num_entries, 30546)
    Gumps.AddAlphaRegion(gd, 0, 0, 230, 10 + ROW_HEIGHT * num_entries)

    for i, entry in enumerate(durability):
        layer, dur, max_dur, item_name = entry
        # Compute various quantities for visualization
        dur_frac = dur / max_dur
        dur_percent = 100 * dur_frac
        level = int(5 * dur_frac)
        cur_y = 5 + ROW_HEIGHT * i
        cur_hue = 0x21 + 5 * level
        tooltip_msg = f"<BASEFONT COLOR=\"#FFFF00\">{item_name}</BASEFONT><BR />{dur} / {max_dur} ({dur_percent:.1f}%)"
        # Display the durability status
        Gumps.AddLabel(gd, 10, cur_y, 0x47E, layer)
        Gumps.AddTooltip(gd, tooltip_msg)
        Gumps.AddImageTiled(gd, 130, cur_y + 2, 90, ROW_HEIGHT - 4, 40004)
        Gumps.AddTooltip(gd, tooltip_msg)
        Gumps.AddImageTiled(gd, 130, cur_y + 2, int(90 * dur_frac), ROW_HEIGHT - 4, 9354)
        Gumps.AddLabel(gd, 90, cur_y, cur_hue, f"{dur_percent:.0f}%")

    Gumps.SendGump(GUMP_ID, Player.Serial, 25, 25, gd.gumpDefinition, gd.gumpStrings)
