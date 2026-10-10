"""
Preview & Edit - interactive terminal UI to review and edit translations
before writing them back into the game.
"""

import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

console = Console()


class PreviewEditor:
    def __init__(self, original: dict, translated: dict):
        self.original = original
        self.translated = dict(translated)
        self.page_size = 20

    def run(self) -> dict:
        """Run the preview UI. Returns the (possibly edited) translated dict."""
        console.rule("Translation Preview")

        keys = list(self.original.keys())
        total = len(keys)
        page = 0
        total_pages = (total + self.page_size - 1) // self.page_size

        while True:
            start = page * self.page_size
            end = min(start + self.page_size, total)
            page_keys = keys[start:end]

            table = Table(
                show_header=True,
                header_style="bold",
                show_lines=True,
                width=console.width,
            )
            table.add_column("#",                      style="dim",    width=4)
            table.add_column("ID",                     style="dim",    max_width=20)
            table.add_column("Japanese (source)",      style="yellow", max_width=40)
            table.add_column("Vietnamese (translated)", style="green",  max_width=50)

            for i, key in enumerate(page_keys, start=start + 1):
                orig  = self.original.get(key, "")
                trans = self.translated.get(key, "-- not translated --")
                orig_d  = (orig[:60]  + "...") if len(orig)  > 60 else orig
                trans_d = (trans[:70] + "...") if len(trans) > 70 else trans
                table.add_row(str(i), key[:18], orig_d, trans_d)

            console.print(table)
            console.print(
                f"Page {page + 1}/{total_pages} | "
                "[n] Next  [p] Prev  [e] Edit entry  [s] Save & quit  [q] Quit without saving"
            )

            choice = Prompt.ask("Choose", default="n").lower().strip()

            if choice == "n":
                if page < total_pages - 1:
                    page += 1
            elif choice == "p":
                if page > 0:
                    page -= 1
            elif choice == "e":
                self._edit_entry(keys)
            elif choice == "s":
                console.print(f"Saved {len(self.translated)} translations.")
                return self.translated
            elif choice == "q":
                if Confirm.ask("Quit without saving edits?"):
                    return self.translated

        return self.translated

    def _edit_entry(self, keys: list):
        idx_str = Prompt.ask("Entry number to edit")
        try:
            idx = int(idx_str) - 1
            key = keys[idx]
        except (ValueError, IndexError):
            console.print("[red]Invalid number.[/red]")
            return

        console.print(Panel(
            f"Japanese (source):\n{self.original.get(key, '')}\n\n"
            f"Current translation:\n{self.translated.get(key, '')}",
            title=f"Entry #{idx + 1} -- {key}",
            border_style="cyan",
        ))

        new_val = Prompt.ask("New translation (Enter to keep current)", default=self.translated.get(key, ""))
        if new_val != self.translated.get(key, ""):
            self.translated[key] = new_val
            console.print(f"Updated entry #{idx + 1}")
