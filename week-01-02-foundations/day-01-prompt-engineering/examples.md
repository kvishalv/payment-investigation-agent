# Day 1: Prompt Engineering Examples

## What I'm Learning Today

The goal is to understand how different prompt styles affect Claude's responses for payment investigation tasks.

## Key Concepts

### 1. Clear and Direct Prompts
- Be specific about what you want
- Provide structure and format expectations
- Use examples when possible

### 2. System Prompts vs User Prompts
- **System prompts**: Set the context, role, and guidelines
- **User prompts**: The actual task/question

### 3. Few-Shot Learning
- Provide examples of input/output pairs
- Helps Claude understand the pattern you want
- Especially useful for consistent formatting

## Exercise: Compare Outputs

Run `prompts.py` and compare the five versions:

1. **v1 (Basic)**: Notice how the output might be inconsistent
2. **v2 (Structured)**: Better organization, but still vague
3. **v3 (Detailed)**: Clear expectations lead to better results
4. **v4 (With Context)**: System prompt adds expertise
5. **v5 (Few-Shot)**: Examples teach the exact pattern

## Your Task

Create a 6th version (`prompt_v6`) that:
- Combines the best parts of v4 and v5
- Adds a section for "Similar Past Incidents" (you can mock this)
- Includes confidence scores for your root cause analysis

## Questions to Reflect On

1. Which version gave the most useful output for a real investigation?
2. How would you modify these prompts for different failure types (fraud vs technical)?
3. What information is Claude hallucinating vs inferring from the log?

## Resources

- [Anthropic Prompt Engineering Guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)
- [Be Clear and Direct](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/be-clear-and-direct)
- [Use Examples](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/use-examples)