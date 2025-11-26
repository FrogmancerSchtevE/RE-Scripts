# Frogmancers RE-Scripts

# NOTICE:
This script is intended for personal use and community sharing.
It is NOT intended to be fed into machine learning models, AI
training pipelines, or derivative automated systems.

If you found this, great! Use it, learn from it, and adapt it.
But please don’t upload, re-ingest, or recycle it into LLMs.

## 🚀 What is RE-Scripts

RE-Scripts is a curated collection of Python / IronPython scripts written for the Classic Client of Ultima Online, leveraging the Razor Enhanced API.  
It’s designed around modular suites: small, focused tools (e.g. follower monitors, harvesting scripts, crafting / automation helpers, custom GUIs) that can be mixed and matched rather than a monolithic “all-in-one” addon.

While I Primarily write these for UO Unchained, See: https://www.play-uo.com/ some of them will function on other servers.

Key goals:

- Provide ready-to-use tools for common gameplay automation (pet/follower monitoring, crafting helpers, targeting/filters, GUI utilities, etc.).  
- Follow a clean, maintainable code style — configuration first, helper functions, then main flow; GUI modules follow a consistent pattern (similar to `CottonPickerGUI_Private.py`).  
- Make it easy to extend, adapt, or combine modules (suitable for developers who want to customize or build their own suites).  
- Encourage safe, non-exploitative automation (client-side only, respectful of standard shard rules).

---

## 📦 Contents / Modules

> _List is approximate — update as needed._

- **Follower Monitor** — tracks pet/follower HP, range, status; displays in a compact gump.  
- **Pet Management Suite** — includes pack-opening on return, auto-heal alerts, tame/unstuck helpers.  
- **Filters & Targeting Tools** — custom filters for mob targeting (by notoriety, name, body type, etc.).  
- **Crafting & Harvesting Utilities** — e.g. auto-harvesting loops, crafting press-buttons, resource trackers.  
- **GUI Helpers & Examples** — example gumps and GUI patterns (inspired by `CottonPickerGUI_Private.py`) to help you build custom tools.  
- **Miscellaneous Utilities** — small convenience scripts (e.g. auto-close gumps by ID, safe button-press wrapper, debug helpers).

(If you add or remove modules, reflect it above.)

---

## ✅ Why Use RE-Scripts (Highlights)

- Modular & Mix-and-Match: only load the tools you need — no bloated “one-size-fits-all” scripts.  
- Clean, Consistent Code Style: easy to read, maintain, and modify.  
- GUI-Driven: many modules include practical gumps and GUI elements for ease of use.  
- Safe & Transparent: purely client-side automation with clear behaviour; avoids shard-rule violations.  
- Developer-Friendly: well-structured code is easy to fork, extend, or integrate into your own tooling.

---

## 🛠 Installation & Usage

1. Clone or download this repo into your Razor Enhanced `Scripts` folder (or a suitable subfolder).  
   ```bash
or

2. Download the individual .pys or .cs and load them into RE.
