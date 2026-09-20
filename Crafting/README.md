# Crafting

This folder contains **Razor Enhanced crafting scripts and crafting suites** for Ultima Online.

The goal of these tools is to make repetitive crafting tasks easier to manage while keeping configuration, status information, and player control accessible.

## What You'll Find Here

Crafting scripts may include functionality such as:

* Batch crafting
* Skill training
* Resource management
* Restocking from designated containers
* Crafting specific quantities of selected items
* Depositing completed items into storage
* Profession-specific utilities
* GUI-driven crafting controls
* Multi-function crafting suites

Some scripts are small tools designed for a single task, while others may develop into larger suites containing several related functions.

## General Design

Where practical, crafting tools follow a common structure:

**Configuration -> Helpers -> Crafting Logic -> GUI -> Main**

Frequently changed settings are kept near the beginning of the script whenever possible.

Larger crafting suites are designed around modular functions so new features can be added without requiring the entire tool to be rewritten.

## Shard Compatibility

These scripts are developed for my own Ultima Online environment using **ClassicUO and Razor Enhanced**.

Crafting systems can vary significantly between shards.

Differences may include:

* Crafting gump layouts and button IDs
* Item and resource IDs
* Custom recipes
* Skill requirements
* Crafting delays
* Resource requirements
* Storage systems
* Custom tools or crafting mechanics

Because of this, a script may require configuration or modification before working correctly on another shard.

## Before Running a Script

Read the configuration section at the beginning of the script and any script-specific documentation provided here.

Make sure you understand what containers, resources, tools, or other setup the script expects before enabling automated crafting functions.

Always follow the scripting and automation rules of the shard you play on.

## Scripts

Specific scripts and their requirements will be documented here as they are added to the repository.

### Crafting Suites

*Coming soon.*

### Standalone Crafting Tools

ToolBookRecharger.py - A tool I made to help automate the storage/withdraw of tools from UO Unchained tool book

## Bugs and Contributions

If a crafting script behaves unexpectedly, please open a bug report or contact me directly.

When reporting an issue, include the script name, the error or unexpected behavior, and any relevant information about your shard's crafting system.

For repository usage, redistribution, modification, and AI/LLM restrictions, see the license and main README in the repository root.

---

**Frogmancer Schteve**

*Build it. Break it. Fix it. Craft another one.*
