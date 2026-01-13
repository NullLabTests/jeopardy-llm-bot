import ollama  # pip install ollama; ollama pull qwen2.5:7b
import pandas as pd
import random
import json
import os
import sys

TSV_URL = "https://github.com/jwolle1/jeopardy_clue_dataset/raw/main/combined_season1-41.tsv"
LOCAL_TSV = "combined_season1-41.tsv"
WEAK_FILE = "weak_categories.json"
SCORE_FILE = "score.json"

if not os.path.exists(LOCAL_TSV):
    print("Downloading TSV (one-time, ~200 MB)...")
    df = pd.read_csv(TSV_URL, sep='\t', low_memory=False)
    df.to_csv(LOCAL_TSV, sep='\t', index=False)
else:
    print("Loading local TSV...")
    df = pd.read_csv(LOCAL_TSV, sep='\t', low_memory=False)

print(f"Loaded {len(df):,} clues.")

weak_cats = set()
score = 0
if os.path.exists(WEAK_FILE):
    with open(WEAK_FILE) as f:
        weak_cats = set(json.load(f))
if os.path.exists(SCORE_FILE):
    with open(SCORE_FILE) as f:
        score = json.load(f).get('score', 0)

def save_progress():
    with open(WEAK_FILE, 'w') as f:
        json.dump(list(weak_cats), f)
    with open(SCORE_FILE, 'w') as f:
        json.dump({'score': score}, f)

def get_clue(prefer_weak=False):
    if prefer_weak and weak_cats:
        cat = random.choice(list(weak_cats))
        cands = df[df['category'].str.contains(cat, case=False, na=False)]
        if not cands.empty:
            return cands.sample(1).iloc[0].to_dict()
    return df.sample(1).iloc[0].to_dict()

def play():
    global score
    print(f"\nJeopardy Bot | Score: {score} | Weak cats: {len(weak_cats)}")
    print("Type 'quit' to exit and save")

    while True:
        clue = get_clue(prefer_weak=bool(weak_cats))
        print(f'\n${clue['clue_value']} {clue['category']} ({clue['air_date']})")
        print(f'Clue: {clue['answer']}")

        user = input("Your response (as question): ").strip().lower()
        if user in ['quit', 'q', 'exit']:
            save_progress()
            print(f"\nSaved. Final score: {score}")
            break

        correct = clue['question'].lower() in user or user in clue['question'].lower()
        if correct:
            score += clue['clue_value']
            print(f'Correct! +${clue['clue_value']}")
            weak_cats.discard(clue['category'])
        else:
            score -= clue['clue_value']
            print(f'Wrong! -${clue['clue_value']} | Correct: {clue['question']}")
            weak_cats.add(clue['category'])

        print(f"Score now: {score}")

if __name__ == "__main__":
    try:
        play()
    except KeyboardInterrupt:
        save_progress()
        print("\nInterrupted. Progress saved.")
