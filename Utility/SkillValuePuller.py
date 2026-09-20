# =================================================
# === Skill Value Probe (Razor Enhanced Script) ===
# =================================================
# Copyright (c) Frogmancer Schteve. All rights reserved except as
# expressly permitted by the repository License.md.
#
# PERSONAL USE
# This script is provided for personal, non-commercial use.
# You may use, study, and modify it for your own use. Redistribution,
# resale, sublicensing, or incorporation into another distributed
# project is not permitted without prior permission.
#
# AI / LLM RESTRICTION
# Do NOT upload, submit, ingest, or otherwise provide this script,
# in whole or substantial part, to Large Language Models (LLMs),
# generative AI systems, AI coding assistants, machine-learning
# datasets, training/fine-tuning pipelines, retrieval systems, or
# automated code-generation systems.
#
# If you encounter a bug or compatibility issue, please submit an
# issue through the repository or contact Frogmancer Schteve directly
# rather than submitting the script to an AI service for troubleshooting.
#
# SHARD RULES
# You are responsible for ensuring your use of this script complies
# with the rules of the Ultima Online shard on which you play.
#
# This notice is only a summary. The repository License.md contains
# the complete terms governing use of this software.
#
# Use it. Learn from it. Improve it.
# Just don't feed the frogs to the robots.
# ====================================================================

# ===========================================================
# CONFIGURATION
# ===========================================================

SKILLS = [
    "Alchemy",
    "Anatomy",
    "Animal Lore",
    "Item ID",
    "Arms Lore",
    "Parry",
    "Begging",
    "Blacksmith",
    "Fletching",
    "Peacemaking",
    "Camping",
    "Carpentry",
    "Cartography",
    "Cooking",
    "Detect Hidden",
    "Discordance",
    "EvalInt",
    "Healing",
    "Fishing",
    "Forensics",
    "Herding",
    "Hiding",
    "Provocation",
    "Inscribe",
    "Lockpicking",
    "Magery",
    "Magic Resist",
    "Mysticism",
    "Tactics",
    "Snooping",
    "Musicianship",
    "Poisoning",
    "Archery",
    "Spirit Speak",
    "Stealing",
    "Tailoring",
    "Animal Taming",
    "Taste ID",
    "Tinkering",
    "Tracking",
    "Veterinary",
    "Swords",
    "Macing",
    "Fencing",
    "Wrestling",
    "Lumberjacking",
    "Mining",
    "Meditation",
    "Stealth",
    "Remove Trap",
    "Necromancy",
    "Focus",
    "Chivalry",
    "Bushido",
    "Ninjitsu",
    "Spell Weaving",
    "Imbuing",
]

# Extra names worth testing
ALIASES = [
    "Bowcraft",
    "Bowcraft/Fletching",
    "Bowcraft and Fletching",
    "Bowcraft & Fletching",
    "Fletching",
]

# ===========================================================
# HELPERS
# ===========================================================

def test_skill(skill_name):
    try:
        value = Player.GetSkillValue(skill_name)
        Misc.SendMessage(
            "{0:<24} = {1}".format(skill_name, value),
            68
        )
        return value
    except Exception as e:
        Misc.SendMessage(
            "{0:<24} = ERROR: {1}".format(skill_name, str(e)),
            33
        )
        return None


# ===========================================================
# MAIN
# ===========================================================

Misc.SendMessage("========== ALL SKILLS ==========", 55)

for skill in SKILLS:
    test_skill(skill)

Misc.SendMessage("========== FLETCHING TEST ==========", 55)

for skill in ALIASES:
    test_skill(skill)

Misc.SendMessage("========== DONE ==========", 55)