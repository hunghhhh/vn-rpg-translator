"""
OpenRouter AI client - OpenAI-compatible REST API.
Supports any model on openrouter.ai (DeepSeek, Claude, GPT-4o, Mistral, etc.).
"""

import json
import time
import re
import requests
from translator.ai.base import BaseAIClient, build_system_prompt


OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "deepseek/deepseek-chat"


class OpenRouterClient(BaseAIClient):
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, api_url: str = OPENROUTER_API_URL):
        self.api_key = api_key
        self.model = model
        self.api_url = api_url or OPENROUTER_API_URL
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/hunghhhh/vn-rpg-translator",
            "X-Title": "VN RPG Translator",
        }

    def translate_batch(
        self,
        batch: dict,
        glossary: dict = None,
        pronoun_mode: str = "neutral",
    ) -> dict:
        if not batch:
            return {}

        system_prompt = build_system_prompt(glossary or {}, pronoun_mode)
        user_content = json.dumps(batch, ensure_ascii=False, indent=2)

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Translate the following batch from Japanese to Vietnamese:\n\n{user_content}",
                },
            ],
            "temperature": 0.2,
            "max_tokens": 8192,
        }

        for attempt in range(3):
            try:
                resp = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=120,
                )
                resp.raise_for_status()
                data = resp.json()
                text = data["choices"][0]["message"]["content"].strip()
                return self._parse_json_response(text, batch)
            except requests.exceptions.HTTPError:
                if resp.status_code == 429:
                    time.sleep(2 ** attempt * 5)
                elif attempt == 2:
                    raise
                else:
                    time.sleep(2 ** attempt)
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)

        return {}

    def _parse_json_response(self, text: str, original_batch: dict) -> dict:
        """Parse JSON from response, handle markdown wrapping."""
        text = re.sub(r"^```(?:json)?\n?", "", text, flags=re.MULTILINE)
        text = re.sub(r"\n?```$",          "", text, flags=re.MULTILINE)
        text = text.strip()

        try:
            result = json.loads(text)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass

        return dict(original_batch)
