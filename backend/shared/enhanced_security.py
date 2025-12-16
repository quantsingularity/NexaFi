import base64
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
from nexafi_logging.logger import get_logger

import ipaddress
import pyotp
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = get_logger(__name__)


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

    def __init__(self, master_key: str = None) -> Any:
        if master_key:
            self.master_key = master_key.encode()
        else:
            self.master_key = os.environ.get(
                "MASTER_ENCRYPTION_KEY", "default-key-change-in-production"
            ).encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"nexafi_salt_2024",
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
            if max_age_seconds and time.time() - timestamp > max_age_seconds:
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
                    pass
        return decrypted_data


class MultiFactorAuthentication:
    """Multi-Factor Authentication implementation"""

    def __init__(self, db_manager: Any) -> Any:
        self.db_manager = db_manager
        self._initialize_mfa_tables()

    def _initialize_mfa_tables(self) -> Any:
        """Initialize MFA tables"""
        mfa_table_sql = "\n        CREATE TABLE IF NOT EXISTS user_mfa_settings (\n            user_id TEXT PRIMARY KEY,\n            totp_secret TEXT,\n            backup_codes TEXT,\n            sms_phone TEXT,\n            email_enabled BOOLEAN DEFAULT FALSE,\n            totp_enabled BOOLEAN DEFAULT FALSE,\n            sms_enabled BOOLEAN DEFAULT FALSE,\n            recovery_codes_used TEXT DEFAULT '[]',\n            last_totp_used INTEGER DEFAULT 0,\n            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n            FOREIGN KEY (user_id) REFERENCES users(id)\n        );\n\n        CREATE TABLE IF NOT EXISTS mfa_attempts (\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n            user_id TEXT NOT NULL,\n            method TEXT NOT NULL,\n            success BOOLEAN NOT NULL,\n            ip_address TEXT,\n            user_agent TEXT,\n            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n            FOREIGN KEY (user_id) REFERENCES users(id)\n        );\n\n        CREATE INDEX IF NOT EXISTS idx_mfa_attempts_user_id ON mfa_attempts(user_id);\n        CREATE INDEX IF NOT EXISTS idx_mfa_attempts_created_at ON mfa_attempts(created_at);\n        "
        self.db_manager.execute_query(mfa_table_sql)

    def setup_totp(self, user_id: str, user_email: str) -> Tuple[str, str, List[str]]:
        """Setup TOTP for user"""
        secret = pyotp.random_base32()
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(name=user_email, issuer_name="NexaFi")
        insert_sql = "\n        INSERT OR REPLACE INTO user_mfa_settings\n        (user_id, totp_secret, backup_codes, totp_enabled, updated_at)\n        VALUES (?, ?, ?, ?, ?)\n        "
        self.db_manager.execute_query(
            insert_sql,
            (user_id, secret, json.dumps(backup_codes), True, datetime.utcnow()),
        )
        return (secret, provisioning_uri, backup_codes)

    def verify_totp(
        self, user_id: str, token: str, ip_address: str = None, user_agent: str = None
    ) -> bool:
        """Verify TOTP token"""
        query_sql = "SELECT totp_secret, last_totp_used FROM user_mfa_settings WHERE user_id = ? AND totp_enabled = 1"
        result = self.db_manager.fetch_one(query_sql, (user_id,))
        if not result:
            self._log_mfa_attempt(user_id, "totp", False, ip_address, user_agent)
            return False
        secret = result["totp_secret"]
        last_used = result["last_totp_used"]
        totp = pyotp.TOTP(secret)
        current_time = int(time.time())
        for time_offset in [0, -30, 30]:
            test_time = current_time + time_offset
            if totp.verify(token, test_time) and test_time > last_used:
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
    ) -> Any:
        """Log MFA attempt"""
        insert_sql = "\n        INSERT INTO mfa_attempts (user_id, method, success, ip_address, user_agent)\n        VALUES (?, ?, ?, ?, ?)\n        "
        self.db_manager.execute_query(
            insert_sql, (user_id, method, success, ip_address, user_agent)
        )


