# Frog Crafting Core

Frog Crafting Core (FCC) is a data-driven crafting suite for Ultima Online Unchained and Razor Enhanced. It presents a familiar crafting-gump-style interface, then adds resource restocking, tool management, output storage, training, BOD filling, and quest automation behind it.

This README describes the current `1.0` build in `In Development`. Run only `FrogCraftingCore.py`; the core discovers the craft modules, training profiles, and optional plugins itself.

## What the suite currently supports

FCC loads eight craft skills from `Modules/*.json`:

- Alchemy
- Blacksmithy
- Carpentry
- Cooking
- Fletching / Bowcraft
- Inscription
- Tailoring
- Tinkering

Those modules currently contain 639 enabled recipes. The interface and automation are generated from the loaded data, so adding or correcting a recipe normally does not require editing the core.

The current plugin set adds:

- **BOD Filler** for one loose deed or a filtered queue of loose deeds.
- **BOD Book Filler** for scanning and completing orders stored in a BOD Book.
- **Quest Crafter** for supported Global and Weekly crafting quests.

## Quick-start walkthrough

For a safe first test:

1. Run `FrogCraftingCore.py` in Razor Enhanced.
2. Configure storage on **Home / Setup**.
3. If you use either shelf, set its withdrawal values to `100` in game and lock/save them.
4. Select one crafting skill from **Crafting Skills**.
5. Choose a category, recipe, material, and amount.
6. Leave **Craft Focus** on **None** for an ordinary test craft.
7. Press **Start** and watch the **Step** and **Status** lines.
8. Confirm that one item is crafted, verified, and stored where expected before starting a large job.

The rest of this guide explains each part in detail.

## 1. Configure Home / Setup

The Home page is both the skill launcher and the persistent setup screen. FCC saves these choices per character.

### Choose a resource source

The **Source** button cycles between:

- **Resource Chest** — ingredients come only from the configured chest.
- **Shelf + Chest** — FCC tries the appropriate shelf first and uses the chest as fallback.

In **Shelf + Chest** mode, the lookup order is:

1. Reagent/Gem Shelf for ingredients mapped to that shelf.
2. Resource Shelf for ingredients mapped there.
3. Resource Chest as the fallback.

FCC confirms delivery before moving to the next source. If the same resource exists on both shelves, a successful first withdrawal prevents a duplicate pull.

Use the following setup buttons:

- **Set Chest** — the ordinary resource chest and final fallback.
- **Set Shelf** — the Unchained Resource Shelf, item `0x71FC`.
- **Set Reagent Shelf** — the reagent/gem storage shelf. FCC validates it by opening gump `0xA8ED56C7`.
- **Set Output** — where ordinary crafted items and `save` training outputs should go. If unset, output remains in the crafting workspace.
- **Set Tool Book** — the Crafting Tool Storage book used by the ToolBookRecharger workflow.
- **Set Trash** — the safe destination for verified training or BOD rejects that cannot be recycled.

Both shelf types must already be configured in game to withdraw `100` units. FCC deliberately does not edit or relock their text entries.

### Set up a Craft Bag

Craft Bag mode is strongly recommended for automated training and BOD work.

1. Place an empty sub-container directly inside the main backpack.
2. Press **Set Craft Bag** and target it.
3. Confirm **Craft Bag: ON**.

When enabled, FCC stages tools and resources into that bag, watches it for new output, and limits automated smelt, salvage, recycle, and trash actions to verified items in that workspace. This keeps unrelated equipment in the main backpack out of disposal operations.

The **Craft Bag: ON/OFF** button can disable or re-enable the saved bag without clearing its serial.

### Configure Artificer Glasses

Open **Crafting Glasses**, press the desired skill, and target that skill's Artificer Glasses.

FCC accepts item `0x2FB8` or an item named Artificer Glasses. The tooltip does not have to expose the skill bonus. Before a normal or plugin-driven craft, FCC equips the saved pair by using it and verifies either:

- the exact serial on the Earrings layer; or
- an increase in the corresponding skill value.

Bonuses may vary; FCC does not assume every pair grants `+10`. Training mode removes Artificer Glasses and uses the unmodified skill so the bonus does not reduce gain chance.

### Map server templates

Open **Craft Templates** and assign each craft skill to its server template number, from 1 through 20.

