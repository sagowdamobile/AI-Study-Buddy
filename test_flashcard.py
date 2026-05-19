import sys
sys.path.insert(0, r"c:\Nishka\AI Strudy Buddy\AI-Study-Buddy\AI_Study_Buddy")
from utils import ask_ollama_json, extract_json_from_text

prompt = (
    "You are a study assistant. Create exactly 6 flashcards for the topic: Python loops\n"
    "Output ONLY a JSON object with this exact structure, no extra text:\n"
    '{"flashcards": [{"front": "question here", "back": "answer here"}]}\n'
    "Make 6 flashcard objects. Keep each front short, each back clear and beginner-friendly."
)
raw = ask_ollama_json(prompt)
print("RAW:", repr(raw[:600]))
print()
parsed = extract_json_from_text(raw)
print("TOP-LEVEL KEYS:", list(parsed.keys()) if isinstance(parsed, dict) else type(parsed))
print("flashcards key:", "flashcards" in parsed if isinstance(parsed, dict) else False)
if isinstance(parsed, dict):
    for k, v in parsed.items():
        print(f"  {k!r}: {type(v).__name__} len={len(v) if hasattr(v,'__len__') else 'N/A'}")
