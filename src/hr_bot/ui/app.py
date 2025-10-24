"""
HR Assistant - Professional Enterprise UI
Clean, modern interface for HR policy assistance
"""

from __future__ import annotations

import time
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

from hr_bot.crew import HrBot

# ============================================================================
# CONFIGURATION
# ============================================================================

PAGE_TITLE = "HR Assistant"
PAGE_ICON = "💼"
DATA_DIR = Path("data").resolve()
DEFAULT_PLACEHOLDER = "Ask me anything about HR policies, benefits, or procedures..."

WARMUP_QUERIES: List[str] = [
    "What is the sick leave policy?",
    "How do I request paternity leave?",
    "What are my vacation entitlements?",
    "How do I report an absence?",
    "What health benefits are available?",
    "How do I submit an expense claim?",
    "What is the remote work policy?",
    "How do I access my payslip?",
    "What training opportunities are available?",
    "How do I refer a candidate?",
    "What is the bereavement leave policy?",
    "How do I update my personal information?",
    "What is the company dress code?",
    "How do I request flexible working?",
    "What are the probation period terms?",
    "How do I raise a grievance?",
    "What is the annual leave policy?",
    "How do I book a meeting room?",
    "What wellness programs are offered?",
    "How do I access employee assistance?",
    "What is the performance review process?",
    "How do I request parental leave?",
    "What equipment can I request?",
    "How do I change my emergency contact?",
    "What happens during a return-to-work interview?",
]

# ============================================================================
# MINIMAL PROFESSIONAL STYLING (Grok-inspired)
# ============================================================================

