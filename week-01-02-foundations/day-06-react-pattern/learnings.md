# Day 6 Learnings - ReAct Pattern

**Date**: 2026-03-13

## What is ReAct?

ReAct = **Re**ason + **Act** — a prompting pattern where the model alternates between:
- **Thought**: Internal reasoning about what to do next
- **Action**: Calling a tool
- **Observation**: Reading the tool result
- ...repeat until ready to answer

```
Thought: I need to check the payment first
Action: get_payment_details("TXN_A001")
Observation: {"status": "failed", "customer_id": "CUST_101", ...}

Thought: Let me look at this customer's profile and all their payments
Action: get_customer_profile("CUST_101")
Observation: {"account_age_days": 14, "total_successful_payments": 0, ...}

Thought: New account, no successes, multiple fails — check fraud signals
Action: get_fraud_signals("CUST_101")
Observation: {"risk_level": "high", "signal_count": 5, ...}

Answer: This is high-confidence fraud. Recommend account suspension.
```

## Key Insight: Prompt Quality = Agent Quality

Comparing basic vs structured prompt on the same query:

| | Basic Prompt | Structured ReAct Prompt |
|--|--|--|
| Tools called | 1-2 | 4-5 |
| Fraud signals checked | No | Yes |
| Velocity analysis | No | Yes |
| Confidence stated | Never | Always |
| Actionable output | Vague | Specific |

**The model is the same. The prompt is the lever.**

## ReAct Protocol for Payment Investigation

```
1. GATHER (never skip this)
   └─ get_payment_details → customer_id, gateway, error_code
   └─ get_customer_profile → risk signals
   └─ check_gateway_health → rule out infrastructure

2. PATTERN SEARCH (if anything looks off)
   └─ get_all_customer_payments → velocity check
   └─ get_fraud_signals → automated risk score

3. REASON EXPLICITLY
   └─ List 2-3 hypotheses
   └─ Match evidence to each
   └─ Pick most supported

4. OUTPUT (structured)
   └─ Root cause category
   └─ Evidence list
   └─ Risk level
   └─ Recommended action
   └─ Confidence + why
```

## Prompting Techniques That Improve Reasoning

### 1. Step numbering
Forces sequential, complete reasoning instead of jumping to conclusions.

### 2. Require alternatives
"Before settling on root cause, list 2 alternative explanations."
Prevents confirmation bias — the agent considers edge cases.

### 3. Require confidence + reason
"State your confidence (%) and explain why."
Makes uncertainty explicit, which helps humans calibrate trust.

### 4. Protocol/checklist format
Agents follow structured protocols better than open-ended instructions.
Treat the system prompt like an SOP document.

### 5. Output templates
Define the exact format — `**Root Cause**: [card_issue | gateway_issue | fraud]`
Makes downstream parsing reliable.

## Failure Modes to Watch

| Failure | Example | Fix |
|---------|---------|-----|
| Premature conclusion | Answers after 1 tool call | Add "gather ALL data before concluding" |
| Tool loop | Calls same tool 3 times | Add dedup logic or output format hint |
| Hallucinated data | Makes up transaction amounts | "Only state facts from tool results" |
| Vague action | "Contact support" | "Specify which team and what info to send" |

## Observations from Today

- **CUST_101 case**: Structured prompt correctly identified fraud with 5 signals
- Basic prompt stopped after 2 tool calls and gave a vague answer
- Velocity pattern (3 attempts in 4 minutes) only surfaced with structured prompt

## Questions

1. Can I add explicit "Thought:" labels to make reasoning visible?
   → Yes — add `"Think step by step. Start each reasoning step with 'Thought:'"` to system prompt

2. How do I prevent the agent from calling too many tools?
   → Add a tool budget: `"Use at most 6 tool calls per investigation"`

3. What if the agent needs to ask the user a clarifying question?
   → Use a `ask_human` tool that routes control back to the user (LangGraph supports this)

## Tomorrow

Day 7: **Memory** — making the agent remember past investigations
- `MemorySaver` for within-session memory
- Summarization for long conversation histories
- Cross-session memory patterns
