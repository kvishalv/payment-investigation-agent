# Day 8 Learnings - Multi-Tool Agent

**Date**: 2026-03-13

## The Jump from 4 to 8 Tools

Days 5-7 used 3-5 tools. Today we built a realistic suite of 8:

| Tool | When to use |
|------|------------|
| `get_payment_details` | Always first |
| `get_customer_profile` | After getting customer_id |
| `get_merchant_info` | Check if merchant category/disputes matter |
| `check_gateway_health` | Rule out infrastructure early |
| `get_payment_logs` | Deep debugging — exact event sequence |
| `list_customer_payments` | Spot velocity/pattern issues |
| `get_retry_recommendation` | Advise customer on next step |
| `create_alert` | Escalate to on-call when criteria met |

## Key Design Decisions

### Action tools vs. Query tools
- **Query tools** (6 of 8): read-only, safe to call anytime
- **Action tools** (2 of 8): `create_alert` has real-world side effects
  - Document in the system prompt exactly WHEN to call action tools
  - Define escalation criteria explicitly — don't leave it to the model's judgment

### Escalation criteria in the prompt
```
ESCALATION CRITERIA (create an alert if any apply):
- Multiple failures for same customer in <10 minutes
- Error code is fraud-related on new account
- High-value transaction (>$1,000) that failed
```
Without explicit criteria, the agent either escalates too much or too little.

### Tool ordering hints
The system prompt defines a numbered protocol:
```
1. get_payment_details → 2. check_gateway_health → 3. get_customer_profile...
```
This reduces unnecessary tool calls and prevents the agent from jumping to conclusions.

## Tool Description Quality

Bad description (vague):
```python
@tool
def get_merchant_info(merchant_id: str) -> str:
    """Get merchant info."""
```

Good description (tells the agent *when* to call it):
```python
@tool
def get_merchant_info(merchant_id: str) -> str:
    """
    Get merchant details: category, average ticket size, chargeback rate, dispute count.
    Use to understand if the merchant category or chargeback history is a factor.
    """
```

The agent reads tool descriptions to decide when to call them — this is prompt engineering.

## Tool Count vs. Complexity

| Tools | Typical use case |
|-------|-----------------|
| 2-4 | Simple Q&A, single-domain queries |
| 5-8 | Multi-step investigations (this week) |
| 8-15 | Complex workflows across systems |
| 15+ | Usually too many — consider splitting into sub-agents |

For the payment agent, 8 tools feels right. Beyond ~12, the agent starts making
suboptimal tool selections and the system prompt gets unwieldy.

## What I Observed Running the Agent

### Case 1 (Repeated failures — TXN_2001 + TXN_2003):
- Agent called 6 tools: payment_details x2, customer_profile, gateway_health, list_payments, create_alert
- Correctly identified: same card, same merchant, 5-minute window → escalation triggered
- Alert severity: "high" — appropriate

### Case 2 (High-value restricted card — TXN_2002):
- Agent called: payment_details, gateway_health, customer_profile, merchant_info, payment_logs, retry_recommendation
- Correctly concluded: restricted card → no retry, different card required
- Noted merchant had 1.2% chargeback rate (higher than average for travel)

## Patterns for Action Tools

```python
# Pattern: Gate action tools behind a confirmation in the prompt
"""
Only create_alert when ALL of these are true:
1. You have completed the full investigation
2. At least one escalation criterion is met
3. You are confident this is not a false positive
"""
```

This prevents the agent from alerting on every failure.

## Tomorrow

Day 9: **Tracing with LangSmith** — make the agent's reasoning observable
- Set up LangSmith project
- Trace every tool call and token
- Debug why the agent made a bad decision using trace replay
- Add custom metadata to traces (case_id, analyst_id)
