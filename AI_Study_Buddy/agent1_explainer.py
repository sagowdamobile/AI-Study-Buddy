from typing import Dict, List, Optional

from utils import ask_gemini, extract_json_from_text


def explain_topic(topic: str, extra_context: Optional[str] = None) -> str:
    """Explain a topic in beginner-friendly language."""
    context_block = f"\nUse this reference context too:\n{extra_context}" if extra_context else ""

    prompt = f"""
You are Study Buddy Agent.
Explain this topic for a beginner student: {topic}

Rules:
- Use simple language.
- Give a short real-world example.
- Add a mini recap at the end.
- Keep it easy to understand.
{context_block}
"""

    return ask_gemini(prompt)


def summarize_notes(notes: str) -> str:
    """Summarize student notes in short, clear points."""
    prompt = f"""
You are Study Buddy Agent.
Summarize these notes in easy bullet points:

{notes}

Rules:
- Keep it concise.
- Use simple words.
- Highlight what is most important.
"""

    return ask_gemini(prompt)


def generate_key_points(topic: str, extra_context: Optional[str] = None) -> str:
    """Generate key takeaways for quick revision."""
    context_block = f"\nReference context:\n{extra_context}" if extra_context else ""

    prompt = f"""
You are Study Buddy Agent.
Generate 6-8 key points for this topic: {topic}

Rules:
- Use bullets.
- Keep each point short.
- Focus on exam-friendly revision.
{context_block}
"""

    return ask_gemini(prompt)


def generate_flashcards(topic: str, extra_context: Optional[str] = None) -> List[Dict[str, str]]:
    """Generate simple Q/A flashcards for active recall."""
    context_block = f"\nReference context:\n{extra_context}" if extra_context else ""

    prompt = f"""
You are Study Buddy Agent.
Create exactly 6 flashcards for this topic: {topic}
Return ONLY valid JSON in this format:
{{
  "flashcards": [
    {{"front": "question", "back": "answer"}}
  ]
}}

Rules:
- Keep front side short.
- Keep back side clear and beginner friendly.
{context_block}
"""

    result = ask_gemini(prompt)
    parsed = extract_json_from_text(result)
    cards = parsed.get("flashcards", [])

    if not isinstance(cards, list):
        return []

    cleaned_cards: List[Dict[str, str]] = []
    for card in cards:
        if isinstance(card, dict):
            cleaned_cards.append(
                {
                    "front": str(card.get("front", "")).strip(),
                    "back": str(card.get("back", "")).strip(),
                }
            )

    return [c for c in cleaned_cards if c["front"] and c["back"]]
