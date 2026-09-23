# ==================================================
# === Frog Crafting Trainer (Razor Enhanced) ===
# =============================================
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

import json
import time
from System.IO import Directory, File, Path
import Gumps
import Items
import Journal
import Misc
import Player
import Target


# ===========================================================
# USER SETTINGS
# ===========================================================

# Set this only if Razor Enhanced cannot determine this script's folder.
TRAINER_DIRECTORY_OVERRIDE = ""
RESTOCK_CRAFTS = 25
SHELF_WITHDRAW_AMOUNT = 100  # Set and lock this on the shelf in game.
TOOL_BOOK_CHARGES = 50


# ===========================================================
# CONFIGURATION / TRAINING PATHS
# ===========================================================

VERSION = "0.1"
GUMP_ID = 0xF2065452
GUMP_X, GUMP_Y = 520, 210
BG_ID = 5054
TITLE_HUE = 1152
LABEL_HUE = 0x0481
DIM_HUE = 0x044E
GOOD_HUE = 68
WARN_HUE = 53
BAD_HUE = 33
SERVER_WAIT_MS = 2500
MOVE_WAIT_MS = 700
RESULT_WAIT_MS = 700
TARGET_WAIT_MS = 2500
REFRESH_MS = 250
MAX_FAILURE_RETRIES = 10
TOOL_BOOK_GUMP_ID = 0xC3DE2C83
SETTINGS_FORMAT = "frog-crafting-trainer-settings"
SETTINGS_FIELDS = ("source_mode", "resource_chest", "resource_shelf", "reagent_shelf", "output_chest", "tool_book", "trash_container")


## DO NOT EDIT THIS. I have zero faith in your abilities to do so. Yes you.

