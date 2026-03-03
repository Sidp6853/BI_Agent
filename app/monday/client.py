import os
import requests
from dotenv import load_dotenv

load_dotenv()

import os
def _get_monday_key():
    try:
        import streamlit as st
        return st.secrets.get("MONDAY_API_KEY") or os.getenv("MONDAY_API_KEY")
    except Exception:
        return os.getenv("MONDAY_API_KEY")

MONDAY_API_KEY = _get_monday_key()
# ─────────────────────────────────────────
# Auth & Config
# ─────────────────────────────────────────

MONDAY_API_KEY = os.getenv("MONDAY_API_KEY")
MONDAY_API_URL = "https://api.monday.com/v2"

HEADERS = {
    "Authorization": f"Bearer {MONDAY_API_KEY}",
    "Content-Type": "application/json",
    "API-Version": "2025-01"
}


# ─────────────────────────────────────────
# Core Runner
# ─────────────────────────────────────────

def run_query(query: str, variables: dict = None) -> dict:
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    try:
        response = requests.post(MONDAY_API_URL, json=payload, headers=HEADERS)
        response.raise_for_status()
        result = response.json()

        if "errors" in result:
            raise ValueError(f"Monday.com API error: {result['errors']}")

        return result

    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Failed to reach Monday.com API: {str(e)}")


# ─────────────────────────────────────────
# Board Discovery
# ─────────────────────────────────────────

def get_all_boards() -> list[dict]:
    query = """
    query {
      boards(board_kind: public, limit: 50) {
        id
        name
      }
    }
    """
    result = run_query(query)
    return result["data"]["boards"]





# ─────────────────────────────────────────
# Internal Helper — builds id → title map
# Never called directly by agent
# ─────────────────────────────────────────

def _build_id_to_title_map(columns: list[dict]) -> dict:
    return {col["id"]: col["title"] for col in columns}


def _build_id_to_type_map(columns: list[dict]) -> dict:
    return {col["id"]: col["type"] for col in columns}


def _map_row(item: dict, id_to_title: dict, id_to_type: dict) -> dict:
    mapped = {"name": item["name"]}
    for cv in item["column_values"]:
        # skip truly empty values but keep zeros
        if cv["text"] is None or cv["text"] == "":
            continue
        col_title = id_to_title.get(cv["id"], cv["id"])
        col_type  = id_to_type.get(cv["id"], "")
        # cast number columns to float
        if col_type == "numbers":
            try:
                mapped[col_title] = float(cv["text"])
            except ValueError:
                mapped[col_title] = cv["text"]
        else:
            mapped[col_title] = cv["text"]
    return mapped


# ─────────────────────────────────────────
# Tool 1 — Schema Only
# Agent uses this to understand board structure
# Returns column names + types, nothing else
# ─────────────────────────────────────────

def get_schema_for_boards(board_ids: list[str]) -> dict:
    """
    TOOL 1 — Called first by agent.
    Returns column names and types for each board.
    Agent uses this to understand what data is available
    before making a data query.

    Returns:
        {
            "Deal funnel Data": {
                "board_id": "123",
                "columns": [
                    {"title": "Sector/service", "type": "status"},
                    {"title": "Masked Deal value", "type": "numbers"},
                    ...
                ]
            }
        }
    """
    query = """
    query ($boardIds: [ID!]) {
      boards(ids: $boardIds) {
        id
        name
        columns {
          id
          title
          type
        }
      }
    }
    """
    variables = {"boardIds": board_ids}
    result    = run_query(query, variables)

    output = {}
    for board in result["data"]["boards"]:
        output[board["name"]] = {
            "board_id": board["id"],
            "columns": [
                {"title": col["title"], "type": col["type"]}
                for col in board["columns"]
            ]
        }
    return output


# ─────────────────────────────────────────
# Tool 2 — Fetch Data (already mapped)
# Agent uses this to get actual row data
# Returns human readable rows directly
# ─────────────────────────────────────────

def get_items_from_boards(board_ids: list[str], limit: int = 500) -> dict:
    """
    TOOL 2 — Called after get_schema_for_boards().
    Fetches all items and returns them already mapped
    with human readable column names.
    Numbers are cast to float automatically.
    Empty values are excluded, zeros are kept.

    Returns:
        {
            "Deal funnel Data": {
                "total_rows": 346,
                "columns": ["Name", "Sector/service", ...],
                "data": [
                    {"name": "Naruto", "Sector/service": "Mining", ...},
                    ...
                ]
            }
        }
    """
    query = """
    query ($boardIds: [ID!], $limit: Int) {
      boards(ids: $boardIds) {
        id
        name
        columns {
          id
          title
          type
        }
        items_page(limit: $limit) {
          items {
            id
            name
            column_values {
              id
              text
              value
            }
          }
        }
      }
    }
    """
    variables = {"boardIds": board_ids, "limit": limit}
    result    = run_query(query, variables)

    output = {}
    for board in result["data"]["boards"]:
        board_name  = board["name"]
        columns     = board["columns"]
        id_to_title = _build_id_to_title_map(columns)
        id_to_type  = _build_id_to_type_map(columns)

        mapped_rows = [
            _map_row(item, id_to_title, id_to_type)
            for item in board["items_page"]["items"]
        ]

        output[board_name] = {
            "total_rows": len(mapped_rows),
            "columns":    [col["title"] for col in columns],
            "data":       mapped_rows
        }

    return output