- Leave a skill **Unassigned** if it should never trigger a swap.
- Skills assigned to the same template reuse the active template without swapping again.
- FCC starts each session with the active template **Unknown**, because the server does not expose a reliable query. The first mapped craft synchronizes once.
- If you change templates outside FCC, press **Forget Active** before the next automated craft.

For a mapped skill, FCC sends `[template N`, waits for confirmation gump `0x11775C2E`, and presses button `1` before checking skill or spending resources.

### Choose a crafting focus

The persisted **Craft Focus** selector offers:

- **As-is** — leave the server's current focus unchanged.
- **None** — ordinary output is not consumed by a focus system.
- **BOD Book**
- **Weekly**
- **Global**
- **Guild**

FCC verifies the requested focus through the live crafting gump before crafting. The plugins choose their required focus automatically.

Guild focus may be selected for manual use, but unattended FCC crafting intentionally pauses before spending resources because the shard's exact consumed-craft success message is not yet mapped.

## 2. Run an ordinary crafting job

Select a skill on Home to open its workbench.

### Pick the craft

1. Choose a category in the left pane.
2. Choose a recipe in the right pane.
3. Review the displayed minimum skill and ingredient cost.
4. If the recipe supports material choices, cycle the material group and selected material.
5. Set the amount with `-100`, `-10`, `-1`, `+1`, `+10`, and `+100`. The valid range is 1 to 9,999.
6. Confirm the crafting focus.
7. Press **Start**.

The **Automation** line reports whether the selected recipe has enough information to run. A missing ingredient mapping, unsupported action, invalid material choice, or unavailable skill is reported before the job begins.

### What FCC does after Start

For each job, FCC:

1. Selects the mapped server template when needed.
2. Equips the configured Artificer Glasses when appropriate.
3. Verifies the player's effective skill.
4. Finds the required tool in the crafting workspace, resource chest, or Tool Storage book.
5. Attempts to craft a replacement tool through Tinkering when the module provides a verified replacement recipe.
6. Loads ingredients for up to 25 crafts at a time, or only the remaining amount when fewer than 25 crafts remain.
7. Opens the real server crafting gump and sends the module's material, category, and recipe buttons.
8. Verifies the result from the exact inventory transaction or the expected consumed-craft journal message.
9. Stores or contributes the output.
10. Returns leftover session ingredients to the configured storage after the job or plugin workflow finishes.

If a recipe needs a crafted component, such as Axle with Gears, FCC first looks for that component in the workspace and storage. If none exists, it crafts and verifies one component with focus **None**, restores the parent focus, and resumes the requested recipe.

### Make Last acceleration

FCC does not trust **Make Last** immediately. It first requires two strongly verified crafts with the same plugin owner, module, recipe, material, focus, and workspace. After that, it uses the server's **Make Last** button as soon as the refreshed crafting gump is available.

Changing the recipe, material, focus, workspace, plugin, or template-sensitive context disarms the shortcut. A failed or ambiguous result also disarms it, so FCC rebuilds confidence through the complete button path instead of blindly repeating the wrong item.

### Pause, cancel, and status

- **Pause** keeps the selected recipe and completed count.
- **Cancel Job** stops the job and reports the partial result.
- **Home / Setup** returns to the landing page. Opening Home alone does not pause an active job.
- Selecting a different module while work is active stops the current job safely.
- The bottom **Step** line names the current phase.
- The bottom **Status** line explains what FCC is doing or why it stopped.

Pause, Cancel, training Pause, plugin Stop, and Close are priority controls. FCC checks them between server actions and cancels pending targeting when possible. A craft already sent to the shard is allowed to finish verification so it is not lost or repeated.

## 3. Resource, tool, and output behavior

### Resource chunks

FCC restocks for 25 crafts at a time rather than withdrawing before every item. If only 11 crafts remain, it loads for 11. A new restock occurs only when the current workspace cannot support the next craft.

### Tools

The search order is:

1. Active crafting workspace.
2. Resource chest.
3. Configured Tool Storage book.
4. Verified Tinkering replacement-tool recipe, when available and usable.

In Craft Bag mode, acquired or newly crafted tools are moved into the bag and used there.

### Output verification

FCC prefers exact item IDs and hues, but it can use exact item-name aliases while the remaining IDs are collected. A normal craft succeeds only after FCC sees a positive transaction matching the expected output.

Items consumed before entering the backpack are verified from fresh journal messages. Current examples include:

