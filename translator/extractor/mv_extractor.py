"""
RPG Maker MV/MZ Extractor - reads .json files from the game data directory.
Handles: Map*.json, Actors, Items, Skills, Weapons, Armors, Enemies, Classes,
         CommonEvents, System, States, Troops.
"""

import json
import re
from pathlib import Path
from rich.console import Console

console = Console()

# Database files and their translatable fields: (field_name, is_multiline)
DATA_FILES_CONFIG = {
    "Actors.json":       [("name", False), ("nickname", False), ("profile", True)],
    "Classes.json":      [("name", False)],
    "Skills.json":       [("name", False), ("description", True), ("message1", True), ("message2", True)],
    "Items.json":        [("name", False), ("description", True)],
    "Weapons.json":      [("name", False), ("description", True)],
    "Armors.json":       [("name", False), ("description", True)],
    "Enemies.json":      [("name", False)],
    "States.json":       [("name", False), ("message1", True), ("message2", True), ("message3", True), ("message4", True)],
    "CommonEvents.json": None,  # handled separately
    "System.json":       None,  # handled separately
}


class MVExtractor:
    def __init__(self, game_dir: str, output_dir: str):
        self.game_dir = Path(game_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir = self._find_data_dir()

    def _find_data_dir(self) -> Path:
        candidates = [
            self.game_dir / "www" / "data",
            self.game_dir / "data",
            self.game_dir / "Data",
        ]
        for c in candidates:
            if c.exists() and any(c.glob("*.json")):
                console.print(f"Data dir: {c}")
                return c
        raise FileNotFoundError(
            f"Could not find a JSON data directory under: {self.game_dir}\n"
            "Make sure this is the root folder of an RPG Maker MV/MZ game."
        )

    def extract(self) -> int:
        """Extract all translatable strings. Returns count of strings found."""
        extracted = {}

        for filename, fields in DATA_FILES_CONFIG.items():
            filepath = self.data_dir / filename
            if not filepath.exists():
                continue

            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            if filename == "CommonEvents.json":
                self._extract_events(data, "CE", extracted)
            elif filename == "System.json":
                self._extract_system(data, extracted)
            elif fields:
                self._extract_database(data, filename, fields, extracted)

        for map_file in sorted(self.data_dir.glob("Map[0-9]*.json")):
            map_id = map_file.stem
            with open(map_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._extract_map(data, map_id, extracted)

        # Keep only strings containing Japanese characters
        extracted = {k: v for k, v in extracted.items() if v and self._has_japanese(v)}

        out_file = self.output_dir / "extracted.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(extracted, f, ensure_ascii=False, indent=2)

        glossary_file = self.output_dir / "glossary.json"
        if not glossary_file.exists():
            with open(glossary_file, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)

        self._save_index()
        return len(extracted)

    def _extract_database(self, data: list, filename: str, fields: list, out: dict):
        if not isinstance(data, list):
            return
        for item in data:
            if not isinstance(item, dict):
                continue
            item_id = item.get("id", 0)
            prefix = f"{filename[:-5]}_{item_id}"
            for field, _ in fields:
                val = item.get(field, "")
                if val:
                    out[f"{prefix}.{field}"] = val

    def _extract_events(self, data: list, prefix: str, out: dict):
        if not isinstance(data, list):
            return
        for event in data:
            if not isinstance(event, dict):
                continue
            eid = event.get("id", 0)
            for i, cmd in enumerate(event.get("list", [])):
                if not isinstance(cmd, dict):
                    continue
                code   = cmd.get("code")
                params = cmd.get("parameters", [])
                if code == 401 and params:
                    text = params[0]
                    if text:
                        out[f"{prefix}_{eid}.cmd_{i}"] = text
                elif code == 102 and params:
                    choices = params[0] if params else []
                    for j, choice in enumerate(choices):
                        if choice:
                            out[f"{prefix}_{eid}.choice_{i}_{j}"] = choice

    def _extract_map(self, data: dict, map_id: str, out: dict):
        events = data.get("events", {})
        if isinstance(events, list):
            events_iter = enumerate(events)
        elif isinstance(events, dict):
            events_iter = events.items()
        else:
            return

        for ev_key, event in events_iter:
            if not isinstance(event, dict):
                continue
            ev_id = event.get("id", ev_key)
            for pg_i, page in enumerate(event.get("pages", [])):
                if not isinstance(page, dict):
                    continue
                for cmd_i, cmd in enumerate(page.get("list", [])):
                    if not isinstance(cmd, dict):
                        continue
                    code   = cmd.get("code")
                    params = cmd.get("parameters", [])
                    if code == 401 and params:
                        text = params[0]
                        if text:
                            out[f"{map_id}.ev{ev_id}.pg{pg_i}.cmd{cmd_i}"] = text
                    elif code == 102 and params:
                        choices = params[0] if params else []
                        for j, choice in enumerate(choices):
                            if choice:
                                out[f"{map_id}.ev{ev_id}.pg{pg_i}.choice{cmd_i}_{j}"] = choice

    def _extract_system(self, data: dict, out: dict):
        if data.get("gameTitle"):
            out["System.gameTitle"] = data["gameTitle"]
        if data.get("currencyUnit"):
            out["System.currencyUnit"] = data["currencyUnit"]
        terms = data.get("terms", data.get("words", {}))
        if isinstance(terms, dict):
            for section, val in terms.items():
                if isinstance(val, str) and val:
                    out[f"System.terms.{section}"] = val
                elif isinstance(val, list):
                    for i, item in enumerate(val):
                        if isinstance(item, str) and item:
                            out[f"System.terms.{section}_{i}"] = item

    def _has_japanese(self, text: str) -> bool:
        return bool(re.search(r"[\u3040-\u30ff\u4e00-\u9fff\u3400-\u4dbf]", text))

    def _save_index(self):
        index = {
            "engine":   "mv",
            "game_dir": str(self.game_dir),
            "data_dir": str(self.data_dir),
        }
        with open(self.output_dir / "index.json", "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
