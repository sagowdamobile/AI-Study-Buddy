import sys, os
sys.path.insert(0, os.path.dirname(__file__))

print("=== 1. Import check ===")
from utils import ask_ollama, ask_ollama_json, extract_json_from_text
from agent1_explainer import explain_topic, generate_flashcards, generate_key_points, summarize_notes
from agent2_quiz import generate_quiz, evaluate_short_answer
print("All imports OK")

print("\n=== 2. ask_ollama_json raw output ===")
raw = ask_ollama_json('Output ONLY a JSON object with key "test" and value "ok". No other text.')
print("RAW:", raw)
parsed = extract_json_from_text(raw)
print("PARSED:", parsed)

print("\n=== 3. generate_flashcards ===")
cards = generate_flashcards("Python lists")
print(f"Cards returned: {len(cards)}")
if cards:
    print("First card:", cards[0])
else:
    print("WARNING: 0 cards returned")

print("\n=== 4. generate_quiz (2 MCQs, 1 short) ===")
quiz = generate_quiz("Python lists", mcq_count=2, short_count=1)
print(f"MCQs: {len(quiz['mcqs'])}, Shorts: {len(quiz['short_answers'])}")
if quiz["mcqs"]:
    q = quiz["mcqs"][0]
    print("Q:", q["question"])
    print("Options:", q["options"])
    print("Answer:", q["answer"])

print("\n=== 5. evaluate_short_answer ===")
result = evaluate_short_answer(
    topic="Python lists",
    question="What method adds an item to a list?",
    sample_answer="append()",
    user_answer="You use append() to add items"
)
print("Score:", result["score"], "| Feedback:", result["feedback"])

print("\nAll checks complete.")
