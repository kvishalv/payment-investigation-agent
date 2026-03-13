"""
Day 5: First LangChain Agent
Goal: Build a payment investigation agent using LangGraph's ReAct agent

What's different from Day 2's manual agentic loop?
- LangGraph manages the tool-calling loop automatically
- Agent decides which tools to use and in what order
- Built-in message history management
- Much less boilerplate
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
import json

load_dotenv()

# ─────────────────────────────────────────────
# Mock data (same as Day 2 — reusing our domain knowledge)
# ─────────────────────────────────────────────
PAYMENT_DB = {
    "TXN_12345": {
        "id": "TXN_12345", "status": "failed", "amount": 150.00,
        "currency": "USD", "customer_id": "CUST_789",
        "payment_method": "card_4242", "gateway": "stripe",
        "error_code": "insufficient_funds", "attempts": 3,
        "created_at": "2024-02-14T10:20:00Z",
        "last_attempt": "2024-02-14T10:23:45Z"
    },
    "TXN_67890": {
        "id": "TXN_67890", "status": "succeeded", "amount": 299.99,
        "currency": "USD", "customer_id": "CUST_456",
        "payment_method": "card_5555", "gateway": "stripe",
        "created_at": "2024-02-14T09:15:00Z"
    },
    "TXN_99999": {
        "id": "TXN_99999", "status": "failed", "amount": 5000.00,
        "currency": "USD", "customer_id": "CUST_789",
        "payment_method": "card_9999", "gateway": "adyen",
        "error_code": "suspected_fraud", "attempts": 1,
        "created_at": "2024-02-14T11:00:00Z",
        "last_attempt": "2024-02-14T11:00:12Z"
    }
}

CUSTOMER_DB = {
    "CUST_789": {
        "id": "CUST_789", "name": "Jane Doe", "email": "jane@example.com",
        "account_status": "active", "payment_methods": ["card_4242", "card_9999"],
        "total_failed_payments": 5, "total_successful_payments": 127,
        "account_age_days": 730, "recent_chargebacks": 0
    },
    "CUST_456": {
        "id": "CUST_456", "name": "John Smith", "email": "john@example.com",
        "account_status": "active", "payment_methods": ["card_5555"],
        "total_failed_payments": 0, "total_successful_payments": 89,
        "account_age_days": 180, "recent_chargebacks": 0
    }
}

GATEWAY_STATUS = {
    "stripe": {"status": "operational", "error_rate_pct": 0.2, "avg_response_ms": 340},
    "adyen": {"status": "degraded", "error_rate_pct": 4.7, "avg_response_ms": 1200,
              "incident": "Elevated decline rates since 10:45 UTC"}
}


# ─────────────────────────────────────────────
# Tools — decorated with @tool so LangChain knows about them
# ─────────────────────────────────────────────

@tool
def get_payment_details(payment_id: str) -> str:
    """
    Retrieve full details for a payment transaction.
    Use this to check status, error codes, amount, gateway, and attempt history.

    Args:
        payment_id: The transaction ID (e.g., TXN_12345)
    """
    if payment_id in PAYMENT_DB:
        return json.dumps(PAYMENT_DB[payment_id], indent=2)
    return json.dumps({"error": f"Payment {payment_id} not found"})


@tool
def get_customer_profile(customer_id: str) -> str:
    """
    Retrieve customer account information including payment history and risk signals.
    Use this after finding the customer_id from payment details.

    Args:
        customer_id: The customer ID (e.g., CUST_789)
    """
    if customer_id in CUSTOMER_DB:
        return json.dumps(CUSTOMER_DB[customer_id], indent=2)
    return json.dumps({"error": f"Customer {customer_id} not found"})


@tool
def check_gateway_health(gateway: str) -> str:
    """
    Check real-time health status of a payment gateway.
    Use this to determine if failures are due to gateway issues vs card/customer issues.

    Args:
        gateway: Gateway name (e.g., stripe, adyen, braintree)
    """
    gateway_lower = gateway.lower()
    if gateway_lower in GATEWAY_STATUS:
        return json.dumps(GATEWAY_STATUS[gateway_lower], indent=2)
    return json.dumps({"error": f"Unknown gateway: {gateway}",
                       "known_gateways": list(GATEWAY_STATUS.keys())})


@tool
def list_customer_transactions(customer_id: str) -> str:
    """
    List all transactions for a customer to identify patterns.
    Use this to spot repeat failures or unusual activity.

    Args:
        customer_id: The customer ID
    """
    transactions = [
        txn for txn in PAYMENT_DB.values()
        if txn.get("customer_id") == customer_id
    ]
    if not transactions:
        return json.dumps({"message": "No transactions found", "customer_id": customer_id})
    return json.dumps(transactions, indent=2)


# ─────────────────────────────────────────────
# Build the agent
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert payment investigation agent.

Your job is to investigate payment failures and anomalies by:
1. Looking up payment details to understand what happened
2. Checking the customer profile for context and risk signals
3. Checking gateway health to rule out infrastructure issues
4. Reviewing all customer transactions to identify patterns
5. Synthesizing a clear root cause analysis with recommended actions

Always be systematic: gather data first, then analyze, then recommend.
Format your final answer with these sections:
- **Root Cause**: What actually caused the failure
- **Risk Assessment**: Any fraud or chargeback risk signals
- **Recommended Action**: What the support team should do next
"""


def create_payment_agent():
    """Create the payment investigation agent."""
    model = ChatAnthropic(model="claude-sonnet-4-20250514")
    tools = [get_payment_details, get_customer_profile, check_gateway_health, list_customer_transactions]

    agent = create_react_agent(model, tools, prompt=SYSTEM_PROMPT)
    return agent


def investigate(query: str):
    """Run the agent on a query and print the result."""
    print(f"\n{'=' * 70}")
    print(f"QUERY: {query}")
    print(f"{'=' * 70}\n")

    agent = create_payment_agent()

    # stream_mode="values" gives us each state after every step
    for step in agent.stream({"messages": [("user", query)]}, stream_mode="values"):
        # Print each message as it's generated
        last_msg = step["messages"][-1]
        msg_type = type(last_msg).__name__

        if msg_type == "AIMessage":
            if last_msg.content:
                print(f"[Agent]: {last_msg.content}\n")
            if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                for tc in last_msg.tool_calls:
                    print(f"[Tool call]: {tc['name']}({tc['args']})")
        elif msg_type == "ToolMessage":
            # Show a preview of tool results (first 200 chars)
            preview = last_msg.content[:200].replace("\n", " ")
            print(f"[Tool result ({last_msg.name})]: {preview}...\n")

    print(f"\n{'=' * 70}\n")


if __name__ == "__main__":
    # Test 1: Simple failure investigation
    investigate("Why did payment TXN_12345 fail?")

    # Test 2: Multi-factor investigation (fraud signal)
    investigate(
        "Payment TXN_99999 was flagged for fraud. "
        "Is this legitimate? What should we do?"
    )

    # Test 3: Gateway health angle
    investigate(
        "We're seeing a spike in Adyen failures. "
        "Can you check what's happening and if TXN_99999 is related?"
    )
