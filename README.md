# AI Study Buddy + Quiz Master

A beginner-friendly multi-agent AI project built with Python, Streamlit, and Google Gemini.

## What this app does

This app has **two AI agents**:

1. **Study Buddy Agent**
- Explains any topic in simple language
- Summarizes your notes
- Generates key revision points
- Creates optional flashcards

2. **Quiz Master Agent**
- Creates MCQs and short-answer questions
- Shows answers and explanations
- Evaluates your responses
- Tracks your quiz progress over time

## Project Structure

```text
AI_Study_Buddy/
├── main.py
├── agent1_explainer.py
├── agent2_quiz.py
├── utils.py
├── .env
├── .gitignore
├── requirements.txt
└── data/
	└── study_history.json
```

## Setup (Local)

1. Open terminal in the project root.
2. Move into the app folder:

```bash
cd AI_Study_Buddy
```

3. Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

4. Install required packages:

```bash
pip install -r requirements.txt
```

5. Add your Gemini API key in `.env`:

```env
GEMINI_API_KEY=your_real_api_key_here
```

6. Run the app:

```bash
streamlit run main.py
```

## How the two agents work together

1. You enter a topic (and optionally notes/PDF).
2. `main.py` builds shared context.
3. `agent1_explainer.py` uses that context to teach and simplify the topic.
4. `agent2_quiz.py` uses the same context to generate and evaluate quiz questions.
5. `utils.py` manages Gemini calls, API key loading, PDF text extraction, and history storage.

Both agents are separate files but connected through `main.py` and shared helper functions in `utils.py`.

## Notes

- Model used: **Gemini 1.5 Flash** (`gemini-1.5-flash`)
- API key is read securely from environment variables
- Quiz history is saved in `data/study_history.json`