MINIMAL_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    
    /* ==================== GLOBAL RESET ==================== */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* ==================== DARK THEME BASE WITH SUBTLE GRADIENT ==================== */
    .main {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0f0f0f 100%) !important;
        color: #e5e5e5;
        min-height: 100vh;
    }
    
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 2rem !important;
        max-width: 900px !important;
    }
    
    /* ==================== HEADER - PROFESSIONAL WITH GRADIENT ==================== */
    h1 {
        font-size: 2rem !important;
        font-weight: 600 !important;
        background: linear-gradient(135deg, #ffffff 0%, #a0a0a0 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        margin-bottom: 0.75rem !important;
        letter-spacing: -0.03em !important;
    }
    
    /* Subtitle with better spacing */
    [data-testid="stCaptionContainer"] {
        font-size: 1rem !important;
        color: #999999 !important;
        font-weight: 300 !important;
        margin-bottom: 3rem !important;
        letter-spacing: 0.01em !important;
    }
    
    /* ==================== CHAT MESSAGES - CLEAN BUBBLES ==================== */
    .stChatMessage {
        background: transparent !important;
        padding: 0.75rem 0 !important;
        border: none !important;
    }
    
    /* User messages - subtle, right-aligned */
    [data-testid="user"] {
        display: flex;
        justify-content: flex-end;
    }
    
    [data-testid="user"] > div {
        background: #1a1a1a !important;
        border: 1px solid #2a2a2a !important;
        color: #e5e5e5 !important;
        padding: 1rem 1.25rem !important;
        border-radius: 1.25rem !important;
        max-width: 75% !important;
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
        box-shadow: none !important;
    }
    
    /* Assistant messages - clean, professional with subtle background */
    [data-testid="assistant"] {
        display: flex;
        justify-content: flex-start;
    }
    
    [data-testid="assistant"] > div {
        background: rgba(255, 255, 255, 0.02) !important;
        color: #e5e5e5 !important;
        padding: 1.5rem !important;
        border-radius: 1rem !important;
        max-width: 85% !important;
        font-size: 0.95rem !important;
        line-height: 1.7 !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15) !important;
    }
    
    /* ==================== MESSAGE CONTENT STYLING ==================== */
    .stMarkdown {
        color: #e5e5e5 !important;
    }
    
    .stMarkdown p {
        margin-bottom: 1rem !important;
        line-height: 1.7 !important;
    }
    
    .stMarkdown ul, .stMarkdown ol {
        margin: 1rem 0 !important;
        padding-left: 1.5rem !important;
    }
    
    .stMarkdown li {
        margin-bottom: 0.75rem !important;
        line-height: 1.7 !important;
    }
    
    .stMarkdown strong {
        font-weight: 600 !important;
        color: #ffffff !important;
    }
    
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #ffffff !important;
        font-weight: 600 !important;
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
    }
    
    .stMarkdown hr {
        margin: 2rem 0 !important;
        border: none !important;
        border-top: 1px solid #2a2a2a !important;
    }
    
    .stMarkdown code {
        background: #1a1a1a !important;
        color: #a8a8a8 !important;
        padding: 0.2rem 0.5rem !important;
        border-radius: 0.375rem !important;
        font-size: 0.875rem !important;
        font-family: 'SF Mono', 'Monaco', 'Courier New', monospace !important;
        border: 1px solid #2a2a2a !important;
    }
    
    /* ==================== STATUS INDICATORS - MINIMAL ==================== */
    .stChatMessage [data-testid="stInfo"] {
        background: transparent !important;
        border: none !important;
        color: #888888 !important;
        padding: 1rem 0 !important;
        font-size: 0.9rem !important;
        font-weight: 300 !important;
    }
    

    
    /* ==================== INPUT AREA - MODERN & INVITING ==================== */
    .stChatInputContainer {
        background: linear-gradient(135deg, rgba(30, 30, 30, 0.8) 0%, rgba(20, 20, 20, 0.9) 100%) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 1.5rem !important;
        padding: 0.75rem 1.25rem !important;
        transition: all 0.3s ease !important;
        backdrop-filter: blur(10px) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
    }
    
    .stChatInputContainer:focus-within {
        border-color: rgba(255, 255, 255, 0.2) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), 0 0 0 2px rgba(255, 255, 255, 0.08) !important;
        transform: translateY(-1px) !important;
    }
    
    .stChatInput textarea {
        background: transparent !important;
        color: #e5e5e5 !important;
        font-size: 0.95rem !important;
        line-height: 1.5 !important;
        border: none !important;
        caret-color: #ffffff !important;
    }
    
    .stChatInput textarea::placeholder {
        color: #777777 !important;
        font-weight: 300 !important;
    }
    
    .stChatInput textarea:focus {
        outline: none !important;
        box-shadow: none !important;
    }
    
    /* ==================== SCROLLBAR - MINIMAL ==================== */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #2a2a2a;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #3a3a3a;
    }
    
    /* ==================== LINKS ==================== */
    a {
        color: #ffffff !important;
        text-decoration: underline !important;
        text-decoration-color: #4a4a4a !important;
    }
    
    a:hover {
        text-decoration-color: #ffffff !important;
    }
    
    /* ==================== ANIMATIONS ==================== */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(8px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }
    
    @keyframes typing {
        0%, 100% {
            opacity: 0.3;
        }
        50% {
            opacity: 1;
        }
    }
    
    /* Message animations */
    .stChatMessage {
        animation: fadeIn 0.3s ease-out;
    }
    
    [data-testid="user"] {
        animation: slideInRight 0.4s ease-out;
    }
    
    [data-testid="assistant"] {
        animation: slideInLeft 0.4s ease-out;
    }
    
    /* Typing indicator animation */
    .typing-indicator {
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    .typing-dot {
        animation: typing 1.4s infinite;
    }
    
    .typing-dot:nth-child(2) {
        animation-delay: 0.2s;
    }
    
    .typing-dot:nth-child(3) {
        animation-delay: 0.4s;
    }
    
    /* ==================== RESPONSIVE ==================== */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 2rem !important;
        }
        
        h1 {
            font-size: 1.5rem !important;
        }
        
        [data-testid="user"] > div,
        [data-testid="assistant"] > div {
            max-width: 90% !important;
        }
    }
