# Day 9 Learnings - Tracing with LangSmith

**Date**: 2026-03-13

## Why Tracing Matters

Without tracing, debugging the agent looks like:
> "It gave the wrong answer... but why? Which tool call? Which reasoning step?"

With tracing, you see the full execution tree:
```
investigate-case-abc123 (1.2s, 1847 tokens)
├── ChatAnthropic [reasoning] (0.4s, 312 tokens)
├── get_payment_details → {"status": "failed", "error_code": "card_declined"}
├── check_gateway_health → {"status": "operational"}  ← agent stopped here!
└── ChatAnthropic [final answer] (0.6s, 298 tokens) ← skipped customer profile
```

Now you know: the agent didn't call `get_customer_profile`. Fix the prompt.

## Setup (3 env vars)

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=<from smith.langchain.com>
export LANGCHAIN_PROJECT=payment-investigation-agent
```

That's it. Every `agent.invoke()`, `chain.invoke()`, and `model.invoke()` is
automatically traced. No code changes needed.

## Four Tracing Patterns

### 1. Auto-tracing (set env vars, done)
```python
# Nothing to add — just set env vars
agent.invoke({"messages": [...]}, config)
# → appears in LangSmith automatically
```

### 2. Metadata + tags for filtering
```python
config = {
    "configurable": {"thread_id": case_id},
    "metadata": {"case_id": case_id, "analyst": "system"},  # searchable in UI
    "tags": ["payment", "fraud"],                            # for grouping
    "run_name": f"investigate-{case_id}",                    # readable name
}
```
Always add `metadata` — makes it easy to find runs for a specific case or analyst.

### 3. `@traceable` for non-LangChain code
```python
@traceable(name="classify-payment-failure")
def classify_failure(error_code, gateway_healthy, customer_risk) -> dict:
    # Pure Python — still shows up as a span in LangSmith
    ...
```
Use this for preprocessing, business logic, and post-processing steps.

### 4. `tracing_v2_enabled()` context manager
```python
with tracing_v2_enabled(project_name="payment-investigation-agent"):
    result = agent.invoke(...)
# Only traces what's inside the `with` block
```
Useful when you want tracing for specific runs only (e.g., production vs. dev).

## LangSmith Features to Use

| Feature | How to use | Why useful |
|---------|-----------|-----------|
| **Run search** | Filter by tag, metadata, date | Find all fraud investigations |
| **Trace replay** | Click any run, see full tree | Debug bad answers step-by-step |
| **Human feedback** | `client.create_feedback(run_id, score)` | Build evaluation dataset |
| **Datasets** | Save input/output pairs | Regression testing |
| **Playground** | Edit prompt, re-run trace | Prompt iteration |
| **Metrics** | Token usage, latency over time | Cost monitoring |

## Building an Evaluation Loop

```
Production runs → LangSmith traces
                      ↓
             Analysts rate answers (0-1)
                      ↓
             LangSmith dataset of good/bad examples
                      ↓
             Run evals on new prompt versions
                      ↓
             Deploy only when eval score improves
```

This is Week 6-7 (Evaluation & Guardrails). LangSmith tracing is the foundation.

## Token Cost Awareness

From traces you'll see token counts. Rough math for `claude-sonnet-4`:
- Input: ~$3 / 1M tokens
- Output: ~$15 / 1M tokens

A typical investigation (8 tool calls, ~3K input tokens, ~500 output tokens):
- ~$0.01 per investigation
- 10,000 investigations/month → ~$100/month

Track this in LangSmith → "Metrics" tab. Set alerts if cost spikes.

## Common Debugging Scenarios

| Symptom | What to look for in trace |
|---------|--------------------------|
| Agent skipped a tool | Missing span between reasoning steps |
| Agent called wrong tool | Check tool description vs. what was needed |
| Slow response | Find the slow span (usually a tool call timeout) |
| Hallucinated data | Tool result vs. what agent said — mismatch? |
| Infinite loop | Repeated tool call spans with same input |

## Tomorrow

Day 10: **Guardrails** — making the agent safe for production
- Input validation (reject malformed or malicious queries)
- Output validation (ensure structured output meets schema)
- Rate limiting and circuit breakers
- Graceful error handling when tools fail
