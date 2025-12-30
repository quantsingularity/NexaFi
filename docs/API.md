# API Reference

Complete reference for NexaFi REST API, GraphQL API, and Webhooks.

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [REST API Endpoints](#rest-api-endpoints)
4. [GraphQL API](#graphql-api)
5. [Webhooks](#webhooks)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)

---

## Overview

**Base URL:** `https://api.nexafi.com` (Production) or `http://localhost:5000` (Development)

**API Version:** `v1`

**Content Type:** `application/json`

**Authentication:** Bearer token (JWT)

---

## Authentication

### Authentication Flow

All protected endpoints require authentication using JWT (JSON Web Tokens).

**Authorization Header Format:**

```
Authorization: Bearer <your-access-token>
```

### Register User

Create a new user account.

**Endpoint:** `POST /api/v1/auth/register`

| Parameter       | Type   | Required | Default | Description                   | Example            |
| --------------- | ------ | -------- | ------- | ----------------------------- | ------------------ |
| `email`         | string | ✅       | -       | User email address            | `user@example.com` |
| `password`      | string | ✅       | -       | Strong password (min 8 chars) | `SecurePass123!`   |
| `full_name`     | string | ✅       | -       | User's full name              | `John Doe`         |
| `business_name` | string | ❌       | -       | Business name (optional)      | `Acme Corp`        |

**Example Request:**

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

**Example Response:**

```json
{
  "user_id": "usr_abc123xyz",
  "email": "newuser@example.com",
  "full_name": "Jane Doe",
  "business_name": "Jane's Bakery",
  "created_at": "2025-12-30T10:30:00Z",
  "status": "active"
}
```

### Login

Authenticate and receive access token.

**Endpoint:** `POST /api/v1/auth/login`

| Parameter     | Type    | Required | Default | Description      | Example            |
| ------------- | ------- | -------- | ------- | ---------------- | ------------------ |
| `email`       | string  | ✅       | -       | Registered email | `user@example.com` |
| `password`    | string  | ✅       | -       | Account password | `SecurePass123!`   |
| `remember_me` | boolean | ❌       | `false` | Extended session | `true`             |

**Example Request:**

```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

**Example Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "usr_abc123xyz",
    "email": "user@example.com",
    "full_name": "Jane Doe"
  }
}
```

### Refresh Token

Obtain a new access token using refresh token.

**Endpoint:** `POST /api/v1/auth/refresh`

| Parameter       | Type   | Required | Default | Description         | Example         |
| --------------- | ------ | -------- | ------- | ------------------- | --------------- |
| `refresh_token` | string | ✅       | -       | Valid refresh token | `eyJhbGciOi...` |

---

## REST API Endpoints

### User Management

#### Get User Profile

**Endpoint:** `GET /api/v1/users/profile`

**Auth Required:** ✅

**Example Request:**

```bash
curl -X GET http://localhost:5000/api/v1/users/profile \
  -H "Authorization: Bearer <token>"
```

**Example Response:**

```json
{
  "id": "usr_abc123xyz",
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "business_name": "Jane's Bakery",
  "phone": "+1234567890",
  "created_at": "2025-01-15T08:00:00Z",
  "updated_at": "2025-12-30T10:30:00Z",
  "kyc_status": "verified",
  "account_status": "active"
}
```

#### Update User Profile

**Endpoint:** `PUT /api/v1/users/profile`

**Auth Required:** ✅

| Parameter       | Type   | Required | Default | Description       | Example                |
| --------------- | ------ | -------- | ------- | ----------------- | ---------------------- |
| `full_name`     | string | ❌       | -       | Updated full name | `Jane Smith`           |
| `phone`         | string | ❌       | -       | Phone number      | `+1234567890`          |
| `business_name` | string | ❌       | -       | Business name     | `Jane's Bakery & Cafe` |

### Ledger & Accounts

#### List Accounts

**Endpoint:** `GET /api/v1/accounts`

**Auth Required:** ✅

**Query Parameters:**

| Parameter  | Type    | Required | Default | Description         | Example                        |
| ---------- | ------- | -------- | ------- | ------------------- | ------------------------------ |
| `type`     | string  | ❌       | `all`   | Account type filter | `asset`, `liability`, `equity` |
| `currency` | string  | ❌       | `all`   | Currency filter     | `USD`, `EUR`, `GBP`            |
| `page`     | integer | ❌       | `1`     | Page number         | `1`                            |
| `limit`    | integer | ❌       | `50`    | Results per page    | `10`                           |

**Example Response:**

```json
{
  "accounts": [
    {
      "id": "acc_123",
      "name": "Business Checking",
      "type": "asset",
      "subtype": "checking",
      "balance": 15430.5,
      "currency": "USD",
      "status": "active",
      "created_at": "2025-01-15T08:00:00Z"
    },
    {
      "id": "acc_456",
      "name": "Accounts Receivable",
      "type": "asset",
      "subtype": "receivable",
      "balance": 8250.0,
      "currency": "USD",
      "status": "active",
      "created_at": "2025-01-16T09:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 2,
    "total_pages": 1
  }
}
```

#### Create Account

**Endpoint:** `POST /api/v1/accounts`

**Auth Required:** ✅

| Parameter         | Type   | Required | Default | Description      | Example                                              |
| ----------------- | ------ | -------- | ------- | ---------------- | ---------------------------------------------------- |
| `name`            | string | ✅       | -       | Account name     | `Business Savings`                                   |
| `type`            | string | ✅       | -       | Account type     | `asset`, `liability`, `equity`, `revenue`, `expense` |
| `subtype`         | string | ❌       | -       | Account subtype  | `checking`, `savings`, `credit_card`                 |
| `currency`        | string | ❌       | `USD`   | Currency code    | `USD`, `EUR`, `GBP`                                  |
| `initial_balance` | number | ❌       | `0.00`  | Starting balance | `10000.00`                                           |

#### Create Journal Entry

**Endpoint:** `POST /api/v1/journal-entries`

**Auth Required:** ✅

| Parameter     | Type   | Required | Default | Description                 | Example            |
| ------------- | ------ | -------- | ------- | --------------------------- | ------------------ |
| `date`        | string | ✅       | -       | Transaction date (ISO 8601) | `2025-12-30`       |
| `description` | string | ✅       | -       | Entry description           | `Payment received` |
| `entries`     | array  | ✅       | -       | Debit/credit entries        | See example below  |

**Example Request:**

```json
{
  "date": "2025-12-30",
  "description": "Client payment received",
  "entries": [
    {
      "account_id": "acc_checking",
      "debit": 1000.0,
      "credit": 0.0
    },
    {
      "account_id": "acc_revenue",
      "debit": 0.0,
      "credit": 1000.0
    }
  ]
}
```

### Payment Processing

#### Create Transaction

**Endpoint:** `POST /api/v1/transactions`

**Auth Required:** ✅

| Parameter           | Type   | Required | Default | Description             | Example                      |
| ------------------- | ------ | -------- | ------- | ----------------------- | ---------------------------- |
| `amount`            | number | ✅       | -       | Transaction amount      | `250.00`                     |
| `currency`          | string | ✅       | -       | Currency code           | `USD`                        |
| `payment_method_id` | string | ✅       | -       | Payment method ID       | `pm_abc123`                  |
| `description`       | string | ❌       | -       | Transaction description | `Invoice #1234`              |
| `metadata`          | object | ❌       | `{}`    | Additional metadata     | `{"invoice_id": "inv_1234"}` |
| `idempotency_key`   | string | ❌       | -       | Idempotency key         | `order_12345`                |

**Example Response:**

```json
{
  "id": "txn_xyz789",
  "amount": 250.0,
  "currency": "USD",
  "status": "succeeded",
  "payment_method": {
    "id": "pm_abc123",
    "type": "card",
    "last4": "4242"
  },
  "description": "Invoice #1234",
  "created_at": "2025-12-30T10:45:00Z",
  "metadata": {
    "invoice_id": "inv_1234"
  }
}
```

#### List Transactions

**Endpoint:** `GET /api/v1/transactions`

**Auth Required:** ✅

**Query Parameters:**

| Parameter   | Type    | Required | Default | Description           | Example                          |
| ----------- | ------- | -------- | ------- | --------------------- | -------------------------------- |
| `status`    | string  | ❌       | `all`   | Filter by status      | `succeeded`, `failed`, `pending` |
| `from_date` | string  | ❌       | -       | Start date (ISO 8601) | `2025-01-01`                     |
| `to_date`   | string  | ❌       | -       | End date (ISO 8601)   | `2025-12-31`                     |
| `limit`     | integer | ❌       | `50`    | Results per page      | `10`                             |

### AI & Predictions

#### Get Cash Flow Forecast

**Endpoint:** `POST /api/v1/predictions/cash-flow`

**Auth Required:** ✅

| Parameter                      | Type    | Required | Default | Description                  | Example       |
| ------------------------------ | ------- | -------- | ------- | ---------------------------- | ------------- |
| `forecast_days`                | integer | ✅       | -       | Number of days to forecast   | `90`          |
| `include_confidence_intervals` | boolean | ❌       | `true`  | Include confidence intervals | `true`        |
| `account_ids`                  | array   | ❌       | `all`   | Specific accounts to analyze | `["acc_123"]` |

**Example Response:**

```json
{
  "forecast": [
    {
      "date": "2025-12-31",
      "predicted_balance": 45230.5,
      "confidence_low": 42000.0,
      "confidence_high": 48500.0
    },
    {
      "date": "2026-01-01",
      "predicted_balance": 46100.25,
      "confidence_low": 43200.0,
      "confidence_high": 49000.0
    }
  ],
  "accuracy_score": 0.92,
  "model_version": "v2.1.0",
  "generated_at": "2025-12-30T10:50:00Z"
}
```

#### Get AI Insights

**Endpoint:** `GET /api/v1/insights`

**Auth Required:** ✅

**Example Response:**

```json
{
  "insights": [
    {
      "type": "cash_flow_alert",
      "priority": "high",
      "message": "Cash flow projected to drop below minimum threshold in 15 days",
      "recommendation": "Consider delaying large purchases or accelerating receivables collection",
      "impact_amount": -5000.0,
      "confidence": 0.89
    },
    {
      "type": "spending_anomaly",
      "priority": "medium",
      "message": "Office supplies spending 40% higher than previous month",
      "recommendation": "Review recent purchases for unusual patterns",
      "impact_amount": 450.0,
      "confidence": 0.95
    }
  ],
  "generated_at": "2025-12-30T10:55:00Z"
}
```

### Compliance

#### Perform KYC Verification

**Endpoint:** `POST /api/v1/compliance/kyc/verify`

**Auth Required:** ✅

| Parameter           | Type   | Required | Default | Description         | Example                     |
| ------------------- | ------ | -------- | ------- | ------------------- | --------------------------- |
| `customer_id`       | string | ✅       | -       | Customer identifier | `cust_123`                  |
| `verification_type` | string | ✅       | -       | Verification level  | `basic`, `enhanced`, `full` |
| `documents`         | array  | ✅       | -       | Identity documents  | See example below           |

**Example Request:**

```json
{
  "customer_id": "cust_123",
  "verification_type": "enhanced",
  "documents": [
    {
      "type": "passport",
      "document_number": "AB123456",
      "country": "US",
      "expiry_date": "2030-12-31",
      "image_url": "https://example.com/passport.jpg"
    }
  ]
}
```

#### AML Transaction Check

**Endpoint:** `POST /api/v1/compliance/aml/check`

**Auth Required:** ✅

| Parameter        | Type   | Required | Default | Description          | Example           |
| ---------------- | ------ | -------- | ------- | -------------------- | ----------------- |
| `transaction_id` | string | ✅       | -       | Transaction to check | `txn_xyz789`      |
| `amount`         | number | ✅       | -       | Transaction amount   | `15000.00`        |
| `currency`       | string | ✅       | -       | Currency code        | `USD`             |
| `counterparty`   | object | ❌       | -       | Counterparty details | `{"name": "..."}` |

---

## GraphQL API

**Endpoint:** `https://api.nexafi.com/graphql` or `http://localhost:5000/graphql`

### Query: Get User with Accounts

```graphql
query GetUserAccounts {
  user {
    id
    email
    fullName
    accounts {
      id
      name
      balance
      currency
      type
      transactions(limit: 10) {
        id
        amount
        description
        status
        createdAt
      }
    }
  }
}
```

### Mutation: Create Transaction

```graphql
mutation CreateTransaction($input: TransactionInput!) {
  createTransaction(input: $input) {
    id
    amount
    currency
    status
    paymentMethod {
      id
      type
    }
    createdAt
  }
}
```

**Variables:**

```json
{
  "input": {
    "amount": 250.0,
    "currency": "USD",
    "paymentMethodId": "pm_abc123",
    "description": "Invoice payment"
  }
}
```

---

## Webhooks

### Setting Up Webhooks

**Endpoint:** `POST /api/v1/webhooks`

| Parameter | Type   | Required | Default | Description              | Example                                |
| --------- | ------ | -------- | ------- | ------------------------ | -------------------------------------- |
| `url`     | string | ✅       | -       | Webhook callback URL     | `https://your-app.com/webhooks/nexafi` |
| `events`  | array  | ✅       | -       | Event types to subscribe | `["transaction.created"]`              |
| `secret`  | string | ✅       | -       | Signing secret           | `whsec_abc123`                         |

### Webhook Events

| Event                   | Description                        |
| ----------------------- | ---------------------------------- |
| `transaction.created`   | New transaction created            |
| `transaction.succeeded` | Transaction completed successfully |
| `transaction.failed`    | Transaction failed                 |
| `account.updated`       | Account details changed            |
| `user.verified`         | User KYC verification completed    |
| `payment.refunded`      | Payment refunded                   |

### Webhook Payload Example

```json
{
  "id": "evt_abc123",
  "type": "transaction.succeeded",
  "created": 1704024000,
  "data": {
    "transaction": {
      "id": "txn_xyz789",
      "amount": 250.0,
      "currency": "USD",
      "status": "succeeded"
    }
  }
}
```

### Verifying Webhook Signatures

```python
import hmac
import hashlib

def verify_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

---

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "invalid_request",
    "message": "Invalid payment method ID",
    "param": "payment_method_id",
    "type": "invalid_request_error"
  }
}
```

### HTTP Status Codes

| Status Code                 | Description                       |
| --------------------------- | --------------------------------- |
| `200 OK`                    | Request succeeded                 |
| `201 Created`               | Resource created successfully     |
| `400 Bad Request`           | Invalid request parameters        |
| `401 Unauthorized`          | Authentication required or failed |
| `403 Forbidden`             | Insufficient permissions          |
| `404 Not Found`             | Resource not found                |
| `429 Too Many Requests`     | Rate limit exceeded               |
| `500 Internal Server Error` | Server error                      |
| `503 Service Unavailable`   | Service temporarily unavailable   |

---

## Rate Limiting

### Rate Limit Headers

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1704024000
```

### Rate Limits by Endpoint Type

| Endpoint Type  | Limit         | Window    |
| -------------- | ------------- | --------- |
| Authentication | 5 requests    | 5 minutes |
| Transactions   | 100 requests  | 1 minute  |
| General API    | 1000 requests | 1 minute  |
| Webhooks       | 10 requests   | 1 minute  |

---
