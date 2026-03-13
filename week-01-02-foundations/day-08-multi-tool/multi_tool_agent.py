"""
Day 8: Multi-Tool Agent
Goal: Build a full payment investigation suite with 8 tools

Previous days used 3-5 tools. Real agents need a richer toolset:
- Payment & customer lookup (from Day 5)
- Log querying — see raw event streams
- Alert management — create/close ops alerts
- Merchant lookup — is the merchant having issues?
- Retry advisor — should we retry this payment?
- Refund eligibility checker

The challenge: with more tools, tool descriptions and the system prompt
must work harder to guide the agent to the right tools.
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage
from dotenv import load_dotenv
import json
from datetime import datetime, timezone
import uuid

load_dotenv()


# ─────────────────────────────────────────────
# Mock data — richer than previous days
# ─────────────────────────────────────────────

PAYMENT_DB = {
    "TXN_2001": {"id": "TXN_2001", "status": "failed", "amount": 450.00,
                 "customer_id": "CUST_301", "merchant_id": "MERCH_99",
                 "gateway": "stripe", "error_code": "card_declined",
                 "payment_method": "card_4242", "currency": "USD",
                 "created_at": "2024-02-14T16:00:00Z", "attempts": 2},
    "TXN_2002": {"id": "TXN_2002", "status": "failed", "amount": 1200.00,
                 "customer_id": "CUST_302", "merchant_id": "MERCH_42",
                 "gateway": "adyen", "error_code": "restricted_card",
                 "payment_method": "card_9876", "currency": "USD",
                 "created_at": "2024-02-14T16:30:00Z", "attempts": 1},
    "TXN_2003": {"id": "TXN_2003", "status": "failed", "amount": 75.00,
                 "customer_id": "CUST_301", "merchant_id": "MERCH_99",
                 "gateway": "stripe", "error_code": "card_declined",
                 "payment_method": "card_4242", "currency": "USD",
                 "created_at": "2024-02-14T16:05:00Z", "attempts": 1},
}

CUSTOMER_DB = {
    "CUST_301": {"id": "CUST_301", "name": "Carlos Mendez", "email": "carlos@example.com",
                 "account_status": "active", "account_age_days": 365,
                 "total_failed": 4, "total_successful": 67, "lifetime_value_usd": 12400,
                 "risk_tier": "standard"},
    "CUST_302": {"id": "CUST_302", "name": "Diana Park", "email": "diana@example.com",
                 "account_status": "active", "account_age_days": 90,
                 "total_failed": 1, "total_successful": 12, "lifetime_value_usd": 3200,
                 "risk_tier": "standard"},
}

MERCHANT_DB = {
    "MERCH_99": {"id": "MERCH_99", "name": "TechGadgets Inc", "category": "electronics",
                 "avg_ticket_usd": 380, "chargeback_rate_pct": 0.8,
                 "active_dispute_count": 2, "status": "active"},
    "MERCH_42": {"id": "MERCH_42", "name": "LuxuryTravel Co", "category": "travel",
                 "avg_ticket_usd": 1800, "chargeback_rate_pct": 1.2,
                 "active_dispute_count": 0, "status": "active"},
}

GATEWAY_DB = {
    "stripe": {"status": "operational", "error_rate_pct": 0.4, "p99_response_ms": 450},
    "adyen": {"status": "operational", "error_rate_pct": 0.6, "p99_response_ms": 520},
}

LOG_DB = {
    "TXN_2001": [
        {"ts": "2024-02-14T16:00:01Z", "event": "payment_initiated", "details": "amount=450.00 card=4242"},
        {"ts": "2024-02-14T16:00:02Z", "event": "gateway_request_sent", "details": "gateway=stripe"},
        {"ts": "2024-02-14T16:00:03Z", "event": "gateway_response", "details": "code=card_declined decline_code=insufficient_funds"},
        {"ts": "2024-02-14T16:00:03Z", "event": "payment_failed", "details": "attempt=1"},
        {"ts": "2024-02-14T16:02:00Z", "event": "payment_retry", "details": "attempt=2"},
        {"ts": "2024-02-14T16:02:01Z", "event": "gateway_response", "details": "code=card_declined decline_code=insufficient_funds"},
        {"ts": "2024-02-14T16:02:01Z", "event": "payment_failed", "details": "attempt=2 max_retries_reached=true"},
    ],
    "TXN_2002": [
        {"ts": "2024-02-14T16:30:00Z", "event": "payment_initiated", "details": "amount=1200.00 card=9876"},
        {"ts": "2024-02-14T16:30:01Z", "event": "gateway_request_sent", "details": "gateway=adyen"},
        {"ts": "2024-02-14T16:30:02Z", "event": "gateway_response", "details": "code=restricted_card"},
        {"ts": "2024-02-14T16:30:02Z", "event": "payment_failed", "details": "attempt=1"},
    ],
}

ALERTS: list[dict] = []

RETRY_RULES = {
    "card_declined":   {"should_retry": True,  "delay_minutes": 60,
                        "reason": "Temporary decline — may resolve with funds"},
    "insufficient_funds": {"should_retry": False, "delay_minutes": None,
                           "reason": "Card has insufficient funds — customer must use different card"},
    "restricted_card": {"should_retry": False, "delay_minutes": None,
                        "reason": "Card is restricted by issuing bank — different card required"},
    "do_not_honor":    {"should_retry": False, "delay_minutes": None,
                        "reason": "Bank hard-declined — contact customer"},
}


# ─────────────────────────────────────────────
# 8 Tools — the full investigation suite
# ─────────────────────────────────────────────

@tool
def get_payment_details(payment_id: str) -> str:
    """
    Get full payment transaction details: status, amount, error code, gateway, merchant, customer.
    Always start here when investigating a specific transaction.
    """
    return json.dumps(PAYMENT_DB.get(payment_id, {"error": f"{payment_id} not found"}), indent=2)


@tool
def get_customer_profile(customer_id: str) -> str:
    """Get customer profile: account age, payment history, risk tier, lifetime value."""
    return json.dumps(CUSTOMER_DB.get(customer_id, {"error": f"{customer_id} not found"}), indent=2)


@tool
def get_merchant_info(merchant_id: str) -> str:
    """
    Get merchant details: category, average ticket size, chargeback rate, dispute count.
    Use to understand if the merchant category or chargeback history is a factor.
    """
    return json.dumps(MERCHANT_DB.get(merchant_id, {"error": f"{merchant_id} not found"}), indent=2)


@tool
def check_gateway_health(gateway: str) -> str:
    """
    Check gateway operational status and current error rate.
    Use early to rule out infrastructure as the failure cause.
    """
    return json.dumps(GATEWAY_DB.get(gateway.lower(), {"error": f"Unknown: {gateway}"}), indent=2)


@tool
def get_payment_logs(payment_id: str) -> str:
    """
    Retrieve the raw event log for a payment: every step from initiation to result.
    Use to see exactly what happened at each stage (e.g., which retry attempt failed, response timing).
    """
    logs = LOG_DB.get(payment_id, [])
    return json.dumps({"payment_id": payment_id, "events": logs, "count": len(logs)}, indent=2)


@tool
def list_customer_payments(customer_id: str) -> str:
    """
    List all payment transactions for a customer.
    Use to spot patterns: repeated failures on same card, velocity issues, etc.
    """
    txns = [t for t in PAYMENT_DB.values() if t.get("customer_id") == customer_id]
    return json.dumps({"customer_id": customer_id, "transactions": txns, "count": len(txns)}, indent=2)


@tool
def get_retry_recommendation(error_code: str) -> str:
    """
    Get a retry recommendation for a given error code.
    Returns whether to retry, how long to wait, and why.
    Call this after identifying the error code to advise the customer or system.

    Args:
        error_code: The gateway error code (e.g., card_declined, insufficient_funds)
    """
    rec = RETRY_RULES.get(error_code, {
        "should_retry": False,
        "delay_minutes": None,
        "reason": f"Unknown error code '{error_code}' — manual review recommended"
    })
    rec["error_code"] = error_code
    return json.dumps(rec, indent=2)


@tool
def create_alert(severity: str, title: str, description: str, payment_id: str = "") -> str:
    """
    Create an operational alert for the on-call team.
    Use when you detect a pattern that needs human attention (fraud spike, gateway issue, high-value failure).

    Args:
        severity: critical | high | medium | low
        title: Short alert title (max 80 chars)
        description: Detailed description of the issue and recommended action
        payment_id: Optional — the triggering transaction ID
    """
    alert = {
        "id": f"ALERT_{str(uuid.uuid4())[:8].upper()}",
        "severity": severity,
        "title": title,
        "description": description,
        "payment_id": payment_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "open",
    }
    ALERTS.append(alert)
    return json.dumps({"created": True, "alert": alert}, indent=2)


# ─────────────────────────────────────────────
# Agent with full toolset
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are a senior payment operations analyst with access to a full investigation toolkit.

TOOLS OVERVIEW:
- get_payment_details      → start here for any transaction
- get_customer_profile     → customer history and risk
- get_merchant_info        → merchant category and dispute rate
- check_gateway_health     → rule out infrastructure issues
- get_payment_logs         → raw event timeline for deep debugging
- list_customer_payments   → spot patterns across a customer's history
- get_retry_recommendation → advise on whether to retry
- create_alert             → escalate to on-call team if needed

INVESTIGATION PROTOCOL:
1. Get payment details → identify customer, merchant, gateway, error_code
2. Check gateway health → rule out infra
3. Get customer profile + payment history → assess risk and patterns
4. Get merchant info → check if merchant category is a factor
5. Get payment logs → understand the exact failure sequence
6. Get retry recommendation → advise on next step
7. If severity warrants it, create an alert

ESCALATION CRITERIA (create an alert if any apply):
- Multiple failures for same customer in <10 minutes
- Error code is fraud-related (restricted_card, do_not_honor on new account)
- High-value transaction (>$1,000) that failed
- Gateway error rate spike detected

OUTPUT FORMAT:
**Transaction**: TXN_XXXX
**Root Cause**: [card_issue | gateway_issue | fraud_signal | merchant_issue | unknown]
**What Happened**: 2-3 sentence timeline
**Customer Context**: Risk level and relevant history
**Retry Recommendation**: Yes/No — and why
**Action Required**: Specific next step
**Alert Created**: Yes (ALERT_XXXX) | No
"""


