# ====================================================
# === Frog BOD Book Filler (Razor Enhanced Script) ===
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

import re
import time

DATA_FILE = "bod_book_filler.json"
BTN_TARGET = 1
BTN_SCAN = 2
BTN_START = 3
BTN_FILTERS = 4
BTN_OPEN = 5
BTN_FILTER_BACK = 6
BTN_FILTER_PREV = 7
BTN_FILTER_NEXT = 8
BTN_FILTER_ROW_BASE = 100

HTML_TEXT_COLOR = "#F4E7C5"
HTML_ACTIVE_COLOR = "#80FF80"
HTML_DIM_COLOR = "#B8D8A8"

STATE_IDLE = "idle"
STATE_SCAN = "scan"
STATE_CRAFT = "craft"
STATE_STAGE = "stage"
STATE_RECYCLE = "recycle"
STATE_CLEANUP = "cleanup"


class FrogBODBookPlugin:
    plugin_id = "bod_book_filler"
    name = "BOD Book Filler"
    version = "1.0"
    home_label = "BOD Book"

    def __init__(self, host):
        self.host = host
        self.button_base = 0
        self.running = False
        self.state = STATE_IDLE
        self.page = "main"
        self.filter_page = 0
        self.filter_button_map = {}
        self.book_serial = host.read_int("bod_book_serial", 0)
        self.data = {}
        self.data_error = ""
        try:
            self.data = host.read_data(DATA_FILE)
            if self.data.get("format") != "frog-bod-book-filler-data" or int(self.data.get("version", 0)) != 1:
                raise Exception("unsupported BOD Book data format")
        except Exception as ex:
            self.data_error = str(ex)
        self.gump_id = self.number(self.data.get("gump_id"), 0)
        self.book_item_id = self.number(self.data.get("book_item_id"), 0)
        self.interaction_cooldown_ms = max(0, self.number(self.data.get("interaction_cooldown_ms"), 750))
        self.open_attempts = max(1, self.number(self.data.get("open_attempts"), 4))
        self.gump_wait_ms = max(500, self.number(self.data.get("gump_wait_ms"), 3000))
        self.gump_settle_ms = max(0, self.number(self.data.get("gump_settle_ms"), 250))
        self.last_book_action_at = 0.0
        self.categories = list(self.data.get("categories", []))
        self.scan_categories = []
        self.scan_index = 0
        self.scan_page = 0
        self.category_hops = 0
        self.scan_records = []
        self.scan_errors = []
        self.queue = []
        self.skipped = 0
        self.completed = 0
        self.points_earned = 0
        self.blocked_keys = set()
        self.active = {}
        self.before_progress = 0
        self.book_completion_confirmed = False
        self.last_completion_points = 0
        self.last_progress_finished = -1
        self.last_progress_total = -1
        self.before_outputs = {}
        self.before_bag_outputs = {}
        self.rejects = []
        self.recycle_queue = []
        self.recycle_attempts = 0
        self.staged_count = 0
        self.staged_amount = 0
        self.zero_progress = {}
        self.resume_after_scan = False
        self.cleanup_started = False
        self.message = "Target a BOD Book directly in the main backpack."

    def number(self, value, fallback=0):
        try:
            return int(str(value), 0)
        except:
            try:
                return int(value)
            except:
                return fallback

    def normalize(self, value):
        return " ".join(str(value or "").strip().lower().split())

    def button_id(self, local_id):
        return int(self.button_base) + int(local_id)

    def is_priority_button(self, local_button):
        return self.running and int(local_button) == BTN_START

    def announce(self, message, hue=LABEL_HUE, step="BOD Book"):
        self.message = str(message)
        self.host.set_status(self.message, hue, step)
        self.host.mark_dirty()

    def activate(self):
        if self.data_error:
            self.announce("BOD Book data error: " + self.data_error, BAD_HUE)
        else:
            self.announce(self.message, GOOD_HUE)

    def stop(self, message, hue=WARN_HUE):
        if self.state == STATE_CRAFT:
            self.host.end_craft_job(self.plugin_id, True)
        self.running = False
        self.state = STATE_IDLE
        self.resume_after_scan = False
        self.rejects = []
        self.recycle_queue = []
        self.announce(message, hue)

    def deactivate(self, message=None):
        if self.running:
            self.stop(message or "BOD Book work paused.")

    def shutdown(self):
        if self.running:
            self.host.end_craft_job(self.plugin_id, True)
        self.running = False
        self.state = STATE_IDLE

    def book_item(self):
        item = self.host.valid_item(self.book_serial)
        backpack = Player.Backpack
        if not item or not backpack:
            return None
        try:
            if int(item.ItemID) != self.book_item_id or int(item.Container) != int(backpack.Serial):
                return None
        except:
            return None
        return item

    def target_book(self):
        serial = self.number(Target.PromptTarget("Target a BOD Book directly in your main backpack."), 0)
        item = self.host.valid_item(serial)
        backpack = Player.Backpack
        if not item or not backpack:
            self.announce("No BOD Book was targeted.", BAD_HUE)
            return
        try:
            valid = int(item.ItemID) == self.book_item_id and int(item.Container) == int(backpack.Serial)
        except:
            valid = False
        if not valid:
            self.announce("BOD Book must be directly in the main backpack (item 0x2259).", BAD_HUE)
            return
        self.book_serial = serial
        self.host.write_int("bod_book_serial", serial)
        self.queue = []
        self.active = {}
        self.announce("BOD Book selected. Scan Book will read All Skills and apply the shared filters.", GOOD_HUE)

    def wait_for_book_action_cooldown(self):
        if self.last_book_action_at <= 0.0 or self.interaction_cooldown_ms <= 0:
            return
        ready_at = self.last_book_action_at + (float(self.interaction_cooldown_ms) / 1000.0)
        remaining_ms = int((ready_at - time.time()) * 1000.0)
        if remaining_ms > 0:
            Misc.Pause(remaining_ms)

    def book_gump_is_open(self):
        try:
            return bool(Gumps.HasGump(self.gump_id))
        except:
            try:
                return bool(Gumps.HasGump()) and self.number(Gumps.CurrentGump(), 0) == self.gump_id
            except:
                return False

    def open_book(self):
        for attempt in range(1, self.open_attempts + 1):
            item = self.book_item()
            if not item:
                return False
            try:
                self.wait_for_book_action_cooldown()
                Gumps.CloseGump(self.gump_id)
                Gumps.ResetGump()
                Items.UseItem(item)
                self.last_book_action_at = time.time()
                Gumps.WaitForGump(self.gump_id, self.gump_wait_ms)
                if self.book_gump_is_open():
                    if self.gump_settle_ms > 0:
                        Misc.Pause(self.gump_settle_ms)
                    return True
            except:
                pass
            if attempt < self.open_attempts:
                self.announce("BOD Book use was ignored; retrying open {0}/{1}.".format(attempt + 1, self.open_attempts), WARN_HUE, "Book Open")
        return False

    def send_book_action(self, button):
        try:
            self.wait_for_book_action_cooldown()
            Gumps.SendAction(self.gump_id, self.number(button, 0))
            self.last_book_action_at = time.time()
            Gumps.WaitForGump(self.gump_id, self.gump_wait_ms)
            if not self.book_gump_is_open():
                return False
            if self.gump_settle_ms > 0:
                Misc.Pause(self.gump_settle_ms)
            return True
        except:
            return False

    def lines(self):
        line_list = []
        gump_strings = []
        try:
            values = Gumps.GetLineList(self.gump_id, False)
            if values:
                line_list = [str(value).strip() for value in values if str(value).strip()]
        except:
            pass
        try:
            data = Gumps.GetGumpData(self.gump_id)
            gump_strings = [str(value).strip() for value in (getattr(data, "gumpStrings", None) or []) if str(value).strip()]
        except:
            pass
        return gump_strings if len(gump_strings) > len(line_list) else line_list

    def current_category(self, lines):
        normalized = [self.normalize(value) for value in lines]
        header_end = len(normalized)
        for index, value in enumerate(normalized):
            if value == "item to craft":
                header_end = index
                break
        for category in self.categories:
            label = self.normalize(category.get("label", ""))
            if label and label in normalized[:header_end]:
                return str(category.get("id", ""))
        return ""

    def page_numbers(self, lines):
        for line in lines:
            match = re.search(r"\bpage\s+(\d+)\s*/\s*(\d+)\b", self.normalize(line))
            if match:
                return int(match.group(1)), int(match.group(2))
        return 0, 0

    def report_parse_lines(self, lines):
        Misc.SendMessage("BOD Book parser diagnostic: {0} captured strings".format(len(lines)), WARN_HUE)
        for index, value in enumerate(lines):
            Misc.SendMessage("BOD Book text [{0}]: {1}".format(index, str(value)), WARN_HUE)

    def parsed_rows(self, lines):
        skill_ids = {}
        for category in self.categories:
            module_id = str(category.get("module_id", ""))
            label = self.normalize(category.get("label", ""))
            if module_id and label:
                skill_ids[label] = module_id
        for alias, module_id in self.data.get("skill_aliases", {}).items():
            skill_ids[self.normalize(alias)] = str(module_id)
        header_names = ("item to craft", "skill", "material", "quality", "amount", "time left")
        header_indices = []
        for index, value in enumerate(lines):
            if self.normalize(value) in header_names:
                header_indices.append(index)
        item_header_indices = [index for index in header_indices if self.normalize(lines[index]) == "item to craft"]
        table_start = item_header_indices[0] + 1 if item_header_indices else 0
        table_end = len(lines)
        for index in range(table_start, len(lines)):
            if re.match(r"^page\s+\d+\s*/\s*\d+$", self.normalize(lines[index])):
                table_end = index
                break

        blocks = []
        block_starts = []
        metadata_indices = set()
        index = table_start
        while index < table_end - 4:
            skill = skill_ids.get(self.normalize(lines[index]), "")
            quality = self.normalize(lines[index + 2])
            progress = re.match(r"^(\d+)\s*/\s*(\d+)$", self.normalize(lines[index + 3]))
            time_left = self.normalize(lines[index + 4])
            if not skill or quality not in ("normal", "except.", "exceptional") or not progress or not re.match(r"^\d+\s*[dhm]$", time_left):
                index += 1
                continue
            finished = int(progress.group(1))
            total = int(progress.group(2))
            if total <= 0 or finished > total:
                raise Exception("invalid book progress near " + str(lines[index]))
            blocks.append({
                "module_id": skill,
                "material_text": str(lines[index + 1]).strip(),
                "exceptional_required": quality != "normal",
                "finished": finished,
                "total": total,
                "time_left": str(lines[index + 4]).strip(),
            })
            block_starts.append(index)
            metadata_indices.update(range(index, index + 5))
            index += 5

        name_candidates = []
        for index in range(table_start, table_end):
            if index in metadata_indices or index in header_indices:
                continue
            name = str(lines[index]).strip()
            normalized = self.normalize(name)
            if not normalized or normalized in header_names:
                continue
            if re.match(r"^\d+\s*/\s*\d+$", normalized) or re.match(r"^\d+\s*[dhm]$", normalized):
                continue
            if normalized.startswith("page ") or re.match(r"^\(\d+\s+deeds?\)$", normalized):
                continue
            name_candidates.append((index, name))

        names = []
        if blocks:
            leading_names = []
            if item_header_indices and item_header_indices[0] >= len(blocks):
                for leading_index in range(len(blocks)):
                    leading_name = str(lines[leading_index]).strip()
                    leading_normalized = self.normalize(leading_name)
                    if not leading_normalized or leading_normalized in header_names:
                        leading_names = []
                        break
                    if re.match(r"^\d+\s*/\s*\d+$", leading_normalized) or re.match(r"^\d+\s*[dhm]$", leading_normalized):
                        leading_names = []
                        break
                    leading_names.append(leading_name)
            if len(leading_names) == len(blocks):
                names = leading_names

            metadata_is_contiguous = all(block_starts[index] == block_starts[0] + (index * 5) for index in range(len(block_starts)))
            before_first_block = [name for index, name in name_candidates if index < block_starts[0]]
            if not names and metadata_is_contiguous and len(before_first_block) >= len(blocks):
                names = before_first_block[-len(blocks):]
            elif not names:
                previous_end = table_start
                positional = []
                for start in block_starts:
                    gap = [name for index, name in name_candidates if previous_end <= index < start]
                    if gap:
                        positional.append(gap[-1])
                    previous_end = start + 5
                if len(positional) == len(blocks):
                    names = positional
                elif len(name_candidates) == len(blocks):
                    names = [name for _index, name in name_candidates]

        if len(names) != len(blocks):
            captured_names = [name for _index, name in name_candidates]
            preview = ", ".join(captured_names[:6]) if captured_names else "none"
            raise Exception("could not pair item names with order rows ({0} candidates: {1}; {2} rows)".format(len(captured_names), preview, len(blocks)))

        rows = []
        for row_index, block in enumerate(blocks):
            row = dict(block)
            row["name"] = names[row_index]
            rows.append(row)
        return rows

    def record_key(self, record):
        return (
            str(record.get("module_id", "")),
            self.normalize(record.get("name", "")),
            self.normalize(record.get("material_text", "")),
            bool(record.get("exceptional_required", False)),
            self.number(record.get("total"), 0),
        )

    def pending_records(self):
        return [record for record in self.queue if self.record_key(record) not in self.blocked_keys]

    def html_escape(self, value):
        return (str(value or "").replace("&", "&amp;")
                                 .replace("<", "&lt;")
                                 .replace(">", "&gt;")
                                 .replace('"', "&quot;"))

    def live_progress(self):
        finished = self.number(self.active.get("finished"), 0)
        total = self.number(self.active.get("total"), 0)
        if 0 <= self.last_progress_finished <= self.last_progress_total and self.last_progress_total > 0:
            finished = self.last_progress_finished
            total = self.last_progress_total
        if self.running and self.state == STATE_CRAFT:
            try:
                status = self.host.craft_job_status(self.plugin_id)
                journal_finished = self.number(status.get("bod_book_progress_finished"), -1)
                journal_total = self.number(status.get("bod_book_progress_total"), -1)
                if 0 <= journal_finished <= journal_total and journal_total > 0:
                    finished = journal_finished
                    total = journal_total
            except:
                pass
        return finished, total

    def craft_order_html(self):
        pending = self.pending_records()
        if not pending:
            return "<basefont color={0}>No queued BODs</basefont>".format(HTML_DIM_COLOR)

        active_key = self.record_key(self.active) if self.active else None
        live_finished, live_total = self.live_progress()
        lines = []
        for index, record in enumerate(pending):
            key = self.record_key(record)
            is_current = active_key is not None and key == active_key
            finished = live_finished if is_current and live_total > 0 else self.number(record.get("finished"), 0)
            total = live_total if is_current and live_total > 0 else self.number(record.get("total"), 0)
            marker = "NOW" if is_current else str(index + 1)
            quality = "Exceptional" if record.get("exceptional_required") else "Normal"
            text = "{0}: {1} [{2}/{3}] | {4} | {5} | {6}".format(marker, record.get("name", "?"), finished, total, record.get("module_id", "?"), record.get("material", "?"), quality)
            color = HTML_ACTIVE_COLOR if is_current else HTML_TEXT_COLOR
            lines.append("<basefont color={0}>{1}</basefont>".format(color, self.html_escape(text)))
        return "<br>".join(lines)

    def bod_engine(self):
        return self.host.plugin("bod_filler")

    def mapped_name(self, module_id, book_name):
        normalized = self.normalize(book_name)
        for alias in self.data.get("recipe_aliases", []):
            if str(alias.get("module_id", "")) == str(module_id) and self.normalize(alias.get("book_name", "")) == normalized:
                recipe_id = str(alias.get("recipe_id", ""))
                if recipe_id:
                    return recipe_id
        return ""

    def component_skill_check(self, engine, module, recipe, seen=None):
        visited = set(seen or [])
        recipe_id = str(recipe.get("id", ""))
        if recipe_id in visited:
            return False, "component recipe dependency cycle at " + recipe_id, ""
        visited.add(recipe_id)

        warnings = []
        for resource in recipe.get("resources", []):
            component_id = str(resource.get("craft_recipe_id", "")).strip()
            if not component_id:
                continue
            component_recipe = None
            for category in module.get("categories", []):
                for candidate in category.get("recipes", []):
                    if str(candidate.get("id", "")) == component_id:
                        component_recipe = candidate
                        break
                if component_recipe:
                    break
            if not component_recipe:
                return False, "component recipe is not mapped in FCC: " + component_id, ""

            minimum_ok, minimum_detail, skill_warning = engine.minimum_skill_check(module, component_recipe)
            if not minimum_ok:
                return False, "component {0}: {1}".format(component_recipe.get("name", component_id), minimum_detail), ""
            if skill_warning:
                warnings.append("{0}: {1}".format(component_recipe.get("name", component_id), skill_warning))

            nested_ok, nested_detail, nested_warning = self.component_skill_check(engine, module, component_recipe, visited)
            if not nested_ok:
                return False, nested_detail, ""
            if nested_warning:
                warnings.append(nested_warning)
        return True, "", "; ".join(warnings)

    def map_record(self, record):
        engine = self.bod_engine()
        if not engine or engine.data_error:
            record["block_reason"] = "BOD Filler filter/recipe engine is unavailable"
            return
        module_id = str(record.get("module_id", ""))
        alias_recipe_id = self.mapped_name(module_id, record.get("name", ""))
        try:
            module, category, recipe = engine.find_recipe_match(module_id, [record.get("name", "")], 0)
        except Exception as ex:
            if not alias_recipe_id:
                record["block_reason"] = "recipe: " + str(ex)
                return
            module = self.host.module(module_id)
            category = None
            recipe = None
            for candidate_category in (module or {}).get("categories", []):
                for candidate_recipe in candidate_category.get("recipes", []):
                    if str(candidate_recipe.get("id", "")) == alias_recipe_id:
                        category = candidate_category
                        recipe = candidate_recipe
                        break
            if not recipe:
                record["block_reason"] = "recipe alias is not in FCC: " + alias_recipe_id
                return
        if alias_recipe_id and str(recipe.get("id", "")) != alias_recipe_id:
            record["block_reason"] = "recipe alias conflicts with the matched FCC recipe"
            return
        material_text = self.normalize(record.get("material_text", ""))
        material_lines = [] if material_text in ("", "---", "—", "-") else [record.get("material_text", "")]
        material, choices, material_error = engine.material_for_order(module, recipe, material_lines)
        if material_lines and not material_error:
            selected_labels = []
            for group in module.get("resource_choice_groups", []):
                selected_id = choices.get(str(group.get("id", "")), "")
                for option in group.get("options", []):
                    if str(option.get("id", "")) == selected_id:
                        selected_labels.append(self.normalize(option.get("name", "")))
                        selected_labels.append(self.normalize(str(selected_id).replace("_", " ")))
            if material_text not in selected_labels:
                material_error = "book material is not mapped to an exact FCC resource choice: " + str(record.get("material_text", ""))
        minimum_ok, minimum_detail, skill_warning = engine.minimum_skill_check(module, recipe)
        component_ok, component_detail, component_warning = self.component_skill_check(engine, module, recipe)
        combined_warnings = [value for value in (skill_warning, component_warning) if value]
        record["category_id"] = str(category.get("id", ""))
        record["recipe_id"] = str(recipe.get("id", ""))
        record["recipe_name"] = str(recipe.get("name", ""))
        record["material"] = str(material)
        record["material_choices"] = dict(choices)
        record["skill_warning"] = "; ".join(combined_warnings)
        record["stackable"] = bool(engine.stackable_for_recipe(module_id, recipe.get("id", "")))
        record["output_ids"] = list(engine.recipe_output_ids(recipe))
        record["output_names"] = list(engine.recipe_output_names(recipe))
        requested_output_name = self.normalize(record.get("name", ""))
        if requested_output_name and requested_output_name not in record["output_names"]:
            record["output_names"].append(requested_output_name)
        if not minimum_ok:
            record["block_reason"] = "skill: " + minimum_detail
        elif not component_ok:
            record["block_reason"] = "skill: " + component_detail
        elif material_error:
            record["block_reason"] = material_error
        elif record["finished"] >= record["total"]:
            record["block_reason"] = "already complete"
        else:
            record["block_reason"] = engine.bulk_filter_reason(record)
        if not record["block_reason"] and not record["output_ids"] and not record["output_names"]:
            record["block_reason"] = "FCC recipe has no output identity for safe reject handling"

    def chosen_categories(self):
        return ["all"]

    def begin_scan(self, resume=False):
        if self.data_error or not self.book_item():
            self.announce("Place and target the BOD Book directly in the main backpack.", BAD_HUE)
            return
        self.scan_categories = self.chosen_categories()
        self.scan_index = 0
        self.scan_page = 0
        self.category_hops = 0
        self.scan_records = []
        self.scan_errors = []
        if not resume:
            self.completed = 0
            self.points_earned = 0
            self.active = {}
        self.resume_after_scan = bool(resume)
        self.running = True
        self.state = STATE_SCAN
        self.announce("Scanning BOD Book pages; this may take a while.", GOOD_HUE, "Book Scan")

    def scan_step(self):
        if self.scan_page == 0 and not self.open_book():
            self.stop("BOD Book did not open after {0} paced attempts; verify it remains in the main backpack.".format(self.open_attempts), BAD_HUE)
            return
        lines = self.lines()
        current = self.current_category(lines)
        if not current:
            self.stop("Could not identify the book category from its gump text.", BAD_HUE)
            return
        wanted = self.scan_categories[self.scan_index]
        if current != wanted:
            self.category_hops += 1
            if self.category_hops >= len(self.categories):
                self.stop("Could not reach the selected book category after a full cycle.", BAD_HUE)
                return
            if not self.send_book_action(self.data.get("category_button", 3)):
                self.stop("Could not change the BOD Book category after a paced gump action.", BAD_HUE)
                return
            self.scan_page = -1
            return
        self.category_hops = 0
        page, pages = self.page_numbers(lines)
        if page <= 0 or pages <= 0 or page > pages:
            self.stop("Could not read the BOD Book page counter.", BAD_HUE)
            return
        if self.scan_page > 0 and page != self.scan_page:
            self.stop("Book page changed unexpectedly during scan.", BAD_HUE)
            return
        if self.scan_page <= 0 and page != 1:
            self.stop("Book did not return to page 1 after opening/changing category.", BAD_HUE)
            return
        try:
            rows = self.parsed_rows(lines)
        except Exception as ex:
            self.report_parse_lines(lines)
            self.stop("Book text parsing stopped: " + str(ex), BAD_HUE)
            return

        table_lines = lines
        for index, value in enumerate(lines):
            if self.normalize(value) == "item to craft":
                table_lines = lines[index + 1:]
                break
        progress_lines = [line for line in table_lines if re.match(r"^\d+\s*/\s*\d+$", self.normalize(line))]
        if len(rows) != len(progress_lines):
            self.report_parse_lines(lines)
            self.stop("Book rows lack readable item names; please send the full RE inspector text.", BAD_HUE)
            return
        for row in rows:
            key = self.record_key(row)
            duplicate = None
            for existing in self.scan_records:
                if self.record_key(existing) == key:
                    duplicate = existing
                    break
            if duplicate:
                duplicate["block_reason"] = "duplicate indistinguishable book rows require manual review"
            else:
                self.map_record(row)
                self.scan_records.append(row)
        if page < pages:
            if not self.send_book_action(self.data.get("next_page_button", 2)):
                self.stop("Could not turn the BOD Book page after a paced gump action.", BAD_HUE)
                return
            self.scan_page = page + 1
            self.announce("Scanned page {0}/{1} in {2}.".format(page, pages, wanted), GOOD_HUE, "Book Scan")
            return
        self.scan_index += 1
        self.scan_page = 0
        self.category_hops = 0
        if self.scan_index >= len(self.scan_categories):
            self.finish_scan()
        else:
            self.announce("Scanned {0}; moving to the next category.".format(wanted), GOOD_HUE, "Book Scan")

    def finish_scan(self):
        self.queue = [row for row in self.scan_records if not row.get("block_reason")]
        self.queue.sort(key=lambda row: (row.get("module_id", ""), str(sorted(row.get("material_choices", {}).items())), row.get("recipe_id", "")))
        self.skipped = len(self.scan_records) - len(self.queue)
        for row in self.scan_records:
            if row.get("block_reason"):
                Misc.SendMessage("BOD Book skip - {0} ({1}): {2}".format(row.get("name", "?"), row.get("module_id", "?"), row["block_reason"]), WARN_HUE)
        self.state = STATE_IDLE
        self.running = False
        if self.resume_after_scan:
            self.resume_after_scan = False
            self.after_rescan()
        else:
            skipped_rows = [row for row in self.scan_records if row.get("block_reason")]
            if skipped_rows:
                first = skipped_rows[0]
                self.announce("Book scan: {0} eligible, {1} skipped. First skip: {2} - {3}.".format(len(self.queue), self.skipped, first.get("name", "?"), first.get("block_reason", "unknown reason")), WARN_HUE, "Book Scan")
            else:
                self.announce("Book scan: {0} eligible, 0 skipped. Start when ready.".format(len(self.queue)), GOOD_HUE, "Book Scan")

    def output_matches(self, item, record):
        try:
            if int(item.ItemID) in record.get("output_ids", []):
                return True
            return self.normalize(getattr(item, "Name", "")) in record.get("output_names", [])
        except:
            return False

    def direct_items(self, serial):
        container = self.host.valid_item(serial)
        if not container:
            return []
        try:
            Items.WaitForContents(container, 1500)
        except:
            pass
        try:
            return list(container.Contains or [])
        except:
            return []

    def output_snapshot(self, record, serial):
        result = {}
        for item in self.direct_items(serial):
            if self.output_matches(item, record):
                try:
                    result[int(item.Serial)] = int(item.Amount)
                except:
                    pass
        return result

    def start_next(self):
        if not self.book_item():
            self.stop("The BOD Book is no longer directly in the main backpack.", BAD_HUE)
            return
        if self.host.craft_job_api_version() < 11:
            self.stop("Restart FrogCraftingCore.py to load host API 11 journal-progress support.", BAD_HUE)
            return
        if not self.host.craft_bag_serial():
            self.stop("Set and enable a Craft Bag for rejected-output cleanup; book crafting itself will use the root backpack.", BAD_HUE)
            return
        candidates = [row for row in self.queue if self.record_key(row) not in self.blocked_keys]
        if not candidates:
            unresolved_blocked = max(0, len(self.blocked_keys) - self.completed)
            self.stop("BOD Book run finished: {0} completed; {1} points earned; {2} skipped/blocked.".format(self.completed, self.points_earned, self.skipped + unresolved_blocked), GOOD_HUE)
            return
        self.active = dict(candidates[0])
        self.before_progress = self.number(self.active.get("finished"), 0)
        self.book_completion_confirmed = False
        self.last_completion_points = 0
        self.last_progress_finished = -1
        self.last_progress_total = -1
        self.before_outputs = self.output_snapshot(self.active, Player.Backpack.Serial)
        remaining = self.active["total"] - self.before_progress
        amount = min(remaining, max(1, self.number(self.data.get("max_crafts_per_pass"), 10)))
        started, message = self.host.begin_craft_job(self.plugin_id, self.active["module_id"], self.active["category_id"], self.active["recipe_id"], amount, self.active["material_choices"], "bod_book", "backpack")
        if not started:
            self.stop("Book craft could not start: " + str(message), BAD_HUE)
            return
        self.running = True
        self.state = STATE_CRAFT
        warning = self.active.get("skill_warning", "")
        prefix = "Skill warning: " + warning + "; " if warning else ""
        self.announce(prefix + "Crafting {0} x{1} in root backpack for BOD Book.".format(self.active["name"], amount), WARN_HUE if warning else GOOD_HUE, "Book Craft")

    def craft_step(self):
        status = self.host.craft_job_status(self.plugin_id)
        if status.get("state") == "running":
            return
        self.book_completion_confirmed = bool(status.get("bod_book_complete", False))
        self.last_completion_points = self.number(status.get("bod_book_points"), 0)
        self.last_progress_finished = self.number(status.get("bod_book_progress_finished"), -1)
        self.last_progress_total = self.number(status.get("bod_book_progress_total"), -1)
        self.host.end_craft_job(self.plugin_id, False)
        if status.get("state") != "complete":
            self.stop("BOD Book crafting stopped: " + str(status.get("message", "unknown error")), BAD_HUE)
            return
        bag_serial = self.host.craft_bag_serial()
        self.before_bag_outputs = self.output_snapshot(self.active, bag_serial) if bag_serial else {}
        self.rejects = []
        for item in self.direct_items(Player.Backpack.Serial):
            if not self.output_matches(item, self.active):
                continue
            try:
                serial = int(item.Serial)
                delta = int(item.Amount) - self.before_outputs.get(serial, 0)
                if delta > 0:
                    self.rejects.append((serial, delta))
            except:
                pass
        self.state = STATE_STAGE
        self.staged_count = 0
        self.staged_amount = 0
        self.recycle_attempts = 0
        self.announce("Craft pass ended; staging {0} rejected output stack(s).".format(len(self.rejects)), GOOD_HUE, "Book Rejects")

    def stage_step(self):
        if not self.rejects:
            self.state = STATE_RECYCLE
            self.recycle_queue = []
            for item in self.direct_items(self.host.craft_bag_serial()):
                if self.output_matches(item, self.active):
                    self.recycle_queue.append(int(item.Serial))
            if self.recycle_queue:
                self.announce("Treating {0} matching Craft Bag stack(s) as rejected output.".format(len(self.recycle_queue)), WARN_HUE, "Book Rejects")
            return
        bag_serial = self.host.craft_bag_serial()
        if not bag_serial:
            self.stop("Craft Bag unavailable while staging rejected book output; items remain in root backpack.", BAD_HUE)
            return
        serial, amount = self.rejects.pop(0)
        item = self.host.valid_item(serial)
        if not item:
            self.stop("Rejected output changed before it could be isolated; check the root backpack.", BAD_HUE)
            return

        try:
            if int(item.Container) != int(Player.Backpack.Serial) or int(item.Amount) < amount or not self.output_matches(item, self.active):
                raise Exception("rejected output identity/location changed")
            Items.Move(serial, bag_serial, amount)
            Misc.Pause(700)
            bag_after = self.output_snapshot(self.active, bag_serial)
            gained_in_bag = sum(max(0, count - self.before_bag_outputs.get(key, 0)) for key, count in bag_after.items())
            if gained_in_bag < self.staged_amount + amount:
                raise Exception("the Craft Bag did not receive the exact rejected output")
            remaining = self.host.valid_item(serial)
            if remaining and int(remaining.Container) == int(Player.Backpack.Serial) and int(remaining.Amount) >= self.before_outputs.get(serial, 0) + amount:
                raise Exception("move did not consume the new output")
        except Exception as ex:
            self.stop("Could not safely stage rejected output: " + str(ex), BAD_HUE)
            return
        self.staged_count += 1
        self.staged_amount += amount
        self.announce("Staged rejected output {0}; {1} stack(s) remain.".format(self.staged_count, len(self.rejects)), GOOD_HUE, "Book Rejects")

    def recycle_step(self):
        if not self.recycle_queue:
            self.state = STATE_CLEANUP
            self.cleanup_started = False
            self.recycle_attempts = 0
            return
        serial = self.recycle_queue[0]
        item = self.host.valid_item(serial)
        if not item:
            self.recycle_queue.pop(0)
            self.recycle_attempts = 0
            return
        if not self.output_matches(item, self.active):
            self.stop("Rejected Craft Bag output changed identity; cleanup stopped.", BAD_HUE)
            return
        if self.active.get("stackable"):
            state, message = self.host.trash_craft_bag_item(self.plugin_id, serial, int(item.ItemID))
        else:
            max_attempts = max(1, self.number(self.data.get("recycle_attempts"), 3))
            if self.recycle_attempts >= max_attempts:
                state, message = self.host.trash_craft_bag_item(self.plugin_id, serial, int(item.ItemID))
            else:
                before = list(self.recycle_queue)
                state, message, remaining = self.host.recycle_craft_bag_contents(self.plugin_id, self.active["module_id"], self.active["recipe_id"], before, 0)
                if state in ("complete", "leftovers"):
                    remaining = [self.number(value, 0) for value in remaining]
                    if len(remaining) != len(set(remaining)) or any(value not in before for value in remaining):
                        self.stop("Safety stop: bag-wide recycle returned an unexpected rejected-item list.", BAD_HUE)
                        return
                    self.recycle_queue = remaining
                    if not remaining:
                        self.recycle_attempts = 0
                        self.announce(str(message), GOOD_HUE, "Book Rejects")
                        return
                    self.recycle_attempts += 1
                    self.announce("{0} Attempt {1}/{2}; {3} rejected item(s) remain.".format(message, self.recycle_attempts, max_attempts, len(remaining)), WARN_HUE, "Book Rejects")
                    return
                if state == "retry":
                    self.recycle_attempts += 1
                    self.announce("Recycle attempt {0}/{1} did not clear the rejects: {2}".format(self.recycle_attempts, max_attempts, message), WARN_HUE, "Book Rejects")
                    return
        if state == "complete":
            self.recycle_queue.pop(0)
            if not self.recycle_queue:
                self.recycle_attempts = 0
        elif state in ("progress", "retry"):
            pass
        else:
            self.stop("Reject cleanup stopped: " + str(message) + " Items remain in the Craft Bag.", BAD_HUE)
            return
        self.announce(str(message), GOOD_HUE if state == "complete" else WARN_HUE, "Book Rejects")

    def cleanup_step(self):
        if not self.cleanup_started:
            started, message = self.host.begin_craft_cleanup(self.plugin_id, "backpack")
            if not started:
                self.stop("Material cleanup could not start: " + str(message), BAD_HUE)
                return
            self.cleanup_started = True
            self.announce("Returning unused crafting materials to configured shelves/chest.", GOOD_HUE, "Book Cleanup")
            return
        if self.host.craft_cleanup_active(self.plugin_id):
            return
        self.finish_craft_pass()

    def update_journal_progress(self, key, finished, total):
        for records in (self.queue, self.scan_records):
            for record in records:
                if self.record_key(record) == key:
                    record["finished"] = finished
                    record["total"] = total
        self.active["finished"] = finished
        self.active["total"] = total

    def finish_craft_pass(self):
        key = self.record_key(self.active)
        if self.book_completion_confirmed:
            self.completed += 1
            self.points_earned += self.last_completion_points
            self.blocked_keys.add(key)
            self.zero_progress.pop(key, None)
            Misc.SendMessage("BOD Book complete - {0}; +{1} artificer points. Continuing queue without a category rescan.".format(self.active.get("name", "order"), self.last_completion_points), GOOD_HUE)
            self.start_next()
            return

        finished = self.last_progress_finished
        total = self.last_progress_total
        expected_total = self.number(self.active.get("total"), 0)
        if total == expected_total and self.before_progress < finished <= total:
            self.update_journal_progress(key, finished, total)
            self.zero_progress[key] = 0
            if finished >= total:
                self.completed += 1
                self.blocked_keys.add(key)
                Misc.SendMessage("BOD Book complete - {0}; journal progress reached {1}/{2}. Continuing queue.".format(self.active.get("name", "order"), finished, total), GOOD_HUE)
            else:
                self.announce("BOD progress confirmed at {0}/{1}; continuing without a category rescan.".format(finished, total), GOOD_HUE, "Book Verify")
            self.start_next()
            return

        Misc.SendMessage("BOD Book journal progress was unavailable or inconsistent; performing one safety rescan.", WARN_HUE)
        self.begin_scan(True)

    def after_rescan(self):
        key = self.record_key(self.active)
        if self.book_completion_confirmed:
            self.completed += 1
            self.points_earned += self.last_completion_points
            self.blocked_keys.add(key)
            Misc.SendMessage("BOD Book complete - {0}; +{1} artificer points. Continuing queue.".format(self.active.get("name", "order"), self.last_completion_points), GOOD_HUE)
            self.start_next()
            return
        updated = None
        for row in self.scan_records:
            if self.record_key(row) == key:
                updated = row
                break
        if not updated:
            self.completed += 1
            self.blocked_keys.add(key)
            self.zero_progress.pop(key, None)
            Misc.SendMessage("BOD Book complete - {0}; completed row disappeared during verification. Continuing queue.".format(self.active.get("name", "order")), GOOD_HUE)
            self.start_next()
            return
        gained = updated["finished"] - self.before_progress
        if gained < 0:
            self.stop("Book progress decreased unexpectedly; verify the active order.", BAD_HUE)
            return
        if updated["finished"] >= updated["total"]:
            self.completed += 1
            self.blocked_keys.add(key)
        elif gained == 0:
            self.zero_progress[key] = self.zero_progress.get(key, 0) + 1
            if self.zero_progress[key] >= max(1, self.number(self.data.get("max_zero_progress_passes"), 2)):
                self.blocked_keys.add(key)
                self.announce("No book progress for {0}; skipping it after bounded attempts.".format(updated["name"]), WARN_HUE, "Book Verify")
        else:
            self.zero_progress[key] = 0
        self.start_next()

    def step(self):
        if not self.running:
            return
        if self.state == STATE_SCAN:
            self.scan_step()
        elif self.state == STATE_CRAFT:
            self.craft_step()
        elif self.state == STATE_STAGE:
            self.stage_step()
        elif self.state == STATE_RECYCLE:
            self.recycle_step()
        elif self.state == STATE_CLEANUP:
            self.cleanup_step()
        else:
            self.stop("BOD Book entered an unknown workflow state.", BAD_HUE)

    def render(self, gd, x, y, width, height):
        if self.page == "filters":
            self.render_filters(gd, x, y, width, height)
            return
        Gumps.AddBackground(gd, x, y, width, height, 3000)
        Gumps.AddAlphaRegion(gd, x, y, width, height)
        Gumps.AddLabel(gd, x + 12, y + 8, TITLE_HUE, "BOD BOOK FILLER")
        Gumps.AddLabel(gd, x + 190, y + 8, DIM_HUE, "Root backpack crafting / shared BOD filters")
        Gumps.AddLabel(gd, x + 20, y + 39, LABEL_HUE, "Book:")
        Gumps.AddLabel(gd, x + 80, y + 39, GOOD_HUE if self.book_item() else BAD_HUE, self.host.item_label(self.book_serial) if self.book_item() else "Not set or not in root backpack")
        self.host.add_button(gd, x + 20, y + 66, self.button_id(BTN_TARGET), "Target Book", LABEL_HUE)
        self.host.add_button(gd, x + 166, y + 66, self.button_id(BTN_OPEN), "Open Book", LABEL_HUE)
        self.host.add_button(gd, x + 300, y + 66, self.button_id(BTN_SCAN), "Scan Book", LABEL_HUE)
        self.host.add_button(gd, x + 438, y + 66, self.button_id(BTN_START), "Stop" if self.running else "Start Fill", WARN_HUE if self.running else GOOD_HUE)
        self.host.add_button(gd, x + 555, y + 66, self.button_id(BTN_FILTERS), "Filters", LABEL_HUE)
        Gumps.AddLabel(gd, x + 20, y + 102, DIM_HUE, "All Skills are scanned; shared Filters control which BODs enter the queue.")
        Gumps.AddLabel(gd, x + 20, y + 128, TITLE_HUE, "WORK QUEUE")
        Gumps.AddLabel(gd, x + 20, y + 150, LABEL_HUE, "Eligible: {0}   Skipped: {1}   Completed: {2}   Points: {3}".format(len(self.queue), self.skipped, self.completed, self.points_earned))
        active_label = self.active.get("name", "No active order")
        live_finished, live_total = self.live_progress()
        current_progress = " | BOD {0}/{1}".format(live_finished, live_total) if self.active and live_total > 0 else ""
        Gumps.AddLabel(gd, x + 20, y + 173, LABEL_HUE, "Current: " + self.host.short_text(active_label, 38) + current_progress)
        if self.active:
            quality = "Exceptional" if self.active.get("exceptional_required") else "Normal"
            Gumps.AddLabel(gd, x + 20, y + 196, DIM_HUE, "{0}  |  {1}  |  {2}".format(self.active.get("module_id", ""), self.active.get("material", ""), quality))

        Gumps.AddLabel(gd, x + 20, y + 220, TITLE_HUE, "CRAFT ORDER")
        Gumps.AddLabel(gd, x + 132, y + 220, DIM_HUE, "Live queue - completed rows are removed")
        Gumps.AddAlphaRegion(gd, x + 16, y + 239, width - 32, 70)
        Gumps.AddHtml(gd, x + 20, y + 242, width - 40, 64, self.craft_order_html(), False, True)

    def render_filters(self, gd, x, y, width, height):
        Gumps.AddBackground(gd, x, y, width, height, 3000)
        Gumps.AddAlphaRegion(gd, x, y, width, height)
        Gumps.AddLabel(gd, x + 12, y + 8, TITLE_HUE, "BOD BOOK FILTERS")
        self.host.add_button(gd, x + width - 115, y + 9, self.button_id(BTN_FILTER_BACK), "Back", LABEL_HUE)
        Gumps.AddLabel(gd, x + 20, y + 33, DIM_HUE, "Shared with BOD Filler. Changes require a new book scan.")
        engine = self.bod_engine()
        if not engine:
            Gumps.AddLabel(gd, x + 20, y + 70, BAD_HUE, "BOD Filler filter engine is unavailable.")
            return
        entries = engine.bulk_filter_entries()
        page_size = 22
        page_count = max(1, (len(entries) + page_size - 1) // page_size)
        self.filter_page = min(self.filter_page, page_count - 1)
        self.filter_button_map = {}
        for offset, entry in enumerate(entries[self.filter_page * page_size:(self.filter_page + 1) * page_size]):
            column = offset // 11
            row = offset % 11
            bx = x + 20 + column * 315
            by = y + 61 + row * 19
            local_button = BTN_FILTER_ROW_BASE + offset
            self.filter_button_map[local_button] = entry
            enabled = engine.bulk_filter_enabled(entry.get("kind", ""), entry.get("key", ""))
            self.host.add_button(gd, bx, by, self.button_id(local_button), "YES" if enabled else "NO", GOOD_HUE if enabled else BAD_HUE)
            Gumps.AddLabel(gd, bx + 64, by + 1, LABEL_HUE, self.host.short_text(entry.get("label", ""), 27))
        self.host.add_button(gd, x + 20, y + 282, self.button_id(BTN_FILTER_PREV), "Previous", LABEL_HUE)
        Gumps.AddLabel(gd, x + 155, y + 283, DIM_HUE, "Page {0}/{1}".format(self.filter_page + 1, page_count))
        self.host.add_button(gd, x + 258, y + 282, self.button_id(BTN_FILTER_NEXT), "Next", LABEL_HUE)

    def handle_button(self, local_button):
        if local_button == BTN_START and self.running:
            self.stop("BOD Book run stopped by player.")
            return
        if self.running:
            self.announce("Stop the current book workflow before changing settings.", WARN_HUE)
            return
        if self.page == "filters":
            if local_button == BTN_FILTER_BACK:
                self.page = "main"
                self.host.mark_dirty()
            elif local_button in (BTN_FILTER_PREV, BTN_FILTER_NEXT):
                engine = self.bod_engine()
                count = len(engine.bulk_filter_entries()) if engine else 0
                pages = max(1, (count + 21) // 22)
                self.filter_page = (self.filter_page + (-1 if local_button == BTN_FILTER_PREV else 1)) % pages
                self.host.mark_dirty()
            elif local_button in self.filter_button_map:
                engine = self.bod_engine()
                if engine:
                    engine.toggle_bulk_filter(self.filter_button_map[local_button])
                    self.queue = []
                    self.active = {}
                    self.announce("Shared filter changed; scan the BOD Book again.", GOOD_HUE)
            return
        if local_button == BTN_TARGET:
            self.target_book()
        elif local_button == BTN_OPEN:
            self.announce("Opened BOD Book." if self.open_book() else "BOD Book did not open.", GOOD_HUE if self.book_item() else BAD_HUE)
        elif local_button == BTN_SCAN:
            self.begin_scan(False)
        elif local_button == BTN_FILTERS:
            self.page = "filters"
            self.filter_page = 0
            self.host.mark_dirty()
        elif local_button == BTN_START:
            if not self.queue:
                self.announce("Scan the BOD Book first; no eligible orders are queued.", WARN_HUE)
            else:
                self.completed = 0
                self.points_earned = 0
                self.blocked_keys = set()
                self.zero_progress = {}
                self.start_next()

    def snapshot(self):
        return (
            self.running, self.state, self.page, self.filter_page, self.book_serial,
            len(self.queue), self.skipped, self.completed, self.points_earned,
            self.scan_index, self.scan_page, len(self.scan_records),
            self.book_completion_confirmed, self.last_completion_points,
            self.last_progress_finished, self.last_progress_total,
            self.live_progress(),
            tuple((self.record_key(record), self.number(record.get("finished"), 0), self.number(record.get("total"), 0)) for record in self.pending_records()),
            self.active.get("name", ""), self.message,
        )


def create_plugin(host):
    return FrogBODBookPlugin(host)
