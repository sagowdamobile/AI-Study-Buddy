from typing import Any, Dict, List, Optional

from utils import ask_ollama_json, extract_json_from_text

_LETTERS = ["A", "B", "C", "D"]


def _normalize_options(options: List[Any]) -> List[str]:
    """Ensure every option has an 'A) ' style letter prefix for consistent grading."""
    normalized: List[str] = []
    for idx, opt in enumerate(options[:4]):
        opt_str = str(opt).strip()
        # Already has a letter prefix like "A)" or "A." or "A:"
        if len(opt_str) >= 2 and opt_str[0].upper() in _LETTERS and opt_str[1] in ").:-":
            normalized.append(opt_str)
        elif idx < len(_LETTERS):
            normalized.append(f"{_LETTERS[idx]}) {opt_str}")
        else:
            normalized.append(opt_str)
    return normalized


def _generate_mcqs(topic: str, mcq_count: int, context_block: str) -> List[Dict[str, Any]]:
    """Generate MCQ questions via Ollama."""
    prompt = (
        f"You are a quiz creator. Create exactly {mcq_count} multiple choice questions about: {topic}\n"
        f"Output ONLY a JSON object with this exact structure, no extra text:\n"
        f'{{ "mcqs": [{{"question": "q", "options": ["A) opt1", "B) opt2", "C) opt3", "D) opt4"], "answer": "A", "explanation": "reason"}}] }}\n'
        f"Rules: generate exactly {mcq_count} mcq objects, keep beginner-friendly, answer field must be A B C or D only."
        f"{context_block}"
    )
    result = ask_ollama_json(prompt)
    parsed = extract_json_from_text(result)
    mcqs = parsed.get("mcqs", []) if isinstance(parsed, dict) else []
    return mcqs if isinstance(mcqs, list) else []


def _generate_short_answers(topic: str, short_count: int, context_block: str) -> List[Dict[str, Any]]:
    """Generate short-answer questions via Ollama."""
    prompt = (
        f"You are a quiz creator. Create exactly {short_count} short answer questions about: {topic}\n"
        f"Output ONLY a JSON object with this exact structure, no extra text:\n"
        f'{{ "short_answers": [{{"question": "q", "sample_answer": "answer", "explanation": "reason"}}] }}\n'
        f"Generate exactly {short_count} short_answer objects."
        f"{context_block}"
    )
    result = ask_ollama_json(prompt)
    parsed = extract_json_from_text(result)
    shorts = parsed.get("short_answers", []) if isinstance(parsed, dict) else []
    return shorts if isinstance(shorts, list) else []


def generate_quiz(
    topic: str,
    extra_context: Optional[str] = None,
    mcq_count: int = 5,
    short_count: int = 2,
) -> Dict[str, List[Dict[str, Any]]]:
    """Generate MCQ and short-answer quiz questions for a topic."""
    context_block = f"\nReference context:\n{extra_context}" if extra_context else ""

    raw_mcqs = _generate_mcqs(topic, mcq_count, context_block)
    raw_shorts = _generate_short_answers(topic, short_count, context_block)

    cleaned_mcqs: List[Dict[str, Any]] = []
    for item in raw_mcqs:
        if not isinstance(item, dict):
            continue
        options = _normalize_options(item.get("options", []))
        answer = str(item.get("answer", "")).strip().upper()[:1]
        cleaned_mcqs.append(
            {
                "question": str(item.get("question", "")).strip(),
                "options": options,
                "answer": answer,
                "explanation": str(item.get("explanation", "")).strip(),
            }
        )

    cleaned_shorts: List[Dict[str, Any]] = []
    for item in raw_shorts:
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
    """Use Ollama to evaluate a student's short answer."""
    prompt = (
        f"You are a quiz evaluator.\n"
        f"Topic: {topic}\n"
        f"Question: {question}\n"
        f"Reference Answer: {sample_answer}\n"
        f"Student Answer: {user_answer}\n"
        f"Output ONLY a JSON object with this exact structure, no extra text:\n"
        f'{{ "score": 1, "feedback": "your feedback here" }}\n'
        f"Set score to 1 if the student answer is mostly correct, 0 if not. Write short encouraging feedback."
    )

    result = ask_ollama_json(prompt)
    parsed = extract_json_from_text(result)

    score = int(parsed.get("score", 0)) if isinstance(parsed, dict) else 0
    feedback = str(parsed.get("feedback", "No feedback generated.")).strip() if isinstance(parsed, dict) else "No feedback generated."

    return {"score": 1 if score == 1 else 0, "feedback": feedback}

