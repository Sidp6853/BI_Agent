from app.monday.client import (
    get_all_boards,
    get_schema_for_boards,
    get_items_from_boards
)

# ─────────────────────────────────────────
print("\n" + "="*60)
print("TEST 1 — get_all_boards()")
print("="*60)
all_boards = get_all_boards()
print(f"Total boards found: {len(all_boards)}")
for b in all_boards:
    print(f"  - {b['name']} (id: {b['id']})")

ids = [b["id"] for b in all_boards]  # ← this was missing

# ─────────────────────────────────────────
print("\n" + "="*60)
print("TEST 2 — get_schema_for_boards()")
print("Schema only — no rows, no raw IDs")
print("="*60)
schema = get_schema_for_boards(ids)
for board_name, data in schema.items():
    print(f"\nBoard : {board_name}")
    print(f"ID    : {data['board_id']}")
    print(f"Columns ({len(data['columns'])}):")
    for col in data["columns"]:
        print(f"  - {col['title']} ({col['type']})")

# ─────────────────────────────────────────
print("\n" + "="*60)
print("TEST 3 — get_items_from_boards() with limit=3")
print("Human readable, mapped, with metadata")
print("="*60)
items = get_items_from_boards(ids, limit=3)
for board_name, board_data in items.items():
    print(f"\nBoard      : {board_name}")
    print(f"Total rows : {board_data['total_rows']}")
    print(f"Columns    : {board_data['columns']}")
    print(f"\nFirst row (mapped + typed):")
    if board_data["data"]:
        for col, val in board_data["data"][0].items():
            print(f"  {col}: {val} ({type(val).__name__})")

# ─────────────────────────────────────────
print("\n" + "="*60)
print("TEST 4 — Zero value check")
print("Zeros should appear, not be dropped")
print("="*60)
for board_name, board_data in items.items():
    for row in board_data["data"]:
        for col, val in row.items():
            if val == 0 or val == 0.0:
                print(f"  ✅ Zero kept — Board: {board_name} | Column: {col} | Value: {val}")

# ─────────────────────────────────────────
print("\n" + "="*60)
print("TEST 5 — Number type check")
print("Number columns should be float, not string")
print("="*60)
for board_name, board_data in items.items():
    print(f"\nBoard: {board_name}")
    for row in board_data["data"]:
        for col, val in row.items():
            if isinstance(val, float):
                print(f"  ✅ Float confirmed — {col}: {val}")
        break

# ─────────────────────────────────────────
print("\n" + "="*60)
print("ALL TESTS DONE")
print("="*60)