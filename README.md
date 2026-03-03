# Monday.com BI Agent

An AI-powered Business Intelligence agent that answers founder-level queries by pulling live data from Monday.com boards.

---

## Live Demo

🔗 [Monday BI Agent — Streamlit App](https://your-app-url.streamlit.app)

📋 [Deal Funnel Data Board] (https://siddhip568s-team-squad.monday.com/boards/5026950636)
📋 [Work Order Tracker Board](https://siddhip568s-team-squad.monday.com/boards/5026950742)

---

## What It Does

- Answers natural language business questions about deals pipeline, work orders, sector performance, and revenue
- Pulls **live data** from Monday.com on every query — no caching
- Handles messy, inconsistent data gracefully and communicates caveats
- Supports follow-up questions with conversation context
- Shows visible tool/API call traces for every query

---

## Example Queries

- *"How's our energy sector pipeline this quarter?"*
- *"Which deals are in advanced stages?"*
- *"What's the total deal value for mining vs powerline?"*
- *"Give me a cross-board summary for the mining sector"*
- *"Who are the top performing owners by deal value?"*

---

## Architecture

```
User (Streamlit UI)
        ↓
streamlit_app.py — chat interface + tool trace panel
        ↓
app/agents/bi_agent.py — LangGraph StateGraph
        ↓
  [llm_node] → Gemini 2.5 Flash with bound tools
        ↓ (if tool call needed)
  [tool_node] → executes tools, logs trace
        ↓ (loops back to llm_node)
  [END] → returns answer + tool_trace
        ↓
app/tools/tools.py — two LangChain tools
  • understand_boards()  — schema discovery
  • fetch_board_data()   — live row data
        ↓
app/monday/client.py — Monday.com GraphQL API v2
```

---

## Tech Stack

| Component | Choice | Reason |
|---|---|---|
| LLM | Gemini 2.5 Flash | Fast, strong tool-calling, high free quota |
| Agent Framework | LangGraph | Explicit state graph, clean tool loop |
| Monday.com | GraphQL API v2 | Direct integration, full control |
| UI | Streamlit |Easy and fast setup|
| Hosting | Streamlit Community Cloud | Public URL, no infra needed |

---

## Project Structure

```
monday-bi-agent/
├── streamlit_app.py          # UI — chat interface + tool trace panel
├── requirements.txt          # Dependencies
├── app/
│   ├── agents/
│   │   └── bi_agent.py       # LangGraph agent + run_agent()
│   ├── tools/
│   │   └── tools.py          # understand_boards + fetch_board_data
│   ├── monday/
│   │   └── client.py         # Monday.com GraphQL client
│   └── prompt/
│       └── system_prompt.py  # 5-part system prompt
```

---

## Local Setup

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/monday-bi-agent.git
cd monday-bi-agent
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the root directory:

```
MONDAY_API_KEY=your_monday_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### 5. Run the app

```bash
streamlit run streamlit_app.py
```

---

## Streamlit Cloud Deployment

1. Push repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo, set main file as `streamlit_app.py`
4. Add secrets in Settings → Secrets:

```toml
MONDAY_API_KEY = "your_key_here"
GEMINI_API_KEY = "your_key_here"
```

5. Deploy

---

## Key Design Decisions

**Two-tool pattern** — `understand_boards` fetches schema first, then `fetch_board_data` fetches rows. The agent understands the data structure before querying it, allowing intelligent board selection per query.

**No caching** — every query triggers live Monday.com API calls as required by the assignment spec.

**Dynamic board discovery** — board IDs are never hardcoded. The agent discovers boards live and selects relevant ones based on the query.

**Agent-based data cleaning** — inconsistent values (typos, casing, whitespace) are normalised by the LLM via system prompt instructions rather than hardcoded preprocessing rules.

**No pagination** — both boards are under 500 rows, within Monday.com's single-request limit. A production system would implement server-side filtering.

---

## Requirements

```
streamlit
langchain
langchain-google-genai
langgraph
requests
python-dotenv
```

---