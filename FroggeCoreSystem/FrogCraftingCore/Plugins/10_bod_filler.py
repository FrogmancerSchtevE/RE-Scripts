# ===============================================
# === Frog BOD Filler (Razor Enhanced Script) ===
# ===============================================
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

# Status: In Development

import re

BOD_DATA_FILE = "bod_filler.json"
REAGENT_GEM_DATA_FILE = "reagent_gem_shelf.json"
FALLBACK_GEM_RESOURCE_KEYS = (
    "amber", "amethyst", "citrine", "diamond", "emerald", "ruby",
    "sapphire", "star_sapphires", "tourmaline", "blue_diamond",
    "dark_sapphire", "ecru_citrine", "fire_ruby", "perfect_emerald",
    "turquoise", "white_pearl", "brilliant_amber",
)

BTN_SET_CHEST_ONE = 1
BTN_SET_CHEST_TWO = 2
BTN_MODE_TOGGLE = 3
BTN_TARGET_BOD = 4
BTN_SCAN = 5
BTN_START_FILL = 7
BTN_FILTERS = 8
BTN_FILTER_BACK = 9
BTN_FILTER_PREV = 10
BTN_FILTER_NEXT = 11
BTN_OPEN_BOD = 12
BTN_FILTER_ROW_BASE = 100

MODE_BULK = "bulk"
MODE_SINGLE = "single"

STATE_IDLE = "idle"
STATE_SCANNING = "scanning"
STATE_BULK_PREPARE = "bulk_prepare"
STATE_BULK_RETURN = "bulk_return"
STATE_CRAFTING = "crafting"
STATE_COMBINING = "combining"
STATE_RECYCLING = "recycling"
STATE_CLEANUP = "cleanup"

PAGE_MAIN = "main"
PAGE_FILTERS = "filters"
FILTER_ROWS = 11
FILTER_COLUMNS = 2
FILTER_PAGE_SIZE = FILTER_ROWS * FILTER_COLUMNS
MOVE_PAUSE_MS = 700
BULK_INSPECT_PAUSE_MS = 600
BOD_GUMP_SETTLE_MS = 250