## I'm serious.
TRAINING_DATA = json.loads(r'''{
"skills":[
{
"id":"alchemy",
"name":"Alchemy",
"skill_name":"Alchemy",
"goal":100.0,
"informational":false,
"message":"",
"gump_id":949095101,
"tool":{"name":"Mortar and Pestle","item_ids":[3739],"names":["Mortar and Pestle","Mortar & Pestle","Alchemy Tool"],"book_button":7},
"stages":[
{"min_skill":0.0,"max_skill":30.0,"mode":"npc_train","label":"NPC Train","recipe_ids":[],"disposal":{"mode":"none","button":null,"target_output":false}},
{"min_skill":30.0,"max_skill":45.0,"mode":"craft","label":"Lesser Heal Potion","recipe_ids":["lesser_heal"],"disposal":{"mode":"trash","button":null,"target_output":false}},
{"min_skill":45.0,"max_skill":55.0,"mode":"craft","label":"Lesser Cure Potion","recipe_ids":["lesser_cure"],"disposal":{"mode":"trash","button":null,"target_output":false}},
{"min_skill":55.0,"max_skill":65.0,"mode":"craft","label":"Agility Potion","recipe_ids":["agility"],"disposal":{"mode":"trash","button":null,"target_output":false}},
{"min_skill":65.0,"max_skill":75.0,"mode":"craft","label":"Total Refresh Potion","recipe_ids":["greater_refreshment"],"disposal":{"mode":"trash","button":null,"target_output":false}},
{"min_skill":75.0,"max_skill":85.0,"mode":"craft","label":"Greater Heal Potion","recipe_ids":["greater_heal"],"disposal":{"mode":"trash","button":null,"target_output":false}},
{"min_skill":85.0,"max_skill":95.0,"mode":"craft","label":"Greater Cure Potion","recipe_ids":["greater_cure"],"disposal":{"mode":"trash","button":null,"target_output":false}},
{"min_skill":95.0,"max_skill":100.0,"mode":"craft","label":"Greater Poison / Conflagration","recipe_ids":["greater_poison","greater_conflagration"],"disposal":{"mode":"trash","button":null,"target_output":false}}
],"recipes":{
"greater_refreshment":{"name":"Greater Refreshment","min_skill":25.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"black_pearl","name":"Black Pearl","amount":5,"item_id":5002,"hue":null,"names":["Black Pearl"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,1]},{"key":"empty_bottle","name":"Empty Bottle","amount":1,"item_id":3854,"hue":null,"names":["Empty Bottle","Empty Bottles"],"shelf_page":3,"shelf_button":50,"reagent_actions":[3577,20]}],"actions":[1,9],"output_ids":[],"output_names":["Greater Refreshment Potion"],"output_hue":-1,"output_amount":1},
"lesser_heal":{"name":"Lesser Heal","min_skill":0.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"ginseng","name":"Ginseng","amount":1,"item_id":3973,"hue":null,"names":["Ginseng"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,8]},{"key":"empty_bottle","name":"Empty Bottle","amount":1,"item_id":3854,"hue":null,"names":["Empty Bottle","Empty Bottles"],"shelf_page":3,"shelf_button":50,"reagent_actions":[3577,20]}],"actions":[1,16],"output_ids":[],"output_names":["Lesser Heal Potion"],"output_hue":-1,"output_amount":1},
"greater_heal":{"name":"Greater Heal","min_skill":55.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"ginseng","name":"Ginseng","amount":7,"item_id":3973,"hue":null,"names":["Ginseng"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,8]},{"key":"empty_bottle","name":"Empty Bottle","amount":1,"item_id":3854,"hue":null,"names":["Empty Bottle","Empty Bottles"],"shelf_page":3,"shelf_button":50,"reagent_actions":[3577,20]}],"actions":[1,30],"output_ids":[],"output_names":["Greater Heal Potion"],"output_hue":-1,"output_amount":1},
"lesser_cure":{"name":"Lesser Cure","min_skill":0.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"garlic","name":"Garlic","amount":1,"item_id":5006,"hue":null,"names":["Garlic"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,7]},{"key":"empty_bottle","name":"Empty Bottle","amount":1,"item_id":3854,"hue":null,"names":["Empty Bottle","Empty Bottles"],"shelf_page":3,"shelf_button":50,"reagent_actions":[3577,20]}],"actions":[1,37],"output_ids":[],"output_names":["Lesser Cure Potion"],"output_hue":-1,"output_amount":1},
"greater_cure":{"name":"Greater Cure","min_skill":65.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"garlic","name":"Garlic","amount":6,"item_id":5006,"hue":null,"names":["Garlic"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,7]},{"key":"empty_bottle","name":"Empty Bottle","amount":1,"item_id":3854,"hue":null,"names":["Empty Bottle","Empty Bottles"],"shelf_page":3,"shelf_button":50,"reagent_actions":[3577,20]}],"actions":[1,51],"output_ids":[],"output_names":["Greater Cure Potion"],"output_hue":-1,"output_amount":1},
"agility":{"name":"Agility","min_skill":15.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"bloodmoss","name":"Bloodmoss","amount":1,"item_id":3963,"hue":null,"names":["Bloodmoss","Blood Moss"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,2]},{"key":"empty_bottle","name":"Empty Bottle","amount":1,"item_id":3854,"hue":null,"names":["Empty Bottle","Empty Bottles"],"shelf_page":3,"shelf_button":50,"reagent_actions":[3577,20]}],"actions":[15,2],"output_ids":[],"output_names":["Agility Potion"],"output_hue":-1,"output_amount":1},
"greater_poison":{"name":"Greater Poison","min_skill":55.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"nightshade","name":"Nightshade","amount":4,"item_id":5009,"hue":null,"names":["Nightshade"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,5]},{"key":"empty_bottle","name":"Empty Bottle","amount":1,"item_id":3854,"hue":null,"names":["Empty Bottle","Empty Bottles"],"shelf_page":3,"shelf_button":50,"reagent_actions":[3577,20]}],"actions":[29,16],"output_ids":[],"output_names":["Greater Poison Potion"],"output_hue":-1,"output_amount":1},
"greater_conflagration":{"name":"Greater Conflagration","min_skill":70.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"sulfurous_ash","name":"Sulfurous Ash","amount":10,"item_id":3980,"hue":null,"names":["Sulfurous Ash","Sulfuroush Ash","1 Sulferous Ash","Sulferous Ash"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,6]},{"key":"empty_bottle","name":"Empty Bottle","amount":1,"item_id":3854,"hue":null,"names":["Empty Bottle","Empty Bottles"],"shelf_page":3,"shelf_button":50,"reagent_actions":[3577,20]}],"actions":[36,30],"output_ids":[],"output_names":["Greater Conflagration Potion"],"output_hue":-1,"output_amount":1}
}},
{
"id":"blacksmithy",
"name":"Blacksmithy",
"skill_name":"Blacksmith",
"goal":120.0,
"informational":false,
"message":"",
"gump_id":949095101,
"tool":{"name":"Smith's Hammer","item_ids":[5091],"names":["Smith's Hammer","Smith Hammer"],"book_button":1},
"stages":[
{"min_skill":0.0,"max_skill":50.0,"mode":"npc_train","label":"NPC Train","recipe_ids":[],"disposal":{"mode":"none","button":null,"target_output":false}},
{"min_skill":50.0,"max_skill":55.0,"mode":"craft","label":"Maces","recipe_ids":["mace"],"disposal":{"mode":"smelt","button":14,"target_output":true}},
{"min_skill":55.0,"max_skill":60.0,"mode":"craft","label":"Mauls","recipe_ids":["maul"],"disposal":{"mode":"smelt","button":14,"target_output":true}},
{"min_skill":60.0,"max_skill":70.0,"mode":"craft","label":"Cutlasses / Katanas","recipe_ids":["cutlass","katana"],"disposal":{"mode":"smelt","button":14,"target_output":true}},
{"min_skill":70.0,"max_skill":95.0,"mode":"craft","label":"Short Spears","recipe_ids":["short_spear"],"disposal":{"mode":"smelt","button":14,"target_output":true}},
{"min_skill":95.0,"max_skill":105.0,"mode":"craft","label":"Plate Gorgets","recipe_ids":["platemail_gorget"],"disposal":{"mode":"smelt","button":14,"target_output":true}},
{"min_skill":105.0,"max_skill":108.0,"mode":"craft","label":"Platemail Gloves","recipe_ids":["platemail_gloves"],"disposal":{"mode":"smelt","button":14,"target_output":true}},
{"min_skill":108.0,"max_skill":115.0,"mode":"craft","label":"Platemail Arms","recipe_ids":["platemail_arms"],"disposal":{"mode":"smelt","button":14,"target_output":true}},
{"min_skill":115.0,"max_skill":120.0,"mode":"craft","label":"Platemail Tunics","recipe_ids":["platemail_tunic"],"disposal":{"mode":"smelt","button":14,"target_output":true}}
],"recipes":{
"platemail_arms":{"name":"Platemail Arms","min_skill":66.3,"enabled":true,"skill_requirements":[],"resources":[{"key":"iron_ingot","name":"Iron","amount":18,"item_id":7154,"hue":0,"names":["Iron","Ingot","Ingots","Iron Ingot","Iron Ingots"],"shelf_page":1,"shelf_button":1,"reagent_actions":[]}],"actions":[7,6,22,51],"output_ids":[],"output_names":["Platemail Arms"],"output_hue":-1,"output_amount":1},
"platemail_gloves":{"name":"Platemail Gloves","min_skill":58.9,"enabled":true,"skill_requirements":[],"resources":[{"key":"iron_ingot","name":"Iron","amount":12,"item_id":7154,"hue":0,"names":["Iron","Ingot","Ingots","Iron Ingot","Iron Ingots"],"shelf_page":1,"shelf_button":1,"reagent_actions":[]}],"actions":[7,6,22,58],"output_ids":[],"output_names":["Platemail Gloves"],"output_hue":-1,"output_amount":1},
"platemail_gorget":{"name":"Platemail Gorget","min_skill":56.4,"enabled":true,"skill_requirements":[],"resources":[{"key":"iron_ingot","name":"Iron","amount":10,"item_id":7154,"hue":0,"names":["Iron","Ingot","Ingots","Iron Ingot","Iron Ingots"],"shelf_page":1,"shelf_button":1,"reagent_actions":[]}],"actions":[7,6,22,65],"output_ids":[],"output_names":["Platemail Gorget"],"output_hue":-1,"output_amount":1},
"platemail_tunic":{"name":"Platemail Tunic","min_skill":75.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"iron_ingot","name":"Iron","amount":25,"item_id":7154,"hue":0,"names":["Iron","Ingot","Ingots","Iron Ingot","Iron Ingots"],"shelf_page":1,"shelf_button":1,"reagent_actions":[]}],"actions":[7,6,22,79],"output_ids":[],"output_names":["Platemail Tunic"],"output_hue":-1,"output_amount":1},
"cutlass":{"name":"Cutlass","min_skill":24.3,"enabled":true,"skill_requirements":[],"resources":[{"key":"iron_ingot","name":"Iron","amount":8,"item_id":7154,"hue":0,"names":["Iron","Ingot","Ingots","Iron Ingot","Iron Ingots"],"shelf_page":1,"shelf_button":1,"reagent_actions":[]}],"actions":[7,6,43,16],"output_ids":[],"output_names":["Cutlass"],"output_hue":-1,"output_amount":1},
"katana":{"name":"Katana","min_skill":44.1,"enabled":true,"skill_requirements":[],"resources":[{"key":"iron_ingot","name":"Iron","amount":8,"item_id":7154,"hue":0,"names":["Iron","Ingot","Ingots","Iron Ingot","Iron Ingots"],"shelf_page":1,"shelf_button":1,"reagent_actions":[]}],"actions":[7,6,43,30],"output_ids":[],"output_names":["Katana"],"output_hue":-1,"output_amount":1},
"short_spear":{"name":"Short Spear","min_skill":45.3,"enabled":true,"skill_requirements":[],"resources":[{"key":"iron_ingot","name":"Iron","amount":6,"item_id":7154,"hue":0,"names":["Iron","Ingot","Ingots","Iron Ingot","Iron Ingots"],"shelf_page":1,"shelf_button":1,"reagent_actions":[]}],"actions":[7,6,105,57,37],"output_ids":[],"output_names":["Short Spear"],"output_hue":-1,"output_amount":1},
"mace":{"name":"Mace","min_skill":14.5,"enabled":true,"skill_requirements":[],"resources":[{"key":"iron_ingot","name":"Iron","amount":6,"item_id":7154,"hue":0,"names":["Iron","Ingot","Ingots","Iron Ingot","Iron Ingots"],"shelf_page":1,"shelf_button":1,"reagent_actions":[]}],"actions":[7,6,105,64,9],"output_ids":[3932],"output_names":["Mace"],"output_hue":-1,"output_amount":1},
"maul":{"name":"Maul","min_skill":19.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"iron_ingot","name":"Iron","amount":10,"item_id":7154,"hue":0,"names":["Iron","Ingot","Ingots","Iron Ingot","Iron Ingots"],"shelf_page":1,"shelf_button":1,"reagent_actions":[]}],"actions":[7,6,105,64,16],"output_ids":[],"output_names":["Maul"],"output_hue":-1,"output_amount":1}
}},
{
"id":"carpentry",
"name":"Carpentry",
"skill_name":"Carpentry",
"goal":120.0,
"informational":false,
"message":"",
"gump_id":949095101,
"tool":{"name":"Carpentry Tool","item_ids":[],"names":["Carpentry Tool","Dovetail Saw","Saw","Nails"],"book_button":2},
"stages":[
{"min_skill":0.0,"max_skill":30.0,"mode":"npc_train","label":"NPC Train","recipe_ids":[],"disposal":{"mode":"none","button":null,"target_output":false}},
{"min_skill":30.0,"max_skill":47.3,"mode":"craft","label":"Medium / Small Crates","recipe_ids":["medium_crate","small_crate"],"disposal":{"mode":"recycle","button":77,"target_output":true}},
{"min_skill":47.3,"max_skill":70.0,"mode":"craft","label":"Ballot Boxes","recipe_ids":["ballot_box"],"disposal":{"mode":"trash","button":77,"target_output":true}},
{"min_skill":70.0,"max_skill":73.6,"mode":"craft","label":"Clubs","recipe_ids":["club"],"disposal":{"mode":"recycle","button":77,"target_output":true}},
{"min_skill":73.6,"max_skill":78.9,"mode":"craft","label":"Quarter Staffs","recipe_ids":["quarter_staff"],"disposal":{"mode":"recycle","button":77,"target_output":true}},
{"min_skill":78.9,"max_skill":100.0,"mode":"craft","label":"Gnarled Staffs","recipe_ids":["gnarled_staff"],"disposal":{"mode":"recycle","button":77,"target_output":true}},
{"min_skill":100.0,"max_skill":107.5,"mode":"craft","label":"Plain Wooden Chests","recipe_ids":["plain_wooden_chest","finished_wooden_chest","gilded_wooden_chest"],"disposal":{"mode":"recycle","button":77,"target_output":true}},
{"min_skill":107.5,"max_skill":120.0,"mode":"craft","label":"Pentagrams / Abbatoirs","recipe_ids":["pentagram","abbatoir"],"disposal":{"mode":"recycle","button":77,"target_output":true}}
],"recipes":{
"small_crate":{"name":"Small Crate","min_skill":10.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"plain_board","name":"Wood","amount":8,"item_id":7127,"hue":0,"names":["Wood","Log","Logs","Board","Boards","Plain Board","Plain Boards","Boards or Logs"],"shelf_page":1,"shelf_button":11,"reagent_actions":[]}],"actions":[7,6,29,9],"output_ids":[],"output_names":["Small Crate"],"output_hue":-1,"output_amount":1},
"medium_crate":{"name":"Medium Crate","min_skill":31.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"plain_board","name":"Wood","amount":15,"item_id":7127,"hue":0,"names":["Wood","Log","Logs","Board","Boards","Plain Board","Plain Boards","Boards or Logs"],"shelf_page":1,"shelf_button":11,"reagent_actions":[]}],"actions":[7,6,29,16],"output_ids":[],"output_names":["Medium Crate"],"output_hue":-1,"output_amount":1},
"plain_wooden_chest":{"name":"Plain Wooden chest","min_skill":90.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"plain_board","name":"Wood","amount":15,"item_id":7127,"hue":0,"names":["Wood","Log","Logs","Board","Boards","Plain Board","Plain Boards","Boards or Logs"],"shelf_page":1,"shelf_button":11,"reagent_actions":[]}],"actions":[7,6,29,58],"output_ids":[],"output_names":["Plain Wooden chest"],"output_hue":-1,"output_amount":1},
"gilded_wooden_chest":{"name":"Gilded Wooden Chest","min_skill":90.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"plain_board","name":"Wood","amount":15,"item_id":7127,"hue":0,"names":["Wood","Log","Logs","Board","Boards","Plain Board","Plain Boards","Boards or Logs"],"shelf_page":1,"shelf_button":11,"reagent_actions":[]}],"actions":[7,6,29,72],"output_ids":[],"output_names":["Gilded Wooden Chest"],"output_hue":-1,"output_amount":1},
"finished_wooden_chest":{"name":"Finished Wooden Chest","min_skill":90.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"plain_board","name":"Wood","amount":15,"item_id":7127,"hue":0,"names":["Wood","Log","Logs","Board","Boards","Plain Board","Plain Boards","Boards or Logs"],"shelf_page":1,"shelf_button":11,"reagent_actions":[]}],"actions":[7,6,29,86],"output_ids":[],"output_names":["Finished Wooden Chest"],"output_hue":-1,"output_amount":1},
"quarter_staff":{"name":"Quarter Staff","min_skill":73.6,"enabled":true,"skill_requirements":[],"resources":[{"key":"plain_board","name":"Wood","amount":6,"item_id":7127,"hue":0,"names":["Wood","Log","Logs","Board","Boards","Plain Board","Plain Boards","Boards or Logs"],"shelf_page":1,"shelf_button":11,"reagent_actions":[]}],"actions":[7,6,36,9],"output_ids":[],"output_names":["Quarter Staff"],"output_hue":-1,"output_amount":1},
"gnarled_staff":{"name":"Gnarled Staff","min_skill":78.9,"enabled":true,"skill_requirements":[],"resources":[{"key":"plain_board","name":"Wood","amount":7,"item_id":7127,"hue":0,"names":["Wood","Log","Logs","Board","Boards","Plain Board","Plain Boards","Boards or Logs"],"shelf_page":1,"shelf_button":11,"reagent_actions":[]}],"actions":[7,6,36,16],"output_ids":[],"output_names":["Gnarled Staff"],"output_hue":-1,"output_amount":1},
"club":{"name":"Club","min_skill":65.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"plain_board","name":"Wood","amount":9,"item_id":7127,"hue":0,"names":["Wood","Log","Logs","Board","Boards","Plain Board","Plain Boards","Boards or Logs"],"shelf_page":1,"shelf_button":11,"reagent_actions":[]}],"actions":[7,6,36,30],"output_ids":[],"output_names":["Club"],"output_hue":-1,"output_amount":1},
"ballot_box":{"name":"Ballot Box","min_skill":47.3,"enabled":true,"skill_requirements":[],"resources":[{"key":"plain_board","name":"Wood","amount":5,"item_id":7127,"hue":0,"names":["Wood","Log","Logs","Board","Boards","Plain Board","Plain Boards","Boards or Logs"],"shelf_page":1,"shelf_button":11,"reagent_actions":[]}],"actions":[7,6,105,64,93],"output_ids":[],"output_names":["Ballot Box"],"output_hue":-1,"output_amount":1},
"pentagram":{"name":"Pentagram","min_skill":100.0,"enabled":true,"skill_requirements":[{"skill_name":"Magery","min_skill":75.0}],"resources":[{"key":"plain_board","name":"Wood","amount":100,"item_id":7127,"hue":0,"names":["Wood","Log","Logs","Board","Boards","Plain Board","Plain Boards","Boards or Logs"],"shelf_page":1,"shelf_button":11,"reagent_actions":[]},{"key":"iron_ingot","name":"Iron Ingot","amount":40,"item_id":7154,"hue":0,"names":["Iron Ingot","Ingot","Ingots","Iron Ingots"],"shelf_page":1,"shelf_button":1,"reagent_actions":[]}],"actions":[7,6,105,64,100],"output_ids":[],"output_names":["Pentagram"],"output_hue":-1,"output_amount":1},
"abbatoir":{"name":"Abbatoir","min_skill":100.0,"enabled":true,"skill_requirements":[{"skill_name":"Magery","min_skill":50.0}],"resources":[{"key":"plain_board","name":"Wood","amount":100,"item_id":7127,"hue":0,"names":["Wood","Log","Logs","Board","Boards","Plain Board","Plain Boards","Boards or Logs"],"shelf_page":1,"shelf_button":11,"reagent_actions":[]},{"key":"iron_ingot","name":"Iron Ingot","amount":40,"item_id":7154,"hue":0,"names":["Iron Ingot","Ingot","Ingots","Iron Ingots"],"shelf_page":1,"shelf_button":1,"reagent_actions":[]}],"actions":[7,6,105,64,107],"output_ids":[],"output_names":["Abbatoir"],"output_hue":-1,"output_amount":1}
}},
{
"id":"cooking",
"name":"Cooking",
"skill_name":"Cooking",
"goal":120.0,
"informational":true,
"message":"You can train this fast by bulk cooking fishsteaks! Best of luck",
"gump_id":949095101,
"tool":{"name":"Cooking Tool","item_ids":[],"names":["Cooking Tool","Skillet","Frying Pan"],"book_button":6},
"stages":[
],"recipes":{
}},
{
"id":"fletching",
"name":"Fletching",
"skill_name":"Bowcraft",
"goal":120.0,
"informational":false,
"message":"",
"gump_id":949095101,
"tool":{"name":"Fletcher's Tools","item_ids":[4130],"names":["Fletcher's Tools","Fletcher Tools","Fletching Tool"],"book_button":8},
"stages":[
{"min_skill":0.0,"max_skill":30.0,"mode":"npc_train","label":"NPC Train","recipe_ids":[],"disposal":{"mode":"none","button":null,"target_output":false}},
{"min_skill":30.0,"max_skill":50.0,"mode":"craft","label":"Arrows / Bolts","recipe_ids":["arrow","crossbow_bolt"],"disposal":{"mode":"recycle","button":77,"target_output":true}},
{"min_skill":50.0,"max_skill":60.0,"mode":"craft","label":"Bows","recipe_ids":["bow"],"disposal":{"mode":"recycle","button":77,"target_output":true}},
{"min_skill":60.0,"max_skill":80.0,"mode":"craft","label":"Crossbows","recipe_ids":["crossbow"],"disposal":{"mode":"recycle","button":77,"target_output":true}},
{"min_skill":80.0,"max_skill":90.0,"mode":"craft","label":"Heavy Crossbows","recipe_ids":["heavy_crossbow"],"disposal":{"mode":"recycle","button":77,"target_output":true}},
{"min_skill":90.0,"max_skill":120.0,"mode":"craft","label":"Repeating Crossbows","recipe_ids":["repeating_crossbow"],"disposal":{"mode":"recycle","button":77,"target_output":true}}
],"recipes":{
"arrow":{"name":"Arrow","min_skill":0.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"shaft","name":"Shaft","amount":1,"item_id":7124,"hue":0,"names":["Shaft","shafts"],"shelf_page":2,"shelf_button":32,"reagent_actions":[]},{"key":"feather","name":"Feather","amount":1,"item_id":7121,"hue":0,"names":["Feather","Feathers"],"shelf_page":2,"shelf_button":33,"reagent_actions":[]}],"actions":[15,2],"output_ids":[],"output_names":["Arrow"],"output_hue":-1,"output_amount":1},
"crossbow_bolt":{"name":"Crossbow Bolt","min_skill":0.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"shaft","name":"Shaft","amount":1,"item_id":7124,"hue":0,"names":["Shaft","shafts"],"shelf_page":2,"shelf_button":32,"reagent_actions":[]},{"key":"feather","name":"Feather","amount":1,"item_id":7121,"hue":0,"names":["Feather","Feathers"],"shelf_page":2,"shelf_button":33,"reagent_actions":[]}],"actions":[15,9],"output_ids":[],"output_names":["Crossbow Bolt"],"output_hue":-1,"output_amount":1},
"bow":{"name":"Bow","min_skill":30.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"plain_board","name":"Wood","amount":7,"item_id":7127,"hue":0,"names":["Wood","Log","Logs","Board","Boards","Plain Board","Plain Boards","Boards or Logs"],"shelf_page":1,"shelf_button":11,"reagent_actions":[]}],"actions":[7,6,22,2],"output_ids":[],"output_names":["Bow"],"output_hue":-1,"output_amount":1},
"crossbow":{"name":"Crossbow","min_skill":60.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"plain_board","name":"Wood","amount":7,"item_id":7127,"hue":0,"names":["Wood","Log","Logs","Board","Boards","Plain Board","Plain Boards","Boards or Logs"],"shelf_page":1,"shelf_button":11,"reagent_actions":[]}],"actions":[7,6,22,9],"output_ids":[],"output_names":["Crossbow"],"output_hue":-1,"output_amount":1},
"heavy_crossbow":{"name":"Heavy Crossbow","min_skill":70.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"plain_board","name":"Wood","amount":10,"item_id":7127,"hue":0,"names":["Wood","Log","Logs","Board","Boards","Plain Board","Plain Boards","Boards or Logs"],"shelf_page":1,"shelf_button":11,"reagent_actions":[]}],"actions":[7,6,22,16],"output_ids":[],"output_names":["Heavy Crossbow"],"output_hue":-1,"output_amount":1},
"repeating_crossbow":{"name":"Repeating Crossbow","min_skill":90.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"plain_board","name":"Wood","amount":10,"item_id":7127,"hue":0,"names":["Wood","Log","Logs","Board","Boards","Plain Board","Plain Boards","Boards or Logs"],"shelf_page":1,"shelf_button":11,"reagent_actions":[]}],"actions":[7,6,22,30],"output_ids":[],"output_names":["Repeating Crossbow"],"output_hue":-1,"output_amount":1}
}},
{
"id":"inscription",
"name":"Inscription",
"skill_name":"Inscription",
"goal":100.0,
"informational":false,
"message":"",
"gump_id":949095101,
"tool":{"name":"Scribe's Pen","item_ids":[4031],"names":["Scribe's Pen","Scribe Pen","Inscription Tool"],"book_button":9},
"stages":[
{"min_skill":0.0,"max_skill":30.0,"mode":"npc_train","label":"NPC Train","recipe_ids":[],"disposal":{"mode":"none","button":null,"target_output":false}},
{"min_skill":30.0,"max_skill":50.0,"mode":"craft","label":"1st / 2nd Circle Scrolls","recipe_ids":["clumsy","feeblemind","agility","heal"],"disposal":{"mode":"save","button":77,"target_output":true}},
{"min_skill":50.0,"max_skill":65.0,"mode":"craft","label":"3rd Circle Scrolls","recipe_ids":["fireball","teleport"],"disposal":{"mode":"save","button":77,"target_output":true}},
{"min_skill":65.0,"max_skill":75.0,"mode":"craft","label":"4th Circle Scrolls","recipe_ids":["recall","greater_heal","lightning"],"disposal":{"mode":"save","button":77,"target_output":true}},
{"min_skill":75.0,"max_skill":85.0,"mode":"craft","label":"5th Circle Scrolls","recipe_ids":["magic_reflection","mind_blast"],"disposal":{"mode":"save","button":77,"target_output":true}},
{"min_skill":85.0,"max_skill":95.0,"mode":"craft","label":"6th Circle Scrolls","recipe_ids":["mark","reveal"],"disposal":{"mode":"save","button":77,"target_output":true}},
{"min_skill":95.0,"max_skill":100.0,"mode":"craft","label":"7th / 8th Circle Scrolls","recipe_ids":["gate_travel","flamestrike","resurrection"],"disposal":{"mode":"save","button":77,"target_output":true}}
],"recipes":{
"clumsy":{"name":"Clumsy","min_skill":0.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"blank_scroll","name":"Blank Scroll","amount":1,"item_id":3827,"hue":null,"names":["Blank Scroll","Blank Scrolls"],"shelf_page":2,"shelf_button":40,"reagent_actions":[]},{"key":"bloodmoss","name":"Bloodmoss","amount":1,"item_id":3963,"hue":null,"names":["Bloodmoss","Blood Moss"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,2]},{"key":"nightshade","name":"Nightshade","amount":1,"item_id":5009,"hue":null,"names":["Nightshade"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,5]}],"actions":[1,9],"output_ids":[7982],"output_names":["Clumsy"],"output_hue":-1,"output_amount":1},
"feeblemind":{"name":"Feeblemind","min_skill":0.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"blank_scroll","name":"Blank Scroll","amount":1,"item_id":3827,"hue":null,"names":["Blank Scroll","Blank Scrolls"],"shelf_page":2,"shelf_button":40,"reagent_actions":[]},{"key":"nightshade","name":"Nightshade","amount":1,"item_id":5009,"hue":null,"names":["Nightshade"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,5]},{"key":"ginseng","name":"Ginseng","amount":1,"item_id":3973,"hue":null,"names":["Ginseng"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,8]}],"actions":[1,23],"output_ids":[7984],"output_names":["Feeblemind"],"output_hue":-1,"output_amount":1},
"heal":{"name":"Heal","min_skill":0.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"blank_scroll","name":"Blank Scroll","amount":1,"item_id":3827,"hue":null,"names":["Blank Scroll","Blank Scrolls"],"shelf_page":2,"shelf_button":40,"reagent_actions":[]},{"key":"garlic","name":"Garlic","amount":1,"item_id":5006,"hue":null,"names":["Garlic"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,7]},{"key":"ginseng","name":"Ginseng","amount":1,"item_id":3973,"hue":null,"names":["Ginseng"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,8]},{"key":"spiders_silk","name":"Spiders Silk","amount":1,"item_id":5005,"hue":null,"names":["Spiders Silk","Spiders' Silk","Spider's Silk"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,4]}],"actions":[1,30],"output_ids":[7985],"output_names":["Heal"],"output_hue":-1,"output_amount":1},
"agility":{"name":"Agility","min_skill":0.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"blank_scroll","name":"Blank Scroll","amount":1,"item_id":3827,"hue":null,"names":["Blank Scroll","Blank Scrolls"],"shelf_page":2,"shelf_button":40,"reagent_actions":[]},{"key":"bloodmoss","name":"Bloodmoss","amount":1,"item_id":3963,"hue":null,"names":["Bloodmoss","Blood Moss"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,2]},{"key":"mandrake_root","name":"Mandrake Root","amount":1,"item_id":3974,"hue":null,"names":["Mandrake Root","Mandrake"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,3]}],"actions":[1,58],"output_ids":[7989],"output_names":["Agility"],"output_hue":-1,"output_amount":1},
"fireball":{"name":"Fireball","min_skill":3.5,"enabled":true,"skill_requirements":[],"resources":[{"key":"black_pearl","name":"Black Pearl","amount":1,"item_id":5002,"hue":null,"names":["Black Pearl"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,1]},{"key":"blank_scroll","name":"Blank Scroll","amount":1,"item_id":3827,"hue":null,"names":["Blank Scroll","Blank Scrolls"],"shelf_page":2,"shelf_button":40,"reagent_actions":[]}],"actions":[8,9],"output_ids":[7998],"output_names":["Fireball"],"output_hue":-1,"output_amount":1},
"teleport":{"name":"Teleport","min_skill":3.5,"enabled":true,"skill_requirements":[],"resources":[{"key":"blank_scroll","name":"Blank Scroll","amount":1,"item_id":3827,"hue":null,"names":["Blank Scroll","Blank Scrolls"],"shelf_page":2,"shelf_button":40,"reagent_actions":[]},{"key":"bloodmoss","name":"Bloodmoss","amount":1,"item_id":3963,"hue":null,"names":["Bloodmoss","Blood Moss"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,2]},{"key":"mandrake_root","name":"Mandrake Root","amount":1,"item_id":3974,"hue":null,"names":["Mandrake Root","Mandrake"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,3]}],"actions":[8,37],"output_ids":[8002],"output_names":["Teleport"],"output_hue":-1,"output_amount":1},
"greater_heal":{"name":"Greater Heal","min_skill":17.6,"enabled":true,"skill_requirements":[],"resources":[{"key":"blank_scroll","name":"Blank Scroll","amount":1,"item_id":3827,"hue":null,"names":["Blank Scroll","Blank Scrolls"],"shelf_page":2,"shelf_button":40,"reagent_actions":[]},{"key":"garlic","name":"Garlic","amount":1,"item_id":5006,"hue":null,"names":["Garlic"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,7]},{"key":"ginseng","name":"Ginseng","amount":1,"item_id":3973,"hue":null,"names":["Ginseng"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,8]},{"key":"mandrake_root","name":"Mandrake Root","amount":1,"item_id":3974,"hue":null,"names":["Mandrake Root","Mandrake"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,3]},{"key":"spiders_silk","name":"Spiders Silk","amount":1,"item_id":5005,"hue":null,"names":["Spiders Silk","Spiders' Silk","Spider's Silk"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,4]}],"actions":[8,86],"output_ids":[8009],"output_names":["Greater Heal"],"output_hue":-1,"output_amount":1},
"lightning":{"name":"Lightning","min_skill":17.6,"enabled":true,"skill_requirements":[],"resources":[{"key":"blank_scroll","name":"Blank Scroll","amount":1,"item_id":3827,"hue":null,"names":["Blank Scroll","Blank Scrolls"],"shelf_page":2,"shelf_button":40,"reagent_actions":[]},{"key":"mandrake_root","name":"Mandrake Root","amount":1,"item_id":3974,"hue":null,"names":["Mandrake Root","Mandrake"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,3]},{"key":"sulfurous_ash","name":"Sulfurous Ash","amount":1,"item_id":3980,"hue":null,"names":["Sulfurous Ash","Sulfuroush Ash","1 Sulferous Ash","Sulferous Ash"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,6]}],"actions":[8,93],"output_ids":[8010],"output_names":["Lightning"],"output_hue":-1,"output_amount":1},
"recall":{"name":"Recall","min_skill":17.6,"enabled":true,"skill_requirements":[],"resources":[{"key":"blank_scroll","name":"Blank Scroll","amount":1,"item_id":3827,"hue":null,"names":["Blank Scroll","Blank Scrolls"],"shelf_page":2,"shelf_button":40,"reagent_actions":[]},{"key":"black_pearl","name":"Black Pearl","amount":1,"item_id":5002,"hue":null,"names":["Black Pearl"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,1]},{"key":"bloodmoss","name":"Bloodmoss","amount":1,"item_id":3963,"hue":null,"names":["Bloodmoss","Blood Moss"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,2]},{"key":"mandrake_root","name":"Mandrake Root","amount":1,"item_id":3974,"hue":null,"names":["Mandrake Root","Mandrake"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,3]}],"actions":[8,107],"output_ids":[8012],"output_names":["Recall"],"output_hue":-1,"output_amount":1},
"magic_reflection":{"name":"Magic Reflection","min_skill":32.1,"enabled":true,"skill_requirements":[],"resources":[{"key":"blank_scroll","name":"Blank Scroll","amount":1,"item_id":3827,"hue":null,"names":["Blank Scroll","Blank Scrolls"],"shelf_page":2,"shelf_button":40,"reagent_actions":[]},{"key":"garlic","name":"Garlic","amount":1,"item_id":5006,"hue":null,"names":["Garlic"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,7]},{"key":"mandrake_root","name":"Mandrake Root","amount":1,"item_id":3974,"hue":null,"names":["Mandrake Root","Mandrake"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,3]},{"key":"spiders_silk","name":"Spiders Silk","amount":1,"item_id":5005,"hue":null,"names":["Spiders Silk","Spiders' Silk","Spider's Silk"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,4]}],"actions":[15,23],"output_ids":[8016],"output_names":["Magic Reflection"],"output_hue":-1,"output_amount":1},
"mind_blast":{"name":"Mind Blast","min_skill":32.1,"enabled":true,"skill_requirements":[],"resources":[{"key":"blank_scroll","name":"Blank Scroll","amount":1,"item_id":3827,"hue":null,"names":["Blank Scroll","Blank Scrolls"],"shelf_page":2,"shelf_button":40,"reagent_actions":[]},{"key":"black_pearl","name":"Black Pearl","amount":1,"item_id":5002,"hue":null,"names":["Black Pearl"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,1]},{"key":"mandrake_root","name":"Mandrake Root","amount":1,"item_id":3974,"hue":null,"names":["Mandrake Root","Mandrake"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,3]},{"key":"nightshade","name":"Nightshade","amount":1,"item_id":5009,"hue":null,"names":["Nightshade"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,5]},{"key":"sulfurous_ash","name":"Sulfurous Ash","amount":1,"item_id":3980,"hue":null,"names":["Sulfurous Ash","Sulfuroush Ash","1 Sulferous Ash","Sulferous Ash"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,6]}],"actions":[15,30],"output_ids":[8017],"output_names":["Mind Blast"],"output_hue":-1,"output_amount":1},
"mark":{"name":"Mark","min_skill":46.4,"enabled":true,"skill_requirements":[],"resources":[{"key":"blank_scroll","name":"Blank Scroll","amount":1,"item_id":3827,"hue":null,"names":["Blank Scroll","Blank Scrolls"],"shelf_page":2,"shelf_button":40,"reagent_actions":[]},{"key":"black_pearl","name":"Black Pearl","amount":1,"item_id":5002,"hue":null,"names":["Black Pearl"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,1]},{"key":"bloodmoss","name":"Bloodmoss","amount":1,"item_id":3963,"hue":null,"names":["Bloodmoss","Blood Moss"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,2]},{"key":"mandrake_root","name":"Mandrake Root","amount":1,"item_id":3974,"hue":null,"names":["Mandrake Root","Mandrake"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,3]}],"actions":[15,86],"output_ids":[8025],"output_names":["Mark"],"output_hue":-1,"output_amount":1},
"reveal":{"name":"Reveal","min_skill":46.4,"enabled":true,"skill_requirements":[],"resources":[{"key":"blank_scroll","name":"Blank Scroll","amount":1,"item_id":3827,"hue":null,"names":["Blank Scroll","Blank Scrolls"],"shelf_page":2,"shelf_button":40,"reagent_actions":[]},{"key":"bloodmoss","name":"Bloodmoss","amount":1,"item_id":3963,"hue":null,"names":["Bloodmoss","Blood Moss"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,2]},{"key":"sulfurous_ash","name":"Sulfurous Ash","amount":1,"item_id":3980,"hue":null,"names":["Sulfurous Ash","Sulfuroush Ash","1 Sulferous Ash","Sulferous Ash"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,6]}],"actions":[15,107],"output_ids":[8028],"output_names":["Reveal"],"output_hue":-1,"output_amount":1},
"flamestrike":{"name":"Flamestrike","min_skill":60.7,"enabled":true,"skill_requirements":[],"resources":[{"key":"blank_scroll","name":"Blank Scroll","amount":1,"item_id":3827,"hue":null,"names":["Blank Scroll","Blank Scrolls"],"shelf_page":2,"shelf_button":40,"reagent_actions":[]},{"key":"spiders_silk","name":"Spiders Silk","amount":1,"item_id":5005,"hue":null,"names":["Spiders Silk","Spiders' Silk","Spider's Silk"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,4]},{"key":"sulfurous_ash","name":"Sulfurous Ash","amount":1,"item_id":3980,"hue":null,"names":["Sulfurous Ash","Sulfuroush Ash","1 Sulferous Ash","Sulferous Ash"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,6]}],"actions":[22,16],"output_ids":[8031],"output_names":["Flamestrike"],"output_hue":-1,"output_amount":1},
"gate_travel":{"name":"Gate Travel","min_skill":60.7,"enabled":true,"skill_requirements":[],"resources":[{"key":"blank_scroll","name":"Blank Scroll","amount":1,"item_id":3827,"hue":null,"names":["Blank Scroll","Blank Scrolls"],"shelf_page":2,"shelf_button":40,"reagent_actions":[]},{"key":"black_pearl","name":"Black Pearl","amount":1,"item_id":5002,"hue":null,"names":["Black Pearl"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,1]},{"key":"mandrake_root","name":"Mandrake Root","amount":1,"item_id":3974,"hue":null,"names":["Mandrake Root","Mandrake"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,3]},{"key":"sulfurous_ash","name":"Sulfurous Ash","amount":1,"item_id":3980,"hue":null,"names":["Sulfurous Ash","Sulfuroush Ash","1 Sulferous Ash","Sulferous Ash"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,6]}],"actions":[22,23],"output_ids":[8032],"output_names":["Gate Travel"],"output_hue":-1,"output_amount":1},
"resurrection":{"name":"Resurrection","min_skill":75.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"blank_scroll","name":"Blank Scroll","amount":1,"item_id":3827,"hue":null,"names":["Blank Scroll","Blank Scrolls"],"shelf_page":2,"shelf_button":40,"reagent_actions":[]},{"key":"bloodmoss","name":"Bloodmoss","amount":1,"item_id":3963,"hue":null,"names":["Bloodmoss","Blood Moss"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,2]},{"key":"ginseng","name":"Ginseng","amount":1,"item_id":3973,"hue":null,"names":["Ginseng"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,8]},{"key":"garlic","name":"Garlic","amount":1,"item_id":5006,"hue":null,"names":["Garlic"],"shelf_page":null,"shelf_button":null,"reagent_actions":[3577,7]}],"actions":[22,72],"output_ids":[8039],"output_names":["Resurrection"],"output_hue":-1,"output_amount":1}
}},
{
"id":"tailoring",
"name":"Tailoring",
"skill_name":"Tailoring",
"goal":120.0,
"informational":false,
"message":"",
"gump_id":949095101,
"tool":{"name":"Sewing Kit","item_ids":[],"names":["Sewing Kit","Tailoring Tool"],"book_button":3},
"stages":[
{"min_skill":0.0,"max_skill":30.0,"mode":"npc_train","label":"NPC Train","recipe_ids":[],"disposal":{"mode":"none","button":null,"target_output":false}},
{"min_skill":30.0,"max_skill":50.0,"mode":"craft","label":"Short Pants / Cloaks","recipe_ids":["short_pants","cloak"],"disposal":{"mode":"recycle","button":77,"target_output":true}},
{"min_skill":50.0,"max_skill":53.9,"mode":"craft","label":"Thigh Boots","recipe_ids":["thigh_boots"],"disposal":{"mode":"recycle","button":77,"target_output":true}},
{"min_skill":53.9,"max_skill":74.6,"mode":"craft","label":"Robes","recipe_ids":["robe"],"disposal":{"mode":"recycle","button":77,"target_output":true}},
{"min_skill":74.6,"max_skill":99.6,"mode":"craft","label":"Oil Cloth","recipe_ids":["oil_cloth"],"disposal":{"mode":"trash","button":null,"target_output":false}},
{"min_skill":99.6,"max_skill":100.0,"mode":"craft","label":"Studded Gorget","recipe_ids":["studded_gorget"],"disposal":{"mode":"recycle","button":77,"target_output":true}},
{"min_skill":100.0,"max_skill":103.1,"mode":"craft","label":"Studded Sleeves","recipe_ids":["studded_sleeves","studded_armor"],"disposal":{"mode":"recycle","button":77,"target_output":true}},
{"min_skill":103.1,"max_skill":110.0,"mode":"craft","label":"Studded Tunic","recipe_ids":["studded_tunic"],"disposal":{"mode":"recycle","button":77,"target_output":true}},
{"min_skill":110.0,"max_skill":120.0,"mode":"craft","label":"Bone Armor","recipe_ids":["bone_armor","bone_leggings"],"disposal":{"mode":"recycle","button":77,"target_output":true}}
],"recipes":{
"cloak":{"name":"Cloak","min_skill":41.4,"enabled":true,"skill_requirements":[],"resources":[{"key":"cloth","name":"Cloth","amount":14,"item_id":5990,"hue":null,"names":["Cloth"],"shelf_page":3,"shelf_button":48,"reagent_actions":[]}],"actions":[29,44],"output_ids":[],"output_names":["Cloak"],"output_hue":-1,"output_amount":1},
"robe":{"name":"Robe","min_skill":53.9,"enabled":true,"skill_requirements":[],"resources":[{"key":"cloth","name":"Cloth","amount":14,"item_id":5990,"hue":null,"names":["Cloth"],"shelf_page":3,"shelf_button":48,"reagent_actions":[]}],"actions":[29,51],"output_ids":[],"output_names":["Robe"],"output_hue":-1,"output_amount":1},
"short_pants":{"name":"Short Pants","min_skill":24.8,"enabled":true,"skill_requirements":[],"resources":[{"key":"cloth","name":"Cloth","amount":6,"item_id":5990,"hue":null,"names":["Cloth"],"shelf_page":3,"shelf_button":48,"reagent_actions":[]}],"actions":[29,86],"output_ids":[],"output_names":["Short Pants"],"output_hue":-1,"output_amount":1},
"oil_cloth":{"name":"Oil Cloth","min_skill":74.6,"enabled":true,"skill_requirements":[],"resources":[{"key":"cloth","name":"Cloth","amount":1,"item_id":5990,"hue":null,"names":["Cloth"],"shelf_page":3,"shelf_button":48,"reagent_actions":[]}],"actions":[36,2],"output_ids":[],"output_names":["Oil Cloth"],"output_hue":-1,"output_amount":1},
"thigh_boots":{"name":"Thigh Boots","min_skill":41.4,"enabled":true,"skill_requirements":[],"resources":[{"key":"cloth","name":"Cloth","amount":10,"item_id":5990,"hue":null,"names":["Cloth"],"shelf_page":3,"shelf_button":48,"reagent_actions":[]}],"actions":[43,23],"output_ids":[],"output_names":["Thigh Boots"],"output_hue":-1,"output_amount":1},
"studded_gorget":{"name":"Studded Gorget","min_skill":78.8,"enabled":true,"skill_requirements":[],"resources":[{"key":"normal_leather","name":"Leather","amount":6,"item_id":4225,"hue":0,"names":["Leather","Hide","Hides","Normal Leather"],"shelf_page":1,"shelf_button":18,"reagent_actions":[]}],"actions":[7,6,105,57,9],"output_ids":[],"output_names":["Studded Gorget"],"output_hue":-1,"output_amount":1},
"studded_sleeves":{"name":"Studded Sleeves","min_skill":87.1,"enabled":true,"skill_requirements":[],"resources":[{"key":"normal_leather","name":"Leather","amount":10,"item_id":4225,"hue":0,"names":["Leather","Hide","Hides","Normal Leather"],"shelf_page":1,"shelf_button":18,"reagent_actions":[]}],"actions":[7,6,105,57,23],"output_ids":[],"output_names":["Studded Sleeves"],"output_hue":-1,"output_amount":1},
"studded_tunic":{"name":"Studded Tunic","min_skill":94.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"normal_leather","name":"Leather","amount":14,"item_id":4225,"hue":0,"names":["Leather","Hide","Hides","Normal Leather"],"shelf_page":1,"shelf_button":18,"reagent_actions":[]}],"actions":[7,6,105,57,37],"output_ids":[],"output_names":["Studded Tunic"],"output_hue":-1,"output_amount":1},
"studded_armor":{"name":"Studded Armor","min_skill":87.1,"enabled":true,"skill_requirements":[],"resources":[{"key":"normal_leather","name":"Leather","amount":10,"item_id":4225,"hue":0,"names":["Leather","Hide","Hides","Normal Leather"],"shelf_page":1,"shelf_button":18,"reagent_actions":[]}],"actions":[7,6,105,64,37],"output_ids":[],"output_names":["Studded Armor"],"output_hue":-1,"output_amount":1},
"bone_leggings":{"name":"Bone Leggings","min_skill":95.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"normal_leather","name":"Leather","amount":10,"item_id":4225,"hue":0,"names":["Leather","Hide","Hides","Normal Leather"],"shelf_page":1,"shelf_button":18,"reagent_actions":[]},{"key":"bone","name":"Bone","amount":6,"item_id":3966,"hue":null,"names":["Bone","Bones"],"shelf_page":3,"shelf_button":47,"reagent_actions":[]}],"actions":[7,6,105,71,23],"output_ids":[],"output_names":["Bone Leggings"],"output_hue":-1,"output_amount":1},
"bone_armor":{"name":"Bone Armor","min_skill":96.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"normal_leather","name":"Leather","amount":12,"item_id":4225,"hue":0,"names":["Leather","Hide","Hides","Normal Leather"],"shelf_page":1,"shelf_button":18,"reagent_actions":[]},{"key":"bone","name":"Bone","amount":10,"item_id":3966,"hue":null,"names":["Bone","Bones"],"shelf_page":3,"shelf_button":47,"reagent_actions":[]}],"actions":[7,6,105,71,30],"output_ids":[],"output_names":["Bone Armor"],"output_hue":-1,"output_amount":1}
}},
{
"id":"tinkering",
"name":"Tinkering",
"skill_name":"Tinkering",
"goal":120.0,
"informational":false,
"message":"",
"gump_id":949095101,
"tool":{"name":"Tinker's Tools","item_ids":[7864],"names":["Tinker's Tools","Tinker Tools","Tinkering Tool"],"book_button":10},
"stages":[
{"min_skill":0.0,"max_skill":27.5,"mode":"npc_train","label":"NPC Train","recipe_ids":[],"disposal":{"mode":"none","button":null,"target_output":false}},
{"min_skill":27.5,"max_skill":45.0,"mode":"craft","label":"Scissors","recipe_ids":["scissors"],"disposal":{"mode":"trash","button":null,"target_output":false}},
{"min_skill":45.0,"max_skill":60.2,"mode":"craft","label":"Hammers","recipe_ids":["hammer"],"disposal":{"mode":"trash","button":null,"target_output":false}},
{"min_skill":60.2,"max_skill":92.5,"mode":"craft","label":"Lockpicks","recipe_ids":["lockpick"],"disposal":{"mode":"save","button":null,"target_output":false}},
{"min_skill":92.5,"max_skill":100.0,"mode":"craft","label":"Candelabras","recipe_ids":["candelabra"],"disposal":{"mode":"trash","button":null,"target_output":false}},
{"min_skill":100.0,"max_skill":105.0,"mode":"craft","label":"Scales / Spyglasses","recipe_ids":["scales","spyglass"],"disposal":{"mode":"trash","button":null,"target_output":false}},
{"min_skill":105.0,"max_skill":120.0,"mode":"craft","label":"Braziers","recipe_ids":["brazier"],"disposal":{"mode":"trash","button":null,"target_output":false}}
],"recipes":{
"scissors":{"name":"Scissors","min_skill":5.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"iron_ingot","name":"Iron","amount":2,"item_id":7154,"hue":0,"names":["Iron","Ingot","Ingots","Iron Ingot","Iron Ingots"],"shelf_page":1,"shelf_button":1,"reagent_actions":[]}],"actions":[7,6,43,2],"output_ids":[],"output_names":["Scissors"],"output_hue":-1,"output_amount":1},
"hammer":{"name":"Hammer","min_skill":30.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"iron_ingot","name":"Iron","amount":1,"item_id":7154,"hue":0,"names":["Iron","Ingot","Ingots","Iron Ingot","Iron Ingots"],"shelf_page":1,"shelf_button":1,"reagent_actions":[]}],"actions":[7,6,43,79],"output_ids":["0x102A"],"output_names":["Hammer"],"output_hue":-1,"output_amount":1},
"lockpick":{"name":"Lockpick","min_skill":45.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"iron_ingot","name":"Iron","amount":1,"item_id":7154,"hue":0,"names":["Iron","Ingot","Ingots","Iron Ingot","Iron Ingots"],"shelf_page":1,"shelf_button":1,"reagent_actions":[]}],"actions":[7,6,43,121],"output_ids":[],"output_names":["Lockpick"],"output_hue":-1,"output_amount":1},
"scales":{"name":"Scales","min_skill":60.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"iron_ingot","name":"Iron","amount":4,"item_id":7154,"hue":0,"names":["Iron","Ingot","Ingots","Iron Ingot","Iron Ingots"],"shelf_page":1,"shelf_button":1,"reagent_actions":[]}],"actions":[7,6,105,57,9],"output_ids":[],"output_names":["Scales"],"output_hue":-1,"output_amount":1},
"spyglass":{"name":"Spyglass","min_skill":60.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"iron_ingot","name":"Iron","amount":4,"item_id":7154,"hue":0,"names":["Iron","Ingot","Ingots","Iron Ingot","Iron Ingots"],"shelf_page":1,"shelf_button":1,"reagent_actions":[]}],"actions":[7,6,105,57,30],"output_ids":[],"output_names":["Spyglass"],"output_hue":-1,"output_amount":1},
"candelabra":{"name":"Candelabra","min_skill":75.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"iron_ingot","name":"Iron","amount":4,"item_id":7154,"hue":0,"names":["Iron","Ingot","Ingots","Iron Ingot","Iron Ingots"],"shelf_page":1,"shelf_button":1,"reagent_actions":[]}],"actions":[7,6,105,64,9],"output_ids":[],"output_names":["Candelabra"],"output_hue":-1,"output_amount":1},
"brazier":{"name":"Brazier","min_skill":100.0,"enabled":true,"skill_requirements":[],"resources":[{"key":"iron_ingot","name":"Iron","amount":35,"item_id":7154,"hue":0,"names":["Iron","Ingot","Ingots","Iron Ingot","Iron Ingots"],"shelf_page":1,"shelf_button":1,"reagent_actions":[]}],"actions":[7,6,105,64,16],"output_ids":[],"output_names":["Brazier"],"output_hue":-1,"output_amount":1}
}}
],
"resource_shelf_gump":111922706,
"resource_shelf_item":29180,
"resource_shelf_next_button":123,
"reagent_shelf_gump":2834126535
}''')
SKILLS = TRAINING_DATA["skills"]

