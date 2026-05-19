import traceback
from typing import Dict, List

import streamlit as st

from .agent1_explainer import explain_topic, generate_flashcards, generate_key_points, summarize_notes
from .agent2_quiz import evaluate_short_answer, generate_quiz
from .utils import (
    average_score_percent,
    build_history_entry,
    load_history,
    read_pdf_text,
    save_history_entry,
)


def show_error(message_prefix: str, exc: Exception) -> None:
    """Show friendly errors for known issues and debug details for unexpected ones."""
    st.error(f"{message_prefix}: {exc}")
    if not isinstance(exc, ValueError):
        with st.expander("Technical details", expanded=False):
            st.code(traceback.format_exc())


def apply_dark_theme() -> None:
    """Inject custom CSS for a clean, dark, student-friendly interface."""
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap');

            :root {
                --bg: #0f172a;
                --card: #1e293b;
                --card-soft: #182336;
                --text: #e2e8f0;
                --muted: #94a3b8;
                --accent: #22d3ee;
                --accent-2: #f59e0b;
                --ok: #34d399;
            }

            html, body, [class*="css"] {
                font-family: 'Manrope', sans-serif;
                color: var(--text);
            }

            .stApp {
                background:
                    radial-gradient(circle at 20% 10%, rgba(34,211,238,0.12), transparent 30%),
                    radial-gradient(circle at 85% 15%, rgba(245,158,11,0.10), transparent 28%),
                    linear-gradient(160deg, #0b1220 0%, #0f172a 40%, #111827 100%);
            }

            .block-container {
                max-width: 1100px;
                padding-top: 2rem;
                padding-bottom: 3rem;
            }

            .card {
                background: linear-gradient(180deg, var(--card) 0%, var(--card-soft) 100%);
                border: 1px solid rgba(148, 163, 184, 0.2);
                border-radius: 18px;
                padding: 1rem 1.2rem;
                margin-bottom: 0.9rem;
                box-shadow: 0 12px 30px rgba(2, 6, 23, 0.35);
            }

            .headline {
                font-weight: 800;
                font-size: 2rem;
                margin-bottom: 0.35rem;
                letter-spacing: 0.2px;
            }

            .subline {
                color: var(--muted);
                margin-bottom: 1rem;
            }

            .pill {
                display: inline-block;
                padding: 0.25rem 0.6rem;
                border-radius: 999px;
                font-size: 0.75rem;
                font-weight: 700;
                margin-right: 0.4rem;
                color: #0b1220;
                background: linear-gradient(135deg, var(--accent), #67e8f9);
            }

            .stButton > button {
                border-radius: 12px;
                border: none;
                padding: 0.6rem 1rem;
                font-weight: 700;
            }

            .stTextInput > div > div,
            .stTextArea > div > div,
            .stSelectbox > div > div {
                border-radius: 12px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def setup_page() -> None:
    """Configure Streamlit page settings and initialize session state keys."""
    st.set_page_config(
        page_title="AI Study Buddy + Quiz Master",
        page_icon="📘",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_dark_theme()

    defaults = {
        "study_explanation": "",
        "study_summary": "",
        "study_key_points": "",
        "flashcards": [],
        "quiz": {"mcqs": [], "short_answers": []},
        "quiz_result": None,
        "pdf_context": "",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_header() -> None:
    """Render app title and quick labels."""
    st.markdown('<div class="headline">AI Study Buddy + Quiz Master</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subline">Two AI agents collaborate: one teaches, one tests. Built with Streamlit + Gemini 1.5 Flash.</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<span class="pill">Study Buddy Agent</span><span class="pill">Quiz Master Agent</span>',
        unsafe_allow_html=True,
    )


def build_context(notes: str, pdf_text: str) -> str:
    """Combine notes and PDF text so both agents can use richer context."""
    context_parts: List[str] = []
    if notes.strip():
        context_parts.append(f"Student Notes:\n{notes.strip()}")
    if pdf_text.strip():
        context_parts.append(f"PDF Reference:\n{pdf_text.strip()}")

    # Keep context reasonably sized to avoid very long prompts.
    joined = "\n\n".join(context_parts)
    return joined[:12000]


def render_sidebar() -> Dict[str, int]:
    """Render sidebar controls and return selected options."""
    st.sidebar.title("Control Center")
    st.sidebar.caption("Adjust quiz settings, upload notes, and track your progress.")

    mcq_count = st.sidebar.slider("Number of MCQs", 3, 8, 5)
    short_count = st.sidebar.slider("Number of short-answer questions", 1, 4, 2)
    use_flashcards = st.sidebar.checkbox("Generate flashcards", value=True)

    st.sidebar.markdown("---")
    uploaded_pdf = st.sidebar.file_uploader("Upload a PDF for extra context", type=["pdf"])

    if uploaded_pdf is not None:
        with st.sidebar.spinner("Reading PDF..."):
            try:
                st.session_state["pdf_context"] = read_pdf_text(uploaded_pdf)
                if st.session_state["pdf_context"]:
                    st.sidebar.success("PDF text loaded and ready for both agents.")
                else:
                    st.sidebar.warning("PDF uploaded, but no readable text was found.")
            except Exception as exc:
                st.sidebar.error(f"Could not read PDF: {exc}")

    st.sidebar.markdown("---")
    history = load_history()
    avg_percent = average_score_percent(history)
    st.sidebar.subheader("Progress Tracker")
    st.sidebar.metric("Total Quiz Attempts", len(history))
    st.sidebar.metric("Average Score", f"{avg_percent}%")

    if history:
        st.sidebar.write("Recent Attempts")
        for item in history[-5:][::-1]:
            st.sidebar.caption(
                f"{item.get('timestamp', '-')}: {item.get('topic', '-')[:26]} | {item.get('score', 0)}/{item.get('total', 0)}"
            )

    return {
        "mcq_count": mcq_count,
        "short_count": short_count,
        "use_flashcards": int(use_flashcards),
    }


def render_study_outputs() -> None:
    """Show Study Buddy outputs in neat expandable sections."""
    if not st.session_state["study_explanation"]:
        return

    st.markdown("### Study Buddy Results")

    with st.expander("Simple Explanation", expanded=True):
        st.write(st.session_state["study_explanation"])

    if st.session_state["study_summary"]:
        with st.expander("Notes Summary", expanded=False):
            st.write(st.session_state["study_summary"])

    if st.session_state["study_key_points"]:
        with st.expander("Key Points for Revision", expanded=False):
            st.write(st.session_state["study_key_points"])

    if st.session_state["flashcards"]:
        with st.expander("Flashcards", expanded=False):
            for idx, card in enumerate(st.session_state["flashcards"], start=1):
                st.markdown(
                    f"<div class='card'><strong>Card {idx}</strong><br><br><em>Front:</em> {card['front']}<br><em>Back:</em> {card['back']}</div>",
                    unsafe_allow_html=True,
                )


def render_quiz_block(topic: str) -> None:
    """Render Quiz Master questions and evaluate student responses."""
    quiz = st.session_state["quiz"]
    mcqs = quiz.get("mcqs", [])
    shorts = quiz.get("short_answers", [])

    if not mcqs and not shorts:
        return

    st.markdown("### Quiz Master")

    for i, q in enumerate(mcqs, start=1):
        st.markdown(f"**MCQ {i}.** {q.get('question', '')}")
        selected = st.selectbox(
            "Choose your answer",
            options=["Select an option"] + q.get("options", []),
            key=f"mcq_select_{i}",
        )
        st.session_state[f"mcq_answer_{i}"] = selected

    for i, q in enumerate(shorts, start=1):
        st.markdown(f"**Short Answer {i}.** {q.get('question', '')}")
        short_ans = st.text_area("Your answer", key=f"short_answer_{i}", height=100)
        st.session_state[f"short_user_{i}"] = short_ans

    if st.button("Submit Quiz", type="primary"):
        with st.spinner("Evaluating your answers..."):
            try:
                score = 0
                total = len(mcqs) + len(shorts)
                details: List[str] = []

                for i, q in enumerate(mcqs, start=1):
                    selected = st.session_state.get(f"mcq_answer_{i}", "")
                    selected_letter = selected[:1].upper() if selected and selected != "Select an option" else ""
                    correct_letter = q.get("answer", "")[:1].upper()

                    if selected_letter == correct_letter:
                        score += 1
                        details.append(f"MCQ {i}: Correct")
                    else:
                        details.append(
                            f"MCQ {i}: Incorrect. Correct answer is {correct_letter}. {q.get('explanation', '')}"
                        )

                for i, q in enumerate(shorts, start=1):
                    user_answer = st.session_state.get(f"short_user_{i}", "").strip()
                    if not user_answer:
                        details.append(f"Short Answer {i}: No answer provided.")
                        continue

                    evaluation = evaluate_short_answer(
                        topic=topic,
                        question=q.get("question", ""),
                        sample_answer=q.get("sample_answer", ""),
                        user_answer=user_answer,
                    )

                    if evaluation.get("score", 0) == 1:
                        score += 1
                        details.append(f"Short Answer {i}: Correct. {evaluation.get('feedback', '')}")
                    else:
                        details.append(
                            f"Short Answer {i}: Needs improvement. {evaluation.get('feedback', '')}"
                        )

                st.session_state["quiz_result"] = {
                    "score": score,
                    "total": total,
                    "details": details,
                }

                save_history_entry(build_history_entry(topic=topic, score=score, total=total))
            except Exception as exc:
                st.error(f"Error while evaluating quiz: {exc}")
                st.code(traceback.format_exc())

    result = st.session_state.get("quiz_result")
    if result:
        score = int(result.get("score", 0))
        total = int(result.get("total", 0))
        percent = (score / total) if total else 0

        st.success(f"Your Score: {score}/{total}")
        st.progress(percent)

        with st.expander("Review Answers and Explanations", expanded=True):
            for item in result.get("details", []):
                st.write(f"- {item}")


def main() -> None:
    """Main Streamlit app flow."""
    setup_page()
    render_header()
    options = render_sidebar()

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    topic = st.text_input("Enter a study topic", placeholder="Example: Photosynthesis")
    notes = st.text_area(
        "Optional: paste your own notes",
        placeholder="Paste class notes to get a custom summary and better quiz...",
        height=160,
    )

    col1, col2 = st.columns(2)
    generate_study = col1.button("Generate Study Guide", type="primary")
    generate_quiz_btn = col2.button("Generate Quiz")
    st.markdown("</div>", unsafe_allow_html=True)

    context_text = build_context(notes=notes, pdf_text=st.session_state.get("pdf_context", ""))

    if generate_study:
        if not topic.strip():
            st.warning("Please enter a topic first.")
        else:
            with st.spinner("Study Buddy Agent is preparing your explanation..."):
                try:
                    st.session_state["study_explanation"] = explain_topic(topic=topic, extra_context=context_text)
                    st.session_state["study_key_points"] = generate_key_points(topic=topic, extra_context=context_text)

                    if notes.strip():
                        st.session_state["study_summary"] = summarize_notes(notes=notes)
                    else:
                        st.session_state["study_summary"] = ""

                    if options.get("use_flashcards", 1):
                        st.session_state["flashcards"] = generate_flashcards(topic=topic, extra_context=context_text)
                    else:
                        st.session_state["flashcards"] = []
                except Exception as exc:
                    show_error("Error while generating study guide", exc)

    if generate_quiz_btn:
        if not topic.strip():
            st.warning("Please enter a topic first.")
        else:
            with st.spinner("Quiz Master Agent is creating your quiz..."):
                try:
                    st.session_state["quiz"] = generate_quiz(
                        topic=topic,
                        extra_context=context_text,
                        mcq_count=options["mcq_count"],
                        short_count=options["short_count"],
                    )
                    st.session_state["quiz_result"] = None
                except Exception as exc:
                    show_error("Error while generating quiz", exc)

    render_study_outputs()
    render_quiz_block(topic=topic)


if __name__ == "__main__":
    main()
