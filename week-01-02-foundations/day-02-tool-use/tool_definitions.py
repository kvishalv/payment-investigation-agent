"""
Tool Definitions Reference
Learn how to write good tool descriptions
"""

# GOOD EXAMPLE: Clear, specific, tells Claude when to use it
GOOD_TOOL_DEFINITION = {
    "name": "query_payment_logs",
    "description": """Searches payment system logs for specific transactions, error patterns, or time ranges.
    
Use this tool when you need to:
- Find all failed payments in a time period
- Search for specific error codes or patterns
- Investigate payment gateway issues
- Analyze retry attempts and their outcomes

Returns structured log entries with timestamps, error details, and context.""",
    "input_schema": {
        "type": "object",
        "properties": {
            "search_query": {
                "type": "string",
                "description": "What to search for (e.g., 'insufficient_funds', 'TXN_12345', 'timeout errors')"
            },
            "start_time": {
                "type": "string",
                "description": "Start of time range in ISO format (e.g., '2024-02-14T00:00:00Z'). Optional."
            },
            "end_time": {
                "type": "string",
                "description": "End of time range in ISO format. Optional."
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of log entries to return. Default: 50, Max: 500"
            }
        },
        "required": ["search_query"]
    }
}

# BAD EXAMPLE: Vague, doesn't help Claude know when to use it
BAD_TOOL_DEFINITION = {
    "name": "get_logs",
    "description": "Gets logs from the system",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "params": {"type": "object"}
        }
    }
}

# EXERCISE: Write your own tool definition
# Task: Define a tool called "check_gateway_status" that checks if a payment gateway is healthy

YOUR_TOOL_DEFINITION = {
    "name": "check_gateway_status",
    "description": """[YOUR DESCRIPTION HERE]
    
    Think about:
    - What does this tool do?
    - When should Claude use it?
    - What information does it return?
    """,
    "input_schema": {
        "type": "object",
        "properties": {
            # Define your parameters here
        },
        "required": []
    }
}

# More tool examples for practice
ADDITIONAL_TOOLS = [
    {
        "name": "calculate_retry_strategy",
        "description": """Calculates optimal retry timing for failed payments based on error type and customer history.
        
Use this when you need to determine:
- How long to wait before retrying a failed payment
- Whether to use exponential backoff
- Maximum number of retry attempts
- Whether to notify the customer before retrying

Takes into account error codes, customer payment history, and time sensitivity.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "error_code": {
                    "type": "string",
                    "description": "The payment error code (e.g., 'insufficient_funds', 'card_declined')"
                },
                "customer_id": {
                    "type": "string",
                    "description": "Customer ID to check payment history"
                },
                "amount": {
                    "type": "number",
                    "description": "Payment amount in dollars"
                },
                "urgency": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Business urgency: low=subscription renewal, medium=one-time purchase, high=critical service"
                }
            },
            "required": ["error_code"]
        }
    }
]

if __name__ == "__main__":
    print("Tool Definition Best Practices:\n")
    print("1. **Name**: Use clear, action-oriented names (query_*, get_*, check_*, calculate_*)")
    print("2. **Description**: Explain WHAT it does and WHEN to use it")
    print("3. **Parameters**: Document each field with examples")
    print("4. **Required fields**: Only mark fields as required if truly necessary")
    print("\nCompare GOOD vs BAD examples above to see the difference!")