BTN_CLOSE = 9000
BTN_HOME = 9001
BTN_TOGGLE = 9002
BTN_SOURCE = 9003
BTN_CHEST = 9010
BTN_RESOURCE_SHELF = 9011
BTN_REAGENT_SHELF = 9012
BTN_OUTPUT = 9013
BTN_TOOL_BOOK = 9014
BTN_TRASH = 9015
BTN_SKILL_BASE = 10000


# ===========================================================
# STATE / SETTINGS LOADER
# ===========================================================

_running = True
_training = False
_dirty = True
_view = "home"
_selected = 0
_status = "Ready."
_status_hue = LABEL_HUE
_step = "Idle"
_crafts = 0
_start_skill = 0.0
_failures = 0
_pending = []
_pending_disposal = {}
_clicked = False
_settings_path = ""
_settings_serial = 0
_settings_source = ""
_settings_blocked = False
_settings_warning = False
_source_mode = "shelf"
_resource_chest = 0
_resource_shelf = 0
_reagent_shelf = 0
_output_chest = 0
_tool_book = 0
_trash_container = 0


def status(message, hue=LABEL_HUE, step=None):
    global _status, _status_hue, _step, _dirty
    value = str(message)
    if value != _status or int(hue) != _status_hue or (step is not None and step != _step):
        _status = value
        _status_hue = int(hue)
        if step is not None:
            _step = str(step)
        _dirty = True


