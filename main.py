#!/usr/bin/env python3
"""
VN RPG Translator - CLI entry point
Translates RPG Maker games from Japanese to Vietnamese using AI.
"""

import sys
import click
from rich.console import Console

from translator.config import ConfigManager
from translator.extractor import get_extractor
from translator.rebuilder import get_rebuilder
from translator.glossary import GlossaryManager
from translator.preview import PreviewEditor
from translator.ai import get_ai_client

console = Console()

BANNER = """
VN RPG Translator  v0.1.0
Japanese -> Vietnamese | RPG Maker MV / MZ / VX Ace
"""


@click.group()
def cli():
    """Translate RPG Maker games from Japanese to Vietnamese using AI."""
    console.print(BANNER)


# CONFIG
@cli.command()
def config():
    """Configure API keys and translation options."""
    cfg = ConfigManager()
    cfg.interactive_setup()


# EXTRACT
@cli.command()
@click.option(
    "--engine",
    type=click.Choice(["mv", "mz", "vxa"], case_sensitive=False),
    required=True,
    help="Game engine: mv (RPG Maker MV), mz (RPG Maker MZ), vxa (VX Ace)",
)
@click.option(
    "--game-dir",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to the root game directory",
)
@click.option(
    "--output-dir",
    default="output",
    show_default=True,
    help="Directory to save extracted files",
)
def extract(engine, game_dir, output_dir):
    """Extract Japanese text from game files."""
    console.rule("STEP 1 -- EXTRACT")

    extractor = get_extractor(engine, game_dir, output_dir)
    with console.status("Reading game files..."):
        count = extractor.extract()

    console.print(f"\nDone. Found {count} strings to translate.")
    console.print(f"Saved to: {output_dir}/extracted.json")
    console.print("\nNext: edit the glossary, then run: python main.py translate")


# TRANSLATE
@cli.command()
@click.option("--input-file",    default="output/extracted.json",  show_default=True)
@click.option("--output-file",   default="output/translated.json", show_default=True)
@click.option("--glossary-file", default="output/glossary.json",   show_default=True)
@click.option("--preview",       is_flag=True, default=False,       help="Open interactive editor after translating")
@click.option("--batch-size",    default=None, type=int,            help="Strings per API call (overrides config)")
@click.option("--resume",        is_flag=True, default=False,       help="Skip already-translated strings")
@click.option("--limit",         default=None, type=int,            help="Limit number of strings to translate")
def translate(input_file, output_file, glossary_file, preview, batch_size, resume, limit):
    """Translate extracted Japanese strings to Vietnamese using AI."""
    console.rule("STEP 2 -- TRANSLATE")

    import json
    import os

    cfg = ConfigManager()
    settings = cfg.load()

    if not settings.get("api_provider"):
        console.print("[red]No API configured. Run: python main.py config[/red]")
        sys.exit(1)

    if not os.path.exists(input_file):
        console.print(f"[red]File not found: {input_file}[/red]")
        console.print("Run: python main.py extract")
        sys.exit(1)

    with open(input_file, "r", encoding="utf-8") as f:
        extracted = json.load(f)

    translated = {}
    if resume and os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            translated = json.load(f)
        console.print(f"Resume: {len(translated)} already translated, skipping...")

    glossary = GlossaryManager(glossary_file)
    glossary_data = glossary.load()
    if glossary_data:
        console.print(f"Glossary: {len(glossary_data)} terms loaded")

    ai_client = get_ai_client(settings)
    effective_batch = batch_size or settings.get("batch_size", 20)

    to_translate = {k: v for k, v in extracted.items() if k not in translated}
    if limit is not None and limit > 0:
        to_translate = dict(list(to_translate.items())[:limit])
    total = len(to_translate)
    console.print(f"To translate: {total} strings | Batch size: {effective_batch}")

    if total == 0:
        console.print("All strings already translated.")
        return

    items = list(to_translate.items())
    batches = [items[i: i + effective_batch] for i in range(0, len(items), effective_batch)]

    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        BarColumn(),
        TextColumn("{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total} batches)"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Translating...", total=len(batches))

        for i, batch in enumerate(batches):
            batch_dict = dict(batch)
            try:
                result = ai_client.translate_batch(
                    batch_dict,
                    glossary=glossary_data,
                    pronoun_mode=settings.get("pronoun_mode", "neutral"),
                )
                translated.update(result)
            except Exception as e:
                console.print(f"\n[yellow]Batch {i + 1} error: {e}[/yellow]")

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(translated, f, ensure_ascii=False, indent=2)

            progress.advance(task)

    console.print(f"\nDone. {len(translated)}/{len(extracted)} strings translated.")

    if preview:
        editor = PreviewEditor(extracted, translated)
        translated = editor.run()
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(translated, f, ensure_ascii=False, indent=2)
        console.print(f"Saved edits to: {output_file}")

    console.print("\nNext: python main.py rebuild --engine <mv|vxa> --game-dir <path>")


# REBUILD
@cli.command()
@click.option("--engine",          type=click.Choice(["mv", "mz", "vxa"], case_sensitive=False), required=True)
@click.option("--game-dir",        required=True, type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--translated-file", default="output/translated.json", show_default=True)
@click.option("--no-backup",       is_flag=True, default=False, help="Skip backup (not recommended)")
def rebuild(engine, game_dir, translated_file, no_backup):
    """Write translated strings back into game files."""
    console.rule("STEP 3 -- REBUILD")

    import json
    import os

    if not os.path.exists(translated_file):
        console.print(f"[red]File not found: {translated_file}[/red]")
        sys.exit(1)

    with open(translated_file, "r", encoding="utf-8") as f:
        translated = json.load(f)

    rebuilder = get_rebuilder(engine, game_dir)

    if not no_backup:
        with console.status("Backing up original files..."):
            backup_path = rebuilder.backup()
        console.print(f"Backup saved: {backup_path}")

    with console.status("Writing translations into game..."):
        count = rebuilder.rebuild(translated)

    console.print(f"\nDone. Wrote {count} strings into game files.")
    console.print("Launch the game and check.")


# GLOSSARY
@cli.command()
@click.option("--file", "glossary_file", default="output/glossary.json", show_default=True)
def glossary(glossary_file):
    """Manage the term glossary (view / add / delete)."""
    gm = GlossaryManager(glossary_file)
    gm.interactive_edit()


if __name__ == "__main__":
    cli()
