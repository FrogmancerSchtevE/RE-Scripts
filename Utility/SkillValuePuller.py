# ==================================
# === Skill Value Probe          ===
# ==================================

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