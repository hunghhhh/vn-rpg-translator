"""
Base AI client interface and shared prompt builder.
"""

from abc import ABC, abstractmethod


# Prompt Builder

PRONOUN_INSTRUCTIONS = {
    "neutral": (
        "Use neutral pronouns: 'toi/ta' for first person, 'ban/cau' for second person, "
        "'anh ay/co ay/ho' for third person. Keep it natural."
    ),
    "formal": (
        "Use formal pronouns: prefer 'anh/chi/ong/ba/ngai' based on character context. "
        "Maintain proper social hierarchy fitting a JRPG setting."
    ),
    "casual": (
        "Use casual/blunt pronouns: 'tao/may/no/bon tao' for young characters, "
        "villains, or adult content. Keep the raw, unfiltered tone."
    ),
}

SYSTEM_PROMPT_TEMPLATE = """You are a professional Japanese to Vietnamese game translator.
Your task: translate text strings from a Japanese RPG game into Vietnamese.

STRICT RULES:
1. Preserve ALL control codes exactly as-is: \\n, \\c[N], \\v[N], \\i[N], \\s[N], <br>, #{{}} and any special tags.
2. Do NOT translate names/locations that appear in the glossary below - use the provided Vietnamese equivalent.
3. {pronoun_instruction}
4. Keep translations concise - games have limited display space.
5. Preserve any leading/trailing whitespace in the original string.
6. For UI/system text (menus, item names, skill names): short and punchy.
7. For dialogue: preserve the character's emotion and personality.

{glossary_section}

INPUT / OUTPUT FORMAT:
- Input:  JSON object {{ "id_1": "Japanese text 1", "id_2": "Japanese text 2", ... }}
- Output: JSON object {{ "id_1": "Vietnamese text 1", "id_2": "Vietnamese text 2", ... }}
- Return ONLY the JSON object. No explanation. No markdown code fences.
"""


def build_system_prompt(glossary: dict, pronoun_mode: str) -> str:
    pronoun_inst = PRONOUN_INSTRUCTIONS.get(pronoun_mode, PRONOUN_INSTRUCTIONS["neutral"])

    if glossary:
        lines = ["GLOSSARY (use these exact translations, no exceptions):"]
        for jp, vi in glossary.items():
            lines.append(f"  {jp} -> {vi}")
        glossary_section = "\n".join(lines)
    else:
        glossary_section = ""

    return SYSTEM_PROMPT_TEMPLATE.format(
        pronoun_instruction=pronoun_inst,
        glossary_section=glossary_section,
    )


# Base Class 

class BaseAIClient(ABC):
    """Shared interface for all AI provider clients."""

    @abstractmethod
    def translate_batch(
        self,
        batch: dict,
        glossary: dict = None,
        pronoun_mode: str = "neutral",
    ) -> dict:
        """
        Translate a batch dict {id: japanese_text} -> {id: vietnamese_text}.
        Must return a dict with the same keys.
        """
        ...
