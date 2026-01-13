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
        print(f"\n${clue['clue_value']} {clue['category']} ({clue['air_date']})")
        print(f"Clue: {clue['answer']}")

        user = input("Your response (as question): ").strip().lower()
        if user in ['quit', 'q', 'exit']:
            save_progress()
            print(f"\nSaved. Final score: {score}")
            break

        is_correct, reason = judge_with_llm(user, clue['question'], clue['answer'], clue['category'])
        if is_correct:
            score += clue['clue_value']
            print(f"Correct! +${clue['clue_value']}")
            weak_cats.discard(clue['category'])
        else:
            score -= clue['clue_value']
            print(f"Wrong! -${clue['clue_value']} | Correct: {clue['question']}")
            print(f"Judge says: {reason}")
            weak_cats.add(clue['category'])

        print(f"Score now: {score}")

if __name__ == "__main__":
    try:
        play()
    except KeyboardInterrupt:
        save_progress()
        print("\nInterrupted. Progress saved.")

def judge_with_llm(user_answer, correct_response, clue_text, category):
    # Normalize both answers
    user_norm = user_answer.lower().strip(' ?.!,"').replace("what is", "").replace("who is", "").replace("what are", "").replace("who are", "")
    correct_norm = correct_response.lower().strip(' ?.!,"').replace("what is", "").replace("who is", "").replace("what are", "").replace("who are", "")

    # Keyword fallback first (fast & reliable)
    if correct_norm in user_norm or user_norm in correct_norm or any(word in user_norm for word in correct_norm.split()):
        return True, "YES (keyword match)"

    # LLM only if keyword fails
    prompt = f"""Fair Jeopardy! judge.
Clue: "{clue_text}"
Correct (as question): "{correct_response}"
User said: "{user_answer}"
Category: {category}

Accept close facts, synonyms, partial answers, missing "What is", capitalization differences, minor typos.
Ignore rude/nonsense — just say NO.
Reply ONLY: YES or NO + one short reason. No lectures."""
    try:
        response = ollama.chat(model="llama3.2:1b", messages=[{"role": "user", "content": prompt}])
        ans = response["message"]["content"].strip()
        if "YES" in ans[:10].upper():
            return True, ans
        elif "NO" in ans[:10].upper():
            return False, ans
        else:
            return False, "NO (invalid judge response)"
    except Exception as e:
        return False, f"NO (LLM error: {str(e)} - keyword fallback failed)"
