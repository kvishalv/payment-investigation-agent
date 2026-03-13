# Day 4 Learnings - LangChain Basics

**Date**: 2026-03-13

## Core Concepts

### Why LangChain?
- Provides higher-level abstractions over raw API calls
- Makes chaining steps clean with the `|` pipe operator
- Built-in streaming, retries, output parsers, and more
- Same patterns work across different LLMs (swap Claude for GPT with one line)

### Key Building Blocks

| Component | What it does | Payment example |
|-----------|-------------|-----------------|
| `ChatAnthropic` | Wraps Claude API | `model = ChatAnthropic(model="claude-sonnet-4-20250514")` |
| `ChatPromptTemplate` | Reusable, parameterized prompts | Template with `{error_code}` slots |
| `StrOutputParser` | Extracts text from response | Get plain string from AIMessage |
| `chain = A \| B \| C` | Pipe components together | `prompt \| model \| parser` |

### The Pipe Operator `|`
```python
# Each step's output feeds the next
chain = prompt | model | parser

# Equivalent to:
formatted = prompt.invoke(inputs)
response = model.invoke(formatted)
result = parser.invoke(response)
```

### PromptTemplate vs raw strings
```python
# BAD: copy-pasting prompts for each error code
response1 = model.invoke(f"Explain insufficient_funds for Stripe...")
response2 = model.invoke(f"Explain card_declined for Adyen...")

# GOOD: template once, reuse many times
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a payment support specialist."),
    ("human", "Explain '{error_code}' for {gateway}.")
])
chain = prompt | model | StrOutputParser()
result = chain.invoke({"error_code": "insufficient_funds", "gateway": "Stripe"})
```

## Experiments to Try

### Experiment 1: What happens if a template variable is missing?
```python
chain.invoke({"error_code": "card_declined"})  # missing {gateway}
# Result: ___
```

### Experiment 2: Batch processing
```python
# LangChain can run multiple inputs in parallel
inputs = [
    {"error_code": "insufficient_funds", "gateway": "Stripe"},
    {"error_code": "card_declined", "gateway": "Adyen"},
]
results = chain.batch(inputs)
# Useful for: analyzing many failed payments at once
```

### Experiment 3: Add temperature
```python
model = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
# temperature=0 → deterministic, consistent classification
# temperature=1 → more creative, varied explanations
```

## Questions

1. When should I use LangChain vs raw Anthropic SDK?
   - LangChain: when building pipelines, need streaming, batching, or LLM-agnostic code
   - Raw SDK: when you need fine-grained control or LangChain's abstraction gets in the way

2. How do I handle errors in a chain?
   - Wrap `chain.invoke()` in try/except
   - Or use `.with_fallbacks()` for automatic retry with different model

3. What's `RunnableParallel` for?
   - Run multiple chains simultaneously and merge results
   - E.g., classify fraud AND generate customer message at the same time

## Key Takeaway

LangChain's `|` pipe makes it easy to compose: **classify → investigate → summarize**.
This is the foundation for the full payment investigation agent.

## Tomorrow

Day 5: Build the first full agent with LangChain tools!
- `create_react_agent` from `langgraph`
- Give the agent tools: `get_payment_status`, `get_customer_info`, `check_gateway_health`
- The agent decides which tools to call and in what order
