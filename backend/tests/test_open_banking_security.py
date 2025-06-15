"""
Comprehensive Test Suite for Open Banking Compliance and Enhanced Security
"""

import unittest
import json
import time
import secrets
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add shared modules to path
sys.path.append('/home/ubuntu/NexaFi/backend/shared')

from open_banking_compliance import (
    FAPI2SecurityProfile, PSD2ConsentManager, SCAManager,
    OpenBankingAPIValidator, TransactionRiskAnalysis,
    ConsentStatus, SCAStatus, AuthenticationMethod
)
from enhanced_security import (
    AdvancedEncryption, MultiFactorAuthentication, SecurityMonitor,
    SecurityEvent, SecurityEventType, ThreatLevel, FraudDetectionEngine,
    SecureSessionManager, SecurityLevel
)

class TestFAPI2SecurityProfile(unittest.TestCase):
    """Test FAPI 2.0 Security Profile implementation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = '/tmp/test_keys'
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self.fapi = FAPI2SecurityProfile(
            private_key_path=f'{self.temp_dir}/test_private.pem',
            public_key_path=f'{self.temp_dir}/test_public.pem'
        )
    
    def test_jwt_creation_and_verification(self):
        """Test JWT creation and verification"""
        payload = {'test': 'data', 'user_id': '12345'}
        audience = 'test-client'
        issuer = 'test-issuer'
        
        # Create JWT
        token = self.fapi.create_signed_jwt(payload, audience, issuer)
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 100)  # JWT should be substantial length
        
        # Verify JWT
        verified_payload = self.fapi.verify_jwt(token, audience, issuer)
        self.assertEqual(verified_payload['test'], 'data')
        self.assertEqual(verified_payload['user_id'], '12345')
        self.assertEqual(verified_payload['aud'], audience)
        self.assertEqual(verified_payload['iss'], issuer)
        
        # Verify required claims exist
        required_claims = ['iss', 'aud', 'iat', 'exp', 'jti']
        for claim in required_claims:
            self.assertIn(claim, verified_payload)
    
    def test_jwt_verification_with_wrong_audience(self):
        """Test JWT verification fails with wrong audience"""
        payload = {'test': 'data'}
        token = self.fapi.create_signed_jwt(payload, 'correct-audience', 'issuer')
        
        with self.assertRaises(ValueError):
            self.fapi.verify_jwt(token, 'wrong-audience', 'issuer')
    
    def test_dpop_proof_creation(self):
        """Test DPoP proof creation"""
        http_method = 'POST'
        http_uri = 'https://api.example.com/resource'
        access_token = 'test-access-token'
        
        dpop_proof = self.fapi.create_dpop_proof(http_method, http_uri, access_token)
        self.assertIsInstance(dpop_proof, str)
        self.assertTrue(len(dpop_proof) > 100)
        
        # Verify DPoP proof structure (basic check)
        parts = dpop_proof.split('.')
        self.assertEqual(len(parts), 3)  # Header.Payload.Signature
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

class TestPSD2ConsentManager(unittest.TestCase):
    """Test PSD2 Consent Management"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db = Mock()
        self.mock_db.execute_query = Mock()
        self.mock_db.fetch_one = Mock()
        
        self.consent_manager = PSD2ConsentManager(self.mock_db)
    
    def test_create_consent(self):
        """Test consent creation"""
        psu_id = 'user123'
        tpp_id = 'tpp456'
        access_data = {
            'accounts': ['account1', 'account2'],
            'balances': ['account1'],
            'transactions': ['account1']
        }
        
        consent = self.consent_manager.create_consent(
            psu_id, tpp_id, access_data
        )
        
        self.assertIsNotNone(consent.consent_id)
        self.assertEqual(consent.psu_id, psu_id)
        self.assertEqual(consent.tpp_id, tpp_id)
        self.assertEqual(consent.status, ConsentStatus.RECEIVED)
        self.assertEqual(consent.access, access_data)
        
        # Verify database call was made
        self.mock_db.execute_query.assert_called()
    
    def test_validate_consent_success(self):
        """Test successful consent validation"""
        consent_id = 'consent123'
        tpp_id = 'tpp456'
        
        # Mock database response
        self.mock_db.fetch_one.return_value = {
            'consent_id': consent_id,
            'tpp_id': tpp_id,
            'status': ConsentStatus.VALID.value,
            'valid_until': (datetime.utcnow() + timedelta(days=30)).isoformat(),
            'psu_id': 'user123',
            'frequency_per_day': 4,
            'recurring_indicator': False,
            'combined_service_indicator': False,
            'access_data': json.dumps({'accounts': ['account1']}),
            'creation_date_time': datetime.utcnow().isoformat(),
            'status_change_date_time': datetime.utcnow().isoformat()
        }
        
        is_valid, message = self.consent_manager.validate_consent(consent_id, tpp_id)
        
        self.assertTrue(is_valid)
        self.assertEqual(message, "Consent is valid")
    
    def test_validate_consent_expired(self):
        """Test consent validation with expired consent"""
        consent_id = 'consent123'
        tpp_id = 'tpp456'
        
        # Mock expired consent
        self.mock_db.fetch_one.return_value = {
            'consent_id': consent_id,
            'tpp_id': tpp_id,
            'status': ConsentStatus.VALID.value,
            'valid_until': (datetime.utcnow() - timedelta(days=1)).isoformat(),
            'psu_id': 'user123',
            'frequency_per_day': 4,
            'recurring_indicator': False,
            'combined_service_indicator': False,
            'access_data': json.dumps({'accounts': ['account1']}),
            'creation_date_time': datetime.utcnow().isoformat(),
            'status_change_date_time': datetime.utcnow().isoformat()
        }
        
        is_valid, message = self.consent_manager.validate_consent(consent_id, tpp_id)
        
        self.assertFalse(is_valid)
        self.assertEqual(message, "Consent has expired")