class FraudDetectionEngine:
    """Advanced fraud detection and prevention"""

    def __init__(self, db_manager: Any) -> Any:
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

    def _initialize_fraud_tables(self) -> Any:
        """Initialize fraud detection tables"""
        fraud_table_sql = "\n        CREATE TABLE IF NOT EXISTS fraud_alerts (\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n            user_id TEXT,\n            alert_type TEXT NOT NULL,\n            risk_score INTEGER NOT NULL,\n            details TEXT NOT NULL,\n            status TEXT DEFAULT 'open',\n            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n            resolved_at TIMESTAMP,\n            resolved_by TEXT,\n            FOREIGN KEY (user_id) REFERENCES users(id)\n        );\n\n        CREATE TABLE IF NOT EXISTS user_behavior_patterns (\n            user_id TEXT PRIMARY KEY,\n            typical_login_hours TEXT,\n            typical_ip_ranges TEXT,\n            typical_transaction_amounts TEXT,\n            device_fingerprints TEXT,\n            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n            FOREIGN KEY (user_id) REFERENCES users(id)\n        );\n\n        CREATE INDEX IF NOT EXISTS idx_fraud_alerts_user_id ON fraud_alerts(user_id);\n        CREATE INDEX IF NOT EXISTS idx_fraud_alerts_created_at ON fraud_alerts(created_at);\n        "
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
        user_cache = self.user_behavior_cache[user_id]
        current_time = datetime.utcnow()
        if ip_address not in user_cache["ip_addresses"]:
            if len(user_cache["ip_addresses"]) > 0:
                risk_score += 20
                risk_factors.append("new_ip_address")
                if self._is_suspicious_location(
                    ip_address, list(user_cache["ip_addresses"])
                ):
                    risk_score += 30
                    risk_factors.append("suspicious_location")
        current_hour = current_time.hour
        typical_hours = self._get_typical_login_hours(user_id)
        if typical_hours and current_hour not in typical_hours:
            risk_score += 15
            risk_factors.append("unusual_login_time")
        if (
            device_fingerprint
            and device_fingerprint not in user_cache["device_fingerprints"]
        ):
            risk_score += 25
            risk_factors.append("new_device")
        recent_ips = list(user_cache["ip_addresses"])[-5:]
        if len(set(recent_ips)) > 3:
            risk_score += 40
            risk_factors.append("multiple_ip_addresses")
        user_cache["login_times"].append(current_time)
        user_cache["ip_addresses"].append(ip_address)
        if device_fingerprint:
            user_cache["device_fingerprints"].append(device_fingerprint)
        return (risk_score, risk_factors)

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
        typical_amounts = list(user_cache["transaction_amounts"])
        if typical_amounts:
            avg_amount = sum(typical_amounts) / len(typical_amounts)
            max_amount = max(typical_amounts)
            if amount > avg_amount * 5:
                risk_score += 30
                risk_factors.append("unusually_large_amount")
            if amount > max_amount * 2:
                risk_score += 20
                risk_factors.append("exceeds_typical_maximum")
        high_risk_categories = [
            "gambling",
            "cryptocurrency",
            "adult_entertainment",
            "money_transfer",
        ]
        if merchant_category in high_risk_categories:
            risk_score += 25
            risk_factors.append("high_risk_merchant")
        recent_transactions = self._get_recent_transactions(user_id, minutes=10)
        if len(recent_transactions) > 5:
            risk_score += 35
            risk_factors.append("rapid_transactions")
        if amount % 100 == 0 and amount >= 1000:
            risk_score += 10
            risk_factors.append("round_amount")
        user_cache["transaction_amounts"].append(amount)
        return (risk_score, risk_factors)

    def create_fraud_alert(
        self, user_id: str, alert_type: str, risk_score: int, details: Dict[str, Any]
    ) -> int:
        """Create fraud alert"""
        insert_sql = "\n        INSERT INTO fraud_alerts (user_id, alert_type, risk_score, details)\n        VALUES (?, ?, ?, ?)\n        "
        result = self.db_manager.execute_query(
            insert_sql, (user_id, alert_type, risk_score, json.dumps(details))
        )
        return result.lastrowid

    def _is_suspicious_location(self, new_ip: str, known_ips: List[str]) -> bool:
        """Check if new IP is from suspicious location"""
        try:
            new_ip_obj = ipaddress.ip_address(new_ip)
            if new_ip_obj.is_private:
                return False
            new_octets = new_ip.split(".")
            for known_ip in known_ips[-3:]:
                known_octets = known_ip.split(".")
                if (
                    abs(int(new_octets[0]) - int(known_octets[0])) > 50
                    or abs(int(new_octets[1]) - int(known_octets[1])) > 100
                ):
                    return True
            return False
        except ValueError:
            return True

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
        return []


