"""
Schema Definitions for Payment Investigation
Practice designing good data models
"""

from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


# Exercise 1: Design a schema for payment retry configuration
class RetryConfiguration(BaseModel):
    """
    YOUR TASK: Fill in the fields for a retry configuration
    
    Think about:
    - How long to wait between retries
    - How many times to retry
    - Whether to use exponential backoff
    - When to give up
    """
    # Add your fields here
    pass


# Exercise 2: Design a schema for fraud detection results
class FraudAnalysis(BaseModel):
    """
    YOUR TASK: Design a fraud detection result schema
    
    Should include:
    - Risk score (0-100)
    - Risk level (low/medium/high)
    - Specific fraud signals detected
    - Whether to block the payment
    - Recommended actions
    """
    # Add your fields here
    pass


# Exercise 3: Design a schema for payment gateway health check
class GatewayHealthStatus(BaseModel):
    """
    YOUR TASK: Design a health check result schema
    
    Should include:
    - Gateway name
    - Overall status (healthy/degraded/down)
    - Response time metrics
    - Error rate
    - Last successful transaction timestamp
    - Any active incidents
    """
    # Add your fields here
    pass


# Example of a well-designed schema (for reference)
class PaymentAttempt(BaseModel):
    """
    A single payment attempt with full details
    This is an example of good schema design
    """
    attempt_number: int = Field(ge=1, description="Which attempt this was (1, 2, 3...)")
    timestamp: datetime
    amount: float = Field(gt=0, description="Payment amount in dollars")
    currency: str = Field(min_length=3, max_length=3, description="ISO currency code")
    gateway: str = Field(description="Payment gateway used (stripe, adyen, etc)")
    payment_method: str = Field(description="Last 4 digits or method ID")
    
    status: Literal["pending", "succeeded", "failed", "cancelled"]
    
    # Error details (only if failed)
    error_code: str | None = None
    error_message: str | None = None
    error_category: Literal["network", "card", "fraud", "limits", "other"] | None = None
    
    # Performance metrics
    response_time_ms: int = Field(ge=0, description="Time taken for gateway response")
    
    # Additional context
    customer_ip: str | None = None
    user_agent: str | None = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "attempt_number": 1,
                "timestamp": "2024-02-14T10:20:12Z",
                "amount": 150.00,
                "currency": "USD",
                "gateway": "stripe",
                "payment_method": "card_4242",
                "status": "failed",
                "error_code": "card_declined",
                "error_message": "Insufficient funds",
                "error_category": "card",
                "response_time_ms": 1247
            }
        }


if __name__ == "__main__":
    print("Schema Design Best Practices:\n")
    print("1. Use descriptive field names")
    print("2. Add Field() descriptions for documentation")
    print("3. Use Literal types for enums (fixed set of values)")
    print("4. Use Optional (| None) for nullable fields")
    print("5. Add validation constraints (ge=0, min_length, etc)")
    print("6. Include examples in Config")
    print("\nSee PaymentAttempt above for a complete example!")
    
    # Print the JSON schema
    print("\n" + "=" * 80)
    print("PaymentAttempt JSON Schema:")
    print("=" * 80)
    print(json.dumps(PaymentAttempt.model_json_schema(), indent=2))