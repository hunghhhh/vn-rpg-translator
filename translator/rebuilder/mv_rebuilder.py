"""
RPG Maker MV/MZ Rebuilder - writes translated strings back into .json game files.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from rich.console import Console

console = Console()

DATA_FILES_CONFIG = {
    "Actors.json":       [("name", False), ("nickname", False), ("profile", True)],
    "Classes.json":      [("name", False)],
    "Skills.json":       [("name", False), ("description", True), ("message1", True), ("message2", True)],
    "Items.json":        [("name", False), ("description", True)],
    "Weapons.json":      [("name", False), ("description", True)],
    "Armors.json":       [("name", False), ("description", True)],
    "Enemies.json":      [("name", False)],
    "States.json":       [("name", False), ("message1", True), ("message2", True), ("message3", True), ("message4", True)],
    "CommonEvents.json": None,
    "System.json":       None,
}


class MVRebuilder:
    def __init__(self, game_dir: str):
        self.game_dir = Path(game_dir)
        self.data_dir = self._find_data_dir()

    def _find_data_dir(self) -> Path:
        for c in [self.game_dir / "www" / "data", self.game_dir / "data", self.game_dir / "Data"]:
            if c.exists() and any(c.glob("*.json")):
                return c
        raise FileNotFoundError(f"Could not find data dir under: {self.game_dir}")

    def backup(self) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.game_dir / f"data_backup_{ts}"
        shutil.copytree(self.data_dir, backup_dir)
        return str(backup_dir)

    def rebuild(self, translated: dict) -> int:
        count = 0

        for filename, fields in DATA_FILES_CONFIG.items():
            filepath = self.data_dir / filename
            if not filepath.exists():
                continue

            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            changed = False
            if filename == "CommonEvents.json":
                c, data = self._rebuild_events(data, "CE", translated)
                count += c; changed = c > 0
            elif filename == "System.json":
                c, data = self._rebuild_system(data, translated)
                count += c; changed = c > 0
            elif fields:
                c, data = self._rebuild_database(data, filename, fields, translated)
                count += c; changed = c > 0

            if changed:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

        for map_file in sorted(self.data_dir.glob("Map[0-9]*.json")):
            map_id = map_file.stem
            with open(map_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            c, data = self._rebuild_map(data, map_id, translated)
            count += c
            if c > 0:
                with open(map_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

        return count

    def _rebuild_database(self, data, filename, fields, translated):
        count = 0
        if not isinstance(data, list):
            return count, data
        for item in data:
            if not isinstance(item, dict):
                continue
            item_id = item.get("id", 0)
            prefix = f"{filename[:-5]}_{item_id}"
            for field, _ in fields:
                key = f"{prefix}.{field}"
                if key in translated:
                    item[field] = translated[key]
                    count += 1
        return count, data

    def _rebuild_events(self, data, prefix, translated):
        count = 0
        if not isinstance(data, list):
            return count, data
        for event in data:
            if not isinstance(event, dict):
                continue
            eid = event.get("id", 0)
            for i, cmd in enumerate(event.get("list", [])):
                if not isinstance(cmd, dict):
                    continue
                code   = cmd.get("code")
                params = cmd.get("parameters", [])
                if code == 401:
                    key = f"{prefix}_{eid}.cmd_{i}"
                    if key in translated and params:
                        params[0] = translated[key]
                        count += 1
                elif code == 102:
                    choices = params[0] if params else []
                    for j in range(len(choices)):
                        key = f"{prefix}_{eid}.choice_{i}_{j}"
                        if key in translated:
                            choices[j] = translated[key]
                            count += 1
        return count, data

    def _rebuild_map(self, data, map_id, translated):
        count = 0
        events = data.get("events", {})
        events_iter = list(enumerate(events)) if isinstance(events, list) else list(events.items())

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
                    if code == 401:
                        key = f"{map_id}.ev{ev_id}.pg{pg_i}.cmd{cmd_i}"
                        if key in translated and params:
                            params[0] = translated[key]
                            count += 1
                    elif code == 102:
                        choices = params[0] if params else []
                        for j in range(len(choices)):
                            key = f"{map_id}.ev{ev_id}.pg{pg_i}.choice{cmd_i}_{j}"
                            if key in translated:
                                choices[j] = translated[key]
                                count += 1
        return count, data

    def _rebuild_system(self, data, translated):
        count = 0
        if "System.gameTitle" in translated:
            data["gameTitle"] = translated["System.gameTitle"]; count += 1
        if "System.currencyUnit" in translated:
            data["currencyUnit"] = translated["System.currencyUnit"]; count += 1
        terms = data.get("terms", data.get("words", {}))
        if isinstance(terms, dict):
            for section, val in list(terms.items()):
                if isinstance(val, str):
                    key = f"System.terms.{section}"
                    if key in translated:
                        terms[section] = translated[key]; count += 1
                elif isinstance(val, list):
                    for i in range(len(val)):
                        key = f"System.terms.{section}_{i}"
                        if key in translated:
                            val[i] = translated[key]; count += 1
        return count, data