def short(value, limit):
    value = str(value or "")
    return value if len(value) <= limit else value[:limit - 3] + "..."


def item(serial):
    if not serial or int(serial) <= 0:
        return None
    try:
        return Items.FindBySerial(int(serial))
    except:
        return None


def label(serial, empty):
    found = item(serial)
    if not found:
        return empty
    try:
        return str(found.Name or "0x{0:X}".format(int(serial)))
    except:
        return "0x{0:X}".format(int(serial))


def script_directory():
    if TRAINER_DIRECTORY_OVERRIDE:
        return Path.GetFullPath(TRAINER_DIRECTORY_OVERRIDE)
    try:
        return Path.GetDirectoryName(Path.GetFullPath(str(__file__)))
    except:
        pass
    current = Misc.CurrentScriptDirectory()
    candidates = (current, Path.Combine(current, "FrogCraftingTrainer"), Path.Combine(current, "In Development", "FrogCraftingTrainer"))
    for candidate in candidates:
        if File.Exists(Path.Combine(candidate, "FrogCraftingTrainer.py")):
            return candidate
    return current


def settings_identities():
    candidates = []
    try:
        serial = int(Player.Serial) & 0xFFFFFFFF
        if serial:
            candidates.append(("player", serial))
    except:
        pass
    try:
        serial = int(Player.Backpack.Serial) & 0xFFFFFFFF
        if serial and not any(value == serial for _source, value in candidates):
            candidates.append(("backpack", serial))
    except:
        pass
    return candidates


