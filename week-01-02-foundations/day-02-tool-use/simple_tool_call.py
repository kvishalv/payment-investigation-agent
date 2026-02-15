"""
Day 2: Tool Use / Function Calling
Goal: Learn how to give Claude tools it can call to get information
"""

from anthropic import Anthropic
import os
from dotenv import load_dotenv
import json

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Mock payment database
PAYMENT_DATABASE = {
    "TXN_12345": {
        "id": "TXN_12345",
        "status": "failed",
        "amount": 150.00,
        "currency": "USD",
        "customer_id": "CUST_789",
        "payment_method": "card_4242",
        "gateway": "stripe",
        "error_code": "insufficient_funds",
        "attempts": 3,
        "created_at": "2024-02-14T10:20:00Z",
        "last_attempt": "2024-02-14T10:23:45Z"
    },
    "TXN_67890": {
        "id": "TXN_67890",
        "status": "succeeded",
        "amount": 299.99,
        "currency": "USD",
        "customer_id": "CUST_456",
        "payment_method": "card_5555",
        "gateway": "stripe",
        "created_at": "2024-02-14T09:15:00Z"
    }
}

# Mock customer database
CUSTOMER_DATABASE = {
    "CUST_789": {
        "id": "CUST_789",
        "name": "Jane Doe",
        "email": "jane@example.com",
        "account_status": "active",
        "payment_methods": ["card_4242"],
        "total_failed_payments": 5,
        "total_successful_payments": 127
    },
    "CUST_456": {
        "id": "CUST_456",
        "name": "John Smith",
        "email": "john@example.com",
        "account_status": "active",
        "payment_methods": ["card_5555"],
        "total_failed_payments": 0,
        "total_successful_payments": 89
    }
}


def get_payment_status(payment_id: str) -> dict:
    """
    Mock function to get payment details
    In real life, this would query your database or API
    """
    print(f"[TOOL CALLED] get_payment_status({payment_id})")
    
    if payment_id in PAYMENT_DATABASE:
        return {
            "success": True,
            "data": PAYMENT_DATABASE[payment_id]
        }
    else:
        return {
            "success": False,
            "error": f"Payment {payment_id} not found"
        }


def get_customer_info(customer_id: str) -> dict:
    """
    Mock function to get customer details
    """
    print(f"[TOOL CALLED] get_customer_info({customer_id})")
    
    if customer_id in CUSTOMER_DATABASE:
        return {
            "success": True,
            "data": CUSTOMER_DATABASE[customer_id]
        }
    else:
        return {
            "success": False,
            "error": f"Customer {customer_id} not found"
        }


# Define tools for Claude
tools = [
    {
        "name": "get_payment_status",
        "description": "Retrieves detailed information about a specific payment transaction including status, amount, customer, and error details if failed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "payment_id": {
                    "type": "string",
                    "description": "The unique payment transaction ID (e.g., TXN_12345)"
                }
            },
            "required": ["payment_id"]
        }
    },
    {
        "name": "get_customer_info",
        "description": "Retrieves customer information including account status, payment history, and contact details.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "The unique customer ID (e.g., CUST_789)"
                }
            },
            "required": ["customer_id"]
        }
    }
]


def process_tool_call(tool_name: str, tool_input: dict) -> dict:
    """
    Route tool calls to the appropriate function
    """
    if tool_name == "get_payment_status":
        return get_payment_status(tool_input["payment_id"])
    elif tool_name == "get_customer_info":
        return get_customer_info(tool_input["customer_id"])
    else:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}


def investigate_payment_with_tools(query: str):
    """
    Main function: Let Claude use tools to investigate a payment issue
    """
    print(f"\n{'=' * 80}")
    print(f"USER QUERY: {query}")
    print(f"{'=' * 80}\n")
    
    messages = [{"role": "user", "content": query}]
    
    # Step 1: Initial request to Claude
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        tools=tools,
        messages=messages
    )
    
    print(f"Claude's initial response:")
    print(f"Stop reason: {response.stop_reason}\n")
    
    # Agentic loop: Keep going until Claude stops asking for tools
    while response.stop_reason == "tool_use":
        # Extract tool calls from response
        tool_calls = [block for block in response.content if block.type == "tool_use"]
        
        # Add Claude's response to messages
        messages.append({"role": "assistant", "content": response.content})
        
        # Execute each tool call
        tool_results = []
        for tool_call in tool_calls:
            print(f"Claude wants to call: {tool_call.name}")
            print(f"With input: {json.dumps(tool_call.input, indent=2)}\n")
            
            # Execute the tool
            result = process_tool_call(tool_call.name, tool_call.input)
            print(f"Tool result: {json.dumps(result, indent=2)}\n")
            
            # Format result for Claude
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_call.id,
                "content": json.dumps(result)
            })
        
        # Send tool results back to Claude
        messages.append({"role": "user", "content": tool_results})
        
        # Get Claude's next response
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            tools=tools,
            messages=messages
        )
        
        print(f"Claude's response after tools:")
        print(f"Stop reason: {response.stop_reason}\n")
    
    # Final response (no more tool calls)
    final_response = next(
        (block.text for block in response.content if hasattr(block, "text")),
        None
    )
    
    print(f"{'=' * 80}")
    print(f"FINAL ANALYSIS:")
    print(f"{'=' * 80}\n")
    print(final_response)
    print(f"\n{'=' * 80}\n")
    
    return final_response


if __name__ == "__main__":
    # Test case 1: Simple payment investigation
    investigate_payment_with_tools(
        "Why did payment TXN_12345 fail? Is this a pattern for this customer?"
    )
    
    print("\n" + "=" * 80)
    input("Press Enter to try another query...")
    print("=" * 80 + "\n")
    
    # Test case 2: Customer-focused query
    investigate_payment_with_tools(
        "Tell me about customer CUST_789's payment history and whether I should be concerned about their recent failures."
    )