class FrogBODFillerPlugin:
    plugin_id = "bod_filler"
    name = "BOD Filler"
    version = "1.0"
    home_label = "BOD Filler"

    def __init__(self, host):
        self.host = host
        self.button_base = 0
        self.running = False
        self.chest_one = host.read_int("bod_filler_chest_one", 0)
        self.chest_two = host.read_int("bod_filler_chest_two", 0)
        self.mode = host.read_text("bod_filler_mode", MODE_BULK)
        if self.mode not in (MODE_BULK, MODE_SINGLE):
            self.mode = MODE_BULK
        self.page = PAGE_MAIN
        self.filter_page = 0
        self.filter_button_map = {}
        self.bulk_filter_values = {}
        self.current_bod_type = ""
        self.current_material = ""
        self.current_item_name = ""
        self.current_item_id = 0
        self.observed_output_item_id = 0
        self.current_bod_serial = 0
        self.matched_module_id = ""
        self.matched_category_id = ""
        self.matched_recipe_id = ""
        self.match_summary = "No order inspected"
        self.start_block_reason = "No BOD has been inspected."
        self.workflow_state = STATE_IDLE
        self.job_initial_finished = 0
        self.job_remaining = 0
        self.job_stackable = False
        self.job_resource_choices = {}
        self.exceptional_required = False
        self.skill_warning = ""
        self.fill_passes = 0
        self.zero_accept_passes = 0
        self.accepted_total = 0
        self.recycled_total = 0
        self.discarded_total = 0
        self.recycle_queue = []
        self.recycle_retry_count = 0
        self.recycle_action_failures = 0
        self.recycle_container_exhausted = False
        self.post_cleanup_action = ""
        self.post_cleanup_message = ""
        self.amount_to_craft = 0
        self.amount_crafted = 0
        self.bods_completed = 0
        self.bods_total = 0
        self.bulk_queue = []
        self.bulk_index = 0
        self.bulk_run_active = False
        self.bulk_run_skipped = 0
        self.bulk_points_completed = 0
        self.scan_candidates = []
        self.scan_index = 0
        self.scan_found = 0
        self.scan_rejected = []
        self.scan_current_serial = 0
        self.scan_current_source = 0
        self.scan_current_staged = False
        self.current_source_serial = 0
        self.current_source_slot = 0
        self.current_bulk_record = {}
        self.artificer_points = 0
        self.artificer_points_known = False
        self.last_gump_lines = []
        self.data = {}
        self.data_error = ""
        try:
            self.data = host.read_data(BOD_DATA_FILE)
            if self.data.get("format") != "frog-bod-filler-data":
                raise Exception("unsupported BOD data format")
            if int(self.data.get("version", 0)) != 1:
                raise Exception("unsupported BOD data version")
        except Exception as ex:
            self.data = {}
            self.data_error = str(ex)
        self.gem_resource_keys = self.load_gem_resource_keys()
        if not self.data_error:
            # Read every persisted filter during plugin load so legacy shared
            # values can be migrated into the character's settings JSON once.
            for entry in self.bulk_filter_entries():
                self.bulk_filter_enabled(entry.get("kind", ""), entry.get("key", ""))

    def button_id(self, local_id):
        return int(self.button_base) + int(local_id)

    def is_priority_button(self, local_button):
        return self.running and int(local_button) == BTN_START_FILL

    def activate(self):
        if self.data_error:
            self.host.set_status("BOD data error: " + self.data_error, BAD_HUE, "BOD Setup")
        elif self.mode == MODE_BULK:
            self.host.set_status("BOD Filler loaded. Set up to two sources, configure filters, then Scan Orders.", GOOD_HUE, "BOD Setup")
        else:
            self.host.set_status("BOD Filler loaded. Target a backpack BOD to inspect it.", GOOD_HUE, "BOD Setup")
        self.host.mark_dirty()

    def deactivate(self, message=None):
        if self.running:
            self.cancel_fill(message or "BOD work paused.", WARN_HUE)
            return
        self.running = False
        self.workflow_state = STATE_IDLE
        self.recycle_queue = []
        self.recycle_retry_count = 0
        self.recycle_action_failures = 0
        self.recycle_container_exhausted = False
        if message:
            self.host.set_status(str(message), WARN_HUE, "BOD Paused")
        self.host.mark_dirty()

    def step(self):
        if not self.running:
            return
        if self.workflow_state == STATE_SCANNING:
            self.scan_step()
            self.host.mark_dirty()
            return
        if self.workflow_state == STATE_BULK_PREPARE:
            self.prepare_bulk_order()
            self.host.mark_dirty()
            return
        if self.workflow_state == STATE_BULK_RETURN:
            self.return_bulk_order()
            self.host.mark_dirty()
            return
        if self.workflow_state == STATE_RECYCLING:
            self.recycle_rejected_output()
            self.host.mark_dirty()
            return
        if self.workflow_state == STATE_CLEANUP:
            self.post_combine_cleanup_step()
            self.host.mark_dirty()
            return
        if self.workflow_state != STATE_CRAFTING:
            self.cancel_fill("BOD fill stopped in an unknown workflow state.", BAD_HUE)
            return

        status = self.host.craft_job_status(self.plugin_id)
        self.host.mark_dirty()
        if str(status.get("state", "")) == "running":
            return

        self.host.end_craft_job(self.plugin_id, False)
        if str(status.get("state", "")) != "complete":
            if self.bulk_run_active and self.current_bulk_record:
                self.return_record_to_source(self.current_bulk_record)
            self.running = False
            self.workflow_state = STATE_IDLE
            self.bulk_run_active = False
            self.host.set_status("BOD crafting stopped: " + str(status.get("message", "unknown FCC stop")), BAD_HUE, "BOD Fill")
            return

        self.workflow_state = STATE_COMBINING
        try:
            self.combine_crafted_output()
        except Exception as ex:
            if self.bulk_run_active and self.current_bulk_record:
                self.return_record_to_source(self.current_bulk_record)
            self.running = False
            self.workflow_state = STATE_IDLE
            self.bulk_run_active = False
            self.host.set_status("BOD combine stopped: " + str(ex), BAD_HUE, "BOD Combine")
        finally:
            try:
                Target.Cancel()
            except:
                pass
            try:
                Gumps.CloseGump(self.profile_int("gump", "gump_id", 0))
            except:
                pass
        self.host.mark_dirty()

    def profile_value(self, section, key, fallback=0):
        record = self.data.get(section, {}) if self.data else {}
        return record.get(key, fallback) if isinstance(record, dict) else fallback

    def profile_int(self, section, key, fallback=0):
        value = self.profile_value(section, key, fallback)
        try:
            text = str(value).strip().lower()
            return int(text, 16) if text.startswith("0x") else int(value)
        except:
            return int(fallback)

    def policy_int(self, key, fallback):
        return max(0, self.profile_int("fill_policy", key, fallback))

    def int_value(self, value, fallback=0):
        try:
            text = str(value).strip().lower()
            return int(text, 16) if text.startswith("0x") else int(value)
        except:
            return int(fallback)

    def normalized_name(self, value):
        text = str(value or "").strip().lower()
        text = re.sub(r"[^a-z0-9]+", " ", text)
        return " ".join(text.split())

    def dotnet_strings(self, values):
        result = []
        try:
            for value in values:
                text = str(value).strip()
                if text:
                    result.append(text)
        except:
            pass
        return result

    def bulk_filter_config(self):
        config = self.data.get("bulk_filters", {}) if self.data else {}
        return config if isinstance(config, dict) else {}

    def load_gem_resource_keys(self):
        keys = []
        try:
            catalog = self.host.read_data(REAGENT_GEM_DATA_FILE)
            for resource in catalog.get("resources", []):
                category = self.normalized_name(resource.get("category", "")).replace(" ", "_")
                resource_key = self.normalized_name(resource.get("id", "")).replace(" ", "_")
                if category == "gems" and resource_key and resource_key not in keys:
                    keys.append(resource_key)
        except:
            pass
        return tuple(keys or FALLBACK_GEM_RESOURCE_KEYS)

    def bulk_filter_setting_key(self, kind, key):
        suffix = self.normalized_name(key).replace(" ", "_")
        return "bod_bulk_filter_{0}_{1}".format(str(kind), suffix)

    def bulk_filter_default(self, kind, key):
        config = self.bulk_filter_config()
        if kind == "exceptional":
            return bool(config.get("exceptional", True))
        values = config.get(str(kind) + "s", {})
        if isinstance(values, dict) and str(key) in values:
            return bool(values.get(str(key)))
        return True

    def bulk_filter_enabled(self, kind, key):
        cache_key = (str(kind), str(key))
        if cache_key in self.bulk_filter_values:
            return bool(self.bulk_filter_values[cache_key])
        fallback = 1 if self.bulk_filter_default(kind, key) else 0
        enabled = self.host.read_int(self.bulk_filter_setting_key(kind, key), fallback) != 0
        self.bulk_filter_values[cache_key] = enabled
        return enabled

    def bulk_filter_entries(self):
        entries = [
            {"kind": "exceptional", "key": "orders", "label": "Exceptional orders"},
            {"kind": "ingredient", "key": "bone", "label": "Recipes requiring Bone"},
            {"kind": "ingredient", "key": "gems", "label": "Recipes requiring Gems"},
        ]
        seen_modules = []
        for profile in self.data.get("craft_profiles", []):
            module_id = str(profile.get("module_id", ""))
            if module_id and module_id not in seen_modules:
                seen_modules.append(module_id)
                entries.append({"kind": "skill", "key": module_id, "label": self.module_title(module_id)})

        seen_materials = []
        for module in self.host.modules():
            for group in module.get("resource_choice_groups", []):
                for option in group.get("options", []):
                    option_id = str(option.get("id", "")).strip()
                    if not option_id or option_id in seen_materials:
                        continue
                    seen_materials.append(option_id)
                    entries.append({
                        "kind": "material",
                        "key": option_id,
                        "label": str(option.get("name", option_id)).strip(),
                    })
        return entries

    def material_filter_label(self, option_id):
        wanted = str(option_id or "")
        for entry in self.bulk_filter_entries():
            if entry.get("kind") == "material" and str(entry.get("key", "")) == wanted:
                return str(entry.get("label", wanted))
        return wanted.replace("_", " ").title()

    def recipe_bulk_enabled(self, module_id, recipe_id):
        for override in self.data.get("recipe_overrides", []):
            if str(override.get("module_id", "")) != str(module_id):
                continue
            if str(override.get("recipe_id", "")) != str(recipe_id):
                continue
            if "bulk_enabled" in override:
                return bool(override.get("bulk_enabled"))
        return True

    def recipe_for_id(self, module_id, recipe_id):
        module = self.host.module(module_id)
        for category in (module or {}).get("categories", []):
            for recipe in category.get("recipes", []):
                if str(recipe.get("id", "")) == str(recipe_id):
                    return recipe
        return None

    def recipe_requires_resource(self, module_id, recipe_id, resource_key, visited=None):
        wanted = self.normalized_name(resource_key).replace(" ", "_")
        recipe = self.recipe_for_id(module_id, recipe_id)
        if not recipe or not wanted:
            return False

        seen = set(visited or [])
        recipe_key = str(module_id) + ":" + str(recipe_id)
        if recipe_key in seen:
            return False
        seen.add(recipe_key)

        for resource in recipe.get("resources", []):
            current_key = self.normalized_name(resource.get("resource_key", "")).replace(" ", "_")
            if current_key == wanted:
                return True
            component_id = str(resource.get("craft_recipe_id", "")).strip()
            if component_id and self.recipe_requires_resource(module_id, component_id, wanted, seen):
                return True
        return False

    def recipe_requires_any_resource(self, module_id, recipe_id, resource_keys):
        for resource_key in resource_keys:
            if self.recipe_requires_resource(module_id, recipe_id, resource_key):
                return True
        return False

    def bulk_filter_reason(self, record):
        module_id = str(record.get("module_id", ""))
        if module_id and not self.bulk_filter_enabled("skill", module_id):
            return self.module_title(module_id) + " orders are disabled"
        if bool(record.get("exceptional_required", False)) and not self.bulk_filter_enabled("exceptional", "orders"):
            return "exceptional orders are disabled"
        if self.recipe_requires_resource(module_id, record.get("recipe_id", ""), "bone") and not self.bulk_filter_enabled("ingredient", "bone"):
            return "recipes requiring Bone are disabled"
        if self.recipe_requires_any_resource(module_id, record.get("recipe_id", ""), self.gem_resource_keys) and not self.bulk_filter_enabled("ingredient", "gems"):
            return "recipes requiring Gems are disabled"
        for option_id in record.get("material_choices", {}).values():
            if not self.bulk_filter_enabled("material", option_id):
                return self.material_filter_label(option_id) + " material is disabled"
        if not self.recipe_bulk_enabled(module_id, record.get("recipe_id", "")):
            return "this recipe is disabled for bulk mode"
        return ""

    def clear_bulk_queue(self, message=None):
        self.bulk_queue = []
        self.bulk_index = 0
        self.bulk_run_active = False
        self.bulk_run_skipped = 0
        self.bulk_points_completed = 0
        self.scan_candidates = []
        self.scan_index = 0
        self.scan_found = 0
        self.scan_rejected = []
        self.set_bulk_progress(0, 0)
        if self.mode == MODE_BULK:
            self.current_bulk_record = {}
            self.current_source_serial = 0
            self.current_source_slot = 0
            self.current_bod_serial = 0
            self.matched_module_id = ""
            self.matched_category_id = ""
            self.matched_recipe_id = ""
            self.job_resource_choices = {}
            self.exceptional_required = False
            self.skill_warning = ""
            self.start_block_reason = "Scan Orders to build a bulk queue."
            self.match_summary = str(message or "No bulk queue scanned")
            self.set_current_order("", "", 0, 0, "", 0)
            self.set_artificer_points(0, False)

    def toggle_bulk_filter(self, entry):
        kind = str(entry.get("kind", ""))
        key = str(entry.get("key", ""))
        enabled = not self.bulk_filter_enabled(kind, key)
        self.host.write_int(self.bulk_filter_setting_key(kind, key), 1 if enabled else 0)
        self.bulk_filter_values[(kind, key)] = enabled
        self.clear_bulk_queue("Filters changed; scan again")
        self.host.set_status(
            "Bulk filter {0}: {1}. Scan Orders again.".format(entry.get("label", key), "Yes" if enabled else "No"),
            GOOD_HUE if enabled else WARN_HUE,
            "BOD Filters",
        )

    def source_containers(self):
        result = []
        seen = []
        for slot, serial in ((1, self.chest_one), (2, self.chest_two)):
            item = self.host.valid_item(serial)
            if not item or not bool(getattr(item, "IsContainer", False)):
                continue
            parsed = self.int_value(getattr(item, "Serial", 0), 0)
            if parsed <= 0 or parsed in seen:
                continue
            seen.append(parsed)
            result.append((slot, parsed))
        return result

    def container_scan_items(self, slot, root_serial):
        root = Items.FindBySerial(root_serial)
        if not root:
            return []
        try:
            Items.UseItem(root)
            Items.WaitForContents(root, 1500)
        except:
            pass

        result = []
        pending = [(root, 0)]
        visited = []
        while pending:
            container, depth = pending.pop(0)
            serial = self.int_value(getattr(container, "Serial", 0), 0)
            if serial <= 0 or serial in visited:
                continue
            visited.append(serial)
            try:
                children = list(container.Contains or [])
            except:
                children = []
            for item in children:
                item_serial = self.int_value(getattr(item, "Serial", 0), 0)
                if item_serial <= 0:
                    continue
                if bool(getattr(item, "IsContainer", False)) and depth < 8:
                    pending.append((item, depth + 1))
                    continue
                result.append({
                    "serial": item_serial,
                    "source_serial": self.int_value(getattr(item, "Container", 0), root_serial),
                    "source_slot": slot,
                })
        return result

    def move_bod_to_container(self, serial, destination_serial):
        item = Items.FindBySerial(self.int_value(serial, 0))
        destination = Items.FindBySerial(self.int_value(destination_serial, 0))
        if not item or not destination or not bool(getattr(destination, "IsContainer", False)):
            return False
        if self.int_value(getattr(item, "Container", 0), 0) == self.int_value(destination_serial, 0):
            return True
        try:
            Items.Move(int(item.Serial), int(destination.Serial), 1)
            Misc.Pause(MOVE_PAUSE_MS)
        except:
            return False
        refreshed = Items.FindBySerial(self.int_value(serial, 0))
        return bool(refreshed) and self.int_value(getattr(refreshed, "Container", 0), 0) == self.int_value(destination_serial, 0)

    def inspect_bod_record(self, serial, source_serial=0, source_slot=0):
        if not self.open_bod_gump(serial):
            raise Exception("order did not open the configured BOD gump")

        lines = self.bod_gump_lines()
        parsed = self.parse_bod_gump(lines)
        item = Items.FindBySerial(serial)
        property_lines = self.item_property_lines(item) if item else []
        if not item or not self.is_bod_item(item, property_lines):
            raise Exception("item is not identified as a bulk order")
        module_hint = self.module_hint_from_item(item, property_lines)
        module, category, recipe = self.find_recipe_match(
            module_hint,
            parsed.get("requested_names", []),
            parsed.get("requested_item_id", 0),
        )
        minimum_ok, minimum_detail, skill_warning = self.minimum_skill_check(module, recipe)
        material, material_choices, material_error = self.material_for_order(
            module,
            recipe,
            parsed.get("gump_lines", lines),
        )

        record = {
            "serial": self.int_value(serial, 0),
            "source_serial": self.int_value(source_serial, 0),
            "source_slot": self.int_value(source_slot, 0),
            "module_id": str(module.get("id", "")),
            "category_id": str(category.get("id", "")),
            "recipe_id": str(recipe.get("id", "")),
            "recipe_name": str(recipe.get("name", "")),
            "material": str(material),
            "material_choices": dict(material_choices),
            "exceptional_required": bool(parsed.get("exceptional_required", False)),
            "skill_warning": str(skill_warning or ""),
            "amount_to_make": self.int_value(parsed.get("amount_to_make"), 0),
            "amount_finished": self.int_value(parsed.get("amount_finished"), 0),
            "requested_item_id": self.int_value(parsed.get("requested_item_id"), 0),
            "artificer_points": self.int_value(parsed.get("artificer_points"), 0),
            "artificer_points_known": bool(parsed.get("artificer_points_known", False)),
            "stackable": self.stackable_for_recipe(module.get("id", ""), recipe.get("id", "")),
            "gump_lines": list(lines),
            "block_reason": "",
        }
        if not minimum_ok:
            record["block_reason"] = "skill filter: " + minimum_detail
        elif material_error:
            record["block_reason"] = material_error
        elif record["amount_finished"] >= record["amount_to_make"]:
            record["block_reason"] = "order is already complete"
        else:
            record["block_reason"] = self.bulk_filter_reason(record)
        return record

    def load_order_record(self, record):
        self.current_bulk_record = dict(record)
        self.current_bod_serial = self.int_value(record.get("serial"), 0)
        self.current_source_serial = self.int_value(record.get("source_serial"), 0)
        self.current_source_slot = self.int_value(record.get("source_slot"), 0)
        self.matched_module_id = str(record.get("module_id", ""))
        self.matched_category_id = str(record.get("category_id", ""))
        self.matched_recipe_id = str(record.get("recipe_id", ""))
        self.job_resource_choices = dict(record.get("material_choices", {}))
        self.exceptional_required = bool(record.get("exceptional_required", False))
        self.skill_warning = str(record.get("skill_warning", ""))
        self.start_block_reason = str(record.get("block_reason", ""))
        self.job_stackable = bool(record.get("stackable", False))
        self.last_gump_lines = list(record.get("gump_lines", []))
        self.match_summary = "Matched {0} / {1}".format(
            self.module_title(self.matched_module_id),
            record.get("recipe_name", ""),
        )
        self.set_current_order(
            self.module_title(self.matched_module_id),
            record.get("material", ""),
            record.get("amount_to_make", 0),
            record.get("amount_finished", 0),
            record.get("recipe_name", ""),
            record.get("requested_item_id", 0),
        )
        self.set_artificer_points(record.get("artificer_points", 0), record.get("artificer_points_known", False))

    def bulk_sort_key(self, record):
        choices = record.get("material_choices", {})
        material_key = ",".join(["{0}:{1}".format(key, choices[key]) for key in sorted(choices.keys())])
        return (
            str(record.get("module_id", "")),
            material_key,
            1 if bool(record.get("exceptional_required", False)) else 0,
            str(record.get("recipe_id", "")),
            self.int_value(record.get("source_slot"), 0),
            self.int_value(record.get("serial"), 0),
        )

    def profile_for_hue(self, hue):
        wanted = self.int_value(hue, -1)
        for profile in self.data.get("craft_profiles", []):
            raw_hue = profile.get("bod_hue")
            if raw_hue is not None and self.int_value(raw_hue, -2) == wanted:
                return profile
        return None

    def profile_for_module(self, module_id):
        wanted = str(module_id or "")
        for profile in self.data.get("craft_profiles", []):
            if str(profile.get("module_id", "")) == wanted:
                return profile
        return None

    def module_hint_from_item(self, item, property_lines):
        profile = self.profile_for_hue(getattr(item, "Hue", -1))
        if profile:
            return str(profile.get("module_id", ""))

        searchable = self.normalized_name(" ".join(property_lines))
        aliases = {
            "alchemy": ("alchemy", "alchemist"),
            "blacksmithy": ("blacksmithy", "blacksmith", "smithing"),
            "carpentry": ("carpentry", "carpenter"),
            "cooking": ("cooking", "cook"),
            "fletching": ("fletching", "bowcraft"),
            "inscription": ("inscription", "scribe"),
            "tailoring": ("tailoring", "tailor"),
            "tinkering": ("tinkering", "tinker"),
        }
        for module_id, words in aliases.items():
            for word in words:
                if word in searchable:
                    return module_id
        return ""

    def module_title(self, module_id):
        module = self.host.module(module_id)
        if module:
            return str(module.get("name", module_id)).strip()
        return str(module_id or "Unknown").replace("_", " ").title()

    def item_property_lines(self, item):
        try:
            Items.WaitForProps(int(item.Serial), 1500)
        except:
            pass
        try:
            return self.dotnet_strings(Items.GetPropStringList(int(item.Serial)))
        except:
            return []

    def is_bod_item(self, item, property_lines):
        identification = self.data.get("identification", {})
        expected_item_id = self.int_value(identification.get("item_id"), 0)
        if expected_item_id > 0 and self.int_value(getattr(item, "ItemID", 0), 0) == expected_item_id:
            return True
        if not bool(identification.get("accept_order_property_match", False)):
            return False
        searchable = self.normalized_name(" ".join(property_lines))
        return "order" in searchable

    def parse_bod_gump(self, lines):
        cleaned = [str(value).strip() for value in lines if str(value).strip()]
        numeric_values = []
        requested_names = []
        points = 0
        points_known = False
        exceptional_required = False
        ignored_exact = (
            "amount to make",
            "amount finished",
            "item requested",
            "exit",
        )

        for line in cleaned:
            normalized = self.normalized_name(line)
            if re.match(r"^\d+$", line):
                numeric_values.append(self.int_value(line, 0))
                continue

            points_match = re.search(r"worth\s+(\d+).*artificer\s+points", line, re.IGNORECASE)
            if points_match:
                points = self.int_value(points_match.group(1), 0)
                points_known = True
                continue

            if "exceptional" in normalized:
                exceptional_required = True
                continue

            if normalized in ignored_exact:
                continue
            if "bulk order" in normalized:
                continue
            if normalized.startswith("combine this deed"):
                continue
            if line.endswith(":"):
                continue
            requested_names.append(line)

        numeric_layout = self.profile_value("gump", "numeric_text_layout", [])
        if not isinstance(numeric_layout, list) or not numeric_layout:
            numeric_layout = ["amount_to_make", "requested_item_id", "amount_finished"]
        if len(numeric_values) != len(numeric_layout):
            raise Exception("the BOD gump contains an unknown numeric layout")
        numeric_data = {}
        for index, field_name in enumerate(numeric_layout):
            numeric_data[str(field_name)] = numeric_values[index]

        amount_to_make = self.int_value(numeric_data.get("amount_to_make"), 0)
        amount_finished = self.int_value(numeric_data.get("amount_finished"), -1)
        requested_item_id = self.int_value(numeric_data.get("requested_item_id"), 0)
        if amount_to_make <= 0:
            raise Exception("amount to make is not positive")
        if amount_finished < 0 or amount_finished > amount_to_make:
            raise Exception("amount finished is outside the requested range")
        if requested_item_id <= 0 or requested_item_id > 0xFFFF:
            raise Exception("the requested item graphic is invalid")

        return {
            "amount_to_make": amount_to_make,
            "amount_finished": amount_finished,
            "requested_item_id": requested_item_id,
            "requested_names": requested_names,
            "gump_lines": cleaned,
            "exceptional_required": exceptional_required,
            "artificer_points": points,
            "artificer_points_known": points_known,
        }

    def recipe_output_ids(self, recipe):
        result = []
        for value in recipe.get("output_item_ids", []):
            parsed = self.int_value(value, 0)
            if parsed > 0:
                result.append(parsed)
        return result

    def recipe_output_names(self, recipe):
        values = list(recipe.get("output_names", []))
        if recipe.get("name"):
            values.append(recipe.get("name"))
        return [self.normalized_name(value) for value in values if self.normalized_name(value)]

    def base_recipe_name(self, value):
        normalized = self.normalized_name(value)
        return re.sub(r"\s+(left|right)$", "", normalized).strip()

    def recipe_override(self, module_id, requested_names, requested_item_id):
        wanted_names = [self.normalized_name(value) for value in requested_names if self.normalized_name(value)]
        for override in self.data.get("recipe_overrides", []):
            if str(override.get("module_id", "")) != str(module_id):
                continue
            override_item_id = self.int_value(override.get("requested_item_id"), 0)
            if override_item_id > 0 and override_item_id != requested_item_id:
                continue
            override_name = self.normalized_name(override.get("requested_name", ""))
            if override_name and override_name not in wanted_names:
                continue
            if override_item_id <= 0 and not override_name:
                continue
            return str(override.get("recipe_id", ""))
        return ""

    def find_recipe_match(self, module_hint, requested_names, requested_item_id):
        wanted_names = [self.normalized_name(value) for value in requested_names if self.normalized_name(value)]
        exact_matches = []
        base_matches = []
        for module in self.host.modules():
            module_id = str(module.get("id", ""))
            if module_hint and module_id != module_hint:
                continue
            for category in module.get("categories", []):
                for recipe in category.get("recipes", []):
                    recipe_names = self.recipe_output_names(recipe)
                    recipe_ids = self.recipe_output_ids(recipe)
                    name_match = any(value in recipe_names for value in wanted_names)
                    base_name_match = any(self.base_recipe_name(value) in [self.base_recipe_name(name) for name in recipe_names] for value in wanted_names)
                    id_match = requested_item_id > 0 and requested_item_id in recipe_ids
                    if (name_match or base_name_match) and requested_item_id > 0 and recipe_ids and not id_match:
                        continue
                    if not name_match and not base_name_match and not id_match:
                        continue
                    key = (module_id, str(recipe.get("id", "")))
                    target = exact_matches if name_match or id_match else base_matches
                    if not any(existing[0] == key for existing in target):
                        target.append((key, module, category, recipe))

        matches = exact_matches if exact_matches else base_matches
        if not matches:
            raise Exception("no exact FCC recipe matched the requested item")
        if len(matches) > 1:
            module_id = str(matches[0][1].get("id", ""))
            override_recipe_id = self.recipe_override(module_id, requested_names, requested_item_id)
            if override_recipe_id:
                for match in matches:
                    if str(match[3].get("id", "")) == override_recipe_id:
                        return match[1], match[2], match[3]
            names = ", ".join([str(match[3].get("name", match[3].get("id", ""))) for match in matches])
            raise Exception("ambiguous FCC recipe for 0x{0:04X}: {1}".format(requested_item_id, names))
        return matches[0][1], matches[0][2], matches[0][3]

    def text_contains_phrase(self, text, phrase):
        normalized_text = " " + self.normalized_name(text) + " "
        normalized_phrase = self.normalized_name(phrase)
        return bool(normalized_phrase) and (" " + normalized_phrase + " ") in normalized_text

    def material_for_order(self, module, recipe, gump_lines):
        needed_groups = []
        for resource in recipe.get("resources", []):
            group_id = str(resource.get("choice_group", "")).strip()
            if group_id and group_id not in needed_groups:
                needed_groups.append(group_id)
        if not needed_groups:
            return "Standard", {}, ""

        groups = {}
        for group in module.get("resource_choice_groups", []):
            groups[str(group.get("id", ""))] = group

        choices = {}
        labels = []
        matched_material = False
        material_requirement_seen = False
        material_lines = []
        normalized_gump_lines = [self.normalized_name(line) for line in gump_lines]
        for line in gump_lines:
            normalized = self.normalized_name(line)
            if "must be made with" in normalized or "must be crafted with" in normalized or "made from" in normalized or "crafted from" in normalized or "must use" in normalized or normalized.startswith("material "):
                material_requirement_seen = True
                material_lines.append(line)

        for group_id in needed_groups:
            group = groups.get(group_id)
            if not group:
                return "Unresolved", {}, "FCC recipe uses an unavailable material group: " + group_id
            options = list(group.get("options", []))
            matches = []
            for option in options:
                option_phrases = [option.get("name", ""), str(option.get("id", "")).replace("_", " ")]
                scores = [len(self.normalized_name(phrase).split()) for line in material_lines for phrase in option_phrases if self.text_contains_phrase(line, phrase)]
                exact_scores = [len(self.normalized_name(phrase).split()) for line in normalized_gump_lines for phrase in option_phrases if self.normalized_name(phrase) and line == self.normalized_name(phrase)]
                if exact_scores:
                    material_requirement_seen = True
                    scores.extend(exact_scores)
                if scores:
                    matches.append((max(scores), option))
            if matches:
                best_score = max([match[0] for match in matches])
                matches = [match[1] for match in matches if match[0] == best_score]
            if len(matches) > 1:
                return "Unresolved", {}, "more than one BOD material matched the " + str(group.get("name", group_id)) + " group"
            if matches:
                option = matches[0]
                matched_material = True
            else:
                default_id = str(group.get("default", ""))
                option = None
                for candidate in options:
                    if str(candidate.get("id", "")) == default_id:
                        option = candidate
                        break
                if not option:
                    return "Unresolved", {}, "FCC material group has no valid default: " + group_id
            choices[group_id] = str(option.get("id", ""))
            labels.append(str(option.get("name", option.get("id", group_id))))

        if material_requirement_seen and not matched_material:
            return "Unresolved", {}, "the BOD names a special material that FCC could not resolve"
        if not matched_material:
            profile = self.profile_for_module(module.get("id", ""))
            if profile and profile.get("default_material_label"):
                return str(profile.get("default_material_label")), choices, ""
        return " / ".join(labels), choices, ""

    def minimum_skill_check(self, module, recipe):
        margin = float(self.profile_value("skill_filter", "minimum_skill_margin", 50.0))
        requirements = []
        deferred = {}
        skill_name = str(module.get("skill_name", "")).strip()
        if skill_name:
            requirements.append((skill_name, float(recipe.get("min_skill", 0.0))))
        for requirement in recipe.get("skill_requirements", []):
            name = str(requirement.get("skill_name", "")).strip()
            if name:
                requirements.append((name, float(requirement.get("min_skill", 0.0))))
        for name, minimum in requirements:
            template_id = self.int_value(self.host.pending_template_for_skill(name), 0)
            if template_id > 0:
                deferred[str(name)] = template_id
                continue
            current = float(self.host.skill_value(name))
            if current < minimum:
                return False, "{0} {1:.1f}/{2:.1f} recipe minimum".format(name, current, minimum), ""
        warnings = ["{0} will be checked after template {1} activates".format(name, template_id) for name, template_id in deferred.items()]
        for name, minimum in requirements:
            if str(name) in deferred:
                continue
            current = float(self.host.skill_value(name))
            required = minimum + margin
            if current < required:
                warnings.append("{0} {1:.1f}/{2:.1f} theoretical 100% threshold".format(name, current, required))
        if warnings:
            return True, "recipe minimum met", "; ".join(warnings)
        return True, "theoretical 100% threshold met", ""

    def stackable_for_recipe(self, module_id, recipe_id):
        for override in self.data.get("recipe_overrides", []):
            if str(override.get("module_id", "")) == str(module_id) and str(override.get("recipe_id", "")) == str(recipe_id):
                if "stackable" in override:
                    return bool(override.get("stackable"))
        profile = self.profile_for_module(module_id)
        if profile and "stackable" in profile:
            return bool(profile.get("stackable"))
        return bool(self.data.get("stackable_default", False))

    def craft_bag_output_items(self):
        bag_serial = self.host.craft_bag_serial()
        bag = Items.FindBySerial(bag_serial) if bag_serial > 0 else None
        if not bag:
            return []
        try:
            Items.WaitForContents(bag, 1000)
        except:
            pass
        bag = Items.FindBySerial(bag_serial) or bag
        output_names = [self.normalized_name(self.current_item_name)]
        module = self.host.module(self.matched_module_id)
        if module:
            for category in module.get("categories", []):
                for recipe in category.get("recipes", []):
                    if str(recipe.get("id", "")) == self.matched_recipe_id:
                        output_names.extend(self.recipe_output_names(recipe))
                        break
        output_names = [name for name in output_names if name]
        result = []
        try:
            for item in list(bag.Contains or []):
                item_id = self.int_value(getattr(item, "ItemID", 0), 0)
                if item_id > 0 and item_id in (self.current_item_id, self.observed_output_item_id):
                    result.append(item)
                    continue
                name = self.normalized_name(getattr(item, "Name", ""))
                if not name:
                    try:
                        Items.WaitForProps(item, 500)
                        name = self.normalized_name(getattr(item, "Name", ""))
                    except:
                        pass
                if name.startswith("a "):
                    name = name[2:]
                elif name.startswith("an "):
                    name = name[3:]
                if name.startswith("exceptional "):
                    name = name[len("exceptional "):]
                if name in output_names:
                    result.append(item)
        except:
            return []
        return result

    def output_item_count(self, items):
        total = 0
        for item in items:
            total += max(1, self.int_value(getattr(item, "Amount", 1), 1))
        return total

    def bod_gump_is_open(self):
        gump_id = self.profile_int("gump", "gump_id", 0)
        if gump_id <= 0:
            return False
        try:
            return Gumps.GetGumpData(gump_id) is not None
        except:
            try:
                return bool(Gumps.HasGump()) and self.int_value(Gumps.CurrentGump(), 0) == gump_id
            except:
                return False

    def open_bod_gump(self, serial):
        gump_id = self.profile_int("gump", "gump_id", 0)
        if gump_id <= 0 or self.int_value(serial, 0) <= 0:
            return False
        Gumps.CloseGump(gump_id)
        Gumps.ResetGump()
        item = Items.FindBySerial(self.int_value(serial, 0))
        Items.UseItem(item if item else int(serial))
        Gumps.WaitForGump(gump_id, 3000)
        if self.bod_gump_is_open():
            Misc.Pause(BOD_GUMP_SETTLE_MS)
        return self.bod_gump_is_open()

    def is_bod_open_failure(self, error):
        return str(error) == "order did not open the configured BOD gump"

    def bod_gump_lines(self):
        gump_id = self.profile_int("gump", "gump_id", 0)
        if gump_id > 0:
            try:
                lines = self.dotnet_strings(Gumps.GetLineList(gump_id, False))
                if lines:
                    return lines
            except:
                pass
        try:
            return self.dotnet_strings(Gumps.LastGumpGetLineList())
        except:
            return []

    def open_selected_bod(self):
        return self.open_bod_gump(self.current_bod_serial)

    def open_current_bod(self):
        if self.current_bod_serial <= 0:
            self.host.set_status("No active BOD is selected.", WARN_HUE, "BOD Open")
            return
        if not Items.FindBySerial(self.current_bod_serial):
            self.host.set_status("The active BOD is no longer available.", BAD_HUE, "BOD Open")
            return
        if self.open_selected_bod():
            self.host.set_status("Opened the active BOD.", GOOD_HUE, "BOD Open")
        else:
            self.host.set_status("The active BOD did not open.", BAD_HUE, "BOD Open")

    def host_craft_job_api_version(self):
        getter = getattr(self.host, "craft_job_api_version", None)
        if not callable(getter):
            return 1
        try:
            return self.int_value(getter(), 1)
        except:
            return 1

    def scan_orders(self):
        if self.data_error:
            self.host.set_status("BOD data error: " + self.data_error, BAD_HUE, "BOD Scan")
            return
        sources = self.source_containers()
        if not sources:
            self.host.set_status("Set at least one available BOD source container before scanning.", BAD_HUE, "BOD Scan")
            return

        self.select_mode(MODE_BULK, False)
        self.bulk_queue = []
        self.bulk_index = 0
        self.bulk_run_active = False
        self.bulk_run_skipped = 0
        self.bulk_points_completed = 0
        self.scan_candidates = []
        self.scan_index = 0
        self.scan_found = 0
        self.scan_rejected = []
        seen = []
        for slot, serial in sources:
            for candidate in self.container_scan_items(slot, serial):
                candidate_serial = self.int_value(candidate.get("serial"), 0)
                if candidate_serial <= 0 or candidate_serial in seen:
                    continue
                seen.append(candidate_serial)
                self.scan_candidates.append(candidate)

        if not self.scan_candidates:
            self.clear_bulk_queue("No items found in the configured BOD sources")
            self.host.set_status("No items were found in the configured BOD source containers.", WARN_HUE, "BOD Scan")
            return

        self.current_bod_serial = 0
        self.current_bulk_record = {}
        self.start_block_reason = "Scan in progress."
        self.match_summary = "Scanning configured BOD sources"
        self.set_current_order("", "", 0, 0, "", 0)
        self.set_bulk_progress(0, 0)
        self.set_artificer_points(0, False)
        self.running = True
        self.workflow_state = STATE_SCANNING
        self.host.set_status(
            "Scanning {0} item{1} from {2} BOD source{3}.".format(
                len(self.scan_candidates),
                "" if len(self.scan_candidates) == 1 else "s",
                len(sources),
                "" if len(sources) == 1 else "s",
            ),
            WARN_HUE,
            "BOD Scan",
        )

    def scan_step(self):
        if self.scan_index >= len(self.scan_candidates):
            self.finish_scan()
            return

        candidate = self.scan_candidates[self.scan_index]
        self.scan_index += 1
        serial = self.int_value(candidate.get("serial"), 0)
        source_serial = self.int_value(candidate.get("source_serial"), 0)
        source_slot = self.int_value(candidate.get("source_slot"), 0)
        item = Items.FindBySerial(serial)
        if not item:
            self.host.set_status(
                "Scan {0}/{1}: an item disappeared; continuing.".format(self.scan_index, len(self.scan_candidates)),
                WARN_HUE,
                "BOD Scan",
            )
            return

        property_lines = self.item_property_lines(item)
        if not self.is_bod_item(item, property_lines):
            self.host.set_status(
                "Scan {0}/{1}: checked source contents; {2} BOD(s) found.".format(self.scan_index, len(self.scan_candidates), self.scan_found),
                LABEL_HUE,
                "BOD Scan",
            )
            return

        self.scan_found += 1
        self.scan_current_serial = serial
        self.scan_current_source = source_serial
        self.scan_current_staged = False
        record = None
        error = ""
        try:
            Misc.Pause(BULK_INSPECT_PAUSE_MS)
            try:
                record = self.inspect_bod_record(serial, source_serial, source_slot)
            except Exception as inspect_error:
                if not self.is_bod_open_failure(inspect_error):
                    raise
                backpack = getattr(Player, "Backpack", None)
                if not backpack or not self.move_bod_to_container(serial, getattr(backpack, "Serial", 0)):
                    raise Exception("order did not open in its source and could not be moved into the backpack for inspection")
                self.scan_current_staged = True
                record = self.inspect_bod_record(serial, source_serial, source_slot)
        except Exception as ex:
            error = str(ex)
        finally:
            try:
                Gumps.CloseGump(self.profile_int("gump", "gump_id", 0))
            except:
                pass

        if self.scan_current_staged and Items.FindBySerial(serial):
            if not self.move_bod_to_container(serial, source_serial):
                self.running = False
                self.workflow_state = STATE_IDLE
                self.scan_rejected.append({"serial": serial, "reason": "could not return the inspected order to its source"})
                self.host.set_status(
                    "Bulk scan stopped: inspected BOD 0x{0:X} remains in the backpack because its source could not be restored.".format(serial),
                    BAD_HUE,
                    "BOD Scan",
                )
                self.scan_current_serial = 0
                self.scan_current_source = 0
                self.scan_current_staged = False
                return

        rejection_reason = ""
        rejection_label = "0x{0:X}".format(serial)
        if record:
            self.load_order_record(record)
            if record.get("block_reason"):
                rejection_reason = str(record.get("block_reason"))
                rejection_label = str(record.get("recipe_name", rejection_label))
                self.scan_rejected.append({"serial": serial, "name": rejection_label, "reason": rejection_reason})
            else:
                self.bulk_queue.append(record)
        else:
            rejection_reason = error or "inspection failed"
            self.scan_rejected.append({"serial": serial, "name": rejection_label, "reason": rejection_reason})

        self.scan_current_serial = 0
        self.scan_current_source = 0
        self.scan_current_staged = False
        if rejection_reason:
            detail = "Skipped {0}: {1}".format(rejection_label, rejection_reason)
            self.match_summary = detail
            try:
                Misc.SendMessage("BOD scan - " + detail, WARN_HUE)
            except:
                pass
            self.host.set_status(
                "Scan {0}/{1}: {2}. {3} ready, {4} skipped.".format(
                    self.scan_index,
                    len(self.scan_candidates),
                    detail,
                    len(self.bulk_queue),
                    len(self.scan_rejected),
                ),
                WARN_HUE,
                "BOD Scan",
            )
        else:
            self.host.set_status(
                "Scan {0}/{1}: {2} BOD(s), {3} ready, {4} skipped.".format(
                    self.scan_index,
                    len(self.scan_candidates),
                    self.scan_found,
                    len(self.bulk_queue),
                    len(self.scan_rejected),
                ),
                GOOD_HUE,
                "BOD Scan",
            )

    def finish_scan(self):
        self.bulk_queue.sort(key=self.bulk_sort_key)
        self.bulk_index = 0
        self.bulk_run_active = False
        self.bulk_run_skipped = 0
        self.bulk_points_completed = 0
        self.running = False
        self.workflow_state = STATE_IDLE
        self.set_bulk_progress(0, len(self.bulk_queue))
        if self.bulk_queue:
            self.load_order_record(self.bulk_queue[0])
            self.start_block_reason = ""
            self.match_summary = "Bulk queue ready: {0} order(s)".format(len(self.bulk_queue))
            self.host.set_status(
                "Scan complete: {0} BOD(s) found, {1} ready, {2} skipped. Click Start Fill.".format(
                    self.scan_found,
                    len(self.bulk_queue),
                    len(self.scan_rejected),
                ),
                GOOD_HUE,
                "BOD Ready",
            )
        else:
            self.current_bulk_record = {}
            self.current_bod_serial = 0
            self.matched_module_id = ""
            self.matched_category_id = ""
            self.matched_recipe_id = ""
            self.job_resource_choices = {}
            self.exceptional_required = False
            self.skill_warning = ""
            self.start_block_reason = "scan found no eligible BODs"
            if self.scan_rejected:
                first_rejection = self.scan_rejected[0]
                self.match_summary = "All skipped: {0}".format(first_rejection.get("reason", "unknown reason"))
            else:
                self.match_summary = "No eligible orders"
            self.set_current_order("", "", 0, 0, "", 0)
            self.set_artificer_points(0, False)
            self.host.set_status(
                "Scan complete: {0} BOD(s) found, but all {1} were skipped.".format(self.scan_found, len(self.scan_rejected)),
                WARN_HUE,
                "BOD Filter",
            )
        self.scan_candidates = []

    def return_record_to_source(self, record):
        serial = self.int_value(record.get("serial"), 0)
        item = Items.FindBySerial(serial)
        if not item:
            return True
        source_serial = self.int_value(record.get("source_serial"), 0)
        if source_serial <= 0 or not self.host.valid_item(source_serial):
            return False
        return self.move_bod_to_container(serial, source_serial)

    def start_bulk_run(self):
        if not self.bulk_queue:
            self.host.set_status("Scan Orders before starting Bulk mode.", BAD_HUE, "BOD Ready")
            return
        if self.host_craft_job_api_version() < 6:
            self.host.set_status("Stop and restart FrogCraftingCore.py to load FCC 1.0 and its crafting-focus bridge.", BAD_HUE, "BOD Start")
            return
        if self.host.craft_bag_serial() <= 0:
            self.host.set_status("Enable and set an FCC Craft Bag before starting Bulk mode.", BAD_HUE, "BOD Start")
            return

        self.bulk_index = 0
        self.bulk_run_active = True
        self.bulk_run_skipped = 0
        self.bulk_points_completed = 0
        self.running = True
        self.workflow_state = STATE_BULK_PREPARE
        self.set_bulk_progress(0, len(self.bulk_queue))
        self.host.set_status("Bulk fill starting with {0} queued BOD(s).".format(len(self.bulk_queue)), GOOD_HUE, "BOD Bulk")

    def prepare_bulk_order(self):
        if self.bulk_index >= len(self.bulk_queue):
            self.finish_bulk_run()
            return

        queued = self.bulk_queue[self.bulk_index]
        serial = self.int_value(queued.get("serial"), 0)
        item = Items.FindBySerial(serial)
        if not item:
            self.bulk_run_skipped += 1
            self.bulk_index += 1
            self.workflow_state = STATE_BULK_PREPARE
            self.host.set_status("Queued BOD disappeared; skipping to the next order.", WARN_HUE, "BOD Bulk")
            return

        try:
            Misc.Pause(BULK_INSPECT_PAUSE_MS)
            try:
                refreshed = self.inspect_bod_record(
                    serial,
                    queued.get("source_serial", 0),
                    queued.get("source_slot", 0),
                )
            except Exception as inspect_error:
                if not self.is_bod_open_failure(inspect_error):
                    raise
                backpack = getattr(Player, "Backpack", None)
                if not backpack or not self.move_bod_to_container(serial, getattr(backpack, "Serial", 0)):
                    raise Exception("order did not open in its source and could not be moved into the backpack for filling")
                refreshed = self.inspect_bod_record(
                    serial,
                    queued.get("source_serial", 0),
                    queued.get("source_slot", 0),
                )
        except Exception as ex:
            self.return_record_to_source(queued)
            self.bulk_run_skipped += 1
            self.bulk_index += 1
            self.host.set_status("Queued BOD recheck failed and was skipped: " + str(ex), WARN_HUE, "BOD Bulk")
            return
        finally:
            try:
                Gumps.CloseGump(self.profile_int("gump", "gump_id", 0))
            except:
                pass

        if refreshed.get("block_reason"):
            self.return_record_to_source(refreshed)
            self.bulk_run_skipped += 1
            self.bulk_index += 1
            self.host.set_status("Queued BOD no longer passes filters: " + str(refreshed.get("block_reason")), WARN_HUE, "BOD Bulk")
            return

        self.bulk_queue[self.bulk_index] = refreshed
        self.load_order_record(refreshed)
        self.start_block_reason = ""
        self.host.set_status(
            "Bulk BOD {0}/{1}: preparing {2}.".format(self.bulk_index + 1, len(self.bulk_queue), self.current_item_name),
            GOOD_HUE,
            "BOD Bulk",
        )
        self.begin_current_fill()

    def return_bulk_order(self):
        record = self.current_bulk_record
        if record and not self.return_record_to_source(record):
            self.running = False
            self.bulk_run_active = False
            self.workflow_state = STATE_IDLE
            self.host.set_status(
                "Bulk fill stopped: completed BOD 0x{0:X} could not be returned to its source and remains in the backpack.".format(self.current_bod_serial),
                BAD_HUE,
                "BOD Bulk",
            )
            return

        self.bods_completed += 1
        if self.artificer_points_known:
            self.bulk_points_completed += self.artificer_points
        self.bulk_index += 1
        if self.bulk_index >= len(self.bulk_queue):
            self.finish_bulk_run()
            return
        self.workflow_state = STATE_BULK_PREPARE
        self.host.set_status(
            "Bulk progress: {0}/{1} filled; preparing the next grouped order.".format(self.bods_completed, self.bods_total),
            GOOD_HUE,
            "BOD Bulk",
        )

    def finish_bulk_run(self):
        self.running = False
        self.bulk_run_active = False
        self.workflow_state = STATE_IDLE
        points_text = " Potential turn-in points: {0}.".format(self.bulk_points_completed) if self.bulk_points_completed > 0 else ""
        self.host.set_status(
            "Bulk complete: {0}/{1} BOD(s) filled; {2} skipped during the run.{3}".format(
                self.bods_completed,
                self.bods_total,
                self.bulk_run_skipped,
                points_text,
            ),
            GOOD_HUE if self.bods_completed > 0 else WARN_HUE,
            "BOD Bulk Complete",
        )

    def start_craft_pass(self):
        if self.host_craft_job_api_version() < 6:
            raise Exception("FCC crafting-focus bridge is unavailable; stop and restart FrogCraftingCore.py to load FCC 1.0")
        remaining = self.amount_to_craft - self.amount_crafted
        if remaining <= 0:
            self.finish_fill()
            return
        max_passes = max(1, self.policy_int("max_passes", 20))
        if self.fill_passes >= max_passes:
            raise Exception("stopped after {0} fill passes with {1} item(s) still needed".format(max_passes, remaining))
        if self.craft_bag_output_items():
            raise Exception("requested-item leftovers remain in the Craft Bag before the next craft pass")

        self.job_initial_finished = self.amount_crafted
        self.job_remaining = remaining
        started, start_message = self.host.begin_craft_job(self.plugin_id, self.matched_module_id, self.matched_category_id, self.matched_recipe_id, self.job_remaining, self.job_resource_choices, "none")
        if not started:
            raise Exception(start_message)

        self.fill_passes += 1
        self.running = True
        self.workflow_state = STATE_CRAFTING
        message = "Pass {0}: crafting {1} remaining {2}(s).".format(self.fill_passes, self.job_remaining, self.current_item_name)
        if self.skill_warning:
            message = "Warning: {0}; continuing. {1}".format(self.skill_warning, message)
        self.host.set_status(message, WARN_HUE if self.skill_warning else GOOD_HUE, "BOD Craft")

    def start_fill(self):
        if self.running:
            self.cancel_fill()
            return
        if self.mode == MODE_BULK:
            self.start_bulk_run()
            return
        self.begin_current_fill()

    def begin_current_fill(self):
        if self.start_block_reason:
            self.host.set_status("BOD cannot start: " + self.start_block_reason, BAD_HUE, "BOD Ready")
            return
        if not self.current_bod_serial or not self.matched_module_id or not self.matched_recipe_id:
            self.host.set_status("Target and inspect a BOD before starting.", BAD_HUE, "BOD Ready")
            return
        if self.host_craft_job_api_version() < 6:
            message = "An older FCC core is still running. Stop and restart FrogCraftingCore.py to load FCC 1.0; Reload only refreshes data and plugins."
            self.host.overhead("Restart FrogCraftingCore.py to load FCC 1.0.", WARN_HUE)
            self.host.set_status(message, BAD_HUE, "BOD Start")
            return

        gump_id = self.profile_int("gump", "gump_id", 0)
        try:
            if not self.open_selected_bod():
                raise Exception("the inspected BOD is no longer available in the backpack")
            refreshed_lines = self.bod_gump_lines()
            refreshed = self.parse_bod_gump(refreshed_lines)
            if self.int_value(refreshed.get("requested_item_id"), 0) != self.current_item_id:
                raise Exception("the inspected BOD now reports a different requested item")
            if self.int_value(refreshed.get("amount_to_make"), 0) != self.amount_to_craft:
                raise Exception("the inspected BOD now reports a different requested amount")

            self.last_gump_lines = refreshed_lines
            self.amount_crafted = self.int_value(refreshed.get("amount_finished"), self.amount_crafted)
            if self.mode == MODE_SINGLE:
                self.set_bulk_progress(1 if self.amount_crafted >= self.amount_to_craft else 0, 1)
            if self.amount_crafted >= self.amount_to_craft:
                raise Exception("this BOD already reports all requested items finished")
            if self.host.craft_bag_serial() <= 0:
                raise Exception("enable and set an FCC Craft Bag before filling")
            if self.craft_bag_output_items():
                raise Exception("remove existing requested items from the Craft Bag before filling")

            self.fill_passes = 0
            self.zero_accept_passes = 0
            self.accepted_total = 0
            self.recycled_total = 0
            self.discarded_total = 0
            self.recycle_queue = []
            self.recycle_retry_count = 0
            self.recycle_action_failures = 0
            self.recycle_container_exhausted = False
            self.job_stackable = self.stackable_for_recipe(self.matched_module_id, self.matched_recipe_id)
            if self.skill_warning:
                self.host.overhead("Warning: " + self.skill_warning + ". Continuing.", WARN_HUE)
            self.start_craft_pass()
        except Exception as ex:
            self.host.end_craft_job(self.plugin_id, True)
            if self.bulk_run_active and self.current_bulk_record:
                self.return_record_to_source(self.current_bulk_record)
            self.running = False
            self.workflow_state = STATE_IDLE
            self.bulk_run_active = False
            self.host.set_status("BOD start stopped: " + str(ex), BAD_HUE, "BOD Start")
        finally:
            try:
                Gumps.CloseGump(gump_id)
            except:
                pass
            self.host.mark_dirty()

    def finish_fill(self):
        self.amount_crafted = self.amount_to_craft
        self.recycle_queue = []
        self.recycle_retry_count = 0
        self.recycle_action_failures = 0
        self.recycle_container_exhausted = False
        if self.bulk_run_active:
            self.running = True
            self.workflow_state = STATE_BULK_RETURN
            self.host.set_status(
                "BOD filled: {0}; returning it to source {1}.".format(self.current_item_name, self.current_source_slot),
                GOOD_HUE,
                "BOD Bulk",
            )
            return

        self.bods_completed = 1
        self.running = False
        self.workflow_state = STATE_IDLE
        message = "BOD filled: {0}; accepted {1}, recycled {2}, trashed {3} reject(s).".format(
            self.current_item_name,
            self.accepted_total,
            self.recycled_total,
            self.discarded_total,
        )
        self.host.set_status(message, GOOD_HUE, "BOD Complete")

    def begin_post_combine_cleanup(self, next_action, message=""):
        starter = getattr(self.host, "begin_craft_cleanup", None)
        if not callable(starter):
            raise Exception("FCC cleanup bridge is unavailable; restart FrogCraftingCore.py")
        started, cleanup_message = starter(self.plugin_id)
        if not started:
            raise Exception(cleanup_message)
        self.post_cleanup_action = str(next_action)
        self.post_cleanup_message = str(message or "")
        self.running = True
        self.workflow_state = STATE_CLEANUP

    def post_combine_cleanup_step(self):
        checker = getattr(self.host, "craft_cleanup_active", None)
        if callable(checker) and bool(checker(self.plugin_id)):
            return

        next_action = self.post_cleanup_action
        message = self.post_cleanup_message
        self.post_cleanup_action = ""
        self.post_cleanup_message = ""
        if next_action == "finish":
            self.finish_fill()
            return
        if next_action == "craft":
            try:
                self.start_craft_pass()
            except Exception as ex:
                self.cancel_fill("BOD restart stopped after cleanup: " + str(ex), BAD_HUE)
            return
        if next_action == "stop":
            self.cancel_fill(message or "BOD fill stopped after post-combine cleanup.", BAD_HUE)
            return
        self.cancel_fill("BOD cleanup finished without a continuation action.", BAD_HUE)

    def queue_rejected_output(self, items):
        self.recycle_queue = [self.int_value(getattr(item, "Serial", 0), 0) for item in items]
        self.recycle_queue = [serial for serial in self.recycle_queue if serial > 0]
        self.recycle_retry_count = 0
        self.recycle_action_failures = 0
        self.recycle_container_exhausted = False
        self.workflow_state = STATE_RECYCLING
        self.host.set_status(
            "The BOD accepted {0} item(s); recycling {1} rejected {2}(s).".format(
                max(0, self.amount_crafted - self.job_initial_finished),
                len(self.recycle_queue),
                self.current_item_name,
            ),
            WARN_HUE,
            "BOD Recycle",
        )

    def trash_unrecyclable_output(self, serial, recycle_message):
        disposer = getattr(self.host, "trash_craft_bag_item", None)
        if not callable(disposer):
            self.cancel_fill(
                "BOD reject recycling stopped: {0} The rejected output remains in the Craft Bag; restart FrogCraftingCore.py to load FCC 1.0.".format(recycle_message),
                BAD_HUE,
            )
            return

        state, message = disposer(self.plugin_id, serial, self.observed_output_item_id or self.current_item_id)
        if state == "complete":
            if self.recycle_queue and self.recycle_queue[0] == serial:
                self.recycle_queue.pop(0)
            self.recycle_retry_count = 0
            self.discarded_total += 1
            self.host.set_status(
                "Recycle limit reached. {0} {1} rejected item(s) remain.".format(message, len(self.recycle_queue)),
                WARN_HUE,
                "BOD Trash",
            )
            return

        self.cancel_fill(
            "BOD reject recycling stopped: {0} {1} The rejected output was left in the Craft Bag.".format(recycle_message, message),
            BAD_HUE,
        )

    def recycle_rejected_container(self):
        if self.recycle_container_exhausted:
            self.trash_unrecyclable_output(self.recycle_queue[0], "Bag-wide recycling left this item intact.")
            return

        recycler = getattr(self.host, "recycle_craft_bag_contents", None)
        if not callable(recycler):
            self.cancel_fill("FCC bag-wide recycle bridge is unavailable; restart FrogCraftingCore.py to load FCC 1.0. Rejected items remain in the Craft Bag.", BAD_HUE)
            return
        before = list(self.recycle_queue)
        state, message, remaining = recycler(self.plugin_id, self.matched_module_id, self.matched_recipe_id, before, self.observed_output_item_id or self.current_item_id)
        if not self.running:
            return
        if state in ("complete", "leftovers"):
            remaining = [self.int_value(serial, 0) for serial in remaining]
            if len(remaining) != len(set(remaining)) or any(serial not in before for serial in remaining):
                self.cancel_fill("Safety stop: bag-wide recycle returned an unexpected rejected-item list.", BAD_HUE)
                return
            self.recycle_queue = remaining
            self.recycled_total += len(before) - len(remaining)
            self.recycle_retry_count += 1
            self.recycle_action_failures = 0
            if not remaining:
                self.host.set_status("{0} All rejected output was recycled.".format(message), GOOD_HUE, "BOD Recycle")
                return
            max_attempts = max(1, self.policy_int("recycle_attempts", self.policy_int("recycle_retries", 3)))
            self.recycle_container_exhausted = self.recycle_retry_count >= max_attempts
            self.host.set_status(
                "{0} {1}".format(message, "Moving the leftovers to configured trash." if self.recycle_container_exhausted else "Retrying bag-wide recycle."),
                WARN_HUE,
                "BOD Recycle",
            )
            return
        if state == "progress":
            self.host.set_status(message, WARN_HUE, "BOD Recycle")
            return
        if state == "retry":
            self.recycle_action_failures += 1
            max_failures = max(1, self.policy_int("recycle_attempts", self.policy_int("recycle_retries", 3)))
            if self.recycle_action_failures < max_failures:
                self.host.set_status("Recycle action retry {0}/{1}: {2}".format(self.recycle_action_failures, max_failures, message), WARN_HUE, "BOD Recycle")
                return
            self.cancel_fill("BOD recycling could not send the bag-wide action: {0} Rejected items remain in the Craft Bag.".format(message), BAD_HUE)
            return
        self.cancel_fill("BOD bag-wide recycling stopped: {0} Rejected items remain in the Craft Bag.".format(message), WARN_HUE if state == "cancelled" else BAD_HUE)

    def recycle_rejected_output(self):
        if not self.recycle_queue:
            max_zero_passes = max(1, self.policy_int("max_zero_accept_passes", 3))
            if self.amount_crafted >= self.amount_to_craft:
                try:
                    self.begin_post_combine_cleanup("finish")
                except Exception as ex:
                    self.cancel_fill("BOD cleanup stopped: " + str(ex), BAD_HUE)
                return
            if not self.exceptional_required and self.zero_accept_passes >= max_zero_passes:
                try:
                    self.begin_post_combine_cleanup(
                        "stop",
                        "BOD stopped after {0} pass(es) accepted no items; rejected output was processed.".format(max_zero_passes),
                    )
                except Exception as ex:
                    self.cancel_fill("BOD cleanup stopped: " + str(ex), BAD_HUE)
                return
            try:
                self.begin_post_combine_cleanup("craft")
            except Exception as ex:
                self.cancel_fill("BOD cleanup stopped: " + str(ex), BAD_HUE)
            return

        if not self.job_stackable:
            self.recycle_rejected_container()
            return

        serial = self.recycle_queue[0]
        item = Items.FindBySerial(serial)
        if not item:
            self.recycle_queue.pop(0)
            self.recycle_retry_count = 0
            return

        state, message = self.host.recycle_craft_bag_item(
            self.plugin_id,
            self.matched_module_id,
            self.matched_recipe_id,
            serial,
            self.observed_output_item_id or self.current_item_id,
        )
        if not self.running:
            return
        if state == "complete":
            self.recycle_queue.pop(0)
            self.recycle_retry_count = 0
            self.recycled_total += 1
            self.host.set_status(
                "{0} {1} rejected item(s) remain to recycle.".format(message, len(self.recycle_queue)),
                WARN_HUE,
                "BOD Recycle",
            )
            return
        if state == "progress":
            self.host.set_status(message, WARN_HUE, "BOD Recycle")
            return
        if state == "cancelled":
            self.cancel_fill(message, WARN_HUE)
            return
        if state == "retry":
            self.recycle_retry_count += 1
            max_attempts = max(1, self.policy_int("recycle_attempts", self.policy_int("recycle_retries", 3)))
            if self.recycle_retry_count < max_attempts:
                self.host.set_status(
                    "Recycle attempt {0}/{1} failed; retrying: {2}".format(self.recycle_retry_count, max_attempts, message),
                    WARN_HUE,
                    "BOD Recycle",
                )
                return
            self.trash_unrecyclable_output(serial, message)
            return
        self.cancel_fill("BOD reject recycling stopped: " + str(message), BAD_HUE)

    def combine_crafted_output(self):
        output_items = []
        output_count = 0
        for attempt in range(4):
            output_items = self.craft_bag_output_items()
            output_count = self.output_item_count(output_items)
            if output_count == self.job_remaining:
                break
            if attempt < 3:
                Misc.Pause(400)
        if output_count != self.job_remaining:
            raise Exception("Craft Bag has {0}/{1} isolated {2} output(s); expected BOD graphic 0x{3:X}. Verify the Craft Bag and recipe output name/ItemID.".format(output_count, self.job_remaining, self.current_item_name, self.current_item_id))
        output_ids = set(self.int_value(getattr(item, "ItemID", 0), 0) for item in output_items)
        if len(output_ids) != 1 or 0 in output_ids:
            raise Exception("Craft Bag output uses mixed or unknown item graphics; refusing unsafe BOD combine")
        self.observed_output_item_id = output_ids.pop()

        if not self.open_selected_bod():
            raise Exception("the selected BOD gump did not reopen")

        gump_id = self.profile_int("gump", "gump_id", 0)
        Target.Cancel()
        if self.job_stackable:
            if len(output_items) != 1:
                raise Exception("stackable output is split across more than one stack")
            button_id = self.profile_int("gump", "combine_item_button", 0)
            target_serial = int(output_items[0].Serial)
        else:
            button_id = self.profile_int("gump", "combine_container_button", 0)
            target_serial = self.host.craft_bag_serial()
        if button_id <= 0 or target_serial <= 0:
            raise Exception("the configured BOD combine action is invalid")

        Gumps.SendAction(gump_id, button_id)
        if not bool(Target.WaitForTarget(2500, False)) and not bool(Target.HasTarget()):
            raise Exception("the BOD combine target cursor did not appear")
        Target.TargetExecute(target_serial)
        Misc.Pause(750)

        refreshed = None
        observed_finished = None
        last_error = "the BOD combine result was not ready"
        settle_attempts = max(1, self.policy_int("combine_settle_attempts", 4))
        for attempt in range(settle_attempts):
            remaining_items = self.craft_bag_output_items()
            output_remaining = self.output_item_count(remaining_items)
            if not self.open_selected_bod():
                if output_remaining == 0:
                    self.accepted_total += self.job_remaining
                    self.begin_post_combine_cleanup("finish")
                    return
                last_error = "the BOD did not reopen and {0} crafted item(s) remain".format(output_remaining)
            else:
                refreshed_lines = self.bod_gump_lines()
                try:
                    candidate = self.parse_bod_gump(refreshed_lines)
                except Exception as ex:
                    last_error = "the BOD result was not readable: " + str(ex)
                else:
                    if self.int_value(candidate.get("requested_item_id"), 0) != self.current_item_id:
                        raise Exception("the reopened BOD requested a different item graphic")
                    new_finished = self.int_value(candidate.get("amount_finished"), self.amount_crafted)
                    if new_finished < self.job_initial_finished or new_finished > self.amount_to_craft:
                        raise Exception("the reopened BOD reported an invalid finished amount")
                    observed_finished = new_finished
                    accepted = new_finished - self.job_initial_finished
                    expected_rejected = self.job_remaining - accepted
                    if output_remaining == expected_rejected:
                        refreshed = candidate
                        self.last_gump_lines = refreshed_lines
                        break
                    last_error = "BOD progress and isolated leftovers disagree: expected {0}, found {1}".format(expected_rejected, output_remaining)
            if attempt < settle_attempts - 1:
                Gumps.CloseGump(gump_id)
                Misc.Pause(500)

        if refreshed is None:
            if not self.job_stackable and output_remaining == self.job_remaining and (observed_finished is None or observed_finished == self.job_initial_finished):
                if not bool(self.profile_value("fill_policy", "recycle_rejected_items", True)):
                    raise Exception("the BOD retained all crafted items; automatic recycling is disabled")
                self.amount_crafted = self.job_initial_finished
                self.zero_accept_passes += 1
                Gumps.CloseGump(gump_id)
                self.queue_rejected_output(remaining_items)
                return
            raise Exception(last_error)

        new_finished = self.int_value(refreshed.get("amount_finished"), self.amount_crafted)
        accepted = new_finished - self.job_initial_finished

        self.amount_crafted = new_finished
        self.accepted_total += accepted
        if accepted > 0:
            self.zero_accept_passes = 0
        else:
            self.zero_accept_passes += 1
        Gumps.CloseGump(gump_id)

        if remaining_items:
            if not bool(self.profile_value("fill_policy", "recycle_rejected_items", True)):
                raise Exception("the BOD rejected {0} item(s); automatic recycling is disabled".format(output_remaining))
            self.queue_rejected_output(remaining_items)
            return
        if self.amount_crafted >= self.amount_to_craft:
            self.begin_post_combine_cleanup("finish")
            return
        if accepted <= 0:
            raise Exception("the BOD accepted no items, but no matching output remained to recycle")
        self.begin_post_combine_cleanup("craft")

    def cancel_fill(self, message="BOD fill cancelled.", hue=WARN_HUE):
        if self.workflow_state == STATE_SCANNING:
            scanned = self.scan_index
            total = len(self.scan_candidates)
            self.finish_scan()
            self.host.set_status(
                "Bulk scan stopped at {0}/{1}; {2} eligible BOD(s) remain queued.".format(scanned, total, len(self.bulk_queue)),
                WARN_HUE,
                "BOD Scan",
            )
            self.host.mark_dirty()
            return

        self.host.end_craft_job(self.plugin_id, True)
        if self.bulk_run_active and self.current_bulk_record:
            self.return_record_to_source(self.current_bulk_record)
        self.running = False
        self.bulk_run_active = False
        self.workflow_state = STATE_IDLE
        self.recycle_queue = []
        self.recycle_retry_count = 0
        self.recycle_action_failures = 0
        self.recycle_container_exhausted = False
        self.post_cleanup_action = ""
        self.post_cleanup_message = ""
        self.host.set_status(message, hue, "BOD Fill")
        self.host.mark_dirty()

    def live_amount_crafted(self):
        if self.running and self.workflow_state == STATE_CRAFTING:
            status = self.host.craft_job_status(self.plugin_id)
            completed = max(0, self.int_value(status.get("completed"), 0))
            return min(self.amount_to_craft, self.job_initial_finished + completed)
        return self.amount_crafted

    def progress_percent(self, amount_crafted=None):
        if self.amount_to_craft <= 0:
            return 0.0
        completed = self.amount_crafted if amount_crafted is None else amount_crafted
        value = 100.0 * float(completed) / float(self.amount_to_craft)
        return max(0.0, min(100.0, value))

    def current_value_hue(self):
        return GOOD_HUE if self.current_bod_type else DIM_HUE

    def set_current_order(self, bod_type, material, amount_to_craft, amount_crafted=0, item_name="", item_id=0):
        self.current_bod_type = str(bod_type or "")
        self.current_material = str(material or "")
        self.current_item_name = str(item_name or "")
        self.current_item_id = max(0, int(item_id))
        self.observed_output_item_id = 0
        self.amount_to_craft = max(0, int(amount_to_craft))
        self.amount_crafted = max(0, int(amount_crafted))
        self.host.mark_dirty()

    def set_bulk_progress(self, completed, total):
        self.bods_completed = max(0, int(completed))
        self.bods_total = max(0, int(total))
        self.host.mark_dirty()

    def set_artificer_points(self, points, known=True):
        self.artificer_points = max(0, int(points))
        self.artificer_points_known = bool(known)
        self.host.mark_dirty()

    def render_filters(self, gd, x, y, width, height):
        Gumps.AddBackground(gd, x, y, width, height, 3000)
        Gumps.AddAlphaRegion(gd, x, y, width, height)
        Gumps.AddLabel(gd, x + 12, y + 8, TITLE_HUE, "BULK FILTERS")
        Gumps.AddLabel(gd, x + 125, y + 8, DIM_HUE, "YES orders enter the next scanned queue")
        self.host.add_button(gd, x + width - 115, y + 7, self.button_id(BTN_FILTER_BACK), "Back", GOOD_HUE)

        entries = self.bulk_filter_entries()
        page_count = max(1, (len(entries) + FILTER_PAGE_SIZE - 1) // FILTER_PAGE_SIZE)
        self.filter_page = max(0, min(self.filter_page, page_count - 1))
        start = self.filter_page * FILTER_PAGE_SIZE
        visible = entries[start:start + FILTER_PAGE_SIZE]
        self.filter_button_map = {}

        Gumps.AddBackground(gd, x + 10, y + 32, width - 20, 242, 3000)
        Gumps.AddAlphaRegion(gd, x + 10, y + 32, width - 20, 242)
        Gumps.AddLabel(gd, x + 20, y + 39, TITLE_HUE, "ALLOW / FILTER")
        Gumps.AddLabel(gd, x + 330, y + 39, TITLE_HUE, "ALLOW / FILTER")

        for index, entry in enumerate(visible):
            column = index // FILTER_ROWS
            row = index % FILTER_ROWS
            column_x = x + 20 + column * 310
            local_button = BTN_FILTER_ROW_BASE + index
            self.filter_button_map[local_button] = entry
            enabled = self.bulk_filter_enabled(entry.get("kind", ""), entry.get("key", ""))
            row_y = y + 60 + row * 19
            self.host.add_button(
                gd,
                column_x,
                row_y,
                self.button_id(local_button),
                "YES" if enabled else "NO",
                GOOD_HUE if enabled else BAD_HUE,
            )
            filter_label = "{0}: {1}".format(str(entry.get("kind", "")).title(), entry.get("label", ""))
            Gumps.AddLabel(gd, column_x + 72, row_y + 1, LABEL_HUE, self.host.short_text(filter_label, 28))

        self.host.add_button(gd, x + 20, y + 282, self.button_id(BTN_FILTER_PREV), "Previous", LABEL_HUE)
        Gumps.AddLabel(gd, x + 145, y + 283, DIM_HUE, "Page {0}/{1}".format(self.filter_page + 1, page_count))
        self.host.add_button(gd, x + 245, y + 282, self.button_id(BTN_FILTER_NEXT), "Next", LABEL_HUE)
        Gumps.AddLabel(gd, x + 355, y + 283, DIM_HUE, "Recipe exceptions: bod_filler.json")

    def render(self, gd, x, y, width, height):
        if self.page == PAGE_FILTERS:
            self.render_filters(gd, x, y, width, height)
            return

        Gumps.AddBackground(gd, x, y, width, height, 3000)
        Gumps.AddAlphaRegion(gd, x, y, width, height)
        Gumps.AddLabel(gd, x + 12, y + 8, TITLE_HUE, "BOD FILLER")
        Gumps.AddLabel(gd, x + 112, y + 8, DIM_HUE, "Unchained order scanner and completion queue")

        Gumps.AddBackground(gd, x + 10, y + 32, width - 20, 124, 3000)
        Gumps.AddAlphaRegion(gd, x + 10, y + 32, width - 20, 124)
        Gumps.AddLabel(gd, x + 20, y + 39, TITLE_HUE, "CURRENT ORDER")
        value_hue = self.current_value_hue()
        displayed_crafted = self.live_amount_crafted()
        bod_type = self.current_bod_type if self.current_bod_type else "No BOD selected"
        material = self.current_material if self.current_material else "--"
        Gumps.AddLabel(gd, x + 20, y + 60, LABEL_HUE, "BOD Type:")
        Gumps.AddLabel(gd, x + 115, y + 60, value_hue, self.host.short_text(bod_type, 28))
        Gumps.AddLabel(gd, x + 335, y + 60, LABEL_HUE, "Material:")
        Gumps.AddLabel(gd, x + 415, y + 60, value_hue, self.host.short_text(material, 23))
        Gumps.AddLabel(gd, x + 20, y + 82, LABEL_HUE, "Amount to Craft / Crafted:")
        Gumps.AddLabel(gd, x + 225, y + 82, value_hue, "{0} / {1}".format(self.amount_to_craft, displayed_crafted))
        Gumps.AddLabel(gd, x + 335, y + 82, LABEL_HUE, "Progress:")
        Gumps.AddLabel(gd, x + 415, y + 82, value_hue, "{0:.1f}%".format(self.progress_percent(displayed_crafted)))
        if self.workflow_state == STATE_SCANNING:
            bulk_text = "Scan {0}/{1} | {2} ready".format(self.scan_index, len(self.scan_candidates), len(self.bulk_queue))
        elif self.mode == MODE_BULK:
            bulk_text = "{0} of {1} BODs completed".format(self.bods_completed, self.bods_total)
        else:
            bulk_text = "Single BOD mode"
        points_text = "{0} on turn-in".format(self.artificer_points) if self.artificer_points_known else "Unknown"
        Gumps.AddLabel(gd, x + 20, y + 105, LABEL_HUE, "Bulk Progress:")
        Gumps.AddLabel(gd, x + 135, y + 105, value_hue, bulk_text)
        Gumps.AddLabel(gd, x + 380, y + 105, LABEL_HUE, "BOD Points:")
        Gumps.AddLabel(gd, x + 510, y + 105, GOOD_HUE if self.artificer_points_known else DIM_HUE, points_text)
        request_text = "Requested: {0}".format(self.current_item_name) if self.current_item_name else self.match_summary
        if self.current_item_id > 0:
            request_text += " (0x{0:04X})".format(self.current_item_id)
        if self.exceptional_required:
            request_text += " | Exceptional"
        Gumps.AddLabel(gd, x + 20, y + 133, DIM_HUE, self.host.short_text(request_text, 62))
        self.host.add_button(gd, x + 535, y + 128, self.button_id(BTN_OPEN_BOD), "Open BOD", GOOD_HUE if self.current_bod_serial > 0 else DIM_HUE)

        Gumps.AddBackground(gd, x + 10, y + 162, width - 20, 66, 3000)
        Gumps.AddAlphaRegion(gd, x + 10, y + 162, width - 20, 66)
        Gumps.AddLabel(gd, x + 20, y + 169, TITLE_HUE, "BOD SOURCES")
        self.host.add_button(gd, x + 20, y + 192, self.button_id(BTN_SET_CHEST_ONE), "Set Chest 1")
        Gumps.AddLabel(gd, x + 145, y + 193, LABEL_HUE, self.host.short_text(self.host.item_label(self.chest_one, "Chest 1 not set"), 24))
        self.host.add_button(gd, x + 335, y + 192, self.button_id(BTN_SET_CHEST_TWO), "Set Chest 2")
        Gumps.AddLabel(gd, x + 460, y + 193, LABEL_HUE, self.host.short_text(self.host.item_label(self.chest_two, "Chest 2 not set"), 22))

        Gumps.AddBackground(gd, x + 10, y + 234, width - 20, 74, 3000)
        Gumps.AddAlphaRegion(gd, x + 10, y + 234, width - 20, 74)
        Gumps.AddLabel(gd, x + 20, y + 241, TITLE_HUE, "MODE & CONTROLS")
        mode_label = "Mode: Bulk" if self.mode == MODE_BULK else "Mode: Single"
        if self.workflow_state == STATE_SCANNING:
            start_label = "Stop Scan"
        elif self.running:
            start_label = "Stop Fill"
        elif self.mode == MODE_BULK:
            start_label = "Start Bulk"
        else:
            start_label = "Start Fill"
        self.host.add_button(gd, x + 20, y + 264, self.button_id(BTN_MODE_TOGGLE), mode_label, GOOD_HUE)
        self.host.add_button(gd, x + 145, y + 264, self.button_id(BTN_TARGET_BOD), "Target BOD", GOOD_HUE)
        self.host.add_button(gd, x + 260, y + 264, self.button_id(BTN_START_FILL), start_label, WARN_HUE if self.running else GOOD_HUE)
        self.host.add_button(gd, x + 365, y + 264, self.button_id(BTN_SCAN), "Scan Orders", WARN_HUE)
        self.host.add_button(gd, x + 20, y + 290, self.button_id(BTN_FILTERS), "Bulk Filters", LABEL_HUE)
        Gumps.AddLabel(gd, x + 145, y + 292, DIM_HUE, "Stackable: Potions and spell scrolls; other crafts default No")

    def set_chest(self, slot):
        serial = self.host.target_container("Target BOD chest {0}.".format(slot))
        if serial <= 0:
            self.host.set_status("BOD chest {0} selection cancelled or invalid.".format(slot), WARN_HUE, "BOD Setup")
            return
        if slot == 1:
            self.chest_one = serial
            self.host.write_int("bod_filler_chest_one", serial)
        else:
            self.chest_two = serial
            self.host.write_int("bod_filler_chest_two", serial)
        self.clear_bulk_queue("BOD source changed; scan again")
        self.host.set_status("BOD chest {0} saved.".format(slot), GOOD_HUE, "BOD Setup")

    def select_mode(self, mode, announce=True):
        self.mode = mode
        self.host.write_text("bod_filler_mode", mode)
        if mode == MODE_BULK:
            if self.bulk_queue:
                self.load_order_record(self.bulk_queue[0])
                self.start_block_reason = ""
                self.set_bulk_progress(0, len(self.bulk_queue))
            else:
                self.clear_bulk_queue("Scan Orders to build a bulk queue")
        else:
            self.current_bulk_record = {}
            self.current_source_serial = 0
            self.current_source_slot = 0
            self.current_bod_serial = 0
            self.matched_module_id = ""
            self.matched_category_id = ""
            self.matched_recipe_id = ""
            self.job_resource_choices = {}
            self.exceptional_required = False
            self.skill_warning = ""
            self.start_block_reason = "Target and inspect a BOD."
            self.match_summary = "No order inspected"
            self.set_current_order("", "", 0, 0, "", 0)
            self.set_bulk_progress(0, 1)
            self.set_artificer_points(0, False)
        if announce:
            self.host.set_status("BOD Filler mode: " + mode.title() + ".", GOOD_HUE, "BOD Setup")

    def toggle_mode(self):
        if self.running:
            self.host.set_status("Stop the active BOD fill before changing mode.", BAD_HUE, "BOD Fill")
            return
        self.select_mode(MODE_SINGLE if self.mode == MODE_BULK else MODE_BULK)

    def target_bod(self):
        if self.data_error:
            self.host.set_status("BOD data error: " + self.data_error, BAD_HUE, "BOD Inspect")
            return

        self.select_mode(MODE_SINGLE, False)
        self.host.set_status("Target a BOD in your backpack.", WARN_HUE, "BOD Inspect")
        serial = self.int_value(Target.PromptTarget("Target a BOD in your backpack."), 0)
        if serial <= 0:
            self.host.set_status("BOD targeting cancelled.", WARN_HUE, "BOD Inspect")
            return

        gump_id = self.profile_int("gump", "gump_id", 0)
        if gump_id <= 0:
            self.host.set_status("The BOD gump ID is not configured.", BAD_HUE, "BOD Inspect")
            return

        try:
            if not self.open_bod_gump(serial):
                raise Exception("target did not open the configured BOD gump")

            self.last_gump_lines = self.bod_gump_lines()
            parsed = self.parse_bod_gump(self.last_gump_lines)
            item = Items.FindBySerial(serial)
            property_lines = self.item_property_lines(item) if item else []
            module_hint = self.module_hint_from_item(item, property_lines)
            module, category, recipe = self.find_recipe_match(
                module_hint,
                parsed.get("requested_names", []),
                parsed.get("requested_item_id", 0),
            )
            minimum_ok, minimum_detail, skill_warning = self.minimum_skill_check(module, recipe)
            material, material_choices, material_error = self.material_for_order(
                module,
                recipe,
                parsed.get("gump_lines", self.last_gump_lines),
            )

            self.current_bod_serial = serial
            self.matched_module_id = str(module.get("id", ""))
            self.matched_category_id = str(category.get("id", ""))
            self.matched_recipe_id = str(recipe.get("id", ""))
            self.job_resource_choices = material_choices
            self.exceptional_required = bool(parsed.get("exceptional_required", False))
            self.skill_warning = str(skill_warning or "")
            self.start_block_reason = ""
            self.fill_passes = 0
            self.zero_accept_passes = 0
            self.accepted_total = 0
            self.recycled_total = 0
            self.discarded_total = 0
            self.recycle_queue = []
            self.recycle_retry_count = 0
            self.recycle_action_failures = 0
            self.recycle_container_exhausted = False
            self.match_summary = "Matched {0} / {1}".format(module.get("name", ""), recipe.get("name", ""))
            self.set_current_order(
                self.module_title(self.matched_module_id),
                material,
                parsed.get("amount_to_make", 0),
                parsed.get("amount_finished", 0),
                recipe.get("name", ""),
                parsed.get("requested_item_id", 0),
            )
            self.set_bulk_progress(1 if self.amount_crafted >= self.amount_to_craft else 0, 1)
            self.set_artificer_points(parsed.get("artificer_points", 0), parsed.get("artificer_points_known", False))

            if not minimum_ok:
                self.start_block_reason = "skill filter: " + minimum_detail
                self.host.set_status("BOD cannot start: " + self.start_block_reason + ".", BAD_HUE, "BOD Filter")
            elif material_error:
                self.start_block_reason = material_error
                self.host.set_status("BOD cannot start: " + self.start_block_reason + ".", BAD_HUE, "BOD Filter")
            elif self.amount_crafted >= self.amount_to_craft:
                self.start_block_reason = "this BOD already reports all requested items finished"
                self.host.set_status("This BOD already reports all requested items finished.", WARN_HUE, "BOD Ready")
            else:
                if self.skill_warning:
                    self.host.overhead("Warning: " + self.skill_warning + ". Start Fill may continue.", WARN_HUE)
                    self.host.set_status("BOD loaded. Warning: {0}. Click Start Fill to continue.".format(self.skill_warning), WARN_HUE, "BOD Ready")
                else:
                    self.host.set_status("BOD loaded and ready. Click Start Fill.", GOOD_HUE, "BOD Ready")
        except Exception as ex:
            self.host.end_craft_job(self.plugin_id, True)
            self.running = False
            self.workflow_state = STATE_IDLE
            self.current_bod_serial = serial
            self.matched_module_id = ""
            self.matched_category_id = ""
            self.matched_recipe_id = ""
            self.job_resource_choices = {}
            self.exceptional_required = False
            self.skill_warning = ""
            self.start_block_reason = ""
            self.recycle_queue = []
            self.match_summary = "Inspection stopped: " + str(ex)
            self.set_current_order("", "", 0, 0, "", 0)
            self.set_bulk_progress(0, 1)
            self.set_artificer_points(0, False)
            self.host.set_status(self.match_summary, BAD_HUE, "BOD Inspect")
        finally:
            try:
                Gumps.CloseGump(gump_id)
            except:
                pass
            self.host.mark_dirty()

    def handle_button(self, local_button):
        if self.running and local_button != BTN_START_FILL:
            self.host.set_status("Stop the active BOD fill before using another control.", BAD_HUE, "BOD Fill")
            return
        if local_button == BTN_OPEN_BOD:
            self.open_current_bod()
            return
        if local_button == BTN_FILTER_BACK:
            self.page = PAGE_MAIN
            self.host.set_status("Bulk filters saved. Scan Orders to rebuild the queue.", GOOD_HUE, "BOD Filters")
            return
        if local_button == BTN_FILTER_PREV:
            page_count = max(1, (len(self.bulk_filter_entries()) + FILTER_PAGE_SIZE - 1) // FILTER_PAGE_SIZE)
            self.filter_page = (self.filter_page - 1) % page_count
            return
        if local_button == BTN_FILTER_NEXT:
            page_count = max(1, (len(self.bulk_filter_entries()) + FILTER_PAGE_SIZE - 1) // FILTER_PAGE_SIZE)
            self.filter_page = (self.filter_page + 1) % page_count
            return
        if local_button in self.filter_button_map:
            self.toggle_bulk_filter(self.filter_button_map[local_button])
            return
        if local_button == BTN_SET_CHEST_ONE:
            self.set_chest(1)
            return
        if local_button == BTN_SET_CHEST_TWO:
            self.set_chest(2)
            return
        if local_button == BTN_MODE_TOGGLE:
            self.toggle_mode()
            return
        if local_button == BTN_TARGET_BOD:
            self.target_bod()
            return
        if local_button == BTN_START_FILL:
            self.start_fill()
            return
        if local_button == BTN_SCAN:
            self.scan_orders()
            return
        if local_button == BTN_FILTERS:
            self.page = PAGE_FILTERS
            self.filter_page = 0
            self.host.set_status("Configure which orders may enter Bulk mode.", GOOD_HUE, "BOD Filters")
            return
    def snapshot(self):
        filter_snapshot = []
        for entry in self.bulk_filter_entries():
            filter_snapshot.append((
                str(entry.get("kind", "")),
                str(entry.get("key", "")),
                self.bulk_filter_enabled(entry.get("kind", ""), entry.get("key", "")),
            ))
        return (
            self.chest_one,
            self.chest_two,
            self.mode,
            self.page,
            self.filter_page,
            tuple(filter_snapshot),
            self.running,
            self.current_bod_type,
            self.current_material,
            self.current_item_name,
            self.current_item_id,
            self.current_bod_serial,
            self.matched_module_id,
            self.matched_category_id,
            self.matched_recipe_id,
            self.match_summary,
            self.workflow_state,
            self.job_initial_finished,
            self.job_remaining,
            self.job_stackable,
            tuple(sorted(self.job_resource_choices.items())),
            self.exceptional_required,
            self.skill_warning,
            self.start_block_reason,
            self.fill_passes,
            self.zero_accept_passes,
            self.accepted_total,
            self.recycled_total,
            self.discarded_total,
            tuple(self.recycle_queue),
            self.recycle_retry_count,
            self.recycle_action_failures,
            self.recycle_container_exhausted,
            self.post_cleanup_action,
            self.post_cleanup_message,
            self.amount_to_craft,
            self.amount_crafted,
            self.bods_completed,
            self.bods_total,
            tuple([self.int_value(record.get("serial"), 0) for record in self.bulk_queue]),
            self.bulk_index,
            self.bulk_run_active,
            self.bulk_run_skipped,
            self.bulk_points_completed,
            tuple([self.int_value(record.get("serial"), 0) for record in self.scan_candidates]),
            self.scan_index,
            self.scan_found,
            tuple([(self.int_value(record.get("serial"), 0), str(record.get("reason", ""))) for record in self.scan_rejected]),
            self.scan_current_serial,
            self.scan_current_source,
            self.scan_current_staged,
            self.current_source_serial,
            self.current_source_slot,
            self.artificer_points,
            self.artificer_points_known,
            tuple(self.last_gump_lines),
            self.data_error,
        )

    def shutdown(self):
        if self.running:
            self.host.end_craft_job(self.plugin_id, True)
        if self.bulk_run_active and self.current_bulk_record:
            self.return_record_to_source(self.current_bulk_record)
        self.running = False
        self.bulk_run_active = False
        self.workflow_state = STATE_IDLE
        self.recycle_queue = []
        self.recycle_retry_count = 0
        self.recycle_action_failures = 0
        self.recycle_container_exhausted = False
        self.post_cleanup_action = ""
        self.post_cleanup_message = ""


def create_plugin(host):
    return FrogBODFillerPlugin(host)
