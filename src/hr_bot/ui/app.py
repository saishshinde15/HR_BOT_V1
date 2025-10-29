"""
HR Assistant - Professional Enterprise UI
Clean, modern interface for HR policy assistance
"""

from __future__ import annotations

import time
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List

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
# MINIMAL PROFESSIONAL STYLING 
# ============================================================================

MINIMAL_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* ==================== THEME TOGGLE BUTTON - ELEGANT & FIXED ==================== */
    .theme-toggle-container {
        position: fixed;
        top: 1.5rem;
        right: 2rem;
        z-index: 9999;
        animation: fadeIn 0.6s ease-out 0.4s both;
    }
    
    .theme-toggle {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        background: linear-gradient(135deg, rgba(120, 119, 198, 0.15) 0%, rgba(155, 143, 217, 0.1) 100%);
        border: 1.5px solid rgba(120, 119, 198, 0.4);
        backdrop-filter: blur(12px);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 16px rgba(120, 119, 198, 0.15), 0 2px 4px rgba(0, 0, 0, 0.1);
        padding: 0;
        outline: none;
    }
    
    .theme-toggle:hover {
        transform: translateY(-2px) scale(1.05);
        border-color: rgba(120, 119, 198, 0.6);
        background: linear-gradient(135deg, rgba(120, 119, 198, 0.25) 0%, rgba(155, 143, 217, 0.2) 100%);
        box-shadow: 0 8px 28px rgba(120, 119, 198, 0.3), 0 4px 8px rgba(0, 0, 0, 0.15);
    }
    
    .theme-toggle:active {
        transform: translateY(0) scale(0.98);
    }
    
    .theme-toggle span {
        font-size: 22px;
        filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
        transition: all 0.3s ease;
    }
    
    .light-theme .theme-toggle {
        background: linear-gradient(135deg, rgba(120, 119, 198, 0.12) 0%, rgba(155, 143, 217, 0.08) 100%);
        border: 1.5px solid rgba(120, 119, 198, 0.3);
        box-shadow: 0 4px 16px rgba(120, 119, 198, 0.12), 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .light-theme .theme-toggle:hover {
        background: linear-gradient(135deg, rgba(120, 119, 198, 0.2) 0%, rgba(155, 143, 217, 0.15) 100%);
        box-shadow: 0 8px 28px rgba(120, 119, 198, 0.2), 0 4px 8px rgba(0, 0, 0, 0.08);
    }
    
    /* ==================== FEEDBACK BUTTONS - ELEGANT DESIGN ==================== */
    .assistant-message-container {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    .assistant-content {
        color: var(--text-primary);
        line-height: 1.7;
    }
    
    .user-message {
        background: linear-gradient(135deg, rgba(120, 119, 198, 0.15) 0%, rgba(155, 143, 217, 0.1) 100%);
        border: 1px solid rgba(120, 119, 198, 0.25);
        border-radius: 16px;
        padding: 1.25rem 1.5rem;
        margin: 1rem 0;
        color: var(--text-primary);
    }
    
    .feedback-container {
        display: flex !important;
        gap: 0.75rem;
        margin-top: 1.5rem;
        padding-top: 1.25rem;
        border-top: 1px solid rgba(120, 119, 198, 0.15);
        align-items: center;
    }
    
    .feedback-label {
        font-size: 0.875rem;
        color: #b8b8b8 !important;
        font-weight: 400;
        margin-right: 0.25rem;
    }
    
    .feedback-btn {
        width: 38px !important;
        height: 38px !important;
        border-radius: 10px !important;
        background: linear-gradient(135deg, rgba(26, 26, 46, 0.4) 0%, rgba(15, 15, 30, 0.5) 100%) !important;
        border: 1px solid rgba(120, 119, 198, 0.2) !important;
        cursor: pointer !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        backdrop-filter: blur(8px);
    }
    
    .feedback-btn:hover {
        transform: translateY(-2px) scale(1.08);
        border-color: rgba(120, 119, 198, 0.4);
        box-shadow: 0 4px 12px rgba(120, 119, 198, 0.15);
    }
    
    .feedback-btn:active {
        transform: translateY(0) scale(0.95);
    }
    
    .feedback-btn.thumbs-up:hover {
        background: linear-gradient(135deg, rgba(76, 175, 80, 0.15) 0%, rgba(56, 142, 60, 0.2) 100%);
        border-color: rgba(76, 175, 80, 0.4);
    }
    
    .feedback-btn.thumbs-down:hover {
        background: linear-gradient(135deg, rgba(244, 67, 54, 0.15) 0%, rgba(211, 47, 47, 0.2) 100%);
        border-color: rgba(244, 67, 54, 0.4);
    }
    
    /* Radio-based selection (JS-free, reliable) */
    .fb-radio { display: none; }

    .fb-radio:checked + label.feedback-btn {
        transform: scale(1.15) !important;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
        box-shadow: 0 8px 24px rgba(120, 119, 198, 0.25);
    }

    .fb-radio:checked + label.thumbs-up {
        background: linear-gradient(135deg, rgba(76, 175, 80, 0.5) 0%, rgba(56, 142, 60, 0.6) 100%) !important;
        border-color: rgba(76, 175, 80, 0.9) !important;
        box-shadow: 0 0 30px rgba(76, 175, 80, 0.7), 0 8px 25px rgba(0, 0, 0, 0.3) !important;
    }

    .fb-radio:checked + label.thumbs-up svg path {
        stroke: #66BB6A !important;
        opacity: 1 !important;
        stroke-width: 3 !important;
        filter: drop-shadow(0 0 10px rgba(76, 175, 80, 1));
    }

    .fb-radio:checked + label.thumbs-down {
        background: linear-gradient(135deg, rgba(244, 67, 54, 0.5) 0%, rgba(211, 47, 47, 0.6) 100%) !important;
        border-color: rgba(244, 67, 54, 0.9) !important;
        box-shadow: 0 0 30px rgba(244, 67, 54, 0.7), 0 8px 25px rgba(0, 0, 0, 0.3) !important;
    }

    .fb-radio:checked + label.thumbs-down svg path {
        stroke: #EF5350 !important;
        opacity: 1 !important;
        stroke-width: 3 !important;
        filter: drop-shadow(0 0 10px rgba(244, 67, 54, 1));
    }

    .feedback-btn.selected {
        transform: scale(1.15) !important;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    }
    
    .feedback-btn.thumbs-up.selected {
        background: linear-gradient(135deg, rgba(76, 175, 80, 0.5) 0%, rgba(56, 142, 60, 0.6) 100%) !important;
        border-color: rgba(76, 175, 80, 0.9) !important;
        box-shadow: 0 0 30px rgba(76, 175, 80, 0.7), 0 8px 25px rgba(0, 0, 0, 0.3) !important;
    }
    
    .feedback-btn.thumbs-up.selected svg path {
        stroke: #66BB6A !important;
        opacity: 1 !important;
        stroke-width: 3 !important;
        filter: drop-shadow(0 0 10px rgba(76, 175, 80, 1));
    }
    
    .feedback-btn.thumbs-down.selected {
        background: linear-gradient(135deg, rgba(244, 67, 54, 0.5) 0%, rgba(211, 47, 47, 0.6) 100%) !important;
        border-color: rgba(244, 67, 54, 0.9) !important;
        box-shadow: 0 0 30px rgba(244, 67, 54, 0.7), 0 8px 25px rgba(0, 0, 0, 0.3) !important;
    }
    
    .feedback-btn.thumbs-down.selected svg path {
        stroke: #EF5350 !important;
        opacity: 1 !important;
        stroke-width: 3 !important;
        filter: drop-shadow(0 0 10px rgba(244, 67, 54, 1));
    }
    
    .feedback-btn svg {
        transition: all 0.3s ease;
    }
    
    .feedback-btn:hover svg {
        transform: scale(1.15);
    }
    
    /* Light theme feedback buttons */
    .light-theme .feedback-btn {
        background: linear-gradient(135deg, rgba(248, 249, 250, 0.8) 0%, rgba(233, 236, 239, 0.9) 100%);
        border: 1px solid rgba(120, 119, 198, 0.15);
    }
    
    .light-theme .feedback-btn:hover {
        box-shadow: 0 4px 12px rgba(120, 119, 198, 0.1);
    }
    
    .light-theme .feedback-label {
        color: #6c757d;
    }
    
    @keyframes feedbackPulse {
        0% {
            transform: scale(1);
        }
        30% {
            transform: scale(1.2);
        }
        50% {
            transform: scale(1.15);
        }
        70% {
            transform: scale(1.18);
        }
        100% {
            transform: scale(1.05);
        }
    }
    
    /* ==================== GLOBAL RESET ==================== */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Remove edit buttons completely */
    button[title="Copy message"],
    button[title="Copy"],
    button[aria-label*="Copy"],
    [data-testid="stChatMessageCopyButton"],
    .stChatMessage button {
        display: none !important;
    }
    
    /* ==================== THEME VARIABLES ==================== */
    :root {
        --bg-gradient-start: #1a1a2e;
        --bg-gradient-mid: #0f0f1e;
        --bg-gradient-end: #000000;
        --text-primary: #e5e5e5;
        --text-secondary: #a0a0a0;
        --card-bg: rgba(26, 26, 46, 0.95);
        --card-border: rgba(120, 119, 198, 0.2);
        --accent-color: rgba(120, 119, 198, 0.5);
    }
    
    .light-theme {
        --bg-gradient-start: #f8f9fa;
        --bg-gradient-mid: #e9ecef;
        --bg-gradient-end: #dee2e6;
        --text-primary: #212529;
        --text-secondary: #6c757d;
        --card-bg: rgba(255, 255, 255, 0.95);
        --card-border: rgba(120, 119, 198, 0.15);
        --accent-color: rgba(120, 119, 198, 0.7);
    }
    
    /* ==================== DARK THEME BASE WITH RICH GRADIENT ==================== */
    .main {
        background: radial-gradient(ellipse at top, var(--bg-gradient-start) 0%, var(--bg-gradient-mid) 50%, var(--bg-gradient-end) 100%) !important;
        color: var(--text-primary);
        min-height: 100vh;
        position: relative;
        transition: background 0.4s ease, color 0.4s ease;
    }
    
    /* Subtle animated background effect */
    .main::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: 
            radial-gradient(ellipse at 20% 30%, rgba(120, 119, 198, 0.05) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 70%, rgba(255, 107, 107, 0.03) 0%, transparent 50%);
        pointer-events: none;
        z-index: 0;
    }
    
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 2rem !important;
        max-width: 900px !important;
        position: relative;
        z-index: 1;
    }
    
    /* ==================== HEADER - STUNNING GRADIENT TITLE ==================== */
    h1 {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, #ffffff 0%, #a8a8ff 50%, #7877c6 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        margin-bottom: 0.5rem !important;
        letter-spacing: -0.04em !important;
        animation: fadeInDown 0.6s ease-out;
    }
    
    /* Subtitle with elegant styling */
    [data-testid="stCaptionContainer"] {
        font-size: 1.05rem !important;
        color: #a0a0a0 !important;
        font-weight: 400 !important;
        margin-bottom: 2.5rem !important;
        letter-spacing: 0.02em !important;
        animation: fadeIn 0.8s ease-out 0.2s both;
    }
    
    /* ==================== CHAT MESSAGES - ELEGANT BUBBLES WITH DEPTH ==================== */
    .stChatMessage {
        background: transparent !important;
        padding: 1rem 0 !important;
        border: none !important;
        margin: 0.5rem 0 !important;
    }
    
    /* User messages - sleek, right-aligned with subtle glow */
    [data-testid="user"] {
        display: flex;
        justify-content: flex-end;
    }
    
    [data-testid="user"] > div {
        background: linear-gradient(135deg, rgba(120, 119, 198, 0.15) 0%, rgba(120, 119, 198, 0.08) 100%) !important;
        border: 1px solid rgba(120, 119, 198, 0.25) !important;
        color: #e8e8e8 !important;
        padding: 1.1rem 1.5rem !important;
        border-radius: 1.5rem 1.5rem 0.5rem 1.5rem !important;
        max-width: 75% !important;
        font-size: 0.975rem !important;
        line-height: 1.65 !important;
        box-shadow: 0 4px 12px rgba(120, 119, 198, 0.08), 0 2px 4px rgba(0, 0, 0, 0.15) !important;
        backdrop-filter: blur(8px) !important;
        transition: all 0.3s ease !important;
    }
    
    [data-testid="user"] > div:hover {
        border-color: rgba(120, 119, 198, 0.35) !important;
        box-shadow: 0 6px 16px rgba(120, 119, 198, 0.12), 0 3px 6px rgba(0, 0, 0, 0.2) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Assistant messages - premium card design with gradient border */
    [data-testid="assistant"] {
        display: flex;
        justify-content: flex-start;
    }
    
    [data-testid="assistant"] > div {
        background: linear-gradient(135deg, var(--card-bg) 0%, var(--card-bg) 100%) !important;
        color: var(--text-primary) !important;
        padding: 2rem !important;
        border-radius: 1.5rem !important;
        max-width: 90% !important;
        font-size: 0.975rem !important;
        line-height: 1.75 !important;
        border: 1px solid var(--card-border) !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25), 0 2px 8px rgba(0, 0, 0, 0.15) !important;
        position: relative !important;
        overflow: hidden !important;
        backdrop-filter: blur(12px) !important;
        transition: all 0.3s ease !important;
    }
    
    /* Light theme adjustments for assistant messages */
    .light-theme [data-testid="assistant"] > div {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.04) !important;
    }
    
    .light-theme [data-testid="assistant"] > div:hover {
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1), 0 3px 6px rgba(0, 0, 0, 0.06) !important;
    }
    
    /* Subtle gradient overlay on assistant messages */
    [data-testid="assistant"] > div::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(120, 119, 198, 0.5), transparent);
        opacity: 0.6;
    }
    
    [data-testid="assistant"] > div:hover {
        border-color: rgba(255, 255, 255, 0.12) !important;
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.3), 0 4px 12px rgba(0, 0, 0, 0.2) !important;
        transform: translateY(-2px) !important;
    }
    
    /* ==================== MESSAGE CONTENT STYLING - ENHANCED TYPOGRAPHY ==================== */
    .stMarkdown {
        color: #e8e8e8 !important;
    }
    
    .stMarkdown p {
        margin-bottom: 1.25rem !important;
        line-height: 1.8 !important;
        color: #e0e0e0 !important;
    }
    
    .stMarkdown ul, .stMarkdown ol {
        margin: 1.25rem 0 !important;
        padding-left: 1.75rem !important;
    }
    
    .stMarkdown li {
        margin-bottom: 0.85rem !important;
        line-height: 1.75 !important;
        color: #d8d8d8 !important;
    }
    
    .stMarkdown strong {
        font-weight: 600 !important;
        color: #ffffff !important;
        text-shadow: 0 0 20px rgba(255, 255, 255, 0.15) !important;
    }
    
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #ffffff !important;
        font-weight: 600 !important;
        margin-top: 2rem !important;
        margin-bottom: 1.25rem !important;
        letter-spacing: -0.02em !important;
    }
    
    .stMarkdown h2 {
        font-size: 1.4rem !important;
        background: linear-gradient(135deg, #ffffff 0%, #c8c8c8 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
    }
    
    .stMarkdown h3 {
        font-size: 1.15rem !important;
        color: #f0f0f0 !important;
    }
    
    .stMarkdown hr {
        margin: 2.5rem 0 !important;
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.15), transparent) !important;
    }
    
    .stMarkdown code {
        background: rgba(20, 20, 35, 0.8) !important;
        color: #b8b8d8 !important;
        padding: 0.25rem 0.6rem !important;
        border-radius: 0.5rem !important;
        font-size: 0.9rem !important;
        font-family: 'SF Mono', 'Monaco', 'Courier New', monospace !important;
        border: 1px solid rgba(120, 119, 198, 0.2) !important;
        font-weight: 500 !important;
    }
    
    /* Enhanced blockquote styling */
    .stMarkdown blockquote {
        border-left: 3px solid rgba(120, 119, 198, 0.5) !important;
        padding-left: 1.5rem !important;
        margin: 1.5rem 0 !important;
        color: #c0c0c0 !important;
        font-style: italic !important;
        background: rgba(120, 119, 198, 0.03) !important;
        padding: 1rem 1.5rem !important;
        border-radius: 0.5rem !important;
    }
    
    /* ==================== STATUS INDICATORS - REFINED ==================== */
    .stChatMessage [data-testid="stInfo"] {
        background: rgba(120, 119, 198, 0.08) !important;
        border: 1px solid rgba(120, 119, 198, 0.15) !important;
        border-radius: 0.75rem !important;
        color: #a8a8a8 !important;
        padding: 1rem 1.25rem !important;
        font-size: 0.925rem !important;
        font-weight: 400 !important;
        backdrop-filter: blur(8px) !important;
    }
    

    
    /* ==================== INPUT AREA - PREMIUM GLASS MORPHISM ==================== */
    .stChatInputContainer {
        background: linear-gradient(135deg, rgba(35, 35, 60, 0.85) 0%, rgba(25, 25, 45, 0.9) 100%) !important;
        border: 1px solid rgba(120, 119, 198, 0.25) !important;
        border-radius: 1.75rem !important;
        padding: 0.85rem 1.5rem !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        backdrop-filter: blur(16px) !important;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.3),
            0 2px 8px rgba(0, 0, 0, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
        position: relative !important;
    }
    
    /* Glow effect on focus */
    .stChatInputContainer::before {
        content: '';
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        background: linear-gradient(135deg, rgba(120, 119, 198, 0.4), rgba(255, 107, 107, 0.2));
        border-radius: 1.85rem;
        opacity: 0;
        transition: opacity 0.4s ease;
        z-index: -1;
    }
    
    .stChatInputContainer:focus-within::before {
        opacity: 1;
    }
    
    .stChatInputContainer:focus-within {
        border-color: rgba(120, 119, 198, 0.45) !important;
        box-shadow: 
            0 12px 48px rgba(120, 119, 198, 0.15),
            0 4px 16px rgba(0, 0, 0, 0.25),
            inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
        transform: translateY(-2px) scale(1.005) !important;
    }
    
    .stChatInput textarea {
        background: transparent !important;
        color: #f0f0f0 !important;
        font-size: 0.975rem !important;
        line-height: 1.6 !important;
        border: none !important;
        caret-color: rgba(120, 119, 198, 0.8) !important;
        font-weight: 400 !important;
    }
    
    .stChatInput textarea::placeholder {
        color: #888888 !important;
        font-weight: 400 !important;
        opacity: 0.8 !important;
    }
    
    .stChatInput textarea:focus {
        outline: none !important;
        box-shadow: none !important;
    }
    
    /* Send button enhancement (if visible) */
    .stChatInputContainer button {
        background: linear-gradient(135deg, rgba(120, 119, 198, 0.2), rgba(120, 119, 198, 0.3)) !important;
        border: 1px solid rgba(120, 119, 198, 0.4) !important;
        border-radius: 0.75rem !important;
        color: #ffffff !important;
        transition: all 0.3s ease !important;
    }
    
    .stChatInputContainer button:hover {
        background: linear-gradient(135deg, rgba(120, 119, 198, 0.35), rgba(120, 119, 198, 0.45)) !important;
        border-color: rgba(120, 119, 198, 0.6) !important;
        transform: scale(1.05) !important;
    }
    
    /* ==================== SCROLLBAR - SLEEK & MODERN ==================== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(0, 0, 0, 0.2);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, rgba(120, 119, 198, 0.4), rgba(120, 119, 198, 0.6));
        border-radius: 10px;
        border: 2px solid transparent;
        background-clip: padding-box;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, rgba(120, 119, 198, 0.6), rgba(120, 119, 198, 0.8));
    }
    
    /* ==================== LINKS - ELEGANT UNDERLINE ==================== */
    a {
        color: rgba(168, 168, 255, 0.95) !important;
        text-decoration: none !important;
        border-bottom: 1px solid rgba(168, 168, 255, 0.3) !important;
        transition: all 0.25s ease !important;
        padding-bottom: 1px !important;
    }
    
    a:hover {
        color: rgba(200, 200, 255, 1) !important;
        border-bottom-color: rgba(168, 168, 255, 0.8) !important;
        text-shadow: 0 0 8px rgba(168, 168, 255, 0.3) !important;
    }
    
    /* ==================== ANIMATIONS - SMOOTH & SOPHISTICATED ==================== */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(12px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(30px) scale(0.95);
        }
        to {
            opacity: 1;
            transform: translateX(0) scale(1);
        }
    }
    
    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-30px) scale(0.95);
        }
        to {
            opacity: 1;
            transform: translateX(0) scale(1);
        }
    }
    
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.4;
        }
    }
    
    @keyframes typing {
        0%, 100% {
            opacity: 0.25;
            transform: scale(0.9);
        }
        50% {
            opacity: 1;
            transform: scale(1.1);
        }
    }
    
    @keyframes shimmer {
        0% {
            background-position: -1000px 0;
        }
        100% {
            background-position: 1000px 0;
        }
    }
    
    /* Message animations with stagger effect */
    .stChatMessage {
        animation: fadeIn 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    [data-testid="user"] {
        animation: slideInRight 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    
    [data-testid="assistant"] {
        animation: slideInLeft 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    
    /* Typing indicator with elegant animation */
    .typing-indicator {
        animation: pulse 1.8s ease-in-out infinite;
    }
    
    .typing-dot {
        animation: typing 1.6s infinite ease-in-out;
        display: inline-block;
    }
    
    .typing-dot:nth-child(2) {
        animation-delay: 0.2s;
    }
    
    .typing-dot:nth-child(3) {
        animation-delay: 0.4s;
    }
    
    /* ==================== RESPONSIVE DESIGN - MOBILE OPTIMIZED ==================== */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 1.5rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        
        h1 {
            font-size: 1.75rem !important;
        }
        
        [data-testid="stCaptionContainer"] {
            font-size: 0.925rem !important;
        }
        
        [data-testid="user"] > div,
        [data-testid="assistant"] > div {
            max-width: 95% !important;
            padding: 1rem 1.25rem !important;
        }
        
        [data-testid="assistant"] > div {
            padding: 1.5rem !important;
        }
    }
    
    /* ==================== WELCOME CARD STYLING ==================== */
    .welcome-card {
        background: linear-gradient(135deg, rgba(26, 26, 46, 0.6) 0%, rgba(15, 15, 30, 0.8) 100%) !important;
        border: 1px solid rgba(120, 119, 198, 0.2) !important;
        border-radius: 1.5rem !important;
        padding: 2rem !important;
        margin: 2rem 0 !important;
        text-align: center !important;
        backdrop-filter: blur(12px) !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2) !important;
        animation: fadeIn 0.8s ease-out 0.4s both !important;
    }
    
    .welcome-card:hover {
        border-color: rgba(120, 119, 198, 0.35) !important;
        box-shadow: 0 12px 48px rgba(120, 119, 198, 0.15) !important;
        transform: translateY(-2px) !important;
        transition: all 0.4s ease !important;
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


def render_message(role: str, content: str, message_id: int | None = None) -> None:
    """Render chat message with clean, professional styling and feedback buttons."""
    if role == "assistant":
        # Use st.html() for feedback controls to force pure HTML rendering
        st.markdown(
            f"""
            <div class="assistant-message-container">
                <div class="assistant-content">
                    {format_answer(content)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.html(f"""
            <style>
                .feedback-container {{
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                    padding: 0.75rem 0;
                    margin-top: 0.5rem;
                }}
                .feedback-label {{
                    font-size: 0.875rem;
                    color: #b8b8b8;
                    font-weight: 400;
                    margin-right: 0.25rem;
                }}
                .fb-radio {{ display: none; }}
                .feedback-btn {{
                    width: 38px;
                    height: 38px;
                    border-radius: 10px;
                    background: linear-gradient(135deg, rgba(26, 26, 46, 0.4) 0%, rgba(15, 15, 30, 0.5) 100%);
                    border: 1px solid rgba(120, 119, 198, 0.2);
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    font-size: 20px;
                }}
                .feedback-btn:hover {{
                    transform: translateY(-2px) scale(1.08);
                    border-color: rgba(120, 119, 198, 0.4);
                    box-shadow: 0 4px 12px rgba(120, 119, 198, 0.15);
                }}
                .fb-radio:checked + .feedback-btn {{
                    transform: scale(1.15);
                    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
                }}
                .fb-radio:checked + .thumbs-up {{
                    background: linear-gradient(135deg, rgba(76, 175, 80, 0.5) 0%, rgba(56, 142, 60, 0.6) 100%);
                    border-color: rgba(76, 175, 80, 0.9);
                    box-shadow: 0 0 30px rgba(76, 175, 80, 0.7), 0 8px 25px rgba(0, 0, 0, 0.3);
                }}
                .fb-radio:checked + .thumbs-down {{
                    background: linear-gradient(135deg, rgba(244, 67, 54, 0.5) 0%, rgba(211, 47, 47, 0.6) 100%);
                    border-color: rgba(244, 67, 54, 0.9);
                    box-shadow: 0 0 30px rgba(244, 67, 54, 0.7), 0 8px 25px rgba(0, 0, 0, 0.3);
                }}
            </style>
            <div class="feedback-container">
                <span class="feedback-label">Was this helpful?</span>

                <input type="radio" name="fb-{message_id}" id="fb-{message_id}-up" class="fb-radio" />
                <label for="fb-{message_id}-up" class="feedback-btn thumbs-up" title="Helpful">👍</label>

                <input type="radio" name="fb-{message_id}" id="fb-{message_id}-down" class="fb-radio" />
                <label for="fb-{message_id}-down" class="feedback-btn thumbs-down" title="Not helpful">👎</label>
            </div>
        """)
    else:
        st.markdown(f'<div class="user-message">{content}</div>', unsafe_allow_html=True)


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
    """
    Query the bot with caching for ultra-fast responses.
    Uses the new query_with_cache method for automatic caching.
    """
    # Use the cached query method instead of direct crew kickoff
    return bot.query_with_cache(query=question, context=history_context or "")


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

    # Inject simple, reliable feedback interaction
    st.markdown(
        """
        <script>
        (function () {
            if (window.__hrbotFeedbackInitialized) {
                return;
            }
            window.__hrbotFeedbackInitialized = true;

            document.addEventListener('click', (event) => {
                const button = event.target.closest('.feedback-btn');
                if (!button) {
                    return;
                }

                const container = button.closest('.feedback-container');
                if (container) {
                    // Remove selection from all buttons in this container
                    container.querySelectorAll('.feedback-btn').forEach((btn) => {
                        btn.classList.remove('selected');
                    });
                }

                // Add selected class - CSS will handle the visual effect
                button.classList.add('selected');

                const messageId = button.getAttribute('data-message-id');
                const sentiment = button.getAttribute('data-feedback');
                console.log(`✅ Feedback recorded: message ${messageId} = ${sentiment}`);
            });
            
            console.log('🎨 Feedback system ready');
        })();
        </script>
        """,
        unsafe_allow_html=True,
    )

    # Professional header with enhanced styling and visible logo
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem;">
        <div style="
            width: 56px; 
            height: 56px; 
            background: linear-gradient(135deg, #7877c6 0%, #9b8fd9 100%);
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px rgba(120, 119, 198, 0.3);
        ">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 6H12L10 4H4C2.9 4 2 4.9 2 6V18C2 19.1 2.9 20 4 20H20C21.1 20 22 19.1 22 18V8C22 6.9 21.1 6 20 6Z" fill="white" opacity="0.9"/>
                <path d="M12 9C10.34 9 9 10.34 9 12C9 13.66 10.34 15 12 15C13.66 15 15 13.66 15 12C15 10.34 13.66 9 12 9Z" fill="white"/>
            </svg>
        </div>
        <div>
            <h1 style="margin: 0 !important; padding: 0 !important;">HR Assistant</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Your intelligent companion for HR policies, benefits, and workplace guidance — available 24/7")
    
    # Enhanced welcome message for first-time users
    if len(st.session_state.get("history", [])) == 0:
        st.markdown("""
        <div class="welcome-card">
            <div style="font-size: 2.5rem; margin-bottom: 1rem;">👋</div>
            <div style="font-size: 1.2rem; color: #ffffff; font-weight: 600; margin-bottom: 1rem;">
                Welcome! How can I assist you today?
            </div>
            <div style="font-size: 0.975rem; color: #b8b8b8; line-height: 1.7; max-width: 600px; margin: 0 auto;">
                I'm here to help with company policies, leave requests, benefits, procedures, and more.<br/>
                <span style="margin-top: 1rem; display: inline-block;">
                    Try asking: <span style="color: #d8d8d8; font-weight: 500;">"What is the sick leave policy?"</span><br/>
                    or <span style="color: #d8d8d8; font-weight: 500;">"How do I request vacation time?"</span>
                </span>
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
    for idx, message in enumerate(st.session_state["history"]):
        render_message(message["role"], message["content"], message_id=idx)

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
            # Show professional animated thinking indicator while processing
            elapsed = time.time() - pending.get("start_time", time.time())
            if elapsed < 8:
                status = "Analyzing your request..."
                progress_width = "25%"
            elif elapsed < 15:
                status = "Searching policy documents..."
                progress_width = "60%"
            else:
                status = "Preparing your response..."
                progress_width = "85%"

            with st.chat_message("assistant"):
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, rgba(26, 26, 46, 0.95) 0%, rgba(15, 15, 30, 0.98) 100%); border: 1px solid rgba(120, 119, 198, 0.2); border-radius: 16px; padding: 2rem; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);">
                    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                        <div style="width: 40px; height: 40px; background: linear-gradient(135deg, #7877c6 0%, #9b8fd9 100%); border-radius: 10px; display: flex; align-items: center; justify-content: center; animation: pulse 2s ease-in-out infinite; box-shadow: 0 4px 12px rgba(120, 119, 198, 0.4);">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <circle cx="12" cy="12" r="10" stroke="white" stroke-width="2" fill="none" opacity="0.8"/>
                                <path d="M12 6v6l4 2" stroke="white" stroke-width="2" stroke-linecap="round" opacity="0.9"/>
                            </svg>
                        </div>
                        <div style="flex: 1;">
                            <div style="color: #e8e8e8; font-size: 1rem; font-weight: 500; margin-bottom: 0.5rem;">
                                {status}
                            </div>
                            <div style="width: 100%; height: 4px; background: rgba(255, 255, 255, 0.1); border-radius: 2px; overflow: hidden;">
                                <div style="width: {progress_width}; height: 100%; background: linear-gradient(90deg, #7877c6 0%, #9b8fd9 100%); border-radius: 2px; transition: width 0.3s ease; box-shadow: 0 0 10px rgba(120, 119, 198, 0.5);"></div>
                            </div>
                        </div>
                    </div>
                    <div style="display: flex; gap: 0.4rem; justify-content: center;">
                        <div class="typing-dot" style="width: 8px; height: 8px; background: rgba(120, 119, 198, 0.6); border-radius: 50%;"></div>
                        <div class="typing-dot" style="width: 8px; height: 8px; background: rgba(120, 119, 198, 0.6); border-radius: 50%;"></div>
                        <div class="typing-dot" style="width: 8px; height: 8px; background: rgba(120, 119, 198, 0.6); border-radius: 50%;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
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
