# Usage Guide

Comprehensive guide for using NexaFi, covering common workflows, CLI usage, and library integration.

## Table of Contents

1. [Quick Start](#quick-start)
2. [CLI Usage](#cli-usage)
3. [Library Usage](#library-usage)
4. [Common Workflows](#common-workflows)
5. [API Integration](#api-integration)
6. [Best Practices](#best-practices)

---

## Quick Start

### 3-Step Quick Start

**Step 1: Start the API Gateway**

```bash
cd backend/api-gateway/src
python3 main.py
```

**Step 2: Verify the service**

```bash
curl http://localhost:5000/health
```

**Step 3: Make your first API call**

```bash
# Register a new user
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'
```

---

## CLI Usage

### Starting Services

**Start all backend services:**

```bash
cd backend
./start_services.sh
```

**Start individual services:**

```bash
# API Gateway
cd backend/api-gateway/src && python3 main.py

# User Service
cd backend/user-service/src && python3 main.py

# Payment Service
cd backend/payment-service/src && python3 main.py

# AI Service
cd backend/ai-service/src && python3 main.py
```

### Stopping Services

```bash
# Stop all services
cd backend
./stop_services.sh

# Or manually kill processes
pkill -f "python3 main.py"
```

### Testing Services

```bash
# Test all services
cd backend
python test_all_services.py

# Test imports
python test_imports.py

# Run comprehensive test suite
python test_suite.py
```

---

## Library Usage

### Python SDK Integration

**Install NexaFi Python SDK:**

```bash
pip install nexafi-sdk
```

**Basic usage:**

```python
from nexafi import NexaFi

# Initialize client
client = NexaFi(
    api_key="your-api-key",
    base_url="http://localhost:5000"
)

# Authenticate user
user = client.auth.login(
    email="user@example.com",
    password="SecurePass123!"
)

# Get account balance
accounts = client.ledger.list_accounts()
for account in accounts:
    print(f"Account: {account.name}, Balance: {account.balance}")

# Make a payment
payment = client.payments.create(
    amount=100.00,
    currency="USD",
    payment_method_id="pm_123456",
    description="Invoice payment"
)

# Get AI insights
insights = client.ai.get_cash_flow_forecast(days=30)
print(f"Projected cash flow: ${insights.projected_balance}")
```

### JavaScript/TypeScript SDK

**Install NexaFi JS SDK:**

```bash
npm install @nexafi/sdk
```

**Basic usage:**

```typescript
import { NexaFi } from "@nexafi/sdk";

// Initialize client
const client = new NexaFi({
  apiKey: "your-api-key",
  baseUrl: "http://localhost:5000",
});

// Authenticate user
const user = await client.auth.login({
  email: "user@example.com",
  password: "SecurePass123!",
});

// Get account information
const accounts = await client.ledger.listAccounts();
console.log("Accounts:", accounts);

// Create a transaction
const transaction = await client.payments.create({
  amount: 100.0,
  currency: "USD",
  paymentMethodId: "pm_123456",
});

// Get AI predictions
const forecast = await client.ai.getCashFlowForecast({ days: 30 });
console.log("Forecast:", forecast);
```

---

## Common Workflows

### Workflow 1: User Registration and Authentication

**Step 1: Register a new user**

```bash
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "SecurePass123!",
    "full_name": "Jane Doe",
    "business_name": "Jane's Bakery"
  }'
```

**Response:**

```json
{
  "user_id": "usr_abc123",
  "email": "newuser@example.com",
  "full_name": "Jane Doe",
  "created_at": "2025-12-30T10:30:00Z"
}
```

**Step 2: Login to get access token**

```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "SecurePass123!"
  }'
```

**Response:**

```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**Step 3: Use access token for authenticated requests**

```bash
curl -X GET http://localhost:5000/api/v1/users/profile \
  -H "Authorization: Bearer eyJhbGc..."
```

### Workflow 2: Creating and Managing Accounts

**Step 1: Create a checking account**

```bash
curl -X POST http://localhost:5000/api/v1/accounts \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Business Checking",
    "type": "asset",
    "subtype": "checking",
    "currency": "USD",
    "initial_balance": 10000.00
  }'
```

**Step 2: List all accounts**

```bash
curl -X GET http://localhost:5000/api/v1/accounts \
  -H "Authorization: Bearer <token>"
```

**Step 3: Get account details**

```bash
curl -X GET http://localhost:5000/api/v1/accounts/acc_123 \
  -H "Authorization: Bearer <token>"
```

### Workflow 3: Processing Payments

**Step 1: Add a payment method**

```bash
curl -X POST http://localhost:5000/api/v1/payment-methods \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "card",
    "card_number": "4242424242424242",
    "exp_month": 12,
    "exp_year": 2025,
    "cvc": "123"
  }'
```

**Step 2: Create a payment transaction**

```bash
curl -X POST http://localhost:5000/api/v1/transactions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 250.00,
    "currency": "USD",
    "payment_method_id": "pm_abc123",
    "description": "Invoice #1234 payment",
    "metadata": {
      "invoice_id": "inv_1234"
    }
  }'
```

**Step 3: Check transaction status**

```bash
curl -X GET http://localhost:5000/api/v1/transactions/txn_xyz789 \
  -H "Authorization: Bearer <token>"
```

### Workflow 4: AI-Powered Cash Flow Forecasting

**Step 1: Get cash flow forecast**

```bash
curl -X POST http://localhost:5000/api/v1/predictions/cash-flow \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "forecast_days": 90,
    "include_confidence_intervals": true
  }'
```

**Response:**

```json
{
  "forecast": [
    {
      "date": "2025-01-01",
      "predicted_balance": 45230.5,
      "confidence_low": 42000.0,
      "confidence_high": 48500.0
    },
    {
      "date": "2025-01-02",
      "predicted_balance": 46100.25,
      "confidence_low": 43200.0,
      "confidence_high": 49000.0
    }
  ],
  "accuracy_score": 0.92,
  "model_version": "v2.1.0"
}
```

**Step 2: Get actionable insights**

```bash
curl -X GET http://localhost:5000/api/v1/insights \
  -H "Authorization: Bearer <token>"
```

### Workflow 5: Compliance Checks

**Step 1: Perform KYC verification**

```bash
curl -X POST http://localhost:5000/api/v1/compliance/kyc/verify \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust_123",
    "verification_type": "enhanced",
    "documents": [
      {
        "type": "passport",
        "document_number": "AB123456",
        "country": "US"
      }
    ]
  }'
```

**Step 2: Run AML check on transaction**

```bash
curl -X POST http://localhost:5000/api/v1/compliance/aml/check \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "txn_xyz789",
    "amount": 15000.00,
    "currency": "USD"
  }'
