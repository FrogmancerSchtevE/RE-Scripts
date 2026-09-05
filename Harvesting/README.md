# Harvesting

This folder contains **Razor Enhanced harvesting scripts and resource-gathering tools** for Ultima Online.

These tools are designed to simplify repetitive gathering tasks, provide useful information while harvesting, and reduce some of the tedious inventory and resource management involved in gathering materials.

## What You'll Find Here

Harvesting scripts may include functionality such as:

* Mining
* Lumberjacking
* Cotton gathering
* Resource collection
* Resource processing
* Weight and inventory management
* Container and storage management
* Nearby resource detection
* Harvesting monitors and status displays
* Assisted gathering tools
* Multi-function harvesting suites

Some scripts may simply assist with gathering nearby resources, while larger suites may combine harvesting, processing, storage, and other related functions into a single tool.

## General Design

Where practical, harvesting tools follow a common structure:

**Configuration -> Helpers -> Harvesting Logic -> GUI -> Main**

Frequently changed settings such as resource IDs, scan ranges, storage containers, delays, and other options are kept near the beginning of the script whenever possible.

Larger harvesting suites are built with modular functions so individual features can be maintained, replaced, or expanded without rebuilding the entire script.

## Assisted and Automated Tools

Not every harvesting script has the same level of automation.

Some tools may only assist the player by identifying resources, interacting with nearby objects, processing materials, or managing inventory.

Others may contain more automated functionality.

**Always understand what a script does before running it.**

Different Ultima Online shards have very different rules regarding unattended harvesting, movement, resource gathering, and automation. The presence of functionality in this repository does not mean that functionality is permitted on every shard.

Always follow the rules of the shard you play on.

## Shard Compatibility

These scripts are developed for my own Ultima Online environment using **ClassicUO and Razor Enhanced**.

Harvesting systems frequently differ between shards.

Differences may include:

* Resource and item IDs
* Harvestable object IDs
* Resource respawn mechanics
* Gathering ranges
* Tool requirements
* Weight limits
* Resource processing
* Custom resources
* Storage systems
* Movement or pathfinding restrictions

Because of this, scripts may require configuration or modification before working correctly on another shard.

## Before Running a Script

Read the configuration section at the beginning of the script and any script-specific documentation provided here.

Pay particular attention to settings involving:

* Resource IDs
* Tool IDs
* Scan ranges
* Storage containers
* Weight limits
* Processing locations
* Movement or pathfinding

Make sure you understand the script's behavior before leaving it running.

## Scripts

Specific scripts and their requirements will be documented here as they are added to the repository.

### Harvesting Suites

*Coming soon.*

### Standalone Harvesting Tools

CottonPickerGUI_Private.py - A tool to assist with cotton gathering and processing. As of right now I don't recommend running this in auto mode as Unchained has mobs at the farms.
LeatherSkinner.py - A tool to assist with skinning animals and processing hides. This script is designed to be run as a dexxer but will work with other builds. I'll admit its a touch janky in this form. Will update.

## Bugs and Contributions

If a harvesting script behaves unexpectedly, please open a bug report or contact me directly.

When reporting an issue, include the script name, the error or unexpected behavior, and any relevant information about your shard's harvesting mechanics.

For repository usage, redistribution, modification, and AI/LLM restrictions, see the license and main README in the repository root.

---

**Frogmancer Schteve**

*Gather it. Process it. Hoard entirely too much of it.*
