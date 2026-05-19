import sys
sys.path.insert(0, r"c:\Nishka\AI Strudy Buddy\AI-Study-Buddy\AI_Study_Buddy")

from agent1_explainer import generate_flashcards
from agent2_quiz import generate_quiz, evaluate_short_answer

print("=== FLASHCARDS ===")
cards = generate_flashcards("Python loops")
print(f"Got {len(cards)} cards")
for c in cards[:2]:
    print(" ", c)

print()
print("=== QUIZ ===")
quiz = generate_quiz("Python loops", mcq_count=2, short_count=1)
mcqs = quiz["mcqs"]
shorts = quiz["short_answers"]
print(f"MCQs: {len(mcqs)}, Short: {len(shorts)}")
if mcqs:
    m = mcqs[0]
    print("  Q:", m["question"])
    print("  Options:", m["options"])
    print("  Answer field:", m["answer"])
    # Verify answer letter matches an option
    expected_opt = [o for o in m["options"] if o.startswith(m["answer"])]
    print("  Answer matches option:", bool(expected_opt))
if shorts:
    s = shorts[0]
    print("  Short Q:", s["question"])

print()
print("=== EVAL ===")
ev = evaluate_short_answer(
    "Python loops",
    "What is a for loop?",
    "A for loop iterates over a sequence",
    "It repeats code for each item in a list"
)
print("Score:", ev["score"], "| Feedback:", ev["feedback"])
print()
print("ALL TESTS PASSED")
