# Frog Development Tools

This folder is the shared home for Razor Enhanced inspection and reverse-engineering helpers.

## Tools

### FrogItemInspector.py

Targets an item and records the public item wrapper, reflected internal state, OPL data, container data, TileData, world-tile context, and annotated field meanings.

Use **SAVE TO FILE** to write a capture bundle under:

`Scripts/FrogDevelopmentTools/data/items`

### FrogGumpInspector.py

Captures an open gump by explicit decimal/hex ID, the most recently observed open gump, or the next gump opened after arming the inspector. It preserves Razor's raw sources separately, parses the layout into controls, maps buttons and inputs, annotates command meanings, and reflects the complete exposed `GumpData` object.

Use **SAVE BUNDLE** to write:

- an annotated text report;
- unabridged raw JSON;
- the untouched raw layout string; and
- an XLSX workbook with Overview, Controls, Buttons, Inputs, Switches, Strings, Response, API Probes, and Raw Layout sheets.

Files are saved under:

`Scripts/FrogDevelopmentTools/data/gumps`

## Gump capture workflow

1. Run `FrogGumpInspector.py` in Razor Enhanced.
2. For a known open gump, enter its ID as decimal or `0xHEX`, then select **CAPTURE ID**.
3. If the ID is unknown, select **CAPTURE NEXT** and trigger the desired gump within 30 seconds.
4. Review the Summary, Controls, Buttons, Inputs, Text, and Raw/API tabs.
5. Select **SAVE BUNDLE** when the capture is the one you want to keep.

The inspector never sends a response to the target gump. It only reads Razor Enhanced's cached data.