- `Global Quest Progress: ... contributed ...`
- `Weekly Quest: Crafted ...`
- `BOD Progress: current/required`
- `BOD complete! You earned ... artificer points!`

Only messages created after the current craft began are considered. This prevents an old success line from being reused.

### Cleanup

FCC records which ingredients were resolved during the session. At completion:

- Chest mode returns matching leftovers to the resource chest.
- Shelf mode tries the Resource Shelf fill-from-backpack action and the Reagent/Gem Shelf refill action.
- Any shelf remainder falls back to the resource chest.

A failed cleanup produces a warning but does not trap an otherwise completed job in a loop.

## 4. Training mode

A **Train** button appears beside every skill with a loaded `Training/*.json` profile.

1. Configure the resource source, Craft Bag, output chest, and trash target on Home.
2. Press **Train** beside the desired skill.
3. Review the current skill, cap, training range, selected recipe, and output policy.
4. Press **Start Training**.

FCC reads the real skill, chooses the current stage and first usable recipe alternative, and uses the normal tool, resource, crafting, and verification engine. It continues until the profile goal or the player's current skill cap.

Each stage declares one output policy:

- `smelt`
- `salvage`
- `recycle`
- `trash`
- `save`
- `none`

A verified output is processed before another item is crafted. Disposal failures retry the same pending item; repeated safety-critical failures pause with the item left in the crafting workspace.

With Craft Bag mode enabled, only the exact verified output in that bag is eligible for automated disposal. Recovered resources are staged back into the bag for reuse. If moving recovered material repeatedly fails, FCC falls back to the resource chest or leaves it in the main backpack for cleanup and continues rather than smelting the same output twice.

Cooking currently provides an informational training guide rather than an automated training cycle.

## 5. Manual workbench actions

The workbench exposes **Smelt**, **Salvage**, **Repair**, **Mark**, and **Recycle** where supported by the active module.

In Craft Bag mode:

- Smelt, Salvage, Repair, and Mark require one verified item directly inside the Craft Bag.
- Recycle accepts either one verified item or the Craft Bag itself.
- Targeting the Craft Bag invokes the server's bag-wide recycle action.

## 6. Fill loose BODs

Open **BOD Filler** from **Crafting Plugins**.

### Single mode

1. Press **Target BOD** and select one deed.
2. Review the parsed skill, recipe, material, progress, exceptional requirement, and points.
3. Press **Start Fill**.

The BOD's server gump is the authoritative validation. FCC does not rely on unreliable cached container metadata.

### Bulk mode

1. Press **Set Chest 1** and optionally **Set Chest 2**.
2. Open **Bulk Filters** and choose which orders are allowed.
3. Press **Scan Orders**.
4. Review the eligible/skipped totals and first queued order.
5. Press **Start Bulk**.

The scanner opens each deed where it currently sits. It temporarily moves a deed to the root backpack only when the live open attempt fails, then returns it to its exact source container.

Shared filters include:

- Exceptional orders.
- Individual craft skills.
- Discovered material choices.
- Recipes requiring Bone, default **NO**.
- Recipes requiring Gems, default **NO**.

Changing a filter invalidates the old queue; scan again before starting.

For non-stackable output, FCC lets the deed consume acceptable items from the Craft Bag, then uses the matching crafting tool's bag-wide recycle action on verified rejects. After repeated recycle attempts, surviving rejects move to the configured trash. If trash is not valid, the rejects remain in the Craft Bag and the run pauses. FCC never drops them on the ground.

Exceptional deeds may reject normal-quality output. FCC keeps crafting within its configured safety limits until the requested exceptional items are accepted.

Multistep Cooking BODs are not ready for unattended use. Leave Cooking disabled in Bulk Filters until ingredient preparation and baking stages are implemented.

## 7. Fill a BOD Book

The **BOD Book Filler** works with BOD Book item `0x2259`.

1. Put the BOD Book directly in the main backpack.
2. Keep the configured Craft Bag directly in the main backpack.
3. Open **BOD Book** from **Crafting Plugins**.
4. Press **Target Book**.
5. Review **Filters**. These are shared with the loose BOD Filler.
6. Press **Scan Book**.
7. Review the live, scrollable craft order and skipped count.
8. Press **Start Fill**.

The plugin scans All Skills, builds a filtered queue, and removes completed rows from the displayed order in real time. The **Current** line uses fresh `BOD Progress` messages when available.

