"""
Day 6: The ReAct Pattern Deep Dive
Goal: Understand how ReAct works and how to make agents reason better

ReAct = Reason + Act
The agent cycles through:
  1. Thought  — "I need to check the payment first"
  2. Action   — calls get_payment_details("TXN_12345")
  3. Observation — receives tool result
  4. Thought  — "The gateway was degraded, let me verify..."
  5. Action   — calls check_gateway_health("adyen")
  ...and so on until it has enough to answer

Today we'll:
- Trace every ReAct step explicitly
- Prompt the agent to reason out loud
- See how prompt engineering changes agent behavior
- Handle cases where the agent gets stuck
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from dotenv import load_dotenv
import json

load_dotenv()

# ─────────────────────────────────────────────
# Richer mock data for more interesting reasoning
# ─────────────────────────────────────────────
PAYMENT_DB = {
    "TXN_A001": {
        "id": "TXN_A001", "status": "failed", "amount": 89.99,
        "customer_id": "CUST_101", "gateway": "stripe",
        "error_code": "do_not_honor", "attempts": 1,
        "timestamp": "2024-02-14T14:00:00Z"
    },
    "TXN_A002": {
        "id": "TXN_A002", "status": "failed", "amount": 89.99,
        "customer_id": "CUST_101", "gateway": "stripe",
        "error_code": "do_not_honor", "attempts": 1,
        "timestamp": "2024-02-14T14:02:00Z"
    },
    "TXN_A003": {
        "id": "TXN_A003", "status": "failed", "amount": 89.99,
        "customer_id": "CUST_101", "gateway": "stripe",
        "error_code": "do_not_honor", "attempts": 1,
        "timestamp": "2024-02-14T14:04:00Z"
    },
}

CUSTOMER_DB = {
    "CUST_101": {
        "id": "CUST_101", "name": "Alice Chen",
        "account_status": "active", "account_age_days": 14,
        "total_failed_payments": 3, "total_successful_payments": 0,
        "payment_methods_count": 3, "recent_chargebacks": 0,
        "signup_ip_country": "US", "last_login_country": "NG"
    }
}

GATEWAY_DB = {
    "stripe": {"status": "operational", "error_rate_pct": 0.3}
}

FRAUD_SIGNALS_DB = {
    "CUST_101": [
        "New account (14 days old)",
        "Multiple failed attempts in short window (3 in 4 minutes)",
        "Login country changed from signup country",
        "3 different payment methods added rapidly",
        "0 successful payments ever"
    ]
}


# ─────────────────────────────────────────────
# Tools
# ─────────────────────────────────────────────

@tool
def get_payment_details(payment_id: str) -> str:
    """
    Get payment transaction details. Always call this first when investigating
    a specific payment ID.

    Args:
        payment_id: Transaction ID (e.g., TXN_A001)
    """
    data = PAYMENT_DB.get(payment_id, {"error": f"{payment_id} not found"})
    return json.dumps(data, indent=2)


@tool
def get_customer_profile(customer_id: str) -> str:
    """
    Get customer profile including account age, payment history, and location data.
    Call after getting payment details to find the customer_id.

    Args:
        customer_id: Customer ID (e.g., CUST_101)
    """
    data = CUSTOMER_DB.get(customer_id, {"error": f"{customer_id} not found"})
    return json.dumps(data, indent=2)


@tool
def get_fraud_signals(customer_id: str) -> str:
    """
    Get automated fraud risk signals for a customer.
    Call this when you suspect fraud or unusual patterns.

    Args:
        customer_id: Customer ID
    """
    signals = FRAUD_SIGNALS_DB.get(customer_id, [])
    return json.dumps({
        "customer_id": customer_id,
        "fraud_signals": signals,
        "signal_count": len(signals),
        "risk_level": "high" if len(signals) >= 3 else "medium" if len(signals) >= 1 else "low"
    }, indent=2)


@tool
def get_all_customer_payments(customer_id: str) -> str:
    """
    List ALL payment attempts for a customer, sorted by time.
    Use this to detect velocity patterns (many attempts in short window).

    Args:
        customer_id: Customer ID
    """
    txns = [t for t in PAYMENT_DB.values() if t.get("customer_id") == customer_id]
    txns.sort(key=lambda x: x.get("timestamp", ""))
    return json.dumps({"transactions": txns, "count": len(txns)}, indent=2)


@tool
def check_gateway_health(gateway: str) -> str:
    """
    Check if a payment gateway has active incidents.
    Use this to rule out infrastructure as the cause of failures.

    Args:
        gateway: Gateway name (stripe, adyen, braintree)
    """
    data = GATEWAY_DB.get(gateway.lower(), {"error": f"Unknown gateway: {gateway}"})
    return json.dumps(data, indent=2)


# ─────────────────────────────────────────────
# Two different system prompts — see how they change agent behavior
# ─────────────────────────────────────────────

BASIC_PROMPT = """You are a payment investigation agent.
Investigate payment issues and provide a summary."""

STRUCTURED_REACT_PROMPT = """You are an expert payment fraud investigator.

