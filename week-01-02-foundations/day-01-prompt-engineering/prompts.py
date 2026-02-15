"""
Day 1: Prompt Engineering Practice
Goal: Learn to write clear, effective prompts for payment investigation tasks
"""

from anthropic import Anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Sample payment failure log for testing
SAMPLE_LOG = """
2024-02-14 10:23:45 [ERROR] Payment ID: TXN_12345
Status: FAILED
Amount: $150.00
Currency: USD
Payment Method: Credit Card ending in 4242
Gateway Response: INSUFFICIENT_FUNDS
Customer ID: CUST_789
Attempt: 3/3
Previous attempts:
  - 10:20:12: CARD_DECLINED (issuer_unavailable)
  - 10:21:34: TIMEOUT (network_error)
"""

def prompt_v1_basic(log: str) -> str:
    """
    Version 1: Basic prompt - too vague
    This will likely give inconsistent results
    """
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": f"Analyze this payment failure:\n\n{log}"}
        ]
    )
    return message.content[0].text


def prompt_v2_structured(log: str) -> str:
    """
    Version 2: More structured with clear expectations
    Better, but could be more specific
    """
    prompt = f"""Analyze this payment failure log and provide:
1. What happened
2. Why it failed
3. What to do next

Log:
{log}"""
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.content[0].text


def prompt_v3_detailed(log: str) -> str:
    """
    Version 3: Detailed with examples and constraints
    This follows Anthropic's best practices
    """
    prompt = f"""You are a payment systems expert analyzing transaction failures.

Analyze the following payment failure log and provide a structured investigation report.

Your analysis should include:
1. **Root Cause**: The primary reason for failure (be specific)
2. **Contributing Factors**: Any secondary issues that may have played a role
3. **Customer Impact**: How this affects the customer experience
4. **Recommended Actions**: Specific next steps, prioritized
5. **Prevention**: How to prevent similar failures

Guidelines:
- Be concise but thorough
- Cite specific evidence from the logs
- If something is unclear, state what additional information you'd need
- Consider both technical and business perspectives

Payment Failure Log:
{log}

Provide your analysis:"""
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.content[0].text


def prompt_v4_with_context(log: str) -> str:
    """
    Version 4: Adding system context and examples
    Most effective for consistent results
    """
    system_prompt = """You are an expert payment systems investigator with 10+ years of experience.
    
Your expertise includes:
- Payment gateway integrations (Stripe, Adyen, Braintree)
- Common failure patterns and their root causes
- Customer communication best practices
- Fraud detection and prevention

When analyzing payment failures:
1. Look for patterns across multiple attempts
2. Consider both technical and business factors
3. Prioritize customer experience in your recommendations
4. Be specific about next steps"""

    user_prompt = f"""Analyze this payment failure and provide a detailed investigation report.

Here's an example of the format I expect:

Example Input:
2024-02-10 14:30:00 [ERROR] Payment TXN_999
Status: FAILED
Gateway Response: CARD_EXPIRED

Example Output:
**Root Cause**: Card expiration
**Contributing Factors**: No automated retry with updated card details
**Customer Impact**: HIGH - Failed purchase, likely frustration
**Recommended Actions**:
1. Send automated email requesting card update
2. Retry payment in 24h if card updated
3. Flag account for follow-up if no response in 3 days
**Prevention**: Implement pre-expiration reminders 30 days before card expiry

Now analyze this actual failure:

{log}"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )
    return message.content[0].text


def prompt_v5_with_few_shot(log: str) -> str:
    """
    Version 5: Few-shot learning with multiple examples
    Best for teaching specific patterns
    """
    system_prompt = """You are a payment systems expert. Analyze payment failures and provide structured investigation reports."""

    user_prompt = f"""I'll show you examples of how to analyze payment failures, then you'll analyze a new one.

Example 1:
Input Log:
2024-01-15 09:00:00 [ERROR] Payment TXN_111
Gateway Response: INVALID_CVV
Attempts: 1/3

Analysis:
**Root Cause**: Incorrect CVV code entered by customer
**Severity**: LOW - User error, easily recoverable
**Next Steps**: Prompt customer to re-enter CVV, no further investigation needed
**Pattern**: Isolated incident, not a systemic issue

Example 2:
Input Log:
2024-01-20 15:45:00 [ERROR] Payment TXN_222
Gateway Response: GATEWAY_TIMEOUT
Attempts: 3/3 (all timeouts)
Duration: Each attempt took >30s

Analysis:
**Root Cause**: Payment gateway experiencing latency issues
**Severity**: HIGH - Affects multiple customers likely
**Next Steps**: 
1. Check gateway status page
2. Contact gateway support
3. Consider failover to backup gateway
4. Monitor error rates across all transactions
**Pattern**: Multiple consecutive timeouts suggest infrastructure issue

Now analyze this payment failure:

{log}

Provide your analysis in the same format:"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )
    return message.content[0].text


if __name__ == "__main__":
    print("=" * 80)
    print("DAY 1: PROMPT ENGINEERING PRACTICE")
    print("=" * 80)
    print("\nSample Log:")
    print(SAMPLE_LOG)
    print("\n" + "=" * 80)
    
    # Test each version
    versions = [
        ("v1: Basic", prompt_v1_basic),
        ("v2: Structured", prompt_v2_structured),
        ("v3: Detailed", prompt_v3_detailed),
        ("v4: With Context", prompt_v4_with_context),
        ("v5: Few-Shot", prompt_v5_with_few_shot),
    ]
    
    for name, func in versions:
        print(f"\n{'=' * 80}")
        print(f"TESTING: {name}")
        print(f"{'=' * 80}\n")
        result = func(SAMPLE_LOG)
        print(result)
        print("\n" + "-" * 80)
        input("\nPress Enter to continue to next version...")