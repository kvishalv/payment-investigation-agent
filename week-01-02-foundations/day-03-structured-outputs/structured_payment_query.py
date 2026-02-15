"""
Day 3: Structured Outputs
Goal: Get Claude to return data in exact JSON schemas we define
"""

from anthropic import Anthropic
import os
from dotenv import load_dotenv
import json
from typing import Literal
from pydantic import BaseModel, Field

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# Define Pydantic models for structured outputs
class PaymentRootCause(BaseModel):
    """Root cause analysis of a payment failure"""
    primary_cause: str = Field(description="The main reason the payment failed")
    error_category: Literal["customer_error", "technical_error", "fraud", "insufficient_funds", "card_issue", "gateway_issue"]
    confidence: Literal["high", "medium", "low"] = Field(description="How confident are we in this analysis")
    contributing_factors: list[str] = Field(description="Other factors that may have contributed", default_factory=list)


class CustomerImpact(BaseModel):
    """Impact assessment on the customer"""
    severity: Literal["low", "medium", "high", "critical"]
    requires_immediate_action: bool
    customer_notification_needed: bool
    estimated_resolution_time: str = Field(description="e.g., '5 minutes', '24 hours', '3-5 days'")


class RecommendedAction(BaseModel):
    """A single recommended action"""
    action: str
    priority: Literal["immediate", "high", "medium", "low"]
    owner: Literal["customer_support", "engineering", "fraud_team", "automated_system"]
    estimated_time: str


class PaymentInvestigationReport(BaseModel):
    """Complete structured investigation report"""
    payment_id: str
    investigation_summary: str = Field(description="2-3 sentence summary of findings")
    root_cause: PaymentRootCause
    customer_impact: CustomerImpact
    recommended_actions: list[RecommendedAction]
    similar_incidents_count: int = Field(description="Estimated number of similar failures in last 30 days")
    should_escalate: bool
    additional_notes: str | None = None


# Sample log for testing
SAMPLE_LOG = """
2024-02-14 10:23:45 [ERROR] Payment ID: TXN_12345
Status: FAILED
Amount: $150.00
Currency: USD
Payment Method: Credit Card ending in 4242
Gateway Response: INSUFFICIENT_FUNDS
Customer ID: CUST_789
Customer Email: jane@example.com
Attempt: 3/3
Previous attempts:
  - 10:20:12: CARD_DECLINED (issuer_unavailable)
  - 10:21:34: TIMEOUT (network_error)
  - 10:23:45: INSUFFICIENT_FUNDS (final attempt)

Customer History:
- Total successful payments: 127
- Total failed payments: 5
- Account status: Active
- Last successful payment: 2024-02-10 (3 days ago)
"""


def analyze_payment_unstructured(log: str) -> str:
    """
    Version 1: No structure, Claude returns free-form text
    """
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": f"Analyze this payment failure and provide a detailed investigation report:\n\n{log}"
        }]
    )
    return response.content[0].text


def analyze_payment_structured(log: str) -> PaymentInvestigationReport:
    """
    Version 2: Using structured outputs with Pydantic models
    Claude MUST return data matching our exact schema
    """
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": f"""Analyze this payment failure and provide a structured investigation report.

Payment Log:
{log}

Return your analysis as a structured JSON object following this exact schema:
- payment_id: string
- investigation_summary: string (2-3 sentences)
- root_cause: object with primary_cause, error_category, confidence, contributing_factors
- customer_impact: object with severity, requires_immediate_action, customer_notification_needed, estimated_resolution_time
- recommended_actions: array of objects with action, priority, owner, estimated_time
- similar_incidents_count: integer estimate
- should_escalate: boolean
- additional_notes: string or null

Error category must be one of: customer_error, technical_error, fraud, insufficient_funds, card_issue, gateway_issue
Confidence must be: high, medium, or low
Severity must be: low, medium, high, or critical
Priority must be: immediate, high, medium, or low
Owner must be: customer_support, engineering, fraud_team, or automated_system

