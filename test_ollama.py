import requests
import json

# Test 1: format=json for flashcards
payload = {
    "model": "llama3.2:1b",
    "prompt": 'You are a study assistant. Create exactly 2 flashcards for the topic: Python loops\nOutput ONLY a JSON object with this exact structure, no extra text:\n{"flashcards": [{"front": "question here", "back": "answer here"}]}\nMake 2 flashcard objects.',
    "stream": False,
    "format": "json"
}
print("=== TEST 1: flashcards with format=json ===")
r = requests.post("http://localhost:11434/api/generate", json=payload, timeout=60)
data = r.json()
raw = data.get("response", "")
print("RAW:", repr(raw[:600]))
try:
    parsed = json.loads(raw)
    print("PARSED OK:", parsed)
except Exception as e:
    print("PARSE FAILED:", e)

print()

# Test 2: format=json for quiz
payload2 = {
    "model": "llama3.2:1b",
    "prompt": 'You are a quiz creator. Create a quiz about: Python loops\nOutput ONLY a JSON object with this exact structure:\n{"mcqs": [{"question": "q", "options": ["A) opt1", "B) opt2", "C) opt3", "D) opt4"], "answer": "A", "explanation": "reason"}], "short_answers": [{"question": "q", "sample_answer": "answer", "explanation": "reason"}]}\nGenerate exactly 2 mcq objects and exactly 1 short_answer objects.',
    "stream": False,
    "format": "json"
}
print("=== TEST 2: quiz with format=json ===")
r2 = requests.post("http://localhost:11434/api/generate", json=payload2, timeout=60)
data2 = r2.json()
raw2 = data2.get("response", "")
print("RAW:", repr(raw2[:800]))
try:
    parsed2 = json.loads(raw2)
    print("PARSED OK keys:", list(parsed2.keys()))
    print("MCQs count:", len(parsed2.get("mcqs", [])))
    print("Short answers count:", len(parsed2.get("short_answers", [])))
except Exception as e:
    print("PARSE FAILED:", e)
