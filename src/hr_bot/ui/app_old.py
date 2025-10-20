"""Streamlit front-end for the HR Bot."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, Future
from pathlib import Path
from typing import Any, Dict, List
import time

import streamlit as st

from hr_bot.crew import HrBot

PAGE_TITLE = "HR Assistant"
PAGE_ICON = "🧭"
DEFAULT_PLACEHOLDER = "Type your HR question here..."
DATA_DIR = Path("data").resolve()
WARMUP_QUERIES: List[str] = [
    "What is the sick leave policy?",
    "How many days of annual leave do employees get?",
    "Explain the maternity leave benefits.",
    "What is the paternity leave process?",
    "Outline the shared parental leave policy.",
    "What is the redundancy procedure?",
    "Tell me about flexible working arrangements.",
    "What is the work-from-home policy?",
    "How does the probation review work?",
    "What is the disciplinary policy?",
    "How do I report a grievance?",
    "What is the overtime compensation rule?",
    "Summarise the dress code guidance.",
    "Explain the travel expense policy.",
    "How do I request training support?",
    "What is the performance review timeline?",
    "How does compassionate leave work?",
    "What is the bereavement leave policy?",
    "How are bank holidays handled?",
    "What cybersecurity rules apply to email?",
    "What is the data protection policy for employees?",
    "How do I update emergency contact details?",
    "What happens during a return-to-work interview?",
    "Explain the onboarding checklist.",
    "How do I access my payslip?",
]


@st.cache_resource(show_spinner=False)
def load_bot() -> HrBot:
    """Instantiate the Crew only once per session."""
    return HrBot()


@st.cache_resource(show_spinner=False)
def get_executor() -> ThreadPoolExecutor:
    """Provide a shared thread pool for background inference."""
    return ThreadPoolExecutor(max_workers=2)


def ensure_sources_clickable(answer: str) -> str:
    """Convert Sources line into a well-formatted section with readable file references."""
    lines = answer.splitlines()
    if not lines:
        return answer

    for idx, line in enumerate(lines):
        if line.lower().startswith("sources:"):
            parts = [p.strip() for p in line.split(":", 1)[1].split(",") if p.strip()]
            source_items: List[str] = []
            
            for part in parts:
                # Handle both "filename" and "chunk_label filename" formats
                if " " in part:
                    chunk_label, _, file_name = part.partition(" ")
                    file_name = file_name.strip()
                else:
                    chunk_label = ""
                    file_name = part.strip()
                
                if not file_name:
                    continue
                    
                candidate_path = (DATA_DIR / file_name).resolve()
                try:
                    within_data_dir = candidate_path.is_relative_to(DATA_DIR)
                except ValueError:
                    within_data_dir = False
                    
                if candidate_path.is_file() and within_data_dir:
                    # Create a clean, readable display name
                    display_name = file_name.replace(".docx", "").replace(".pdf", "").replace("-", " ")
                    source_items.append(f"📄 **{display_name}**")
                else:
                    display_name = file_name.replace(".docx", "").replace(".pdf", "").replace("-", " ")
                    source_items.append(f"📄 **{display_name}**")
            
            if source_items:
                # Format sources in a professional way with a divider
                lines[idx] = "\n\n---\n\n**📚 Information sourced from:**\n\n" + " • ".join(source_items)
            else:
                lines[idx] = ""
            break

    return "\n".join(lines)


def soften_bullets(answer: str) -> str:
    """Replace leading * or - bullets with proper markdown bullets for better rendering."""
    formatted: List[str] = []
    in_list = False
    
    for line in answer.splitlines():
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]
        
        # Handle bullet points with proper spacing
        if stripped.startswith("* ") or stripped.startswith("- "):
            # Convert to proper markdown list item
            content = stripped[2:]
            formatted.append(f"{indent}- {content}")
            in_list = True
        elif stripped.startswith("*") and not stripped.startswith("**"):
            # Handle bullets without space after
            content = stripped[1:].lstrip()
            formatted.append(f"{indent}- {content}")
            in_list = True
        else:
            # Add extra spacing after lists for better readability
            if in_list and stripped and not stripped.startswith("-"):
                formatted.append("")
                in_list = False
            formatted.append(line)
    
    return "\n".join(formatted)


def format_answer(answer: str) -> str:
    """Apply presentation tweaks to keep responses professional."""
    answer = soften_bullets(answer)
    answer = ensure_sources_clickable(answer)
    return answer


def _warm_bot(bot: HrBot) -> None:
    """Preload indexes and caches so the first user sees a fast response."""
    try:
        hybrid_tool = getattr(bot, "hybrid_rag_tool", None)
        retriever = getattr(hybrid_tool, "retriever", None) if hybrid_tool else None
        if retriever:
            retriever.build_index(force_rebuild=False)
            cache_enabled = getattr(retriever, "enable_cache", True)
            if not cache_enabled:
                print("[warmup] ENABLE_CACHE is false; consider enabling it for faster responses.")
            for query in WARMUP_QUERIES:
                try:
                    retriever.hybrid_search(query, top_k=3)
                except Exception:
                    continue
        bot.crew()
    except Exception:
        # Warm-up is best-effort; ignore failures to avoid blocking UI startup.
        pass


def render_message(role: str, content: str) -> None:
    """Render message blocks with professional formatting."""
    with st.chat_message(role):
        if role == "assistant":
            # Apply formatting and render with proper markdown
            formatted_content = format_answer(content)
            st.markdown(formatted_content, unsafe_allow_html=False)
        else:
            st.markdown(content)


def query_bot(bot: HrBot, question: str) -> str:
    """Execute the crew and return the response string."""
    result = bot.crew().kickoff(inputs={"query": question, "context": ""})
    return str(result)


def _rerun() -> None:
    """Trigger a Streamlit rerun compatible with new and legacy APIs."""
    if hasattr(st, "rerun"):
        st.rerun()
    else:  # pragma: no cover - legacy fallback for older Streamlit versions
        st.experimental_rerun()


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide")

    # Custom CSS for better formatting
    st.markdown("""
        <style>
        /* Improve spacing and readability */
        .stChatMessage {
            padding: 1.5rem !important;
        }
        
        /* Better list formatting */
        .stMarkdown ul {
            margin-left: 0 !important;
            padding-left: 1.5rem !important;
        }
        
        .stMarkdown li {
            margin-bottom: 0.75rem !important;
            line-height: 1.6 !important;
        }
        
        /* Code/badge styling for sources */
        .stMarkdown code {
            background-color: #f0f2f6 !important;
            padding: 0.2rem 0.6rem !important;
            border-radius: 0.3rem !important;
            font-size: 0.9rem !important;
        }
        
        /* Horizontal rule styling */
        .stMarkdown hr {
            margin: 1.5rem 0 !important;
            border-top: 2px solid #e0e0e0 !important;
        }
        
        /* Better paragraph spacing */
        .stMarkdown p {
            margin-bottom: 1rem !important;
            line-height: 1.7 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("HR Assistant")
    st.caption("Professional HR guidance with grounded answers and clickable sources.")

    if "history" not in st.session_state:
        st.session_state["history"] = []
    if "pending_response" not in st.session_state:
        st.session_state["pending_response"] = None
    if "warm_future" not in st.session_state:
        st.session_state["warm_future"] = None

    bot = load_bot()
    executor = get_executor()

    if st.session_state["warm_future"] is None:
        st.session_state["warm_future"] = executor.submit(_warm_bot, bot)

    # Check for pending response and move to history when complete
    pending = st.session_state.get("pending_response")
    if pending:
        future = pending["future"]
        if future.done():
            try:
                answer = future.result()
                formatted = format_answer(answer)
                st.session_state.history.append({
                    "role": "assistant",
                    "content": formatted
                })
                del st.session_state.pending_response
                _rerun()
            except Exception as e:
                st.error(f"Error getting response: {e}")
                del st.session_state.pending_response
                _rerun()
        else:
            # Still processing - show adaptive spinner
            elapsed = time.time() - pending.get("start_time", time.time())
            if elapsed < 5:
                status = "Thinking through your question…"
            elif elapsed < 12:
                status = "Gathering the right policies and benefits for you…"
            elif elapsed < 20:
                status = "Double-checking sources to keep the answer accurate…"
            else:
                status = "Taking a little longer to verify every detail—thanks for your patience."
            with st.chat_message("assistant"):
                st.info(status)
            # Poll every second to check if future completed
            time.sleep(1)
            _rerun()

    for message in st.session_state["history"]:
        render_message(message["role"], message["content"])

    if prompt := st.chat_input(DEFAULT_PLACEHOLDER):
        st.session_state["history"].append({"role": "user", "content": prompt})
        render_message("user", prompt)
        future = executor.submit(query_bot, bot, prompt)
        st.session_state["pending_response"] = {"future": future, "start_time": time.time()}
        _rerun()


if __name__ == "__main__":
    main()
