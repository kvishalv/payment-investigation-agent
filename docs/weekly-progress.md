# Weekly Progress Tracker

## Week 1-2: Foundations
**Status**: Complete ✓
**Goal**: Complete prompt engineering fundamentals and build first multi-tool agent

**Completed**:
- [x] Day 1: Prompt engineering basics — prompts.py, examples.md
- [x] Day 2: Tool use/function calling — simple_tool_call.py (manual agentic loop)
- [x] Day 3: Structured outputs — schemas.py, structured_payment_query.py (Pydantic + tool-calling)
- [x] Day 4: LangChain setup — ChatAnthropic, ChatPromptTemplate, chains with `|` operator
- [x] Day 5: First agent — create_react_agent with 4 payment investigation tools
- [x] Day 6: ReAct pattern — deep dive, step tracing, prompt engineering comparison
- [x] Day 7: Memory — MemorySaver, thread_id scoping, cross-session notes tool
- [x] Day 8: Multi-tool agent — 8-tool suite, action vs query tools, escalation criteria
- [x] Day 9: Tracing with LangSmith — auto-tracing, @traceable, metadata/tags, eval loop
- [x] Day 10: Guardrails — input validation, prompt injection detection, safe tools, rate limiting, output validation
- [ ] Weekend: UI (Streamlit)

**Key Learnings**:
- Tool descriptions are as important as the tools themselves — agents reason from them
- Structured ReAct prompts (step-by-step protocol) dramatically outperform vague prompts
- The `@tool` decorator + LangGraph `create_react_agent` eliminates manual loop boilerplate
- Pydantic schemas + tool-calling = most reliable structured output approach
- MemorySaver + thread_id = in-session memory; explicit "save note" tool = cross-session
- 8 tools is near the upper bound before agent tool selection degrades
- LangSmith: set 3 env vars, everything is traced automatically
- Guardrail order: rate limit → input validation → safe tools → output validation
- Tools must never raise exceptions — always return error JSON

**Blockers**:
- None

---

## Week 3-5: Agent v1
**Status**: Not Started
...