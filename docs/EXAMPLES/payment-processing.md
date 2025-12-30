# Payment Processing Example

Complete example showing how to process payments using NexaFi.

## Overview

This example covers:

- Adding payment methods
- Processing transactions
- Handling different payment types
- Error handling
- Webhook integration

## Prerequisites

- Active NexaFi account
- API access token
- Test payment method (use card 4242424242424242 for testing)

## Example Code

### Adding a Payment Method

```python
import requests

BASE_URL = "http://localhost:5000/api/v1"
API_TOKEN = "your-access-token"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Add credit card
payment_method_data = {
    "type": "card",
    "card_number": "4242424242424242",  # Test card
    "exp_month": 12,
    "exp_year": 2025,
    "cvc": "123",
    "cardholder_name": "John Doe"
}

response = requests.post(
    f"{BASE_URL}/payment-methods",
    headers=headers,
    json=payment_method_data
)

if response.status_code == 201:
    payment_method = response.json()
    print(f"Payment method added: {payment_method['id']}")
    print(f"Last 4 digits: {payment_method['card']['last4']}")
else:
    print(f"Error: {response.status_code}")
```

### Processing a Transaction

```python
def process_payment(amount, currency, payment_method_id, description):
    """Process a payment transaction"""

    transaction_data = {
        "amount": amount,
        "currency": currency,
        "payment_method_id": payment_method_id,
        "description": description,
        "metadata": {
            "order_id": "order_12345",
            "customer_id": "cust_67890"
        },
        "idempotency_key": f"payment_{amount}_{int(time.time())}"
    }

    response = requests.post(
        f"{BASE_URL}/transactions",
        headers=headers,
        json=transaction_data
    )

    if response.status_code == 200:
        transaction = response.json()
        print(f"✅ Payment successful!")
        print(f"   Transaction ID: {transaction['id']}")
        print(f"   Amount: ${transaction['amount']}")
        print(f"   Status: {transaction['status']}")
        return transaction
    else:
        error = response.json()
        print(f"❌ Payment failed: {error['error']['message']}")
        return None

# Usage
transaction = process_payment(
    amount=250.00,
    currency="USD",
    payment_method_id="pm_abc123",
    description="Invoice #1234 payment"
)
```

### Checking Transaction Status

```python
def check_transaction_status(transaction_id):
    """Check status of a transaction"""

    response = requests.get(
        f"{BASE_URL}/transactions/{transaction_id}",
        headers=headers
    )

    if response.status_code == 200:
        transaction = response.json()

        status_emoji = {
            'succeeded': '✅',
            'pending': '⏳',
            'failed': '❌',
            'refunded': '↩️'
        }

        emoji = status_emoji.get(transaction['status'], '❓')

        print(f"{emoji} Transaction: {transaction['id']}")
        print(f"   Status: {transaction['status']}")
        print(f"   Amount: ${transaction['amount']}")
        print(f"   Created: {transaction['created_at']}")

        return transaction
    else:
        print(f"Transaction not found: {transaction_id}")
        return None
```

## Complete Payment Flow

