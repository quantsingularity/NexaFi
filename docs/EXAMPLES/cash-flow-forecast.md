# Cash Flow Forecasting Example

Complete example showing how to use NexaFi's AI-powered cash flow forecasting.

## Overview

This example demonstrates:

- Making a cash flow forecast API call
- Interpreting forecast results
- Using confidence intervals
- Handling predictions in your application

## Prerequisites

- Active NexaFi account
- Valid API token
- At least 30 days of historical transaction data

## Example Code

### Python Example

```python
import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:5000/api/v1"
API_TOKEN = "your-access-token-here"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Request cash flow forecast for 90 days
forecast_request = {
    "forecast_days": 90,
    "include_confidence_intervals": True,
    "account_ids": ["acc_123", "acc_456"]  # Optional: specific accounts
}

response = requests.post(
    f"{BASE_URL}/predictions/cash-flow",
    headers=headers,
    json=forecast_request
)

if response.status_code == 200:
    forecast_data = response.json()

    print(f"Accuracy Score: {forecast_data['accuracy_score'] * 100}%")
    print(f"Model Version: {forecast_data['model_version']}")
    print("\nForecast:")

    for day in forecast_data['forecast'][:7]:  # First 7 days
        print(f"Date: {day['date']}")
        print(f"  Predicted Balance: ${day['predicted_balance']:,.2f}")
        print(f"  Range: ${day['confidence_low']:,.2f} - ${day['confidence_high']:,.2f}")
        print()
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

### JavaScript Example

```javascript
const axios = require("axios");

const BASE_URL = "http://localhost:5000/api/v1";
const API_TOKEN = "your-access-token-here";

async function getCashFlowForecast() {
  try {
    const response = await axios.post(
      `${BASE_URL}/predictions/cash-flow`,
      {
        forecast_days: 90,
        include_confidence_intervals: true,
      },
      {
        headers: {
          Authorization: `Bearer ${API_TOKEN}`,
          "Content-Type": "application/json",
        },
      },
    );

    const { forecast, accuracy_score, model_version } = response.data;

    console.log(`Accuracy: ${(accuracy_score * 100).toFixed(1)}%`);
    console.log(`Model: ${model_version}\n`);

    forecast.slice(0, 7).forEach((day) => {
      console.log(`${day.date}: $${day.predicted_balance.toFixed(2)}`);
      console.log(
        `  Range: $${day.confidence_low} - $${day.confidence_high}\n`,
      );
    });

    return forecast;
  } catch (error) {
    console.error("Forecast error:", error.response?.data || error.message);
  }
}

getCashFlowForecast();
```

## Response Format

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

## Visualization Example

```python
import matplotlib.pyplot as plt
import pandas as pd

def visualize_forecast(forecast_data):
    """Create visualization of cash flow forecast"""

    df = pd.DataFrame(forecast_data['forecast'])
    df['date'] = pd.to_datetime(df['date'])

    plt.figure(figsize=(12, 6))

    # Plot predicted balance
    plt.plot(df['date'], df['predicted_balance'],
             label='Predicted Balance', color='blue', linewidth=2)

    # Plot confidence interval
    plt.fill_between(df['date'],
                     df['confidence_low'],
                     df['confidence_high'],
                     alpha=0.3, color='blue',
                     label='Confidence Interval')

    plt.xlabel('Date')
    plt.ylabel('Balance ($)')
    plt.title('90-Day Cash Flow Forecast')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig('cash_flow_forecast.png')
    print("Forecast visualization saved to cash_flow_forecast.png")

# Usage
if response.status_code == 200:
    visualize_forecast(forecast_data)
```

## Best Practices

1. **Historical Data**: Ensure at least 30 days of transaction history
2. **Regular Updates**: Re-forecast weekly for best accuracy
3. **Confidence Intervals**: Use for risk assessment and planning
4. **Alert Thresholds**: Set up alerts for low balance predictions
5. **Combine with Insights**: Use with `/api/v1/insights` for actionable recommendations

## Common Use Cases

### Use Case 1: Cash Flow Alert

```python
def check_cash_flow_alert(forecast, threshold=5000):
    """Alert if cash flow drops below threshold"""
    for day in forecast:
        if day['predicted_balance'] < threshold:
            print(f"⚠️  ALERT: Cash flow projected below ${threshold} on {day['date']}")
            print(f"   Predicted: ${day['predicted_balance']:,.2f}")
            return True
    return False

# Usage
if response.status_code == 200:
    check_cash_flow_alert(forecast_data['forecast'], threshold=10000)
```

### Use Case 2: Planning Report

```python
def generate_planning_report(forecast):
    """Generate cash flow planning report"""

    balances = [day['predicted_balance'] for day in forecast]

    report = {
        'min_balance': min(balances),
        'max_balance': max(balances),
        'avg_balance': sum(balances) / len(balances),
        'days_below_10k': sum(1 for b in balances if b < 10000)
    }

    print("Cash Flow Planning Report (90 days)")
    print(f"Minimum Balance: ${report['min_balance']:,.2f}")
    print(f"Maximum Balance: ${report['max_balance']:,.2f}")
    print(f"Average Balance: ${report['avg_balance']:,.2f}")
    print(f"Days Below $10k: {report['days_below_10k']}")

    return report
```

## Related Examples

- [AI Insights](analytics.md)
- [Transaction Management](payments.md)
- [Account Management](accounts.md)

---