def settings_values():
    return {
        "source_mode": _source_mode,
        "resource_chest": _resource_chest,
        "resource_shelf": _resource_shelf,
        "reagent_shelf": _reagent_shelf,
        "output_chest": _output_chest,
        "tool_book": _tool_book,
        "trash_container": _trash_container,
    }


def apply_settings(data):
    global _source_mode, _resource_chest, _resource_shelf, _reagent_shelf
    global _output_chest, _tool_book, _trash_container
    _source_mode = "chest" if str(data.get("source_mode", "shelf")) == "chest" else "shelf"
    for field in SETTINGS_FIELDS[1:]:
        try:
            value = max(0, int(data.get(field, 0)))
        except:
            value = 0
        if field == "resource_chest":
            _resource_chest = value
        elif field == "resource_shelf":
            _resource_shelf = value
        elif field == "reagent_shelf":
            _reagent_shelf = value
        elif field == "output_chest":
            _output_chest = value
        elif field == "tool_book":
            _tool_book = value
        elif field == "trash_container":
            _trash_container = value


def load_settings():
    global _settings_path, _settings_blocked, _settings_serial, _settings_source
    candidates = settings_identities()
    if not candidates:
        status("Player and backpack serial unavailable; settings cannot load.", BAD_HUE, "Settings")
        return
    base = script_directory()
    core_base = Path.Combine(Path.GetDirectoryName(base), "FrogCraftingCore", "Settings")
    source, serial = candidates[0]
    for candidate_source, candidate_serial in candidates:
        candidate_name = "character_0x{0:08X}.json".format(candidate_serial)
        if File.Exists(Path.Combine(base, "Settings", candidate_name)):
            source, serial = candidate_source, candidate_serial
            break
    else:
        for candidate_source, candidate_serial in candidates:
            candidate_name = "character_0x{0:08X}.json".format(candidate_serial)
            if File.Exists(Path.Combine(core_base, candidate_name)):
                source, serial = candidate_source, candidate_serial
                break
    _settings_serial = serial
    _settings_source = source
    name = "character_0x{0:08X}.json".format(serial)
    _settings_path = Path.Combine(base, "Settings", name)
    if File.Exists(_settings_path):
        try:
            data = json.loads(File.ReadAllText(_settings_path))
            if data.get("format") != SETTINGS_FORMAT or int(data.get("version", 0)) != 1 or int(data.get("character_serial", 0)) != serial or not isinstance(data.get("targets"), dict):
                raise Exception("format, version, character, or targets mismatch")
            apply_settings(data["targets"])
            status("Loaded trainer settings for this character.", GOOD_HUE, "Settings")
            return
        except Exception as ex:
            _settings_blocked = True
            status("Trainer settings invalid; original file preserved: " + str(ex), BAD_HUE, "Settings")
            return
    # First launch imports the player's existing FrogCraftingCore setup.
    core_path = Path.Combine(core_base, name)
    imported = False
    if File.Exists(core_path):
        try:
            core = json.loads(File.ReadAllText(core_path))
            if core.get("format") == "frog-crafting-character-settings" and int(core.get("character_serial", 0)) == serial:
                apply_settings(core.get("core") or {})
                imported = True
            else:
                raise Exception("format or character does not match")
        except Exception as ex:
            status("Core settings import failed: " + str(ex), WARN_HUE, "Settings")
            return
    if save_settings():
        status("Imported and saved FrogCraftingCore targets." if imported else "Created trainer settings for this character.", GOOD_HUE, "Settings")


