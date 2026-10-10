"""
RPG Maker VX Ace Extractor - reads .rvdata2 files (Ruby Marshal binary format).
Uses marshalparser if available; falls back to binary string scanning.
"""

import os
import re
import json
from pathlib import Path
from rich.console import Console

console = Console()


class VXAExtractor:
    def __init__(self, game_dir: str, output_dir: str):
        self.game_dir = Path(game_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir = self._find_data_dir()

    def _find_data_dir(self) -> Path:
        for c in [self.game_dir / "Data", self.game_dir / "data"]:
            if c.exists() and any(c.glob("*.rvdata2")):
                console.print(f"Data dir (VXA): {c}")
                return c
        raise FileNotFoundError(
            f"Could not find a Data directory with .rvdata2 files under: {self.game_dir}"
        )

    def extract(self) -> int:
        try:
            return self._extract_via_marshalparser()
        except ImportError:
            console.print("[yellow]marshalparser not installed, falling back to binary scan...[/yellow]")
            return self._extract_via_binary_scan()

    def _extract_via_marshalparser(self) -> int:
        import marshalparser

        extracted = {}
        target_files = list(self.data_dir.glob("*.rvdata2"))
        console.print(f"Found {len(target_files)} .rvdata2 files")

        for filepath in target_files:
            stem = filepath.stem
            try:
                with open(filepath, "rb") as f:
                    data = marshalparser.load(f)
                self._walk_and_extract(data, stem, extracted)
            except Exception as e:
                console.print(f"[yellow]Skipping {filepath.name}: {e}[/yellow]")

        extracted = {k: v for k, v in extracted.items() if v and self._has_japanese(v)}
        self._save_results(extracted)
        return len(extracted)

    def _extract_via_binary_scan(self) -> int:
        """
        Fallback: scan binary to find UTF-8 strings containing Japanese.
        Ruby Marshal format: 0x22 (double-quote) followed by packed length then UTF-8 bytes.
        """
        extracted = {}
        for filepath in self.data_dir.glob("*.rvdata2"):
            stem = filepath.stem
            try:
                with open(filepath, "rb") as f:
                    data = f.read()
                strings = self._scan_marshal_strings(data)
                for i, s in enumerate(strings):
                    if self._has_japanese(s):
                        extracted[f"{stem}.str_{i}"] = s
            except Exception as e:
                console.print(f"[yellow]Skipping {filepath.name}: {e}[/yellow]")

        console.print(
            "[yellow]Warning: binary scan mode - position metadata is lost.[/yellow]\n"
            "Install marshalparser for full support: pip install marshalparser"
        )
        self._save_results(extracted)
        return len(extracted)

    def _scan_marshal_strings(self, data: bytes) -> list:
        results = []
        i = 0
        while i < len(data) - 2:
            if data[i] == 0x22:
                try:
                    length, consumed = self._read_marshal_int(data, i + 1)
                    if 2 <= length <= 2000:
                        start = i + 1 + consumed
                        end   = start + length
                        if end <= len(data):
                            raw = data[start:end]
                            try:
                                text = raw.decode("utf-8")
                                if text.isprintable() or "\n" in text:
                                    results.append(text)
                                    i = end
                                    continue
                            except UnicodeDecodeError:
                                pass
                except Exception:
                    pass
            i += 1
        return results

    def _read_marshal_int(self, data: bytes, pos: int):
        """Read a Ruby Marshal packed integer. Returns (value, bytes_consumed)."""
        b = data[pos]
        if b == 0:
            return 0, 1
        elif b > 4:
            return b - 5, 1
        elif b < 252:
            val = b - 256 if b > 127 else b
            if val > 4:
                return val - 5, 1
            elif val < -4:
                return val + 5, 1
        count = b if b <= 4 else 256 - b
        val = 0
        for k in range(1, count + 1):
            val |= data[pos + k] << (8 * (k - 1))
        if b > 128:
            val -= (1 << (8 * count))
        return val, 1 + count

    def _walk_and_extract(self, obj, prefix: str, out: dict, depth: int = 0):
        if depth > 20:
            return
        if isinstance(obj, str):
            if self._has_japanese(obj) and obj.strip():
                key = prefix
                counter = 0
                while key in out:
                    counter += 1
                    key = f"{prefix}_{counter}"
                out[key] = obj
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                self._walk_and_extract(item, f"{prefix}[{i}]", out, depth + 1)
        elif isinstance(obj, dict):
            for k, v in obj.items():
                self._walk_and_extract(v, f"{prefix}.{k}", out, depth + 1)
        elif hasattr(obj, "__dict__"):
            self._walk_and_extract(obj.__dict__, prefix, out, depth + 1)
        elif hasattr(obj, "instance_variables"):
            for var in obj.instance_variables:
                val = getattr(obj, var, None)
                self._walk_and_extract(val, f"{prefix}.{var}", out, depth + 1)

    def _has_japanese(self, text: str) -> bool:
        return bool(re.search(r"[\u3040-\u30ff\u4e00-\u9fff\u3400-\u4dbf]", text))

    def _save_results(self, extracted: dict):
        out_file = self.output_dir / "extracted.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(extracted, f, ensure_ascii=False, indent=2)

        glossary_file = self.output_dir / "glossary.json"
        if not glossary_file.exists():
            with open(glossary_file, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)

        with open(self.output_dir / "index.json", "w", encoding="utf-8") as f:
            json.dump(
                {"engine": "vxa", "game_dir": str(self.game_dir), "data_dir": str(self.data_dir)},
                f, ensure_ascii=False, indent=2,
            )
