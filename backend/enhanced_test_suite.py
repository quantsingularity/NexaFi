#!/usr/bin/env python3
"""
Enhanced NexaFi Backend Test Suite
Comprehensive testing for all microservices and infrastructure components
"""

import requests
import json
import time
import sys
import threading
from datetime import datetime
from typing import Dict, List, Any

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class TestResult:
    """Test result container"""
    def __init__(self, name: str, passed: bool, message: str = "", duration: float = 0):
        self.name = name
        self.passed = passed
        self.message = message
        self.duration = duration

class NexaFiTestSuite:
    """Comprehensive test suite for NexaFi backend"""
    
    def __init__(self):
        self.base_urls = {
            'api-gateway': 'http://localhost:5000',
            'user-service': 'http://localhost:5001',
            'ledger-service': 'http://localhost:5002',
            'payment-service': 'http://localhost:5003',
            'ai-service': 'http://localhost:5004',
            'analytics-service': 'http://localhost:5005',
            'credit-service': 'http://localhost:5006',
            'document-service': 'http://localhost:5007'
        }
        
        self.infrastructure_urls = {
            'redis': 'localhost:6379',
            'rabbitmq': 'http://localhost:15672',
            'elasticsearch': 'http://localhost:9200',
            'kibana': 'http://localhost:5601'
        }
        
        self.test_results: List[TestResult] = []
        self.test_user_token = None
        self.test_user_id = None
    
    def print_header(self, text: str):
        """Print formatted header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")
    
    def print_test(self, name: str, passed: bool, message: str = "", duration: float = 0):
        """Print test result"""
        status = f"{Colors.GREEN}✅ PASS{Colors.END}" if passed else f"{Colors.RED}❌ FAIL{Colors.END}"
        duration_str = f" ({duration:.2f}s)" if duration > 0 else ""
        print(f"{status} {name}{duration_str}")
        if message:
            print(f"    {Colors.YELLOW}{message}{Colors.END}")
    
    def run_test(self, test_func, test_name: str) -> TestResult:
        """Run a single test and record result"""
        start_time = time.time()
        try:
            result = test_func()
            duration = time.time() - start_time
            
            if isinstance(result, tuple):
                passed, message = result
            else:
                passed, message = result, ""
            
            test_result = TestResult(test_name, passed, message, duration)
            self.test_results.append(test_result)
            self.print_test(test_name, passed, message, duration)
            return test_result
            
        except Exception as e:
            duration = time.time() - start_time
            test_result = TestResult(test_name, False, str(e), duration)
            self.test_results.append(test_result)
            self.print_test(test_name, False, str(e), duration)
            return test_result
    
    def test_infrastructure_health(self):
        """Test infrastructure services health"""
        self.print_header("INFRASTRUCTURE HEALTH TESTS")
        
        # Test Redis
        def test_redis():
            import redis
            try:
                r = redis.Redis(host='localhost', port=6379, decode_responses=True)
                r.ping()
                r.set('test_key', 'test_value')
                value = r.get('test_key')
                r.delete('test_key')
                return value == 'test_value', "Redis connection and operations successful"
            except Exception as e:
                return False, f"Redis error: {str(e)}"
        
        # Test RabbitMQ
        def test_rabbitmq():
            try:
                response = requests.get('http://localhost:15672', timeout=5)
                return response.status_code == 200, "RabbitMQ management interface accessible"
            except Exception as e:
                return False, f"RabbitMQ error: {str(e)}"
        
        # Test Elasticsearch
        def test_elasticsearch():
            try:
                response = requests.get('http://localhost:9200', timeout=5)
                return response.status_code == 200, "Elasticsearch accessible"
            except Exception as e:
                return False, f"Elasticsearch error: {str(e)}"
        
        # Test Kibana
        def test_kibana():
            try:
                response = requests.get('http://localhost:5601', timeout=5)
                return response.status_code == 200, "Kibana accessible"
            except Exception as e:
                return False, f"Kibana error: {str(e)}"
        
        self.run_test(test_redis, "Redis Connection and Operations")
        self.run_test(test_rabbitmq, "RabbitMQ Management Interface")
        self.run_test(test_elasticsearch, "Elasticsearch Health")
        self.run_test(test_kibana, "Kibana Dashboard")
    
    def test_service_health(self):
        """Test all microservices health endpoints"""
        self.print_header("MICROSERVICE HEALTH TESTS")
        
        for service_name, base_url in self.base_urls.items():
            def test_health(url=base_url, name=service_name):
                try:
                    response = requests.get(f"{url}/health", timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        return True, f"Service healthy: {data.get('status', 'unknown')}"
                    else:
                        return False, f"Health check failed with status {response.status_code}"
                except Exception as e:
                    return False, f"Health check error: {str(e)}"
            
            self.run_test(test_health, f"{service_name.title()} Health Check")
    
    def test_user_service_functionality(self):
        """Test user service core functionality"""
        self.print_header("USER SERVICE FUNCTIONALITY TESTS")
        
        # Test user registration
        def test_user_registration():
            try:
                user_data = {
                    "email": f"test_{int(time.time())}@nexafi.com",
                    "password": "TestPassword123!",
                    "first_name": "Test",
                    "last_name": "User",
                    "business_type": "technology",
                    "company_size": "1-10"
                }
                
                response = requests.post(
                    f"{self.base_urls['user-service']}/api/v1/auth/register",
                    json=user_data,
                    timeout=10
                )
                
                if response.status_code == 201:
                    data = response.json()
                    self.test_user_token = data.get('access_token')
                    self.test_user_id = data.get('user', {}).get('id')
                    return True, "User registration successful"
                else:
                    return False, f"Registration failed: {response.text}"
            except Exception as e:
                return False, f"Registration error: {str(e)}"
        
        # Test user login
        def test_user_login():
            if not self.test_user_token:
                return False, "No test user available for login test"
            
            try:
                # Get user profile to verify token works
                headers = {'Authorization': f'Bearer {self.test_user_token}'}
                response = requests.get(
                    f"{self.base_urls['user-service']}/api/v1/users/profile",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    return True, "User authentication successful"
                else:
                    return False, f"Authentication failed: {response.text}"
            except Exception as e:
                return False, f"Authentication error: {str(e)}"
        
        # Test profile update
        def test_profile_update():
            if not self.test_user_token:
                return False, "No test user available for profile update test"
            
            try:
                headers = {'Authorization': f'Bearer {self.test_user_token}'}
                update_data = {
                    "phone": "+1234567890",
                    "profile": {
                        "timezone": "UTC",
                        "language": "en"
                    }
                }
                
                response = requests.put(
                    f"{self.base_urls['user-service']}/api/v1/users/profile",
                    json=update_data,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    return True, "Profile update successful"
                else:
                    return False, f"Profile update failed: {response.text}"
            except Exception as e:
                return False, f"Profile update error: {str(e)}"
        
        self.run_test(test_user_registration, "User Registration")
        self.run_test(test_user_login, "User Authentication")
        self.run_test(test_profile_update, "Profile Update")
    
    def test_ledger_service_functionality(self):
        """Test ledger service core functionality"""
        self.print_header("LEDGER SERVICE FUNCTIONALITY TESTS")
        
        if not self.test_user_token:
            print(f"{Colors.YELLOW}⚠️  Skipping ledger tests - no authenticated user{Colors.END}")
            return
        
        headers = {'Authorization': f'Bearer {self.test_user_token}'}
        
        # Test chart of accounts
        def test_chart_of_accounts():
            try:
                response = requests.get(
                    f"{self.base_urls['ledger-service']}/api/v1/accounts",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    return True, "Chart of accounts accessible"
                else:
                    return False, f"Chart of accounts failed: {response.text}"
            except Exception as e:
                return False, f"Chart of accounts error: {str(e)}"
        
        # Test journal entry creation
        def test_journal_entry():
            try:
                entry_data = {
                    "description": "Test journal entry",
                    "reference": "TEST001",
                    "entries": [
                        {
                            "account_code": "1000",
                            "debit_amount": 100.00,
                            "credit_amount": 0.00
                        },
                        {
                            "account_code": "2000",
                            "debit_amount": 0.00,
                            "credit_amount": 100.00
                        }
                    ]
                }
                
                response = requests.post(
                    f"{self.base_urls['ledger-service']}/api/v1/journal-entries",
                    json=entry_data,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code in [200, 201]:
                    return True, "Journal entry creation successful"
                else:
                    return False, f"Journal entry failed: {response.text}"
            except Exception as e:
                return False, f"Journal entry error: {str(e)}"
        
        self.run_test(test_chart_of_accounts, "Chart of Accounts Access")
        self.run_test(test_journal_entry, "Journal Entry Creation")
    
    def test_payment_service_functionality(self):
        """Test payment service core functionality"""
        self.print_header("PAYMENT SERVICE FUNCTIONALITY TESTS")
        
        if not self.test_user_token:
            print(f"{Colors.YELLOW}⚠️  Skipping payment tests - no authenticated user{Colors.END}")
            return
        
        headers = {'Authorization': f'Bearer {self.test_user_token}'}
        
        # Test wallet creation
        def test_wallet_creation():
            try:
                wallet_data = {
                    "name": "Test Wallet",
                    "currency": "USD",
                    "wallet_type": "business"
                }
                
                response = requests.post(
                    f"{self.base_urls['payment-service']}/api/v1/wallets",
                    json=wallet_data,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code in [200, 201]:
                    return True, "Wallet creation successful"
                else:
                    return False, f"Wallet creation failed: {response.text}"
            except Exception as e:
                return False, f"Wallet creation error: {str(e)}"
        
        # Test payment methods
        def test_payment_methods():
            try:
                response = requests.get(
                    f"{self.base_urls['payment-service']}/api/v1/payment-methods",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    return True, "Payment methods accessible"
                else:
                    return False, f"Payment methods failed: {response.text}"
            except Exception as e:
                return False, f"Payment methods error: {str(e)}"
        
        self.run_test(test_wallet_creation, "Wallet Creation")
        self.run_test(test_payment_methods, "Payment Methods Access")
    
    def test_ai_service_functionality(self):
        """Test AI service core functionality"""
        self.print_header("AI SERVICE FUNCTIONALITY TESTS")
        
        if not self.test_user_token:
            print(f"{Colors.YELLOW}⚠️  Skipping AI tests - no authenticated user{Colors.END}")
            return
        
        headers = {'Authorization': f'Bearer {self.test_user_token}'}
        
        # Test financial insights
        def test_financial_insights():
            try:
                response = requests.get(
                    f"{self.base_urls['ai-service']}/api/v1/insights/financial",
                    headers=headers,
                    timeout=15
                )
                
                if response.status_code == 200:
                    return True, "Financial insights accessible"
                else:
                    return False, f"Financial insights failed: {response.text}"
            except Exception as e:
                return False, f"Financial insights error: {str(e)}"
        
        # Test cash flow prediction
        def test_cash_flow_prediction():
            try:
                prediction_data = {
                    "period_months": 6,
                    "include_seasonality": True
                }
                
                response = requests.post(
                    f"{self.base_urls['ai-service']}/api/v1/predictions/cash-flow",
                    json=prediction_data,
                    headers=headers,
                    timeout=15
                )
                
                if response.status_code in [200, 201]:
                    return True, "Cash flow prediction successful"
                else:
                    return False, f"Cash flow prediction failed: {response.text}"
            except Exception as e:
                return False, f"Cash flow prediction error: {str(e)}"
        
        self.run_test(test_financial_insights, "Financial Insights")
        self.run_test(test_cash_flow_prediction, "Cash Flow Prediction")
    
    def test_analytics_service_functionality(self):
        """Test analytics service core functionality"""
        self.print_header("ANALYTICS SERVICE FUNCTIONALITY TESTS")
        
        if not self.test_user_token:
            print(f"{Colors.YELLOW}⚠️  Skipping analytics tests - no authenticated user{Colors.END}")
            return
        
        headers = {'Authorization': f'Bearer {self.test_user_token}'}
        
        # Test dashboard creation
        def test_dashboard_creation():
            try:
                dashboard_data = {
                    "name": "Test Dashboard",
                    "description": "Test dashboard for validation",
                    "category": "financial"
                }
                
                response = requests.post(
                    f"{self.base_urls['analytics-service']}/api/v1/dashboards",
                    json=dashboard_data,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code in [200, 201]:
                    return True, "Dashboard creation successful"
                else:
                    return False, f"Dashboard creation failed: {response.text}"
            except Exception as e:
                return False, f"Dashboard creation error: {str(e)}"
        
        self.run_test(test_dashboard_creation, "Dashboard Creation")
    
    def test_credit_service_functionality(self):
        """Test credit service core functionality"""
        self.print_header("CREDIT SERVICE FUNCTIONALITY TESTS")
        
        if not self.test_user_token:
            print(f"{Colors.YELLOW}⚠️  Skipping credit tests - no authenticated user{Colors.END}")
            return
        
        headers = {'Authorization': f'Bearer {self.test_user_token}'}
        
        # Test credit score calculation
        def test_credit_score():
            try:
                score_data = {
                    "annual_income": 75000,
                    "total_debt": 25000,
                    "payment_history_months": 24,
                    "business_revenue": 100000,
                    "business_age_months": 36
                }
                
                response = requests.post(
                    f"{self.base_urls['credit-service']}/api/v1/credit-scores/calculate",
                    json=score_data,
                    headers=headers,
                    timeout=15
                )
                
                if response.status_code in [200, 201]:
                    return True, "Credit score calculation successful"
                else:
                    return False, f"Credit score calculation failed: {response.text}"
            except Exception as e:
                return False, f"Credit score calculation error: {str(e)}"
        
        self.run_test(test_credit_score, "Credit Score Calculation")
    
    def test_load_performance(self):
        """Test system performance under load"""
        self.print_header("LOAD PERFORMANCE TESTS")
        
        def test_concurrent_requests():
            """Test concurrent requests to health endpoints"""
            results = []
            
            def make_request(service_name, url):
                try:
                    start_time = time.time()
                    response = requests.get(f"{url}/health", timeout=5)
                    duration = time.time() - start_time
                    results.append((service_name, response.status_code == 200, duration))
                except Exception as e:
                    results.append((service_name, False, 0))
            
            # Create threads for concurrent requests
            threads = []
            for service_name, base_url in self.base_urls.items():
                for _ in range(5):  # 5 concurrent requests per service
                    thread = threading.Thread(target=make_request, args=(service_name, base_url))
                    threads.append(thread)
            
            # Start all threads
            start_time = time.time()
            for thread in threads:
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            total_duration = time.time() - start_time
            
            # Analyze results
            successful_requests = sum(1 for _, success, _ in results if success)
            total_requests = len(results)
            avg_response_time = sum(duration for _, _, duration in results) / len(results)
            
            success_rate = (successful_requests / total_requests) * 100
            
            if success_rate >= 95 and avg_response_time < 2.0:
                return True, f"Load test passed: {success_rate:.1f}% success rate, {avg_response_time:.2f}s avg response time"
            else:
                return False, f"Load test failed: {success_rate:.1f}% success rate, {avg_response_time:.2f}s avg response time"
        
        self.run_test(test_concurrent_requests, "Concurrent Request Load Test")
    
    def generate_report(self):
        """Generate comprehensive test report"""
        self.print_header("TEST REPORT SUMMARY")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.passed)
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        total_duration = sum(result.duration for result in self.test_results)
        
        print(f"{Colors.BOLD}📊 Test Statistics:{Colors.END}")
        print(f"   Total Tests: {total_tests}")
        print(f"   {Colors.GREEN}Passed: {passed_tests}{Colors.END}")
        print(f"   {Colors.RED}Failed: {failed_tests}{Colors.END}")
        print(f"   Success Rate: {Colors.GREEN if success_rate >= 90 else Colors.RED}{success_rate:.1f}%{Colors.END}")
        print(f"   Total Duration: {total_duration:.2f}s")
        
        if failed_tests > 0:
            print(f"\n{Colors.RED}❌ Failed Tests:{Colors.END}")
            for result in self.test_results:
                if not result.passed:
                    print(f"   • {result.name}: {result.message}")
        
        print(f"\n{Colors.BOLD}🎯 Overall Status: ", end="")
        if success_rate >= 95:
            print(f"{Colors.GREEN}EXCELLENT{Colors.END}")
        elif success_rate >= 90:
            print(f"{Colors.YELLOW}GOOD{Colors.END}")
        elif success_rate >= 80:
            print(f"{Colors.YELLOW}ACCEPTABLE{Colors.END}")
        else:
            print(f"{Colors.RED}NEEDS IMPROVEMENT{Colors.END}")
        
        # Save report to file
        report_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'total_duration': total_duration,
            'test_results': [
                {
                    'name': result.name,
                    'passed': result.passed,
                    'message': result.message,
                    'duration': result.duration
                }
                for result in self.test_results
            ]
        }
        
        with open('logs/test_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: logs/test_report.json")
        
        return success_rate >= 80
    
    def run_all_tests(self):
        """Run all test suites"""
        print(f"{Colors.BOLD}{Colors.PURPLE}")
        print("🧪 NexaFi Enhanced Backend Test Suite")
        print("=====================================")
        print(f"{Colors.END}")
        
        # Run all test suites
        self.test_infrastructure_health()
        self.test_service_health()
        self.test_user_service_functionality()
        self.test_ledger_service_functionality()
        self.test_payment_service_functionality()
        self.test_ai_service_functionality()
        self.test_analytics_service_functionality()
        self.test_credit_service_functionality()
        self.test_load_performance()
        
        # Generate final report
        success = self.generate_report()
        
        return success

def main():
    """Main test execution"""
    test_suite = NexaFiTestSuite()
    
    try:
        success = test_suite.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Tests interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Test suite error: {str(e)}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()