def save_settings():
    global _settings_warning
    if _settings_blocked or not _settings_path:
        return False
    data = {"format": SETTINGS_FORMAT, "version": 1, "character_serial": _settings_serial, "identity_source": _settings_source, "targets": settings_values()}
    temporary = _settings_path + ".tmp"
    try:
        Directory.CreateDirectory(Path.GetDirectoryName(_settings_path))
        File.WriteAllText(temporary, json.dumps(data, indent=2, sort_keys=True) + "\n")
        if File.Exists(_settings_path):
            File.Replace(temporary, _settings_path, _settings_path + ".bak")
        else:
            File.Move(temporary, _settings_path)
        _settings_warning = False
        return True
    except Exception as ex:
        if not _settings_warning:
            status("Trainer settings could not save: " + str(ex), BAD_HUE, "Settings")
            _settings_warning = True
        return False


# ===========================================================
# TRAINING PATH / INVENTORY HELPERS
# ===========================================================

def selected_skill():
    return SKILLS[_selected]


def skill_value(skill_name):
    names = ("Bowcraft", "Bowcraft/Fletching", "Bowcraft and Fletching", "Bowcraft & Fletching") if "fletch" in skill_name.lower() or "bowcraft" in skill_name.lower() else (skill_name,)
    for name in names:
        try:
            value = float(Player.GetRealSkillValue(name))
            if value > 0 or len(names) == 1:
                return value
        except:
            pass
        try:
            value = float(Player.GetSkillValue(name))
            if value > 0 or len(names) == 1:
                return value
        except:
            pass
    return 0.0


def skill_cap(skill_name):
    names = ("Bowcraft", "Bowcraft/Fletching", "Bowcraft and Fletching", "Bowcraft & Fletching") if "fletch" in skill_name.lower() or "bowcraft" in skill_name.lower() else (skill_name,)
    for name in names:
        try:
            cap = float(Player.GetSkillCap(name))
            if cap > 0:
                return cap
        except:
            pass
    return 0.0


def training_context():
    skill = selected_skill()
    current = skill_value(skill["skill_name"])
    cap = skill_cap(skill["skill_name"])
    goal = min(float(skill["goal"]), cap) if cap > 0 else float(skill["goal"])
    if skill["informational"]:
        return current, cap, goal, None, None, skill["message"]
    if current >= goal:
        return current, cap, goal, None, None, "Training goal reached."
    for stage in skill["stages"]:
        if float(stage["min_skill"]) <= current < float(stage["max_skill"]):
            if stage["mode"] == "npc_train":
                return current, cap, goal, stage, None, "NPC train to {0:.1f}.".format(float(stage["max_skill"]))
            unavailable = []
            for recipe_id in stage["recipe_ids"]:
                recipe = skill["recipes"].get(recipe_id)
                if not recipe or not recipe["enabled"]:
                    unavailable.append(recipe_id + " unavailable")
                    continue
                if current < float(recipe["min_skill"]):
                    unavailable.append(recipe["name"] + " needs {0:.1f}".format(float(recipe["min_skill"])))
                    continue
                missing = []
                for requirement in recipe["skill_requirements"]:
                    required_name = requirement["skill_name"]
                    required_value = float(requirement["min_skill"])
                    if skill_value(required_name) < required_value:
                        missing.append("{0} {1:.1f}".format(required_name, required_value))
                if missing:
                    unavailable.append(recipe["name"] + " needs " + ", ".join(missing))
                    continue
                return current, cap, goal, stage, recipe, ""
            return current, cap, goal, stage, None, "; ".join(unavailable) or "No mapped recipe in this stage."
    return current, cap, goal, None, None, "No training stage covers this skill value."


def normalize(value):
    cleaned = []
    for char in str(value or "").strip().lower().replace("’", "'"):
        cleaned.append(char if char.isalnum() else " ")
    return " ".join("".join(cleaned).split())


def direct_items(container_serial):
    container = item(container_serial)
    if not container:
        return []
    try:
        return list(container.Contains or [])
    except:
        return []


def item_name(found):
    try:
        name = str(found.Name or "").strip()
        if name:
            return name
        Items.WaitForProps(found, 500)
        return str(found.Name or "").strip()
    except:
        return ""


def matches(found, descriptor, output=False):
    try:
        hue = descriptor.get("output_hue", -1) if output else descriptor.get("hue", -1)
        if hue is not None and int(hue) >= 0 and int(found.Hue) != int(hue):
            return False
        ids = descriptor.get("output_ids", []) if output else ([descriptor.get("item_id")] if descriptor.get("item_id") else descriptor.get("item_ids", []))
        if int(found.ItemID) in [int(str(value), 0) for value in ids if value]:
            return True
        names = descriptor.get("output_names", []) if output else descriptor.get("names", [])
        return normalize(item_name(found)) in [normalize(value) for value in names]
    except:
        return False


def count_resource(resource):
    total = 0
    for found in direct_items(Player.Backpack.Serial):
        if matches(found, resource):
            try:
                total += int(found.Amount)
            except:
                pass
    return total


def find_match(container_serial, descriptor):
    for found in direct_items(container_serial):
        if matches(found, descriptor):
            return found
    return None


def snapshot_backpack():
    result = {}
    for found in direct_items(Player.Backpack.Serial):
        try:
            result[int(found.Serial)] = int(found.Amount)
        except:
            pass
    return result


def detected_outputs(recipe, before):
    matched = []
    positive = []
    for found in direct_items(Player.Backpack.Serial):
        try:
            delta = int(found.Amount) - int(before.get(int(found.Serial), 0))
            if delta <= 0:
                continue
            record = {"serial": int(found.Serial), "amount": delta, "container": int(Player.Backpack.Serial)}
            if matches(found, recipe, True):
                matched.append(record)
            elif not any(matches(found, resource) for resource in recipe["resources"]):
                positive.append(record)
        except:
            pass
    outputs = matched if matched else (positive if len(positive) == 1 else [])
    total = sum(record["amount"] for record in outputs)
    return outputs, total


def gump_open(gump_id):
    try:
        return bool(Gumps.GetGumpData(int(gump_id)))
    except:
        return False


def close_gump(gump_id):
    try:
        Gumps.CloseGump(int(gump_id))
    except:
        pass


def open_container(serial):
    found = item(serial)
    if not found:
        return False
    try:
        Items.UseItem(found)
        Items.WaitForContents(found, 1500)
        return True
    except:
        return False


# ===========================================================
# SHELVES / TOOL STORAGE
# ===========================================================

def poll_priority():
    global _clicked, _dirty
    try:
        gd = Gumps.GetGumpData(GUMP_ID)
        button = int(getattr(gd, "buttonid", 0)) if gd else 0
    except:
        button = 0
        gd = None
    if button not in (BTN_CLOSE, BTN_HOME, BTN_TOGGLE):
        return False
    try:
        gd.buttonid = 0
    except:
        pass
    close_gump(GUMP_ID)
    handle_button(button)
    _clicked = True
    _dirty = True
    Misc.Pause(180)
    return True


def wait_for_resource(resource, old_count):
    elapsed = 0
    while elapsed < 4000:
        if poll_priority() or not _training:
            return False
        if count_resource(resource) > old_count:
            return True
        Misc.Pause(100)
        elapsed += 100
    return count_resource(resource) > old_count


def pull_from_resource_shelf(resource):
    shelf = item(_resource_shelf)
    if not shelf:
        return False, "Resource Shelf is not set or nearby."
    try:
        if int(shelf.ItemID) != int(TRAINING_DATA["resource_shelf_item"]):
            return False, "Saved Resource Shelf has the wrong item ID."
    except:
        return False, "Resource Shelf could not be checked."
    page = int(resource.get("shelf_page") or 0)
    button = int(resource.get("shelf_button") or 0)
    if page <= 0 or button <= 0:
        return False, "No Resource Shelf mapping for " + resource["name"]
    old_count = count_resource(resource)
    gump_id = int(TRAINING_DATA["resource_shelf_gump"])
    close_gump(gump_id)
    Items.UseItem(shelf)
    Gumps.WaitForGump(gump_id, SERVER_WAIT_MS)
    if poll_priority() or not _training:
        return False, "Paused during shelf navigation."
    if not gump_open(gump_id):
        return False, "Resource Shelf gump did not open."
    for _index in range(1, page):
        Gumps.SendAction(gump_id, int(TRAINING_DATA["resource_shelf_next_button"]))
        Gumps.WaitForGump(gump_id, SERVER_WAIT_MS)
        if poll_priority() or not _training:
            return False, "Paused during shelf navigation."
        if not gump_open(gump_id):
            return False, "Resource Shelf page did not open."
    Gumps.SendAction(gump_id, button)
    Gumps.WaitForGump(gump_id, SERVER_WAIT_MS)
    close_gump(gump_id)
    if wait_for_resource(resource, old_count):
        return True, "Withdrew " + resource["name"] + " from Resource Shelf."
    return False, "No {0} arrived; check shelf stock and locked amount {1}.".format(resource["name"], SHELF_WITHDRAW_AMOUNT)


def pull_from_reagent_shelf(resource):
    shelf = item(_reagent_shelf)
    if not shelf:
        return False, "Reagent/Gem Shelf is not set or nearby."
    actions = resource.get("reagent_actions") or []
    if not actions:
        return False, "No Reagent/Gem Shelf mapping for " + resource["name"]
    old_count = count_resource(resource)
    gump_id = int(TRAINING_DATA["reagent_shelf_gump"])
    close_gump(gump_id)
    Items.UseItem(shelf)
    Gumps.WaitForGump(gump_id, SERVER_WAIT_MS)
    if poll_priority() or not _training:
        return False, "Paused during reagent shelf navigation."
    if not gump_open(gump_id):
        return False, "Reagent/Gem Shelf gump did not open."
    for index, action in enumerate(actions):
        Gumps.SendAction(gump_id, int(action))
        Gumps.WaitForGump(gump_id, SERVER_WAIT_MS)
        if poll_priority() or not _training:
            return False, "Paused during reagent shelf navigation."
        if index < len(actions) - 1 and not gump_open(gump_id):
            return False, "Reagent/Gem Shelf page did not open."
    close_gump(gump_id)
    if wait_for_resource(resource, old_count):
        return True, "Withdrew " + resource["name"] + " from Reagent/Gem Shelf."
    return False, "No {0} arrived; check shelf stock and locked amount {1}.".format(resource["name"], SHELF_WITHDRAW_AMOUNT)


def pull_from_chest(resource, target_count):
    chest = item(_resource_chest)
    if not chest:
        return False, "Resource chest is not set or nearby."
    open_container(chest.Serial)
    found = find_match(chest.Serial, resource)
    if not found:
        return False, "No " + resource["name"] + " in resource chest."
    old_count = count_resource(resource)
    try:
        amount = min(int(found.Amount), max(1, int(target_count) - old_count))
        Items.Move(found, Player.Backpack.Serial, amount)
        Misc.Pause(MOVE_WAIT_MS)
    except Exception as ex:
        return False, "Chest move failed: " + str(ex)
    if count_resource(resource) <= old_count:
        return False, "Chest move did not deliver " + resource["name"]
    return True, "Restocked " + resource["name"] + " from chest."


