import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv
from pypdf import PdfReader

# Keep one central path for history so every module uses the same file.
HISTORY_FILE = Path(__file__).parent / "data" / "study_history.json"
ENV_FILE = Path(__file__).resolve().parent / ".env"

load_dotenv(dotenv_path=ENV_FILE, override=True)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")


def _post_ollama(payload: Dict[str, Any]) -> str:
    """Internal helper: POST to Ollama and return the response text."""
    url = f"{OLLAMA_BASE_URL}/api/generate"
    try:
        response = requests.post(url, json=payload, timeout=180)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Cannot connect to Ollama. Make sure Ollama is running (ollama serve) on "
            + OLLAMA_BASE_URL
        )
    except requests.exceptions.Timeout:
        raise RuntimeError("Ollama request timed out. The model may be taking too long to respond.")
    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(f"Ollama returned an error: {exc}") from exc

    data = response.json()
    text = data.get("response", "").strip()
    if not text:
        raise RuntimeError("Ollama returned an empty response.")
    return text


def ask_ollama(prompt: str) -> str:
    """Send a prompt to a local Ollama model and return the response text."""
    return _post_ollama({"model": OLLAMA_MODEL, "prompt": prompt, "stream": False})


def ask_ollama_json(prompt: str) -> str:
    """Send a prompt requiring JSON output. Uses Ollama format=json to enforce valid JSON."""
    return _post_ollama({"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "format": "json"})


def extract_json_from_text(text: str) -> Dict[str, Any]:
    """Safely parse JSON from model output with multiple fallback strategies."""
    cleaned = text.strip()

    # Strategy 1: strip markdown code fences
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()

    # Strategy 2: direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Strategy 3: find outermost { ... } block
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError:
            pass

    # Strategy 4: find outermost [ ... ] block
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not parse JSON from model output.")


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
