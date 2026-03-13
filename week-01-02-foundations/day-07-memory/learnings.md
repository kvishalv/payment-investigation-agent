# Day 7 Learnings - Memory

**Date**: 2026-03-13

## Why Memory Matters

Without memory, every follow-up question resets the agent:
```
Turn 1: "Investigate TXN_A001" → agent fetches payment + customer + history
Turn 2: "What about that customer's other payments?"
         → without memory: "Which customer?" (re-fetches everything)
         → with memory: uses CUST_101 already in context
```

This doubles API calls and makes the agent feel stateless and frustrating.

## Three Memory Patterns

### 1. In-Session Memory (`MemorySaver`)
```python
checkpointer = MemorySaver()
agent = create_react_agent(model, tools, checkpointer=checkpointer)

# Same thread_id = same memory
config = {"configurable": {"thread_id": "case-101"}}
agent.invoke({"messages": [...]}, config)
```
- Stores full message history for a `thread_id`
- Memory is lost when the process restarts (in-memory only)
- Use for: conversation continuity within a single session

### 2. Cross-Session Memory (saved notes tool)
```python
@tool
def save_investigation_note(case_id: str, note: str) -> str:
    """Save key findings for future sessions."""
    NOTES[case_id].append(note)
```
- Agent explicitly writes findings to a store
- Survives process restarts
- Scales to: Redis, Postgres, S3 for production
- Use for: handoffs between analysts, long-running cases

### 3. Conversation Summarization
For very long investigations, the message history gets large and expensive.
Strategy: Summarize older turns and keep recent turns verbatim.
```python
# Pattern: keep last N messages + summary of older ones
# LangGraph has built-in support via custom state reducers
# We'll implement this in Week 3-5 for production use
```

## `thread_id` — The Memory Key

```python
config = {"configurable": {"thread_id": "case-CUST_101-2024-02-14"}}
```
Design decisions:
- `thread_id` per case → all turns about one case share memory
- `thread_id` per analyst session → fresh start each day
- `thread_id` per transaction → fine-grained isolation

**Recommendation for payment agents**: `thread_id = f"case-{customer_id}"` so all
analysts working on the same customer see the same investigation history.

## Inspecting Memory State
```python
state = agent.get_state(config)
messages = state.values["messages"]
# Full message history — HumanMessage, AIMessage, ToolMessage
```
Use this for debugging when the agent seems confused about context.

## Memory Anti-Patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| Unbounded history | Context window fills up, costs rise | Summarize or trim old messages |
| One thread for everything | Unrelated cases pollute each other | Use case-scoped thread IDs |
| Saving tool results to notes | Notes get huge and unreadable | Save only key conclusions |
| No memory at all | Every turn starts from scratch | Use MemorySaver at minimum |

## The `save_investigation_note` Tool

A key insight: memory tools should be first-class tools the agent can call.
The agent decides *what* to remember, not you.
This is more flexible than automatically storing everything.

Good notes to save:
- "CUST_101 is high fraud risk — account 14 days old, 3 failed payments, 0 successful"
- "Adyen had an incident on 2024-02-14 10:45-14:00 UTC"

Bad notes (too verbose, should stay in conversation history):
- The full JSON output of every tool call

## Questions

1. What happens when MemorySaver fills up?
   → It's bounded by RAM. For production, use `AsyncPostgresSaver` or `RedisSaver`

2. Can two agents share the same memory?
   → Yes — if they use the same checkpointer and thread_id. Useful for handoffs.

3. How do I delete a thread's memory?
   → `checkpointer.delete(config)` — useful for clearing test data

## Tomorrow

Day 8: **Multi-tool agent** — expand the toolset to a full payment investigation suite:
- Log querying tool
- Alert creation tool
- Merchant lookup tool
- More complex investigation scenarios
