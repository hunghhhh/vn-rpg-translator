"""
Glossary manager - manages the Japanese -> Vietnamese term dictionary.
"""

import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

console = Console()


class GlossaryManager:
    def __init__(self, glossary_path: str = "output/glossary.json"):
        self.path = Path(glossary_path)

    def load(self) -> dict:
        if not self.path.exists():
            return {}
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, data: dict):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add(self, japanese: str, vietnamese: str):
        data = self.load()
        data[japanese] = vietnamese
        self.save(data)

    def interactive_edit(self):
        """Interactive terminal UI to view and edit the glossary."""
        data = self.load()

        while True:
            console.rule("Glossary Manager")

            if data:
                table = Table(show_header=True, header_style="bold")
                table.add_column("#",                   style="dim", width=4)
                table.add_column("Japanese (source)",   style="yellow")
                table.add_column("Vietnamese (target)", style="green")
                for i, (k, v) in enumerate(data.items(), 1):
                    table.add_row(str(i), k, v)
                console.print(table)
            else:
                console.print("Glossary is empty.")

            console.print("\n[a] Add  [d] Delete  [q] Quit")
            choice = Prompt.ask("Choose", default="q").lower().strip()

            if choice == "q":
                break
            elif choice == "a":
                jp = Prompt.ask("Japanese (source)")
                vi = Prompt.ask("Vietnamese (target)")
                data[jp] = vi
                self.save(data)
                console.print(f"Added: {jp} -> {vi}")
            elif choice == "d":
                if not data:
                    continue
                idx_str = Prompt.ask("Entry number to delete")
                try:
                    idx = int(idx_str) - 1
                    key = list(data.keys())[idx]
                    if Confirm.ask(f"Delete '{key}'?"):
                        del data[key]
                        self.save(data)
                        console.print(f"Deleted: {key}")
                except (ValueError, IndexError):
                    console.print("[red]Invalid number.[/red]")

    def build_prompt_section(self, glossary: dict) -> str:
        """Build a glossary block for injection into the AI prompt."""
        if not glossary:
            return ""
        lines = ["GLOSSARY (do NOT translate these differently):"]
        for jp, vi in glossary.items():
            lines.append(f"  {jp} -> {vi}")
        return "\n".join(lines)
