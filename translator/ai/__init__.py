"""AI clients package"""

from translator.config import ConfigManager
from translator.ai.base import BaseAIClient
from translator.ai.gemini_client import GeminiClient
from translator.ai.openrouter_client import OpenRouterClient


def get_ai_client(settings: dict) -> BaseAIClient:
    """Factory: returns matching AI client for settings."""
    provider = settings.get("api_provider", "gemini").lower()

    if provider == "gemini":
        key = settings.get("gemini_api_key", "")
        model = settings.get("gemini_model", "gemini-2.5-flash")
        if not key:
            raise ValueError("No Gemini API key found. Run: python main.py config")
        return GeminiClient(api_key=key, model=model)

    elif provider in ("openrouter", "local", "custom"):
        key = settings.get("openrouter_api_key", "") or settings.get("custom_api_key", "dummy-key")
        model = settings.get("openrouter_model", "deepseek/deepseek-chat")
        api_url = settings.get("custom_api_url", "")
        if provider == "openrouter" and not key:
            raise ValueError("No OpenRouter API key found. Run: python main.py config")
        return OpenRouterClient(api_key=key, model=model, api_url=api_url)

    else:
        raise ValueError(f"Unsupported provider: {provider}. Use 'gemini', 'openrouter', or 'custom'.")
