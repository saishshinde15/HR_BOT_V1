"""
Professional HR Assistant - Enterprise-Grade Streamlit Application
Production-ready UI with modern design and stakeholder-ready presentation.
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

PAGE_TITLE = "HR Assistant | Enterprise Edition"
PAGE_ICON = "🏢"
DATA_DIR = Path("data").resolve()
DEFAULT_PLACEHOLDER = "Ask me anything about HR policies, benefits, leave, or procedures..."

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
# STYLING & DESIGN
# ============================================================================

PROFESSIONAL_CSS = """
<style>
    /* ==================== MODERN MINIMAL DESIGN ==================== */
    
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* ==================== MAIN CONTAINER ==================== */
    
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0 !important;
    }
    
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 1200px !important;
    }
    
    /* ==================== HEADER SECTION ==================== */
    
    .custom-header {
        background: white;
        padding: 2rem 2.5rem;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
        border: 1px solid rgba(102, 126, 234, 0.1);
    }
    
    .header-title {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1.2;
    }
    
    .header-subtitle {
        font-size: 1rem;
        color: #64748b;
        margin-top: 0.5rem;
        font-weight: 500;
    }
    
    .header-badge {
        display: inline-block;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 600;
        margin-top: 1rem;
        letter-spacing: 0.5px;
    }
    
    /* ==================== CHAT CONTAINER ==================== */
    
    .chat-container {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        min-height: 500px;
        max-height: 600px;
        overflow-y: auto;
        border: 1px solid rgba(102, 126, 234, 0.1);
        margin-bottom: 1rem;
    }
    
    /* ==================== MESSAGE BUBBLES ==================== */
    
    .stChatMessage {
        background: transparent !important;
        padding: 1rem 0 !important;
        border: none !important;
    }
    
    /* User messages - right aligned, purple */
    [data-testid="user"] {
        background: transparent !important;
    }
    
    [data-testid="user"] .stMarkdown {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.25rem 1.5rem;
        border-radius: 18px 18px 4px 18px;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
        max-width: 80%;
        margin-left: auto;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    
    /* Assistant messages - left aligned, light background */
    [data-testid="assistant"] {
        background: transparent !important;
    }
    
    [data-testid="assistant"] .stMarkdown {
        background: #f8fafc;
        color: #1e293b;
        padding: 1.5rem;
        border-radius: 18px 18px 18px 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border-left: 4px solid #667eea;
        max-width: 90%;
        font-size: 0.95rem;
        line-height: 1.8;
    }
    
    /* ==================== MESSAGE CONTENT STYLING ==================== */
    
    .stMarkdown p {
        margin-bottom: 1rem !important;
        color: inherit;
    }
    
    .stMarkdown ul, .stMarkdown ol {
        margin: 1rem 0 !important;
        padding-left: 1.5rem !important;
    }
    
    .stMarkdown li {
        margin-bottom: 0.75rem !important;
        line-height: 1.7 !important;
        color: inherit;
    }
    
    .stMarkdown strong {
        font-weight: 600;
        color: #667eea;
    }
    
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #1e293b;
        font-weight: 700;
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
    }
    
    .stMarkdown hr {
        margin: 1.5rem 0 !important;
        border: none;
        border-top: 2px solid #e2e8f0;
        opacity: 0.5;
    }
    
    .stMarkdown code {
        background: #667eea20 !important;
        color: #667eea !important;
        padding: 0.2rem 0.6rem !important;
        border-radius: 6px !important;
        font-size: 0.875rem !important;
        font-family: 'Monaco', 'Courier New', monospace !important;
        font-weight: 500 !important;
    }
    
    /* ==================== STATUS INDICATORS ==================== */
    
    .stChatMessage .stInfo {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%) !important;
        border-left: 4px solid #667eea !important;
        padding: 1.25rem !important;
        border-radius: 12px !important;
        font-size: 0.95rem !important;
        color: #475569 !important;
        animation: pulse 2s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    /* ==================== INPUT AREA ==================== */
    
    .stChatInputContainer {
        background: white;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        padding: 1rem;
        border: 2px solid transparent;
        transition: all 0.3s ease;
    }
    
    .stChatInputContainer:focus-within {
        border-color: #667eea;
        box-shadow: 0 4px 24px rgba(102, 126, 234, 0.25);
    }
    
    .stChatInput textarea {
        font-size: 0.95rem !important;
        line-height: 1.5 !important;
        color: #1e293b !important;
        border: none !important;
    }
    
    .stChatInput textarea::placeholder {
        color: #94a3b8 !important;
    }
    
    /* ==================== SCROLLBAR ==================== */
    
    .chat-container::-webkit-scrollbar {
        width: 8px;
    }
    
    .chat-container::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 10px;
    }
    
    .chat-container::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    .chat-container::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #5568d3 0%, #653a8a 100%);
    }
    
    /* ==================== FOOTER ==================== */
    
    .custom-footer {
        background: white;
        padding: 1.5rem 2rem;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-top: 1rem;
        text-align: center;
        border: 1px solid rgba(102, 126, 234, 0.1);
    }
    
    .footer-text {
        font-size: 0.875rem;
        color: #64748b;
        margin: 0;
    }
    
    .footer-badge {
        display: inline-block;
        background: #667eea15;
        color: #667eea;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-left: 0.5rem;
        letter-spacing: 0.5px;
    }
    
    /* ==================== RESPONSIVE DESIGN ==================== */
    
    @media (max-width: 768px) {
        .header-title {
            font-size: 1.5rem;
        }
        
        .custom-header {
            padding: 1.5rem;
        }
        
        [data-testid="user"] .stMarkdown,
        [data-testid="assistant"] .stMarkdown {
            max-width: 95%;
        }
    }
    
    /* ==================== ANIMATIONS ==================== */
    
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .stChatMessage {
        animation: fadeIn 0.4s ease-out;
    }