class TestSCAManager(unittest.TestCase):
    """Test Strong Customer Authentication Manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db = Mock()
        self.mock_db.execute_query = Mock()
        self.mock_db.fetch_one = Mock()
        
        self.sca_manager = SCAManager(self.mock_db)
    
    def test_initiate_sca(self):
        """Test SCA initiation"""
        psu_id = 'user123'
        sca_method = AuthenticationMethod.SMS_OTP
        consent_id = 'consent456'
        
        sca_data = self.sca_manager.initiate_sca(psu_id, sca_method, consent_id)
        
        self.assertIsNotNone(sca_data.authentication_id)
        self.assertEqual(sca_data.status, SCAStatus.RECEIVED)
        self.assertEqual(sca_data.sca_method, sca_method)
        self.assertIsNotNone(sca_data.challenge_data)
        self.assertIsNotNone(sca_data.expires_at)
        
        # Verify database call was made
        self.mock_db.execute_query.assert_called()
    
    def test_verify_sca_success(self):
        """Test successful SCA verification"""
        authentication_id = 'auth123'
        challenge_response = '123456'
        
        # Mock database response
        self.mock_db.fetch_one.return_value = {
            'authentication_id': authentication_id,
            'challenge_data': challenge_response,
            'expires_at': (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
            'attempts': 0,
            'max_attempts': 3
        }
        
        is_verified, status = self.sca_manager.verify_sca(authentication_id, challenge_response)
        
        self.assertTrue(is_verified)
        self.assertEqual(status, SCAStatus.FINALISED)
    
    def test_verify_sca_expired(self):
        """Test SCA verification with expired challenge"""
        authentication_id = 'auth123'
        challenge_response = '123456'
        
        # Mock expired challenge
        self.mock_db.fetch_one.return_value = {
            'authentication_id': authentication_id,
            'challenge_data': challenge_response,
            'expires_at': (datetime.utcnow() - timedelta(minutes=1)).isoformat(),
            'attempts': 0,
            'max_attempts': 3
        }
        
        is_verified, status = self.sca_manager.verify_sca(authentication_id, challenge_response)
        
        self.assertFalse(is_verified)
        self.assertEqual(status, SCAStatus.FAILED)

class TestAdvancedEncryption(unittest.TestCase):
    """Test Advanced Encryption utilities"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.encryption = AdvancedEncryption('test-master-key')
    
    def test_encrypt_decrypt_sensitive_data(self):
        """Test encryption and decryption of sensitive data"""
        original_data = "sensitive-information-123"
        
        # Encrypt data
        encrypted_data = self.encryption.encrypt_sensitive_data(original_data)
        self.assertNotEqual(encrypted_data, original_data)
        self.assertIsInstance(encrypted_data, str)
        
        # Decrypt data
        decrypted_data = self.encryption.decrypt_sensitive_data(encrypted_data)
        self.assertEqual(decrypted_data, original_data)
    
    def test_encrypt_decrypt_with_expiry(self):
        """Test encryption with expiry validation"""
        original_data = "time-sensitive-data"
        
        encrypted_data = self.encryption.encrypt_sensitive_data(original_data)
        
        # Should decrypt successfully within time limit
        decrypted_data = self.encryption.decrypt_sensitive_data(encrypted_data, max_age_seconds=60)
        self.assertEqual(decrypted_data, original_data)
        
        # Should fail with very short time limit
        with self.assertRaises(ValueError):
            self.encryption.decrypt_sensitive_data(encrypted_data, max_age_seconds=0)
    
    def test_field_level_encryption(self):
        """Test field-level encryption and decryption"""
        original_data = {
            'name': 'John Doe',
            'ssn': '123-45-6789',
            'account_number': '9876543210',
            'public_info': 'This is public'
        }
        
        sensitive_fields = ['ssn', 'account_number']
        
        # Encrypt sensitive fields
        encrypted_data = self.encryption.encrypt_field_level(original_data, sensitive_fields)
        
        # Verify sensitive fields are encrypted
        self.assertNotEqual(encrypted_data['ssn'], original_data['ssn'])
        self.assertNotEqual(encrypted_data['account_number'], original_data['account_number'])
        
        # Verify non-sensitive fields are unchanged
        self.assertEqual(encrypted_data['name'], original_data['name'])
        self.assertEqual(encrypted_data['public_info'], original_data['public_info'])
        
        # Decrypt sensitive fields
        decrypted_data = self.encryption.decrypt_field_level(encrypted_data, sensitive_fields)
        
        # Verify all data matches original
        self.assertEqual(decrypted_data, original_data)

