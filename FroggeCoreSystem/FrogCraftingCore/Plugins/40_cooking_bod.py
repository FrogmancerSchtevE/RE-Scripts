# ====================================================
# === Frog Cooking BODs (FrogCraftingCore Plugin) ===
# ====================================================
# Copyright (c) Frogmancer Schteve. All rights reserved except as
# expressly permitted by the repository License.md.
#
# PERSONAL USE
# This script is provided for personal, non-commercial use.
# You may use, study, and modify it for your own use. Redistribution,
# resale, sublicensing, or incorporation into another distributed
# project is not permitted without prior permission.
#
# SHARD RULES
# You are responsible for ensuring your use of this script complies
# with the rules of the Ultima Online shard on which you play.
# ==================================================================

# Status: In Development

import math
import re
import time

import Journal


DATA_FILE = "cooking_bod_rules.json"
MODULE_ID = "cooking"

BTN_SCAN = 1
BTN_READ_STORAGE = 2
BTN_FILL_READY = 3
BTN_FILL_WHAT_WE_CAN = 4
BTN_STOP = 5
BTN_SET_MASTER = 6
BTN_SET_CHEF = 7
BTN_SET_WATER = 8
BTN_TOGGLE_SACKS = 9
BTN_OPEN_BOD = 10
BTN_SET_CHEST_ONE = 11
BTN_SET_CHEST_TWO = 12

STATE_IDLE = "idle"
STATE_SCAN = "scan"
STATE_PREPARE = "prepare"
STATE_WAIT_CRAFT = "wait_craft"
STATE_COMBINE = "combine"
STATE_RECYCLE = "recycle"
STATE_CLEANUP = "cleanup"

MODE_READY = "ready"
MODE_WHAT_WE_CAN = "what_we_can"

RX_GUMP_ELEMENT = re.compile(r"\{[^{}]*\}")
RX_GUMP_PAGE = re.compile(r"\{\s*page\s+(\d+)\s*\}", re.IGNORECASE)
RX_GUMP_BUTTON = re.compile(r"\{\s*button\s+(-?\d+)\s+(-?\d+)\s+\d+\s+\d+\s+(\d+)\s+(-?\d+)\s+(\d+)\s*\}", re.IGNORECASE)
RX_GUMP_TEXT = re.compile(r"\{\s*text\s+(-?\d+)\s+(-?\d+)\s+\d+\s+(\d+)\s*\}", re.IGNORECASE)
RX_GUMP_CROP = re.compile(r"\{\s*croppedtext\s+(-?\d+)\s+(-?\d+)\s+\d+\s+\d+\s+\d+\s+(\d+)\s*\}", re.IGNORECASE)
RX_GUMP_HTML = re.compile(r"\{\s*htmlgump\s+(-?\d+)\s+(-?\d+)\s+\d+\s+\d+\s+(\d+)\s+\d+\s+\d+\s*\}", re.IGNORECASE)
RX_HTML_TAG = re.compile(r"<[^>]*>")

MOVE_PAUSE_MS = 700
BOD_INSPECT_PAUSE_MS = 600


