import base64
import ipaddress
import json
import os
import secrets
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import pyotp
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecurityLevel(Enum):
    """Security levels for different operations"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatLevel(Enum):
    """Threat assessment levels"""

    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEventType(Enum):
    """Types of security events"""

    LOGIN_ATTEMPT = "login_attempt"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    PASSWORD_CHANGE = "password_change"
    ACCOUNT_LOCKOUT = "account_lockout"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    FRAUD_DETECTION = "fraud_detection"
    DATA_ACCESS = "data_access"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    SECURITY_VIOLATION = "security_violation"


@dataclass
class SecurityEvent:
    """Security event data structure"""

    event_type: SecurityEventType
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    timestamp: datetime
    details: Dict[str, Any]
    threat_level: ThreatLevel
    session_id: Optional[str] = None
    location: Optional[str] = None


class AdvancedEncryption:
    """Advanced encryption utilities for sensitive data"""

    def __init__(self, master_key: str = None):
        if master_key:
            self.master_key = master_key.encode()
        else:
            self.master_key = os.environ.get(
                "MASTER_ENCRYPTION_KEY", "default-key-change-in-production"
            ).encode()

        # Derive encryption key from master key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"nexafi_salt_2024",  # In production, use random salt per encryption
            iterations=100000,
            backend=default_backend(),
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
        self.fernet = Fernet(key)

    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data with timestamp"""
        timestamp = int(time.time())
        data_with_timestamp = f"{timestamp}:{data}"
        encrypted = self.fernet.encrypt(data_with_timestamp.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt_sensitive_data(
        self, encrypted_data: str, max_age_seconds: int = None
    ) -> str:
        """Decrypt sensitive data with optional age validation"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes).decode()

            timestamp_str, data = decrypted.split(":", 1)
            timestamp = int(timestamp_str)

            if max_age_seconds and (time.time() - timestamp) > max_age_seconds:
                raise ValueError("Encrypted data has expired")

            return data
        except Exception as e:
            raise ValueError(f"Failed to decrypt data: {str(e)}")

    def encrypt_field_level(
        self, data: Dict[str, Any], sensitive_fields: List[str]
    ) -> Dict[str, Any]:
        """Encrypt specific fields in a dictionary"""
        encrypted_data = data.copy()
        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field] is not None:
                encrypted_data[field] = self.encrypt_sensitive_data(
                    str(encrypted_data[field])
                )
        return encrypted_data

    def decrypt_field_level(
        self, data: Dict[str, Any], sensitive_fields: List[str]
    ) -> Dict[str, Any]:
        """Decrypt specific fields in a dictionary"""
        decrypted_data = data.copy()
        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data[field] is not None:
                try:
                    decrypted_data[field] = self.decrypt_sensitive_data(
                        decrypted_data[field]
                    )
                except ValueError:
                    # Field might not be encrypted, leave as is
                    pass
        return decrypted_data


class MultiFactorAuthentication:
    """Multi-Factor Authentication implementation"""

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self._initialize_mfa_tables()

    def _initialize_mfa_tables(self):
        """Initialize MFA tables"""
        mfa_table_sql = """
        CREATE TABLE IF NOT EXISTS user_mfa_settings (
            user_id TEXT PRIMARY KEY,
            totp_secret TEXT,
            backup_codes TEXT,
            sms_phone TEXT,
            email_enabled BOOLEAN DEFAULT FALSE,
            totp_enabled BOOLEAN DEFAULT FALSE,
            sms_enabled BOOLEAN DEFAULT FALSE,
            recovery_codes_used TEXT DEFAULT '[]',
            last_totp_used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS mfa_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            method TEXT NOT NULL,
            success BOOLEAN NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE INDEX IF NOT EXISTS idx_mfa_attempts_user_id ON mfa_attempts(user_id);
        CREATE INDEX IF NOT EXISTS idx_mfa_attempts_created_at ON mfa_attempts(created_at);
        """

        self.db_manager.execute_query(mfa_table_sql)

    def setup_totp(self, user_id: str, user_email: str) -> Tuple[str, str, List[str]]:
        """Setup TOTP for user"""
        # Generate secret
        secret = pyotp.random_base32()

        # Generate backup codes
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]

        # Create TOTP URI for QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(name=user_email, issuer_name="NexaFi")

        # Store in database
        insert_sql = """
        INSERT OR REPLACE INTO user_mfa_settings
        (user_id, totp_secret, backup_codes, totp_enabled, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """

        self.db_manager.execute_query(
            insert_sql,
            (user_id, secret, json.dumps(backup_codes), True, datetime.utcnow()),
        )

        return secret, provisioning_uri, backup_codes

    def verify_totp(
        self, user_id: str, token: str, ip_address: str = None, user_agent: str = None
    ) -> bool:
        """Verify TOTP token"""
        # Get user's TOTP secret
        query_sql = "SELECT totp_secret, last_totp_used FROM user_mfa_settings WHERE user_id = ? AND totp_enabled = 1"
        result = self.db_manager.fetch_one(query_sql, (user_id,))

        if not result:
            self._log_mfa_attempt(user_id, "totp", False, ip_address, user_agent)
            return False

        secret = result["totp_secret"]
        last_used = result["last_totp_used"]

        # Verify token
        totp = pyotp.TOTP(secret)
        current_time = int(time.time())

        # Check current and previous time windows to account for clock skew
        for time_offset in [0, -30, 30]:
            test_time = current_time + time_offset
            if totp.verify(token, test_time) and test_time > last_used:
                # Update last used time to prevent replay attacks
                update_sql = (
                    "UPDATE user_mfa_settings SET last_totp_used = ? WHERE user_id = ?"
                )
                self.db_manager.execute_query(update_sql, (test_time, user_id))

                self._log_mfa_attempt(user_id, "totp", True, ip_address, user_agent)
                return True

        self._log_mfa_attempt(user_id, "totp", False, ip_address, user_agent)
        return False

    def verify_backup_code(
        self, user_id: str, code: str, ip_address: str = None, user_agent: str = None
    ) -> bool:
        """Verify backup recovery code"""
        query_sql = "SELECT backup_codes, recovery_codes_used FROM user_mfa_settings WHERE user_id = ?"
        result = self.db_manager.fetch_one(query_sql, (user_id,))

        if not result:
            self._log_mfa_attempt(user_id, "backup_code", False, ip_address, user_agent)
            return False

        backup_codes = json.loads(result["backup_codes"])
        used_codes = json.loads(result["recovery_codes_used"])

        code_upper = code.upper()

        if code_upper in backup_codes and code_upper not in used_codes:
            # Mark code as used
            used_codes.append(code_upper)
            update_sql = (
                "UPDATE user_mfa_settings SET recovery_codes_used = ? WHERE user_id = ?"
            )
            self.db_manager.execute_query(update_sql, (json.dumps(used_codes), user_id))

            self._log_mfa_attempt(user_id, "backup_code", True, ip_address, user_agent)
            return True

        self._log_mfa_attempt(user_id, "backup_code", False, ip_address, user_agent)
        return False

    def _log_mfa_attempt(
        self,
        user_id: str,
        method: str,
        success: bool,
        ip_address: str = None,
        user_agent: str = None,
    ):
        """Log MFA attempt"""
        insert_sql = """
        INSERT INTO mfa_attempts (user_id, method, success, ip_address, user_agent)
        VALUES (?, ?, ?, ?, ?)
        """

        self.db_manager.execute_query(
            insert_sql, (user_id, method, success, ip_address, user_agent)
        )


class FraudDetectionEngine:
    """Advanced fraud detection and prevention"""

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.user_behavior_cache = defaultdict(
            lambda: {
                "login_times": deque(maxlen=50),
                "ip_addresses": deque(maxlen=20),
                "transaction_amounts": deque(maxlen=100),
                "device_fingerprints": deque(maxlen=10),
            }
        )
        self._initialize_fraud_tables()

    def _initialize_fraud_tables(self):
        """Initialize fraud detection tables"""
        fraud_table_sql = """
        CREATE TABLE IF NOT EXISTS fraud_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            alert_type TEXT NOT NULL,
            risk_score INTEGER NOT NULL,
            details TEXT NOT NULL,
            status TEXT DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            resolved_by TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS user_behavior_patterns (
            user_id TEXT PRIMARY KEY,
            typical_login_hours TEXT,
            typical_ip_ranges TEXT,
            typical_transaction_amounts TEXT,
            device_fingerprints TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE INDEX IF NOT EXISTS idx_fraud_alerts_user_id ON fraud_alerts(user_id);
        CREATE INDEX IF NOT EXISTS idx_fraud_alerts_created_at ON fraud_alerts(created_at);
        """

        self.db_manager.execute_query(fraud_table_sql)

    def analyze_login_behavior(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str,
        device_fingerprint: str = None,
    ) -> Tuple[int, List[str]]:
        """Analyze login behavior for fraud indicators"""
        risk_score = 0
        risk_factors = []

        # Get user's behavior cache
        user_cache = self.user_behavior_cache[user_id]
        current_time = datetime.utcnow()

        # Analyze IP address patterns
        if ip_address not in user_cache["ip_addresses"]:
            # New IP address
            if len(user_cache["ip_addresses"]) > 0:
                risk_score += 20
                risk_factors.append("new_ip_address")

                # Check if IP is from different country/region
                if self._is_suspicious_location(
                    ip_address, list(user_cache["ip_addresses"])
                ):
                    risk_score += 30
                    risk_factors.append("suspicious_location")

        # Analyze login time patterns
        current_hour = current_time.hour
        typical_hours = self._get_typical_login_hours(user_id)

        if typical_hours and current_hour not in typical_hours:
            risk_score += 15
            risk_factors.append("unusual_login_time")

        # Analyze device fingerprint
        if (
            device_fingerprint
            and device_fingerprint not in user_cache["device_fingerprints"]
        ):
            risk_score += 25
            risk_factors.append("new_device")

        # Check for rapid successive logins from different IPs
        recent_ips = list(user_cache["ip_addresses"])[-5:]  # Last 5 IPs
        if len(set(recent_ips)) > 3:  # More than 3 different IPs recently
            risk_score += 40
            risk_factors.append("multiple_ip_addresses")

        # Update behavior cache
        user_cache["login_times"].append(current_time)
        user_cache["ip_addresses"].append(ip_address)
        if device_fingerprint:
            user_cache["device_fingerprints"].append(device_fingerprint)

        return risk_score, risk_factors

    def analyze_transaction_behavior(
        self,
        user_id: str,
        amount: float,
        currency: str,
        merchant_category: str,
        ip_address: str,
    ) -> Tuple[int, List[str]]:
        """Analyze transaction behavior for fraud indicators"""
        risk_score = 0
        risk_factors = []

        user_cache = self.user_behavior_cache[user_id]

        # Analyze transaction amount patterns
        typical_amounts = list(user_cache["transaction_amounts"])
        if typical_amounts:
            avg_amount = sum(typical_amounts) / len(typical_amounts)
            max_amount = max(typical_amounts)

            # Check for unusually large transactions
            if amount > avg_amount * 5:
                risk_score += 30
                risk_factors.append("unusually_large_amount")

            if amount > max_amount * 2:
                risk_score += 20
                risk_factors.append("exceeds_typical_maximum")

        # Check for high-risk merchant categories
        high_risk_categories = [
            "gambling",
            "cryptocurrency",
            "adult_entertainment",
            "money_transfer",
        ]
        if merchant_category in high_risk_categories:
            risk_score += 25
            risk_factors.append("high_risk_merchant")

        # Check for rapid successive transactions
        recent_transactions = self._get_recent_transactions(user_id, minutes=10)
        if len(recent_transactions) > 5:
            risk_score += 35
            risk_factors.append("rapid_transactions")

        # Check for round number amounts (potential money laundering indicator)
        if amount % 100 == 0 and amount >= 1000:
            risk_score += 10
            risk_factors.append("round_amount")

        # Update behavior cache
        user_cache["transaction_amounts"].append(amount)

        return risk_score, risk_factors

    def create_fraud_alert(
        self, user_id: str, alert_type: str, risk_score: int, details: Dict[str, Any]
    ) -> int:
        """Create fraud alert"""
        insert_sql = """
        INSERT INTO fraud_alerts (user_id, alert_type, risk_score, details)
        VALUES (?, ?, ?, ?)
        """

        result = self.db_manager.execute_query(
            insert_sql, (user_id, alert_type, risk_score, json.dumps(details))
        )

        return result.lastrowid

    def _is_suspicious_location(self, new_ip: str, known_ips: List[str]) -> bool:
        """Check if new IP is from suspicious location"""
        # Simplified geolocation check
        # In production, integrate with proper geolocation service
        try:
            new_ip_obj = ipaddress.ip_address(new_ip)

            # Check if it's a private IP
            if new_ip_obj.is_private:
                return False

            # Simple heuristic: if first two octets are very different, consider suspicious
            new_octets = new_ip.split(".")
            for known_ip in known_ips[-3:]:  # Check last 3 known IPs
                known_octets = known_ip.split(".")
                if (
                    abs(int(new_octets[0]) - int(known_octets[0])) > 50
                    or abs(int(new_octets[1]) - int(known_octets[1])) > 100
                ):
                    return True

            return False
        except ValueError:
            return True  # Invalid IP format is suspicious

    def _get_typical_login_hours(self, user_id: str) -> List[int]:
        """Get user's typical login hours"""
        query_sql = (
            "SELECT typical_login_hours FROM user_behavior_patterns WHERE user_id = ?"
        )
        result = self.db_manager.fetch_one(query_sql, (user_id,))

        if result and result["typical_login_hours"]:
            return json.loads(result["typical_login_hours"])

        return []

    def _get_recent_transactions(self, user_id: str, minutes: int = 10) -> List[Dict]:
        """Get recent transactions for user"""
        # This would query the transactions table
        # For now, return empty list
        return []


class SecurityMonitor:
    """Real-time security monitoring and alerting"""

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.security_events = deque(maxlen=10000)  # Keep last 10k events in memory
        self.threat_indicators = defaultdict(int)
        self.lock = threading.Lock()
        self._initialize_monitoring_tables()

    def _initialize_monitoring_tables(self):
        """Initialize security monitoring tables"""
        monitoring_table_sql = """
        CREATE TABLE IF NOT EXISTS security_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            user_id TEXT,
            ip_address TEXT NOT NULL,
            user_agent TEXT,
            session_id TEXT,
            threat_level TEXT NOT NULL,
            details TEXT NOT NULL,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS threat_indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            indicator_type TEXT NOT NULL,
            indicator_value TEXT NOT NULL,
            threat_level TEXT NOT NULL,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            occurrence_count INTEGER DEFAULT 1,
            status TEXT DEFAULT 'active'
        );

        CREATE INDEX IF NOT EXISTS idx_security_events_user_id ON security_events(user_id);
        CREATE INDEX IF NOT EXISTS idx_security_events_ip_address ON security_events(ip_address);
        CREATE INDEX IF NOT EXISTS idx_security_events_created_at ON security_events(created_at);
        CREATE INDEX IF NOT EXISTS idx_threat_indicators_value ON threat_indicators(indicator_value);
        """

        self.db_manager.execute_query(monitoring_table_sql)

    def log_security_event(self, event: SecurityEvent):
        """Log security event"""
        with self.lock:
            # Add to memory cache
            self.security_events.append(event)

            # Store in database
            insert_sql = """
            INSERT INTO security_events
            (event_type, user_id, ip_address, user_agent, session_id, threat_level, details, location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """

            self.db_manager.execute_query(
                insert_sql,
                (
                    event.event_type.value,
                    event.user_id,
                    event.ip_address,
                    event.user_agent,
                    event.session_id,
                    event.threat_level.value,
                    json.dumps(event.details),
                    event.location,
                ),
            )

            # Update threat indicators
            self._update_threat_indicators(event)

            # Check for immediate threats
            self._check_immediate_threats(event)

    def _update_threat_indicators(self, event: SecurityEvent):
        """Update threat indicators based on event"""
        indicators = []

        # IP-based indicators
        if event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            indicators.append(("malicious_ip", event.ip_address))

        # User-based indicators
        if event.event_type == SecurityEventType.FRAUD_DETECTION:
            indicators.append(("suspicious_user", event.user_id))

        # Pattern-based indicators
        if event.event_type == SecurityEventType.LOGIN_FAILURE:
            indicators.append(("failed_login_ip", event.ip_address))

        for indicator_type, indicator_value in indicators:
            self._upsert_threat_indicator(
                indicator_type, indicator_value, event.threat_level
            )

    def _upsert_threat_indicator(
        self, indicator_type: str, indicator_value: str, threat_level: ThreatLevel
    ):
        """Insert or update threat indicator"""
        # Check if indicator exists
        query_sql = "SELECT id, occurrence_count FROM threat_indicators WHERE indicator_type = ? AND indicator_value = ?"
        result = self.db_manager.fetch_one(query_sql, (indicator_type, indicator_value))

        if result:
            # Update existing indicator
            update_sql = """
            UPDATE threat_indicators
            SET occurrence_count = occurrence_count + 1, last_seen = ?, threat_level = ?
            WHERE id = ?
            """
            self.db_manager.execute_query(
                update_sql, (datetime.utcnow(), threat_level.value, result["id"])
            )
        else:
            # Insert new indicator
            insert_sql = """
            INSERT INTO threat_indicators (indicator_type, indicator_value, threat_level)
            VALUES (?, ?, ?)
            """
            self.db_manager.execute_query(
                insert_sql, (indicator_type, indicator_value, threat_level.value)
            )

    def _check_immediate_threats(self, event: SecurityEvent):
        """Check for immediate threats requiring action"""
        # Check for brute force attacks
        if event.event_type == SecurityEventType.LOGIN_FAILURE:
            recent_failures = self._count_recent_events(
                event.ip_address, SecurityEventType.LOGIN_FAILURE, minutes=15
            )
            if recent_failures >= 10:
                self._trigger_ip_block(event.ip_address, "brute_force_attack")

        # Check for account takeover attempts
        if (
            event.event_type == SecurityEventType.LOGIN_SUCCESS
            and event.threat_level == ThreatLevel.HIGH
        ):
            self._trigger_account_review(event.user_id, "suspicious_login")

    def _count_recent_events(
        self, ip_address: str, event_type: SecurityEventType, minutes: int = 15
    ) -> int:
        """Count recent events from IP address"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)

        query_sql = """
        SELECT COUNT(*) as count FROM security_events
        WHERE ip_address = ? AND event_type = ? AND created_at > ?
        """

        result = self.db_manager.fetch_one(
            query_sql, (ip_address, event_type.value, cutoff_time)
        )
        return result["count"] if result else 0

    def _trigger_ip_block(self, ip_address: str, reason: str):
        """Trigger IP address block"""
        # Implementation would integrate with firewall/WAF
        print(f"SECURITY ALERT: Blocking IP {ip_address} - Reason: {reason}")

    def _trigger_account_review(self, user_id: str, reason: str):
        """Trigger account security review"""
        # Implementation would notify security team
        print(f"SECURITY ALERT: Account {user_id} requires review - Reason: {reason}")

    def get_threat_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get threat summary for specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        # Count events by type
        events_query = """
        SELECT event_type, threat_level, COUNT(*) as count
        FROM security_events
        WHERE created_at > ?
        GROUP BY event_type, threat_level
        """

        events_result = self.db_manager.fetch_all(events_query, (cutoff_time,))

        # Get top threat indicators
        indicators_query = """
        SELECT indicator_type, indicator_value, threat_level, occurrence_count
        FROM threat_indicators
        WHERE last_seen > ? AND status = 'active'
        ORDER BY occurrence_count DESC
        LIMIT 10
        """

        indicators_result = self.db_manager.fetch_all(indicators_query, (cutoff_time,))

        return {
            "time_period_hours": hours,
            "events_by_type": events_result,
            "top_threat_indicators": indicators_result,
            "total_events": sum(row["count"] for row in events_result),
        }


class SecureSessionManager:
    """Secure session management with advanced features"""

    def __init__(self, db_manager, encryption: AdvancedEncryption):
        self.db_manager = db_manager
        self.encryption = encryption
        self.active_sessions = {}  # In-memory session cache
        self._initialize_session_tables()

    def _initialize_session_tables(self):
        """Initialize session management tables"""
        session_table_sql = """
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            ip_address TEXT NOT NULL,
            user_agent TEXT,
            device_fingerprint TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            security_level TEXT DEFAULT 'medium',
            mfa_verified BOOLEAN DEFAULT FALSE,
            session_data TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
        """

        self.db_manager.execute_query(session_table_sql)

    def create_session(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str = None,
        device_fingerprint: str = None,
        security_level: SecurityLevel = SecurityLevel.MEDIUM,
    ) -> str:
        """Create new secure session"""
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)  # 24-hour default

        # Adjust expiry based on security level
        if security_level == SecurityLevel.HIGH:
            expires_at = datetime.utcnow() + timedelta(hours=8)
        elif security_level == SecurityLevel.CRITICAL:
            expires_at = datetime.utcnow() + timedelta(hours=2)

        session_data = {
            "created_ip": ip_address,
            "security_level": security_level.value,
            "permissions": [],
        }

        # Store session
        insert_sql = """
        INSERT INTO user_sessions
        (session_id, user_id, ip_address, user_agent, device_fingerprint,
         expires_at, security_level, session_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        self.db_manager.execute_query(
            insert_sql,
            (
                session_id,
                user_id,
                ip_address,
                user_agent,
                device_fingerprint,
                expires_at,
                security_level.value,
                self.encryption.encrypt_sensitive_data(json.dumps(session_data)),
            ),
        )

        # Add to memory cache
        self.active_sessions[session_id] = {
            "user_id": user_id,
            "expires_at": expires_at,
            "security_level": security_level,
            "mfa_verified": False,
        }

        return session_id

    def validate_session(
        self, session_id: str, ip_address: str = None, require_mfa: bool = False
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Validate session with security checks"""
        # Check memory cache first
        if session_id in self.active_sessions:
            cached_session = self.active_sessions[session_id]
            if datetime.utcnow() > cached_session["expires_at"]:
                del self.active_sessions[session_id]
                return False, None, {}

        # Query database
        query_sql = """
        SELECT user_id, ip_address, expires_at, is_active, security_level,
               mfa_verified, session_data, device_fingerprint
        FROM user_sessions
        WHERE session_id = ? AND is_active = 1
        """

        result = self.db_manager.fetch_one(query_sql, (session_id,))

        if not result:
            return False, None, {}

        # Check expiry
        expires_at = datetime.fromisoformat(result["expires_at"])
        if datetime.utcnow() > expires_at:
            self.invalidate_session(session_id)
            return False, None, {}

        # Check IP address if provided (optional for mobile apps)
        if ip_address and result["ip_address"] != ip_address:
            # Log suspicious activity but don't immediately fail
            # Mobile users might have changing IPs
            pass

        # Check MFA requirement
        if require_mfa and not result["mfa_verified"]:
            return False, result["user_id"], {"requires_mfa": True}

        # Decrypt session data
        try:
            session_data = json.loads(
                self.encryption.decrypt_sensitive_data(result["session_data"])
            )
        except ValueError:
            session_data = {}

        # Update last activity
        self._update_session_activity(session_id)

        return (
            True,
            result["user_id"],
            {
                "security_level": result["security_level"],
                "mfa_verified": result["mfa_verified"],
                "session_data": session_data,
            },
        )

    def mark_mfa_verified(self, session_id: str):
        """Mark session as MFA verified"""
        update_sql = "UPDATE user_sessions SET mfa_verified = 1 WHERE session_id = ?"
        self.db_manager.execute_query(update_sql, (session_id,))

        if session_id in self.active_sessions:
            self.active_sessions[session_id]["mfa_verified"] = True

    def invalidate_session(self, session_id: str):
        """Invalidate session"""
        update_sql = "UPDATE user_sessions SET is_active = 0 WHERE session_id = ?"
        self.db_manager.execute_query(update_sql, (session_id,))

        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

    def invalidate_all_user_sessions(self, user_id: str):
        """Invalidate all sessions for a user"""
        update_sql = "UPDATE user_sessions SET is_active = 0 WHERE user_id = ?"
        self.db_manager.execute_query(update_sql, (user_id,))

        # Remove from memory cache
        to_remove = [
            sid
            for sid, data in self.active_sessions.items()
            if data["user_id"] == user_id
        ]
        for sid in to_remove:
            del self.active_sessions[sid]

    def _update_session_activity(self, session_id: str):
        """Update session last activity timestamp"""
        update_sql = "UPDATE user_sessions SET last_activity = ? WHERE session_id = ?"
        self.db_manager.execute_query(update_sql, (datetime.utcnow(), session_id))

    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        cutoff_time = datetime.utcnow()

        # Remove from database
        delete_sql = "DELETE FROM user_sessions WHERE expires_at < ? OR is_active = 0"
        self.db_manager.execute_query(delete_sql, (cutoff_time,))

        # Remove from memory cache
        expired_sessions = [
            sid
            for sid, data in self.active_sessions.items()
            if datetime.utcnow() > data["expires_at"]
        ]
        for sid in expired_sessions:
            del self.active_sessions[sid]
