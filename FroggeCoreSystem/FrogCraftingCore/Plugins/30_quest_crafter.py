# ==================================
# ==      Frog Quest Crafter      ==
# ==================================
# Status: In Development

import re
import time


DATA_FILE = "quest_crafter.json"

# Unchained currently labels this Global as Gold Armor but counts Agapite armor.
# Set this to False when the shard-side quest material is corrected.
OVERRIDE_GOLD_ARMOR_TO_AGAPITE = True

BTN_REFRESH = 1
BTN_OPEN = 2
BTN_START = 3
BTN_DIAGNOSTICS = 4
BTN_OPEN_WEEKLY = 5
BTN_WEEKLY_TOGGLE = 6
BTN_START_GLOBAL = 7
BTN_START_WEEKLY = 8
BTN_RULE_BASE = 100

STATE_IDLE = "idle"
STATE_WATCH = "watch"
STATE_CRAFT = "craft"
STATE_CLEANUP = "cleanup"
STATE_REFRESH = "refresh"

WATCH_BOTH = "both"
WATCH_GLOBAL = "global"
WATCH_WEEKLY = "weekly"


class FrogQuestCrafterPlugin:
    plugin_id = "quest_crafter"
    name = "Quest Crafter"
    version = "1.0"
    home_label = "Quest Crafter"

    def __init__(self, host):
        self.host = host
        self.button_base = 0
        self.running = False
        self.state = STATE_IDLE
        self.data = {}
        self.data_error = ""
        try:
            self.data = host.read_data(DATA_FILE)
            if self.data.get("format") != "frog-quest-crafter-data" or self.number(self.data.get("version"), 0) != 1:
                raise Exception("unsupported Quest Crafter data format")
        except Exception as ex:
            self.data_error = str(ex)

        self.command_cooldown_ms = max(0, self.number(self.data.get("command_cooldown_ms"), 4000)) if isinstance(self.data, dict) else 4000
        self.last_command_at = 0.0

        global_data = self.data.get("global", {}) if isinstance(self.data, dict) else {}
        self.gump_id = self.number(global_data.get("gump_id"), 0)
        self.commands = [str(value) for value in global_data.get("commands", []) if str(value).strip()]
        self.open_timeout_ms = max(500, self.number(global_data.get("open_timeout_ms"), 3000))
        self.poll_interval_ms = max(5000, self.number(global_data.get("poll_interval_ms"), 30000))
        self.batch_size = max(1, self.number(global_data.get("batch_size"), 25))
        self.rules = list(self.data.get("quest_rules", [])) if isinstance(self.data, dict) else []
        self.ignored_global_quests = list(self.data.get("ignored_global_quests", [])) if isinstance(self.data, dict) else []

        weekly_data = self.data.get("weekly", {}) if isinstance(self.data, dict) else {}
        self.weekly_data = weekly_data if isinstance(weekly_data, dict) else {}
        self.compendium_gump_id = self.number(self.weekly_data.get("compendium_gump_id"), 0)
        self.compendium_commands = [str(value) for value in self.weekly_data.get("compendium_commands", []) if str(value).strip()]
        self.paperdoll_gump_id = self.number(self.weekly_data.get("paperdoll_gump_id"), 0x1CD)
        self.paperdoll_compendium_button = self.number(self.weekly_data.get("paperdoll_compendium_button"), 1)
        self.paperdoll_compendium_switches = [self.number(value) for value in self.weekly_data.get("paperdoll_compendium_switches", [1739])]
        self.weekly_page_button = self.number(self.weekly_data.get("weekly_page_button"), 0)
        self.weekly_open_timeout_ms = max(500, self.number(self.weekly_data.get("open_timeout_ms"), 3000))
        self.weekly_page_refresh_delay_ms = max(250, self.number(self.weekly_data.get("page_refresh_delay_ms"), 500))
        self.weekly_batch_size = max(1, self.number(self.weekly_data.get("batch_size"), 25))

        self.lines = []
        self.line_source = "none"
        self.quest_active = False
        self.quest_title = ""
        self.description = ""
        self.time_left = ""
        self.next_quest = ""
        self.progress = 0
        self.total = 0
        self.contribution = 0
        self.top_contributor = ""
        self.matched_rule = None
        self.plan = {}
        self.block_reason = "Refresh the Global Quest gump."
        self.message = "Global and Weekly crafting quest automation ready."
        self.batch_target = 0
        self.batch_completed = 0
        self.batches_completed = 0
        self.before_progress = 0
        self.before_contribution = 0
        self.quest_signature = ""
        self.zero_progress_refreshes = 0
        self.next_poll_at = 0.0
        self.skipped_signature = ""
        self.skipped_reason = ""
        self.held_signatures = {}
        self.watch_message = ""
        self.watch_mode = WATCH_BOTH
        self.active_source = ""
        self.active_signature = ""
        self.last_global_plan = {}
        self.global_block_reason = "Refresh the Global Quest gump."
        self.compendium_lines = []
        self.compendium_line_source = "none"
        self.compendium_open_method = "none"
        self.weekly_tasks = []
        self.compendium_tasks = []
        self.weekly_plans = []
        self.weekly_unresolved = []
        self.reported_weekly_unresolved = {}
        self.weekly_given = 0
        self.weekly_limit = 0
        self.weekly_completed = 0

    def number(self, value, fallback=0):
        try:
            return int(str(value), 0)
        except:
            try:
                return int(value)
            except:
                return int(fallback)

    def normalize(self, value):
        text = re.sub(r"<[^>]*>", " ", str(value or ""))
        text = text.replace("&nbsp;", " ").replace("&#160;", " ")
        return " ".join(text.strip().lower().split())

    def clean_line(self, value):
        text = re.sub(r"<[^>]*>", " ", str(value or ""))
        text = text.replace("&nbsp;", " ").replace("&#160;", " ")
        return " ".join(text.strip().split())

    def values(self, source):
        result = []
        try:
            for value in source or []:
                pieces = re.split(r"(?i)(?:<br\s*/?>|\r?\n)", str(value or ""))
                for piece in pieces:
                    line = self.clean_line(piece)
                    if line:
                        result.append(line)
        except:
            pass
        return result

    def button_id(self, local_id):
        return int(self.button_base) + int(local_id)

    def announce(self, message, hue=LABEL_HUE, step="Quest Crafter"):
        self.message = str(message)
        self.host.set_status(self.message, hue, step)
        self.host.mark_dirty()

    def is_priority_button(self, local_button):
        return self.running and int(local_button) in (BTN_START, BTN_START_GLOBAL, BTN_START_WEEKLY)

    def normalized_watch_mode(self, mode=None):
        value = str(mode or self.watch_mode or WATCH_BOTH).lower()
        return value if value in (WATCH_BOTH, WATCH_GLOBAL, WATCH_WEEKLY) else WATCH_BOTH

    def watch_mode_label(self, mode=None):
        value = self.normalized_watch_mode(mode)
        if value == WATCH_GLOBAL:
            return "Globals"
        if value == WATCH_WEEKLY:
            return "Weeklies"
        return "Both"

    def source_enabled(self, source, mode=None):
        watch_mode = self.normalized_watch_mode(mode)
        return watch_mode == WATCH_BOTH or watch_mode == str(source or "").lower()

    def activate(self):
        if self.data_error:
            self.announce("Quest Crafter data error: " + self.data_error, BAD_HUE)
        elif self.host.craft_job_api_version() < 10:
            self.announce("Restart FrogCraftingCore.py to load its Weekly skill-trust bridge.", BAD_HUE)
        else:
            self.announce(self.message, GOOD_HUE)

    def schedule_watch(self, immediate=False):
        if immediate:
            self.next_poll_at = 0.0
        else:
            self.next_poll_at = time.time() + (float(self.poll_interval_ms) / 1000.0)

    def watch_announce(self, message, hue=WARN_HUE, step="Quest Watch"):
        text = str(message)
        if text != self.watch_message:
            self.watch_message = text
            self.announce(text, hue, step)
        else:
            self.host.mark_dirty()

    def enter_watch(self, message, hue=WARN_HUE, skip_current=False):
        if skip_current and (self.active_signature or self.plan.get("signature", "")):
            held_signature = str(self.active_signature or self.plan.get("signature", ""))
            self.held_signatures[held_signature] = str(message)
        self.running = True
        self.state = STATE_WATCH
        self.batch_target = 0
        self.batch_completed = 0
        self.schedule_watch(False)
        self.watch_announce(message, hue, "Quest Watch")

    def hold_current_quest(self, message, hue=WARN_HUE):
        if self.state == STATE_CRAFT:
            self.host.end_craft_job(self.plugin_id, True)
        self.enter_watch(message, hue, True)

    def stop(self, message, hue=WARN_HUE):
        if self.state == STATE_CRAFT:
            self.host.end_craft_job(self.plugin_id, True)
        self.running = False
        self.state = STATE_IDLE
        self.batch_target = 0
        self.batch_completed = 0
        self.next_poll_at = 0.0
        self.watch_message = ""
        self.active_source = ""
        self.active_signature = ""
        self.announce(message, hue)

    def deactivate(self, message=None):
        if self.running:
            self.stop(message or "Quest Crafter paused.")

    def shutdown(self):
        if self.running and self.state == STATE_CRAFT:
            self.host.end_craft_job(self.plugin_id, True)
        self.running = False
        self.state = STATE_IDLE

    def gump_is_open(self, gump_id=None):
        wanted_id = self.gump_id if gump_id is None else self.number(gump_id, 0)
        if wanted_id <= 0:
            return False
        try:
            return bool(Gumps.HasGump(wanted_id))
        except:
            try:
                return Gumps.GetGumpData(wanted_id) is not None
            except:
                try:
                    return bool(Gumps.HasGump()) and self.number(Gumps.CurrentGump(), 0) == wanted_id
                except:
                    return False

    def wait_for_command_cooldown(self):
        if self.command_cooldown_ms <= 0 or self.last_command_at <= 0.0:
            return
        elapsed_ms = int((time.time() - self.last_command_at) * 1000.0)
        remaining_ms = self.command_cooldown_ms - elapsed_ms
        if remaining_ms > 0:
            Misc.Pause(remaining_ms)

    def open_command_gump(self, gump_id, commands, timeout_ms):
        wanted_id = self.number(gump_id, 0)
        if wanted_id <= 0:
            return False
        for command in commands:
            try:
                Gumps.CloseGump(wanted_id)
                Gumps.ResetGump()
                self.wait_for_command_cooldown()
                Player.ChatSay(command)
                self.last_command_at = time.time()
                Gumps.WaitForGump(wanted_id, timeout_ms)
                if self.gump_is_open(wanted_id):
                    Misc.Pause(250)
                    return True
            except:
                pass
        return False

    def open_global_quest(self):
        return self.open_command_gump(self.gump_id, self.commands, self.open_timeout_ms)

    def open_compendium_from_paperdoll(self):
        if self.paperdoll_gump_id <= 0 or self.paperdoll_compendium_button <= 0:
            return False
        if not self.gump_is_open(self.paperdoll_gump_id):
            return False
        try:
            Gumps.CloseGump(self.compendium_gump_id)
            Gumps.SendAdvancedAction(self.paperdoll_gump_id, self.paperdoll_compendium_button, list(self.paperdoll_compendium_switches), [], [])
            Gumps.WaitForGump(self.compendium_gump_id, self.weekly_open_timeout_ms)
            if self.gump_is_open(self.compendium_gump_id):
                Misc.Pause(250)
                return True
        except:
            pass
        return False

    def open_compendium_weekly(self):
        if self.gump_is_open(self.compendium_gump_id):
            self.compendium_open_method = "page"
        elif self.open_compendium_from_paperdoll():
            self.compendium_open_method = "paperdoll"
        elif self.open_command_gump(self.compendium_gump_id, self.compendium_commands, self.weekly_open_timeout_ms):
            self.compendium_open_method = "command"
        else:
            self.compendium_open_method = "none"
            return False
        try:
            Gumps.SendAction(self.compendium_gump_id, self.weekly_page_button)
            Misc.Pause(self.weekly_page_refresh_delay_ms)
            Gumps.WaitForGump(self.compendium_gump_id, self.weekly_open_timeout_ms)
            deadline = time.time() + (float(self.weekly_open_timeout_ms) / 1000.0)
            while time.time() < deadline:
                if self.gump_is_open(self.compendium_gump_id):
                    _source, lines = self.read_gump_lines(self.compendium_gump_id)
                    normalized = [self.normalize(line) for line in lines]
                    if any("crafting tasks" in value for value in normalized):
                        return True
                Misc.Pause(100)
            return False
        except:
            return False

    def read_gump_lines(self, gump_id=None):
        wanted_id = self.gump_id if gump_id is None else self.number(gump_id, 0)
        sources = []
        try:
            sources.append(("GetLineList", self.values(Gumps.GetLineList(wanted_id, False))))
        except:
            pass
        try:
            data = Gumps.GetGumpData(wanted_id)
            sources.append(("GumpData.gumpStrings", self.values(getattr(data, "gumpStrings", None))))
        except:
            pass
        try:
            if self.number(Gumps.CurrentGump(), 0) == wanted_id:
                sources.append(("LastGumpGetLineList", self.values(Gumps.LastGumpGetLineList())))
        except:
            pass
        try:
            if self.number(Gumps.CurrentGump(), 0) == wanted_id:
                sources.append(("LastGumpRawText", self.values(Gumps.LastGumpRawText())))
        except:
            pass
        sources = [record for record in sources if record[1]]
        if not sources:
            return "none", []
        sources.sort(key=lambda record: len(record[1]), reverse=True)
        return sources[0]

    def value_after(self, lines, header):
        wanted = self.normalize(header)
        headers = (
            "global quest", "time left", "progression", "progress",
            "top contributor (#1)", "top contributor", "your contribution", "next quest in",
        )
        for index, line in enumerate(lines):
            if self.normalize(line) != wanted:
                continue
            for candidate in lines[index + 1:index + 4]:
                normalized = self.normalize(candidate)
                if normalized and normalized not in headers:
                    return str(candidate)
        return ""

    def allowed(self, rule):
        fallback = 1 if bool(rule.get("default_allowed", False)) else 0
        key = "quest_crafter_allow_" + str(rule.get("id", ""))
        return self.host.read_int(key, fallback) > 0

    def toggle_rule(self, rule):
        key = "quest_crafter_allow_" + str(rule.get("id", ""))
        self.host.write_int(key, 0 if self.allowed(rule) else 1)
        self.build_plan()
        self.announce("Quest filter updated. Refresh before starting.", GOOD_HUE)

    def weekly_allowed(self):
        fallback = 1 if bool(self.weekly_data.get("default_allowed", True)) else 0
        return self.host.read_int("quest_crafter_allow_weekly", fallback) > 0

    def toggle_weekly(self):
        self.host.write_int("quest_crafter_allow_weekly", 0 if self.weekly_allowed() else 1)
        self.announce("Weekly crafting filter updated. Refresh before starting.", GOOD_HUE)

    def match_rule(self, title):
        for rule in self.rules:
            if not bool(rule.get("enabled", False)):
                continue
            pattern = str(rule.get("title_pattern", ""))
            if not pattern:
                continue
            try:
                match = re.match(pattern, str(title), re.IGNORECASE)
            except:
                match = None
            if match:
                return rule, match
        return None, None

    def ignored_global_reason(self, title):
        for entry in self.ignored_global_quests:
            if not isinstance(entry, dict):
                continue
            pattern = str(entry.get("title_pattern", ""))
            if not pattern:
                continue
            try:
                matched = re.match(pattern, str(title or ""), re.IGNORECASE)
            except:
                matched = None
            if matched:
                return str(entry.get("reason", "Known non-crafting Global Quest."))
        return ""

    def parse_gump(self, raw_lines):
        lines = [self.clean_line(value) for value in raw_lines if self.clean_line(value)]
        self.lines = lines
        self.quest_active = False
        self.quest_title = ""
        self.description = ""
        self.time_left = ""
        self.next_quest = ""
        self.progress = 0
        self.total = 0
        self.contribution = 0
        self.top_contributor = ""
        self.matched_rule = None
        self.plan = {}

        normalized = [self.normalize(value) for value in lines]
        if any("no active global quest" in value for value in normalized):
            self.next_quest = self.value_after(lines, "NEXT QUEST IN")
            self.block_reason = "No active Global Quest."
            return

        matched_rule = None
        matched_title = None
        for line in lines:
            matched_rule, _title_match = self.match_rule(line)
            if matched_rule:
                matched_title = line
                break

        if not matched_title:
            ignored = (
                "global quest", "time left", "progression", "progress",
                "top contributor (#1)", "top contributor", "your contribution", "next quest in",
            )
            try:
                start = normalized.index("global quest") + 1
            except:
                start = 0
            for index in range(start, len(lines)):
                value = normalized[index]
                if value in ignored or value.startswith("craft ") or re.search(r"\d+\s*/\s*\d+", value):
                    continue
                matched_title = lines[index]
                break

        self.quest_title = str(matched_title or "Unknown active quest")
        self.matched_rule = matched_rule
        for line in lines:
            if self.normalize(line).startswith("craft ") and " point" in self.normalize(line):
                self.description = line
                break
        self.time_left = self.value_after(lines, "TIME LEFT")
        self.top_contributor = self.value_after(lines, "TOP CONTRIBUTOR (#1)") or self.value_after(lines, "TOP CONTRIBUTOR")
        contribution_text = self.value_after(lines, "YOUR CONTRIBUTION")
        contribution_match = re.search(r"\b(\d+)\b", contribution_text)
        self.contribution = int(contribution_match.group(1)) if contribution_match else 0

        for line in lines:
            progress_match = re.search(r"\b(\d+)\s*/\s*(\d+)\b", line)
            if progress_match:
                self.progress = int(progress_match.group(1))
                self.total = int(progress_match.group(2))
                break

        if matched_rule and self.description:
            pattern = str(matched_rule.get("description_pattern", ""))
            try:
                description_match = re.match(pattern, self.description, re.IGNORECASE) if pattern else None
            except:
                description_match = None
            if description_match:
                total_group = self.number(matched_rule.get("description_total_group"), 0)
                if self.total <= 0 and total_group > 0:
                    self.total = self.number(description_match.group(total_group), 0)

        self.quest_active = bool(self.quest_title) and self.total > 0 and self.progress < self.total
        if self.total > 0 and self.progress >= self.total:
            self.block_reason = "The Global Quest is already complete."
        elif not self.quest_active:
            self.block_reason = "Active quest data was incomplete; use Diagnostics."

    def match_key(self, value):
        return " ".join(re.sub(r"[^a-z0-9]+", " ", self.normalize(value)).split())

    def compact_key(self, value):
        return self.match_key(value).replace(" ", "")

    def progress_segments(self, lines, lookback=8):
        segments = []
        previous_progress = -1
        for index, line in enumerate(lines):
            if not re.search(r"\d+\s*/\s*\d+", str(line)):
                continue
            first = max(previous_progress + 1, index - max(1, int(lookback)))
            variants = []
            for start in range(index, first - 1, -1):
                text = self.clean_line(" ".join([str(value) for value in lines[start:index + 1]]))
                if text:
                    variants.append(text)
            segments.append(variants)
            previous_progress = index
        return segments

    def weekly_recipe_index(self):
        index = {}
        for module in self.host.modules():
            module_id = str(module.get("id", ""))
            for category in module.get("categories", []):
                for recipe in category.get("recipes", []):
                    if not bool(recipe.get("enabled", False)):
                        continue
                    names = [recipe.get("name", ""), str(recipe.get("id", "")).replace("_", " ")]
                    names.extend(recipe.get("output_names", []))
                    if module_id == "inscription":
                        names.extend([str(value) + " Scroll" for value in list(names) if value and "scroll" not in self.normalize(value)])
                    record = (module, category, recipe)
                    for name in names:
                        key = self.match_key(name)
                        if not key:
                            continue
                        bucket = index.setdefault(key, [])
                        identity = (module_id, str(recipe.get("id", "")))
                        if not any((str(item[0].get("id", "")), str(item[2].get("id", ""))) == identity for item in bucket):
                            bucket.append(record)
        return index

    def resolve_weekly_recipe(self, item_name, allow_suffix=False):
        key = self.match_key(item_name)
        aliases = self.weekly_data.get("recipe_aliases", {}) if isinstance(self.weekly_data.get("recipe_aliases", {}), dict) else {}
        index = self.weekly_recipe_index()
        candidates = [key]
        if allow_suffix:
            known = list(aliases.keys()) + list(index.keys())
            suffixes = [self.match_key(value) for value in known if key.endswith(" " + self.match_key(value))]
            suffixes.sort(key=len, reverse=True)
            candidates.extend(suffixes)
        checked = set()
        for candidate in candidates:
            if not candidate or candidate in checked:
                continue
            checked.add(candidate)
            alias = aliases.get(candidate)
            if isinstance(alias, dict):
                module, category, recipe = self.find_recipe(alias.get("module_id", ""), alias.get("recipe_id", ""))
                if module and category and recipe and bool(recipe.get("enabled", False)):
                    return module, category, recipe, candidate, ""
            records = index.get(candidate, [])
            if len(records) == 1:
                module, category, recipe = records[0]
                return module, category, recipe, candidate, ""
            if len(records) > 1 and candidate == key:
                return None, None, None, candidate, "Weekly recipe name '{0}' matches more than one FCC recipe.".format(item_name)
        return None, None, None, key, "No FCC recipe matches weekly item '{0}'.".format(item_name)

    def split_compendium_label(self, value):
        text = self.clean_line(value).rstrip(":").strip()
        parenthetical = re.match(r"^(.+?)\s*\(([^()]*)\)\s*$", text)
        if parenthetical:
            return self.clean_line(parenthetical.group(1)), self.clean_line(parenthetical.group(2))
        aliases = self.weekly_data.get("material_aliases", {}) if isinstance(self.weekly_data.get("material_aliases", {}), dict) else {}
        material_names = sorted([str(name) for name in aliases.keys() if str(name).strip()], key=len, reverse=True)
        for material_name in material_names:
            match = re.search(r"(?:^|\s)" + re.escape(material_name) + r"$", text, re.IGNORECASE)
            if not match:
                continue
            item_name = self.clean_line(text[:match.start()])
            if item_name:
                return item_name, self.clean_line(text[match.start():])
        return text, ""

    def parse_compendium_lines(self, raw_lines):
        lines = [self.clean_line(value) for value in raw_lines if self.clean_line(value)]
        joined = " ".join(lines)
        completed_match = re.search(r"Completed\s*:\s*(\d+)\s*/\s*(\d+)\s*tasks?", joined, re.IGNORECASE)
        if completed_match:
            self.weekly_completed = self.number(completed_match.group(1), 0)
            self.weekly_given = self.number(completed_match.group(2), 0)
            self.weekly_limit = self.weekly_given
        else:
            self.weekly_completed = 0
            self.weekly_given = 0
            self.weekly_limit = 0
        rows = []
        seen = set()
        for variants in self.progress_segments(lines, 10):
            resolved = None
            parsed = None
            for candidate in variants:
                match = re.search(r"(\d+)\s*/\s*(\d+)\s*$", candidate)
                if not match:
                    continue
                raw_name, material = self.split_compendium_label(candidate[:match.start()])
                current = self.number(match.group(1), 0)
                total = self.number(match.group(2), 0)
                if not raw_name or total <= 0 or self.normalize(raw_name).startswith("completed"):
                    continue
                module, category, recipe, matched_name, error = self.resolve_weekly_recipe(raw_name, True)
                record = {
                    "name": raw_name,
                    "matched_name": matched_name or self.match_key(raw_name),
                    "material": material,
                    "current": current,
                    "total": total,
                    "requested": total,
                    "module": module,
                    "category": category,
                    "recipe": recipe,
                    "parse_error": error,
                }
                if module and category and recipe:
                    resolved = record
                    break
                if parsed is None or (material and not parsed.get("material")):
                    parsed = record
            row = resolved or parsed
            if not row:
                continue
            identity = "{0}|{1}|{2}".format(self.match_key(row.get("matched_name", row.get("name", ""))), self.compact_key(row.get("material", "")), row.get("total", 0))
            if identity in seen:
                continue
            seen.add(identity)
            row["job_signature"] = identity
            rows.append(row)
        return lines, rows

    def weekly_material_id(self, value, group_id=""):
        normalized = self.normalize(value)
        compact = self.compact_key(value)
        implicit_rules = self.weekly_data.get("implicit_choice_materials", {}) if isinstance(self.weekly_data.get("implicit_choice_materials", {}), dict) else {}
        implicit_rule = implicit_rules.get(normalized, implicit_rules.get(compact))
        if group_id and isinstance(implicit_rule, dict):
            contextual_id = str(implicit_rule.get(str(group_id), "") or "")
            if contextual_id:
                return contextual_id
        aliases = self.weekly_data.get("material_aliases", {}) if isinstance(self.weekly_data.get("material_aliases", {}), dict) else {}
        return str(aliases.get(normalized, aliases.get(compact, "")) or "")

    def weekly_material_option(self, module, group_id, material):
        group = None
        for candidate in module.get("resource_choice_groups", []):
            if str(candidate.get("id", "")) == str(group_id):
                group = candidate
                break
        if not group:
            return None, "FCC material group is unavailable: " + str(group_id)
        wanted = self.weekly_material_id(material, group_id)
        for option in group.get("options", []):
            option_id = str(option.get("id", ""))
            if wanted and option_id == wanted:
                return option, ""
            if not wanted and self.compact_key(material) in (self.compact_key(option_id), self.compact_key(option.get("name", ""))):
                return option, ""
        return None, "No FCC {0} material matches weekly value '{1}'.".format(group.get("name", group_id), material)

    def find_recipe(self, module_id, recipe_id):
        module = self.host.module(module_id)
        if not module:
            return None, None, None
        for category in module.get("categories", []):
            for recipe in category.get("recipes", []):
                if str(recipe.get("id", "")) == str(recipe_id):
                    return module, category, recipe
        return module, None, None

    def title_match_for_rule(self, rule):
        try:
            return re.match(str(rule.get("title_pattern", "")), self.quest_title, re.IGNORECASE)
        except:
            return None

    def recipe_id_for_rule(self, rule):
        fixed_id = str(rule.get("recipe_id", "") or "").strip()
        if fixed_id:
            return fixed_id, ""
        aliases = rule.get("recipe_aliases", {}) if isinstance(rule.get("recipe_aliases", {}), dict) else {}
        group_id = self.number(rule.get("title_recipe_group"), 0)
        title_match = self.title_match_for_rule(rule)
        requested = ""
        if title_match and group_id > 0:
            try:
                captured = title_match.group(group_id)
                requested = str(captured or "").strip()
            except:
                requested = ""
        normalized = self.normalize(requested)
        candidates = [normalized]
        if normalized.endswith(" potions"):
            candidates.append(normalized[:-1])
        for candidate in candidates:
            recipe_id = str(aliases.get(candidate, "") or "").strip()
            if recipe_id:
                return recipe_id, ""
        return "", "No FCC recipe alias matches quest request '{0}'.".format(requested or self.quest_title)

    def points_setting_key(self, rule_id, recipe_id):
        return "quest_crafter_points_{0}_{1}".format(self.normalize(rule_id).replace(" ", "_"), self.normalize(recipe_id).replace(" ", "_"))

    def material_from_match(self, rule):
        material = str(rule.get("default_material", "") or "").strip()
        title_match = self.title_match_for_rule(rule)
        title_group = self.number(rule.get("title_material_group"), 0)
        if title_match and title_group > 0:
            try:
                captured = title_match.group(title_group)
                if captured:
                    material = str(captured).strip()
            except:
                pass

        if self.description:
            try:
                description_match = re.match(str(rule.get("description_pattern", "")), self.description, re.IGNORECASE)
            except:
                description_match = None
            description_group = self.number(rule.get("description_material_group"), 0)
            if description_match and description_group > 0:
                description_material = str(description_match.group(description_group)).strip()
                if material and self.normalize(material) != self.normalize(description_material):
                    return "", "Quest title and description report different materials."
                material = description_material
        return material, ""

    def override_global_material(self, rule, reported_material):
        effective_material = str(reported_material or "").strip()
        if (
            OVERRIDE_GOLD_ARMOR_TO_AGAPITE
            and str(rule.get("id", "")) == "armory_armor"
            and self.normalize(reported_material) == "gold"
        ):
            return "agapite", "Server override: quest reports Gold Armor; crafting Agapite."
        return effective_material, ""

    def material_option(self, module, group_id, material, rule):
        group = None
        for candidate in module.get("resource_choice_groups", []):
            if str(candidate.get("id", "")) == str(group_id):
                group = candidate
                break
        if not group:
            return None, "FCC material group is unavailable: " + str(group_id)
        aliases = rule.get("material_aliases", {}) if isinstance(rule.get("material_aliases", {}), dict) else {}
        wanted = str(aliases.get(self.normalize(material), ""))
        if not wanted and not self.normalize(material):
            wanted = str(rule.get("default_choice", "") or "")
        for option in group.get("options", []):
            option_id = str(option.get("id", ""))
            if wanted and option_id == wanted:
                return option, ""
            if not wanted and self.normalize(material) in (self.normalize(option_id), self.normalize(option.get("name", ""))):
                return option, ""
        return None, "No FCC {0} material matches '{1}'.".format(group.get("name", group_id), material)

    def skill_error(self, module, recipe):
        checks = [(str(module.get("skill_name", module.get("name", "Skill"))), recipe.get("min_skill"))]
        for requirement in recipe.get("skill_requirements", []):
            checks.append((str(requirement.get("skill_name", "Skill")), requirement.get("min_skill")))
        for skill_name, raw_minimum in checks:
            try:
                minimum = float(raw_minimum)
            except:
                return "Recipe skill data is incomplete."
            if self.host.pending_template_for_skill(skill_name) > 0:
                continue
            current = self.host.skill_value(skill_name)
            if current < minimum:
                return "Need {0} {1:.1f}; current {2:.1f}.".format(skill_name, minimum, current)
        return ""

    def resource_rows(self, recipe, selected_option, choice_group):
        rows = []
        for resource in recipe.get("resources", []):
            amount = max(1, self.number(resource.get("amount"), 1))
            if choice_group and selected_option and str(resource.get("choice_group", "")) == str(choice_group):
                name = str(selected_option.get("name", choice_group))
            else:
                name = str(resource.get("name", resource.get("resource_key", "Resource"))).replace("_", " ").title()
            rows.append((name, amount))
        return rows

    def implicit_fixed_material_label(self, recipe, material):
        rules = self.weekly_data.get("implicit_fixed_materials", {}) if isinstance(self.weekly_data.get("implicit_fixed_materials", {}), dict) else {}
        rule = rules.get(self.normalize(material))
        if not isinstance(rule, dict):
            return ""
        expected = sorted([self.normalize(value).replace(" ", "_") for value in rule.get("resource_keys", []) if str(value).strip()])
        actual = []
        for resource in recipe.get("resources", []):
            if str(resource.get("choice_group", "") or ""):
                return ""
            resource_key = self.normalize(resource.get("resource_key", "")).replace(" ", "_")
            if not resource_key:
                return ""
            actual.append(resource_key)
        if actual and sorted(set(actual)) == sorted(set(expected)):
            return str(rule.get("label", material or "Standard resources"))
        return ""

    def requirement_text(self, rows, crafts):
        return ", ".join(["{0} x{1}".format(name, amount * max(0, int(crafts))) for name, amount in rows])

    def build_weekly_plans(self):
        self.weekly_plans = []
        self.weekly_unresolved = []
        for task in self.weekly_tasks:
            module = task.get("module")
            category = task.get("category")
            recipe = task.get("recipe")
            exact_name = str(task.get("matched_name", task.get("name", "")))
            material = str(task.get("material", ""))
            if not module or not category or not recipe:
                self.weekly_unresolved.append("{0}: {1}".format(task.get("name", "Task"), task.get("parse_error", "No FCC recipe mapping is available.")))
                continue

            choice_groups = []
            for resource in recipe.get("resources", []):
                group_id = str(resource.get("choice_group", "") or "")
                if group_id and group_id not in choice_groups:
                    choice_groups.append(group_id)
            if len(choice_groups) > 1:
                self.weekly_unresolved.append("{0}: recipe uses more than one material choice group.".format(task.get("name", "Task")))
                continue
            choice_group = choice_groups[0] if choice_groups else ""
            option = None
            fixed_material_label = ""
            if choice_group:
                if not material:
                    self.weekly_unresolved.append("{0}: weekly material was not readable.".format(task.get("name", "Task")))
                    continue
                option, option_error = self.weekly_material_option(module, choice_group, material)
                if not option:
                    self.weekly_unresolved.append("{0}: {1}".format(task.get("name", "Task"), option_error))
                    continue
            elif material:
                fixed_material_label = self.implicit_fixed_material_label(recipe, material)
                if not fixed_material_label:
                    self.weekly_unresolved.append("{0}: weekly reports material '{1}', but the FCC recipe has no matching fixed-material rule.".format(task.get("name", "Task"), material))
                    continue

            remaining = max(0, self.number(task.get("total"), 0) - self.number(task.get("current"), 0))
            if remaining <= 0:
                continue
            batch = min(self.weekly_batch_size, remaining)
            rows = self.resource_rows(recipe, option, choice_group)
            display_material = str(option.get("name", material)) if option else (fixed_material_label or "Standard resources")
            signature = "weekly|{0}|{1}|{2}".format(task.get("job_signature", ""), module.get("id", ""), recipe.get("id", ""))
            self.weekly_plans.append({
                "source": "weekly",
                "focus": "weekly",
                "ignore_skill_requirements": bool(self.weekly_data.get("trust_player_skill", True)),
                "signature": signature,
                "job_signature": str(task.get("job_signature", "")),
                "task_name": str(task.get("name", "")),
                "exact_name": exact_name,
                "module_id": str(module.get("id", "")),
                "module_name": str(module.get("name", module.get("id", ""))),
                "category_id": str(category.get("id", "")),
                "recipe_id": str(recipe.get("id", "")),
                "recipe_name": str(recipe.get("name", exact_name)),
                "choice_group": choice_group,
                "choice_id": str(option.get("id", "")) if option else "",
                "material": display_material,
                "progress": self.number(task.get("current"), 0),
                "total": self.number(task.get("total"), 0),
                "remaining": remaining,
                "batch": batch,
                "resources": rows,
                "per_craft": self.requirement_text(rows, 1),
                "batch_need": self.requirement_text(rows, batch),
                "remaining_need": self.requirement_text(rows, remaining),
            })

    def report_weekly_unresolved(self):
        current = {}
        for problem in self.weekly_unresolved:
            text = str(problem)
            current[text] = True
            if text not in self.reported_weekly_unresolved:
                Misc.SendMessage("Quest Crafter Weekly unresolved: " + text, BAD_HUE)
        if self.reported_weekly_unresolved and not current:
            Misc.SendMessage("Quest Crafter: all current Weekly crafting tasks now resolve.", GOOD_HUE)
        self.reported_weekly_unresolved = current

    def refresh_weeklies(self, announce_result=True):
        if not self.open_compendium_weekly():
            if announce_result:
                self.announce("Compendium Weekly page on gump 0x{0:08X} did not open.".format(self.compendium_gump_id), BAD_HUE, "Weekly Refresh")
            return False
        self.compendium_line_source, raw_lines = self.read_gump_lines(self.compendium_gump_id)
        if not raw_lines:
            if announce_result:
                self.announce("Compendium Weekly page opened but exposed no readable text.", BAD_HUE, "Weekly Parse")
            return False
        self.compendium_lines, self.compendium_tasks = self.parse_compendium_lines(raw_lines)
        self.weekly_tasks = [task for task in self.compendium_tasks if self.number(task.get("current"), 0) < self.number(task.get("total"), 0)]
        self.build_weekly_plans()
        self.report_weekly_unresolved()
        if announce_result:
            self.announce(
                "Compendium Weekly parsed: {0} row(s), {1} incomplete, {2} ready, {3} unresolved.".format(
                    len(self.compendium_tasks), len(self.weekly_tasks), len(self.weekly_plans), len(self.weekly_unresolved)
                ),
                GOOD_HUE if self.weekly_plans or not self.weekly_tasks else WARN_HUE,
                "Weekly Ready" if self.weekly_plans else "Weekly Parse",
            )
        self.host.mark_dirty()
        return True

    def select_available_plan(self, mode=None):
        watch_mode = self.normalized_watch_mode(mode)
        candidates = []
        if self.source_enabled(WATCH_GLOBAL, watch_mode) and self.last_global_plan:
            candidates.append(dict(self.last_global_plan))
        if self.source_enabled(WATCH_WEEKLY, watch_mode) and self.weekly_allowed():
            candidates.extend([dict(plan) for plan in self.weekly_plans])
        available_signatures = [str(candidate.get("signature", "")) for candidate in candidates if candidate.get("signature")]
        for signature in list(self.held_signatures.keys()):
            if signature not in available_signatures:
                del self.held_signatures[signature]
        for candidate in candidates:
            signature = str(candidate.get("signature", ""))
            if signature and signature in self.held_signatures:
                continue
            self.plan = candidate
            self.block_reason = ""
            self.active_source = str(candidate.get("source", ""))
            self.active_signature = signature
            return True
        self.plan = {}
        self.active_source = ""
        self.active_signature = ""
        return False

    def refresh_all(self, announce_result=True, mode=WATCH_BOTH):
        watch_mode = self.normalized_watch_mode(mode)
        self.plan = {}
        global_ok = False
        weekly_ok = False
        if self.source_enabled(WATCH_GLOBAL, watch_mode):
            global_ok = self.refresh_quest(False)
            self.last_global_plan = dict(self.plan) if global_ok and self.plan and not self.block_reason else {}
            self.global_block_reason = str(self.block_reason)
        if self.source_enabled(WATCH_WEEKLY, watch_mode):
            weekly_ok = self.refresh_weeklies(False)
        selected = self.select_available_plan(watch_mode)
        if announce_result:
            if selected:
                self.announce(
                    "Selected {0}: {1} x{2}.".format(self.active_source.title(), self.plan.get("recipe_name", "recipe"), self.plan.get("batch", 0)),
                    GOOD_HUE,
                    "Quest Ready",
                )
            else:
                reasons = []
                if self.source_enabled(WATCH_GLOBAL, watch_mode) and self.global_block_reason:
                    reasons.append(self.global_block_reason)
                if self.source_enabled(WATCH_WEEKLY, watch_mode):
                    if not self.weekly_allowed():
                        reasons.append("Weekly crafting is filtered out.")
                    elif self.weekly_unresolved:
                        reasons.append(self.weekly_unresolved[0])
                    elif not self.weekly_tasks:
                        reasons.append("No incomplete weekly crafting tasks.")
                self.block_reason = " ".join(reasons) or "No eligible crafting quest is available."
                self.announce(self.block_reason, WARN_HUE, "Quest Idle")
        return global_ok or weekly_ok

    def build_plan(self):
        self.plan = {}
        if not self.quest_active:
            return
        ignored_reason = self.ignored_global_reason(self.quest_title)
        if ignored_reason:
            self.block_reason = "Known Global skipped: {0}. {1}".format(self.quest_title, ignored_reason)
            return
        rule = self.matched_rule
        if not rule:
            self.block_reason = "This Global Quest is not mapped as an allowed crafting quest."
            return
        if not self.allowed(rule):
            self.block_reason = str(rule.get("label", rule.get("id", "Quest"))) + " is disabled by its filter."
            return

        module_id = str(rule.get("module_id", ""))
        recipe_id, recipe_error = self.recipe_id_for_rule(rule)
        if recipe_error:
            self.block_reason = recipe_error
            return
        module, category, recipe = self.find_recipe(module_id, recipe_id)
        if not module or not category or not recipe or not bool(recipe.get("enabled", False)):
            self.block_reason = "The mapped FCC recipe is unavailable: {0}/{1}.".format(module_id, recipe_id)
            return

        reported_material, material_error = self.material_from_match(rule)
        if material_error:
            self.block_reason = material_error
            return
        material, material_override = self.override_global_material(rule, reported_material)
        choice_group = str(rule.get("choice_group", ""))
        option = None
        if choice_group:
            option, option_error = self.material_option(module, choice_group, material, rule)
            if not option:
                self.block_reason = option_error
                return
        skill_error = self.skill_error(module, recipe)
        if skill_error:
            self.block_reason = skill_error
            return

        remaining_points = max(0, self.total - self.progress)
        points_key = self.points_setting_key(rule.get("id", ""), recipe_id)
        configured_points = self.number(rule.get("points_per_craft"), 0)
        learned_points = self.host.read_int(points_key, 0) if configured_points <= 0 else 0
        points_per_craft = configured_points if configured_points > 0 else learned_points
        calibrating = points_per_craft <= 0
        crafts_remaining = 1 if calibrating else (remaining_points + points_per_craft - 1) // points_per_craft
        batch = 1 if calibrating else min(self.batch_size, crafts_remaining)
        rows = self.resource_rows(recipe, option, choice_group)
        effective_material = str(option.get("name", material)) if option else str(rule.get("material_label", "Standard"))
        material_display = effective_material
        if material_override:
            material_display = "{0} (quest reports {1})".format(effective_material, reported_material)
        self.plan = {
            "source": "global",
            "focus": "global",
            "signature": "global|{0}|{1}".format(self.normalize(self.quest_title), self.total),
            "rule_id": str(rule.get("id", "")),
            "module_id": module_id,
            "module_name": str(module.get("name", module_id)),
            "category_id": str(category.get("id", "")),
            "recipe_id": recipe_id,
            "recipe_name": str(recipe.get("name", recipe_id)),
            "choice_group": choice_group,
            "choice_id": str(option.get("id", "")) if option else "",
            "reported_material": reported_material,
            "material": effective_material,
            "material_display": material_display,
            "material_override": material_override,
            "remaining_points": remaining_points,
            "points_per_craft": points_per_craft,
            "points_key": points_key,
            "points_source": "configured" if configured_points > 0 else ("learned" if learned_points > 0 else "calibration"),
            "calibrating": calibrating,
            "crafts_remaining": crafts_remaining,
            "batch": batch,
            "batch_points": batch * points_per_craft,
            "resources": rows,
            "per_craft": self.requirement_text(rows, 1),
            "batch_need": self.requirement_text(rows, batch),
            "remaining_need": "Unknown until one-craft calibration" if calibrating else self.requirement_text(rows, crafts_remaining),
        }
        self.block_reason = ""

    def refresh_quest(self, announce_result=True):
        if not self.open_global_quest():
            self.block_reason = "Global Quest gump 0x{0:08X} did not open.".format(self.gump_id)
            if announce_result:
                self.announce(self.block_reason, BAD_HUE, "Quest Refresh")
            return False
        self.line_source, lines = self.read_gump_lines()
        if not lines:
            self.block_reason = "Global Quest gump opened but exposed no readable text."
            if announce_result:
                self.announce(self.block_reason, BAD_HUE, "Quest Parse")
            return False
        self.parse_gump(lines)
        self.build_plan()
        if announce_result:
            if self.plan and self.plan.get("calibrating", False):
                self.announce(
                    "Global Quest parsed: {0}; one safe craft will measure its personal-contribution value.".format(self.quest_title),
                    WARN_HUE,
                    "Quest Calibration",
                )
            elif self.plan:
                self.announce(
                    "Global Quest parsed: {0}; {1} point(s) / {2} craft(s) remain.".format(
                        self.quest_title,
                        self.plan.get("remaining_points", 0),
                        self.plan.get("crafts_remaining", 0),
                    ),
                    GOOD_HUE,
                    "Quest Ready",
                )
            elif self.quest_active:
                self.announce(self.block_reason, WARN_HUE, "Quest Filter")
            else:
                self.announce(self.block_reason, WARN_HUE, "Quest Idle")
        self.host.mark_dirty()
        return True

    def diagnostics(self):
        Misc.SendMessage("Quest Crafter Global diagnostic: gump 0x{0:08X}, source={1}, lines={2}".format(self.gump_id, self.line_source, len(self.lines)), WARN_HUE)
        for index, line in enumerate(self.lines):
            Misc.SendMessage("Global text [{0}]: {1}".format(index, line), WARN_HUE)
        try:
            data = Gumps.GetGumpData(self.gump_id)
            definition = str(getattr(data, "gumpDefinition", "") or "")
            layout = str(getattr(data, "gumpLayout", "") or "")
            Misc.SendMessage("Quest GumpData: definition chars={0}, layout chars={1}".format(len(definition), len(layout)), WARN_HUE)
        except Exception as ex:
            Misc.SendMessage("Quest GumpData diagnostic failed: " + str(ex), BAD_HUE)
        Misc.SendMessage("Compendium Weekly diagnostic: gump 0x{0:08X}, opener={1}, source={2}, lines={3}, rows={4}, incomplete={5}".format(self.compendium_gump_id, self.compendium_open_method, self.compendium_line_source, len(self.compendium_lines), len(self.compendium_tasks), len(self.weekly_tasks)), WARN_HUE)
        for index, line in enumerate(self.compendium_lines):
            Misc.SendMessage("Compendium text [{0}]: {1}".format(index, line), WARN_HUE)
        for index, task in enumerate(self.compendium_tasks):
            mapping = "{0}/{1}".format(task.get("module", {}).get("id", "?"), task.get("recipe", {}).get("id", "?")) if task.get("module") and task.get("recipe") else "UNRESOLVED: " + str(task.get("parse_error", "unknown mapping"))
            Misc.SendMessage("Compendium task [{0}]: {1} | {2} | {3}/{4} | {5}".format(index, task.get("name", ""), task.get("material", ""), task.get("current", 0), task.get("total", 0), mapping), GOOD_HUE if task.get("recipe") else BAD_HUE)
        for index, plan in enumerate(self.weekly_plans):
            Misc.SendMessage("Weekly plan [{0}]: {1}/{2}, {3}, {4}/{5}".format(index, plan.get("module_id", ""), plan.get("recipe_id", ""), plan.get("material", ""), plan.get("progress", 0), plan.get("total", 0)), GOOD_HUE)
        for problem in self.weekly_unresolved:
            Misc.SendMessage("Weekly unresolved: " + str(problem), BAD_HUE)
        global_plan = self.global_display_plan()
        if global_plan:
            Misc.SendMessage("Global plan material: reported={0}, effective={1}".format(global_plan.get("reported_material", global_plan.get("material", "")), global_plan.get("material", "")), WARN_HUE if global_plan.get("material_override", "") else GOOD_HUE)
            if global_plan.get("material_override", ""):
                Misc.SendMessage("Global material override: " + str(global_plan.get("material_override", "")), WARN_HUE)
        if self.block_reason:
            Misc.SendMessage("Quest plan blocked: " + self.block_reason, WARN_HUE)

    def begin_batch(self):
        if not self.plan or self.block_reason:
            self.enter_watch(self.block_reason or "No eligible quest plan is available.", WARN_HUE)
            return
        amount = max(0, self.number(self.plan.get("batch"), 0))
        if amount <= 0:
            self.enter_watch("The selected crafting quest is complete; watching for the next task.", GOOD_HUE)
            return
        choices = {}
        if self.plan.get("choice_group") and self.plan.get("choice_id"):
            choices[str(self.plan.get("choice_group"))] = str(self.plan.get("choice_id"))
        started, message = self.host.begin_craft_job(
            self.plugin_id,
            self.plan.get("module_id"),
            self.plan.get("category_id"),
            self.plan.get("recipe_id"),
            amount,
            choices,
            self.plan.get("focus", "global"),
            None,
            bool(self.plan.get("ignore_skill_requirements", False)),
        )
        if not started:
            self.hold_current_quest("Quest held after FCC could not start it: " + str(message), BAD_HUE)
            return
        self.batch_target = amount
        self.batch_completed = 0
        self.before_progress = self.number(self.plan.get("progress"), self.progress)
        self.before_contribution = self.contribution
        self.active_source = str(self.plan.get("source", "global"))
        self.active_signature = str(self.plan.get("signature", ""))
        self.state = STATE_CRAFT
        self.running = True
        self.watch_message = ""
        action = "Calibrating with" if self.plan.get("calibrating", False) else "Crafting"
        self.announce(
            "{0} {1} x{2} in {3}; {4} focus will be verified before each craft.".format(
                action, self.plan.get("recipe_name", "recipe"), amount, self.plan.get("material", "material"), self.active_source.title()
            ),
            GOOD_HUE,
            "Quest Calibration" if self.plan.get("calibrating", False) else self.active_source.title() + " Craft",
        )

    def start(self, mode=WATCH_BOTH):
        if self.data_error:
            self.announce("Quest Crafter data error: " + self.data_error, BAD_HUE)
            return
        if self.host.craft_job_api_version() < 10:
            self.announce("Restart FrogCraftingCore.py to load its Weekly skill-trust bridge.", BAD_HUE)
            return
        self.watch_mode = self.normalized_watch_mode(mode)
        self.running = True
        self.state = STATE_WATCH
        self.batches_completed = 0
        self.zero_progress_refreshes = 0
        self.skipped_signature = ""
        self.skipped_reason = ""
        self.held_signatures = {}
        self.watch_message = ""
        self.schedule_watch(True)
        self.watch_step(True)

    def watch_step(self, immediate=False):
        if not immediate and time.time() < self.next_poll_at:
            return
        self.schedule_watch(False)
        if not self.refresh_all(False, self.watch_mode):
            source_text = "Global and Weekly quest sources" if self.watch_mode == WATCH_BOTH else self.watch_mode_label() + " quest source"
            self.watch_announce(source_text + " could not be read; watcher will retry.", WARN_HUE, "Quest Watch")
            return
        if not self.plan or self.block_reason:
            if self.held_signatures:
                reason = next(iter(self.held_signatures.values()))
                self.watch_announce(reason + " Other eligible quests will still be checked.", WARN_HUE, "Quest Held")
            else:
                details = []
                if self.source_enabled(WATCH_GLOBAL) and self.global_block_reason and self.global_block_reason != "No active Global Quest.":
                    details.append(self.global_block_reason)
                if self.source_enabled(WATCH_WEEKLY) and self.weekly_unresolved:
                    details.append(self.weekly_unresolved[0])
                message = " ".join(details) or "No eligible {0} crafting quest; watcher remains idle.".format(self.watch_mode_label().lower())
                self.watch_announce(message, WARN_HUE if details else GOOD_HUE, "Quest Watch")
            return
        if self.active_source == "global":
            self.quest_signature = self.normalize(self.quest_title)
        self.zero_progress_refreshes = 0
        self.begin_batch()

    def craft_step(self):
        status = self.host.craft_job_status(self.plugin_id)
        self.batch_completed = max(0, self.number(status.get("completed"), 0))
        self.host.mark_dirty()
        state = str(status.get("state", ""))
        if state == "running":
            return
        self.host.end_craft_job(self.plugin_id, False)
        if state != "complete":
            self.state = STATE_WATCH
            self.hold_current_quest("{0} quest held after craft failure: {1}".format(self.active_source.title(), str(status.get("message", "unknown FCC stop"))), BAD_HUE)
            return
        started, message = self.host.begin_craft_cleanup(self.plugin_id)
        if not started:
            self.state = STATE_WATCH
            self.hold_current_quest("{0} quest held because cleanup did not start: {1}".format(self.active_source.title(), str(message)), BAD_HUE)
            return
        self.batches_completed += 1
        self.state = STATE_CLEANUP
        self.announce("Batch complete; returning unused materials before refreshing the quest.", GOOD_HUE, "Quest Cleanup")

    def cleanup_step(self):
        if self.host.craft_cleanup_active(self.plugin_id):
            return
        self.state = STATE_REFRESH
        self.announce("Material cleanup complete; refreshing {0} progress.".format(self.active_source.title()), GOOD_HUE, "Quest Refresh")

    def select_after_weekly_refresh(self):
        self.plan = {}
        if self.source_enabled(WATCH_GLOBAL):
            global_ok = self.refresh_quest(False)
            self.last_global_plan = dict(self.plan) if global_ok and self.plan and not self.block_reason else {}
            self.global_block_reason = str(self.block_reason)
        if self.select_available_plan(self.watch_mode):
            if self.active_source == "global":
                self.quest_signature = self.normalize(self.quest_title)
            self.zero_progress_refreshes = 0
            self.begin_batch()
        else:
            self.enter_watch("Weekly progress updated; no other eligible crafting task is ready. Watching continues.", GOOD_HUE)

    def weekly_refresh_step(self, previous_plan):
        if not self.refresh_weeklies(False):
            self.enter_watch("Compendium Weekly refresh failed; watcher will retry.", BAD_HUE)
            return
        job_signature = str(previous_plan.get("job_signature", ""))
        current_task = None
        for task in self.weekly_tasks:
            if str(task.get("job_signature", "")) == job_signature:
                current_task = task
                break
        if current_task is None:
            self.zero_progress_refreshes = 0
            self.select_after_weekly_refresh()
            return
        current_progress = self.number(current_task.get("current"), 0)
        if current_progress <= self.before_progress:
            self.zero_progress_refreshes += 1
            if self.zero_progress_refreshes < 2:
                Misc.Pause(500)
                self.announce("Weekly progress has not refreshed yet; checking once more.", WARN_HUE, "Weekly Verify")
                return
            self.hold_current_quest("Weekly progress did not advance after a verified craft batch; holding this task before spending more materials.", BAD_HUE)
            return
        self.zero_progress_refreshes = 0
        self.select_after_weekly_refresh()

    def refresh_step(self):
        previous_plan = dict(self.plan)
        if str(previous_plan.get("source", "")) == "weekly":
            self.weekly_refresh_step(previous_plan)
            return
        was_calibrating = bool(previous_plan.get("calibrating", False))
        if not self.refresh_quest(False):
            self.enter_watch(self.block_reason + " Watching will retry.", BAD_HUE)
            return
        current_signature = self.normalize(self.quest_title)
        observed_points = self.contribution - self.before_contribution if was_calibrating else 0
        if was_calibrating and current_signature == self.quest_signature and observed_points > 0:
            points_key = str(previous_plan.get("points_key", ""))
            if points_key:
                self.host.write_int(points_key, observed_points)
            self.build_plan()
            self.zero_progress_refreshes = 0
            self.announce(
                "Learned and saved {0} quest point(s) per {1} from personal contribution.".format(
                    observed_points, previous_plan.get("recipe_name", "craft")
                ),
                GOOD_HUE,
                "Quest Calibration",
            )
        if not self.quest_active or self.progress >= self.total:
            self.skipped_signature = ""
            self.skipped_reason = ""
            self.enter_watch("Global Quest finished after {0} batch(es); watching for the next quest.".format(self.batches_completed), GOOD_HUE)
            return
        if current_signature != self.quest_signature:
            self.skipped_signature = ""
            self.skipped_reason = ""
            if self.plan and not self.block_reason:
                self.quest_signature = self.normalize(self.quest_title)
                self.zero_progress_refreshes = 0
                self.begin_batch()
            else:
                self.enter_watch((self.block_reason or "The new Global Quest is not eligible.") + " Watching remains active.", WARN_HUE)
            return
        if was_calibrating:
            if observed_points > 0:
                if self.plan and not self.block_reason:
                    self.begin_batch()
                else:
                    self.hold_current_quest(self.block_reason or "Calibrated quest could not build its next batch.", WARN_HUE)
                return
            self.zero_progress_refreshes += 1
            if self.zero_progress_refreshes < 2:
                Misc.Pause(500)
                self.announce("Personal contribution has not refreshed yet; checking once more.", WARN_HUE, "Quest Calibration")
                return
            self.hold_current_quest(
                "Calibration craft succeeded, but personal contribution did not expose a verified point increase; holding this quest.",
                BAD_HUE,
            )
            return
        if not self.plan or self.block_reason:
            self.hold_current_quest(self.block_reason or "The refreshed quest no longer has an eligible plan.", WARN_HUE)
            return
        if self.progress <= self.before_progress:
            self.zero_progress_refreshes += 1
            if self.zero_progress_refreshes < 2:
                Misc.Pause(500)
                self.announce("Quest progress has not refreshed yet; checking once more.", WARN_HUE, "Quest Verify")
                return
            self.hold_current_quest("Global Quest progress did not advance after a verified craft batch; holding it before spending more materials.", BAD_HUE)
            return
        self.zero_progress_refreshes = 0
        self.begin_batch()

    def step(self):
        if not self.running:
            return
        if self.state == STATE_WATCH:
            self.watch_step(False)
        elif self.state == STATE_CRAFT:
            self.craft_step()
        elif self.state == STATE_CLEANUP:
            self.cleanup_step()
        elif self.state == STATE_REFRESH:
            self.refresh_step()
        else:
            self.stop("Quest Crafter entered an unknown workflow state.", BAD_HUE)

    def global_display_plan(self):
        if self.plan.get("source") == "global":
            return self.plan
        return self.last_global_plan

    def weekly_display_plan(self):
        if self.plan.get("source") == "weekly":
            return self.plan
        for candidate in self.weekly_plans:
            signature = str(candidate.get("signature", ""))
            if not signature or signature not in self.held_signatures:
                return candidate
        return self.weekly_plans[0] if self.weekly_plans else {}

    def runtime_display_text(self):
        if self.state in (STATE_CRAFT, STATE_CLEANUP, STATE_REFRESH):
            return "{0} {1} {2}/{3}".format(self.state.upper(), self.active_source.upper(), self.batch_completed, self.batch_target)
        if self.running:
            return "WATCHING " + self.watch_mode_label().upper()
        return "IDLE"

    def render(self, gd, x, y, width, height):
        Gumps.AddBackground(gd, x, y, width, height, 3000)
        Gumps.AddAlphaRegion(gd, x, y, width, height)
        Gumps.AddLabel(gd, x + 12, y + 8, TITLE_HUE, "QUEST CRAFTER")
        Gumps.AddLabel(gd, x + 145, y + 8, GOOD_HUE if self.running else DIM_HUE, self.host.short_text(self.runtime_display_text(), 24))
        self.host.add_button(gd, x + 322, y + 6, self.button_id(BTN_REFRESH), "Refresh All", LABEL_HUE)
        self.host.add_button(gd, x + 432, y + 6, self.button_id(BTN_START), "Stop" if self.running else "Both", WARN_HUE if self.running else GOOD_HUE)
        self.host.add_button(gd, x + 514, y + 6, self.button_id(BTN_DIAGNOSTICS), "Journal", LABEL_HUE)

        global_plan = self.global_display_plan()
        Gumps.AddBackground(gd, x + 8, y + 28, width - 16, 132, 3000)
        Gumps.AddAlphaRegion(gd, x + 8, y + 28, width - 16, 132)
        Gumps.AddLabel(gd, x + 18, y + 34, TITLE_HUE, "GLOBAL QUEST")
        self.host.add_button(gd, x + 150, y + 33, self.button_id(BTN_OPEN), "Refresh GQ", LABEL_HUE)
        self.host.add_button(gd, x + 262, y + 33, self.button_id(BTN_START_GLOBAL), "Stop" if self.running else "Watch Global", WARN_HUE if self.running else GOOD_HUE)
        global_state = "ACTIVE" if self.quest_active else ("COMPLETE" if self.total > 0 and self.progress >= self.total else "NO ACTIVE QUEST")
        Gumps.AddLabel(gd, x + 408, y + 35, GOOD_HUE if self.quest_active else DIM_HUE, global_state)
        global_title = "{0} [{1}/{2}]".format(self.quest_title or "Refresh to read the current Global Quest", self.progress, self.total)
        Gumps.AddLabel(gd, x + 18, y + 57, LABEL_HUE, self.host.short_text(global_title, 82))
        if global_plan:
            global_plan_text = "Plan: {0} / {1} / {2}".format(global_plan.get("module_name", "Craft"), global_plan.get("recipe_name", "Recipe"), global_plan.get("material_display", global_plan.get("material", "Material")))
            global_batch_text = "Next: {0} craft(s), {1}".format(global_plan.get("batch", 0), global_plan.get("batch_need", ""))
            Gumps.AddLabel(gd, x + 18, y + 77, GOOD_HUE, self.host.short_text(global_plan_text, 82))
            Gumps.AddLabel(gd, x + 18, y + 96, LABEL_HUE, self.host.short_text(global_batch_text, 82))
        else:
            Gumps.AddLabel(gd, x + 18, y + 77, WARN_HUE if self.global_block_reason else DIM_HUE, self.host.short_text(self.global_block_reason or "No Global craft plan loaded.", 82))
        filters = [(str(rule.get("label", rule.get("id", "Rule"))), self.allowed(rule), self.button_id(BTN_RULE_BASE + index)) for index, rule in enumerate(self.rules[:6])]
        for index, filter_data in enumerate(filters):
            bx = x + 18 + (index % 3) * 205
            by = y + 116 + (index // 3) * 19
            label, enabled, button_id = filter_data
            self.host.add_button(gd, bx, by, button_id, "YES" if enabled else "NO", GOOD_HUE if enabled else BAD_HUE)
            Gumps.AddLabel(gd, bx + 64, by + 1, LABEL_HUE, self.host.short_text(label, 17))

        weekly_plan = self.weekly_display_plan()
        Gumps.AddBackground(gd, x + 8, y + 164, width - 16, 144, 3000)
        Gumps.AddAlphaRegion(gd, x + 8, y + 164, width - 16, 144)
        Gumps.AddLabel(gd, x + 18, y + 170, TITLE_HUE, "WEEKLY QUESTS")
        self.host.add_button(gd, x + 150, y + 169, self.button_id(BTN_OPEN_WEEKLY), "Refresh WQ", LABEL_HUE)
        self.host.add_button(gd, x + 262, y + 169, self.button_id(BTN_START_WEEKLY), "Stop" if self.running else "Do Weeklies", WARN_HUE if self.running else GOOD_HUE)
        weekly_enabled = self.weekly_allowed()
        self.host.add_button(gd, x + 408, y + 169, self.button_id(BTN_WEEKLY_TOGGLE), "YES" if weekly_enabled else "NO", GOOD_HUE if weekly_enabled else BAD_HUE)
        Gumps.AddLabel(gd, x + 470, y + 170, LABEL_HUE, "Weekly Crafts")
        weekly_summary = "{0} incomplete | {1} ready | {2} unresolved | completed {3}/{4}".format(len(self.weekly_tasks), len(self.weekly_plans), len(self.weekly_unresolved), self.weekly_completed, self.weekly_given)
        Gumps.AddLabel(gd, x + 18, y + 193, LABEL_HUE, weekly_summary)
        if weekly_plan:
            weekly_plan_text = "Plan: {0} / {1} / {2} [{3}/{4}]".format(weekly_plan.get("module_name", "Craft"), weekly_plan.get("recipe_name", "Recipe"), weekly_plan.get("material", "Material"), weekly_plan.get("progress", 0), weekly_plan.get("total", 0))
            weekly_batch_text = "Next: {0} craft(s), {1}".format(weekly_plan.get("batch", 0), weekly_plan.get("batch_need", ""))
            Gumps.AddLabel(gd, x + 18, y + 213, GOOD_HUE, self.host.short_text(weekly_plan_text, 82))
            Gumps.AddLabel(gd, x + 18, y + 232, LABEL_HUE, self.host.short_text(weekly_batch_text, 82))
            Gumps.AddLabel(gd, x + 18, y + 251, DIM_HUE, "Remaining: " + self.host.short_text(weekly_plan.get("remaining_need", ""), 70))
        else:
            weekly_reason = self.weekly_unresolved[0] if self.weekly_unresolved else "No incomplete Weekly craft plan loaded."
            Gumps.AddLabel(gd, x + 18, y + 213, WARN_HUE if self.weekly_unresolved else DIM_HUE, self.host.short_text(weekly_reason, 82))
        unresolved_text = "Unresolved: " + self.weekly_unresolved[0] if self.weekly_unresolved else "All parsed Weekly rows are mapped."
        Gumps.AddLabel(gd, x + 18, y + 270, BAD_HUE if self.weekly_unresolved else GOOD_HUE, self.host.short_text(unresolved_text, 82))
        parser_text = "Sources: Global {0} | Weekly {1}/{2}".format(self.line_source, self.compendium_line_source, self.compendium_open_method)
        Gumps.AddLabel(gd, x + 18, y + 289, DIM_HUE, self.host.short_text(parser_text, 82))

    def handle_button(self, local_button):
        if local_button in (BTN_START, BTN_START_GLOBAL, BTN_START_WEEKLY) and self.running:
            self.stop("Quest Crafter {0} watcher stopped by player.".format(self.watch_mode_label().lower()))
            return
        if self.running:
            self.announce("Stop Quest Crafter before changing filters or refreshing.", WARN_HUE)
            return
        if local_button == BTN_REFRESH:
            self.refresh_all(True, WATCH_BOTH)
        elif local_button == BTN_OPEN:
            self.plan = {}
            global_ok = self.refresh_quest(True)
            self.last_global_plan = dict(self.plan) if global_ok and self.plan and not self.block_reason else {}
            self.global_block_reason = str(self.block_reason)
        elif local_button == BTN_OPEN_WEEKLY:
            self.refresh_weeklies(True)
        elif local_button == BTN_START:
            self.start(WATCH_BOTH)
        elif local_button == BTN_START_GLOBAL:
            self.start(WATCH_GLOBAL)
        elif local_button == BTN_START_WEEKLY:
            self.start(WATCH_WEEKLY)
        elif local_button == BTN_DIAGNOSTICS:
            if not self.lines or not self.compendium_lines:
                self.refresh_all(False, WATCH_BOTH)
            self.diagnostics()
            self.announce("Global and Compendium Weekly diagnostics written to the journal.", WARN_HUE, "Quest Diagnostics")
        elif local_button == BTN_WEEKLY_TOGGLE:
            self.toggle_weekly()
        elif BTN_RULE_BASE <= local_button < BTN_RULE_BASE + len(self.rules):
            self.toggle_rule(self.rules[local_button - BTN_RULE_BASE])

    def snapshot(self):
        global_plan = self.global_display_plan()
        weekly_plan = self.weekly_display_plan()
        return (
            self.running,
            self.state,
            self.watch_mode,
            self.quest_active,
            self.quest_title,
            self.description,
            self.time_left,
            self.progress,
            self.total,
            self.contribution,
            self.line_source,
            self.compendium_line_source,
            self.compendium_open_method,
            len(self.weekly_tasks),
            len(self.weekly_plans),
            len(self.weekly_unresolved),
            self.block_reason,
            self.active_source,
            self.plan.get("rule_id", ""),
            self.plan.get("recipe_id", ""),
            self.plan.get("material", ""),
            self.plan.get("reported_material", ""),
            self.plan.get("material_override", ""),
            self.plan.get("batch", 0),
            global_plan.get("recipe_id", ""),
            global_plan.get("material", ""),
            global_plan.get("reported_material", ""),
            global_plan.get("material_override", ""),
            global_plan.get("batch", 0),
            weekly_plan.get("recipe_id", ""),
            weekly_plan.get("material", ""),
            weekly_plan.get("batch", 0),
            self.batch_completed,
            self.batch_target,
            self.batches_completed,
            self.message,
            tuple([self.allowed(rule) for rule in self.rules]),
            self.weekly_allowed(),
            tuple(sorted(self.held_signatures.keys())),
        )


def create_plugin(host):
    return FrogQuestCrafterPlugin(host)