def ensure_resources(recipe):
    for resource in recipe["resources"]:
        per_craft = int(resource["amount"])
        have = count_resource(resource)
        if have >= per_craft:
            continue
        target_count = per_craft * RESTOCK_CRAFTS
        errors = []
        if _source_mode == "shelf":
            if resource.get("reagent_actions") and item(_reagent_shelf):
                ok, message = pull_from_reagent_shelf(resource)
                if ok:
                    return "progress", message
                errors.append(message)
                if not _training:
                    return "paused", message
            if resource.get("shelf_page") and item(_resource_shelf):
                ok, message = pull_from_resource_shelf(resource)
                if ok:
                    return "progress", message
                errors.append(message)
                if not _training:
                    return "paused", message
        if item(_resource_chest):
            ok, message = pull_from_chest(resource, target_count)
            if ok:
                return "progress", message
            errors.append(message)
        if not errors:
            errors.append("No configured source for " + resource["name"])
        return "error", "; ".join(errors)
    return "ready", ""


def pull_tool_from_book(tool):
    book = item(_tool_book)
    button = int(tool.get("book_button") or 0)
    if not book or button <= 0:
        return False
    close_gump(TOOL_BOOK_GUMP_ID)
    Items.UseItem(book)
    Gumps.WaitForGump(TOOL_BOOK_GUMP_ID, 10000)
    if poll_priority() or not _training or not gump_open(TOOL_BOOK_GUMP_ID):
        return False
    Gumps.SendAdvancedAction(TOOL_BOOK_GUMP_ID, button, [], [0], ["50"])
    Gumps.WaitForGump(TOOL_BOOK_GUMP_ID, 10000)
    if poll_priority() or not _training or not gump_open(TOOL_BOOK_GUMP_ID):
        return False
    Gumps.SendAdvancedAction(TOOL_BOOK_GUMP_ID, 100, [], [0], [str(TOOL_BOOK_CHARGES)])
    Gumps.WaitForGump(TOOL_BOOK_GUMP_ID, 10000)
    Gumps.SendAdvancedAction(TOOL_BOOK_GUMP_ID, 0, [], [0], ["50"])
    Misc.Pause(MOVE_WAIT_MS)
    close_gump(TOOL_BOOK_GUMP_ID)
    return find_match(Player.Backpack.Serial, tool) is not None


def ensure_tool(skill):
    tool = skill["tool"]
    found = find_match(Player.Backpack.Serial, tool)
    if found:
        return "ready", found
    if item(_resource_chest):
        chest = item(_resource_chest)
        open_container(chest.Serial)
        found = find_match(chest.Serial, tool)
        if found:
            try:
                Items.Move(found, Player.Backpack.Serial, 1)
                Misc.Pause(MOVE_WAIT_MS)
                if find_match(Player.Backpack.Serial, tool):
                    return "progress", "Pulled " + tool["name"] + " from chest."
            except:
                pass
    if item(_tool_book) and pull_tool_from_book(tool):
        return "progress", "Pulled " + tool["name"] + " from Tool Storage."
    return "error", "No " + tool["name"] + "; supply one, a chest, or Tool Storage."


# ===========================================================
# CRAFT / OUTPUT CYCLE
# ===========================================================

def craft_gump(skill, tool):
    gump_id = int(skill["gump_id"])
    close_gump(gump_id)
    Misc.Pause(150)
    if poll_priority() or not _training:
        return False
    Items.UseItem(tool)
    Gumps.WaitForGump(gump_id, SERVER_WAIT_MS)
    if poll_priority() or not _training:
        return False
    return gump_open(gump_id)


def send_actions(gump_id, actions):
    for index, action in enumerate(actions):
        if poll_priority() or not _training:
            return False
        Gumps.SendAction(int(gump_id), int(action))
        Gumps.WaitForGump(int(gump_id), SERVER_WAIT_MS)
        if index < len(actions) - 1 and not gump_open(gump_id):
            return False
    return True


def journal_cursor():
    try:
        entries = Journal.GetJournalEntry(0) or []
        return entries[-1] if entries else None
    except:
        return None


def quest_consumed(cursor):
    deadline = time.time() + 2.5
    while time.time() < deadline:
        try:
            entries = Journal.GetJournalEntry(cursor) if cursor else Journal.GetJournalEntry(0)
        except:
            entries = []
        for entry in entries or []:
            text = " ".join(str(getattr(entry, "Text", "")).strip().lower().split())
            if (text.startswith("global quest progress:") and " contributed" in text) or text.startswith("weekly quest: crafted "):
                return True
        poll_priority()
        Misc.Pause(100)
    return False


def pause(message, hue=WARN_HUE):
    global _training
    _training = False
    status(message, hue, "Paused")


def fail(message):
    global _failures
    if not _training:
        return
    _failures += 1
    if _failures > MAX_FAILURE_RETRIES:
        pause(message + " Paused after {0} retries.".format(MAX_FAILURE_RETRIES), BAD_HUE)
    else:
        status(message + " Retry {0}/{1}.".format(_failures, MAX_FAILURE_RETRIES), WARN_HUE, "Retry")


def clear_failures():
    global _failures
    _failures = 0


def process_output():
    global _pending
    if not _pending:
        return
    record = _pending[0]
    found = item(record["serial"])
    if not found:
        _pending.pop(0)
        clear_failures()
        status("Crafted output is already gone; continuing.", WARN_HUE, "Output")
        return
    try:
        if int(found.Container) != int(record["container"]):
            pause("Crafted output moved; inspect it before resuming.", BAD_HUE)
            return
    except:
        pause("Crafted output location is unknown.", BAD_HUE)
        return
    mode = _pending_disposal["mode"]
    if mode == "none" or (mode == "save" and not _output_chest):
        _pending.pop(0)
        clear_failures()
        status("Kept crafted output in backpack.", GOOD_HUE, "Output")
        return
    if mode in ("save", "trash"):
        destination = item(_output_chest if mode == "save" else _trash_container)
        if not destination:
            fail("Output destination is unavailable.")
            return
        try:
            before_amount = int(found.Amount)
            Items.Move(found.Serial, destination.Serial, int(record["amount"]))
            Misc.Pause(MOVE_WAIT_MS)
            remaining = item(record["serial"])
            if remaining and int(remaining.Container) == int(record["container"]) and int(remaining.Amount) >= before_amount:
                fail("Crafted output did not move.")
                return
        except Exception as ex:
            fail("Crafted output move failed: " + str(ex))
            return
        _pending.pop(0)
        clear_failures()
        status("{0} crafted output.".format("Saved" if mode == "save" else "Trashed"), GOOD_HUE, "Output")
        return
    if mode not in ("smelt", "salvage", "recycle"):
        pause("Unsupported training output policy: " + mode, BAD_HUE)
        return

    try:
        before_amount = int(found.Amount)
        if before_amount > int(record["amount"]):
            pause("Output merged with an older stack. Handle that stack manually, then resume.", BAD_HUE)
            return
    except:
        pause("Cannot verify output stack size.", BAD_HUE)
        return
    skill = selected_skill()
    tool_state, tool_result = ensure_tool(skill)
    if tool_state == "progress":
        status(str(tool_result), GOOD_HUE, "Tool")
        return
    if tool_state != "ready":
        fail(str(tool_result))
        return
    if not craft_gump(skill, tool_result):
        fail("Disposal craft gump did not open.")
        return
    button = int(_pending_disposal.get("button") or 0)
    if button <= 0 or not send_actions(skill["gump_id"], [button]):
        fail("Disposal action failed for " + mode + ".")
        return
    if bool(_pending_disposal.get("target_output", False)):
        if not Target.WaitForTarget(TARGET_WAIT_MS, False):
            fail("No target cursor for " + mode + ".")
            return
        if poll_priority() or not _training:
            Target.Cancel()
            return
        Target.TargetExecute(found.Serial)
        Misc.Pause(RESULT_WAIT_MS)
        remaining = item(found.Serial)
        if remaining:
            try:
                if int(remaining.Container) == int(record["container"]) and int(remaining.Amount) >= before_amount:
                    fail(mode.title() + " did not consume the crafted output.")
                    return
            except:
                pass
    _pending.pop(0)
    clear_failures()
    status(mode.title() + " processed crafted output.", GOOD_HUE, "Output")


def training_step():
    global _training, _crafts, _pending, _pending_disposal
    if not _training:
        return
    if _pending:
        process_output()
        return
    skill = selected_skill()
    current, cap, goal, stage, recipe, reason = training_context()
    if current >= goal:
        _training = False
        status("Training complete: {0:.1f}/{1:.1f}.".format(current, goal), GOOD_HUE, "Complete")
        Misc.SendMessage("Frog Crafting Trainer complete.", GOOD_HUE)
        return
    if not stage or stage["mode"] != "craft" or not recipe:
        pause(reason or "No usable training recipe.", WARN_HUE)
        return
    disposal = stage["disposal"]
    if disposal["mode"] == "trash" and not item(_trash_container):
        pause("Set a nearby trash container on Home / Setup.", BAD_HUE)
        return
    if disposal["mode"] in ("smelt", "salvage", "recycle") and int(disposal.get("button") or 0) <= 0:
        pause("Training disposal button is missing.", BAD_HUE)
        return
    tool_state, tool_result = ensure_tool(skill)
    if not _training:
        return
    if tool_state == "progress":
        clear_failures()
        status(str(tool_result), GOOD_HUE, "Tool")
        return
    if tool_state != "ready":
        fail(str(tool_result))
        return
    resource_state, resource_message = ensure_resources(recipe)
    if not _training:
        return
    if resource_state == "progress":
        clear_failures()
        status(resource_message, GOOD_HUE, "Restock")
        return
    if resource_state != "ready":
        fail(resource_message)
        return
    before = snapshot_backpack()
    if not craft_gump(skill, tool_result):
        fail("Craft gump did not open.")
        return
    status("Crafting " + recipe["name"] + ".", LABEL_HUE, "Craft")
    cursor = journal_cursor()
    actions_complete = send_actions(skill["gump_id"], recipe["actions"])

    Misc.Pause(RESULT_WAIT_MS)
    outputs, amount = detected_outputs(recipe, before)
    quest_result = False
    if amount < max(1, int(recipe["output_amount"])):
        quest_result = quest_consumed(cursor)
    if not actions_complete and not outputs and not quest_result:
        fail("Craft button sequence was incomplete.")
        return
    if not outputs and not quest_result:
        fail("No matching crafted output appeared.")
        return
    clear_failures()
    _crafts += 1
    if outputs:
        _pending = outputs
        _pending_disposal = disposal
        status("Crafted " + recipe["name"] + "; processing output.", GOOD_HUE, "Output")
    else:
        status("Quest accepted " + recipe["name"] + ".", GOOD_HUE, "Craft")


# ===========================================================
# GUI / CONTROLS
# ===========================================================

def add_button(gd, x, y, button_id, text, hue=LABEL_HUE, up=4005, down=4007):
    Gumps.AddButton(gd, x, y, up, down, int(button_id), 1, 0)
    Gumps.AddLabel(gd, x + 24, y, int(hue), str(text))


def status_panel(gd, y, width):
    Gumps.AddBackground(gd, 10, y, width, 55, 3000)
    Gumps.AddAlphaRegion(gd, 10, y, width, 55)
    Gumps.AddLabel(gd, 20, y + 4, TITLE_HUE, "STATUS")
    Gumps.AddLabel(gd, 83, y + 4, DIM_HUE, short(_step, 40))
    Gumps.AddLabel(gd, 20, y + 27, _status_hue, short(_status, 70 if width > 600 else 57))


