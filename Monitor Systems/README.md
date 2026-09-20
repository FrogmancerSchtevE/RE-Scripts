# Monitor Systems

This folder contains **Razor Enhanced monitors, trackers, alerts, and informational displays** for Ultima Online.

Monitor Systems are designed around a simple idea:

**Give the player useful information without getting in the way.**

These tools watch game state, equipment, items, mobiles, resources, or other conditions and present that information through compact Gumps, alerts, visual indicators, or other feedback.

## What You'll Find Here

Monitor Systems may include functionality such as:

* Equipment and durability tracking
* Health and status monitors
* Follower and summon monitoring
* Resource and progress tracking
* Nearby mobile detection
* Item detection
* Visual alerts
* Status Gumps
* Progress bars
* Threshold warnings
* Directional indicators
* Character or equipment state tracking

Some monitors are intentionally tiny and display a single piece of information.

Others may combine several related sources of information into a more complete dashboard.

## General Design

Monitor Systems generally follow a common structure:

**Configuration -> Helpers -> Monitoring Logic -> GUI -> Main**

The monitoring logic gathers information from Razor Enhanced while the GUI or notification layer presents it to the player.

Whenever possible, monitors should remain lightweight and responsive.

They should observe the game without becoming the game.

## Gumps & Displays

Many Monitor Systems use custom Razor Enhanced Gumps to provide persistent information directly on the game screen.

Common interface elements may include:

* Compact status rows
* Colored progress bars
* Percentage displays
* Item or mobile names
* Health information
* Warning states
* Tooltips
* Status colors
* Interactive buttons
* Current target or tracked entity information

Gumps are generally designed to provide useful information while occupying as little screen space as practical.

Larger monitoring tools may provide additional pages, settings, filters, or interactive controls.

## Alerts

Some monitors can notify the player when a particular condition occurs.

Examples may include:

* Equipment reaching low durability
* A tracked resource reaching a threshold
* A follower reaching low health
* A tracked object disappearing
* A nearby condition changing
* Something requiring the player's attention

Alerts may use:

* Overhead messages
* Razor Enhanced messages
* Gump state changes
* Color changes
* Visual effects
* Tracking arrows
* Other client-side indicators

Where possible, alerts should avoid excessive repetition or unnecessary spam.

The purpose is to draw attention to useful information, not bury the player in notifications.

## Performance

Monitoring scripts often run continuously while the player is logged in.

Because of this, efficiency matters.

Monitor Systems should generally:

* Use reasonable refresh intervals
* Avoid unnecessary repeated searches
* Cache information where appropriate
* Avoid excessive Gump rebuilding
* Minimize blocking operations
* Avoid unnecessary journal or property requests
* Update only as often as the monitored information requires

A monitor that runs for several hours should remain just as usable as one that has been running for several minutes.

## Interaction vs. Automation

Monitor Systems are primarily intended to **observe, display, and notify**.

Some monitors may include interactive controls or small convenience actions related directly to what is being monitored.

For example, a monitor might allow the player to interact with a tracked item, mobile, follower, or related system directly from its Gump.

More substantial automation generally belongs in another category or within a FroggeCore system.

## Configuration

Depending on the monitor, configurable settings may include:

* Refresh intervals
* Scan ranges
* Alert thresholds
* Item IDs
* Mobile filters
* Gump positions
* Gump dimensions
* Display options
* Alert behavior
* Highlight colors
* Tracking behavior

Frequently changed settings are kept near the beginning of the script whenever possible.

## Shard Compatibility

These scripts are developed for my own Ultima Online environment using **ClassicUO and Razor Enhanced**.

Monitor Systems can depend heavily on the information exposed by the client and shard.

Differences may include:

* Item properties
* Mobile properties
* Custom item IDs
* Custom status messages
* Equipment systems
* Followers and summons
* Journal messages
* Custom shard mechanics

A monitor may therefore require configuration or modification before working correctly on another shard.

## Scripts

Specific Monitor Systems and their requirements will be documented here as they are added to the repository.

### Status & Equipment Monitors

DurabilityChecker.py - My first script, its built on the example script and it'll keep a visual representation of your equipment durability on screen.
DarkPassage.py - On release of the Lantern for summoners I wrote this to keep track of the souls contained within. More or less useless since we don't have a way to stockpile/release the energy at will
CircleHudork.py - A circle hud that displays your current health and some selected items around your player. Moveable. Forked!! This was originally wrote by MeesaJarJar from the ServUO discord.


### Mobile & Follower Monitors

PlayerTrackerFrogg.py - A monitor that tracks and lists out players within a 24 tile radius, enumerating them from closest to furthert away.
FrogTamerSuite.py - A easy to use tamer monitor that has my FroggeVet built into it.
SummonSuite.py - My personal use assistent for managing summons on UO Unchained

### Alerts & Detection Systems

StealthDetector.py - A medium weight stealther detector, it works by detecting the stealth sound/footprints of stealthing npcs/players. (Also works on staff members)

### Resource & Progress Trackers

*Coming soon.*

## Bugs and Contributions

If a Monitor System displays incorrect information, fails to update, generates excessive alerts, or otherwise behaves unexpectedly, please open a bug report or contact me directly.

When reporting an issue, include the script name, what the monitor was displaying, what you expected it to display, and any relevant Razor Enhanced errors.

For repository usage, redistribution, modification, and AI/LLM restrictions, see the license and main README in the repository root.

---

**Frogmancer Schteve**

*If the client knows about it, there's probably a way to put it in a Gump.*
