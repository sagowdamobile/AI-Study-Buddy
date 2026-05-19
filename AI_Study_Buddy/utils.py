import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from pypdf import PdfReader

# Keep one central path for history so every module uses the same file.
HISTORY_FILE = Path(__file__).parent / "data" / "study_history.json"

# Ollama API endpoint
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:1b"


def ask_ollama(prompt: str, model: str = OLLAMA_MODEL) -> str:
    """Send a prompt to Ollama and return plain text response."""
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Cannot connect to Ollama. Make sure Ollama is running (ollama serve) on localhost:11434"
        )
    except requests.exceptions.Timeout:
        raise RuntimeError("Ollama request timed out. The model may be processing a complex prompt.")
    except Exception as exc:
        raise RuntimeError(f"Ollama request failed: {str(exc)}") from exc


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
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                pass
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
