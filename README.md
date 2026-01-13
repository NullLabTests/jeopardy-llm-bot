# Jeopardy! Learning Bot

Offline Jeopardy! practice with full J-Archive dataset (~539k clues).

## Features
- Caches TSV locally after one download
- Prefers weak categories you miss
- Basic keyword judging
- Saves score + weak cats between runs

## Quick start
pip install -r requirements.txt
python jeopardy_bot.py

Type answer as question. 'quit' to save/exit.

## Upgrades
1. LLM judging (Ollama)
   pip install ollama
   ollama pull qwen2.5:7b   # or phi3:mini
   Edit jeopardy_bot.py to use Ollama for judging.

2. Category picker
3. Hint/explain commands

Data: https://github.com/jwolle1/jeopardy_clue_dataset

Good luck on the test!
