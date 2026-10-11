"""
Gemini AI client - uses google-generativeai SDK.
Default model: gemini-2.0-flash (fast and cheap for bulk translation).
"""

import json
import time
import re
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)
import google.generativeai as genai
from translator.ai.base import BaseAIClient, build_system_prompt


DEFAULT_MODEL = "gemini-2.0-flash"


class GeminiClient(BaseAIClient):
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(
            model_name=model,
            generation_config={
                "temperature": 0.2,
                "top_p": 0.8,
                "max_output_tokens": 8192,
            },
        )

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

        prompt = (
            f"{system_prompt}\n\n"
            f"Translate the following batch from Japanese to Vietnamese:\n\n"
            f"{user_content}"
        )

        for attempt in range(3):
            try:
                response = self.model.generate_content(prompt)
                text = response.text.strip()
                return self._parse_json_response(text, batch)
            except Exception as e:
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)

        return {}

    def _parse_json_response(self, text: str, original_batch: dict) -> dict:
        """Parse JSON from response, handle cases where model wraps in markdown."""
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

        # Fallback: return originals so no data is lost
        return dict(original_batch)