```python
import time

class PaymentProcessor:
    def __init__(self, api_token):
        self.base_url = "http://localhost:5000/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

    def add_card(self, card_data):
        """Add credit card payment method"""
        response = requests.post(
            f"{self.base_url}/payment-methods",
            headers=self.headers,
            json=card_data
        )
        return response.json() if response.status_code == 201 else None

    def process_payment(self, amount, payment_method_id, **kwargs):
        """Process payment with retry logic"""
        max_retries = 3

        for attempt in range(max_retries):
            try:
                transaction_data = {
                    "amount": amount,
                    "currency": kwargs.get('currency', 'USD'),
                    "payment_method_id": payment_method_id,
                    "description": kwargs.get('description', ''),
                    "metadata": kwargs.get('metadata', {}),
                    "idempotency_key": kwargs.get('idempotency_key')
                }

                response = requests.post(
                    f"{self.base_url}/transactions",
                    headers=self.headers,
                    json=transaction_data,
                    timeout=30
                )

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limit
                    wait_time = 2 ** attempt
                    print(f"Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"Payment failed: {response.json()}")
                    return None

            except requests.exceptions.Timeout:
                print(f"Timeout on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)

        return None

    def refund_payment(self, transaction_id, amount=None, reason=None):
        """Refund a transaction"""
        refund_data = {
            "transaction_id": transaction_id,
            "reason": reason or "Customer request"
        }

        if amount:
            refund_data["amount"] = amount  # Partial refund

        response = requests.post(
            f"{self.base_url}/refunds",
            headers=self.headers,
            json=refund_data
        )

        return response.json() if response.status_code == 200 else None

# Usage
processor = PaymentProcessor(API_TOKEN)

# Add payment method
card = processor.add_card({
    "type": "card",
    "card_number": "4242424242424242",
    "exp_month": 12,
    "exp_year": 2025,
    "cvc": "123"
})

if card:
    # Process payment
    transaction = processor.process_payment(
        amount=100.00,
        payment_method_id=card['id'],
        description="Product purchase",
        metadata={"product_id": "prod_123"}
    )

    if transaction:
        print(f"Payment successful: {transaction['id']}")
```

## Webhook Integration

```python
from flask import Flask, request
import hmac
import hashlib

app = Flask(__name__)
WEBHOOK_SECRET = "your-webhook-secret"

def verify_webhook_signature(payload, signature):
    """Verify webhook signature"""
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

@app.route('/webhooks/nexafi', methods=['POST'])
def handle_webhook():
    """Handle NexaFi webhooks"""
    payload = request.get_data(as_text=True)
    signature = request.headers.get('X-NexaFi-Signature')

    if not verify_webhook_signature(payload, signature):
        return 'Invalid signature', 401

    event = request.get_json()

    if event['type'] == 'transaction.succeeded':
        # Handle successful payment
        transaction = event['data']['transaction']
        print(f"Payment succeeded: {transaction['id']}")
        # Update order status, send confirmation email, etc.

    elif event['type'] == 'transaction.failed':
        # Handle failed payment
        transaction = event['data']['transaction']
        print(f"Payment failed: {transaction['id']}")
        # Notify customer, retry logic, etc.

    return 'OK', 200

if __name__ == '__main__':
    app.run(port=5555)
```

## Error Handling

```python
class PaymentError(Exception):
    """Base payment error"""
    pass

class InsufficientFundsError(PaymentError):
    """Insufficient funds"""
    pass

class InvalidCardError(PaymentError):
    """Invalid card details"""
    pass

def handle_payment_error(error_response):
    """Handle payment errors gracefully"""
    error_code = error_response.get('error', {}).get('code')
    error_message = error_response.get('error', {}).get('message')

    error_map = {
        'insufficient_funds': InsufficientFundsError,
        'invalid_card': InvalidCardError,
        'card_declined': PaymentError
    }

    error_class = error_map.get(error_code, PaymentError)
    raise error_class(error_message)

# Usage
try:
    transaction = process_payment(...)
    if not transaction:
        handle_payment_error(response.json())
except InsufficientFundsError:
    print("Insufficient funds. Please add funds and try again.")
except InvalidCardError:
    print("Invalid card details. Please check and try again.")
except PaymentError as e:
    print(f"Payment error: {e}")
```

## Testing

```python
# Test cards
TEST_CARDS = {
    'success': '4242424242424242',
    'decline': '4000000000000002',
    'insufficient_funds': '4000000000009995',
    'expired': '4000000000000069'
}

def run_payment_tests():
    """Run payment processing tests"""
    processor = PaymentProcessor(API_TOKEN)

    # Test successful payment
    card = processor.add_card({
        "type": "card",
        "card_number": TEST_CARDS['success'],
        "exp_month": 12,
        "exp_year": 2025,
        "cvc": "123"
    })

    transaction = processor.process_payment(
        amount=10.00,
        payment_method_id=card['id']
    )

    assert transaction['status'] == 'succeeded'
    print("✅ Payment test passed")

if __name__ == '__main__':
    run_payment_tests()
```

---