```

**Step 3: Screen against sanctions lists**

```bash
curl -X POST http://localhost:5000/api/v1/compliance/sanctions/screen \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_name": "John Smith",
    "entity_type": "individual",
    "country": "US"
  }'
```

---

## API Integration

### REST API Integration

**Base URL:** `http://localhost:5000/api/v1`

**Authentication:**
All requests require a Bearer token in the Authorization header:

```
Authorization: Bearer <your-access-token>
```

**Rate Limits:**

- Authentication endpoints: 5 requests / 5 minutes
- Financial transactions: 100 requests / minute
- General API calls: 1000 requests / minute

**Example: Complete payment flow**

```python
import requests

BASE_URL = "http://localhost:5000/api/v1"
token = "your-access-token"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 1. Create payment method
payment_method = requests.post(
    f"{BASE_URL}/payment-methods",
    headers=headers,
    json={
        "type": "bank_account",
        "account_number": "1234567890",
        "routing_number": "021000021"
    }
).json()

# 2. Create transaction
transaction = requests.post(
    f"{BASE_URL}/transactions",
    headers=headers,
    json={
        "amount": 500.00,
        "currency": "USD",
        "payment_method_id": payment_method["id"],
        "description": "Monthly subscription"
    }
).json()

# 3. Check status
status = requests.get(
    f"{BASE_URL}/transactions/{transaction['id']}",
    headers=headers
).json()

print(f"Transaction status: {status['status']}")
```