def run_investigation(query: str, thread_id: str | None = None):
    """Run a multi-tool investigation."""
    print(f"\n{'=' * 70}")
    print(f"QUERY: {query}")
    print(f"{'=' * 70}\n")

    model = ChatAnthropic(model="claude-sonnet-4-20250514")
    tools = [
        get_payment_details, get_customer_profile, get_merchant_info,
        check_gateway_health, get_payment_logs, list_customer_payments,
        get_retry_recommendation, create_alert,
    ]

    checkpointer = MemorySaver()
    agent = create_react_agent(model, tools, prompt=SYSTEM_PROMPT,
                               checkpointer=checkpointer)

    config = {"configurable": {"thread_id": thread_id or str(uuid.uuid4())}}

    tool_call_count = 0
    for state in agent.stream({"messages": [("user", query)]}, config, stream_mode="values"):
        last = state["messages"][-1]
        if isinstance(last, AIMessage):
            if hasattr(last, "tool_calls") and last.tool_calls:
                for tc in last.tool_calls:
                    tool_call_count += 1
                    print(f"  [tool {tool_call_count}] {tc['name']}({list(tc['args'].values())})")
            elif last.content:
                print(f"\n{last.content}")

    if ALERTS:
        print(f"\n--- Active Alerts ({len(ALERTS)}) ---")
        for a in ALERTS:
            print(f"  [{a['severity'].upper()}] {a['id']}: {a['title']}")


if __name__ == "__main__":
    # Case 1: Repeated failures on same customer — should trigger alert
    run_investigation(
        "TXN_2001 and TXN_2003 both failed for the same customer in quick succession. "
        "Investigate and tell me if we need to escalate."
    )

    # Case 2: High-value restricted card
    run_investigation(
        "Investigate TXN_2002 — it's a $1,200 transaction with a restricted card. "
        "Full analysis please."
    )
