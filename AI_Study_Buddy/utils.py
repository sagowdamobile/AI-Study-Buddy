import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from dotenv import load_dotenv
from pypdf import PdfReader

# Keep one central path for history so every module uses the same file.
HISTORY_FILE = Path(__file__).parent / "data" / "study_history.json"
ENV_FILE = Path(__file__).resolve().parent / ".env"


def load_api_key() -> str:
    """Load Gemini API key from .env file and return it."""
    # Always load from the app-local .env file and override stale global values.
    load_dotenv(dotenv_path=ENV_FILE, override=True)
    api_key = os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'")

    if api_key.lower() in {"", "your_gemini_api_key_here", "replace_me"}:
        raise ValueError(
            "Gemini API key is not set. Open AI_Study_Buddy/.env and set GEMINI_API_KEY to your real key."
        )

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing. Add it in your .env file before running the app."
        )
    return api_key


def get_gemini_model(model_name: str = "gemini-1.5-flash") -> genai.GenerativeModel:
    """Create and return a Gemini model instance."""
    api_key = load_api_key()
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)


def ask_gemini(prompt: str, model_name: str = "gemini-1.5-flash") -> str:
    """Send a prompt to Gemini and return plain text response."""
    model = get_gemini_model(model_name)
    try:
        response = model.generate_content(prompt)
    except Exception as exc:
        message = str(exc)
        if "API_KEY_INVALID" in message or "API key not valid" in message:
            raise ValueError(
                "Invalid Gemini API key. Please generate a new key in Google AI Studio, "
                "paste it into AI_Study_Buddy/.env as GEMINI_API_KEY, then restart Streamlit."
            ) from exc
        raise RuntimeError(f"Gemini request failed: {message}") from exc

    if hasattr(response, "text") and response.text:
        return response.text.strip()

    # Fallback in case text is empty but candidates exist.
    try:
        return str(response.candidates[0].content.parts[0].text).strip()
    except Exception as exc:
        raise RuntimeError("Gemini returned an unexpected response format.") from exc


def extract_json_from_text(text: str) -> Dict[str, Any]:
    """Safely parse JSON from model output, even if wrapped in markdown."""
    cleaned = text.strip()

    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError("Could not parse JSON from model output.") from exc


def read_pdf_text(uploaded_file: Any) -> str:
    """Extract text from an uploaded PDF file."""
    reader = PdfReader(uploaded_file)
    pages_text: List[str] = []

    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            pages_text.append(page_text)

    return "\n".join(pages_text).strip()


def load_history() -> List[Dict[str, Any]]:
    """Load saved study sessions from disk."""
    if not HISTORY_FILE.exists():
        return []

    try:
        content = HISTORY_FILE.read_text(encoding="utf-8")
        return json.loads(content)
    except Exception:
        return []


def save_history_entry(entry: Dict[str, Any]) -> None:
    """Append one study session entry to history file."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    history = load_history()
    history.append(entry)
    HISTORY_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")


def build_history_entry(topic: str, score: int, total: int) -> Dict[str, Any]:
    """Create a consistent history object for one quiz attempt."""
    percent = round((score / total) * 100, 1) if total else 0.0
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "topic": topic,
        "score": score,
        "total": total,
        "percent": percent,
    }


def average_score_percent(history: List[Dict[str, Any]]) -> float:
    """Calculate average score percentage from all history entries."""
    if not history:
        return 0.0

    values = [float(item.get("percent", 0.0)) for item in history]
    return round(sum(values) / len(values), 1)