### GraphQL API Integration

**Endpoint:** `http://localhost:5000/graphql`

**Example query:**

```graphql
query GetUserAccounts {
  user {
    id
    email
    accounts {
      id
      name
      balance
      currency
      transactions(limit: 10) {
        id
        amount
        description
        createdAt
      }
    }
  }
}
```

**Example mutation:**

```graphql
mutation CreateTransaction {
  createTransaction(
    amount: 250.00
    currency: "USD"
    paymentMethodId: "pm_123"
    description: "Invoice payment"
  ) {
    id
    status
    amount
    createdAt
  }
}
```

### Webhook Integration

**Setting up webhooks:**

```bash
curl -X POST http://localhost:5000/api/v1/webhooks \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhooks/nexafi",
    "events": [
      "transaction.created",
      "transaction.succeeded",
      "transaction.failed",
      "account.updated"
    ],
    "secret": "your-webhook-secret"
  }'
```

**Verifying webhook signatures:**

```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    expected_signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)

# In your webhook handler
@app.route('/webhooks/nexafi', methods=['POST'])
def handle_webhook():
    payload = request.get_data(as_text=True)
    signature = request.headers.get('X-NexaFi-Signature')

    if not verify_webhook_signature(payload, signature, WEBHOOK_SECRET):
        return 'Invalid signature', 401

    event = request.get_json()

    if event['type'] == 'transaction.succeeded':
        # Handle successful transaction
        pass

    return 'OK', 200
```

---

## Best Practices

### Security Best Practices

| Practice                      | Description               | Example                              |
| ----------------------------- | ------------------------- | ------------------------------------ |
| **Use environment variables** | Never hardcode secrets    | `SECRET_KEY=os.getenv('SECRET_KEY')` |
| **Rotate API keys regularly** | Change keys every 90 days | Use key management service           |
| **Implement rate limiting**   | Protect against abuse     | Already built into API Gateway       |
| **Validate all inputs**       | Prevent injection attacks | Use provided validators              |
| **Use HTTPS in production**   | Encrypt data in transit   | Configure reverse proxy              |
| **Enable MFA**                | Add extra security layer  | `/api/v1/auth/mfa/enable`            |

### Performance Best Practices

| Practice                           | Description               | Benefit                 |
| ---------------------------------- | ------------------------- | ----------------------- |
| **Cache frequently accessed data** | Use Redis for caching     | Reduce database load    |
| **Batch API requests**             | Combine multiple calls    | Reduce network overhead |
| **Use pagination**                 | Limit result set size     | Improve response time   |
| **Enable compression**             | Gzip API responses        | Reduce bandwidth usage  |
| **Monitor API usage**              | Track performance metrics | Identify bottlenecks    |

### Development Best Practices

```python
# Use try-except for API calls
try:
    response = client.payments.create(...)
except NexaFiAPIError as e:
    logger.error(f"Payment failed: {e.message}")
    handle_error(e)

# Always check response status
if response.status_code == 200:
    data = response.json()
else:
    handle_error(response)

# Use idempotency keys for payment operations
payment = client.payments.create(
    idempotency_key="order_12345",
    amount=100.00,
    currency="USD"
)
```

---

## Troubleshooting Common Usage Issues

| Issue                         | Cause                    | Solution                           |
| ----------------------------- | ------------------------ | ---------------------------------- |
| **401 Unauthorized**          | Invalid or expired token | Refresh token or re-authenticate   |
| **429 Too Many Requests**     | Rate limit exceeded      | Implement exponential backoff      |
| **400 Bad Request**           | Invalid request data     | Check request payload format       |
| **500 Internal Server Error** | Server-side issue        | Check server logs, contact support |
| **Connection timeout**        | Network or service issue | Verify service is running          |

---

## Additional Resources

- [API Reference](API.md) - Complete API documentation
- [CLI Reference](CLI.md) - Command-line tools
- [Configuration](CONFIGURATION.md) - Environment setup
- [Examples](EXAMPLES/) - Code examples

---