class FrogCookingBODPlugin:
    plugin_id = "cooking_bod"
    name = "Cooking BODs"
    version = "1.0"
    home_label = "Cooking BODs"

    def __init__(self, host):
        self.host = host
        self.button_base = 0
        self.running = False
        self.state = STATE_IDLE
        self.mode = MODE_READY
        self.rules = {}
        self.module = {}
        self.ingredients = {}
        self.master_catalog = {}
        self.recipes = {}
        self.recipe_categories = {}
        self.preparation_by_output = {}
        self.raw_resource_keys = set()
        self.component_aliases = {}
        self.data_error = ""

        self.master_serial = host.read_int("cooking_bod_master_shelf", 0)
        self.chef_serial = host.read_int("cooking_bod_chef_shelf", 0)
        self.water_serial = host.read_int("cooking_bod_water_trough", 0)
        self.manual_sacks = host.read_int("cooking_bod_manual_sacks", 1) != 0

        self.scan_candidates = []
        self.scan_index = 0
        self.scan_found = 0
        self.scan_skipped = []
        self.orders = []
        self.queue = []
        self.queue_index = 0
        self.active = {}
        self.before_outputs = {}
        self.reject_serials = []
        self.recycle_attempts = 0
        self.completed = 0
        self.partial = 0
        self.deferred = 0
        self.failed = 0
        self.failure_reasons = []
        self.job_started = False
        self.cleanup_message = ""
        self.zero_accepts = 0
        self.batch_plan = []
        self.batch_plan_index = 0
        self.batch_final_crafted = 0
        self.current_step = {}
        self.before_step_count = 0

        self.shopping_required = {}
        self.shopping_pack = {}
        self.shopping_master = {}
        self.shopping_chef = {}
        self.shopping_missing = {}
        self.master_rows = []
        self.chef_rows = []
        self.storage_errors = []

        self.load_data()

    # ------------------------------------------------------------
    # Basic helpers and plugin contract
    # ------------------------------------------------------------

    def number(self, value, fallback=0):
        try:
            text = str(value).strip().lower()
            return int(text, 16) if text.startswith("0x") else int(value)
        except:
            return int(fallback)

    def normalize(self, value):
        text = str(value or "").strip().lower()
        text = re.sub(r"[^a-z0-9]+", " ", text)
        return " ".join(text.split())

    def key(self, value):
        return self.normalize(value).replace(" ", "_")

    def html(self, value):
        return str(value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def button_id(self, local_id):
        return int(self.button_base) + int(local_id)

    def is_priority_button(self, local_button):
        return self.running and int(local_button) == BTN_STOP

    def timing(self, key, fallback):
        return max(0, self.number(self.rules.get("timing", {}).get(key), fallback))

    def announce(self, message, hue=LABEL_HUE, step="Cooking BODs"):
        self.host.set_status(str(message), hue, step)
        self.host.mark_dirty()

    def activate(self):
        if self.data_error:
            self.announce("Cooking BOD data error: " + self.data_error, BAD_HUE, "Cooking Setup")
        else:
            self.announce("Cooking BODs uses the BOD Filler sources and FrogCraftingCore's verified crafting engine.", GOOD_HUE, "Cooking Ready")

    def deactivate(self, message=None):
        if self.running:
            self.stop(message or "Cooking BOD work paused.", WARN_HUE)
        elif message:
            self.announce(message, WARN_HUE, "Cooking Paused")

    def shutdown(self):
        if self.running:
            self.stop("Cooking BOD plugin stopped.", WARN_HUE)

    def snapshot(self):
        return (
            self.state,
            self.running,
            len(self.orders),
            self.queue_index,
            len(self.queue),
            self.number(self.active.get("amount_finished"), 0),
            self.number(self.active.get("amount_to_make"), 0),
            self.batch_plan_index,
            len(self.batch_plan),
            str(self.current_step.get("recipe_id", "")),
            len(self.shopping_missing),
            self.manual_sacks,
        )

    def load_data(self):
        try:
            self.rules = self.host.read_data(DATA_FILE)
            if self.rules.get("format") != "frog-cooking-bod-rules" or self.number(self.rules.get("version"), 0) != 1:
                raise Exception("unsupported Cooking BOD rules format")
            self.module = self.host.module(MODULE_ID) or {}
            if self.module.get("format") != "frog-crafting-module" or str(self.module.get("id", "")) != MODULE_ID:
                raise Exception("Cooking module is unavailable")
            ingredient_data = self.host.read_data("ingredient_ids.json")
            self.master_catalog = self.host.read_data("master_shelf.json")
            if ingredient_data.get("format") != "frog-ingredient-identifiers":
                raise Exception("ingredient identifier data is unavailable")
            if self.master_catalog.get("format") != "frog-master-shelf":
                raise Exception("Master Shelf data is unavailable")

            for record in ingredient_data.get("ingredients", []):
                resource_key = self.key(record.get("resource_key", ""))
                if resource_key:
                    self.ingredients[resource_key] = dict(record)
            for category in self.module.get("categories", []):
                for recipe in category.get("recipes", []):
                    recipe_id = str(recipe.get("id", ""))
                    if recipe_id:
                        self.recipes[recipe_id] = recipe
                        self.recipe_categories[recipe_id] = str(category.get("id", ""))
            self.raw_resource_keys = set(self.key(value) for value in self.rules.get("raw_resource_keys", []))
            self.component_aliases = dict((self.key(key), str(value)) for key, value in self.rules.get("component_aliases", {}).items())
            for rule in self.rules.get("preparations", []):
                resource_key = self.key(rule.get("output_resource_key", ""))
                if resource_key:
                    self.preparation_by_output[resource_key] = dict(rule)
        except Exception as ex:
            self.data_error = str(ex)

    def bod_engine(self):
        return self.host.plugin("bod_filler")

    def source_containers(self):
        engine = self.bod_engine()
        return engine.source_containers() if engine else []

    def save_targets(self):
        self.host.write_int("cooking_bod_master_shelf", self.master_serial)
        self.host.write_int("cooking_bod_chef_shelf", self.chef_serial)
        self.host.write_int("cooking_bod_water_trough", self.water_serial)
        self.host.write_int("cooking_bod_manual_sacks", 1 if self.manual_sacks else 0)

    # ------------------------------------------------------------
    # Inventory and recipe planning
    # ------------------------------------------------------------

    def item_name(self, item, properties=False):
        if not item:
            return ""
        name = str(getattr(item, "Name", "") or "").strip()
        if name and name.lower() not in ("item", "object"):
            return name
        if properties:
            try:
                Items.WaitForProps(item, 1000)
                values = list(getattr(item, "Properties", None) or [])
                if values:
                    return str(getattr(values[0], "ToString", lambda: values[0])())
            except:
                pass
        return name

    def direct_items(self, container_serial):
        container = self.host.valid_item(container_serial)
        if not container:
            return []
        try:
            Items.WaitForContents(container, 1200)
        except:
            pass
        try:
            return list(container.Contains or [])
        except:
            return []

    def recursive_items(self, container_serial, max_depth=8):
        result = []
        pending = [(self.number(container_serial), 0)]
        seen = set()
        while pending:
            serial, depth = pending.pop(0)
            if serial <= 0 or serial in seen or depth > max_depth:
                continue
            seen.add(serial)
            for item in self.direct_items(serial):
                result.append(item)
                if bool(getattr(item, "IsContainer", False)):
                    pending.append((self.number(getattr(item, "Serial", 0)), depth + 1))
        return result

    def descriptor(self, resource_key):
        key = self.key(resource_key)
        result = dict(self.ingredients.get(key, {}))
        override = self.rules.get("resource_overrides", {}).get(key, {})
        if isinstance(override, dict):
            result.update(override)
        result["resource_key"] = key
        if not result.get("name"):
            result["name"] = key.replace("_", " ").title()
        names = []
        for value in list(result.get("names", [])) + [result.get("name", "")]:
            normalized = self.normalize(value)
            if normalized and normalized not in names:
                names.append(normalized)
        result["normalized_names"] = names
        values = list(result.get("item_ids", []))
        if result.get("item_id") is not None:
            values.append(result.get("item_id"))
        result["parsed_item_ids"] = [self.number(value) for value in values if self.number(value) > 0]
        hues = list(result.get("hues", []))
        if result.get("hue") is not None:
            hues.append(result.get("hue"))
        result["parsed_hues"] = [self.number(value, -1) for value in hues if self.number(value, -1) >= 0]
        return result

    def item_matches(self, item, descriptor, exact_names=None):
        if not item:
            return False
        if exact_names is not None:
            wanted = [self.normalize(value) for value in exact_names]
            wanted = [value for value in wanted if value]
            if not wanted:
                return False
            actual = self.normalize(self.item_name(item, True))
            return actual in wanted
        item_id = self.number(getattr(item, "ItemID", 0))
        hue = self.number(getattr(item, "Hue", -1), -1)
        ids = descriptor.get("parsed_item_ids", [])
        hues = descriptor.get("parsed_hues", [])
        if ids and item_id in ids and (not hues or hue in hues):
            return True
        wanted = [self.normalize(value) for value in descriptor.get("normalized_names", [])]
        wanted = [value for value in wanted if value]
        if not wanted:
            return False
        return self.normalize(self.item_name(item, True)) in wanted

    def resource_items(self, resource_key, exact_names=None):
        backpack = getattr(Player, "Backpack", None)
        if not backpack:
            return []
        descriptor = self.descriptor(resource_key)
        return [item for item in self.recursive_items(backpack.Serial) if self.item_matches(item, descriptor, exact_names)]

    def resource_count(self, resource_key):
        return sum(max(1, self.number(getattr(item, "Amount", 1), 1)) for item in self.resource_items(resource_key))

    def active_preparation(self, resource_key):
        rule = self.preparation_by_output.get(self.key(resource_key))
        if not rule:
            return None
        if bool(rule.get("master_shelf_optional", False)) and not self.manual_sacks:
            return None
        return rule

    def expand_requirements(self, recipe_id, count, raw_needs, preparation_units, stack=None):
        recipe_id = str(recipe_id)
        recipe = self.recipes.get(recipe_id)
        if not recipe:
            raise Exception("unknown Cooking recipe " + recipe_id)
        visited = list(stack or [])
        if recipe_id in visited:
            raise Exception("Cooking component cycle at " + recipe_id)
        visited.append(recipe_id)
        count = max(1, self.number(count, 1))
        for resource in recipe.get("resources", []):
            key = self.key(resource.get("resource_key", ""))
            amount = max(1, self.number(resource.get("amount"), 1)) * count
            preparation = self.active_preparation(key)
            if preparation:
                rule_id = self.key(preparation.get("id", key))
                preparation_units[rule_id] = preparation_units.get(rule_id, 0) + amount
                continue
            component_id = str(resource.get("craft_recipe_id", "") or self.component_aliases.get(key, ""))
            if component_id and component_id in self.recipes and key not in self.raw_resource_keys:
                output_amount = max(1, self.number(self.recipes[component_id].get("output_amount"), 1))
                crafts = int(math.ceil(float(amount) / float(output_amount)))
                self.expand_requirements(component_id, crafts, raw_needs, preparation_units, visited)
                continue
            raw_needs[key] = raw_needs.get(key, 0) + amount

    def preparation_rule(self, rule_id):
        wanted = self.key(rule_id)
        for rule in self.rules.get("preparations", []):
            if self.key(rule.get("id", "")) == wanted:
                return rule
        return None

    def package_requirements(self, preparation_units):
        result = {}
        for rule_id, logical_units in preparation_units.items():
            rule = self.preparation_rule(rule_id)
            if not rule:
                continue
            units = max(1, self.number(rule.get("units_per_source"), 1))
            packages = 1 if bool(rule.get("reusable", False)) and logical_units > 0 else int(math.ceil(float(logical_units) / float(units)))
            key = self.key(rule.get("source_resource_key", ""))
            result[key] = result.get(key, 0) + packages
        return result

    def recipe_requirements(self, recipe_id, count=1):
        raw = {}
        preparations = {}
        self.expand_requirements(recipe_id, count, raw, preparations)
        for key, amount in self.package_requirements(preparations).items():
            raw[key] = raw.get(key, 0) + amount
        return raw, preparations

    def component_recipe_id(self, resource):
        key = self.key(resource.get("resource_key", ""))
        if key in self.raw_resource_keys:
            return ""
        recipe_id = str(resource.get("craft_recipe_id", "") or self.component_aliases.get(key, ""))
        return recipe_id if recipe_id in self.recipes else ""

    def append_batch_plan(self, recipe_id, output_units, plan, stack=None):
        recipe_id = str(recipe_id)
        recipe = self.recipes.get(recipe_id)
        if not recipe:
            raise Exception("unknown Cooking recipe " + recipe_id)
        visited = list(stack or [])
        if recipe_id in visited:
            raise Exception("Cooking component cycle at " + recipe_id)
        visited.append(recipe_id)
        output_units = max(1, self.number(output_units, 1))
        output_amount = max(1, self.number(recipe.get("output_amount"), 1))
        craft_count = int(math.ceil(float(output_units) / float(output_amount)))
        for resource in recipe.get("resources", []):
            component_id = self.component_recipe_id(resource)
            if not component_id:
                continue
            component_units = max(1, self.number(resource.get("amount"), 1)) * craft_count
            self.append_batch_plan(component_id, component_units, plan, visited)
        plan.append({
            "recipe_id": recipe_id,
            "recipe_name": str(recipe.get("name", recipe_id)),
            "category_id": str(self.recipe_categories.get(recipe_id, "")),
            "amount": output_units,
            "remaining": output_units,
            "started": False,
            "is_final": False,
        })

    def build_batch_plan(self, recipe_id, output_units):
        plan = []
        self.append_batch_plan(recipe_id, output_units, plan, [])
        if plan:
            plan[-1]["is_final"] = True
        return plan

    def batch_limit(self):
        configured = max(1, self.number(self.rules.get("subcraft_batch_size"), 5))
        return min(10, configured)

    def bounded_batch_plan(self, recipe_id, desired_units):
        units = min(max(1, self.number(desired_units, 1)), self.batch_limit())
        return units, self.build_batch_plan(recipe_id, units)

    def reset_batch_plan(self):
        self.batch_plan = []
        self.batch_plan_index = 0
        self.batch_final_crafted = 0
        self.current_step = {}
        self.before_step_count = 0
        self.before_outputs = {}

    def direct_preparation_units(self, recipe_id, output_units):
        recipe = self.recipes.get(str(recipe_id))
        if not recipe:
            raise Exception("unknown Cooking recipe " + str(recipe_id))
        output_amount = max(1, self.number(recipe.get("output_amount"), 1))
        craft_count = int(math.ceil(float(max(1, self.number(output_units, 1))) / float(output_amount)))
        preparations = {}
        for resource in recipe.get("resources", []):
            if self.component_recipe_id(resource):
                continue
            key = self.key(resource.get("resource_key", ""))
            preparation = self.active_preparation(key)
            if not preparation:
                continue
            rule_id = self.key(preparation.get("id", key))
            amount = max(1, self.number(resource.get("amount"), 1)) * craft_count
            preparations[rule_id] = preparations.get(rule_id, 0) + amount
        return preparations

    def direct_reusable_preparation(self, recipe_id):
        for rule_id in self.direct_preparation_units(recipe_id, 1):
            rule = self.preparation_rule(rule_id)
            if rule and bool(rule.get("reusable", False)):
                return True
        return False

    def recipe_cost(self, record):
        try:
            raw, preparations = self.recipe_requirements(record.get("recipe_id", ""), 1)
            return (sum(raw.values()), len(raw), len(preparations), self.normalize(record.get("recipe_name", "")))
        except:
            return (999999, 999999, 999999, self.normalize(record.get("recipe_name", "")))

    def resource_label(self, resource_key):
        return str(self.descriptor(resource_key).get("name", self.key(resource_key).replace("_", " ").title()))

    def rebuild_shopping(self):
        raw = {}
        preparations = {}
        for order in self.orders:
            remaining = max(0, self.number(order.get("amount_to_make")) - self.number(order.get("amount_finished")))
            if remaining <= 0:
                continue
            try:
                self.expand_requirements(order.get("recipe_id", ""), remaining, raw, preparations)
            except Exception as ex:
                order["block_reason"] = str(ex)
        for key, amount in self.package_requirements(preparations).items():
            raw[key] = raw.get(key, 0) + amount
        multiplier = 1.0 + (max(0, self.number(self.rules.get("shopping_buffer_percent"), 0)) / 100.0)
        self.shopping_required = dict((key, int(math.ceil(float(amount) * multiplier))) for key, amount in raw.items())
        self.shopping_pack = dict((key, self.resource_count(key)) for key in self.shopping_required)
        self.shopping_master = self.allocate_rows(self.master_rows, {})
        self.shopping_chef = self.allocate_rows(self.chef_rows, self.shopping_master)
        self.shopping_missing = {}
        for key, required in self.shopping_required.items():
            owned = self.shopping_pack.get(key, 0) + self.shopping_master.get(key, 0) + self.shopping_chef.get(key, 0)
            if owned < required:
                self.shopping_missing[key] = required - owned
        self.host.mark_dirty()

    # ------------------------------------------------------------
    # Storage gump parsing
    # ------------------------------------------------------------

    def close_gump(self, gump_id):
        try:
            Gumps.CloseGump(self.number(gump_id))
        except:
            pass

    def gump_open(self, gump_id):
        try:
            return Gumps.GetGumpData(self.number(gump_id)) is not None
        except:
            try:
                return bool(Gumps.HasGump(self.number(gump_id)))
            except:
                return False

    def open_storage(self, serial, gump_id):
        item = self.host.valid_item(serial)
        if not item:
            return False
        self.close_gump(gump_id)
        try:
            Items.UseItem(item)
            Gumps.WaitForGump(self.number(gump_id), self.timing("storage_gump_wait_ms", 3500))
        except:
            return False
        if self.gump_open(gump_id):
            Misc.Pause(self.timing("storage_settle_ms", 300))
        return self.gump_open(gump_id)

    def raw_layout(self, gump_id):
        readers = (
            lambda: Gumps.GetGumpRawLayout(self.number(gump_id)),
            lambda: getattr(Gumps.GetGumpData(self.number(gump_id)), "gumpLayout", ""),
        )
        for reader in readers:
            try:
                value = str(reader() or "")
                if value.strip():
                    return value
            except:
                pass
        try:
            if self.number(Gumps.CurrentGump()) == self.number(gump_id):
                return str(Gumps.LastGumpRawLayout() or "")
        except:
            pass
        return ""

    def gump_elements(self, layout):
        result = []
        page = 0
        for match in RX_GUMP_ELEMENT.finditer(str(layout or "")):
            element = match.group(0)
            page_match = RX_GUMP_PAGE.match(element)
            if page_match:
                page = self.number(page_match.group(1))
            else:
                result.append((page, element))
        return result

    def string_table(self, gump_id, layout):
        needed = 0
        for expression in (RX_GUMP_TEXT, RX_GUMP_CROP, RX_GUMP_HTML):
            for match in expression.finditer(str(layout or "")):
                needed = max(needed, self.number(match.group(3), -1) + 1)
        candidates = []
        try:
            data = Gumps.GetGumpData(self.number(gump_id))
            for attribute in ("gumpStrings", "stringList", "gumpText"):
                try:
                    candidates.append([str(value) for value in getattr(data, attribute)])
                except:
                    pass
        except:
            pass
        try:
            candidates.append([str(value) for value in Gumps.GetLineList(self.number(gump_id), False)])
        except:
            pass
        try:
            candidates.append([str(value) for value in Gumps.LastGumpGetLineList()])
        except:
            pass
        for values in candidates:
            if values and len(values) >= needed:
                return values
        for values in candidates:
            if values:
                return values
        return []

    def clean_gump_text(self, value):
        return " ".join(RX_HTML_TAG.sub("", str(value or "")).split())

    def page_snapshot(self, gump_id):
        layout = self.raw_layout(gump_id)
        indexed_strings = self.string_table(gump_id, layout)
        texts = []
        buttons = []
        for page, element in self.gump_elements(layout):
            for expression in (RX_GUMP_TEXT, RX_GUMP_CROP, RX_GUMP_HTML):
                match = expression.match(element)
                if match:
                    index = self.number(match.group(3), -1)
                    texts.append({
                        "x": self.number(match.group(1)),
                        "y": self.number(match.group(2)),
                        "text": self.clean_gump_text(indexed_strings[index]) if 0 <= index < len(indexed_strings) else "",
                        "page": page,
                    })
                    break
            match = RX_GUMP_BUTTON.match(element)
            if match and self.number(match.group(3)) == 1:
                buttons.append({"id": self.number(match.group(5)), "x": self.number(match.group(1)), "y": self.number(match.group(2)), "page": page})
        resolved = []
        try:
            resolved = [self.clean_gump_text(value) for value in Gumps.GetLineList(self.number(gump_id), False)]
        except:
            pass
        strings = list(indexed_strings) + [value for value in resolved if value]
        return layout, strings, texts, buttons

    def numeric_value(self, value):
        text = self.clean_gump_text(value).replace(",", "").strip()
        if text in ("-", "--"):
            return 0
        match = re.match(r"^(?:stock\s*:?\s*)?(\d+)$", text, re.IGNORECASE)
        return self.number(match.group(1), -1) if match else -1

    def name_forms(self, value):
        base = self.normalize(value)
        if not base:
            return []
        forms = [base]
        pending = [base]
        prefixes = ("sack of ", "sack ", "jar of ", "jar ", "bottle of ", "bottle ", "pitcher of ", "pitcher ", "bag of ", "bag ", "cooked ")
        while pending:
            current = pending.pop(0)
            variants = []
            for prefix in prefixes:
                if current.startswith(prefix) and len(current) > len(prefix):
                    variants.append(current[len(prefix):])
            if "uncooked" in current:
                variants.append(current.replace("uncooked", "unbaked"))
            if "unbaked" in current:
                variants.append(current.replace("unbaked", "uncooked"))
            if current.endswith("ies") and len(current) > 4:
                variants.append(current[:-3] + "y")
            if current.endswith("es") and len(current) > 4 and not current.endswith("ses"):
                variants.append(current[:-2])
            if current.endswith("s") and len(current) > 3 and not current.endswith("ss"):
                variants.append(current[:-1])
            for variant in variants:
                variant = self.normalize(variant)
                if variant and variant not in forms:
                    forms.append(variant)
                    pending.append(variant)
        return forms

    def storage_names(self, resource_key):
        key = self.key(resource_key)
        descriptor = self.descriptor(key)
        values = [key.replace("_", " "), descriptor.get("name", "")]
        values.extend(descriptor.get("names", []))
        aliases = self.rules.get("storage", {}).get("name_aliases", {})
        configured = aliases.get(key, []) if isinstance(aliases, dict) else []
        values.extend(configured if isinstance(configured, list) else [configured])
        result = []
        for value in values:
            name = self.normalize(value)
            if name and name not in result:
                result.append(name)
        return result

    def match_score(self, resource_key, label, storage_id=""):
        key = self.key(resource_key)
        if storage_id and self.key(storage_id) == key:
            return 120
        label_name = self.normalize(label)
        names = self.storage_names(key)
        if label_name in names:
            return 100
        wanted = set()
        for name in names:
            wanted.update(self.name_forms(name))
        return 70 if wanted & set(self.name_forms(label_name)) else 0

    def count_near_label(self, texts, strings, names):
        wanted = set()
        for name in names:
            wanted.update(self.name_forms(name))
        for label in [record for record in texts if set(self.name_forms(record.get("text", ""))) & wanted]:
            numbers = []
            for record in texts:
                value = self.numeric_value(record.get("text", ""))
                if value < 0 or abs(self.number(record.get("y")) - self.number(label.get("y"))) > 10:
                    continue
                numbers.append((0 if self.number(record.get("x")) > self.number(label.get("x")) else 1, abs(self.number(record.get("x")) - self.number(label.get("x"))), value))
            if numbers:
                numbers.sort()
                return numbers[0][2]
        normalized = [self.normalize(value) for value in strings]
        for index, value in enumerate(normalized):
            if not (set(self.name_forms(value)) & wanted):
                continue
            for candidate in strings[index + 1:index + 5]:
                parsed = self.numeric_value(candidate)
                if parsed >= 0:
                    return parsed
        return None

    def master_entries_for_page(self, category_id, page):
        return [dict(entry) for entry in self.master_catalog.get("resources", []) if self.key(entry.get("category", "")) == self.key(category_id) and max(1, self.number(entry.get("page"), 1)) == max(1, self.number(page, 1))]

    def master_page_visible(self, gump_id, category_id, page):
        layout, strings, texts, _buttons = self.page_snapshot(gump_id)
        if not layout:
            return False
        visible = set()
        for value in list(strings) + [record.get("text", "") for record in texts]:
            visible.update(self.name_forms(value))
        for entry in self.master_entries_for_page(category_id, page):
            names = [entry.get("name", ""), str(entry.get("id", "")).replace("_", " ")]
            if any(set(self.name_forms(name)) & visible for name in names):
                return True
        return False

    def storage_signature(self, gump_id):
        layout, strings, _texts, _buttons = self.page_snapshot(gump_id)
        if not layout:
            return ""
        return layout + "\x1f" + "\x1e".join([str(value) for value in strings])

    def wait_master_page(self, gump_id, category_id, page, previous_signature):
        deadline = time.time() + (float(self.timing("storage_gump_wait_ms", 3500)) / 1000.0)
        while time.time() < deadline:
            if self.gump_open(gump_id):
                current = self.storage_signature(gump_id)
                if current and current != previous_signature and self.master_page_visible(gump_id, category_id, page):
                    Misc.Pause(self.timing("storage_settle_ms", 300))
                    return True
            Misc.Pause(125)
        return False

    def select_master_category(self, gump_id, category_id, button):
        if self.master_page_visible(gump_id, category_id, 1):
            return True
        if self.number(button) <= 0:
            return False
        before = self.storage_signature(gump_id)
        try:
            Gumps.SendAction(gump_id, self.number(button))
        except:
            return False
        return self.wait_master_page(gump_id, category_id, 1, before)

    def advance_master_page(self, gump_id, category_id, page):
        if self.master_page_visible(gump_id, category_id, page):
            return True
        before = self.storage_signature(gump_id)
        try:
            Gumps.SendAction(gump_id, self.number(self.master_catalog.get("next_page_button"), 11))
        except:
            return False
        return self.wait_master_page(gump_id, category_id, page, before)

    def relevant_master_entries(self):
        result = []
        for raw in self.master_catalog.get("resources", []):
            entry = dict(raw)
            if any(self.match_score(key, entry.get("name", ""), entry.get("id", "")) > 0 for key in self.shopping_required):
                result.append(entry)
        return result

    def read_master_rows(self):
        entries = self.relevant_master_entries()
        if not entries:
            return [], ""
        gump_id = self.number(self.master_catalog.get("gump_id"), 0x79DF5A83)
        if not self.open_storage(self.master_serial, gump_id):
            return [], "Master Shelf gump did not open."
        categories = dict((self.key(category.get("id", "")), self.number(category.get("button"))) for category in self.master_catalog.get("categories", []))
        rows = []
        try:
            for category_id in [self.key(category.get("id", "")) for category in self.master_catalog.get("categories", [])]:
                relevant = [entry for entry in entries if self.key(entry.get("category", "")) == category_id]
                if not relevant:
                    continue
                if not self.select_master_category(gump_id, category_id, categories.get(category_id, 0)):
                    raise Exception("category {0} did not open".format(category_id))
                maximum = max(max(1, self.number(entry.get("page"), 1)) for entry in relevant)
                for page in range(1, maximum + 1):
                    _layout, strings, texts, _buttons = self.page_snapshot(gump_id)
                    for entry in [value for value in relevant if max(1, self.number(value.get("page"), 1)) == page]:
                        count = self.count_near_label(texts, strings, [entry.get("name", ""), str(entry.get("id", "")).replace("_", " ")])
                        if count is not None:
                            rows.append({"id": self.key(entry.get("id", "")), "label": str(entry.get("name", "")), "count": max(0, self.number(count))})
                    if page < maximum and not self.advance_master_page(gump_id, category_id, page + 1):
                        raise Exception("page {0} did not advance".format(page))
        except Exception as ex:
            self.close_gump(gump_id)
            return rows, "Master Shelf read was incomplete: " + str(ex)
        self.close_gump(gump_id)
        return (rows, "" if rows else "Master Shelf opened, but no requested ingredient counts were parsed.")

    def chef_rule(self):
        value = self.rules.get("storage", {}).get("chef_shelf", {})
        return value if isinstance(value, dict) else {}

    def dynamic_chef_rows(self, texts, buttons, minimum, maximum):
        rows = []
        for button in buttons:
            button_id = self.number(button.get("id"))
            if button_id < minimum or button_id > maximum:
                continue
            nearby = [(self.number(record.get("x")) - self.number(button.get("x")), record) for record in texts if abs(self.number(record.get("y")) - self.number(button.get("y"))) <= 10 and record.get("text")]
            names = sorted([(offset, record) for offset, record in nearby if 15 <= offset <= 100], key=lambda value: value[0])
            counts = sorted([(offset, self.numeric_value(record.get("text", ""))) for offset, record in nearby if 100 <= offset <= 250 and self.numeric_value(record.get("text", "")) >= 0], key=lambda value: value[0])
            if names:
                rows.append({"id": self.normalize(names[0][1].get("text", "")), "label": names[0][1].get("text", ""), "count": counts[0][1] if counts else 0})
        return rows

    def storage_page_of(self, texts):
        for record in texts:
            match = re.search(r"\(\s*(\d+)\s*/\s*(\d+)\s*\)", record.get("text", ""))
            if match:
                return self.number(match.group(1)), self.number(match.group(2))
        return 0, 0

    def read_chef_rows(self):
        config = self.chef_rule()
        gump_id = self.number(config.get("gump_id"), 0x06ABCE12)
        if not self.open_storage(self.chef_serial, gump_id):
            return [], "Chef Storage gump did not open."
        minimum = max(1, self.number(config.get("row_button_min"), 1))
        maximum = max(minimum, self.number(config.get("row_button_max"), 149))
        pages = max(1, self.number(config.get("max_pages"), 6))
        next_button = self.number(config.get("next_page_button"), 163)
        rows = {}
        seen = []
        error = ""
        try:
            for _page in range(pages):
                layout, _strings, texts, buttons = self.page_snapshot(gump_id)
                if not layout:
                    raise Exception("gump layout was unavailable")
                current = self.dynamic_chef_rows(texts, buttons, minimum, maximum)
                signature = "|".join(sorted(self.normalize(row.get("label", "")) for row in current))
                if signature and signature in seen:
                    break
                if signature:
                    seen.append(signature)
                for row in current:
                    rows[self.normalize(row.get("label", ""))] = row
                current_page, total_pages = self.storage_page_of(texts)
                visible = [self.number(button.get("id")) for button in buttons]
                if (total_pages > 0 and current_page >= total_pages) or next_button not in visible:
                    break
                Gumps.SendAction(gump_id, next_button)
                Gumps.WaitForGump(gump_id, self.timing("storage_action_wait_ms", 1500))
                Misc.Pause(self.timing("storage_settle_ms", 300))
        except Exception as ex:
            error = "Chef Storage read was incomplete: " + str(ex)
        self.close_gump(gump_id)
        values = list(rows.values())
        return (values, error if error else ("" if values else "Chef Storage opened, but no ingredient rows were parsed."))

    def allocate_rows(self, rows, prior):
        result = dict((key, 0) for key in self.shopping_required)
        remaining = dict((index, max(0, self.number(row.get("count")))) for index, row in enumerate(rows))
        pairs = []
        for index, row in enumerate(rows):
            for key in self.shopping_required:
                score = self.match_score(key, row.get("label", ""), row.get("id", ""))
                if score > 0:
                    pairs.append((-score, key, index))
        pairs.sort()
        for _score, key, index in pairs:
            available = remaining.get(index, 0)
            if available > 0:
                result[key] += available
                remaining[index] = 0
        return result

    def read_storage(self, show_status=True):
        self.storage_errors = []
        self.master_rows = []
        self.chef_rows = []
        if self.host.valid_item(self.master_serial):
            self.master_rows, error = self.read_master_rows()
            if error:
                self.storage_errors.append(error)
        if self.host.valid_item(self.chef_serial):
            self.chef_rows, error = self.read_chef_rows()
            if error:
                self.storage_errors.append(error)
        self.rebuild_shopping()
        if show_status:
            if self.storage_errors:
                self.announce(" ".join(self.storage_errors), WARN_HUE, "Cooking Storage")
            else:
                self.announce("Storage counted: {0} Master row(s), {1} Chef row(s).".format(len(self.master_rows), len(self.chef_rows)), GOOD_HUE, "Cooking Storage")

    # ------------------------------------------------------------
    # Special cooking preparation bridge
    # ------------------------------------------------------------

    def preparation_names(self, rule, fields):
        result = []
        for field in fields:
            for value in rule.get(field, []):
                if self.normalize(value) and value not in result:
                    result.append(value)
        return result

    def preparation_items(self, rule, fields):
        names = self.preparation_names(rule, fields)
        return self.resource_items(rule.get("source_resource_key", ""), names) if names else []

    def preparation_count(self, rule, fields):
        seen = set()
        total = 0
        for item in self.preparation_items(rule, fields):
            serial = self.number(getattr(item, "Serial", 0))
            if serial > 0 and serial not in seen:
                seen.add(serial)
                total += max(1, self.number(getattr(item, "Amount", 1), 1))
        return total

    def master_entry(self, resource_id):
        wanted = self.key(resource_id)
        for entry in self.master_catalog.get("resources", []):
            if self.key(entry.get("id", "")) == wanted:
                return dict(entry)
        matches = []
        for entry in self.master_catalog.get("resources", []):
            score = self.match_score(wanted, entry.get("name", ""), entry.get("id", ""))
            if score > 0:
                matches.append((-score, self.key(entry.get("id", "")), dict(entry)))
        matches.sort(key=lambda value: (value[0], value[1]))
        return matches[0][2] if matches else None

    def master_category_button(self, category_id):
        for category in self.master_catalog.get("categories", []):
            if self.key(category.get("id", "")) == self.key(category_id):
                return self.number(category.get("button"))
        return 0

    def open_master_entry(self, entry):
        gump_id = self.number(self.master_catalog.get("gump_id"), 0x79DF5A83)
        if not self.host.valid_item(self.master_serial):
            return False, "Set a valid Master Shelf in Cooking BODs."
        if not self.open_storage(self.master_serial, gump_id):
            return False, "Master Shelf gump did not open."
        category = self.key(entry.get("category", ""))
        if not self.select_master_category(gump_id, category, self.master_category_button(category)):
            self.close_gump(gump_id)
            return False, "Master Shelf category {0} did not open.".format(category)
        for page in range(2, max(1, self.number(entry.get("page"), 1)) + 1):
            if not self.advance_master_page(gump_id, category, page):
                self.close_gump(gump_id)
                return False, "Master Shelf page {0} did not open.".format(page)
        return True, ""

    def journal_cursor(self):
        try:
            entries = Journal.GetJournalEntry(0) or []
            return entries[-1] if entries else None
        except:
            return None

    def journal_withdrawn(self, cursor, requested, label):
        try:
            entries = Journal.GetJournalEntry(cursor) if cursor else Journal.GetJournalEntry(0)
        except:
            entries = []
        wanted = self.normalize(label)
        for entry in entries or []:
            text = str(getattr(entry, "Text", ""))
            match = re.search(r"\bwithdrew\s+(\d+)\s*x\s+(.+?)(?:\.\s*)?$", text, re.IGNORECASE)
            if not match:
                continue
            delivered = self.number(match.group(1))
            actual = self.normalize(match.group(2))
            if delivered > 0 and (not wanted or not actual or wanted in actual or actual in wanted):
                return min(delivered, requested)
        return 0

    def withdraw_master(self, entry, amount, count_reader, label):
        amount = max(1, self.number(amount, 1))
        button = self.number(entry.get("withdraw_button"), 0)
        if button <= 0:
            return False, "Master Shelf withdrawal is not mapped for " + str(label) + "."
        maximum = max(1, self.number(self.master_catalog.get("withdraw_amount_max"), 1000))
        text_id = self.number(self.master_catalog.get("withdraw_amount_text_entry_id"), 0)
        remaining = amount
        while remaining > 0:
            requested = min(remaining, maximum)
            opened, message = self.open_master_entry(entry)
            if not opened:
                return False, message
            gump_id = self.number(self.master_catalog.get("gump_id"), 0x79DF5A83)
            before = max(0, self.number(count_reader()))
            cursor = self.journal_cursor()
            try:
                Gumps.SendAdvancedAction(gump_id, button, [], [text_id], [str(requested)])
            except Exception as ex:
                self.close_gump(gump_id)
                return False, "Master Shelf withdrawal failed: " + str(ex)
            deadline = time.time() + (float(self.timing("master_withdraw_verify_ms", 2500)) / 1000.0)
            delivered = 0
            while time.time() < deadline:
                Misc.Pause(125)
                delivered = max(delivered, max(0, self.number(count_reader()) - before), self.journal_withdrawn(cursor, requested, label))
                if delivered >= requested:
                    break
            self.close_gump(gump_id)
            strict = bool(self.rules.get("storage", {}).get("master_shelf", {}).get("strict_withdraw_verification", False))
            if delivered <= 0 and strict:
                return False, "Master Shelf did not verify delivery of " + str(label) + "."
            remaining -= requested if delivered <= 0 else min(requested, delivered)
        return True, "Withdrew {0} {1}.".format(amount, label)

    def withdraw_preparation(self, rule, required):
        resource_id = rule.get("master_resource_id", rule.get("source_resource_key", ""))
        entry = self.master_entry(resource_id)
        if not entry:
            return False, "Master Shelf mapping is missing for " + str(rule.get("shopping_name", resource_id)) + "."
        override_button = self.number(rule.get("master_withdraw_button"), 0)
        if override_button > 0:
            entry["withdraw_button"] = override_button
        current = self.preparation_count(rule, ("closed_names", "prepared_names", "source_names", "filled_names"))
        needed = max(0, self.number(required) - current)
        if needed <= 0:
            return True, ""
        return self.withdraw_master(entry, needed, lambda: self.preparation_count(rule, ("closed_names", "prepared_names", "source_names", "filled_names")), rule.get("shopping_name", resource_id))

    def fill_water(self, rule):
        filled = self.preparation_items(rule, ("filled_names",))
        if filled:
            return True, ""
        filled_serials = set(self.number(getattr(item, "Serial", 0)) for item in filled)
        empty = [item for item in self.preparation_items(rule, ("source_names",)) if self.number(getattr(item, "Serial", 0)) not in filled_serials]
        if not empty:
            ready, message = self.withdraw_preparation(rule, 1)
            if not ready:
                return False, message
            empty = self.preparation_items(rule, ("source_names",))
        if not empty:
            return False, "No empty pitcher could be identified after withdrawal."
        if not self.host.valid_item(self.water_serial):
            return False, "Set a valid Water Trough in Cooking BODs."
        try:
            Target.Cancel()
            Items.UseItem(empty[0])
            if not bool(Target.WaitForTarget(self.timing("water_target_wait_ms", 2500), False)) and not bool(Target.HasTarget()):
                return False, "Using the empty pitcher did not produce a target cursor."
            Target.TargetExecute(self.water_serial)
            Misc.Pause(self.timing("water_fill_pause_ms", 850))
        except Exception as ex:
            return False, "Water fill failed: " + str(ex)
        return (True, "") if self.preparation_items(rule, ("filled_names",)) else (False, "A filled pitcher was not detected.")

    def execute_preparations(self, preparation_units):
        source_reader = getattr(self.host, "craft_source_mode", None)
        source_mode = str(source_reader()) if callable(source_reader) else ""
        if self.manual_sacks and source_mode == "master_shelf":
            for rule_id in preparation_units:
                rule = self.preparation_rule(rule_id)
                if rule and bool(rule.get("master_shelf_optional", False)):
                    return False, "Manual flour/sugar preparation requires the Core source to be Resource Chest or Shelf + Chest. Use direct sack mode only when the server can craft those ingredients from the Master Shelf."
        packages = self.package_requirements(preparation_units)
        for rule_id, logical_units in preparation_units.items():
            rule = self.preparation_rule(rule_id)
            if not rule:
                continue
            action = str(rule.get("action", ""))
            source_key = self.key(rule.get("source_resource_key", ""))
            required = max(1, packages.get(source_key, 1))
            if action == "fill_at_target":
                ready, message = self.fill_water(rule)
                if not ready:
                    return False, message
                continue
            if action != "use_each":
                continue
            prepared = self.preparation_count(rule, ("prepared_names",))
            needed = max(0, required - prepared)
            if needed > 0:
                closed = self.preparation_items(rule, ("closed_names",))
                closed_uses = []
                for item in closed:
                    closed_uses.extend([item] * max(1, self.number(getattr(item, "Amount", 1), 1)))
                if len(closed_uses) < needed:
                    ready, message = self.withdraw_preparation(rule, required)
                    if not ready:
                        return False, message
                    closed = self.preparation_items(rule, ("closed_names",))
                    closed_uses = []
                    for item in closed:
                        closed_uses.extend([item] * max(1, self.number(getattr(item, "Amount", 1), 1)))
                if len(closed_uses) < needed:
                    return False, "Not enough closed {0} package(s) were available.".format(rule.get("shopping_name", source_key))
                for item in closed_uses[:needed]:
                    try:
                        Items.UseItem(item)
                        Misc.Pause(self.timing("prepare_pause_ms", 650))
                    except Exception as ex:
                        return False, "Could not prepare {0}: {1}".format(rule.get("shopping_name", source_key), ex)
        return True, "Cooking-specific ingredient preparation is ready."

    def prepare_external_recipe(self, recipe_id, count=1):
        """Public recursive bridge used by BOD Filler and BOD Book."""
        try:
            _raw, preparation_units = self.recipe_requirements(recipe_id, count)
        except Exception as ex:
            return False, str(ex)
        return self.execute_preparations(preparation_units)

    def prepare_direct_recipe(self, recipe_id, count=1):
        """Prepare only inputs consumed directly by one planned craft stage."""
        try:
            preparation_units = self.direct_preparation_units(recipe_id, count)
        except Exception as ex:
            return False, str(ex)
        return self.execute_preparations(preparation_units)

    # ------------------------------------------------------------
    # BOD scan and fill state machine
    # ------------------------------------------------------------

    def close_bod_gump(self):
        engine = self.bod_engine()
        if engine:
            self.close_gump(engine.profile_int("gump", "gump_id", 0))

    def cooking_record(self, record):
        if not record or str(record.get("module_id", "")) != MODULE_ID:
            return None
        reason = str(record.get("block_reason", ""))
        if reason == "Cooking orders are disabled":
            record["block_reason"] = ""
        return record

    def scan(self):
        engine = self.bod_engine()
        if self.data_error:
            self.announce("Cooking BOD data error: " + self.data_error, BAD_HUE, "Cooking Scan")
            return
        if not engine or engine.data_error:
            self.announce("The BOD Filler parsing engine is unavailable.", BAD_HUE, "Cooking Scan")
            return
        sources = self.source_containers()
        if not sources:
            self.announce("Set BOD source chests in BOD Filler or use the source buttons here.", BAD_HUE, "Cooking Scan")
            return
        self.scan_candidates = []
        seen = set()
        for slot, serial in sources:
            for candidate in engine.container_scan_items(slot, serial):
                candidate_serial = self.number(candidate.get("serial"))
                if candidate_serial > 0 and candidate_serial not in seen:
                    seen.add(candidate_serial)
                    self.scan_candidates.append(candidate)
        self.scan_index = 0
        self.scan_found = 0
        self.scan_skipped = []
        self.orders = []
        self.running = True
        self.state = STATE_SCAN
        self.announce("Scanning {0} possible BOD item(s) through the shared BOD parser.".format(len(self.scan_candidates)), WARN_HUE, "Cooking Scan")

    def scan_step(self):
        engine = self.bod_engine()
        if self.scan_index >= len(self.scan_candidates):
            self.running = False
            self.state = STATE_IDLE
            self.orders.sort(key=self.recipe_cost)
            self.rebuild_shopping()
            if self.orders and (self.host.valid_item(self.master_serial) or self.host.valid_item(self.chef_serial)):
                self.read_storage(False)
            message = "Cooking scan complete: {0} open BOD(s), {1} skipped.".format(len(self.orders), len(self.scan_skipped))
            if self.storage_errors:
                message += " Storage warning: " + " ".join(self.storage_errors)
            elif self.orders:
                message += " Counted {0} Master and {1} Chef row(s).".format(len(self.master_rows), len(self.chef_rows))
            self.announce(message, WARN_HUE if self.storage_errors or not self.orders else GOOD_HUE, "Cooking Shopping")
            return
        candidate = self.scan_candidates[self.scan_index]
        self.scan_index += 1
        serial = self.number(candidate.get("serial"))
        item = self.host.valid_item(serial)
        if not item:
            return
        properties = engine.item_property_lines(item)
        if not engine.is_bod_item(item, properties):
            return
        record = None
        error = ""
        staged = False
        try:
            Misc.Pause(BOD_INSPECT_PAUSE_MS)
            try:
                record = engine.inspect_bod_record(serial, candidate.get("source_serial", 0), candidate.get("source_slot", 0))
            except Exception as first_error:
                if not engine.is_bod_open_failure(first_error):
                    raise
                backpack = getattr(Player, "Backpack", None)
                if not backpack or not engine.move_bod_to_container(serial, backpack.Serial):
                    raise Exception("order could not move to the backpack for inspection")
                staged = True
                record = engine.inspect_bod_record(serial, candidate.get("source_serial", 0), candidate.get("source_slot", 0))
        except Exception as ex:
            error = str(ex)
        finally:
            self.close_bod_gump()
        if staged and self.host.valid_item(serial) and not engine.move_bod_to_container(serial, candidate.get("source_serial", 0)):
            self.stop("Cooking scan stopped: inspected BOD could not return to its source.", BAD_HUE)
            return
        record = self.cooking_record(record)
        if not record:
            return
        self.scan_found += 1
        if record.get("block_reason"):
            error = str(record.get("block_reason"))
        elif self.number(record.get("amount_finished")) < self.number(record.get("amount_to_make")):
            self.orders.append(record)
            self.announce("Scan {0}/{1}: queued {2}.".format(self.scan_index, len(self.scan_candidates), record.get("recipe_name", "Cooking BOD")), GOOD_HUE, "Cooking Scan")
            return
        else:
            error = "already complete"
        self.scan_skipped.append({"serial": serial, "reason": error or "inspection failed"})
        Misc.SendMessage("Cooking BOD scan skipped 0x{0:X}: {1}".format(serial, error or "inspection failed"), WARN_HUE)

    def return_active(self):
        if not self.active:
            return True
        item = self.host.valid_item(self.active.get("serial", 0))
        if not item:
            return True
        engine = self.bod_engine()
        return bool(engine) and engine.move_bod_to_container(item.Serial, self.active.get("source_serial", 0))

    def refresh_active(self, queued):
        serial = self.number(queued.get("serial"))
        if not self.host.valid_item(serial):
            raise Exception("BOD is unavailable")
        record = dict(queued)
        record["source_serial"] = self.number(queued.get("source_serial"))
        record["source_slot"] = self.number(queued.get("source_slot"))
        return record

    def output_matches(self, item, recipe, requested_item_id=0):
        engine = self.bod_engine()
        item_id = self.number(getattr(item, "ItemID", 0))
        ids = engine.recipe_output_ids(recipe) if engine else []
        if self.number(requested_item_id) > 0:
            ids.append(self.number(requested_item_id))
        if item_id in ids:
            return True
        names = engine.recipe_output_names(recipe) if engine else []
        return self.normalize(self.item_name(item, True)) in names

    def recipe_output_snapshot(self, recipe_id, requested_item_id=0):
        recipe = self.recipes.get(str(recipe_id), {})
        result = {}
        for item in self.direct_items(self.host.craft_bag_serial()):
            if self.output_matches(item, recipe, requested_item_id):
                result[self.number(item.Serial)] = max(1, self.number(getattr(item, "Amount", 1), 1))
        return result

    def recipe_output_count(self, recipe_id, requested_item_id=0):
        return sum(self.recipe_output_snapshot(recipe_id, requested_item_id).values())

    def direct_component_requirements(self, recipe_id, output_units=1):
        recipe = self.recipes.get(str(recipe_id), {})
        output_amount = max(1, self.number(recipe.get("output_amount"), 1))
        craft_count = int(math.ceil(float(max(1, self.number(output_units, 1))) / float(output_amount)))
        result = {}
        for resource in recipe.get("resources", []):
            component_id = self.component_recipe_id(resource)
            if not component_id:
                continue
            amount = max(1, self.number(resource.get("amount"), 1)) * craft_count
            result[component_id] = result.get(component_id, 0) + amount
        return result

    def direct_component_counts(self, recipe_id):
        result = {}
        for component_id in self.direct_component_requirements(recipe_id):
            result[component_id] = self.recipe_output_count(component_id)
        return result

    def component_consumption_error(self, recipe_id, before_counts, output_units):
        requirements = self.direct_component_requirements(recipe_id, output_units)
        for component_id, expected in requirements.items():
            before = max(0, self.number(dict(before_counts or {}).get(component_id), 0))
            after = self.recipe_output_count(component_id)
            if before <= 0:
                return "The staged {0} component was missing before the parent craft.".format(self.recipes.get(component_id, {}).get("name", component_id))
            consumed = max(0, before - after)
            if consumed < min(before, expected):
                return "The server did not consume the staged {0} component from the Craft Bag. It may have used a storage copy instead.".format(self.recipes.get(component_id, {}).get("name", component_id))
        return ""

    def output_snapshot(self, record):
        return self.recipe_output_snapshot(record.get("recipe_id", ""), record.get("requested_item_id", 0))

    def new_outputs(self):
        after = self.output_snapshot(self.active)
        result = []
        for serial, amount in after.items():
            if amount > self.before_outputs.get(serial, 0):
                result.append(serial)
        return result

    def staged_component_labels(self):
        labels = []
        seen = set()
        for step in self.batch_plan:
            if step.get("is_final"):
                continue
            recipe_id = str(step.get("recipe_id", ""))
            if not recipe_id or recipe_id in seen:
                continue
            seen.add(recipe_id)
            if self.recipe_output_count(recipe_id) > 0:
                labels.append(str(step.get("recipe_name", recipe_id)))
        return labels

    def start_fill(self, mode):
        if not self.orders:
            self.announce("Scan Cooking BODs before starting a fill pass.", BAD_HUE, "Cooking Fill")
            return
        if self.host.craft_job_api_version() < 13:
            self.announce("Restart FrogCraftingCore.py to load the Cooking subcraft batch bridge.", BAD_HUE, "Cooking Fill")
            return
        if self.host.craft_bag_serial() <= 0:
            self.announce("Enable and set the Core Craft Bag before filling Cooking BODs.", BAD_HUE, "Cooking Fill")
            return
        if self.host.valid_item(self.master_serial) or self.host.valid_item(self.chef_serial):
            self.read_storage(False)
        else:
            self.rebuild_shopping()
        queue = []
        for order in sorted([dict(value) for value in self.orders if not value.get("block_reason")], key=self.recipe_cost):
            remaining = max(0, self.number(order.get("amount_to_make")) - self.number(order.get("amount_finished")))
            if remaining <= 0:
                continue
            order["pass_count"] = remaining
            queue.append(order)
        if not queue:
            self.announce("No unfinished mapped Cooking BODs are available to hand to Core.", WARN_HUE, "Cooking Queue")
            return
        self.mode = mode
        self.queue = queue
        self.queue_index = 0
        self.active = {}
        self.reject_serials = []
        self.completed = 0
        self.partial = 0
        self.deferred = 0
        self.failed = 0
        self.failure_reasons = []
        self.reset_batch_plan()
        self.running = True
        self.state = STATE_PREPARE
        source_reader = getattr(self.host, "craft_source_mode", None)
        source_mode = str(source_reader()) if callable(source_reader) else "Core configured source"
        self.announce("Handing {0} mapped BOD(s) to Core cheapest-first. Core owns crafting and resource checks ({1}).".format(len(self.queue), source_mode), GOOD_HUE, "Cooking Fill")

    def begin_next_order(self):
        self.reset_batch_plan()
        while self.queue_index < len(self.queue):
            queued = self.queue[self.queue_index]
            try:
                self.active = self.refresh_active(queued)
            except Exception as ex:
                self.failed += 1
                self.failure_reasons.append(str(ex))
                self.queue_index += 1
                Misc.SendMessage("Cooking BOD queue failure for {0}: {1}".format(queued.get("recipe_name", "Cooking BOD"), ex), WARN_HUE)
                self.announce("Skipped {0}: {1}".format(queued.get("recipe_name", "Cooking BOD"), ex), WARN_HUE, "Cooking Queue")
                return
            if self.number(self.active.get("amount_finished")) >= self.number(self.active.get("amount_to_make")):
                self.return_active()
                self.completed += 1
                self.queue_index += 1
                self.active = {}
                continue
            self.announce("Preparing {0} ({1}/{2}).".format(self.active.get("recipe_name", "Cooking BOD"), self.active.get("amount_finished", 0), self.active.get("amount_to_make", 0)), GOOD_HUE, "Cooking Prepare")
            remaining = max(0, self.number(self.active.get("amount_to_make")) - self.number(self.active.get("amount_finished")))
            pass_count = min(remaining, max(1, self.number(queued.get("pass_count"), remaining)))
            self.active["pass_end_finished"] = self.number(self.active.get("amount_finished")) + pass_count
            self.zero_accepts = 0
            return
        self.finish_pass()

    def prepare_next_batch(self):
        finished = self.number(self.active.get("amount_finished"))
        total = self.number(self.active.get("amount_to_make"))
        pass_end = min(total, max(finished, self.number(self.active.get("pass_end_finished"), total)))
        desired = max(0, pass_end - finished)
        if desired <= 0:
            self.after_unit()
            return False
        if self.output_snapshot(self.active):
            self.defer_or_stop("Matching final output already exists in the Craft Bag; isolate or remove it before continuing.")
            return False
        try:
            units, plan = self.bounded_batch_plan(self.active.get("recipe_id", ""), desired)
        except Exception as ex:
            self.defer_or_stop("Could not build the Cooking subcraft chain: " + str(ex))
            return False
        if units <= 0 or not plan:
            self.defer_or_stop("Could not build a bounded Cooking batch.")
            return False
        self.batch_plan = plan
        self.batch_plan_index = 0
        self.batch_final_crafted = 0
        self.current_step = {}
        self.before_step_count = 0
        self.before_outputs = {}
        chain = " -> ".join("{0} x{1}".format(step.get("recipe_name", "item"), step.get("amount", 1)) for step in plan)
        self.announce("Cooking batch {0}-{1}: {2}.".format(finished + 1, finished + units, chain), GOOD_HUE, "Cooking Plan")
        return True

    def start_one_craft(self):
        if not self.batch_plan:
            self.prepare_next_batch()
            return
        if self.batch_plan_index >= len(self.batch_plan):
            self.defer_or_stop("Cooking subcraft plan ended before the final output was ready.")
            return

        step = self.batch_plan[self.batch_plan_index]
        recipe_id = str(step.get("recipe_id", ""))
        requested_item_id = self.number(self.active.get("requested_item_id"), 0) if step.get("is_final") else 0
        if not step.get("started"):
            existing = self.recipe_output_count(recipe_id, requested_item_id)
            if step.get("is_final"):
                if existing > 0:
                    self.defer_or_stop("Matching final output already exists in the Craft Bag; isolate or remove it before continuing.")
                    return
                self.before_outputs = self.output_snapshot(self.active)
                step["remaining"] = max(1, self.number(step.get("amount"), 1))
            else:
                step["remaining"] = max(0, self.number(step.get("amount"), 1) - existing)
            step["started"] = True
            step["failures"] = 0
            if self.number(step.get("remaining")) <= 0:
                self.batch_plan_index += 1
                self.current_step = {}
                self.announce("Using staged {0}; advancing to the next Cooking stage.".format(step.get("recipe_name", "component")), GOOD_HUE, "Cooking Subcraft")
                return

        remaining = max(1, self.number(step.get("remaining"), 1))
        reusable_preparation = self.direct_reusable_preparation(recipe_id)
        job_units = 1 if reusable_preparation else remaining
        ready, message = self.prepare_direct_recipe(recipe_id, job_units)
        if not ready:
            self.announce("Preparation warning for {0}: {1} Core will still attempt the mapped craft.".format(step.get("recipe_name", recipe_id), message), WARN_HUE, "Core Cooking")

        self.before_step_count = self.recipe_output_count(recipe_id, requested_item_id)
        self.current_step = step
        self.current_step["job_units"] = job_units
        self.current_step["component_before"] = self.direct_component_counts(recipe_id)
        failure_limit = 1 if reusable_preparation else 0
        staged_components_only = bool(self.direct_component_requirements(recipe_id))
        started, message = self.host.begin_craft_job(self.plugin_id, MODULE_ID, step.get("category_id", ""), recipe_id, job_units, self.active.get("material_choices", {}), "none", None, False, failure_limit, staged_components_only)
        if not started:
            self.defer_or_stop("Core craft could not start {0}: {1}".format(step.get("recipe_name", recipe_id), message))
            return
        self.job_started = True
        self.state = STATE_WAIT_CRAFT
        label = "Cooking Final" if step.get("is_final") else "Cooking Subcraft"
        self.announce("{0} {1}/{2}: Core is crafting {3} x{4}.".format(label, self.batch_plan_index + 1, len(self.batch_plan), step.get("recipe_name", recipe_id), job_units), GOOD_HUE, label)

    def wait_craft_step(self):
        status = self.host.craft_job_status(self.plugin_id)
        if status.get("state") == "running":
            return
        step = self.current_step
        recipe_id = str(step.get("recipe_id", ""))
        requested_item_id = self.number(self.active.get("requested_item_id"), 0) if step.get("is_final") else 0
        job_units = max(1, self.number(step.get("job_units"), 1))
        after_count = self.recipe_output_count(recipe_id, requested_item_id)
        produced = max(0, after_count - self.before_step_count)
        self.host.end_craft_job(self.plugin_id, False)
        self.job_started = False

        if status.get("state") != "complete":
            if produced > 0:
                component_error = self.component_consumption_error(recipe_id, step.get("component_before", {}), produced)
                if component_error:
                    self.stop(component_error + " Staged components were left isolated for review.", BAD_HUE)
                    return
            if step.get("is_final") and produced > 0:
                self.batch_final_crafted += produced
                self.state = STATE_COMBINE
                self.announce("Core stopped after producing {0} final item(s); combining the verified partial batch.".format(self.batch_final_crafted), WARN_HUE, "Cooking Combine")
                return
            if produced > 0:
                step["remaining"] = 0
                self.batch_plan_index += 1
                self.current_step = {}
                self.state = STATE_PREPARE
                self.announce("Core staged a partial {0} batch; continuing downstream with the verified components.".format(step.get("recipe_name", recipe_id)), WARN_HUE, "Cooking Subcraft")
                return
            if self.direct_reusable_preparation(recipe_id):
                step["failures"] = self.number(step.get("failures"), 0) + 1
                maximum_failures = max(1, self.number(self.rules.get("timing", {}).get("max_craft_failures"), 4))
                if self.number(step.get("failures")) < maximum_failures:
                    self.state = STATE_PREPARE
                    self.announce("{0} attempt failed; returning to the plugin to refill its reusable ingredient before retry {1}/{2}.".format(step.get("recipe_name", recipe_id), step.get("failures"), maximum_failures), WARN_HUE, "Cooking Preparation")
                    return
                if not step.get("is_final") and after_count > 0:
                    step["remaining"] = 0
                    self.batch_plan_index += 1
                    self.current_step = {}
                    self.state = STATE_PREPARE
                    self.announce("Reusable preparation retries ended; continuing with the partial {0} batch already staged.".format(step.get("recipe_name", recipe_id)), WARN_HUE, "Cooking Subcraft")
                    return
            self.defer_or_stop("Core cooking stopped during {0}: {1}".format(step.get("recipe_name", recipe_id), status.get("message", "unknown error")))
            return

        completed = max(0, self.number(status.get("completed"), 0))
        verified = max(produced, completed)
        if verified <= 0:
            self.defer_or_stop("Core reported completion, but no verified {0} output appeared in the Craft Bag.".format(step.get("recipe_name", "Cooking")))
            return

        component_error = self.component_consumption_error(recipe_id, step.get("component_before", {}), verified)
        if component_error:
            self.stop(component_error + " Staged components were left isolated for review.", BAD_HUE)
            return

        step["failures"] = 0
        step["remaining"] = max(0, self.number(step.get("remaining"), job_units) - verified)
        if step.get("is_final"):
            self.batch_final_crafted += verified
        if self.number(step.get("remaining")) > 0:
            self.state = STATE_PREPARE
            self.announce("{0} staged; {1} {2} still needed in this batch.".format(verified, step.get("remaining"), step.get("recipe_name", recipe_id)), GOOD_HUE, "Cooking Subcraft")
            return

        if step.get("is_final"):
            outputs = self.new_outputs()
            if not outputs:
                self.defer_or_stop("Core completed the final Cooking batch, but no verified final output appeared in the Craft Bag.")
                return
            self.state = STATE_COMBINE
            self.announce("Final batch verified; combining the Craft Bag with the Cooking BOD.", GOOD_HUE, "Cooking Combine")
            return

        self.batch_plan_index += 1
        self.current_step = {}
        self.state = STATE_PREPARE
        self.announce("Staged {0}; advancing to Cooking stage {1}/{2}.".format(step.get("recipe_name", recipe_id), self.batch_plan_index + 1, len(self.batch_plan)), GOOD_HUE, "Cooking Subcraft")

    def combine_step(self):
        engine = self.bod_engine()
        before = self.number(self.active.get("amount_finished"))
        serial = self.number(self.active.get("serial"))
        if not engine.open_bod_gump(serial):
            self.defer_or_stop("Active Cooking BOD did not open for combining.")
            return
        gump_id = engine.profile_int("gump", "gump_id", 0)
        try:
            Target.Cancel()
            Gumps.SendAction(gump_id, engine.profile_int("gump", "combine_container_button", 4))
            if not bool(Target.WaitForTarget(2500, False)) and not bool(Target.HasTarget()):
                raise Exception("combine target cursor did not appear")
            Target.TargetExecute(self.host.craft_bag_serial())
            Misc.Pause(750)
        except Exception as ex:
            self.close_bod_gump()
            self.defer_or_stop("BOD combine failed: " + str(ex))
            return

        refreshed = None
        if self.host.valid_item(serial) and engine.open_bod_gump(serial):
            try:
                parsed = engine.parse_bod_gump(engine.bod_gump_lines())
                refreshed = self.number(parsed.get("amount_finished"), before)
            except:
                refreshed = None
        self.close_bod_gump()
        leftovers = list(self.output_snapshot(self.active).keys())
        if refreshed is None and not leftovers:
            accepted = max(1, self.batch_final_crafted)
            refreshed = min(self.number(self.active.get("amount_to_make"), before + accepted), before + accepted)
        if refreshed is not None and refreshed > before:
            self.zero_accepts = 0
            self.active["amount_finished"] = refreshed
            for order in self.orders:
                if self.number(order.get("serial")) == serial:
                    order["amount_finished"] = refreshed
                    break
            self.reject_serials = leftovers
            if leftovers:
                self.recycle_attempts = 0
                self.state = STATE_RECYCLE
            else:
                self.after_unit()
            return
        self.reject_serials = leftovers
        if leftovers:
            self.zero_accepts += 1
            self.recycle_attempts = 0
            self.state = STATE_RECYCLE
            self.announce("BOD rejected the cooked output; recycling verified rejects.", WARN_HUE, "Cooking Recycle")
        else:
            self.defer_or_stop("The BOD made no progress and no verified reject remained.")

    def recycle_step(self):
        if not self.reject_serials:
            self.after_unit()
            return
        state, message, remaining = self.host.recycle_craft_bag_contents(self.plugin_id, MODULE_ID, self.active.get("recipe_id", ""), list(self.reject_serials), self.number(self.active.get("requested_item_id"), 0), self.active.get("material_choices", {}))
        if state in ("complete", "leftovers"):
            self.reject_serials = [self.number(serial) for serial in remaining]
            self.recycle_attempts += 1
            if not self.reject_serials:
                self.after_unit()
                return
            if self.recycle_attempts >= max(1, self.number(self.rules.get("timing", {}).get("max_combine_failures"), 4)):
                serial = self.reject_serials[0]
                trash_state, trash_message = self.host.trash_craft_bag_item(self.plugin_id, serial, self.number(self.active.get("requested_item_id"), 0))
                if trash_state != "complete":
                    self.stop("Reject cleanup stopped: {0} {1}".format(message, trash_message), BAD_HUE)
                    return
                self.reject_serials.pop(0)
            return
        if state == "progress":
            return
        self.stop("Reject recycling stopped: " + str(message), BAD_HUE)

    def after_unit(self):
        finished = self.number(self.active.get("amount_finished"))
        total = self.number(self.active.get("amount_to_make"))
        pass_end = min(total, max(finished, self.number(self.active.get("pass_end_finished"), total)))
        self.reset_batch_plan()
        maximum_rejects = max(1, self.number(self.rules.get("timing", {}).get("max_craft_failures"), 4))
        if self.zero_accepts >= maximum_rejects:
            self.defer_or_stop("BOD rejected {0} consecutive verified cooked outputs.".format(self.zero_accepts))
            return
        if finished >= total:
            label = self.active.get("recipe_name", "Cooking BOD")
            if not self.return_active():
                self.stop("Completed BOD could not return to its source.", BAD_HUE)
                return
            self.completed += 1
            self.queue_index += 1
            self.active = {}
            self.state = STATE_PREPARE
            self.announce("Completed {0}; moving to the next Cooking BOD.".format(label), GOOD_HUE, "Cooking Queue")
            return
        if finished >= pass_end:
            label = self.active.get("recipe_name", "Cooking BOD")
            if not self.return_active():
                self.stop("Partially filled BOD could not return to its source.", BAD_HUE)
                return
            self.partial += 1
            self.queue_index += 1
            self.active = {}
            self.state = STATE_PREPARE
            self.announce("Used the currently reserved stock on {0}; moving to the next affordable Cooking BOD.".format(label), GOOD_HUE, "Cooking Queue")
            return
        self.state = STATE_PREPARE
        self.announce("BOD progress {0}/{1}; preparing the next safe Cooking batch.".format(finished, total), GOOD_HUE, "Cooking Fill")

    def defer_or_stop(self, message):
        Misc.SendMessage("Cooking BOD craft result: " + str(message), WARN_HUE)
        staged_components = self.staged_component_labels()
        if staged_components:
            self.stop(message + " Staged subcrafts remain in the Craft Bag ({0}); stopping for safe review.".format(", ".join(staged_components)), BAD_HUE)
            return
        if self.mode == MODE_WHAT_WE_CAN:
            if self.active and self.output_snapshot(self.active):
                self.stop(message + " Verified cooked output remains in the Craft Bag; stopping for safe review.", BAD_HUE)
                return
            if self.active:
                if self.number(self.active.get("amount_finished")) > self.number(self.queue[self.queue_index].get("amount_finished")):
                    self.partial += 1
                else:
                    self.deferred += 1
                self.return_active()
            self.queue_index += 1
            self.active = {}
            self.reset_batch_plan()
            self.state = STATE_PREPARE
            self.announce(message + " Deferred this BOD and continuing.", WARN_HUE, "Cooking Deferred")
        else:
            self.stop(message, BAD_HUE)

    def finish_pass(self):
        self.reset_batch_plan()
        self.active = {}
        self.cleanup_message = "Cooking pass complete: {0} completed, {1} partial, {2} deferred, {3} failed.".format(self.completed, self.partial, self.deferred, self.failed)
        if self.failure_reasons:
            self.cleanup_message += " First failure: " + self.failure_reasons[0]
        starter = getattr(self.host, "begin_craft_cleanup", None)
        if callable(starter):
            started, message = starter(self.plugin_id)
            if started:
                self.running = True
                self.state = STATE_CLEANUP
                self.announce("Cooking pass ended; returning staged materials through the Core cleanup bridge.", WARN_HUE, "Cooking Cleanup")
                return
            self.cleanup_message += " Cleanup warning: " + str(message)
        self.finish_cleanup()

    def finish_cleanup(self):
        message = self.cleanup_message or "Cooking pass complete."
        self.cleanup_message = ""
        self.running = False
        self.state = STATE_IDLE
        self.reset_batch_plan()
        self.rebuild_shopping()
        self.announce(message, GOOD_HUE if self.completed or self.partial else WARN_HUE, "Cooking Complete")

    def stop(self, message="Cooking BOD work stopped.", hue=WARN_HUE):
        if self.job_started:
            self.host.end_craft_job(self.plugin_id, True)
        self.job_started = False
        try:
            Target.Cancel()
        except:
            pass
        self.close_bod_gump()
        if self.active:
            self.return_active()
        self.running = False
        self.state = STATE_IDLE
        self.active = {}
        self.reject_serials = []
        self.reset_batch_plan()
        self.announce(message, hue, "Cooking Stopped")

    def step(self):
        if not self.running:
            return
        if self.state == STATE_SCAN:
            self.scan_step()
        elif self.state == STATE_PREPARE:
            if not self.active:
                self.begin_next_order()
            else:
                self.start_one_craft()
        elif self.state == STATE_WAIT_CRAFT:
            self.wait_craft_step()
        elif self.state == STATE_COMBINE:
            self.combine_step()
        elif self.state == STATE_RECYCLE:
            self.recycle_step()
        elif self.state == STATE_CLEANUP:
            checker = getattr(self.host, "craft_cleanup_active", None)
            if not callable(checker) or not checker(self.plugin_id):
                self.finish_cleanup()
        else:
            self.stop("Cooking BOD workflow entered an unknown state.", BAD_HUE)
        self.host.mark_dirty()

    # ------------------------------------------------------------
    # UI and controls
    # ------------------------------------------------------------

    def source_label(self, slot):
        engine = self.bod_engine()
        serial = engine.chest_one if engine and slot == 1 else (engine.chest_two if engine else 0)
        return self.host.short_text(self.host.item_label(serial, "Not set"), 18)

    def shopping_html(self):
        if not self.shopping_required:
            return "<basefont color=#B8B8B8>Scan Cooking BODs to build a shopping list.</basefont>"
        lines = []
        for key in sorted(self.shopping_required, key=lambda value: self.resource_label(value)):
            required = self.shopping_required.get(key, 0)
            pack = self.shopping_pack.get(key, 0)
            master = self.shopping_master.get(key, 0)
            chef = self.shopping_chef.get(key, 0)
            missing = self.shopping_missing.get(key, 0)
            color = "#66FF66" if missing <= 0 else "#FF8A66"
            text = "{0}: need {1} | pack {2} | master {3} | chef {4}".format(self.html(self.resource_label(key)), required, pack, master, chef)
            if missing > 0:
                text += " | buy {0}".format(missing)
            lines.append("<basefont color={0}>{1}</basefont>".format(color, text))
        return "<br>".join(lines)

    def orders_html(self):
        if not self.orders:
            return "<basefont color=#B8B8B8>No unfinished mapped Cooking BODs.</basefont>"
        active_serial = self.number(self.active.get("serial"))
        lines = []
        for index, order in enumerate(self.orders):
            color = "#FFFF66" if self.number(order.get("serial")) == active_serial else "#DDDDDD"
            suffix = " [Exceptional]" if order.get("exceptional_required") else ""
            text = "{0}. {1}: {2}/{3}{4}".format(index + 1, self.html(order.get("recipe_name", "Cooking BOD")), order.get("amount_finished", 0), order.get("amount_to_make", 0), suffix)
            lines.append("<basefont color={0}>{1}</basefont>".format(color, text))
        return "<br>".join(lines)

    def render(self, gd, x, y, width, height):
        Gumps.AddBackground(gd, x, y, width, height, 3000)
        Gumps.AddAlphaRegion(gd, x, y, width, height)
        Gumps.AddLabel(gd, x + 10, y + 6, TITLE_HUE, "COOKING BOD PLANNER / CORE CRAFT BRIDGE")

        self.host.add_button(gd, x + 10, y + 30, self.button_id(BTN_SET_CHEST_ONE), "Set Chest 1")
        Gumps.AddLabel(gd, x + 115, y + 31, LABEL_HUE, self.source_label(1))
        self.host.add_button(gd, x + 330, y + 30, self.button_id(BTN_SET_CHEST_TWO), "Set Chest 2")
        Gumps.AddLabel(gd, x + 435, y + 31, LABEL_HUE, self.source_label(2))

        self.host.add_button(gd, x + 10, y + 55, self.button_id(BTN_SET_MASTER), "Set Master")
        Gumps.AddLabel(gd, x + 115, y + 56, LABEL_HUE, self.host.short_text(self.host.item_label(self.master_serial, "Not set"), 18))
        self.host.add_button(gd, x + 225, y + 55, self.button_id(BTN_SET_CHEF), "Set Chef")
        Gumps.AddLabel(gd, x + 315, y + 56, LABEL_HUE, self.host.short_text(self.host.item_label(self.chef_serial, "Not set"), 16))
        self.host.add_button(gd, x + 420, y + 55, self.button_id(BTN_SET_WATER), "Set Water")
        Gumps.AddLabel(gd, x + 515, y + 56, LABEL_HUE, self.host.short_text(self.host.item_label(self.water_serial, "Not set"), 15))

        self.host.add_button(gd, x + 10, y + 80, self.button_id(BTN_SCAN), "Scan BODs", GOOD_HUE)
        self.host.add_button(gd, x + 115, y + 80, self.button_id(BTN_READ_STORAGE), "Read Storage", GOOD_HUE)
        self.host.add_button(gd, x + 245, y + 80, self.button_id(BTN_TOGGLE_SACKS), "Sacks: " + ("Open" if self.manual_sacks else "Direct"), WARN_HUE)
        if self.running:
            self.host.add_button(gd, x + 390, y + 80, self.button_id(BTN_STOP), "Stop", BAD_HUE, 4011, 4013)
        else:
            self.host.add_button(gd, x + 390, y + 80, self.button_id(BTN_FILL_READY), "Fill Ready", GOOD_HUE, 4011, 4013)
            self.host.add_button(gd, x + 505, y + 80, self.button_id(BTN_FILL_WHAT_WE_CAN), "Fill What We Can", WARN_HUE, 4011, 4013)

        Gumps.AddLabel(gd, x + 10, y + 108, TITLE_HUE, "SHOPPING LIST")
        Gumps.AddLabel(gd, x + 335, y + 108, TITLE_HUE, "COOKING BODS")
        Gumps.AddHtml(gd, x + 10, y + 130, 310, 173, self.shopping_html(), False, True)
        Gumps.AddHtml(gd, x + 335, y + 130, 305, 173, self.orders_html(), False, True)

    def target_item(self, prompt):
        try:
            Target.Cancel()
            serial = self.number(Target.PromptTarget(prompt), 0)
            return serial if self.host.valid_item(serial) else 0
        except:
            return 0

    def handle_button(self, local_button):
        local_button = self.number(local_button)
        if local_button == BTN_STOP:
            self.stop("Cooking BOD work stopped by player.", WARN_HUE)
            return
        if self.running:
            self.announce("Stop the active Cooking workflow before changing setup.", WARN_HUE, "Cooking Busy")
            return
        engine = self.bod_engine()
        if local_button == BTN_SET_CHEST_ONE and engine:
            engine.set_chest(1)
        elif local_button == BTN_SET_CHEST_TWO and engine:
            engine.set_chest(2)
        elif local_button == BTN_SET_MASTER:
            serial = self.target_item("Target the Artificer Master Shelf.")
            if serial:
                self.master_serial = serial
                self.master_rows = []
                self.save_targets()
                self.announce("Cooking Master Shelf saved.", GOOD_HUE, "Cooking Setup")
        elif local_button == BTN_SET_CHEF:
            serial = self.target_item("Target the Chef Storage Shelf.")
            if serial:
                self.chef_serial = serial
                self.chef_rows = []
                self.save_targets()
                self.announce("Chef Storage Shelf saved.", GOOD_HUE, "Cooking Setup")
        elif local_button == BTN_SET_WATER:
            serial = self.target_item("Target the Water Trough used for pitchers.")
            if serial:
                self.water_serial = serial
                self.save_targets()
                self.announce("Cooking Water Trough saved.", GOOD_HUE, "Cooking Setup")
        elif local_button == BTN_TOGGLE_SACKS:
            self.manual_sacks = not self.manual_sacks
            self.save_targets()
            self.rebuild_shopping()
            self.announce("Flour/sugar sack workaround: {0}.".format("manual open" if self.manual_sacks else "direct shelf craft"), GOOD_HUE, "Cooking Setup")
        elif local_button == BTN_SCAN:
            self.scan()
        elif local_button == BTN_READ_STORAGE:
            if not self.orders:
                self.announce("Scan Cooking BODs before reading storage.", WARN_HUE, "Cooking Storage")
            else:
                self.read_storage(True)
        elif local_button == BTN_FILL_READY:
            self.start_fill(MODE_READY)
        elif local_button == BTN_FILL_WHAT_WE_CAN:
            self.start_fill(MODE_WHAT_WE_CAN)
        elif local_button == BTN_OPEN_BOD and self.active:
            engine.open_bod_gump(self.active.get("serial", 0))
        self.host.mark_dirty()


def create_plugin(host):
    return FrogCookingBODPlugin(host)