class TestMultiFactorAuthentication(unittest.TestCase):
    """Test Multi-Factor Authentication"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db = Mock()
        self.mock_db.execute_query = Mock()
        self.mock_db.fetch_one = Mock()
        
        self.mfa = MultiFactorAuthentication(self.mock_db)
    
    def test_setup_totp(self):
        """Test TOTP setup"""
        user_id = 'user123'
        user_email = 'user@example.com'
        
        secret, provisioning_uri, backup_codes = self.mfa.setup_totp(user_id, user_email)
        
        # Verify secret is generated
        self.assertIsInstance(secret, str)
        self.assertTrue(len(secret) >= 16)
        
        # Verify provisioning URI contains expected elements
        self.assertIn('otpauth://totp/', provisioning_uri)
        self.assertIn(user_email, provisioning_uri)
        self.assertIn('NexaFi', provisioning_uri)
        
        # Verify backup codes are generated
        self.assertEqual(len(backup_codes), 10)
        for code in backup_codes:
            self.assertIsInstance(code, str)
            self.assertTrue(len(code) >= 8)
        
        # Verify database call was made
        self.mock_db.execute_query.assert_called()
    
    @patch('pyotp.TOTP')
    def test_verify_totp_success(self, mock_totp_class):
        """Test successful TOTP verification"""
        user_id = 'user123'
        token = '123456'
        
        # Mock database response
        self.mock_db.fetch_one.return_value = {
            'totp_secret': 'test-secret',
            'last_totp_used': int(time.time()) - 60  # 1 minute ago
        }
        
        # Mock TOTP verification
        mock_totp = Mock()
        mock_totp.verify.return_value = True
        mock_totp_class.return_value = mock_totp
        
        result = self.mfa.verify_totp(user_id, token)
        
        self.assertTrue(result)
        
        # Verify TOTP was called with correct secret
        mock_totp_class.assert_called_with('test-secret')
    
    def test_verify_backup_code_success(self):
        """Test successful backup code verification"""
        user_id = 'user123'
        backup_code = 'ABCD1234'
        
        # Mock database response
        backup_codes = ['ABCD1234', 'EFGH5678', 'IJKL9012']
        used_codes = ['MNOP3456']  # Different code already used
        
        self.mock_db.fetch_one.return_value = {
            'backup_codes': json.dumps(backup_codes),
            'recovery_codes_used': json.dumps(used_codes)
        }
        
        result = self.mfa.verify_backup_code(user_id, backup_code)
        
        self.assertTrue(result)
        
        # Verify database update was called to mark code as used
        self.mock_db.execute_query.assert_called()

class TestFraudDetectionEngine(unittest.TestCase):
    """Test Fraud Detection Engine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db = Mock()
        self.mock_db.execute_query = Mock()
        self.mock_db.fetch_one = Mock()
        self.mock_db.fetch_all = Mock()
        
        self.fraud_engine = FraudDetectionEngine(self.mock_db)
    
    def test_analyze_login_behavior_new_ip(self):
        """Test login behavior analysis with new IP"""
        user_id = 'user123'
        ip_address = '192.168.1.100'
        user_agent = 'Mozilla/5.0 Test Browser'
        device_fingerprint = 'device123'
        
        # Mock empty behavior cache (new user)
        risk_score, risk_factors = self.fraud_engine.analyze_login_behavior(
            user_id, ip_address, user_agent, device_fingerprint
        )
        
        # New IP should add some risk
        self.assertGreater(risk_score, 0)
        self.assertIn('new_device', risk_factors)
    
    def test_analyze_transaction_behavior_high_amount(self):
        """Test transaction behavior analysis with high amount"""
        user_id = 'user123'
        amount = 10000.0  # High amount
        currency = 'USD'
        merchant_category = 'gambling'  # High-risk category
        ip_address = '192.168.1.100'
        
        # Mock recent transactions
        self.mock_db.fetch_all.return_value = []  # No recent transactions
        
        risk_score, risk_factors = self.fraud_engine.analyze_transaction_behavior(
            user_id, amount, currency, merchant_category, ip_address
        )
        
        # High amount and risky merchant should increase risk
        self.assertGreater(risk_score, 50)
        self.assertIn('high_risk_merchant', risk_factors)
    
    def test_create_fraud_alert(self):
        """Test fraud alert creation"""
        user_id = 'user123'
        alert_type = 'suspicious_login'
        risk_score = 75
        details = {'ip_address': '192.168.1.100', 'reason': 'new_location'}
        
        # Mock database response
        mock_result = Mock()
        mock_result.lastrowid = 12345
        self.mock_db.execute_query.return_value = mock_result
        
        alert_id = self.fraud_engine.create_fraud_alert(user_id, alert_type, risk_score, details)
        
        self.assertEqual(alert_id, 12345)
        self.mock_db.execute_query.assert_called()

