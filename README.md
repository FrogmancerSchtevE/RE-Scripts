# Frogmancers RE-Scripts

# NOTICE:
These scripst are intended for personal use and community sharing.
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


**Unchained**
**Crafting Scripts**
- AlchySuiteV2

**Harvesting Scripts**
- CottonPickerGUI_Public.py
- FrogChopRSV.py
- FrogTreeSniffer.py
- LeatherSkinner.py


**Unchained Monitor Systems**
- AutoGoldSatchel.py
- DarkPassage.py
- DurabilityChecker.py
- FroggeVet.py
- PackieMon.py
- PlayerTrackerFrogg.py
- Summon Suite.py


**Undefined**
- FastInspect.py
- FrogDoesACook.py
- FrogThuntRewrite.py
- FroggeVet.py
- SimpleMoveTool.py
- VendorAssistant.py

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