Follow this investigation protocol for every case:

STEP 1 — GATHER FACTS
- Get payment details for any mentioned transaction IDs
- Get the customer profile
- Check gateway health

STEP 2 — LOOK FOR PATTERNS
- Get all customer payments to check velocity
- If anything looks unusual, get fraud signals

STEP 3 — REASON EXPLICITLY
Before giving your final answer, think through:
- Is this a card issue, gateway issue, or fraud?
- What's the confidence level in your assessment?
- What additional info would change your conclusion?

STEP 4 — STRUCTURED ANSWER
Format your response as:
**Summary**: One sentence on what happened
**Root Cause**: [card_issue | gateway_issue | fraud | unknown]
**Evidence**: Bullet list of supporting facts
**Risk Level**: [low | medium | high | critical]
**Recommended Action**: Specific next step for the support team
**Confidence**: [low | medium | high] — and why
"""


# ─────────────────────────────────────────────
# Tracer: prints every ReAct step
# ─────────────────────────────────────────────

def trace_agent(query: str, system_prompt: str, label: str):
    """Run the agent and trace every Thought/Action/Observation."""
    print(f"\n{'=' * 70}")
    print(f"[{label}]")
    print(f"QUERY: {query}")
    print(f"{'=' * 70}\n")

    model = ChatAnthropic(model="claude-sonnet-4-20250514")
    tools = [get_payment_details, get_customer_profile, get_fraud_signals,
             get_all_customer_payments, check_gateway_health]

    agent = create_react_agent(model, tools, prompt=system_prompt)

    step_num = 0
    for state in agent.stream({"messages": [("user", query)]}, stream_mode="values"):
        last = state["messages"][-1]
        step_num += 1

        if isinstance(last, AIMessage):
            if last.content:
                print(f"[Step {step_num}] THOUGHT/ANSWER:")
                print(last.content[:500])  # cap long outputs for readability
                if len(last.content) > 500:
                    print("...[truncated]")
                print()
            if hasattr(last, "tool_calls") and last.tool_calls:
                for tc in last.tool_calls:
                    print(f"[Step {step_num}] ACTION: {tc['name']}({tc['args']})")
                print()

        elif isinstance(last, ToolMessage):
            preview = last.content[:300].replace("\n", " ")
            print(f"[Step {step_num}] OBSERVATION ({last.name}): {preview}")
            if len(last.content) > 300:
                print("...[truncated]")
            print()

    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    query = "Investigate payment TXN_A001 — is there anything suspicious?"

    # Compare basic vs structured prompting
    trace_agent(query, BASIC_PROMPT, "BASIC PROMPT")
    trace_agent(query, STRUCTURED_REACT_PROMPT, "STRUCTURED ReAct PROMPT")


# ─────────────────────────────────────────────
# EXERCISE: Prompt engineering for better reasoning
# ─────────────────────────────────────────────
"""
EXERCISE: Modify STRUCTURED_REACT_PROMPT to also:
1. Always express confidence as a percentage (e.g., 85%)
2. Always list 2 alternative hypotheses before settling on root cause
3. Flag if more data is needed before a decision

Run trace_agent with your new prompt and compare the output quality.
"""
