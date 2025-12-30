# KYC & Compliance Example

Example showing KYC verification and compliance checks using NexaFi.

## Overview

This example demonstrates:

- KYC verification process
- AML transaction monitoring
- Sanctions screening
- Compliance reporting

## Prerequisites

- NexaFi account with compliance features enabled
- API access token with compliance permissions
- Customer data and documents

## Example Code

### KYC Verification

```python
import requests
import base64

BASE_URL = "http://localhost:5000/api/v1"
API_TOKEN = "your-access-token"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def verify_customer_kyc(customer_id, documents):
    """Initiate KYC verification"""

    kyc_data = {
        "customer_id": customer_id,
        "verification_type": "enhanced",  # basic, enhanced, or full
        "documents": documents
    }

    response = requests.post(
        f"{BASE_URL}/compliance/kyc/verify",
        headers=headers,
        json=kyc_data
    )

    if response.status_code == 200:
        verification = response.json()
        print(f"✅ KYC verification initiated")
        print(f"   Verification ID: {verification['id']}")
        print(f"   Status: {verification['status']}")
        print(f"   Estimated time: {verification['estimated_completion']}")
        return verification
    else:
        print(f"❌ KYC verification failed: {response.json()}")
        return None

# Prepare documents
documents = [
    {
        "type": "passport",
        "document_number": "AB123456",
        "country": "US",
        "expiry_date": "2030-12-31",
        "image_url": "https://example.com/passport.jpg"
    },
    {
        "type": "proof_of_address",
        "document_type": "utility_bill",
        "issue_date": "2025-11-01",
        "image_url": "https://example.com/utility_bill.jpg"
    }
]

# Initiate verification
verification = verify_customer_kyc("cust_123", documents)
```

### Check KYC Status

```python
def check_kyc_status(verification_id):
    """Check KYC verification status"""

    response = requests.get(
        f"{BASE_URL}/compliance/kyc/status/{verification_id}",
        headers=headers
    )

    if response.status_code == 200:
        status = response.json()

        status_emoji = {
            'pending': '⏳',
            'in_review': '🔍',
            'approved': '✅',
            'rejected': '❌',
            'requires_action': '⚠️'
        }

        emoji = status_emoji.get(status['status'], '❓')

        print(f"{emoji} KYC Status: {status['status']}")
        print(f"   Risk Level: {status['risk_level']}")

        if status['status'] == 'requires_action':
            print(f"   Required Action: {status['required_action']}")

        return status
    else:
        print(f"Status check failed: {response.json()}")
        return None
```

### AML Transaction Check

```python
def check_aml_transaction(transaction_id, amount, currency):
    """Perform AML check on transaction"""

    aml_data = {
        "transaction_id": transaction_id,
        "amount": amount,
        "currency": currency,
        "check_types": ["transaction_monitoring", "risk_scoring"]
    }

    response = requests.post(
        f"{BASE_URL}/compliance/aml/check",
        headers=headers,
        json=aml_data
    )

    if response.status_code == 200:
        result = response.json()

        print(f"AML Check Results:")
        print(f"   Risk Score: {result['risk_score']}/100")
        print(f"   Risk Level: {result['risk_level']}")

        if result['flags']:
            print(f"   ⚠️  Flags: {', '.join(result['flags'])}")

        if result['requires_manual_review']:
            print(f"   🔍 Manual review required")

        return result
    else:
        print(f"AML check failed: {response.json()}")
        return None

# Usage
aml_result = check_aml_transaction(
    transaction_id="txn_xyz789",
    amount=15000.00,
    currency="USD"
)
```

### Sanctions Screening

```python
def screen_sanctions(entity_name, entity_type, country=None):
    """Screen entity against sanctions lists"""

    screening_data = {
        "entity_name": entity_name,
        "entity_type": entity_type,  # individual or business
        "country": country
    }

    response = requests.post(
        f"{BASE_URL}/compliance/sanctions/screen",
        headers=headers,
        json=screening_data
    )

    if response.status_code == 200:
        result = response.json()

        if result['matches']:
            print(f"⚠️  {len(result['matches'])} potential matches found")
            for match in result['matches']:
                print(f"   - {match['name']} ({match['list']})")
                print(f"     Match score: {match['score']}")
        else:
            print(f"✅ No sanctions matches found")

        return result
    else:
        print(f"Sanctions screening failed: {response.json()}")
        return None

# Usage
sanctions_result = screen_sanctions(
    entity_name="John Smith",
    entity_type="individual",
    country="US"
)
```