class TestTransactionRiskAnalysis(unittest.TestCase):
    """Test Transaction Risk Analysis for SCA exemptions"""
    
    def test_calculate_risk_score_low_risk(self):
        """Test risk calculation for low-risk transaction"""
        transaction_data = {
            'amount': 50.0,
            'currency': 'EUR',
            'merchant_category': 'grocery',
            'country': 'DE',
            'timestamp': datetime.utcnow().replace(hour=14).isoformat()  # Afternoon
        }
        
        user_data = {
            'risk_score': 10,
            'country': 'DE'
        }
        
        risk_score, risk_factors = TransactionRiskAnalysis.calculate_risk_score(
            transaction_data, user_data
        )
        
        # Low amount, safe merchant, same country, normal time
        self.assertLess(risk_score, 30)
        self.assertEqual(len(risk_factors), 0)
    
    def test_calculate_risk_score_high_risk(self):
        """Test risk calculation for high-risk transaction"""
        transaction_data = {
            'amount': 1000.0,  # High amount
            'currency': 'EUR',
            'merchant_category': 'gambling',  # High-risk
            'country': 'US',  # Different country
            'timestamp': datetime.utcnow().replace(hour=2).isoformat()  # Late night
        }
        
        user_data = {
            'risk_score': 80,  # High-risk user
            'country': 'DE'
        }
        
        risk_score, risk_factors = TransactionRiskAnalysis.calculate_risk_score(
            transaction_data, user_data
        )
        
        # Should have high risk score and multiple factors
        self.assertGreater(risk_score, 70)
        self.assertIn('high_amount', risk_factors)
        self.assertIn('high_risk_merchant', risk_factors)
        self.assertIn('high_risk_user', risk_factors)
        self.assertIn('cross_border_transaction', risk_factors)
        self.assertIn('unusual_time', risk_factors)
    
    def test_exemption_eligibility_low_value(self):
        """Test SCA exemption eligibility for low-value transactions"""
        # Low value, low risk - should be eligible
        self.assertTrue(
            TransactionRiskAnalysis.is_eligible_for_exemption(20, 25.0, 'low_value')
        )
        
        # Low value, high risk - should not be eligible
        self.assertFalse(
            TransactionRiskAnalysis.is_eligible_for_exemption(40, 25.0, 'low_value')
        )
        
        # High value - should not be eligible regardless of risk
        self.assertFalse(
            TransactionRiskAnalysis.is_eligible_for_exemption(10, 50.0, 'low_value')
        )
    
    def test_exemption_eligibility_low_risk(self):
        """Test SCA exemption eligibility for low-risk transactions"""
        # Low amount, very low risk - should be eligible
        self.assertTrue(
            TransactionRiskAnalysis.is_eligible_for_exemption(15, 80.0, 'low_risk')
        )
        
        # Medium amount, low risk - should be eligible
        self.assertTrue(
            TransactionRiskAnalysis.is_eligible_for_exemption(10, 200.0, 'low_risk')
        )
        
        # High amount, very low risk - should be eligible
        self.assertTrue(
            TransactionRiskAnalysis.is_eligible_for_exemption(5, 400.0, 'low_risk')
        )
        
        # Any amount, high risk - should not be eligible
        self.assertFalse(
            TransactionRiskAnalysis.is_eligible_for_exemption(50, 100.0, 'low_risk')
        )

