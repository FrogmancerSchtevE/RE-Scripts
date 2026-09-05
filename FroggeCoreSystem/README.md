# FroggeCoreSystems

**FroggeCoreSystems** is the home for larger, modular Razor Enhanced systems built for Ultima Online.

Unlike the standalone scripts found elsewhere in this repository, FroggeCore projects are designed around a **core + module architecture**.

The goal is to build larger tools without building larger messes.

Instead of putting every feature into a single monolithic script, FroggeCore systems separate shared functionality, user interfaces, configuration, and individual features into logical components that can be developed and maintained independently.

## What Is a FroggeCore System?

A FroggeCore system is intended to act more like an application framework than a traditional Razor Enhanced script.

The **Core** provides the common foundation.

Individual **Modules** provide the actual features.

A complete system may contain:

* Core runtime logic
* Shared configuration
* Common helper functions
* GUI and Gump frameworks
* Module registration
* Runtime module states
* Shared data and state management
* Status and notification systems
* Reusable item and mobile utilities
* Individual feature modules
* System-specific extensions

The exact architecture may evolve as FroggeCore develops, but the guiding principle remains the same:

**Build features as components, not as one enormous script.**

## Core + Modules

FroggeCore systems are designed around a modular relationship.

Conceptually:

```text
FroggeCore System
│
├── Core
│   ├── Runtime
│   ├── Configuration
│   ├── Shared State
│   ├── Common Helpers
│   └── GUI / Gump System
│
├── Modules
│   ├── Module A
│   ├── Module B
│   ├── Module C
│   └── ...
│
└── Main
    └── Coordinates the Core and active modules
```

The Core should handle the things that multiple modules need.

Modules should focus on doing their own job.

## Plugin-Driven Design

Where possible, new functionality should be added as a module or plugin rather than directly modifying unrelated parts of the Core.

This makes larger systems easier to:

* Expand
* Debug
* Maintain
* Disable or enable
* Reuse
* Test independently
* Share common functionality between features

A module should ideally know as little as possible about the internal implementation of other modules.

Shared functionality belongs in the Core.

Feature-specific functionality belongs in the module.

## Responsive Systems

FroggeCore projects are intended to remain responsive even as additional functionality is added.

Modules should perform small units of work and return control to the main system rather than monopolizing execution with long-running loops or unnecessary blocking delays.

A typical runtime concept looks something like:

```text
Read Input
    ↓
Update Core
    ↓
Run Active Module(s)
    ↓
Update Shared State
    ↓
Refresh Interface
    ↓
Repeat
```

This allows the interface, status system, and other modules to continue operating while work is being performed.

## User Interface

GUI-driven operation is an important part of FroggeCore.

Larger systems should provide an intuitive interface rather than requiring the user to constantly edit variables or manually start and stop separate scripts.

Depending on the project, interfaces may provide:

* Module ON/OFF controls
* Settings pages
* Current system status
* Module-specific controls
* Runtime information
* Resource information
* Alerts
* Target selection
* Saved configuration
* Navigation between modules
* Context-sensitive actions

The goal is for a completed FroggeCore system to feel like a cohesive Ultima Online tool rather than a collection of unrelated scripts.

## Shared Systems

Functionality that becomes useful across multiple projects may eventually become part of the FroggeCore foundation.

Examples could include:

* Gump helpers
* Targeting helpers
* Item and mobile searching
* Shared configuration handling
* Persistent settings
* Status reporting
* Common UI components
* Module lifecycle management
* Logging and debugging utilities

This allows future projects to build on systems that have already been tested instead of solving the same problems repeatedly.

## Development Philosophy

FroggeCore development follows a few basic principles:

**Modular**
Features should be isolated into logical components.

**Reusable**
Common functionality should be written once and shared where practical.

**Responsive**
Modules should avoid unnecessarily blocking the rest of the system.

**Maintainable**
Adding one feature should not require rewriting five unrelated ones.

**Intuitive**
Complex functionality should still be approachable through sensible controls and interfaces.

**Expandable**
A system should be able to grow without its architecture collapsing under its own weight.

## Experimental Nature

FroggeCoreSystems is also where more ambitious ideas are likely to live.

Some projects in this folder may be actively evolving, experimental, incomplete, or undergoing architectural changes.

Interfaces may change.

Module APIs may change.

Core systems may be rewritten as better patterns are discovered.

That is part of the purpose of this directory.

Standalone tools elsewhere in the repository may prioritize simplicity and stability.

**FroggeCore is where we build the bigger machines.**

## Compatibility

Unless otherwise stated, FroggeCoreSystems are developed for:

**Ultima Online**
**ClassicUO**
**Razor Enhanced**
**Razor Enhanced Python / IronPython**

Shard-specific mechanics may require individual modules to be configured or modified.

Always follow the scripting and automation rules of the shard you play on.

## Systems

Individual FroggeCore projects and their modules will be documented here as they are added.

### Core Systems

FrogDungeons
FrogGathering
FrogCrafting
FrogRoutes/Waypointer

### Modules & Plugins

MiningBot
LoggingBot
CottonBot
Route Builder

### Shared Components

Routes

## Bugs and Contributions

Because FroggeCore projects contain multiple interacting components, detailed bug reports are particularly useful.

When reporting an issue, please include:

* System name
* Module name
* What you were doing when the problem occurred
* Expected behavior
* Actual behavior
* Razor Enhanced error or traceback
* Relevant configuration
* Whether the problem occurs consistently

Please open a bug report or contact me directly rather than submitting the project to an LLM or AI coding service.

For repository usage, redistribution, modification, and AI/LLM restrictions, see the license and main README in the repository root.

---

**Frogmancer Schteve**

*Small scripts solve problems. FroggeCore is its own system.*
