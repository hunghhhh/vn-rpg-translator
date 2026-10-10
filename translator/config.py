"""
Config manager - reads/writes config.json and provides interactive setup.
"""

import json
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

console = Console()

DEFAULT_CONFIG = {
    "api_provider":       "",                       # "gemini" or "openrouter"
    "gemini_api_key":     "",
    "openrouter_api_key": "",
    "openrouter_model":   "deepseek/deepseek-chat",
    "batch_size":         20,
    "pronoun_mode":       "neutral",                # neutral | formal | casual
    "source_lang":        "ja",
    "target_lang":        "vi",
}

CONFIG_FILE = Path("config.json")


class ConfigManager:
    def __init__(self, config_path: str = None):
        self.path = Path(config_path) if config_path else CONFIG_FILE

    def load(self) -> dict:
        if not self.path.exists():
            return dict(DEFAULT_CONFIG)
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {**DEFAULT_CONFIG, **data}

    def save(self, cfg: dict):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        console.print(f"Config saved to: {self.path}")

    def interactive_setup(self):
        """Step-by-step interactive configuration wizard."""
        cfg = self.load()

        console.rule("VN RPG Translator -- Config")

        table = Table(title="Current Configuration", show_header=True)
        table.add_column("Key",   style="cyan")
        table.add_column("Value")
        for k, v in cfg.items():
            display_val = "***" if "key" in k and v else str(v)
            table.add_row(k, display_val)
        console.print(table)
        console.print()

        provider = Prompt.ask(
            "API provider",
            choices=["gemini", "openrouter"],
            default=cfg.get("api_provider") or "gemini",
        )
        cfg["api_provider"] = provider

        if provider == "gemini":
            key = Prompt.ask(
                "Gemini API Key (press Enter to keep current)",
                default=cfg.get("gemini_api_key", ""),
                password=True,
            )
            if key:
                cfg["gemini_api_key"] = key
        else:
            key = Prompt.ask(
                "OpenRouter API Key (press Enter to keep current)",
                default=cfg.get("openrouter_api_key", ""),
                password=True,
            )
            if key:
                cfg["openrouter_api_key"] = key
            model = Prompt.ask(
                "OpenRouter model",
                default=cfg.get("openrouter_model", "deepseek/deepseek-chat"),
            )
            cfg["openrouter_model"] = model

        batch = Prompt.ask(
            "Batch size - strings per API call (larger = cheaper but more fragile)",
            default=str(cfg.get("batch_size", 20)),
        )
        cfg["batch_size"] = int(batch)

        console.print("\nPronoun mode:")
        console.print("  neutral  -- toi/ban/co ay  (safest default)")
        console.print("  formal   -- anh/chi/ong/ba")
        console.print("  casual   -- tao/may/no     (slice of life, adult games)")
        pronoun = Prompt.ask(
            "Pronoun mode",
            choices=["neutral", "formal", "casual"],
            default=cfg.get("pronoun_mode", "neutral"),
        )
        cfg["pronoun_mode"] = pronoun

        self.save(cfg)
