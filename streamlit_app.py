import streamlit as st
import os

# DEBUG — remove after fixing
st.write("GEMINI key:", st.secrets.get("GEMINI_API_KEY", "NOT FOUND"))
st.write("MONDAY key:", st.secrets.get("MONDAY_API_KEY", "NOT FOUND"))
st.stop()  # stops app here so nothing else runs

import streamlit as st
from app.agents.bi_agent import run_agent

# ─────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────

st.set_page_config(
    page_title="Monday BI Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

* { font-family: 'DM Sans', sans-serif; }

/* Dark background */
.stApp {
    background-color: #0d0d0d;
    color: #e8e8e8;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #111111;
    border-right: 1px solid #1e1e1e;
}

/* Hide default streamlit elements */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* Chat messages */
.user-bubble {
    background: #1a1a2e;
    border: 1px solid #2a2a4a;
    border-radius: 12px 12px 2px 12px;
    padding: 14px 18px;
    margin: 8px 0;
    margin-left: 15%;
    color: #c8c8ff;
    font-size: 0.95rem;
    line-height: 1.6;
}

.assistant-bubble {
    background: #111111;
    border: 1px solid #1e1e1e;
    border-radius: 2px 12px 12px 12px;
    padding: 16px 20px;
    margin: 8px 0;
    margin-right: 5%;
    color: #e8e8e8;
    font-size: 0.95rem;
    line-height: 1.7;
}

/* Tool trace */
.trace-container {
    background: #0a0a0a;
    border: 1px solid #1a1a1a;
    border-radius: 8px;
    padding: 12px 16px;
    font-family: 'DM Mono', monospace;
    font-size: 0.78rem;
    color: #555;
    margin-top: 6px;
}

.trace-step {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 6px 0;
    border-bottom: 1px solid #1a1a1a;
    color: #666;
}

.trace-step:last-child { border-bottom: none; }

.trace-icon-success { color: #2ecc71; }
.trace-icon-error   { color: #e74c3c; }
.trace-icon-running { color: #f39c12; }

.trace-tool-name {
    color: #8888cc;
    font-weight: 500;
}

.trace-summary {
    color: #555;
    font-size: 0.75rem;
}

/* Input area */
.stTextInput > div > div > input {
    background-color: #111111 !important;
    border: 1px solid #222 !important;
    border-radius: 8px !important;
    color: #e8e8e8 !important;
    font-family: 'DM Sans', sans-serif !important;
    padding: 12px 16px !important;
}

.stTextInput > div > div > input:focus {
    border-color: #4444aa !important;
    box-shadow: 0 0 0 1px #4444aa !important;
}

/* Button */
.stButton > button {
    background: #1a1a3e !important;
    border: 1px solid #3333aa !important;
    color: #aaaaff !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    padding: 10px 20px !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    background: #22224e !important;
    border-color: #5555cc !important;
    color: #ccccff !important;
}

/* Header */
.app-header {
    padding: 20px 0 10px 0;
    border-bottom: 1px solid #1a1a1a;
    margin-bottom: 24px;
}

.app-title {
    font-size: 1.3rem;
    font-weight: 600;
    color: #aaaaff;
    letter-spacing: -0.02em;
}

.app-subtitle {
    font-size: 0.8rem;
    color: #444;
    margin-top: 2px;
    font-family: 'DM Mono', monospace;
}

/* Status dot */
.status-dot {
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #2ecc71;
    margin-right: 6px;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

/* Sidebar sections */
.sidebar-section {
    padding: 12px 0;
    border-bottom: 1px solid #1a1a1a;
    margin-bottom: 12px;
}

.sidebar-label {
    font-size: 0.7rem;
    color: #444;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-family: 'DM Mono', monospace;
    margin-bottom: 8px;
}

.sample-query {
    background: #111;
    border: 1px solid #1e1e1e;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 0.82rem;
    color: #666;
    margin: 4px 0;
    cursor: pointer;
    transition: all 0.15s ease;
}

.sample-query:hover {
    border-color: #333;
    color: #999;
}

/* Scrollable chat area */
.chat-area {
    max-height: 65vh;
    overflow-y: auto;
    padding-right: 8px;
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #333;
}

.empty-state-icon {
    font-size: 2.5rem;
    margin-bottom: 16px;
    opacity: 0.4;
}

.empty-state-text {
    font-size: 0.9rem;
    color: #3a3a3a;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# Session State
# ─────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []

if "traces" not in st.session_state:
    st.session_state.traces = []


# ─────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div class="app-header">
        <div class="app-title">📊 Monday BI Agent</div>
        <div class="app-subtitle">
            <span class="status-dot"></span>live · monday.com
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-label">Sample Queries</div>', unsafe_allow_html=True)

    sample_queries = [
        "How's our energy sector pipeline this quarter?",
        "What's the total deal value for mining vs powerline?",
        "Show me open work orders and their status",
        "Which deals are in advanced stages?",
        "Give me a cross-board summary for mining sector",
        "Who are the top performing owners by deal value?",
    ]

    for q in sample_queries:
        if st.button(q, key=f"sq_{q[:20]}", use_container_width=True):
            st.session_state["prefill"] = q

    st.markdown("---")
    st.markdown('<div class="sidebar-label">Session</div>', unsafe_allow_html=True)

    if st.button("🗑 Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.traces   = []
        st.rerun()

    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.72rem; color:#333; font-family:'DM Mono',monospace; line-height:1.8;">
    Every query triggers<br>live Monday.com API calls.<br>No caching.
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────
# Main Area — Two columns
# Left: Chat | Right: Tool Trace
# ─────────────────────────────────────────

col_chat, col_trace = st.columns([2, 1], gap="large")

with col_chat:
    st.markdown('<div class="sidebar-label">Conversation</div>', unsafe_allow_html=True)

    # Empty state
    if not st.session_state.messages:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📊</div>
            <div class="empty-state-text">
                Ask a founder-level business question.<br>
                I'll pull live data from your Monday.com boards.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Render messages
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="user-bubble">{msg["content"]}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="assistant-bubble">{msg["content"]}</div>',
                unsafe_allow_html=True
            )

    # Input
    prefill = st.session_state.pop("prefill", "")

    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input(
            label="Message",
            value=prefill,
            placeholder="Ask about your pipeline, revenue, work orders...",
            label_visibility="collapsed"
        )
        submitted = st.form_submit_button("Send →")

    if submitted and user_input.strip():

        # add user message
        st.session_state.messages.append({
            "role":    "user",
            "content": user_input.strip()
        })

        # build history (exclude current message)
        history = st.session_state.messages[:-1]

        # call agent
        with st.spinner("Thinking..."):
            result = run_agent(
                user_message = user_input.strip(),
                chat_history = history
            )

        # add assistant response
        st.session_state.messages.append({
            "role":    "assistant",
            "content": result["answer"]
        })

        # store trace
        st.session_state.traces.append({
            "query":      user_input.strip(),
            "tool_trace": result["tool_trace"]
        })

        st.rerun()


# ─────────────────────────────────────────
# Right Column — Tool Trace Panel
# ─────────────────────────────────────────

with col_trace:
    st.markdown('<div class="sidebar-label">Tool Trace</div>', unsafe_allow_html=True)

    if not st.session_state.traces:
        st.markdown("""
        <div style="color:#2a2a2a; font-size:0.82rem; font-family:'DM Mono',monospace;
                    padding: 40px 0; text-align:center;">
            Tool calls will<br>appear here
        </div>
        """, unsafe_allow_html=True)

    else:
        # show most recent trace first
        for trace_item in reversed(st.session_state.traces):
            query      = trace_item["query"]
            tool_trace = trace_item["tool_trace"]

            st.markdown(
                f'<div style="font-size:0.75rem; color:#444; font-family:\'DM Mono\',monospace; '
                f'margin-bottom:6px; padding-top:8px;">▸ {query[:50]}{"..." if len(query)>50 else ""}</div>',
                unsafe_allow_html=True
            )

            if not tool_trace:
                st.markdown(
                    '<div class="trace-container" style="color:#2a2a2a;">No tools called</div>',
                    unsafe_allow_html=True
                )
            else:
                trace_html = '<div class="trace-container">'
                for entry in tool_trace:
                    icon    = "✓" if entry["status"] == "success" else "✗"
                    icon_cls = "trace-icon-success" if entry["status"] == "success" else "trace-icon-error"
                    summary  = entry.get("result_summary", entry.get("error", ""))

                    trace_html += f"""
                    <div class="trace-step">
                        <span class="{icon_cls}">{icon}</span>
                        <div>
                            <div class="trace-tool-name">{entry['tool']}</div>
                            <div class="trace-summary">{summary}</div>
                        </div>
                    </div>
                    """
                trace_html += "</div>"
                st.markdown(trace_html, unsafe_allow_html=True)

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)