class TestOpenBankingAPIValidator(unittest.TestCase):
    """Test Open Banking API Validator"""
    
    def test_validate_fapi_headers_success(self):
        """Test successful FAPI header validation"""
        headers = {
            'x-fapi-auth-date': datetime.utcnow().isoformat() + 'Z',
            'x-fapi-customer-ip-address': '192.168.1.100',
            'x-fapi-interaction-id': 'interaction-123'
        }
        
        is_valid, errors = OpenBankingAPIValidator.validate_fapi_headers(headers)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_fapi_headers_missing_required(self):
        """Test FAPI header validation with missing required headers"""
        headers = {
            'x-fapi-auth-date': datetime.utcnow().isoformat() + 'Z'
            # Missing other required headers
        }
        
        is_valid, errors = OpenBankingAPIValidator.validate_fapi_headers(headers)
        
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        self.assertIn('Missing required header: x-fapi-customer-ip-address', errors)
        self.assertIn('Missing required header: x-fapi-interaction-id', errors)
    
    def test_validate_fapi_headers_invalid_ip(self):
        """Test FAPI header validation with invalid IP address"""
        headers = {
            'x-fapi-auth-date': datetime.utcnow().isoformat() + 'Z',
            'x-fapi-customer-ip-address': 'invalid-ip-address',
            'x-fapi-interaction-id': 'interaction-123'
        }
        
        is_valid, errors = OpenBankingAPIValidator.validate_fapi_headers(headers)
        
        self.assertFalse(is_valid)
        self.assertIn('Invalid x-fapi-customer-ip-address format', errors)
    
    def test_validate_tpp_certificate(self):
        """Test TPP certificate validation"""
        certificate_data = "mock-certificate-data"
        
        is_valid, cert_info = OpenBankingAPIValidator.validate_tpp_certificate(certificate_data)
        
        # Mock implementation always returns True
        self.assertTrue(is_valid)
        self.assertIn('organization_id', cert_info)
        self.assertIn('organization_name', cert_info)
        self.assertIn('roles', cert_info)

class TestSecurityMonitor(unittest.TestCase):
    """Test Security Monitor"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db = Mock()
        self.mock_db.execute_query = Mock()
        self.mock_db.fetch_one = Mock()
        self.mock_db.fetch_all = Mock()
        
        self.security_monitor = SecurityMonitor(self.mock_db)
    
    def test_log_security_event(self):
        """Test security event logging"""
        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_ATTEMPT,
            user_id='user123',
            ip_address='192.168.1.100',
            user_agent='Test Browser',
            timestamp=datetime.utcnow(),
            details={'test': 'data'},
            threat_level=ThreatLevel.MODERATE
        )
        
        self.security_monitor.log_security_event(event)
        
        # Verify database call was made
        self.mock_db.execute_query.assert_called()
        
        # Verify event was added to memory cache
        self.assertEqual(len(self.security_monitor.security_events), 1)
        self.assertEqual(self.security_monitor.security_events[0], event)
    
    def test_get_threat_summary(self):
        """Test threat summary generation"""
        # Mock database responses
        self.mock_db.fetch_all.side_effect = [
            [{'event_type': 'login_failure', 'threat_level': 'high', 'count': 5}],
            [{'indicator_type': 'malicious_ip', 'indicator_value': '192.168.1.100', 
              'threat_level': 'high', 'occurrence_count': 3}]
        ]
        
        summary = self.security_monitor.get_threat_summary(24)
        
        self.assertEqual(summary['time_period_hours'], 24)
        self.assertIn('events_by_type', summary)
        self.assertIn('top_threat_indicators', summary)
        self.assertIn('total_events', summary)

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestFAPI2SecurityProfile,
        TestPSD2ConsentManager,
        TestSCAManager,
        TestAdvancedEncryption,
        TestMultiFactorAuthentication,
        TestFraudDetectionEngine,
        TestTransactionRiskAnalysis,
        TestOpenBankingAPIValidator,
        TestSecurityMonitor
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    # Exit with appropriate code
    exit_code = 0 if result.wasSuccessful() else 1
    exit(exit_code)

