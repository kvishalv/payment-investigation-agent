"""
Day 7: Memory
Goal: Make the agent remember context across turns in a conversation

Why memory matters for payment investigation:
- Analyst says "investigate TXN_A001" → agent gathers all the data
- Analyst follows up "what about that customer's other payments?"
  → without memory: agent starts fresh, asks "which customer?"
  → with memory: agent already knows it's CUST_101

Three memory patterns today:
1. In-session memory — MemorySaver (thread-scoped)
2. Conversation summarization — compress long histories
3. Cross-session memory — persist findings to a simple store
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage
from dotenv import load_dotenv
import json
import uuid

load_dotenv()

# ─────────────────────────────────────────────
# Mock data
# ─────────────────────────────────────────────
PAYMENT_DB = {
    "TXN_A001": {"id": "TXN_A001", "status": "failed", "amount": 89.99,
                 "customer_id": "CUST_101", "gateway": "stripe",
                 "error_code": "do_not_honor", "timestamp": "2024-02-14T14:00:00Z"},
    "TXN_A002": {"id": "TXN_A002", "status": "failed", "amount": 89.99,
                 "customer_id": "CUST_101", "gateway": "stripe",
                 "error_code": "do_not_honor", "timestamp": "2024-02-14T14:02:00Z"},
    "TXN_B001": {"id": "TXN_B001", "status": "succeeded", "amount": 199.00,
                 "customer_id": "CUST_202", "gateway": "adyen",
                 "timestamp": "2024-02-14T15:00:00Z"},
}

CUSTOMER_DB = {
    "CUST_101": {"id": "CUST_101", "name": "Alice Chen",
                 "account_age_days": 14, "total_failed": 3, "total_successful": 0,
                 "risk_level": "high"},
    "CUST_202": {"id": "CUST_202", "name": "Bob Rivera",
                 "account_age_days": 540, "total_failed": 1, "total_successful": 98,
                 "risk_level": "low"},
}

# Simple in-memory cross-session store (in production: Redis, Postgres, etc.)
INVESTIGATION_NOTES: dict[str, list[str]] = {}


# ─────────────────────────────────────────────
# Tools
# ─────────────────────────────────────────────

@tool
def get_payment_details(payment_id: str) -> str:
    """Get payment transaction details by ID."""
    data = PAYMENT_DB.get(payment_id, {"error": f"{payment_id} not found"})
    return json.dumps(data, indent=2)


@tool
def get_customer_profile(customer_id: str) -> str:
    """Get customer profile and risk level."""
    data = CUSTOMER_DB.get(customer_id, {"error": f"{customer_id} not found"})
    return json.dumps(data, indent=2)


@tool
def list_customer_payments(customer_id: str) -> str:
    """List all payments for a customer."""
    txns = [t for t in PAYMENT_DB.values() if t.get("customer_id") == customer_id]
    return json.dumps({"transactions": txns, "count": len(txns)}, indent=2)


@tool
def save_investigation_note(case_id: str, note: str) -> str:
    """
    Save a note about this investigation to persistent memory.
    Use this to record key findings so they're available in future sessions.

    Args:
        case_id: A unique identifier for this case (e.g., customer ID or transaction ID)
        note: A concise summary of the finding to remember
    """
    if case_id not in INVESTIGATION_NOTES:
        INVESTIGATION_NOTES[case_id] = []
    INVESTIGATION_NOTES[case_id].append(note)
    return json.dumps({"saved": True, "case_id": case_id, "note": note})


@tool
def get_investigation_notes(case_id: str) -> str:
    """
    Retrieve previously saved notes for a case.
    Always call this at the start of an investigation to check prior findings.

    Args:
        case_id: The case ID to retrieve notes for
    """
    notes = INVESTIGATION_NOTES.get(case_id, [])
    return json.dumps({
        "case_id": case_id,
        "notes": notes,
        "count": len(notes),
        "has_prior_investigation": len(notes) > 0
    }, indent=2)


# ─────────────────────────────────────────────
# Pattern 1: In-session memory with MemorySaver
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are a payment investigation agent with memory.

At the start of each investigation, check for prior notes using get_investigation_notes.
After completing an investigation, save key findings with save_investigation_note.

When the analyst asks follow-up questions, use the conversation history —
don't re-fetch data you already retrieved in this session.
"""


