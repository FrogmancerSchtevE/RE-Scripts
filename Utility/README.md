# Utility

This folder contains **general-purpose Razor Enhanced utilities and quality-of-life tools** for Ultima Online.

These scripts are intended to solve the smaller problems that come up during everyday gameplay. Some are simple single-purpose tools, while others may provide a GUI or several related functions.

If it is useful but doesn't belong anywhere else, there's a good chance it belongs here.

## What You'll Find Here

Utility scripts may include functionality such as:

* Equipment and weapon management
* Item and container management
* Looting helpers
* Targeting tools
* Vendor and shopping assistants
* Inventory organization
* Item inspection and highlighting
* Character convenience tools
* Small GUI-driven helpers
* General quality-of-life improvements

The focus is usually on making common actions faster, easier to manage, or more informative without requiring a large dedicated suite.

## General Design

Where practical, utility tools follow a common structure:

**Configuration -> Helpers -> Utility Logic -> GUI -> Main**

Frequently changed settings are kept near the beginning of the script whenever possible.

Smaller utilities may intentionally remain simple rather than being expanded into a larger framework. A tool that does one job reliably doesn't necessarily need to become a suite.

## Configuration

Many utility scripts require some amount of player-specific configuration.

Depending on the tool, this may include:

* Item or graphic IDs
* Saved item serials
* Containers
* Scan ranges
* Gump positions
* Refresh rates
* Targeting preferences
* Shard-specific settings

Some tools may save selected items or configuration through Razor Enhanced shared values so they do not need to be configured every time the script is started.

Read the configuration section and any script-specific documentation before running a new utility.

## Shard Compatibility

These scripts are developed for my own Ultima Online environment using **ClassicUO and Razor Enhanced**.

Utility scripts can be particularly sensitive to shard-specific mechanics because they often interact directly with items, equipment, containers, vendors, context menus, or custom systems.

A script working correctly on my shard does not guarantee identical behavior elsewhere.

Always follow the scripting and automation rules of the shard you play on.

## Before Running a Script

Take a moment to understand what the utility interacts with before using it.

In particular, check whether the script:

* Moves items
* Equips or unequips equipment
* Uses stored item serials
* Interacts with containers
* Targets mobiles or items
* Uses context menus
* Performs actions automatically

When in doubt, test new utilities somewhere safe before trusting them with valuable equipment or resources.

## Scripts

GrinchSatchelPointer.py - A tool to help locate the christmas grinch satchels, circa 2025.
FrogHouseDecayLogger.py - A tool to log fairly and worse conditioned houses, it'll output it in .xml format and place it in your CUO map data folder. Reload to refresh your markers)


### General Utilities

*FroggVet - A small utility to help manage your pets and their health.*
SummonerSuite - A utility I use personally to manage and control my summons. I believe its pretty intuitive and easy to use. I am aware that the names glitch out. I'm working on it for the Core System.
TrapMaster.py - A fun tool to help with a trapper build, Its janky but functional. And it looks cool.
SkillValuePuller.py - This will run a list of GetSkillValue and print what is successful and what isnt, made it to diagnose fletching on UO Unchained.
PlayerCatcher.py - This script will drop wooden boxes at target location or around a players four cardinal directions. Funny

### Equipment & Inventory Tools

AutoGoldSatchel.py - A tool that automatically loots gold into your satchel (or designated bag) and keeps a halfass log/gph tracker. 

### Vendor & Item Tools

VendorAssistant.py - Supposed to help filter a player vendor to prevent scamming. TOKMACI is a dipshit and I'll stand on that hill.
FastInspect.py

## Bugs and Contributions

If a utility behaves unexpectedly, please open a bug report or contact me directly.

When reporting an issue, include the script name, what you expected it to do, what actually happened, and any Razor Enhanced errors that were generated.

For repository usage, redistribution, modification, and AI/LLM restrictions, see the license and main README in the repository root.

---

**Frogmancer Schteve**

*Small tools for problems that got annoying enough to automate.*
