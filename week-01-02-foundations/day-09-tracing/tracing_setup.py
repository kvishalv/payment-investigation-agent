"""
Day 9: Tracing with LangSmith
Goal: Make the agent's reasoning fully observable and debuggable

Why tracing matters:
- "The agent gave a wrong answer" — tracing shows you exactly which tool
  returned bad data or which reasoning step went wrong
- Measure latency and token usage per step
- Compare prompt versions (A/B) with eval metrics
- Audit trail for compliance

Setup:
  pip install langsmith
  export LANGCHAIN_TRACING_V2=true
  export LANGCHAIN_API_KEY=<your key from smith.langchain.com>
  export LANGCHAIN_PROJECT=payment-investigation-agent

Once set, every agent.invoke() / chain.invoke() is automatically traced.
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain_core.tracers.context import tracing_v2_enabled
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage
from langsmith import Client
from langsmith import traceable
from dotenv import load_dotenv
import json
import os
import uuid

load_dotenv()


# ─────────────────────────────────────────────
# LangSmith configuration check
# ─────────────────────────────────────────────

def check_langsmith_setup() -> bool:
    """Verify LangSmith environment is configured."""
    required = ["LANGCHAIN_API_KEY", "LANGCHAIN_TRACING_V2"]
    missing = [k for k in required if not os.getenv(k)]

    if missing:
        print(f"[LangSmith] Missing env vars: {missing}")
        print("  Set these to enable tracing:")
        print("  export LANGCHAIN_TRACING_V2=true")
        print("  export LANGCHAIN_API_KEY=<from smith.langchain.com>")
        print("  export LANGCHAIN_PROJECT=payment-investigation-agent")
        print("  (Continuing without tracing — agent still works)\n")
        return False

    project = os.getenv("LANGCHAIN_PROJECT", "default")
    print(f"[LangSmith] Tracing enabled → project: '{project}'")
    return True


# ─────────────────────────────────────────────
# Mock data
# ─────────────────────────────────────────────

PAYMENT_DB = {
    "TXN_3001": {"id": "TXN_3001", "status": "failed", "amount": 320.00,
                 "customer_id": "CUST_401", "gateway": "stripe",
                 "error_code": "card_declined", "attempts": 2,
                 "created_at": "2024-02-14T17:00:00Z"},
}

CUSTOMER_DB = {
    "CUST_401": {"id": "CUST_401", "name": "Emma Wilson",
                 "account_age_days": 180, "total_failed": 2,
                 "total_successful": 45, "risk_tier": "standard"},
}

GATEWAY_DB = {
    "stripe": {"status": "operational", "error_rate_pct": 0.3},
}


# ─────────────────────────────────────────────
# Tools (with @traceable for custom span names)
# ─────────────────────────────────────────────

@tool
def get_payment_details(payment_id: str) -> str:
    """Get payment transaction details by ID."""
    return json.dumps(PAYMENT_DB.get(payment_id, {"error": f"{payment_id} not found"}), indent=2)


@tool
def get_customer_profile(customer_id: str) -> str:
    """Get customer profile and risk information."""
    return json.dumps(CUSTOMER_DB.get(customer_id, {"error": f"{customer_id} not found"}), indent=2)


@tool
def check_gateway_health(gateway: str) -> str:
    """Check gateway operational status and error rate."""
    return json.dumps(GATEWAY_DB.get(gateway.lower(), {"error": f"Unknown: {gateway}"}), indent=2)


# ─────────────────────────────────────────────
# Pattern 1: Automatic tracing (just set env vars)
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are a payment investigation agent.
Investigate failures systematically: get payment details, check gateway health,
get customer profile, then provide a concise root cause analysis."""


def run_with_auto_tracing(query: str, case_id: str):
    """
    Auto-tracing: just setting LANGCHAIN_TRACING_V2=true traces everything.
    The run will appear in LangSmith under your project.
    """
    print(f"\n[Auto-Tracing] Case: {case_id}")
    print(f"Query: {query}\n")

    model = ChatAnthropic(model="claude-sonnet-4-20250514")
    tools = [get_payment_details, get_customer_profile, check_gateway_health]

    agent = create_react_agent(model, tools, prompt=SYSTEM_PROMPT,
                               checkpointer=MemorySaver())

    config = {
        "configurable": {"thread_id": case_id},
        # Metadata appears in LangSmith trace — use for filtering and analysis
        "metadata": {
            "case_id": case_id,
            "analyst": "system",
            "investigation_type": "payment_failure",
        },
        # Tags appear in LangSmith — use for grouping runs
        "tags": ["payment", "investigation", "week-01"],
        # Run name appears in LangSmith trace list
        "run_name": f"investigate-{case_id}",
    }

    final_response = ""
    for state in agent.stream({"messages": [("user", query)]}, config, stream_mode="values"):
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and last.content and not getattr(last, "tool_calls", None):
            final_response = last.content

    print(final_response[:600])
    if len(final_response) > 600:
        print("...[truncated]")