Respond ONLY with the JSON object, no other text."""
        }]
    )
    
    # Extract text and parse JSON
    text_response = response.content[0].text
    
    # Remove markdown code blocks if present
    if text_response.strip().startswith("```"):
        text_response = text_response.strip()
        text_response = text_response[text_response.find("{"):text_response.rfind("}")+1]
    
    # Parse into Pydantic model
    json_data = json.loads(text_response)
    return PaymentInvestigationReport(**json_data)


def analyze_payment_with_tool(log: str) -> PaymentInvestigationReport:
    """
    Version 3: Using tool calling for structured output
    This is more reliable than asking for JSON in the prompt
    """
    # Define a tool that accepts our structured output
    tools = [{
        "name": "submit_investigation_report",
        "description": "Submit a structured payment investigation report with root cause analysis and recommended actions",
        "input_schema": PaymentInvestigationReport.model_json_schema()
    }]
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        tools=tools,
        messages=[{
            "role": "user",
            "content": f"""Analyze this payment failure and submit a complete investigation report using the submit_investigation_report tool.

Be thorough in your analysis:
- Identify the root cause and contributing factors
- Assess customer impact and urgency
- Provide specific, actionable recommendations
- Estimate similar incident frequency

Payment Log:
{log}"""
        }]
    )
    
    # Extract tool call
    tool_use = next(block for block in response.content if block.type == "tool_use")
    
    # Parse into Pydantic model
    return PaymentInvestigationReport(**tool_use.input)


def pretty_print_report(report: PaymentInvestigationReport):
    """Print the report in a readable format"""
    print(f"\n{'=' * 80}")
    print(f"PAYMENT INVESTIGATION REPORT: {report.payment_id}")
    print(f"{'=' * 80}\n")
    
    print(f"**Summary**: {report.investigation_summary}\n")
    
    print(f"**Root Cause Analysis**")
    print(f"  Primary Cause: {report.root_cause.primary_cause}")
    print(f"  Category: {report.root_cause.error_category}")
    print(f"  Confidence: {report.root_cause.confidence}")
    if report.root_cause.contributing_factors:
        print(f"  Contributing Factors:")
        for factor in report.root_cause.contributing_factors:
            print(f"    - {factor}")
    print()
    
    print(f"**Customer Impact**")
    print(f"  Severity: {report.customer_impact.severity}")
    print(f"  Immediate Action Required: {report.customer_impact.requires_immediate_action}")
    print(f"  Notify Customer: {report.customer_impact.customer_notification_needed}")
    print(f"  Est. Resolution: {report.customer_impact.estimated_resolution_time}")
    print()
    
    print(f"**Recommended Actions** ({len(report.recommended_actions)})")
    for i, action in enumerate(report.recommended_actions, 1):
        print(f"  {i}. [{action.priority.upper()}] {action.action}")
        print(f"     Owner: {action.owner} | Time: {action.estimated_time}")
    print()
    
    print(f"**Additional Context**")
    print(f"  Similar Incidents (30d): ~{report.similar_incidents_count}")
    print(f"  Escalate: {'YES' if report.should_escalate else 'NO'}")
    if report.additional_notes:
        print(f"  Notes: {report.additional_notes}")
    
    print(f"\n{'=' * 80}\n")


if __name__ == "__main__":
    print("DAY 3: STRUCTURED OUTPUTS\n")
    
    # Version 1: Unstructured (for comparison)
    print("Testing Version 1: Unstructured output...")
    print("(This gives us text, but it's hard to parse programmatically)\n")
    unstructured = analyze_payment_unstructured(SAMPLE_LOG)
    print(unstructured)
    print("\n" + "=" * 80)
    input("\nPress Enter to try structured approach...")
    
    # Version 2: Structured with JSON in prompt
    print("\n\nTesting Version 2: Structured with JSON in prompt...")
    print("(Better, but Claude might not follow the schema exactly)\n")
    try:
        structured_prompt = analyze_payment_structured(SAMPLE_LOG)
        pretty_print_report(structured_prompt)
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        print("(This is why Version 3 is better!)")
    
    print("=" * 80)
    input("\nPress Enter to try tool-based approach...")
    
    # Version 3: Structured with tool calling
    print("\n\nTesting Version 3: Structured with tool calling...")
    print("(Most reliable - Claude must match the schema)\n")
    structured_tool = analyze_payment_with_tool(SAMPLE_LOG)
    pretty_print_report(structured_tool)
    
    # Show the raw JSON
    print("\nRaw JSON output:")
    print(json.dumps(structured_tool.model_dump(), indent=2))