</style>
"""

# ============================================================================
# RESOURCE LOADING & CACHING
# ============================================================================


@st.cache_resource(show_spinner=False)
def load_bot() -> HrBot:
    """Instantiate the Crew only once per session."""
    return HrBot()


@st.cache_resource(show_spinner=False)
def get_executor() -> ThreadPoolExecutor:
    """Provide a shared thread pool for background inference."""
    return ThreadPoolExecutor(max_workers=2)


# ============================================================================
# CONTENT FORMATTING
# ============================================================================


def format_sources(answer: str) -> str:
    """Convert Sources line into a beautiful, professional format."""
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
                    _, _, file_name = part.partition(" ")
                    file_name = file_name.strip()
                else:
                    file_name = part.strip()

                if not file_name:
                    continue

                # Create clean display name
                display_name = (
                    file_name.replace(".docx", "")
                    .replace(".pdf", "")
                    .replace("-", " ")
                    .title()
                )
                source_items.append(f"`{display_name}`")

            if source_items:
                # Professional source section
                separator = " • ".join(source_items)
                lines[idx] = f"\n\n---\n\n**📚 Reference Documents**\n\n{separator}"
            else:
                lines[idx] = ""
            break

    return "\n".join(lines)


def format_answer(answer: str) -> str:
    """Apply professional formatting to responses."""
    answer = format_sources(answer)
    return answer


def render_message(role: str, content: str) -> None:
    """Render message with professional styling."""
    with st.chat_message(role):
        if role == "assistant":
            formatted_content = format_answer(content)
            st.markdown(formatted_content, unsafe_allow_html=False)
        else:
            st.markdown(content)


# ============================================================================
# BACKGROUND PROCESSING
# ============================================================================


def _warm_bot(bot: HrBot) -> None:
    """Preload indexes and caches for optimal performance."""
    try:
        hybrid_tool = getattr(bot, "hybrid_rag_tool", None)
        retriever = getattr(hybrid_tool, "retriever", None) if hybrid_tool else None
        if retriever:
            retriever.build_index(force_rebuild=False)
            cache_enabled = getattr(retriever, "enable_cache", True)
            if not cache_enabled:
                print(
                    "[warmup] ENABLE_CACHE is false; consider enabling it for faster responses."
                )
            # Warm up with representative queries
            for query in WARMUP_QUERIES:
                try:
                    retriever.hybrid_search(query, top_k=3)
                except Exception:
                    continue
        # Initialize crew
        bot.crew()
    except Exception:
        # Warm-up is best-effort; ignore failures
        pass


def query_bot(bot: HrBot, question: str) -> str:
    """Execute the crew and return the response."""
    result = bot.crew().kickoff(inputs={"query": question, "context": ""})
    return str(result)


def _rerun() -> None:
    """Trigger a Streamlit rerun."""
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


# ============================================================================
# MAIN APPLICATION
# ============================================================================


def main() -> None:
    """Main application entry point."""
    # Page configuration
    st.set_page_config(
        page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide", initial_sidebar_state="collapsed"
    )

    # Apply professional styling
    st.markdown(PROFESSIONAL_CSS, unsafe_allow_html=True)

    # Professional Header
    st.markdown(
        """
        <div class="custom-header">
            <h1 class="header-title">🏢 HR Assistant</h1>
            <p class="header-subtitle">Your AI-powered guide to company policies, benefits, and HR procedures</p>
            <span class="header-badge">✨ ENTERPRISE EDITION</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

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

    # Check for pending response
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
                st.error(f"An error occurred: {e}")
                del st.session_state.pending_response
                _rerun()
        else:
            # Show adaptive status
            elapsed = time.time() - pending.get("start_time", time.time())
            if elapsed < 5:
                status = "🤔 Analyzing your question..."
            elif elapsed < 12:
                status = "📚 Searching through company policies..."
            elif elapsed < 20:
                status = "✍️ Crafting a comprehensive answer..."
            else:
                status = "⏳ Finalizing the details for you..."

            with st.chat_message("assistant"):
                st.info(status)
            time.sleep(1)
            _rerun()

    # Render chat history
    for message in st.session_state["history"]:
        render_message(message["role"], message["content"])

    # Chat input
    if prompt := st.chat_input(DEFAULT_PLACEHOLDER):
        st.session_state["history"].append({"role": "user", "content": prompt})
        render_message("user", prompt)
        future = executor.submit(query_bot, bot, prompt)
        st.session_state["pending_response"] = {"future": future, "start_time": time.time()}
        _rerun()

    # Professional Footer
    st.markdown(
        """
        <div class="custom-footer">
            <p class="footer-text">
                Powered by Advanced AI • Backed by Company Policies
                <span class="footer-badge">SECURE & CONFIDENTIAL</span>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
