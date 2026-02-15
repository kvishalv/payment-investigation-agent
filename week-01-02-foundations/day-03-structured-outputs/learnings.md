# Day 3 Learnings - Structured Outputs

**Date**: [Fill in]

## What I Learned

### Why Structured Outputs Matter
1. Makes Claude's responses programmatically usable
2. Ensures consistency across API calls
3. Easier to validate and test
4. Can feed directly into other systems

### Three Approaches to Structured Output
**Approach 1: Ask nicely in prompt**
- Pros:
- Cons:

**Approach 2: JSON mode with detailed schema**
- Pros:
- Cons:

**Approach 3: Tool calling with Pydantic**
- Pros:
- Cons:

**Which should I use?**


## Experiments

### Experiment 1: What happens if schema is too complex?
**Try**: Create a deeply nested schema with 5+ levels

**Result**:


### Experiment 2: Can Claude handle optional fields correctly?
**Try**: Make several fields optional and see if Claude includes them

**Result**:


## Schema Design Practice
```python
# My custom schemas

class MyCustomSchema(BaseModel):
    # What I designed
    pass
```

## Questions

1. How do I handle arrays of different types?
2. What's the max complexity Claude can handle?
3. Should I use Pydantic or plain JSON schemas?

## Key Takeaway

The best approach for my use case is: _____ because _____

## Tomorrow

Day 4: Setting up LangChain and building first agent!