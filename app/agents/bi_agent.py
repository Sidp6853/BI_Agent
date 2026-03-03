# app/agent/agent.py

import os
import json
import logging
from dotenv import load_dotenv
from typing import Annotated, Dict, Any
from operator import add

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import MessagesState

from app.tools.tools import MONDAY_TOOLS
from app.prompt.system_prompt import SYSTEM_PROMPT

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────
# LLM Setup
# ─────────────────────────────────────────


_model_with_tools = None

def _get_model():
    global _model_with_tools
    if _model_with_tools is None:
        base_model = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0,
            streaming=False
        )
        _model_with_tools = base_model.bind_tools(MONDAY_TOOLS)
    return _model_with_tools


# ─────────────────────────────────────────
# State
# MessagesState handles messages automatically
# tool_trace accumulates across all tool calls
# ─────────────────────────────────────────

class AgentState(MessagesState):
    tool_trace: Annotated[list, add]


# ─────────────────────────────────────────
# Node 1 — LLM Node
# ─────────────────────────────────────────

def llm_node(state: AgentState) -> Dict[str, Any]:
    conversation = [SystemMessage(content=SYSTEM_PROMPT)]
    conversation.extend(state["messages"])

    logger.info("🤖 Agent thinking...")

    result = _get_model().invoke(conversation)

    if getattr(result, "tool_calls", None):
        logger.info(f"🔧 Tool calls requested: {[tc['name'] for tc in result.tool_calls]}")

    return {
        "messages":   [result],
        "tool_trace": []
    }


# ─────────────────────────────────────────
# Node 2 — Tool Node
# ─────────────────────────────────────────

tool_map = {tool.name: tool for tool in MONDAY_TOOLS}

def tool_node(state: AgentState) -> Dict[str, Any]:
    last_message  = state["messages"][-1]
    tool_results  = []
    trace_entries = []

    if not getattr(last_message, "tool_calls", None):
        return {"messages": [], "tool_trace": []}

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        logger.info(f"[TOOL] {tool_name} | args: {tool_args}")

        trace_entry = {
            "tool":   tool_name,
            "args":   tool_args,
            "status": "running"
        }

        try:
            result = tool_map[tool_name].invoke(tool_args)

            # build readable summary for UI trace panel
            trace_entry["status"]         = "success"
            trace_entry["result_summary"] = _summarise(tool_name, result)
            logger.info(f"✅ {tool_name} → {trace_entry['result_summary']}")

        except Exception as e:
            result                = json.dumps({"error": str(e)})
            trace_entry["status"] = "error"
            trace_entry["error"]  = str(e)
            logger.error(f"❌ {tool_name} failed: {str(e)}")

        trace_entries.append(trace_entry)

        tool_results.append(
            ToolMessage(
                content      = result,
                tool_call_id = tool_call["id"],
                name         = tool_name
            )
        )

    return {
        "messages":   tool_results,
        "tool_trace": trace_entries
    }


def _summarise(tool_name: str, result: str) -> str:
    try:
        parsed = json.loads(result)
        if tool_name == "understand_boards":
            boards = parsed.get("available_boards", [])
            return f"{len(boards)} boards found: {[b['name'] for b in boards]}"
        if tool_name == "fetch_board_data":
            total  = parsed.get("total_rows", "?")
            boards = list(parsed.get("data", {}).keys())
            return f"{total} rows fetched from: {boards}"
        return "success"
    except Exception:
        return "success"


# ─────────────────────────────────────────
# Router
# ─────────────────────────────────────────

def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return END


# ─────────────────────────────────────────
# Graph
# ─────────────────────────────────────────

graph = StateGraph(AgentState)

graph.add_node("llm",   llm_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "llm")
graph.add_conditional_edges("llm", should_continue, ["tools", END])
graph.add_edge("tools", "llm")

agent_app = graph.compile()


# ─────────────────────────────────────────
# Public Interface — called by FastAPI
# ─────────────────────────────────────────

def run_agent(user_message: str, chat_history: list[dict]) -> dict:
    """
    Called by FastAPI endpoint.

    Args:
        user_message : latest user message
        chat_history : [{"role": "user/assistant", "content": "..."}]

    Returns:
        {
            "answer":     "...",
            "tool_trace": [...]
        }
    """
    messages = []
    for msg in chat_history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=user_message))

    logger.info(f"💬 User: {user_message}")

    result = agent_app.invoke({
        "messages":   messages,
        "tool_trace": []
    })

    final_message = result["messages"][-1]


    content = final_message.content if hasattr(final_message, "content") else ""
    if isinstance(content, list):
        answer = " ".join(
            block.get("text", "") for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    else:
        answer = content
    

    logger.info("✅ Answer ready")

    return {
        "answer":     answer,
        "tool_trace": result.get("tool_trace", [])
    }