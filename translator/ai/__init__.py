"""AI clients package"""

from translator.config import ConfigManager
from translator.ai.base import BaseAIClient
from translator.ai.gemini_client import GeminiClient
from translator.ai.openrouter_client import OpenRouterClient


def get_ai_client(settings: dict) -> BaseAIClient:
    """Factory: trả về AI client phù hợp theo config."""
    provider = settings.get("api_provider", "gemini").lower()

    if provider == "gemini":
        key = settings.get("gemini_api_key", "")
        if not key:
            raise ValueError("Chưa có Gemini API Key. Chạy: python main.py config")
        return GeminiClient(api_key=key)

    elif provider == "openrouter":
        key = settings.get("openrouter_api_key", "")
        model = settings.get("openrouter_model", "deepseek/deepseek-chat")
        if not key:
            raise ValueError("Chưa có OpenRouter API Key. Chạy: python main.py config")
        return OpenRouterClient(api_key=key, model=model)

    else:
        raise ValueError(f"Provider không hỗ trợ: {provider}. Dùng 'gemini' hoặc 'openrouter'.")
