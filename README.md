# VN RPG Translator

A CLI tool to translate RPG Maker games from Japanese to Vietnamese using AI,
optimized for Vietnamese pronouns and cultural context.

Supports: RPG Maker VX Ace (.rvdata2) and RPG Maker MV/MZ (.json)

---

## Features

- Auto Extract — reads game files and pulls all Japanese text
- AI Translation — via Gemini or OpenRouter (GPT-4o, Claude, DeepSeek...)
- Vietnamese-optimized prompts — pronoun modes, cultural context, term consistency
- Glossary — keep character names, skills, and locations consistent
- Preview & Edit — review and edit translations before writing back to game
- Auto Backup — backs up original files before overwriting

---

## Installation

### Requirements
- Python 3.9+
- API Key: Google Gemini (https://aistudio.google.com/) or OpenRouter (https://openrouter.ai/)

### Setup

```bash
git clone https://github.com/hunghhhh/vn-rpg-translator.git
cd vn-rpg-translator
pip install -r requirements.txt
```

---

## Quick Start

### 1. Configure API key

```bash
python main.py config
```

### 2. Extract text from game

```bash
# RPG Maker MV/MZ
python main.py extract --engine mv --game-dir "D:/Games/MyGame"

# RPG Maker VX Ace
python main.py extract --engine vxa --game-dir "D:/Games/MyGame"
```

### 3. Edit glossary (optional but recommended)

Open `output/glossary.json` and add character names, locations, etc:

```json
{
  "キャラ": "Kira",
  "魔王": "Demon King",
  "王国": "Kingdom"
}
```

### 4. Translate

```bash
python main.py translate --preview
```

`--preview` opens an interactive terminal editor so you can review and fix translations before saving.

### 5. Write back to game

```bash
python main.py rebuild --engine mv --game-dir "D:/Games/MyGame"
```

---

## Configuration (`config.json`)

```json
{
  "api_provider": "gemini",
  "gemini_api_key": "...",
  "openrouter_api_key": "...",
  "openrouter_model": "deepseek/deepseek-chat",
  "batch_size": 20,
  "pronoun_mode": "neutral"
}
```

**`pronoun_mode`** — Vietnamese pronoun style:

| Mode    | Usage                                         |
|---------|-----------------------------------------------|
| neutral | toi / ban / co ay — safe default              |
| formal  | anh / chi / ong / ba — period pieces          |
| casual  | tao / may / no — slice of life, adult games   |

---

## Project Structure

```
vn-rpg-translator/
├── main.py                      # CLI entry point
├── config.json                  # Config (auto-created on first run)
├── requirements.txt
├── translator/
│   ├── config.py                # Config manager
│   ├── glossary.py              # Glossary manager
│   ├── preview.py               # Terminal preview & edit UI
│   ├── extractor/
│   │   ├── mv_extractor.py      # RPG Maker MV/MZ extractor
│   │   └── vxa_extractor.py     # RPG Maker VX Ace extractor
│   ├── ai/
│   │   ├── base.py              # Shared interface + prompt builder
│   │   ├── gemini_client.py     # Gemini API client
│   │   └── openrouter_client.py # OpenRouter API client
│   └── rebuilder/
│       ├── mv_rebuilder.py      # MV/MZ file writer
│       └── vxa_rebuilder.py     # VXA file writer
└── output/                      # Auto-created after extract
    ├── extracted.json           # Source Japanese strings
    ├── translated.json          # Translated Vietnamese strings
    └── glossary.json            # Term glossary
```

---

## Roadmap

- [ ] Web UI (Flask/FastAPI)
- [ ] Wolf RPG Editor support
- [ ] Context-aware translation (pass surrounding lines to AI)
- [ ] Character voice/personality profiles
- [ ] Token cost estimator before translating

---

## Contributing

PRs and issues welcome.

---

## License

MIT