During each craft pass, FCC temporarily:

- uses the root backpack as the crafting workspace;
- verifies **BOD Book** focus;
- lets the book consume matching output;
- stages rejected matching output into the Craft Bag;
- recycles or safely trashes those rejects;
- cleans up root-backpack ingredients; and
- restores the player's saved Craft Bag setting.

A fresh `BOD complete!` message ends the provisional batch immediately. If that line is missed, the plugin performs one safety rescan and treats a disappeared active row as completion.

## 8. Automate Global and Weekly quests

Open **Quest Crafter** from **Crafting Plugins**. Its upper panel is Global Quest automation; its lower panel is Weekly Quest automation.

### Review without starting

- **Refresh GQ** reads the current Global Quest.
- **Refresh WQ** opens or refreshes the Compendium Weekly page.
- **Refresh All** reads both.
- **Journal** prints the full parser and mapping diagnostics.

The panel shows the parsed quest, progress, selected FCC module/recipe/material, next batch, and any block reason.

### Start a watcher

- **Watch Global** watches only the Global Quest.
- **Do Weeklies** works only the selected Weekly crafting tasks.
- **Both** watches both and gives an eligible Global craft priority at a batch boundary.

The watcher remains idle when nothing supported is available. An unsupported, disabled, unresolved, or under-resourced task is held without killing the watcher, allowing later eligible work to start automatically.

### Global behavior

Global polling opens gump `0x4EC6CF84` with `[gq` and falls back to `[globalquest`. Known non-crafting quests can be ignored. **Lumber Crisis**, which asks for 5,000 gathered logs, is deliberately skipped.

Current default craft plans include:

- Metal weapons → Blacksmithy Katana.
- Metal armor → Blacksmithy Ringmail Gloves.
- Magic/any spell scrolls → Inscription Energy Bolt.
- Bows → Fletching Bow.
- Wooden weapons → Carpentry Quarter Staff.
- Named potions → configured Alchemy aliases, with potion Globals disabled by default.

Known point yields are used directly. An enabled recipe with an unknown yield performs one calibration craft, reads **Your Contribution**, saves the learned value, and then calculates the remaining crafts with ceiling division.

The shard currently reports **Armory Crafting - Gold Armor** while counting Agapite armor. `OVERRIDE_GOLD_ARMOR_TO_AGAPITE = True` in `Plugins/30_quest_crafter.py` preserves the reported Gold text but crafts Agapite. Set it to `False` if the shard bug is fixed.

### Weekly behavior

Weeklies are read from the Compendium page, not `[job`, because the Compendium preserves left/right item variants. FCC prefers the captured paperdoll action and uses `[compendium` only as a throttled fallback. Quest commands share a four-second cooldown.

The player selected the Weekly jobs, so the plugin assumes the selected character template can perform them. It bypasses only the early skill-planning rejection; template switching, the real pre-craft skill check, tools, resources, focus, output verification, and all other safeguards remain active.

Weekly tasks run in batches of at most 25. After each batch, FCC refreshes the Compendium page and verifies progress before continuing.

The resolver:

- checks exact aliases first;
- then compares the name with enabled FCC recipe and output names;
- preserves left/right variants;
- interprets `Regular` as Cloth only for cloth-only recipes;
- interprets `Regular` as Plain Boards for wood-choice recipes;
- interprets `Regular` as ordinary Leather for leather-choice recipes; and
- leaves unrelated `Regular` materials unresolved instead of guessing.

Every unresolved row is retained for diagnostics and written to the journal once. It consumes no resources.

## 9. Saved settings and Reload

FCC stores per-character settings in:

```text
Settings/character_0xXXXXXXXX.json
```

Saved values include:

- all chest, shelf, Tool Storage, trash, and Craft Bag targets;
- source mode and Craft Bag state;
- craft amount and selected module;
- Craft Focus;
- Artificer Glasses assignments;
- craft-template assignments;
- BOD source containers, mode, and shared filters;
- Quest Crafter allow filters; and
- calibrated Global contribution values.

The player serial is the preferred identity. If it is unavailable, FCC uses the backpack serial and records that fallback as `identity_source`.

Settings are written through a temporary file, and the previous valid copy remains as `.bak`. If the JSON is malformed, FCC reports it and leaves the file untouched rather than silently replacing it. The first successful save prints the exact path and identity source in the journal.

