# test_agent.py

from app.agents.bi_agent import run_agent

def test(message: str, history: list = []):
    print(f"\n{'='*60}")
    print(f"USER: {message}")
    print(f"{'='*60}")

    result = run_agent(
        user_message=message,
        chat_history=history
    )

    print(f"\nANSWER:\n{result['answer']}")

    print(f"\nTOOL TRACE:")
    if result["tool_trace"]:
        for entry in result["tool_trace"]:
            print(f"  🔧 {entry['tool']}")
            print(f"     status  : {entry['status']}")
            if "result_summary" in entry:
                print(f"     summary : {entry['result_summary']}")
    else:
        print("  No tools called ✅")

# ─────────────────────────────────────────
# Test 1 — Greeting (NO tools should be called)
# ─────────────────────────────────────────
test("Hi")

# ─────────────────────────────────────────
# Test 2 — Assignment query
# ─────────────────────────────────────────
test("which sector closed maxium deals?")
