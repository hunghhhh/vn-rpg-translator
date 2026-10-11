# VN RPG Translator

A CLI pipeline to extract, translate, and re-inject text for RPG Maker games from Japanese to Vietnamese using AI.

Supported engines: RPG Maker MV, MZ (.json) and VX Ace (.rvdata2).

---

## Philosophy

VN RPG Translator acts as an engine bridge: it parses game archives, isolates translatable Japanese text while preserving engine control codes (\c[n], \v[n], etc.), and reinjects the translated text back into the game data structures.

Translation quality depends entirely on the AI model you choose. The tool is designed to be model-agnostic: you can use fast and cost-effective models (Gemini Flash), flagship reasoning models (Claude Opus, GPT-4o), open-weight powerhouses (Llama 3.3 70B, DeepSeek V3/R1), or completely offline local models (via Ollama or LM Studio).

---

## Supported AI Providers & Models

### 1. Google Gemini
- Default: `gemini-2.5-flash` (fast, generous free tier)
- Also supports: `gemini-2.5-pro`, `gemini-1.5-pro`
- Requires Gemini API key from https://aistudio.google.com/apikey

### 2. OpenRouter (Access to 100+ models)
- Anthropic: `anthropic/claude-3-opus`, `anthropic/claude-3.5-sonnet`
- Meta: `meta-llama/llama-3.3-70b-instruct`, `meta-llama/llama-3.1-405b-instruct`
- DeepSeek: `deepseek/deepseek-chat` (V3), `deepseek/deepseek-reasoner` (R1)
- OpenAI: `openai/gpt-4o`, `openai/gpt-4o-mini`
- Requires OpenRouter API key from https://openrouter.ai/

### 3. Local / Custom OpenAI-compatible Endpoints
- Ollama: `http://localhost:11434/v1/chat/completions` (run Llama 3, Qwen 2.5 offline for free)
- LM Studio: `http://localhost:1234/v1/chat/completions`
- vLLM / LocalAI / Any custom endpoint

---

## Features

- Auto Extract: Reads database, maps, and common events, extracting Japanese text while keeping engine tags.
- Model Flexibility: Switch freely between Gemini, Claude Opus, Llama 3, DeepSeek, or local LLMs.
- Auto Word-Wrap: Includes an MZ plugin (`AutoWordWrap.js`) to prevent text from overflowing message windows.
- Vietnamese Localization Controls: Pronoun modes (`neutral`, `formal`, `casual`) and custom glossary.
- Preview & Edit: Terminal table preview to review and adjust translations before rebuilding.
- Targeted Testing: Filter by map ID (`--filter Map081`) and limit test size (`--limit 20`).
- Auto Backup: Creates timestamped backups before writing back to game files.

---

## Installation

### Requirements
- Python 3.9+
- An API key (Gemini, OpenRouter) or a running local LLM (Ollama).

### Setup

```bash
git clone https://github.com/hunghhhh/vn-rpg-translator.git
cd vn-rpg-translator
pip install -r requirements.txt
```

---

## Quick Start

### 1. Configure Provider & Model

```bash
python main.py config
```

Select your provider (`gemini`, `openrouter`, or `custom`), enter your API key, and choose your preferred model.

### 2. Extract Text from Game

```bash
# RPG Maker MV/MZ
python main.py extract --engine mv --game-dir "D:/Games/MyGame"

# RPG Maker VX Ace
python main.py extract --engine vxa --game-dir "D:/Games/MyGame"
```

Text is saved to `output/extracted.json`.

### 3. Set Glossary (Optional)

Add consistent character names and terminology in `output/glossary.json`:

```json
{
  "ミユキ": "Miyuki",
  "レニアド": "Renyad",
  "魔王": "Ma Vuong"
}
```

Or manage it interactively:
```bash
python main.py glossary
```

### 4. Translate

```bash
# Test translate first 20 strings of prologue map with preview:
python main.py translate --filter Map081 --limit 20 --preview

# Bulk translate all remaining strings:
python main.py translate --batch-size 40
```

### 5. Rebuild into Game

```bash
python main.py rebuild --engine mv --game-dir "D:/Games/MyGame"
```

Original game data is automatically backed up before overwriting.

---

## Text Overflow & Auto Word-Wrap (RPG Maker MZ)

Japanese sentences are compact (Kanji), while Vietnamese and English text is significantly longer. Standard RPG Maker message windows do not auto-wrap words by default, which can cause translated lines to clip past the right border.

To fix this, an auto word-wrap plugin is provided in `translator/plugins/AutoWordWrap.js`:

1. Copy `translator/plugins/AutoWordWrap.js` into your game's `js/plugins/` directory.
2. Open `js/plugins.js` and add this entry before the closing `];`:
```javascript
{"name":"AutoWordWrap","status":true,"description":"Auto Word Wrap for Message Window","parameters":{}}
```
3. Launch the game. Text will now dynamically wrap to the next line when approaching the right margin.

---

## Configuration Reference (`config.json`)

```json
{
  "api_provider": "openrouter",
  "gemini_api_key": "",
  "gemini_model": "gemini-2.5-flash",
  "openrouter_api_key": "sk-or-v1-...",
  "openrouter_model": "anthropic/claude-3-opus",
  "custom_api_url": "http://localhost:11434/v1/chat/completions",
  "custom_api_key": "ollama",
  "batch_size": 20,
  "pronoun_mode": "neutral",
  "source_lang": "ja",
  "target_lang": "vi"
}
```

---

## License

MIT