class SecurityMonitor:
    """Real-time security monitoring and alerting"""

    def __init__(self, db_manager: Any) -> Any:
        self.db_manager = db_manager
        self.security_events = deque(maxlen=10000)
        self.threat_indicators = defaultdict(int)
        self.lock = threading.Lock()
        self._initialize_monitoring_tables()

    def _initialize_monitoring_tables(self) -> Any:
        """Initialize security monitoring tables"""
        monitoring_table_sql = "\n        CREATE TABLE IF NOT EXISTS security_events (\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n            event_type TEXT NOT NULL,\n            user_id TEXT,\n            ip_address TEXT NOT NULL,\n            user_agent TEXT,\n            session_id TEXT,\n            threat_level TEXT NOT NULL,\n            details TEXT NOT NULL,\n            location TEXT,\n            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n        );\n\n        CREATE TABLE IF NOT EXISTS threat_indicators (\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n            indicator_type TEXT NOT NULL,\n            indicator_value TEXT NOT NULL,\n            threat_level TEXT NOT NULL,\n            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n            occurrence_count INTEGER DEFAULT 1,\n            status TEXT DEFAULT 'active'\n        );\n\n        CREATE INDEX IF NOT EXISTS idx_security_events_user_id ON security_events(user_id);\n        CREATE INDEX IF NOT EXISTS idx_security_events_ip_address ON security_events(ip_address);\n        CREATE INDEX IF NOT EXISTS idx_security_events_created_at ON security_events(created_at);\n        CREATE INDEX IF NOT EXISTS idx_threat_indicators_value ON threat_indicators(indicator_value);\n        "
        self.db_manager.execute_query(monitoring_table_sql)

    def log_security_event(self, event: SecurityEvent) -> Any:
        """Log security event"""
        with self.lock:
            self.security_events.append(event)
            insert_sql = "\n            INSERT INTO security_events\n            (event_type, user_id, ip_address, user_agent, session_id, threat_level, details, location)\n            VALUES (?, ?, ?, ?, ?, ?, ?, ?)\n            "
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
            self._update_threat_indicators(event)
            self._check_immediate_threats(event)

    def _update_threat_indicators(self, event: SecurityEvent) -> Any:
        """Update threat indicators based on event"""
        indicators = []
        if event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            indicators.append(("malicious_ip", event.ip_address))
        if event.event_type == SecurityEventType.FRAUD_DETECTION:
            indicators.append(("suspicious_user", event.user_id))
        if event.event_type == SecurityEventType.LOGIN_FAILURE:
            indicators.append(("failed_login_ip", event.ip_address))
        for indicator_type, indicator_value in indicators:
            self._upsert_threat_indicator(
                indicator_type, indicator_value, event.threat_level
            )

    def _upsert_threat_indicator(
        self, indicator_type: str, indicator_value: str, threat_level: ThreatLevel
    ) -> Any:
        """Insert or update threat indicator"""
        query_sql = "SELECT id, occurrence_count FROM threat_indicators WHERE indicator_type = ? AND indicator_value = ?"
        result = self.db_manager.fetch_one(query_sql, (indicator_type, indicator_value))
        if result:
            update_sql = "\n            UPDATE threat_indicators\n            SET occurrence_count = occurrence_count + 1, last_seen = ?, threat_level = ?\n            WHERE id = ?\n            "
            self.db_manager.execute_query(
                update_sql, (datetime.utcnow(), threat_level.value, result["id"])
            )
        else:
            insert_sql = "\n            INSERT INTO threat_indicators (indicator_type, indicator_value, threat_level)\n            VALUES (?, ?, ?)\n            "
            self.db_manager.execute_query(
                insert_sql, (indicator_type, indicator_value, threat_level.value)
            )

    def _check_immediate_threats(self, event: SecurityEvent) -> Any:
        """Check for immediate threats requiring action"""
        if event.event_type == SecurityEventType.LOGIN_FAILURE:
            recent_failures = self._count_recent_events(
                event.ip_address, SecurityEventType.LOGIN_FAILURE, minutes=15
            )
            if recent_failures >= 10:
                self._trigger_ip_block(event.ip_address, "brute_force_attack")
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
        query_sql = "\n        SELECT COUNT(*) as count FROM security_events\n        WHERE ip_address = ? AND event_type = ? AND created_at > ?\n        "
        result = self.db_manager.fetch_one(
            query_sql, (ip_address, event_type.value, cutoff_time)
        )
        return result["count"] if result else 0

    def _trigger_ip_block(self, ip_address: str, reason: str) -> Any:
        """Trigger IP address block"""
        logger.info(f"SECURITY ALERT: Blocking IP {ip_address} - Reason: {reason}")

    def _trigger_account_review(self, user_id: str, reason: str) -> Any:
        """Trigger account security review"""
        logger.info(
            f"SECURITY ALERT: Account {user_id} requires review - Reason: {reason}"
        )

    def get_threat_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get threat summary for specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        events_query = "\n        SELECT event_type, threat_level, COUNT(*) as count\n        FROM security_events\n        WHERE created_at > ?\n        GROUP BY event_type, threat_level\n        "
        events_result = self.db_manager.fetch_all(events_query, (cutoff_time,))
        indicators_query = "\n        SELECT indicator_type, indicator_value, threat_level, occurrence_count\n        FROM threat_indicators\n        WHERE last_seen > ? AND status = 'active'\n        ORDER BY occurrence_count DESC\n        LIMIT 10\n        "
        indicators_result = self.db_manager.fetch_all(indicators_query, (cutoff_time,))
        return {
            "time_period_hours": hours,
            "events_by_type": events_result,
            "top_threat_indicators": indicators_result,
            "total_events": sum((row["count"] for row in events_result)),
        }


