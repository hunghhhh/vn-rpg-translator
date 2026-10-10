"""
RPG Maker VX Ace Rebuilder - writes translated strings back into .rvdata2 files.
Requires marshalparser with write support; shows instructions otherwise.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from rich.console import Console

console = Console()


class VXARebuilder:
    def __init__(self, game_dir: str):
        self.game_dir = Path(game_dir)
        self.data_dir = self._find_data_dir()

    def _find_data_dir(self) -> Path:
        for c in [self.game_dir / "Data", self.game_dir / "data"]:
            if c.exists() and any(c.glob("*.rvdata2")):
                return c
        raise FileNotFoundError(f"Could not find Data dir under: {self.game_dir}")

    def backup(self) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.game_dir / f"Data_backup_{ts}"
        shutil.copytree(self.data_dir, backup_dir)
        return str(backup_dir)

    def rebuild(self, translated: dict) -> int:
        try:
            import marshalparser
            return self._rebuild_via_marshalparser(translated, marshalparser)
        except ImportError:
            self._show_manual_instructions(translated)
            return 0

    def _rebuild_via_marshalparser(self, translated: dict, marshalparser) -> int:
        count = 0

        # Group keys by source file stem
        file_groups: dict[str, dict] = {}
        for key in translated:
            stem = key.split("[")[0].split(".")[0]
            file_groups.setdefault(stem, {})[key] = translated[key]

        for stem, translations in file_groups.items():
            filepath = self.data_dir / f"{stem}.rvdata2"
            if not filepath.exists():
                continue
            try:
                with open(filepath, "rb") as f:
                    data = marshalparser.load(f)

                modified = self._apply_translations_to_object(data, stem, translations)
                count += modified

                if modified > 0:
                    with open(filepath, "wb") as f:
                        marshalparser.dump(data, f)
                    console.print(f"{stem}.rvdata2 -- {modified} strings written")
            except Exception as e:
                console.print(f"[yellow]{stem}.rvdata2: {e}[/yellow]")

        return count

    def _apply_translations_to_object(self, obj, current_key: str, translations: dict) -> int:
        count = 0

        if isinstance(obj, list):
            for i, item in enumerate(obj):
                child_key = f"{current_key}[{i}]"
                if isinstance(item, str) and child_key in translations:
                    obj[i] = translations[child_key]
                    count += 1
                else:
                    count += self._apply_translations_to_object(item, child_key, translations)

        elif isinstance(obj, dict):
            for k, v in obj.items():
                child_key = f"{current_key}.{k}"
                if isinstance(v, str) and child_key in translations:
                    obj[k] = translations[child_key]
                    count += 1
                else:
                    count += self._apply_translations_to_object(v, child_key, translations)

        return count

    def _show_manual_instructions(self, translated: dict):
        out_file = self.game_dir / "translated_strings.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(translated, f, ensure_ascii=False, indent=2)

        console.print(f"""
[yellow]VXA Rebuilder requires marshalparser with write support.[/yellow]

Option 1 - Install marshalparser:
  pip install marshalparser

Option 2 - Use an external tool (RGSS Decryptor, etc.):
  Translations saved to: {out_file}
""")
