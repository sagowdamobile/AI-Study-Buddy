import logging
from typing import Any, Dict, List, Optional

from utils import ask_gemini, extract_json_from_text

LOGGER = logging.getLogger(__name__)


def generate_quiz(
    topic: str,
    extra_context: Optional[str] = None,
    mcq_count: int = 5,
    short_count: int = 2,
) -> Dict[str, List[Dict[str, Any]]]:
    """Generate MCQ and short-answer quiz questions for a topic."""
    context_block = f"\nReference context:\n{extra_context}" if extra_context else ""

    prompt = f"""
You are Quiz Master Agent.
Create a quiz about: {topic}

Return ONLY valid JSON in this exact structure:
{{
  "mcqs": [
    {{
      "question": "...",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "answer": "A",
      "explanation": "..."
    }}
  ],
  "short_answers": [
    {{
      "question": "...",
      "sample_answer": "...",
      "explanation": "..."
    }}
  ]
}}

Rules:
- Generate exactly {mcq_count} MCQs.
- Generate exactly {short_count} short-answer questions.
- Keep questions beginner-friendly.
- Ensure correct answer letter matches one option.
{context_block}
    """

    result = ask_gemini(prompt)
    try:
        parsed = extract_json_from_text(result)
    except ValueError as exc:
        LOGGER.warning("Failed to parse quiz JSON: %s", exc)
        parsed = {}

    mcqs = parsed.get("mcqs", []) if isinstance(parsed, dict) else []
    shorts = parsed.get("short_answers", []) if isinstance(parsed, dict) else []

    if not isinstance(mcqs, list):
        mcqs = []
    if not isinstance(shorts, list):
        shorts = []

    cleaned_mcqs: List[Dict[str, Any]] = []
    for item in mcqs:
        if not isinstance(item, dict):
            continue
        options = item.get("options", [])
        if not isinstance(options, list):
            options = []

        cleaned_mcqs.append(
            {
                "question": str(item.get("question", "")).strip(),
                "options": [str(opt).strip() for opt in options][:4],
                "answer": str(item.get("answer", "")).strip().upper()[:1],
                "explanation": str(item.get("explanation", "")).strip(),
            }
        )

    cleaned_shorts: List[Dict[str, Any]] = []
    for item in shorts:
        if not isinstance(item, dict):
            continue
        cleaned_shorts.append(
            {
                "question": str(item.get("question", "")).strip(),
                "sample_answer": str(item.get("sample_answer", "")).strip(),
                "explanation": str(item.get("explanation", "")).strip(),
            }
        )

    return {
        "mcqs": [q for q in cleaned_mcqs if q["question"] and len(q["options"]) >= 2],
        "short_answers": [q for q in cleaned_shorts if q["question"]],
    }


def evaluate_short_answer(
    topic: str,
    question: str,
    sample_answer: str,
    user_answer: str,
) -> Dict[str, Any]:
    """Use Gemini to evaluate a student's short answer."""
    prompt = f"""
You are Quiz Master Agent.
Evaluate the student's answer.

Topic: {topic}
Question: {question}
Reference Answer: {sample_answer}
Student Answer: {user_answer}

Return ONLY valid JSON:
{{
  "score": 0 or 1,
  "feedback": "short, clear feedback"
}}

Rules:
- score 1 if mostly correct; otherwise 0.
- feedback should be encouraging and helpful.
"""

    result = ask_gemini(prompt)
    try:
        parsed = extract_json_from_text(result)
    except ValueError as exc:
        LOGGER.warning("Failed to parse short-answer evaluation JSON: %s", exc)
        parsed = {}

    score = int(parsed.get("score", 0)) if isinstance(parsed, dict) else 0
    feedback = str(parsed.get("feedback", "No feedback generated.")).strip() if isinstance(parsed, dict) else "No feedback generated."

    return {"score": 1 if score == 1 else 0, "feedback": feedback}
