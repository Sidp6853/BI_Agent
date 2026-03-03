# app/tools/monday_tools.py

import json
from pydantic import BaseModel, Field
from langchain.tools import tool

from app.monday.client import (
    get_all_boards,
    get_schema_for_boards,
    get_items_from_boards
)


# ─────────────────────────────────────────
# Pydantic Input Schemas
# ─────────────────────────────────────────

class UnderstandBoardsInput(BaseModel):
    """No input needed — discovers all boards and their schema automatically."""
    pass


class FetchBoardDataInput(BaseModel):
    board_ids: list[str] = Field(
        description=(
            "List of board IDs to fetch data from. "
            "Get these from understand_boards tool first. "
            "Pass one ID for single board, multiple IDs for cross-board queries."
        )
    )


# ─────────────────────────────────────────
# TOOL 1 — understand_boards
# Always called first by the agent
# Combines board discovery + schema in one call
# ─────────────────────────────────────────

@tool(args_schema=UnderstandBoardsInput)
def understand_boards() -> str:
    """
    ALWAYS call this tool first before answering any business question.

    Discovers all available Monday.com boards and returns their
    column structure so you understand what data is available.

    Returns:
    - All board names and IDs
    - Column names and types for each board
    - Use the board IDs from here to call fetch_board_data

    You must call this before fetch_board_data so you know
    which board IDs to pass and what columns exist.
    """
    try:
        # Step 1 — get all boards
        boards = get_all_boards()

        if not boards:
            return json.dumps({
                "error": "No boards found in workspace."
            })

        # Step 2 — get schema for all boards in one call
        board_ids = [b["id"] for b in boards]
        schema    = get_schema_for_boards(board_ids)

        # Step 3 — combine into one clean response
        output = {
            "available_boards": [
                {
                    "id":      b["id"],
                    "name":    b["name"],
                    "columns": schema.get(b["name"], {}).get("columns", [])
                }
                for b in boards
            ],
            "instruction": (
                "Use the 'id' field to call fetch_board_data. "
                "Pick boards relevant to the user's question. "
                "Ignore boards with no relevant columns."
            )
        }

        return json.dumps(output, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "note": "Failed to fetch boards and schema."
        })


# ─────────────────────────────────────────
# TOOL 2 — fetch_board_data
# Called after understand_boards
# Agent picks which board IDs are relevant
# ─────────────────────────────────────────

@tool(args_schema=FetchBoardDataInput)
def fetch_board_data(board_ids: list[str]) -> str:
    """
    Fetches actual data from one or more Monday.com boards.

    Call this after understand_boards once you know which
    board IDs are relevant to the user's question.

    Pass a single board ID for single-board questions.
    Pass multiple board IDs for cross-board questions
    e.g. combining Deals + Work Orders data.

    Data is returned already cleaned:
    - Column IDs replaced with human readable names
    - Number columns cast to float
    - Empty values excluded, zeros preserved

    Returns for each board:
    - total_rows: how many items exist
    - columns: list of all column names
    - data: list of row dicts with column_name → value
    """
    try:
        items = get_items_from_boards(board_ids)

        # add token warning if data is large
        total_rows = sum(
            v["total_rows"]
            for v in items.values()
            if isinstance(v, dict) and "total_rows" in v
        )

        result = {
            "data":       items,
            "total_rows": total_rows,
        }

        if total_rows > 300:
            result["warning"] = (
                f"Large dataset: {total_rows} rows returned. "
                "Focus your analysis on the specific question asked. "
                "Avoid summarising all rows."
            )

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({
            "error":     str(e),
            "board_ids": board_ids,
            "note":      "Failed to fetch board data."
        })


# ─────────────────────────────────────────
# Export — used by agent.py to bind tools
# ─────────────────────────────────────────

MONDAY_TOOLS = [
    understand_boards,
    fetch_board_data
]