def render_home():
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)
    Gumps.AddBackground(gd, 0, 0, 670, 410, BG_ID)
    Gumps.AddAlphaRegion(gd, 0, 0, 670, 410)
    Gumps.AddItem(gd, 8, 5, 0x2130, TITLE_HUE)
    Gumps.AddLabel(gd, 42, 8, TITLE_HUE, "FROG CRAFTING TRAINER " + VERSION)
    Gumps.AddButton(gd, 636, 7, 4017, 4018, BTN_CLOSE, 1, 0)

    Gumps.AddBackground(gd, 10, 34, 650, 148, 3000)
    Gumps.AddAlphaRegion(gd, 10, 34, 650, 148)
    Gumps.AddLabel(gd, 20, 40, TITLE_HUE, "CRAFTING SKILLS")
    Gumps.AddLabel(gd, 185, 40, DIM_HUE, "Choose a training path.")
    for index, skill in enumerate(SKILLS):
        x = 20 + (index % 2) * 320
        y = 67 + (index // 2) * 27
        hue = GOOD_HUE if index == _selected else LABEL_HUE
        add_button(gd, x, y, BTN_SKILL_BASE + index, short(skill["name"], 27), hue)

    Gumps.AddBackground(gd, 10, 188, 650, 160, 3000)
    Gumps.AddAlphaRegion(gd, 10, 188, 650, 160)
    Gumps.AddLabel(gd, 20, 194, TITLE_HUE, "SETUP & STORAGE")
    add_button(gd, 20, 216, BTN_SOURCE, "Source: " + ("Shelf + Chest" if _source_mode == "shelf" else "Resource Chest"), GOOD_HUE)
    add_button(gd, 20, 243, BTN_CHEST, "Set Chest")
    Gumps.AddLabel(gd, 140, 244, LABEL_HUE, short(label(_resource_chest, "Chest not set"), 24))
    add_button(gd, 20, 269, BTN_RESOURCE_SHELF, "Set Shelf")
    Gumps.AddLabel(gd, 140, 270, LABEL_HUE, short(label(_resource_shelf, "Shelf not set"), 24))
    add_button(gd, 20, 295, BTN_REAGENT_SHELF, "Set Reagent Shelf")
    Gumps.AddLabel(gd, 170, 296, LABEL_HUE, short(label(_reagent_shelf, "Reagent shelf not set"), 21))
    add_button(gd, 340, 243, BTN_OUTPUT, "Set Output")
    Gumps.AddLabel(gd, 464, 244, LABEL_HUE, short(label(_output_chest, "Backpack output"), 22))
    add_button(gd, 340, 269, BTN_TOOL_BOOK, "Set Tool Book")
    Gumps.AddLabel(gd, 464, 270, LABEL_HUE, short(label(_tool_book, "Tool book not set"), 22))
    add_button(gd, 340, 295, BTN_TRASH, "Set Trash")
    Gumps.AddLabel(gd, 464, 296, LABEL_HUE, short(label(_trash_container, "Trash not set"), 22))
    Gumps.AddLabel(gd, 20, 322, DIM_HUE, "Shelf users: set and lock the withdrawal amount to 100 for each used entry.")
    status_panel(gd, 352, 650)
    Gumps.SendGump(GUMP_ID, Player.Serial, GUMP_X, GUMP_Y, gd.gumpDefinition, gd.gumpStrings)


def render_training():
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)
    Gumps.AddBackground(gd, 0, 0, 560, 262, BG_ID)
    Gumps.AddAlphaRegion(gd, 0, 0, 560, 262)
    Gumps.AddItem(gd, 8, 5, 0x2130, TITLE_HUE)
    Gumps.AddLabel(gd, 42, 8, TITLE_HUE, "FROG CRAFTING TRAINER " + VERSION)
    add_button(gd, 420, 7, BTN_HOME, "Home", GOOD_HUE)
    Gumps.AddButton(gd, 526, 7, 4017, 4018, BTN_CLOSE, 1, 0)
    skill = selected_skill()
    current, cap, goal, stage, recipe, reason = training_context()
    informational = bool(skill["informational"])
    Gumps.AddBackground(gd, 10, 34, 540, 118, 3000)
    Gumps.AddAlphaRegion(gd, 10, 34, 540, 118)
    Gumps.AddLabel(gd, 20, 41, TITLE_HUE, "TRAINING " + skill["name"].upper())
    Gumps.AddLabel(gd, 20, 64, LABEL_HUE, "{0}: {1:.1f} / cap {2:.1f} / goal {3:.1f}".format(skill["skill_name"], current, cap, goal))
    if informational:
        Gumps.AddLabel(gd, 20, 85, GOOD_HUE, "Guide: " + short(reason, 55))
        Gumps.AddLabel(gd, 20, 128, DIM_HUE, "Information only - no automated craft cycle")
    elif stage:
        Gumps.AddLabel(gd, 20, 85, LABEL_HUE, "Stage: {0:.1f} - {1:.1f}".format(float(stage["min_skill"]), float(stage["max_skill"])))
        Gumps.AddLabel(gd, 185, 85, GOOD_HUE if recipe else WARN_HUE, "Crafting: " + short(recipe["name"] if recipe else stage["label"], 36))
        policy = stage["disposal"]["mode"]
        if policy == "save":
            policy = "Save to output chest" if _output_chest else "Save in backpack"
        Gumps.AddLabel(gd, 20, 106, LABEL_HUE, "Output: " + policy.title())
        gained = max(0.0, current - _start_skill)
        Gumps.AddLabel(gd, 20, 128, DIM_HUE, "Crafts this run: {0} | Skill gained: +{1:.1f}{2}".format(_crafts, gained, " | output pending" if _pending else ""))
    else:
        Gumps.AddLabel(gd, 20, 85, WARN_HUE, "Stage: " + short(reason, 55))
        Gumps.AddLabel(gd, 20, 128, DIM_HUE, "Crafts this run: " + str(_crafts))
    Gumps.AddBackground(gd, 10, 158, 540, 36, 3000)
    Gumps.AddAlphaRegion(gd, 10, 158, 540, 36)
    action = "Show Message" if informational else ("Pause" if _training else "Start Training")
    add_button(gd, 20, 165, BTN_TOGGLE, action, WARN_HUE if _training else GOOD_HUE, 4011, 4013)
    add_button(gd, 220, 165, BTN_HOME, "Home / Setup", LABEL_HUE)
    Gumps.AddLabel(gd, 407, 166, DIM_HUE, "Using: " + ("Shelf" if _source_mode == "shelf" else "Chest"))
    status_panel(gd, 200, 540)
    Gumps.SendGump(GUMP_ID, Player.Serial, GUMP_X, GUMP_Y, gd.gumpDefinition, gd.gumpStrings)


def render():
    global _dirty
    close_gump(GUMP_ID)
    if _view == "training":
        render_training()
    else:
        render_home()
    _dirty = False


def set_target(button):
    global _resource_chest, _resource_shelf, _reagent_shelf
    global _output_chest, _tool_book, _trash_container
    prompts = {
        BTN_CHEST: "Target the resource chest",
        BTN_RESOURCE_SHELF: "Target the Resource Shelf",
        BTN_REAGENT_SHELF: "Target the Reagent/Gem Shelf",
        BTN_OUTPUT: "Target the output chest",
        BTN_TOOL_BOOK: "Target the Crafting Tool Storage book",
        BTN_TRASH: "Target the training trash container",
    }
    Target.Cancel()
    serial = Target.PromptTarget(prompts[button])
    found = item(serial)
    if not found:
        status("Target cancelled or item unavailable.", WARN_HUE, "Setup")
        return
    if button in (BTN_CHEST, BTN_OUTPUT, BTN_TRASH):
        try:
            if not bool(found.IsContainer):
                status("Target a container for this setting.", BAD_HUE, "Setup")
                return
        except:
            status("Container target could not be verified.", BAD_HUE, "Setup")
            return
    if button == BTN_RESOURCE_SHELF:
        if int(found.ItemID) != int(TRAINING_DATA["resource_shelf_item"]):
            status("That item is not the Resource Shelf.", BAD_HUE, "Setup")
            return
        _resource_shelf = int(serial)
    elif button == BTN_REAGENT_SHELF:
        gump_id = int(TRAINING_DATA["reagent_shelf_gump"])
        close_gump(gump_id)
        Items.UseItem(found)
        Gumps.WaitForGump(gump_id, SERVER_WAIT_MS)
        if not gump_open(gump_id):
            status("That item did not open the Reagent/Gem Shelf.", BAD_HUE, "Setup")
            return
        close_gump(gump_id)
        _reagent_shelf = int(serial)
    elif button == BTN_CHEST:
        _resource_chest = int(serial)
    elif button == BTN_OUTPUT:
        _output_chest = int(serial)
    elif button == BTN_TOOL_BOOK:
        _tool_book = int(serial)
    elif button == BTN_TRASH:
        _trash_container = int(serial)
    if save_settings():
        status("Target saved for this character.", GOOD_HUE, "Setup")
    else:
        status("Target set for this session; settings were not saved.", WARN_HUE, "Setup")


def handle_button(button):
    global _running, _training, _view, _selected, _source_mode
    global _crafts, _start_skill, _failures, _dirty
    if button == BTN_CLOSE:
        _training = False
        _running = False
        return
    if button == BTN_HOME:
        if _training:
            pause("Training paused. Return to the skill to resume.")
        _view = "home"
        _dirty = True
        return
    if button == BTN_TOGGLE:
        skill = selected_skill()
        if skill["informational"]:
            status(skill["message"], GOOD_HUE, "Guide")
            Misc.SendMessage(skill["message"], GOOD_HUE)
            return
        if _training:
            pause("Training paused; pending output is preserved.")
            return
        current, cap, goal, stage, recipe, reason = training_context()
        if not _pending and (current >= goal or not stage or stage["mode"] != "craft" or not recipe):
            status(reason or "No usable training stage.", WARN_HUE, "Training")
            return
        if _crafts == 0 and not _pending:
            _start_skill = current
        _failures = 0
        _training = True
        status("Training " + skill["name"] + ".", GOOD_HUE, "Training")
        return
    if _training or _pending:
        status("Pause and process pending output before changing setup or skill.", WARN_HUE, "Training")
        return
    if button == BTN_SOURCE:
        _source_mode = "chest" if _source_mode == "shelf" else "shelf"
        saved = save_settings()
        message = "Resource source: " + ("Shelf + Chest" if _source_mode == "shelf" else "Chest") + "."
        status(message if saved else message + " Settings were not saved.", GOOD_HUE if saved else WARN_HUE, "Setup")
        return
    if button in (BTN_CHEST, BTN_RESOURCE_SHELF, BTN_REAGENT_SHELF, BTN_OUTPUT, BTN_TOOL_BOOK, BTN_TRASH):
        set_target(button)
        return
    if BTN_SKILL_BASE <= button < BTN_SKILL_BASE + len(SKILLS):
        _selected = button - BTN_SKILL_BASE
        _crafts = 0
        _start_skill = skill_value(selected_skill()["skill_name"])
        _view = "training"
        status("Selected " + selected_skill()["name"] + ".", GOOD_HUE, "Training")
        _dirty = True


def poll_button():
    global _dirty
    try:
        gd = Gumps.GetGumpData(GUMP_ID)
        button = int(getattr(gd, "buttonid", 0)) if gd else 0
    except:
        button = 0
        gd = None
    if button <= 0:
        return False
    try:
        gd.buttonid = 0
    except:
        pass
    close_gump(GUMP_ID)
    handle_button(button)
    _dirty = True
    Misc.Pause(180)
    return True


# ===========================================================
# MAIN
# ===========================================================

def Main():
    global _dirty, _clicked
    load_settings()
    _dirty = True
    render()
    Misc.SendMessage("Frog Crafting Trainer {0} loaded ({1} paths).".format(VERSION, len(SKILLS)), GOOD_HUE)
    previous = None
    while _running and Player.Connected:
        _clicked = False
        try:
            if poll_button():
                Misc.Pause(REFRESH_MS)
                continue
            if _training:
                training_step()
            if _clicked or not _running:
                Misc.Pause(REFRESH_MS)
                continue
            if poll_button():
                Misc.Pause(REFRESH_MS)
                continue
            if _view == "training":
                context = training_context()
                snapshot = (context[0], context[3]["label"] if context[3] else "", context[4]["name"] if context[4] else "", _crafts, len(_pending))
                if snapshot != previous:
                    previous = snapshot
                    _dirty = True
            if _dirty or not gump_open(GUMP_ID):
                render()
        except Exception as ex:
            pause("Trainer error: " + str(ex), BAD_HUE)
            Misc.SendMessage("Frog Crafting Trainer error: " + str(ex), BAD_HUE)
        Misc.Pause(REFRESH_MS)
    close_gump(GUMP_ID)
    close_gump(TOOL_BOOK_GUMP_ID)
    close_gump(int(TRAINING_DATA["resource_shelf_gump"]))
    close_gump(int(TRAINING_DATA["reagent_shelf_gump"]))
    Misc.SendMessage("Frog Crafting Trainer stopped." + (" Crafted output remains in backpack." if _pending else ""), WARN_HUE)


Main()