</style>
"""

# ============================================================================
# RESOURCE LOADING & CACHING
# ============================================================================


@st.cache_resource(show_spinner=False)
def load_bot() -> HrBot:
    """Load bot instance."""
    return HrBot()


@st.cache_resource(show_spinner=False)
def get_executor() -> ThreadPoolExecutor:
    """Get thread pool executor."""
    return ThreadPoolExecutor(max_workers=2)


# ============================================================================
# CONTENT FORMATTING
# ============================================================================


def format_sources(answer: str) -> str:
    """Format source citations cleanly."""
    lines = answer.splitlines()
    if not lines:
        return answer

    for idx, line in enumerate(lines):
        if line.lower().startswith("sources:"):
            parts = [p.strip() for p in line.split(":", 1)[1].split(",") if p.strip()]
            source_items: List[str] = []

            for part in parts:
                if " " in part:
                    _, _, file_name = part.partition(" ")
                    file_name = file_name.strip()
                else:
                    file_name = part.strip()

                if not file_name:
                    continue

                display_name = (
                    file_name.replace(".docx", "")
                    .replace(".pdf", "")
                    .replace("-", " ")
                    .title()
                )
                source_items.append(f"`{display_name}`")

            if source_items:
                separator = " · ".join(source_items)
                lines[idx] = f"\n\n---\n\n**Sources:** {separator}"
            else:
                lines[idx] = ""
            break

    return "\n".join(lines)


def clean_markdown_artifacts(text: str) -> str:
    """Remove markdown code block markers and other artifacts."""
    # Remove markdown code block markers
    text = text.replace("```markdown", "").replace("```", "")
    # Remove extra blank lines at start/end
    text = text.strip()
    return text


def remove_document_evidence_section(text: str) -> str:
    """CRITICAL: Remove any 'Document Evidence' section that appears after sources."""
    lines = text.splitlines()
    result_lines = []
    found_sources = False
    skip_remaining = False
    
    for line in lines:
        # Check if we hit the sources line
        if line.lower().startswith("sources:") or "**sources:**" in line.lower():
            found_sources = True
            result_lines.append(line)
            skip_remaining = True  # Skip everything after sources
            continue
        
        # If we haven't found sources yet, or we're before sources, keep the line
        if not skip_remaining:
            # Skip any line with "Document Evidence" heading
            if "document evidence" in line.lower() and ("##" in line or "**" in line):
                skip_remaining = True
                continue
            result_lines.append(line)
        # After sources, skip everything (including Document Evidence section)
    
    return "\n".join(result_lines)


def format_answer(answer: str) -> str:
    """Apply formatting and clean up artifacts."""
    answer = clean_markdown_artifacts(answer)
    answer = remove_document_evidence_section(answer)  # CRITICAL: Remove Document Evidence
    answer = format_sources(answer)
    return answer


def render_message(role: str, content: str) -> None:
    """Render chat message with clean, professional styling."""
    with st.chat_message(role):
        if role == "assistant":
            st.markdown(format_answer(content))
        else:
            st.markdown(content, unsafe_allow_html=False)


# ============================================================================
# BACKGROUND PROCESSING
# ============================================================================


def _warm_bot(bot: HrBot) -> None:
    """Warm up the bot."""
    try:
        hybrid_tool = getattr(bot, "hybrid_rag_tool", None)
        retriever = getattr(hybrid_tool, "retriever", None) if hybrid_tool else None
        if retriever:
            retriever.build_index(force_rebuild=False)
            for query in WARMUP_QUERIES:
                try:
                    retriever.hybrid_search(query, top_k=3)
                except Exception:
                    continue
        bot.crew()
    except Exception:
        pass


def build_history_context(history: List[Dict[str, str]], new_question: str | None = None, max_entries: int = 3) -> str:
    """Construct a lightweight conversation context string for the LLM."""
    user_messages: List[str] = [msg["content"] for msg in history if msg.get("role") == "user"]
    if new_question:
        user_messages.append(new_question)

    if not user_messages:
        return ""

    recent_messages = user_messages[-max_entries:]
    history_parts = []
    for idx, content in enumerate(recent_messages, 1):
        history_parts.append(f"Question {idx}: {content[:200]}")

    return "Recent conversation:\n" + "\n".join(history_parts)


def query_bot(bot: HrBot, question: str, history_context: str) -> str:
    """Query the bot with an explicit conversation history context."""
    inputs = {"query": question, "context": history_context or ""}
    result = bot.crew().kickoff(inputs=inputs)
    return str(result)


def _rerun() -> None:
    """Trigger rerun."""
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


def render_typing_indicator() -> None:
    """Render animated typing indicator."""
    typing_html = """
    <div style="display: flex; align-items: center; gap: 0.5rem; padding: 1rem 0;">
        <div style="display: flex; gap: 0.3rem;">
            <div class="typing-dot" style="width: 8px; height: 8px; background: #888888; border-radius: 50%;"></div>
            <div class="typing-dot" style="width: 8px; height: 8px; background: #888888; border-radius: 50%;"></div>
            <div class="typing-dot" style="width: 8px; height: 8px; background: #888888; border-radius: 50%;"></div>
        </div>
        <span style="color: #888888; font-size: 0.9rem; font-weight: 300; margin-left: 0.5rem;">Thinking...</span>
    </div>
    """
    st.markdown(typing_html, unsafe_allow_html=True)


# ============================================================================
# MAIN APPLICATION
# ============================================================================


def main() -> None:
    """Main application."""
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Apply professional styling
    st.markdown(MINIMAL_CSS, unsafe_allow_html=True)

    # Professional header with emoji and description
    st.title("💼 HR Assistant")
    st.caption("Your trusted companion for HR policies, benefits, and workplace guidance. Ask me anything!")
    
    # Add a subtle welcome message for first-time users
    if len(st.session_state.get("history", [])) == 0:
        st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); 
                    border-radius: 1rem; padding: 1.5rem; margin: 2rem 0; text-align: center;">
            <div style="font-size: 1.1rem; color: #ffffff; font-weight: 500; margin-bottom: 0.75rem;">
                👋 Welcome! How can I help you today?
            </div>
            <div style="font-size: 0.9rem; color: #999999; line-height: 1.6;">
                I can answer questions about company policies, leave requests, benefits, procedures, and more.<br/>
                Try asking: <span style="color: #cccccc;">"What is the sick leave policy?"</span> or 
                <span style="color: #cccccc;">"How do I request vacation?"</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Initialize session state
    if "history" not in st.session_state:
        st.session_state["history"] = []
    if "pending_response" not in st.session_state:
        st.session_state["pending_response"] = None
    if "warm_future" not in st.session_state:
        st.session_state["warm_future"] = None

    # Load resources
    bot = load_bot()
    executor = get_executor()

    # Background warmup
    if st.session_state["warm_future"] is None:
        st.session_state["warm_future"] = executor.submit(_warm_bot, bot)

    # Render chat history
    for message in st.session_state["history"]:
        render_message(message["role"], message["content"])

    # Check pending response and show status
    pending = st.session_state.get("pending_response")
    if pending:
        future = pending["future"]
        if future.done():
            try:
                answer = future.result()
                formatted = format_answer(answer)
                st.session_state.history.append({"role": "assistant", "content": formatted})
                del st.session_state.pending_response
                _rerun()
            except Exception as e:
                st.error(f"Error: {e}")
                del st.session_state.pending_response
                _rerun()
        else:
            # Show animated typing indicator while processing
            elapsed = time.time() - pending.get("start_time", time.time())
            if elapsed < 8:
                status = "Thinking..."
            elif elapsed < 15:
                status = "Searching policies..."
            else:
                status = "Crafting response..."

            with st.chat_message("assistant"):
                typing_html = f"""
                <div style="display: flex; align-items: center; gap: 0.5rem; padding: 1rem 0;">
                    <div style="display: flex; gap: 0.3rem;">
                        <div class="typing-dot" style="width: 8px; height: 8px; background: #888888; border-radius: 50%;"></div>
                        <div class="typing-dot" style="width: 8px; height: 8px; background: #888888; border-radius: 50%;"></div>
                        <div class="typing-dot" style="width: 8px; height: 8px; background: #888888; border-radius: 50%;"></div>
                    </div>
                    <span style="color: #888888; font-size: 0.9rem; font-weight: 300; margin-left: 0.5rem;">{status}</span>
                </div>
                """
                st.markdown(typing_html, unsafe_allow_html=True)
            time.sleep(1)
            _rerun()

    # Chat input - DON'T render immediately, just add to history
    if prompt := st.chat_input(DEFAULT_PLACEHOLDER):
        history_context = build_history_context(st.session_state["history"], prompt)
        # Add to history (will be rendered on next rerun)
        st.session_state["history"].append({"role": "user", "content": prompt})
        # Start processing
        future = executor.submit(query_bot, bot, prompt, history_context)
        st.session_state["pending_response"] = {"future": future, "start_time": time.time()}
        _rerun()


if __name__ == "__main__":
    main()