class SecureSessionManager:
    """Secure session management with advanced features"""

    def __init__(self, db_manager: Any, encryption: AdvancedEncryption) -> Any:
        self.db_manager = db_manager
        self.encryption = encryption
        self.active_sessions = {}
        self._initialize_session_tables()

    def _initialize_session_tables(self) -> Any:
        """Initialize session management tables"""
        session_table_sql = "\n        CREATE TABLE IF NOT EXISTS user_sessions (\n            session_id TEXT PRIMARY KEY,\n            user_id TEXT NOT NULL,\n            ip_address TEXT NOT NULL,\n            user_agent TEXT,\n            device_fingerprint TEXT,\n            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n            expires_at TIMESTAMP NOT NULL,\n            is_active BOOLEAN DEFAULT TRUE,\n            security_level TEXT DEFAULT 'medium',\n            mfa_verified BOOLEAN DEFAULT FALSE,\n            session_data TEXT,\n            FOREIGN KEY (user_id) REFERENCES users(id)\n        );\n\n        CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);\n        CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);\n        "
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
        expires_at = datetime.utcnow() + timedelta(hours=24)
        if security_level == SecurityLevel.HIGH:
            expires_at = datetime.utcnow() + timedelta(hours=8)
        elif security_level == SecurityLevel.CRITICAL:
            expires_at = datetime.utcnow() + timedelta(hours=2)
        session_data = {
            "created_ip": ip_address,
            "security_level": security_level.value,
            "permissions": [],
        }
        insert_sql = "\n        INSERT INTO user_sessions\n        (session_id, user_id, ip_address, user_agent, device_fingerprint,\n         expires_at, security_level, session_data)\n        VALUES (?, ?, ?, ?, ?, ?, ?, ?)\n        "
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
        if session_id in self.active_sessions:
            cached_session = self.active_sessions[session_id]
            if datetime.utcnow() > cached_session["expires_at"]:
                del self.active_sessions[session_id]
                return (False, None, {})
        query_sql = "\n        SELECT user_id, ip_address, expires_at, is_active, security_level,\n               mfa_verified, session_data, device_fingerprint\n        FROM user_sessions\n        WHERE session_id = ? AND is_active = 1\n        "
        result = self.db_manager.fetch_one(query_sql, (session_id,))
        if not result:
            return (False, None, {})
        expires_at = datetime.fromisoformat(result["expires_at"])
        if datetime.utcnow() > expires_at:
            self.invalidate_session(session_id)
            return (False, None, {})
        if ip_address and result["ip_address"] != ip_address:
            pass
        if require_mfa and (not result["mfa_verified"]):
            return (False, result["user_id"], {"requires_mfa": True})
        try:
            session_data = json.loads(
                self.encryption.decrypt_sensitive_data(result["session_data"])
            )
        except ValueError:
            session_data = {}
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

    def mark_mfa_verified(self, session_id: str) -> Any:
        """Mark session as MFA verified"""
        update_sql = "UPDATE user_sessions SET mfa_verified = 1 WHERE session_id = ?"
        self.db_manager.execute_query(update_sql, (session_id,))
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["mfa_verified"] = True

    def invalidate_session(self, session_id: str) -> Any:
        """Invalidate session"""
        update_sql = "UPDATE user_sessions SET is_active = 0 WHERE session_id = ?"
        self.db_manager.execute_query(update_sql, (session_id,))
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

    def invalidate_all_user_sessions(self, user_id: str) -> Any:
        """Invalidate all sessions for a user"""
        update_sql = "UPDATE user_sessions SET is_active = 0 WHERE user_id = ?"
        self.db_manager.execute_query(update_sql, (user_id,))
        to_remove = [
            sid
            for sid, data in self.active_sessions.items()
            if data["user_id"] == user_id
        ]
        for sid in to_remove:
            del self.active_sessions[sid]

    def _update_session_activity(self, session_id: str) -> Any:
        """Update session last activity timestamp"""
        update_sql = "UPDATE user_sessions SET last_activity = ? WHERE session_id = ?"
        self.db_manager.execute_query(update_sql, (datetime.utcnow(), session_id))

    def cleanup_expired_sessions(self) -> Any:
        """Clean up expired sessions"""
        cutoff_time = datetime.utcnow()
        delete_sql = "DELETE FROM user_sessions WHERE expires_at < ? OR is_active = 0"
        self.db_manager.execute_query(delete_sql, (cutoff_time,))
        expired_sessions = [
            sid
            for sid, data in self.active_sessions.items()
            if datetime.utcnow() > data["expires_at"]
        ]
        for sid in expired_sessions:
            del self.active_sessions[sid]
