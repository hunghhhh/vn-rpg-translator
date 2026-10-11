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
    "api_provider":       "",                       # "gemini", "openrouter", or "custom"
    "gemini_api_key":     "",
    "gemini_model":       "gemini-2.5-flash",
    "openrouter_api_key": "",
    "openrouter_model":   "deepseek/deepseek-chat",
    "custom_api_url":     "",                       # e.g. http://localhost:11434/v1/chat/completions for Ollama
    "custom_api_key":     "ollama",
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
            choices=["gemini", "openrouter", "custom"],
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
            model = Prompt.ask(
                "Gemini model",
                default=cfg.get("gemini_model", "gemini-2.5-flash"),
            )
            cfg["gemini_model"] = model
        elif provider == "openrouter":
            key = Prompt.ask(
                "OpenRouter API Key (press Enter to keep current)",
                default=cfg.get("openrouter_api_key", ""),
                password=True,
            )
            if key:
                cfg["openrouter_api_key"] = key
            console.print("\nPopular OpenRouter models:")
            console.print("  - anthropic/claude-3-opus")
            console.print("  - anthropic/claude-3.5-sonnet")
            console.print("  - meta-llama/llama-3.3-70b-instruct")
            console.print("  - deepseek/deepseek-chat")
            console.print("  - openai/gpt-4o")
            model = Prompt.ask(
                "Model ID",
                default=cfg.get("openrouter_model", "deepseek/deepseek-chat"),
            )
            cfg["openrouter_model"] = model
        else:
            console.print("\nCustom / Local OpenAI-compatible API (Ollama, LM Studio, etc.)")
            url = Prompt.ask(
                "API Endpoint URL",
                default=cfg.get("custom_api_url", "http://localhost:11434/v1/chat/completions"),
            )
            cfg["custom_api_url"] = url
            model = Prompt.ask(
                "Model name",
                default=cfg.get("openrouter_model", "llama3.3"),
            )
            cfg["openrouter_model"] = model
            key = Prompt.ask(
                "API Key (or press Enter for default)",
                default=cfg.get("custom_api_key", "ollama"),
            )
            cfg["custom_api_key"] = key

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
