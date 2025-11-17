import json
import os
import sys
import time
from datetime import datetime, timedelta

import requests

# Test configuration
BASE_URL = "http://localhost:5000"
SERVICES = {
    "api-gateway": 5000,
    "user-service": 5001,
    "ledger-service": 5002,
    "payment-service": 5003,
    "ai-service": 5004,
    "compliance-service": 5005,
    "notification-service": 5006,
}


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.access_token = None
        self.user_id = None
        self.test_data = {}

    def log(self, message, color=Colors.BLUE):
        print(f"{color}{message}{Colors.ENDC}")

    def success(self, message):
        self.passed += 1
        print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")

    def error(self, message):
        self.failed += 1
        print(f"{Colors.RED}✗ {message}{Colors.ENDC}")

    def warning(self, message):
        print(f"{Colors.YELLOW}⚠ {message}{Colors.ENDC}")

    def test_health_checks(self):
        """Test health endpoints for all services"""
        self.log("\n=== Testing Health Checks ===", Colors.BOLD)

        for service_name, port in SERVICES.items():
            try:
                response = requests.get(
                    f"http://localhost:{port}/api/v1/health", timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    self.success(
                        f"{service_name} health check passed - {data.get('status', 'unknown')}"
                    )
                else:
                    self.error(
                        f"{service_name} health check failed - HTTP {response.status_code}"
                    )
            except requests.exceptions.RequestException as e:
                self.error(f"{service_name} health check failed - {str(e)}")

    def test_api_gateway(self):
        """Test API Gateway functionality"""
        self.log("\n=== Testing API Gateway ===", Colors.BOLD)

        try:
            # Test gateway health
            response = requests.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                self.success("API Gateway health check passed")
            else:
                self.error("API Gateway health check failed")

            # Test service listing
            response = requests.get(f"{BASE_URL}/api/v1/services")
            if response.status_code == 200:
                data = response.json()
                services = data.get("services", {})
                if len(services) >= 6:  # We have 6 backend services
                    self.success(
                        f"Service discovery working - found {len(services)} services"
                    )
                else:
                    self.warning(f"Expected 6+ services, found {len(services)}")
            else:
                self.error("Service discovery failed")

        except requests.exceptions.RequestException as e:
            self.error(f"API Gateway test failed - {str(e)}")

    def test_user_service(self):
        self.log("\n=== Testing User Service ===", Colors.BOLD)

        try:
            # Test user registration
            registration_data = {
                "email": f"test_{int(time.time())}@nexafi.com",
                "password": "SecurePassword123!@#",
                "first_name": "Test",
                "last_name": "User",
                "phone": "1234567890",
                "company_name": "Test Company",
            }

            response = requests.post(
                f"{BASE_URL}/api/v1/auth/register", json=registration_data
            )
            if response.status_code == 201:
                data = response.json()
                self.success("User registration successful")
                self.test_data["user_email"] = registration_data["email"]
                self.test_data["user_password"] = registration_data["password"]
            else:
                self.error(f"User registration failed - {response.text}")
                return

            # Test user login
            login_data = {
                "email": registration_data["email"],
                "password": registration_data["password"],
            }

            response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.user_id = data.get("user", {}).get("id")
                self.success("User login successful")

                # Store tokens for other tests
                self.test_data["access_token"] = self.access_token
                self.test_data["user_id"] = str(self.user_id)
            else:
                self.error(f"User login failed - {response.text}")
                return

            # Test profile retrieval
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{BASE_URL}/api/v1/users/profile", headers=headers)
            if response.status_code == 200:
                self.success("Profile retrieval successful")
            else:
                self.error("Profile retrieval failed")

            # Test weak password rejection
            weak_password_data = {
                "email": f"weak_{int(time.time())}@nexafi.com",
                "password": "123",  # Weak password
                "first_name": "Weak",
                "last_name": "Password",
            }

            response = requests.post(
                f"{BASE_URL}/api/v1/auth/register", json=weak_password_data
            )
            if response.status_code == 400:
                self.success("Weak password properly rejected")
            else:
                self.warning("Weak password validation may not be working")

        except requests.exceptions.RequestException as e:
            self.error(f"User service test failed - {str(e)}")

    def test_ledger_service(self):
        self.log("\n=== Testing Ledger Service ===", Colors.BOLD)

        if not self.access_token:
            self.error("No access token available for ledger tests")
            return

        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            # Test account listing
            response = requests.get(f"{BASE_URL}/api/v1/accounts", headers=headers)
            if response.status_code == 200:
                data = response.json()
                accounts = data.get("accounts", [])
                self.success(
                    f"Account listing successful - found {len(accounts)} accounts"
                )

                # Store first account for testing
                if accounts:
                    self.test_data["account_id"] = accounts[0]["id"]
            else:
                self.error("Account listing failed")

            # Test account creation
            account_data = {
                "account_code": f"TEST{int(time.time())}",
                "name": "Test Account",
                "account_type": "asset",
                "account_subtype": "cash",
                "currency": "USD",
                "description": "Test account for validation",
            }

            response = requests.post(
                f"{BASE_URL}/api/v1/accounts", json=account_data, headers=headers
            )
            if response.status_code == 201:
                data = response.json()
                self.success("Account creation successful")
                self.test_data["created_account_id"] = data["account"]["id"]
            else:
                self.error(f"Account creation failed - {response.text}")

            # Test journal entry creation
            if "created_account_id" in self.test_data:
                journal_data = {
                    "description": "Test journal entry",
                    "reference_number": f"TEST-{int(time.time())}",
                    "lines": [
                        {
                            "account_id": self.test_data["created_account_id"],
                            "debit_amount": 100.00,
                            "description": "Test debit",
                        },
                        {
                            "account_id": self.test_data["created_account_id"],
                            "credit_amount": 100.00,
                            "description": "Test credit",
                        },
                    ],
                }

                response = requests.post(
                    f"{BASE_URL}/api/v1/journal-entries",
                    json=journal_data,
                    headers=headers,
                )
                if response.status_code == 201:
                    data = response.json()
                    self.success("Journal entry creation successful")
                    self.test_data["journal_entry_id"] = data["journal_entry"]["id"]
                else:
                    self.error(f"Journal entry creation failed - {response.text}")

            # Test trial balance report
            response = requests.get(
                f"{BASE_URL}/api/v1/reports/trial-balance", headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                self.success("Trial balance report generated successfully")
                if data.get("is_balanced"):
                    self.success("Trial balance is properly balanced")
                else:
                    self.warning("Trial balance is not balanced")
            else:
                self.error("Trial balance report failed")

        except requests.exceptions.RequestException as e:
            self.error(f"Ledger service test failed - {str(e)}")

    def test_compliance_service(self):
        """Test Compliance Service (AML, KYC, Sanctions)"""
        self.log("\n=== Testing Compliance Service ===", Colors.BOLD)

        if not self.access_token or not self.user_id:
            self.error("No access token or user ID available for compliance tests")
            return

        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            # Test KYC verification initiation
            kyc_data = {
                "user_id": self.user_id,
                "verification_type": "identity",
                "document_type": "passport",
                "document_number": "TEST123456",
            }

            response = requests.post(
                f"{BASE_URL}/api/v1/kyc/verify", json=kyc_data, headers=headers
            )
            if response.status_code == 201:
                data = response.json()
                self.success("KYC verification initiated successfully")
                self.test_data["kyc_verification_id"] = data["verification_id"]
            else:
                self.error(f"KYC verification failed - {response.text}")

            # Test AML check
            aml_data = {
                "transaction_id": f"TXN-{int(time.time())}",
                "user_id": self.user_id,
                "check_type": "transaction_monitoring",
                "transaction_data": {
                    "amount": 5000.00,
                    "currency": "USD",
                    "country": "US",
                    "daily_transaction_count": 1,
                },
            }

            response = requests.post(
                f"{BASE_URL}/api/v1/aml/check", json=aml_data, headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                self.success(
                    f"AML check completed - Risk level: {data.get('risk_level')}"
                )
            else:
                self.error(f"AML check failed - {response.text}")

            # Test sanctions screening
            sanctions_data = {
                "entity_id": self.user_id,
                "entity_type": "user",
                "entity_name": "Test User",
            }

            response = requests.post(
                f"{BASE_URL}/api/v1/sanctions/screen",
                json=sanctions_data,
                headers=headers,
            )
            if response.status_code == 200:
                data = response.json()
                self.success(
                    f"Sanctions screening completed - Result: {data.get('result')}"
                )
            else:
                self.error(f"Sanctions screening failed - {response.text}")

            # Test compliance dashboard
            response = requests.get(
                f"{BASE_URL}/api/v1/compliance/dashboard", headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                self.success("Compliance dashboard accessible")
            else:
                self.error("Compliance dashboard failed")

        except requests.exceptions.RequestException as e:
            self.error(f"Compliance service test failed - {str(e)}")

    def test_notification_service(self):
        """Test Notification Service"""
        self.log("\n=== Testing Notification Service ===", Colors.BOLD)

        if not self.access_token or not self.user_id:
            self.error("No access token or user ID available for notification tests")
            return

        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            # Test notification preferences retrieval
            response = requests.get(
                f"{BASE_URL}/api/v1/notifications/preferences/{self.user_id}",
                headers=headers,
            )
            if response.status_code == 200:
                self.success("Notification preferences retrieved successfully")
            else:
                self.error("Notification preferences retrieval failed")

            # Test sending a notification
            notification_data = {
                "user_id": self.user_id,
                "notification_type": "security_alert",
                "channel": "email",
                "priority": "high",
                "subject": "Test Security Alert",
                "message": "This is a test security alert notification.",
                "template_name": "security_alert_email",
                "template_data": {
                    "user_name": "Test User",
                    "alert_type": "Login from new device",
                    "timestamp": datetime.utcnow().isoformat(),
                    "ip_address": "192.168.1.1",
                    "details": "Test login alert",
                },
            }

            response = requests.post(
                f"{BASE_URL}/api/v1/notifications/send",
                json=notification_data,
                headers=headers,
            )
            if response.status_code == 201:
                data = response.json()
                self.success("Notification sent successfully")
                self.test_data["notification_id"] = data["notification_id"]
            else:
                self.error(f"Notification sending failed - {response.text}")

            # Test notification statistics
            response = requests.get(
                f"{BASE_URL}/api/v1/notifications/stats", headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                self.success("Notification statistics retrieved successfully")
            else:
                self.error("Notification statistics failed")

        except requests.exceptions.RequestException as e:
            self.error(f"Notification service test failed - {str(e)}")

    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        self.log("\n=== Testing Rate Limiting ===", Colors.BOLD)

        try:
            # Test rate limiting on login endpoint (5 attempts per 5 minutes)
            login_data = {
                "email": "nonexistent@example.com",
                "password": "wrongpassword",
            }

            rate_limited = False
            for i in range(7):  # Try 7 times to trigger rate limit
                response = requests.post(
                    f"{BASE_URL}/api/v1/auth/login", json=login_data
                )
                if response.status_code == 429:
                    rate_limited = True
                    self.success("Rate limiting is working - got 429 Too Many Requests")
                    break
                time.sleep(0.1)  # Small delay between requests

            if not rate_limited:
                self.warning("Rate limiting may not be working as expected")

        except requests.exceptions.RequestException as e:
            self.error(f"Rate limiting test failed - {str(e)}")

    def test_security_features(self):
        """Test security features"""
        self.log("\n=== Testing Security Features ===", Colors.BOLD)

        try:
            # Test unauthorized access
            response = requests.get(f"{BASE_URL}/api/v1/users/profile")
            if response.status_code == 401:
                self.success("Unauthorized access properly blocked")
            else:
                self.error("Unauthorized access not properly blocked")

            # Test invalid token
            headers = {"Authorization": "Bearer invalid_token"}
            response = requests.get(f"{BASE_URL}/api/v1/users/profile", headers=headers)
            if response.status_code == 401:
                self.success("Invalid token properly rejected")
            else:
                self.error("Invalid token not properly rejected")

            # Test SQL injection attempt
            malicious_data = {
                "email": "test'; DROP TABLE users; --",
                "password": "password",
            }

            response = requests.post(
                f"{BASE_URL}/api/v1/auth/login", json=malicious_data
            )
            if response.status_code in [
                400,
                401,
            ]:  # Should be rejected, not cause server error
                self.success("SQL injection attempt properly handled")
            else:
                self.warning("SQL injection handling unclear")

        except requests.exceptions.RequestException as e:
            self.error(f"Security test failed - {str(e)}")

    def test_audit_logging(self):
        """Test audit logging functionality"""
        self.log("\n=== Testing Audit Logging ===", Colors.BOLD)

        # Check if audit log files are being created
        audit_log_dir = "/home/ubuntu/nexafi_backend_refactored/logs/audit"
        if os.path.exists(audit_log_dir):
            log_files = os.listdir(audit_log_dir)
            if log_files:
                self.success(
                    f"Audit logs are being created - found {len(log_files)} log files"
                )
            else:
                self.warning("Audit log directory exists but no log files found")
        else:
            self.warning("Audit log directory not found")

        # Check general log files
        log_dir = "/home/ubuntu/nexafi_backend_refactored/logs"
        if os.path.exists(log_dir):
            log_files = [f for f in os.listdir(log_dir) if f.endswith(".log")]
            if log_files:
                self.success(
                    f"Service logs are being created - found {len(log_files)} log files"
                )
            else:
                self.warning("Log directory exists but no log files found")
        else:
            self.warning("Log directory not found")

    def run_all_tests(self):
        """Run all tests"""
        self.log(
            f"\n{Colors.BOLD}=== NexaFi Enhanced Backend Test Suite ==={Colors.ENDC}"
        )
        self.log(f"Testing against: {BASE_URL}")
        self.log(f"Timestamp: {datetime.utcnow().isoformat()}")

        # Wait a moment for services to be fully ready
        self.log("\nWaiting for services to be ready...")
        time.sleep(3)

        # Run tests in order
        self.test_health_checks()
        self.test_api_gateway()
        self.test_user_service()
        self.test_ledger_service()
        self.test_compliance_service()
        self.test_notification_service()
        self.test_rate_limiting()
        self.test_security_features()
        self.test_audit_logging()

        # Summary
        total_tests = self.passed + self.failed
        success_rate = (self.passed / total_tests * 100) if total_tests > 0 else 0

        self.log(f"\n{Colors.BOLD}=== Test Summary ==={Colors.ENDC}")
        self.log(f"Total tests: {total_tests}")
        self.log(f"Passed: {Colors.GREEN}{self.passed}{Colors.ENDC}")
        self.log(f"Failed: {Colors.RED}{self.failed}{Colors.ENDC}")
        self.log(f"Success rate: {success_rate:.1f}%")

        if self.failed == 0:
            self.log(
                f"\n{Colors.GREEN}{Colors.BOLD}🎉 All tests passed! NexaFi Enhanced Backend is working correctly.{Colors.ENDC}"
            )
            return True
        else:
            self.log(
                f"\n{Colors.RED}{Colors.BOLD}❌ Some tests failed. Please check the logs and fix the issues.{Colors.ENDC}"
            )
            return False


if __name__ == "__main__":
    runner = TestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)