def create_memory_agent():
    """Agent with in-session memory — remembers within a thread_id."""
    model = ChatAnthropic(model="claude-sonnet-4-20250514")
    tools = [get_payment_details, get_customer_profile, list_customer_payments,
             save_investigation_note, get_investigation_notes]

    # MemorySaver stores the full message history keyed by thread_id
    checkpointer = MemorySaver()

    agent = create_react_agent(model, tools, prompt=SYSTEM_PROMPT,
                               checkpointer=checkpointer)
    return agent


def run_multi_turn_conversation():
    """
    Demo: Multi-turn conversation where agent remembers previous turns.
    Each call uses the same thread_id — agent sees full history.
    """
    print("\n" + "=" * 70)
    print("DEMO 1: In-Session Memory (Multi-Turn Conversation)")
    print("=" * 70)

    agent = create_memory_agent()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # Turn 1: Initial investigation
    turn(agent, config, "Please investigate payment TXN_A001.", turn_num=1)

    # Turn 2: Follow-up — agent should remember TXN_A001's customer
    turn(agent, config, "What other payments has that customer made?", turn_num=2)

    # Turn 3: Deep follow-up — agent still has full context
    turn(agent, config, "Based on everything you've seen, what's your risk assessment and recommended action?", turn_num=3)


def turn(agent, config: dict, message: str, turn_num: int):
    """Execute one conversation turn and print the final response."""
    print(f"\n--- Turn {turn_num} ---")
    print(f"Analyst: {message}")
    print()

    final_response = ""
    for state in agent.stream({"messages": [("user", message)]}, config,
                               stream_mode="values"):
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and last.content and not getattr(last, "tool_calls", None):
            final_response = last.content

    print(f"Agent: {final_response[:600]}")
    if len(final_response) > 600:
        print("...[truncated]")


# ─────────────────────────────────────────────
# Pattern 2: New session — picks up from saved notes
# ─────────────────────────────────────────────

def run_cross_session_demo():
    """
    Demo: New thread_id (new session), but agent checks saved notes
    and picks up where the last session left off.
    """
    print("\n" + "=" * 70)
    print("DEMO 2: Cross-Session Memory (via saved notes)")
    print("=" * 70)

    # First session — investigate and save findings
    print("\n[SESSION 1] Initial investigation...")
    agent = create_memory_agent()
    session1_config = {"configurable": {"thread_id": "session-1"}}
    turn(agent, session1_config,
         "Investigate CUST_101 and save your key findings for future reference.",
         turn_num=1)

    # Second session — brand new thread, but notes persist
    print("\n[SESSION 2] New analyst picks up the case...")
    session2_config = {"configurable": {"thread_id": "session-2"}}  # new thread!
    turn(agent, session2_config,
         "I'm reviewing the CUST_101 case. Check if there are any prior investigation notes, then tell me the current status.",
         turn_num=1)


# ─────────────────────────────────────────────
# Pattern 3: Inspect message history
# ─────────────────────────────────────────────

def inspect_memory(agent, config: dict):
    """Show what's stored in the agent's memory for a thread."""
    print("\n--- Memory snapshot ---")
    state = agent.get_state(config)
    messages = state.values.get("messages", [])
    print(f"Total messages in thread: {len(messages)}")
    for i, msg in enumerate(messages):
        role = type(msg).__name__.replace("Message", "")
        preview = str(msg.content)[:80].replace("\n", " ")
        print(f"  [{i}] {role}: {preview}")


if __name__ == "__main__":
    run_multi_turn_conversation()
    run_cross_session_demo()