Use **Reload** after editing module, training, shelf, ingredient, or plugin data. Reload safely stops active automation, discovers the files again, and redraws the current page.

## 10. When FCC pauses

FCC retries transient failures instead of stopping on the first missed gump, move, tool pull, target cursor, or button sequence. Repeated safety-critical failures pause before more resources are consumed.

If a job pauses:

1. Read the bottom **Step** and **Status** lines.
2. Check the Razor Enhanced journal for the more detailed reason.
3. Confirm the required chest, shelf, bag, book, tool, and trash target still exist and are accessible.
4. Confirm shelf withdrawal values remain locked at `100`.
5. Confirm the expected template and Artificer Glasses are available.
6. Check weight, container space, and available materials.
7. Resume or restart only after correcting the reported condition.

Common intentional stops include:

- repeated crafting-gump failures;
- missing or unverifiable resources or tools;
- output that cannot be matched safely;
- invalid or ambiguous BOD/quest mappings;
- an unsafe reject with no valid trash destination;
- template or glasses verification failure; and
- unsupported Guild consumed-craft verification.

## Current limitations

- The suite remains in `In Development` and still requires live shard testing after data changes.
- `Data/ingredient_ids.json` contains 216 ingredients: 137 have IDs and 79 remain unknown or ambiguous. Exact name matching is the fallback, but custom shard names can still require aliases.
- Tinkering's captured gump map is highly numeric and deserves extra smoke testing after recipe edits.
- Multistep Cooking BOD automation is intentionally deferred.
- Cooking training is informational only.
- Guild-focus consumed output is not automated until its exact success message is known.
- The future Master Shelf craft-from-storage bridge is not implemented.
- Server latency can delay a control until the current server action returns, but FCC checks priority controls between actions and avoids sending the next action afterward.

## Project layout

```text
FrogCraftingCore/
├── FrogCraftingCore.py
├── Modules/
├── Training/
├── Plugins/
├── Data/
├── Settings/
├── MODULE_SCHEMA.md
├── PLUGIN_CONTRACT.md
└── README.md
```

Important files:

- `Modules/*.json` — categories, recipes, server button actions, skills, ingredients, outputs, and material choices.
- `Training/*.json` — training ranges, recipe alternatives, material selections, and disposal policies.
- `Plugins/*.py` — optional workflows loaded through `create_plugin(host)`.
- `Data/ingredient_ids.json` — editable item ID and hue overlay.
- `Data/resource_shelf.json` — Resource Shelf pages, buttons, aliases, and navigation.
- `Data/reagent_gem_shelf.json` — Reagent/Gem Shelf categories, pages, buttons, and string IDs.
- `Data/bod_filler.json` — BOD identifiers, parsing layout, filters, safety limits, and recipe overrides.
- `Data/bod_book_filler.json` — BOD Book navigation and editable name-to-recipe aliases.
- `Data/quest_crafter.json` — Global/Weekly polling, filters, aliases, and quest-to-recipe mappings.
- `MODULE_SCHEMA.md` — module contract and recipe-data checklist.
- `PLUGIN_CONTRACT.md` — host API and plugin lifecycle.

Normal module JSON uses decimal integers. `ingredient_ids.json` also accepts quoted hexadecimal strings such as `"0x1BF2"`. Unknown values must be JSON `null`, not the string `"null"`.

## Maintainer smoke test

Static checks cannot prove live shard behavior. Before a player-facing deployment, test at least:

1. One recipe and each changed material path in every edited module.
2. Chest, Resource Shelf, Reagent/Gem Shelf, Tool Storage, Craft Bag, output, and cleanup paths.
3. Two full verified crafts followed by Make Last acceleration and one forced invalidation.
4. Pause and Cancel during restocking, gump navigation, result verification, and disposal.
5. One training stage for every disposal action currently referenced by data.
6. Single and Bulk BOD runs, including exceptional rejects, Bone/Gem filters, recycle fallback, and missing-trash safety.
7. One BOD Book queue with accepted output, rejected output, journal progress, completion, cleanup, and Craft Bag restoration.
8. Quest Crafter refresh and execution for each newly captured Global title or Weekly row.
9. Settings persistence across a full script restart and between two characters.
10. Template switching, same-template reuse, **Forget Active**, randomized glasses bonuses, already-equipped glasses, and glasses removal during training.

Do not move this suite out of `In Development` until its current behavior has been confirmed in game.
