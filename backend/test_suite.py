#!/usr/bin/env python3
"""
NexaFi Backend Test Suite
Comprehensive testing for all microservices
"""

import requests
import json
import time
import sys
from datetime import datetime, date

# Service configurations
SERVICES = {
    'user-service': {'port': 5001, 'base_url': 'http://localhost:5001/api/v1'},
    'ledger-service': {'port': 5002, 'base_url': 'http://localhost:5002/api/v1'},
    'payment-service': {'port': 5003, 'base_url': 'http://localhost:5003/api/v1'},
    'ai-service': {'port': 5004, 'base_url': 'http://localhost:5004/api/v1'},
}

class NexaFiTester:
    def __init__(self):
        self.test_results = {}
        self.access_token = None
        self.test_user_id = None
        
    def log(self, message, level='INFO'):
        """Log test messages"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {level}: {message}")
    
    def test_service_health(self, service_name):
        """Test service health endpoint"""
        try:
            url = f"{SERVICES[service_name]['base_url']}/health"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                self.log(f"✅ {service_name} health check passed")
                return True
            else:
                self.log(f"❌ {service_name} health check failed: {response.status_code}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"❌ {service_name} health check failed: {str(e)}", 'ERROR')
            return False
    
    def test_user_service(self):
        """Test User Service functionality"""
        self.log("Testing User Service...")
        base_url = SERVICES['user-service']['base_url']
        
        # Test user registration
        try:
            register_data = {
                'email': 'test@nexafi.com',
                'password': 'TestPassword123!',
                'first_name': 'Test',
                'last_name': 'User'
            }
            
            response = requests.post(f"{base_url}/auth/register", json=register_data)
            
            if response.status_code == 201:
                self.log("✅ User registration successful")
                user_data = response.json()
                self.test_user_id = user_data['user']['id']
            else:
                self.log(f"❌ User registration failed: {response.status_code} - {response.text}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"❌ User registration failed: {str(e)}", 'ERROR')
            return False
        
        # Test user login
        try:
            login_data = {
                'email': 'test@nexafi.com',
                'password': 'TestPassword123!'
            }
            
            response = requests.post(f"{base_url}/auth/login", json=login_data)
            
            if response.status_code == 200:
                self.log("✅ User login successful")
                login_result = response.json()
                self.access_token = login_result['access_token']
            else:
                self.log(f"❌ User login failed: {response.status_code} - {response.text}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"❌ User login failed: {str(e)}", 'ERROR')
            return False
        
        # Test profile update
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            profile_data = {
                'business_name': 'Test Business Inc.',
                'business_type': 'Technology',
                'industry': 'Software',
                'annual_revenue': 500000,
                'employee_count': 10
            }
            
            response = requests.put(f"{base_url}/users/profile", json=profile_data, headers=headers)
            
            if response.status_code == 200:
                self.log("✅ Profile update successful")
            else:
                self.log(f"❌ Profile update failed: {response.status_code} - {response.text}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"❌ Profile update failed: {str(e)}", 'ERROR')
            return False
        
        return True
    
    def test_ledger_service(self):
        """Test Ledger Service functionality"""
        self.log("Testing Ledger Service...")
        base_url = SERVICES['ledger-service']['base_url']
        headers = {'X-User-ID': self.test_user_id}
        
        # Test account initialization
        try:
            response = requests.post(f"{base_url}/accounts/initialize", headers=headers)
            
            if response.status_code == 201:
                self.log("✅ Chart of accounts initialization successful")
            else:
                self.log(f"❌ Chart of accounts initialization failed: {response.status_code} - {response.text}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"❌ Chart of accounts initialization failed: {str(e)}", 'ERROR')
            return False
        
        # Test getting accounts
        try:
            response = requests.get(f"{base_url}/accounts", headers=headers)
            
            if response.status_code == 200:
                accounts_data = response.json()
                self.log(f"✅ Retrieved {accounts_data['total']} accounts")
                
                # Store some account IDs for journal entry testing
                self.cash_account_id = None
                self.revenue_account_id = None
                
                for account in accounts_data['accounts']:
                    if account['account_code'] == '1000':  # Cash account
                        self.cash_account_id = account['id']
                    elif account['account_code'] == '4000':  # Revenue account
                        self.revenue_account_id = account['id']
                        
            else:
                self.log(f"❌ Getting accounts failed: {response.status_code} - {response.text}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"❌ Getting accounts failed: {str(e)}", 'ERROR')
            return False
        
        # Test journal entry creation
        if self.cash_account_id and self.revenue_account_id:
            try:
                journal_data = {
                    'description': 'Test revenue entry',
                    'entry_date': date.today().isoformat(),
                    'lines': [
                        {
                            'account_id': self.cash_account_id,
                            'description': 'Cash received',
                            'debit_amount': 1000,
                            'credit_amount': 0
                        },
                        {
                            'account_id': self.revenue_account_id,
                            'description': 'Revenue earned',
                            'debit_amount': 0,
                            'credit_amount': 1000
                        }
                    ],
                    'auto_post': True
                }
                
                response = requests.post(f"{base_url}/journal-entries", json=journal_data, headers=headers)
                
                if response.status_code == 201:
                    self.log("✅ Journal entry creation successful")
                else:
                    self.log(f"❌ Journal entry creation failed: {response.status_code} - {response.text}", 'ERROR')
                    return False
                    
            except Exception as e:
                self.log(f"❌ Journal entry creation failed: {str(e)}", 'ERROR')
                return False
        
        # Test trial balance report
        try:
            response = requests.get(f"{base_url}/reports/trial-balance", headers=headers)
            
            if response.status_code == 200:
                trial_balance = response.json()
                self.log(f"✅ Trial balance generated - Balanced: {trial_balance['is_balanced']}")
            else:
                self.log(f"❌ Trial balance generation failed: {response.status_code} - {response.text}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"❌ Trial balance generation failed: {str(e)}", 'ERROR')
            return False
        
        return True
    
    def test_payment_service(self):
        """Test Payment Service functionality"""
        self.log("Testing Payment Service...")
        base_url = SERVICES['payment-service']['base_url']
        headers = {'X-User-ID': self.test_user_id}
        
        # Test payment method creation
        try:
            payment_method_data = {
                'type': 'card',
                'provider': 'stripe',
                'details': {
                    'last_four': '4242',
                    'brand': 'visa',
                    'exp_month': 12,
                    'exp_year': 2025
                },
                'is_default': True
            }
            
            response = requests.post(f"{base_url}/payment-methods", json=payment_method_data, headers=headers)
            
            if response.status_code == 201:
                self.log("✅ Payment method creation successful")
                payment_method = response.json()['payment_method']
                self.payment_method_id = payment_method['id']
            else:
                self.log(f"❌ Payment method creation failed: {response.status_code} - {response.text}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"❌ Payment method creation failed: {str(e)}", 'ERROR')
            return False
        
        # Test transaction creation
        try:
            transaction_data = {
                'payment_method_id': self.payment_method_id,
                'transaction_type': 'payment',
                'amount': 250.00,
                'currency': 'USD',
                'description': 'Test payment transaction'
            }
            
            response = requests.post(f"{base_url}/transactions", json=transaction_data, headers=headers)
            
            if response.status_code == 201:
                self.log("✅ Transaction creation successful")
                transaction = response.json()['transaction']
                self.transaction_id = transaction['id']
            else:
                self.log(f"❌ Transaction creation failed: {response.status_code} - {response.text}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"❌ Transaction creation failed: {str(e)}", 'ERROR')
            return False
        
        # Test wallet retrieval
        try:
            response = requests.get(f"{base_url}/wallets/USD", headers=headers)
            
            if response.status_code == 200:
                wallet = response.json()['wallet']
                self.log(f"✅ Wallet retrieved - Balance: ${wallet['balance']}")
            else:
                self.log(f"❌ Wallet retrieval failed: {response.status_code} - {response.text}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"❌ Wallet retrieval failed: {str(e)}", 'ERROR')
            return False
        
        # Test payment analytics
        try:
            from datetime import timedelta
            start_date = (date.today() - timedelta(days=30)).isoformat()
            end_date = date.today().isoformat()
            
            response = requests.get(f"{base_url}/analytics/summary?start_date={start_date}&end_date={end_date}", headers=headers)
            
            if response.status_code == 200:
                analytics = response.json()
                self.log(f"✅ Payment analytics retrieved - Total volume: ${analytics['summary']['total_volume']}")
            else:
                self.log(f"❌ Payment analytics failed: {response.status_code} - {response.text}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"❌ Payment analytics failed: {str(e)}", 'ERROR')
            return False
        
        return True
    
    def test_ai_service(self):
        """Test AI Service functionality"""
        self.log("Testing AI Service...")
        base_url = SERVICES['ai-service']['base_url']
        headers = {'X-User-ID': self.test_user_id}
        
        # Test cash flow prediction
        try:
            prediction_data = {
                'historical_data': {
                    'average_monthly_cash_flow': 15000,
                    'seasonal_patterns': True,
                    'growth_trend': 0.02
                },
                'days_ahead': 30
            }
            
            response = requests.post(f"{base_url}/predictions/cash-flow", json=prediction_data, headers=headers)
            
            if response.status_code == 200:
                prediction = response.json()
                self.log(f"✅ Cash flow prediction successful - Confidence: {prediction['summary']['confidence_score']}")
            else:
                self.log(f"❌ Cash flow prediction failed: {response.status_code} - {response.text}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"❌ Cash flow prediction failed: {str(e)}", 'ERROR')
            return False
        
        # Test credit score calculation
        try:
            credit_data = {
                'business_data': {
                    'annual_revenue': 500000,
                    'business_age_months': 24,
                    'employee_count': 10,
                    'industry': 'Technology'
                }
            }
            
            response = requests.post(f"{base_url}/predictions/credit-score", json=credit_data, headers=headers)
            
            if response.status_code == 200:
                credit_result = response.json()
                self.log(f"✅ Credit score calculation successful - Score: {credit_result['credit_score']}")
            else:
                self.log(f"❌ Credit score calculation failed: {response.status_code} - {response.text}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"❌ Credit score calculation failed: {str(e)}", 'ERROR')
            return False
        
        # Test insights generation
        try:
            insights_data = {
                'financial_data': {
                    'cash_flow_trend': 'declining',
                    'current_cash_flow': 12000,
                    'previous_cash_flow': 15000,
                    'unusual_expenses': True,
                    'marketing_expenses': 3500,
                    'avg_marketing_expenses': 2500
                }
            }
            
            response = requests.post(f"{base_url}/insights/generate", json=insights_data, headers=headers)
            
            if response.status_code == 201:
                insights = response.json()
                self.log(f"✅ Insights generation successful - Generated {len(insights['insights'])} insights")
            else:
                self.log(f"❌ Insights generation failed: {response.status_code} - {response.text}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"❌ Insights generation failed: {str(e)}", 'ERROR')
            return False
        
        # Test chat session creation
        try:
            session_data = {
                'session_name': 'Test Chat Session'
            }
            
            response = requests.post(f"{base_url}/chat/sessions", json=session_data, headers=headers)
            
            if response.status_code == 201:
                session = response.json()['session']
                self.chat_session_id = session['id']
                self.log("✅ Chat session creation successful")
            else:
                self.log(f"❌ Chat session creation failed: {response.status_code} - {response.text}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"❌ Chat session creation failed: {str(e)}", 'ERROR')
            return False
        
        # Test chat message
        try:
            message_data = {
                'message': 'Can you help me analyze my cash flow?'
            }
            
            response = requests.post(f"{base_url}/chat/sessions/{self.chat_session_id}/messages", json=message_data, headers=headers)
            
            if response.status_code == 201:
                chat_result = response.json()
                self.log("✅ Chat message successful")
                self.log(f"AI Response: {chat_result['ai_response']['content'][:100]}...")
            else:
                self.log(f"❌ Chat message failed: {response.status_code} - {response.text}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"❌ Chat message failed: {str(e)}", 'ERROR')
            return False
        
        return True
    
    def run_all_tests(self):
        """Run all tests"""
        self.log("🚀 Starting NexaFi Backend Test Suite")
        self.log("=" * 50)
        
        # Test service health
        self.log("Testing service health...")
        health_results = {}
        for service_name in SERVICES:
            health_results[service_name] = self.test_service_health(service_name)
        
        # Check if all services are healthy
        if not all(health_results.values()):
            self.log("❌ Some services are not healthy. Please start all services first.", 'ERROR')
            return False
        
        self.log("✅ All services are healthy")
        self.log("=" * 50)
        
        # Run functional tests
        test_functions = [
            ('User Service', self.test_user_service),
            ('Ledger Service', self.test_ledger_service),
            ('Payment Service', self.test_payment_service),
            ('AI Service', self.test_ai_service),
        ]
        
        results = {}
        for test_name, test_function in test_functions:
            self.log(f"Running {test_name} tests...")
            try:
                results[test_name] = test_function()
                if results[test_name]:
                    self.log(f"✅ {test_name} tests passed")
                else:
                    self.log(f"❌ {test_name} tests failed", 'ERROR')
            except Exception as e:
                self.log(f"❌ {test_name} tests failed with exception: {str(e)}", 'ERROR')
                results[test_name] = False
            
            self.log("-" * 30)
        
        # Summary
        self.log("=" * 50)
        self.log("TEST SUMMARY")
        self.log("=" * 50)
        
        passed_tests = sum(1 for result in results.values() if result)
        total_tests = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            self.log(f"{test_name}: {status}")
        
        self.log(f"Overall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            self.log("🎉 All tests passed! NexaFi backend is working correctly.")
            return True
        else:
            self.log("⚠️  Some tests failed. Please check the logs above.", 'ERROR')
            return False

if __name__ == '__main__':
    tester = NexaFiTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