## Complete Compliance Workflow

```python
class ComplianceManager:
    def __init__(self, api_token):
        self.base_url = "http://localhost:5000/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

    def onboard_customer(self, customer_data, documents):
        """Complete customer onboarding with compliance checks"""

        print("Starting customer onboarding...")

        # 1. Sanctions screening
        print("\n1. Sanctions screening...")
        sanctions = self.screen_sanctions(
            customer_data['full_name'],
            'individual',
            customer_data.get('country')
        )

        if sanctions and sanctions['matches']:
            print("❌ Sanctions match found. Cannot proceed.")
            return None

        # 2. KYC verification
        print("\n2. Initiating KYC verification...")
        kyc = self.verify_kyc(customer_data['id'], documents)

        if not kyc:
            print("❌ KYC verification failed")
            return None

        # 3. Risk assessment
        print("\n3. Performing risk assessment...")
        risk = self.assess_risk(customer_data)

        result = {
            'customer_id': customer_data['id'],
            'kyc_verification_id': kyc['id'],
            'risk_level': risk['level'],
            'status': 'pending_kyc_approval',
            'next_steps': [
                'Wait for KYC document review',
                'Complete additional verification if required'
            ]
        }

        print("\n✅ Onboarding initiated successfully")
        return result

    def monitor_transaction(self, transaction_id, amount, customer_id):
        """Monitor transaction for AML/compliance"""

        alerts = []

        # Check transaction amount threshold
        if amount >= 10000:
            alerts.append({
                'type': 'large_transaction',
                'severity': 'medium',
                'message': f'Transaction amount ${amount} exceeds threshold'
            })

        # Perform AML check
        aml_result = self.check_aml(transaction_id, amount)

        if aml_result['risk_score'] > 70:
            alerts.append({
                'type': 'high_risk',
                'severity': 'high',
                'message': 'High AML risk score detected'
            })

        # Check customer risk profile
        customer_risk = self.get_customer_risk(customer_id)

        if customer_risk['level'] == 'high':
            alerts.append({
                'type': 'high_risk_customer',
                'severity': 'high',
                'message': 'Transaction from high-risk customer'
            })

        return {
            'transaction_id': transaction_id,
            'alerts': alerts,
            'requires_review': len([a for a in alerts if a['severity'] == 'high']) > 0
        }

    def generate_sar(self, transaction_id, reason):
        """Generate Suspicious Activity Report"""

        sar_data = {
            "transaction_id": transaction_id,
            "reason": reason,
            "report_type": "SAR",
            "filing_institution": "NexaFi Platform"
        }

        response = requests.post(
            f"{self.base_url}/compliance/reports/sar",
            headers=self.headers,
            json=sar_data
        )

        if response.status_code == 201:
            report = response.json()
            print(f"✅ SAR generated: {report['report_id']}")
            return report
        else:
            print(f"SAR generation failed")
            return None

# Usage
compliance = ComplianceManager(API_TOKEN)

# Onboard new customer
customer_data = {
    'id': 'cust_123',
    'full_name': 'Jane Doe',
    'email': 'jane@example.com',
    'country': 'US'
}

documents = [
    {
        "type": "passport",
        "document_number": "AB123456",
        "country": "US",
        "expiry_date": "2030-12-31",
        "image_url": "https://example.com/passport.jpg"
    }
]

onboarding_result = compliance.onboard_customer(customer_data, documents)

# Monitor transaction
monitoring_result = compliance.monitor_transaction(
    transaction_id="txn_abc123",
    amount=15000.00,
    customer_id="cust_123"
)

if monitoring_result['requires_review']:
    print("⚠️  Transaction requires manual review")
```

---