# ─────────────────────────────────────────────
# Pattern 2: @traceable for custom Python functions
# ─────────────────────────────────────────────

@traceable(name="classify-payment-failure", tags=["classification"])
def classify_failure(error_code: str, gateway_healthy: bool, customer_risk: str) -> dict:
    """
    Pure Python function decorated with @traceable.
    It will appear as its own span in LangSmith, even without LangChain.
    Great for tracing non-LLM steps in your pipeline.
    """
    if not gateway_healthy:
        return {"category": "gateway_issue", "confidence": "high"}
    if customer_risk == "high":
        return {"category": "fraud_signal", "confidence": "medium"}
    if error_code in ("insufficient_funds",):
        return {"category": "card_issue", "confidence": "high"}
    return {"category": "unknown", "confidence": "low"}


# ─────────────────────────────────────────────
# Pattern 3: Manual run feedback (for eval)
# ─────────────────────────────────────────────

def submit_feedback_to_langsmith(run_id: str, score: float, comment: str):
    """
    Submit human feedback on a run — powers LangSmith's evaluation dashboard.
    score: 0.0 (wrong) to 1.0 (correct)

    In production: build a UI where analysts rate the agent's answer after each case.
    """
    if not os.getenv("LANGCHAIN_API_KEY"):
        print("[LangSmith] Skipping feedback — no API key configured")
        return

    client = Client()
    client.create_feedback(
        run_id=run_id,
        key="correctness",
        score=score,
        comment=comment,
    )
    print(f"[LangSmith] Feedback submitted: score={score} for run {run_id}")


# ─────────────────────────────────────────────
# Pattern 4: Context manager for selective tracing
# ─────────────────────────────────────────────

def run_with_selective_tracing(query: str):
    """
    Use tracing_v2_enabled() context manager to trace only specific code blocks,
    even if global tracing is off.
    """
    project = os.getenv("LANGCHAIN_PROJECT", "payment-investigation-agent")

    print(f"\n[Selective Tracing] Only this block is traced")

    model = ChatAnthropic(model="claude-sonnet-4-20250514")
    tools = [get_payment_details, get_customer_profile]
    agent = create_react_agent(model, tools, prompt=SYSTEM_PROMPT,
                               checkpointer=MemorySaver())

    with tracing_v2_enabled(project_name=project):
        result = agent.invoke(
            {"messages": [("user", query)]},
            config={"configurable": {"thread_id": "trace-test"}}
        )

    last = result["messages"][-1]
    print(last.content[:400] if hasattr(last, "content") else str(last))


# ─────────────────────────────────────────────
# What to look for in LangSmith traces
# ─────────────────────────────────────────────

TRACING_GUIDE = """
LangSmith Trace Anatomy for Payment Agent
==========================================

Top-level run: "investigate-CASE_XXX"
├── ChatAnthropic (Turn 1)          ← Initial reasoning
│   └── tokens: input=NNN output=NNN
├── get_payment_details              ← Tool call
│   └── input: {"payment_id": "TXN_3001"}
│   └── output: {"status": "failed", ...}
├── check_gateway_health             ← Tool call
│   └── input: {"gateway": "stripe"}
│   └── output: {"status": "operational", ...}
├── ChatAnthropic (Turn 2)          ← Reasoning with tool results
│   └── tokens: input=NNN output=NNN
└── Final output: "Root Cause: card_issue..."

Metrics to track:
- Total latency (ms)
- Total tokens (input + output)
- Number of tool calls
- Tool call errors
- Final answer quality (from human feedback)

Debugging a bad answer:
1. Find the run in LangSmith
2. Expand tool call results — was the data correct?
3. Check the ChatAnthropic turn where reasoning went wrong
4. Edit the system prompt and re-run → compare the two traces
"""


if __name__ == "__main__":
    langsmith_active = check_langsmith_setup()

    # Run the investigation (traced if LangSmith is configured, works regardless)
    run_with_auto_tracing(
        "Why did TXN_3001 fail? Should we retry it?",
        case_id=f"case-{uuid.uuid4().hex[:8]}"
    )

    # Demo @traceable on a pure Python function
    result = classify_failure(
        error_code="card_declined",
        gateway_healthy=True,
        customer_risk="standard"
    )
    print(f"\n[classify_failure] result: {result}")

    print(TRACING_GUIDE)
