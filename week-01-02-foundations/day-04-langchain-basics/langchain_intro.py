"""
Day 4: LangChain Basics
Goal: Learn LangChain's core abstractions and connect them to Claude

Key concepts today:
1. ChatAnthropic - LangChain's wrapper around Claude
2. PromptTemplate / ChatPromptTemplate - reusable prompt structures
3. Chains - connecting components with | (pipe operator)
4. Output parsers - structured outputs from LangChain
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# 1. Basic: ChatAnthropic model
# ─────────────────────────────────────────────
def example_1_basic_model():
    """Direct model call — same as anthropic SDK but wrapped in LangChain."""
    print("\n=== Example 1: Direct Model Call ===")

    model = ChatAnthropic(model="claude-sonnet-4-20250514")

    messages = [
        SystemMessage(content="You are a payment systems expert. Be concise."),
        HumanMessage(content="What are the top 3 reasons a card payment fails?")
    ]

    response = model.invoke(messages)
    print(response.content)


# ─────────────────────────────────────────────
# 2. PromptTemplate — reusable, parameterized prompts
# ─────────────────────────────────────────────
def example_2_prompt_template():
    """PromptTemplate lets you write prompts once and reuse with different inputs."""
    print("\n=== Example 2: Prompt Templates ===")

    model = ChatAnthropic(model="claude-sonnet-4-20250514")

    # Define a reusable template
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a payment support specialist. Be concise and helpful."),
        ("human", "Explain the error code '{error_code}' for {gateway} in plain English. "
                  "What should the customer do?")
    ])

    # Invoke with different inputs — no copy-pasting prompts
    for error_code, gateway in [
        ("insufficient_funds", "Stripe"),
        ("card_declined", "Adyen"),
        ("expired_card", "Braintree"),
    ]:
        chain = prompt | model | StrOutputParser()
        result = chain.invoke({"error_code": error_code, "gateway": gateway})
        print(f"\n[{gateway}] {error_code}:\n{result}")


# ─────────────────────────────────────────────
# 3. Chains — composing steps with the | operator
# ─────────────────────────────────────────────
def example_3_chains():
    """
    The pipe operator | connects components:
      prompt | model | parser
    Each step's output becomes the next step's input.
    """
    print("\n=== Example 3: Simple Chain ===")

    model = ChatAnthropic(model="claude-sonnet-4-20250514")
    parser = StrOutputParser()

    # Step 1: Classify the failure
    classify_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a payment analyst. Reply with ONE category only: "
                   "card_issue | network_issue | fraud | bank_issue | user_error"),
        ("human", "Payment failure: {failure_description}")
    ])

    # Step 2: Generate a resolution based on the classification
    resolve_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a payment support agent. Give a 2-sentence resolution."),
        ("human", "Payment failed due to: {category}\nCustomer context: {failure_description}")
    ])

    # Build each chain
    classify_chain = classify_prompt | model | parser
    resolve_chain = resolve_prompt | model | parser

    # Run them sequentially (manual chaining — good for learning)
    failure = "Customer's Visa card was declined at checkout for $299. They have used this card successfully before."

    print(f"\nFailure: {failure}")
    category = classify_chain.invoke({"failure_description": failure})
    print(f"Classification: {category}")

    resolution = resolve_chain.invoke({"category": category, "failure_description": failure})
    print(f"Resolution: {resolution}")


# ─────────────────────────────────────────────
# 4. Streaming — get tokens as they arrive
# ─────────────────────────────────────────────
def example_4_streaming():
    """Streaming is great for long analyses — show progress to the user."""
    print("\n=== Example 4: Streaming ===")

    model = ChatAnthropic(model="claude-sonnet-4-20250514")

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a payment fraud analyst."),
        ("human", "Write a brief (3 bullet) checklist for investigating a suspected fraud transaction.")
    ])

    chain = prompt | model | StrOutputParser()

    print("\nStreaming response:")
    for chunk in chain.stream({}):
        print(chunk, end="", flush=True)
    print()  # newline after stream


# ─────────────────────────────────────────────
# 5. Your turn — fill this in
# ─────────────────────────────────────────────
def exercise_build_your_chain():
    """
    EXERCISE: Build a chain that:
    1. Takes a payment_id and amount as input
    2. Generates a customer-friendly decline message
    3. Also suggests 2 alternative payment methods

    Hint: Use ChatPromptTemplate.from_messages() and pipe to model and StrOutputParser
    """
    print("\n=== Exercise: Build Your Own Chain ===")

    model = ChatAnthropic(model="claude-sonnet-4-20250514")

    # YOUR CODE HERE
    prompt = ChatPromptTemplate.from_messages([
        ("system", "TODO: write your system prompt"),
        ("human", "TODO: write your human prompt with {payment_id} and {amount}")
    ])

    chain = prompt | model | StrOutputParser()

    # Uncomment and run when ready:
    # result = chain.invoke({"payment_id": "TXN_12345", "amount": 150.00})
    # print(result)
    print("(exercise not yet implemented — fill in the TODOs above!)")


if __name__ == "__main__":
    example_1_basic_model()
    example_2_prompt_template()
    example_3_chains()
    example_4_streaming()
    exercise_build_your_chain()
