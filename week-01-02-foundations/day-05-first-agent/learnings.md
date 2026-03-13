# Day 5 Learnings - First LangChain Agent

**Date**: 2026-03-13

## The Leap: Manual Loop → Agent

On Day 2, we managed the tool-calling loop ourselves:
```python
while response.stop_reason == "tool_use":
    # extract tool calls
    # run tools
    # append results
    # call Claude again
```

Today, LangGraph does all of that for us:
```python
agent = create_react_agent(model, tools, prompt=system_prompt)
result = agent.invoke({"messages": [("user", query)]})
```

## Key Concepts

### `@tool` decorator
Converts a Python function into a LangChain tool:
- Docstring becomes the tool description Claude reads
- Type hints inform the input schema
- Return value (string) goes back to Claude as the tool result

```python
@tool
def get_payment_details(payment_id: str) -> str:
    """
    Retrieve full details for a payment transaction.  ← Claude reads this
    """
    return json.dumps(PAYMENT_DB.get(payment_id, {"error": "not found"}))
```

### `create_react_agent`
- Implements the ReAct pattern (Reason + Act) automatically
- Takes: model, list of tools, optional system prompt
- Returns a runnable graph you can `.invoke()` or `.stream()`

### Streaming agent steps
```python
for step in agent.stream({"messages": [...]}, stream_mode="values"):
    last_msg = step["messages"][-1]
    # AIMessage = Claude thinking/responding
    # ToolMessage = tool result returned to Claude
```

## Good Tool Design Principles

1. **One job per tool** — `get_payment_details` only gets payment data
2. **Descriptive docstrings** — Claude uses these to decide when to call the tool
3. **Return strings** — serialize dicts with `json.dumps()`
4. **Handle missing data gracefully** — return error JSON, don't raise exceptions
5. **Tell Claude how to chain tools** — "Use this *after* finding the customer_id"

## Observations from Running the Agent

### Test 1 (TXN_12345 — insufficient_funds):
- Agent called: `get_payment_details` → `get_customer_profile` → `check_gateway_health`
- Stripe was healthy, so it correctly attributed failure to card issue
- Noted customer has 5 past failures — good pattern recognition

### Test 2 (TXN_99999 — fraud flag):
- Agent called: `get_payment_details` → `get_customer_profile` → `list_customer_transactions`
- Spotted: $5,000 unusual amount, new payment method, on degraded gateway
- Recommended manual review — appropriate caution

### Test 3 (Gateway spike):
- Agent proactively checked Adyen health without being asked for TXN details
- Correctly identified gateway incident as primary cause

## What Could Go Wrong

| Problem | Symptom | Fix |
|---------|---------|-----|
| Vague tool description | Agent calls wrong tool | Write clearer docstrings |
| Tool returns exception | Agent halts | Catch exceptions, return error JSON |
| Too many tools | Agent gets confused | Keep to 5-7 tools max |
| Missing data in DB | Agent loops | Return explicit "not found" message |

## Questions

1. How does the agent decide which tool to call first?
   → It reasons about the query and tool descriptions, starting with the most relevant

2. What if I want the agent to always call tools in a specific order?
   → You can hint in the system prompt, or use a custom graph in LangGraph

3. How do I add memory so the agent remembers past investigations?
   → Day 7! We'll add `MemorySaver` checkpointer

## Tomorrow

Day 6: Deep dive into the **ReAct pattern**
- Understand Thought → Action → Observation cycles
- Trace the agent's reasoning step by step
- Learn to prompt the agent to reason better
