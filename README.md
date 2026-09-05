# Frogmancer Schteve's Ultima Online Unchained Scripts

A collection of scripts, tools, monitors, and modular systems created for **Ultima Online**, primarily for use with **ClassicUO and Razor Enhanced**.

This repository is organized into several categories:

* **Crafting** - Crafting assistants, trainers, and profession-specific suites.
* **Harvesting** - Resource gathering and harvesting tools.
* **Monitor Systems** - Gumps, trackers, alerts, and informational displays.
* **Utility** - General quality-of-life tools and miscellaneous helpers.
* **FroggeCoreSystems** - Shared systems, frameworks, helpers, and reusable components used by other Frogge scripts.

## Intended Use

These scripts are shared for players who want to **use them, learn from them, modify them for their own needs, and contribute improvements back to the community**.

They are primarily written around my own playstyle, shard environment, and scripting preferences. Because Ultima Online shards can differ significantly in mechanics, item properties, gumps, delays, and rules, a script working in my environment does not guarantee that it will work unchanged in yours.

Always follow the rules of the shard you play on.

## AI / LLM Usage

**Please do not upload, submit, ingest, or otherwise provide the contents of this repository to Large Language Models (LLMs), AI coding assistants, machine-learning datasets, training pipelines, or similar automated systems.**

This includes using these scripts as source material for:

* AI training or fine-tuning
* Dataset creation
* Automated code generation
* AI-assisted derivative projects
* Repository-wide AI analysis or ingestion
* Repackaging these scripts through an AI service

These scripts represent time spent experimenting, debugging, learning the Razor Enhanced environment, and developing my own scripting patterns.

If you want to understand how something works, I encourage you to read the code, experiment with it, modify it, and learn from it directly.

**Contribute your own creativity. That's how we built this.**

## Bugs and Problems

If you encounter a problem with one of the scripts, **please report the problem to me rather than feeding the script into an LLM and asking it to fix it.**

When submitting a bug report, please include as much of the following as possible:

* Script name
* Script version, if listed
* Razor Enhanced version
* ClassicUO/client version when relevant
* What you expected to happen
* What actually happened
* Any Razor Enhanced error message or traceback
* The exact line number reported by the error
* Steps that reliably reproduce the issue
* Any shard-specific mechanics that may be relevant

You can submit an issue through this repository or contact me directly.

A good bug report helps improve the original script for everyone.

## Modifying the Scripts

Personal modifications are welcome.

Many scripts intentionally keep configuration values near the beginning of the file so common settings can be changed without digging through the implementation.

Depending on the script, this may include:

* Item and graphic IDs
* Gump positions
* Refresh rates
* Scan ranges
* Resource quantities
* Crafting settings
* Alert thresholds
* Shard-specific values

Some tools may require more substantial modification when used on shards with custom mechanics.

## Compatibility

Unless otherwise stated, scripts in this repository are designed around:

**Ultima Online Unchained**
**ClassicUO**
**Razor Enhanced**

These are not regular Razor scripts. They can be converted into Razor scripts if you strip the fluff out of them completely.

## Repository Philosophy

The goal of this project is not simply automation.

The goal is to build tools that are:

**Useful. Understandable. Modular. Maintainable.**

Larger projects may be organized as suites containing independent modules with shared interfaces and common systems. Smaller scripts may intentionally remain focused on solving one specific problem.

Expect the repository to evolve as existing scripts are cleaned up, documented, standardized, and expanded.

## Disclaimer

These scripts are provided **as-is**.

Ultima Online shards have different rules regarding scripting and automation. It is your responsibility to understand and follow the rules of the server on which you play.

The existence of functionality in this repository should not be interpreted as permission to use that functionality on a particular shard.

## Author

**Frogmancer Schteve**

If something breaks, open a bug report or come talk to me.

If something works, enjoy it.

If you improve something, I'd love to hear about it.

And please:

**Don't feed the frogs to the robots.**
