# Day 10 Learnings - Guardrails

**Date**: 2026-03-13

## The Four Guardrail Layers

Production agents need protection at every boundary:

```
User query
    ↓ [Guardrail 1: Input validation]
Agent
    ↓ [Guardrail 2: Safe tools with retry/fallback]
Tool results → Agent reasoning
    ↓ [Guardrail 3: Output validation]
Structured result
    ↑ [Guardrail 4: Rate limiting — applied before input reaches agent]
```

## Guardrail 1: Input Validation

### Schema validation with Pydantic
```python
class InvestigationRequest(BaseModel):
    query: str = Field(min_length=10, max_length=2000)
    payment_ids: list[str] = Field(default=[], max_length=10)
    analyst_id: str = Field(min_length=1, max_length=50)
```
Catches malformed requests before they waste API tokens.

### Prompt injection detection
```python
INJECTION_PATTERNS = [
    r"ignore (previous|all|prior) instructions",
    r"you are now",
    r"pretend (you are|to be)",
]
```
Payment agents handle sensitive data — prompt injection is a real threat.
Regex is a lightweight first line of defense. For adversarial inputs, use
a dedicated classifier model as a second layer.

### ID format validation
```python
if not re.match(r"^TXN_[A-Z0-9]+$", pid):
    return False, f"Invalid payment ID format: {pid}"
```
Prevents garbage IDs from hitting the database/tool.

## Guardrail 2: Safe Tool Wrappers

The golden rule: **tools must never raise exceptions to the agent**.
```python
@tool
def get_payment_details(payment_id: str) -> str:
    try:
        return json.dumps(PAYMENT_DB[payment_id])
    except ConnectionError:
        return json.dumps({
            "error": "payment_service_unavailable",
            "message": "Try again in 30 seconds."
        })
```

If a tool raises an exception, the LangGraph agent will often halt or loop.
Return error JSON instead — the agent can reason about it ("service unavailable, I'll note this").

### Retry decorator for transient errors
```python
@with_retries(max_attempts=3, delay_seconds=0.5)
def _fetch_from_database(payment_id):
    # Transient failures (network, timeout) are retried automatically
    ...
```
Only retry transient errors (ConnectionError, TimeoutError), not logic errors.

## Guardrail 3: Output Validation

The agent returns free-form text. Before handing to downstream systems, validate:
```python
class InvestigationResult(BaseModel):
    root_cause: Literal["card_issue", "gateway_issue", "fraud_signal", "merchant_issue", "unknown"]
    risk_level: Literal["low", "medium", "high", "critical"]
    retry_recommended: bool
    # ...
```

If validation fails → return safe defaults or flag for manual review.

**Better approach (production)**: Force structured output via tool-calling (Day 3 pattern).
Have the agent call a `submit_investigation_result(...)` tool at the end — this
guarantees the output matches your schema because the tool schema enforces it.

## Guardrail 4: Rate Limiting

```python
class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests    # e.g., 10
        self.window_seconds = window_seconds  # e.g., 60
```

Sliding window per `analyst_id` prevents:
- A single analyst accidentally hammering the API
- Abuse / script-driven attacks
- Runaway cost from a bug in calling code

For production: use Redis for distributed rate limiting across multiple servers.

## Defense in Depth

No single guardrail is perfect. Layer them:

```
Rate limit  →  stops bulk abuse before it touches the model
Input validation  →  stops malformed/malicious queries
Safe tools  →  stops tool failures from crashing the agent
Output validation  →  stops bad data from reaching downstream systems
LangSmith tracing (Day 9)  →  detects patterns of bad outputs after the fact
```

## Guardrail Test Results

| Test | Expected | Result |
|------|---------|--------|
| Valid request | success | ✓ |
| Prompt injection | blocked | ✓ |
| Invalid payment ID | blocked | ✓ |
| Query too short | blocked | ✓ |
| Rate limit (4th req, limit=3) | blocked | ✓ |
| Tool connection error | graceful fallback | ✓ |

## What NOT to Guardrail

Don't over-engineer:
- Don't validate every word in the query (too brittle)
- Don't retry non-transient errors (pointless and slow)
- Don't rate limit too aggressively (frustrates legitimate use)
- Don't reject vague queries — let the agent ask for clarification

## Week 1-2 Complete!

We've now covered the full foundation:

| Day | Concept | Key File |
|-----|---------|---------|
| 1 | Prompt engineering | prompts.py |
| 2 | Tool use / agentic loop | simple_tool_call.py |
| 3 | Structured outputs | schemas.py |
| 4 | LangChain basics | langchain_intro.py |
| 5 | First agent | first_agent.py |
| 6 | ReAct pattern | react_deep_dive.py |
| 7 | Memory | memory_agent.py |
| 8 | Multi-tool agent | multi_tool_agent.py |
| 9 | Tracing | tracing_setup.py |
| 10 | Guardrails | guardrails.py |

## Next Week

Week 3-5: **Agent v1** — build the full payment investigation agent
- Real tool integrations (Stripe API, log aggregators)
- Structured investigation workflow graph
- Human-in-the-loop checkpoints
- Production-ready error handling
