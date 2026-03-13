# Weekly Progress Tracker

## Week 1-2: Foundations
**Status**: In Progress
**Goal**: Complete prompt engineering fundamentals and build first multi-tool agent

**Completed**:
- [x] Day 1: Prompt engineering basics — prompts.py, examples.md
- [x] Day 2: Tool use/function calling — simple_tool_call.py (manual agentic loop)
- [x] Day 3: Structured outputs — schemas.py, structured_payment_query.py (Pydantic + tool-calling)
- [x] Day 4: LangChain setup — ChatAnthropic, ChatPromptTemplate, chains with `|` operator
- [x] Day 5: First agent — create_react_agent with 4 payment investigation tools
- [x] Day 6: ReAct pattern — deep dive, step tracing, prompt engineering comparison
- [ ] Day 7: Memory
- [ ] Day 8: Multi-tool agent
- [ ] Day 9: Tracing with LangSmith
- [ ] Day 10: Guardrails
- [ ] Weekend: UI

**Key Learnings**:
- Tool descriptions are as important as the tools themselves — agents reason from them
- Structured ReAct prompts (step-by-step protocol) dramatically outperform vague prompts
- The `@tool` decorator + LangGraph `create_react_agent` eliminates manual loop boilerplate
- Pydantic schemas + tool-calling = most reliable structured output approach

**Blockers**:
- None currently

---

## Week 3-5: Agent v1
**Status**: Not Started
...