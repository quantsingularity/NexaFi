"""
Zero-Trust Security Framework for NexaFi
Implements comprehensive zero-trust architecture with never trust, always verify principles
"""

import asyncio
import hashlib
import hmac
import ipaddress
import json
import logging
import os
import re
import socket
import ssl
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

import aiohttp
import bcrypt
import dns.resolver
import geoip2.database
import jwt
import redis
import requests
import user_agents
import whois
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from flask import g, request
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class TrustLevel(Enum):
    """Trust levels for zero-trust evaluation"""

    UNTRUSTED = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    VERIFIED = 4


class RiskLevel(Enum):
    """Risk levels for security assessment"""

    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    MINIMAL = 1


class AccessDecision(Enum):
    """Access control decisions"""

    ALLOW = "allow"
    DENY = "deny"
    CHALLENGE = "challenge"
    MONITOR = "monitor"


@dataclass
class SecurityContext:
    """Security context for requests"""

    user_id: str
    session_id: str
    device_id: str
    ip_address: str
    user_agent: str
    location: Dict[str, Any]
    timestamp: datetime
    trust_score: float
    risk_score: float
    authentication_factors: List[str]
    device_fingerprint: str
    network_info: Dict[str, Any]
    behavioral_score: float
    compliance_status: Dict[str, Any]


@dataclass
class PolicyRule:
    """Zero-trust policy rule"""

    rule_id: str
    name: str
    description: str
    conditions: Dict[str, Any]
    action: AccessDecision
    priority: int
    enabled: bool
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]


class SecurityEvent(Base):
    """Security event model"""

    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True)
    event_id = Column(String(100), unique=True, nullable=False)
    event_type = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)
    user_id = Column(String(100))
    session_id = Column(String(100))
    ip_address = Column(String(50))
    user_agent = Column(Text)
    resource = Column(String(200))
    action = Column(String(100))
    decision = Column(String(50))
    trust_score = Column(Float)
    risk_score = Column(Float)
    details = Column(Text)  # JSON
    timestamp = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)


class DeviceFingerprint(Base):
    """Device fingerprint model"""

    __tablename__ = "device_fingerprints"

    id = Column(Integer, primary_key=True)
    device_id = Column(String(100), unique=True, nullable=False)
    user_id = Column(String(100))
    fingerprint_hash = Column(String(256), nullable=False)
    device_info = Column(Text)  # JSON
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    trust_level = Column(String(50), default=TrustLevel.UNTRUSTED.name)
    is_trusted = Column(Boolean, default=False)
    risk_indicators = Column(Text)  # JSON


class UserBehavior(Base):
    """User behavior tracking"""

    __tablename__ = "user_behaviors"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), nullable=False)
    session_id = Column(String(100))
    action_type = Column(String(100), nullable=False)
    resource = Column(String(200))
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(50))
    location = Column(Text)  # JSON
    device_id = Column(String(100))
    success = Column(Boolean)
    anomaly_score = Column(Float, default=0.0)
    metadata = Column(Text)  # JSON


class ThreatIntelligence(Base):
    """Threat intelligence data"""

    __tablename__ = "threat_intelligence"

    id = Column(Integer, primary_key=True)
    indicator_type = Column(String(50), nullable=False)  # ip, domain, hash, etc.
    indicator_value = Column(String(500), nullable=False)
    threat_type = Column(String(100))
    severity = Column(String(50))
    confidence = Column(Float)
    source = Column(String(100))
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    metadata = Column(Text)  # JSON


class ContextAnalyzer:
    """Analyzes security context for zero-trust decisions"""

    def __init__(
        self, redis_client: redis.Redis, db_session, geoip_db_path: str = None
    ):
        self.redis_client = redis_client
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)

        # Initialize GeoIP database
        self.geoip_reader = None
        if geoip_db_path and os.path.exists(geoip_db_path):
            try:
                self.geoip_reader = geoip2.database.Reader(geoip_db_path)
            except Exception as e:
                self.logger.error(f"Failed to load GeoIP database: {str(e)}")

    def analyze_request_context(
        self, user_id: str, request_data: Dict[str, Any]
    ) -> SecurityContext:
        """Analyze request context and generate security context"""
        try:
            # Extract basic information
            ip_address = request_data.get("ip_address", "")
            user_agent = request_data.get("user_agent", "")
            session_id = request_data.get("session_id", "")

            # Generate device fingerprint
            device_fingerprint = self._generate_device_fingerprint(request_data)
            device_id = hashlib.sha256(device_fingerprint.encode()).hexdigest()[:16]

            # Get location information
            location = self._get_location_info(ip_address)

            # Get network information
            network_info = self._analyze_network(ip_address)

            # Calculate trust score
            trust_score = self._calculate_trust_score(
                user_id, device_id, ip_address, location
            )

            # Calculate risk score
            risk_score = self._calculate_risk_score(
                user_id, ip_address, user_agent, location
            )

            # Get authentication factors
            auth_factors = self._get_authentication_factors(user_id, session_id)

            # Calculate behavioral score
            behavioral_score = self._calculate_behavioral_score(user_id, request_data)

            # Get compliance status
            compliance_status = self._get_compliance_status(user_id, device_id)

            return SecurityContext(
                user_id=user_id,
                session_id=session_id,
                device_id=device_id,
                ip_address=ip_address,
                user_agent=user_agent,
                location=location,
                timestamp=datetime.utcnow(),
                trust_score=trust_score,
                risk_score=risk_score,
                authentication_factors=auth_factors,
                device_fingerprint=device_fingerprint,
                network_info=network_info,
                behavioral_score=behavioral_score,
                compliance_status=compliance_status,
            )

        except Exception as e:
            self.logger.error(f"Context analysis failed: {str(e)}")
            # Return minimal context with low trust
            return SecurityContext(
                user_id=user_id,
                session_id=session_id or "",
                device_id="unknown",
                ip_address=ip_address,
                user_agent=user_agent,
                location={},
                timestamp=datetime.utcnow(),
                trust_score=0.0,
                risk_score=1.0,
                authentication_factors=[],
                device_fingerprint="",
                network_info={},
                behavioral_score=0.0,
                compliance_status={},
            )

    def _generate_device_fingerprint(self, request_data: Dict[str, Any]) -> str:
        """Generate device fingerprint from request data"""
        fingerprint_data = {
            "user_agent": request_data.get("user_agent", ""),
            "accept_language": request_data.get("accept_language", ""),
            "accept_encoding": request_data.get("accept_encoding", ""),
            "screen_resolution": request_data.get("screen_resolution", ""),
            "timezone": request_data.get("timezone", ""),
            "platform": request_data.get("platform", ""),
            "plugins": request_data.get("plugins", []),
            "fonts": request_data.get("fonts", []),
            "canvas_fingerprint": request_data.get("canvas_fingerprint", ""),
            "webgl_fingerprint": request_data.get("webgl_fingerprint", ""),
        }

        fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()

    def _get_location_info(self, ip_address: str) -> Dict[str, Any]:
        """Get location information from IP address"""
        if not self.geoip_reader or not ip_address:
            return {}

        try:
            response = self.geoip_reader.city(ip_address)
            return {
                "country": response.country.name,
                "country_code": response.country.iso_code,
                "city": response.city.name,
                "latitude": (
                    float(response.location.latitude)
                    if response.location.latitude
                    else None
                ),
                "longitude": (
                    float(response.location.longitude)
                    if response.location.longitude
                    else None
                ),
                "timezone": response.location.time_zone,
                "accuracy_radius": response.location.accuracy_radius,
                "is_anonymous_proxy": response.traits.is_anonymous_proxy,
                "is_satellite_provider": response.traits.is_satellite_provider,
            }
        except Exception as e:
            self.logger.warning(f"GeoIP lookup failed for {ip_address}: {str(e)}")
            return {}

    def _analyze_network(self, ip_address: str) -> Dict[str, Any]:
        """Analyze network information"""
        network_info = {
            "is_private": False,
            "is_loopback": False,
            "is_multicast": False,
            "is_reserved": False,
            "network_type": "unknown",
            "asn": None,
            "organization": None,
        }

        try:
            ip = ipaddress.ip_address(ip_address)
            network_info.update(
                {
                    "is_private": ip.is_private,
                    "is_loopback": ip.is_loopback,
                    "is_multicast": ip.is_multicast,
                    "is_reserved": ip.is_reserved,
                    "network_type": "ipv6" if ip.version == 6 else "ipv4",
                }
            )

            # Check against threat intelligence
            threat_info = self._check_threat_intelligence(ip_address)
            if threat_info:
                network_info["threat_indicators"] = threat_info

        except Exception as e:
            self.logger.warning(f"Network analysis failed for {ip_address}: {str(e)}")

        return network_info

    def _calculate_trust_score(
        self, user_id: str, device_id: str, ip_address: str, location: Dict[str, Any]
    ) -> float:
        """Calculate trust score based on various factors"""
        trust_score = 0.0

        try:
            # Device trust (40% weight)
            device_trust = self._get_device_trust(device_id, user_id)
            trust_score += device_trust * 0.4

            # Location trust (20% weight)
            location_trust = self._get_location_trust(user_id, location)
            trust_score += location_trust * 0.2

            # IP reputation (20% weight)
            ip_trust = self._get_ip_trust(ip_address)
            trust_score += ip_trust * 0.2

            # Historical behavior (20% weight)
            behavior_trust = self._get_behavior_trust(user_id)
            trust_score += behavior_trust * 0.2

            return min(max(trust_score, 0.0), 1.0)

        except Exception as e:
            self.logger.error(f"Trust score calculation failed: {str(e)}")
            return 0.0

    def _calculate_risk_score(
        self, user_id: str, ip_address: str, user_agent: str, location: Dict[str, Any]
    ) -> float:
        """Calculate risk score based on various factors"""
        risk_score = 0.0

        try:
            # Threat intelligence check (30% weight)
            threat_risk = self._get_threat_risk(ip_address)
            risk_score += threat_risk * 0.3

            # Anomaly detection (25% weight)
            anomaly_risk = self._get_anomaly_risk(user_id, ip_address, location)
            risk_score += anomaly_risk * 0.25

            # User agent analysis (15% weight)
            ua_risk = self._analyze_user_agent_risk(user_agent)
            risk_score += ua_risk * 0.15

            # Geographic risk (15% weight)
            geo_risk = self._get_geographic_risk(location)
            risk_score += geo_risk * 0.15

            # Time-based risk (15% weight)
            time_risk = self._get_time_based_risk(user_id)
            risk_score += time_risk * 0.15

            return min(max(risk_score, 0.0), 1.0)

        except Exception as e:
            self.logger.error(f"Risk score calculation failed: {str(e)}")
            return 1.0  # Default to high risk on error

    def _get_device_trust(self, device_id: str, user_id: str) -> float:
        """Get device trust level"""
        try:
            device = (
                self.db_session.query(DeviceFingerprint)
                .filter_by(device_id=device_id, user_id=user_id)
                .first()
            )

            if not device:
                return 0.0  # Unknown device

            if device.is_trusted:
                return 0.9

            # Calculate based on usage history
            days_since_first_seen = (datetime.utcnow() - device.first_seen).days
            if days_since_first_seen > 30:
                return 0.7
            elif days_since_first_seen > 7:
                return 0.5
            else:
                return 0.3

        except Exception as e:
            self.logger.error(f"Device trust calculation failed: {str(e)}")
            return 0.0

    def _get_location_trust(self, user_id: str, location: Dict[str, Any]) -> float:
        """Get location trust level"""
        if not location:
            return 0.5

        try:
            # Check if location is in user's typical locations
            cache_key = f"user_locations:{user_id}"
            typical_locations = self.redis_client.get(cache_key)

            if typical_locations:
                typical_locations = json.loads(typical_locations)
                current_country = location.get("country_code", "")

                if current_country in typical_locations:
                    return 0.8
                else:
                    return 0.3  # New location

            return 0.5  # No history

        except Exception as e:
            self.logger.error(f"Location trust calculation failed: {str(e)}")
            return 0.5

    def _get_ip_trust(self, ip_address: str) -> float:
        """Get IP address trust level"""
        try:
            # Check threat intelligence
            threat = (
                self.db_session.query(ThreatIntelligence)
                .filter_by(
                    indicator_type="ip", indicator_value=ip_address, is_active=True
                )
                .first()
            )

            if threat:
                if threat.severity == "critical":
                    return 0.0
                elif threat.severity == "high":
                    return 0.2
                elif threat.severity == "medium":
                    return 0.4
                else:
                    return 0.6

            # Check IP reputation cache
            cache_key = f"ip_reputation:{ip_address}"
            reputation = self.redis_client.get(cache_key)

            if reputation:
                return float(reputation)

            return 0.7  # Default for unknown IPs

        except Exception as e:
            self.logger.error(f"IP trust calculation failed: {str(e)}")
            return 0.5

    def _get_behavior_trust(self, user_id: str) -> float:
        """Get behavioral trust level"""
        try:
            # Get recent behavior patterns
            recent_behaviors = (
                self.db_session.query(UserBehavior)
                .filter(
                    UserBehavior.user_id == user_id,
                    UserBehavior.timestamp >= datetime.utcnow() - timedelta(days=30),
                )
                .all()
            )

            if not recent_behaviors:
                return 0.5

            # Calculate average anomaly score
            anomaly_scores = [
                b.anomaly_score for b in recent_behaviors if b.anomaly_score is not None
            ]

            if anomaly_scores:
                avg_anomaly = sum(anomaly_scores) / len(anomaly_scores)
                return max(0.0, 1.0 - avg_anomaly)

            return 0.7

        except Exception as e:
            self.logger.error(f"Behavior trust calculation failed: {str(e)}")
            return 0.5

    def _get_threat_risk(self, ip_address: str) -> float:
        """Get threat risk from IP address"""
        try:
            threat = (
                self.db_session.query(ThreatIntelligence)
                .filter_by(
                    indicator_type="ip", indicator_value=ip_address, is_active=True
                )
                .first()
            )

            if threat:
                severity_map = {"critical": 1.0, "high": 0.8, "medium": 0.6, "low": 0.4}
                return severity_map.get(threat.severity, 0.5)

            return 0.0

        except Exception as e:
            self.logger.error(f"Threat risk calculation failed: {str(e)}")
            return 0.0

    def _get_anomaly_risk(
        self, user_id: str, ip_address: str, location: Dict[str, Any]
    ) -> float:
        """Get anomaly risk score"""
        risk_factors = []

        try:
            # Check for unusual location
            if location:
                cache_key = f"user_locations:{user_id}"
                typical_locations = self.redis_client.get(cache_key)

                if typical_locations:
                    typical_locations = json.loads(typical_locations)
                    current_country = location.get("country_code", "")

                    if current_country not in typical_locations:
                        risk_factors.append(0.6)  # New location risk

            # Check for unusual time
            current_hour = datetime.utcnow().hour
            cache_key = f"user_active_hours:{user_id}"
            typical_hours = self.redis_client.get(cache_key)

            if typical_hours:
                typical_hours = json.loads(typical_hours)
                if current_hour not in typical_hours:
                    risk_factors.append(0.4)  # Unusual time risk

            # Check for rapid requests
            cache_key = f"user_request_rate:{user_id}"
            request_count = self.redis_client.get(cache_key)

            if (
                request_count and int(request_count) > 100
            ):  # More than 100 requests in window
                risk_factors.append(0.8)  # High request rate risk

            return min(sum(risk_factors), 1.0) if risk_factors else 0.0

        except Exception as e:
            self.logger.error(f"Anomaly risk calculation failed: {str(e)}")
            return 0.0

    def _analyze_user_agent_risk(self, user_agent: str) -> float:
        """Analyze user agent for risk indicators"""
        if not user_agent:
            return 0.5

        try:
            ua = user_agents.parse(user_agent)

            risk_score = 0.0

            # Check for automated tools
            if any(
                bot in user_agent.lower()
                for bot in ["bot", "crawler", "spider", "scraper"]
            ):
                risk_score += 0.6

            # Check for outdated browsers
            if ua.browser.family and ua.browser.version_string:
                # This is a simplified check - in production, maintain a database of vulnerable versions
                if "Internet Explorer" in ua.browser.family:
                    risk_score += 0.4

            # Check for suspicious patterns
            if len(user_agent) < 20 or len(user_agent) > 500:
                risk_score += 0.3

            return min(risk_score, 1.0)

        except Exception as e:
            self.logger.error(f"User agent analysis failed: {str(e)}")
            return 0.0

    def _get_geographic_risk(self, location: Dict[str, Any]) -> float:
        """Get geographic risk score"""
        if not location:
            return 0.3

        try:
            country_code = location.get("country_code", "")

            # High-risk countries (this should be configurable)
            high_risk_countries = ["CN", "RU", "KP", "IR"]  # Example list
            medium_risk_countries = ["PK", "BD", "NG"]  # Example list

            if country_code in high_risk_countries:
                return 0.8
            elif country_code in medium_risk_countries:
                return 0.5

            # Check for anonymous proxy indicators
            if location.get("is_anonymous_proxy", False):
                return 0.9

            return 0.1  # Low risk for most countries

        except Exception as e:
            self.logger.error(f"Geographic risk calculation failed: {str(e)}")
            return 0.3

    def _get_time_based_risk(self, user_id: str) -> float:
        """Get time-based risk score"""
        try:
            current_time = datetime.utcnow()
            current_hour = current_time.hour

            # Check user's typical active hours
            cache_key = f"user_active_hours:{user_id}"
            typical_hours = self.redis_client.get(cache_key)

            if typical_hours:
                typical_hours = json.loads(typical_hours)

                if current_hour in typical_hours:
                    return 0.0  # Normal time
                else:
                    return 0.4  # Unusual time

            # Default business hours check
            if 9 <= current_hour <= 17:
                return 0.1  # Business hours
            elif 18 <= current_hour <= 22:
                return 0.2  # Evening
            else:
                return 0.5  # Night/early morning

        except Exception as e:
            self.logger.error(f"Time-based risk calculation failed: {str(e)}")
            return 0.0

    def _get_authentication_factors(self, user_id: str, session_id: str) -> List[str]:
        """Get authentication factors for the session"""
        try:
            cache_key = f"session_auth_factors:{session_id}"
            factors = self.redis_client.get(cache_key)

            if factors:
                return json.loads(factors)

            return ["password"]  # Default

        except Exception as e:
            self.logger.error(f"Authentication factors retrieval failed: {str(e)}")
            return []

    def _calculate_behavioral_score(
        self, user_id: str, request_data: Dict[str, Any]
    ) -> float:
        """Calculate behavioral score based on user patterns"""
        try:
            # Get recent user behavior
            recent_behaviors = (
                self.db_session.query(UserBehavior)
                .filter(
                    UserBehavior.user_id == user_id,
                    UserBehavior.timestamp >= datetime.utcnow() - timedelta(hours=24),
                )
                .all()
            )

            if not recent_behaviors:
                return 0.5

            # Analyze patterns
            action_counts = {}
            for behavior in recent_behaviors:
                action_counts[behavior.action_type] = (
                    action_counts.get(behavior.action_type, 0) + 1
                )

            # Check for unusual activity patterns
            total_actions = len(recent_behaviors)
            if total_actions > 1000:  # Very high activity
                return 0.2
            elif total_actions > 500:  # High activity
                return 0.4
            elif total_actions < 5:  # Very low activity
                return 0.6
            else:
                return 0.8  # Normal activity

        except Exception as e:
            self.logger.error(f"Behavioral score calculation failed: {str(e)}")
            return 0.5

    def _get_compliance_status(self, user_id: str, device_id: str) -> Dict[str, Any]:
        """Get compliance status for user and device"""
        try:
            compliance_status = {
                "gdpr_compliant": True,
                "pci_compliant": True,
                "sox_compliant": True,
                "device_compliant": True,
                "policy_violations": [],
            }

            # Check device compliance
            device = (
                self.db_session.query(DeviceFingerprint)
                .filter_by(device_id=device_id)
                .first()
            )
            if device and device.risk_indicators:
                risk_indicators = json.loads(device.risk_indicators)
                if risk_indicators:
                    compliance_status["device_compliant"] = False
                    compliance_status["policy_violations"].extend(risk_indicators)

            return compliance_status

        except Exception as e:
            self.logger.error(f"Compliance status check failed: {str(e)}")
            return {"compliant": False, "error": str(e)}

    def _check_threat_intelligence(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Check IP against threat intelligence"""
        try:
            threat = (
                self.db_session.query(ThreatIntelligence)
                .filter_by(
                    indicator_type="ip", indicator_value=ip_address, is_active=True
                )
                .first()
            )

            if threat:
                return {
                    "threat_type": threat.threat_type,
                    "severity": threat.severity,
                    "confidence": threat.confidence,
                    "source": threat.source,
                    "first_seen": threat.first_seen.isoformat(),
                    "last_seen": threat.last_seen.isoformat(),
                }

            return None

        except Exception as e:
            self.logger.error(f"Threat intelligence check failed: {str(e)}")
            return None


class PolicyEngine:
    """Zero-trust policy engine"""

    def __init__(self, redis_client: redis.Redis, db_session):
        self.redis_client = redis_client
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)
        self.policies: List[PolicyRule] = []
        self._load_policies()

    def _load_policies(self):
        """Load policies from configuration"""
        # Default policies
        default_policies = [
            PolicyRule(
                rule_id="high_risk_deny",
                name="High Risk Deny",
                description="Deny access for high-risk requests",
                conditions={"risk_score": {"operator": ">=", "value": 0.8}},
                action=AccessDecision.DENY,
                priority=1,
                enabled=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                metadata={},
            ),
            PolicyRule(
                rule_id="low_trust_challenge",
                name="Low Trust Challenge",
                description="Challenge low-trust requests",
                conditions={"trust_score": {"operator": "<=", "value": 0.3}},
                action=AccessDecision.CHALLENGE,
                priority=2,
                enabled=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                metadata={},
            ),
            PolicyRule(
                rule_id="unknown_device_challenge",
                name="Unknown Device Challenge",
                description="Challenge requests from unknown devices",
                conditions={"device_trust": {"operator": "==", "value": 0.0}},
                action=AccessDecision.CHALLENGE,
                priority=3,
                enabled=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                metadata={},
            ),
            PolicyRule(
                rule_id="threat_intel_deny",
                name="Threat Intelligence Deny",
                description="Deny access from known threat sources",
                conditions={"threat_indicators": {"operator": "exists", "value": True}},
                action=AccessDecision.DENY,
                priority=1,
                enabled=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                metadata={},
            ),
        ]

        self.policies = default_policies
        self.logger.info(f"Loaded {len(self.policies)} policies")

    def evaluate_access(
        self, context: SecurityContext, resource: str, action: str
    ) -> Tuple[AccessDecision, str]:
        """Evaluate access decision based on context and policies"""
        try:
            # Sort policies by priority
            sorted_policies = sorted(self.policies, key=lambda p: p.priority)

            for policy in sorted_policies:
                if not policy.enabled:
                    continue

                if self._evaluate_conditions(
                    policy.conditions, context, resource, action
                ):
                    self.logger.info(
                        f"Policy matched: {policy.name} -> {policy.action.value}"
                    )
                    return policy.action, policy.name

            # Default allow if no policies match
            return AccessDecision.ALLOW, "default_allow"

        except Exception as e:
            self.logger.error(f"Policy evaluation failed: {str(e)}")
            return AccessDecision.DENY, "evaluation_error"

    def _evaluate_conditions(
        self,
        conditions: Dict[str, Any],
        context: SecurityContext,
        resource: str,
        action: str,
    ) -> bool:
        """Evaluate policy conditions against context"""
        try:
            for field, condition in conditions.items():
                if not self._evaluate_condition(
                    field, condition, context, resource, action
                ):
                    return False
            return True

        except Exception as e:
            self.logger.error(f"Condition evaluation failed: {str(e)}")
            return False

    def _evaluate_condition(
        self,
        field: str,
        condition: Dict[str, Any],
        context: SecurityContext,
        resource: str,
        action: str,
    ) -> bool:
        """Evaluate single condition"""
        operator = condition.get("operator")
        value = condition.get("value")

        # Get field value from context
        if field == "risk_score":
            field_value = context.risk_score
        elif field == "trust_score":
            field_value = context.trust_score
        elif field == "device_trust":
            # This would need to be calculated or stored in context
            field_value = 0.0  # Placeholder
        elif field == "threat_indicators":
            field_value = bool(context.network_info.get("threat_indicators"))
        elif field == "location_country":
            field_value = context.location.get("country_code", "")
        elif field == "authentication_factors":
            field_value = len(context.authentication_factors)
        else:
            return False

        # Evaluate operator
        if operator == ">=":
            return field_value >= value
        elif operator == "<=":
            return field_value <= value
        elif operator == "==":
            return field_value == value
        elif operator == "!=":
            return field_value != value
        elif operator == ">":
            return field_value > value
        elif operator == "<":
            return field_value < value
        elif operator == "in":
            return field_value in value
        elif operator == "not_in":
            return field_value not in value
        elif operator == "exists":
            return bool(field_value) == value
        else:
            return False

    def add_policy(self, policy: PolicyRule):
        """Add new policy"""
        self.policies.append(policy)
        self.policies.sort(key=lambda p: p.priority)
        self.logger.info(f"Added policy: {policy.name}")

    def remove_policy(self, rule_id: str):
        """Remove policy by ID"""
        self.policies = [p for p in self.policies if p.rule_id != rule_id]
        self.logger.info(f"Removed policy: {rule_id}")

    def update_policy(self, rule_id: str, updates: Dict[str, Any]):
        """Update existing policy"""
        for policy in self.policies:
            if policy.rule_id == rule_id:
                for key, value in updates.items():
                    if hasattr(policy, key):
                        setattr(policy, key, value)
                policy.updated_at = datetime.utcnow()
                self.logger.info(f"Updated policy: {rule_id}")
                break


class ZeroTrustFramework:
    """Main zero-trust framework"""

    def __init__(
        self, redis_client: redis.Redis, db_session, geoip_db_path: str = None
    ):
        self.redis_client = redis_client
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.context_analyzer = ContextAnalyzer(redis_client, db_session, geoip_db_path)
        self.policy_engine = PolicyEngine(redis_client, db_session)

        # Initialize database tables
        Base.metadata.create_all(bind=db_session.bind)

    def evaluate_request(
        self, user_id: str, resource: str, action: str, request_data: Dict[str, Any]
    ) -> Tuple[AccessDecision, SecurityContext, str]:
        """Evaluate request and return access decision"""
        try:
            # Analyze security context
            context = self.context_analyzer.analyze_request_context(
                user_id, request_data
            )

            # Evaluate access policy
            decision, policy_name = self.policy_engine.evaluate_access(
                context, resource, action
            )

            # Log security event
            self._log_security_event(context, resource, action, decision, policy_name)

            # Update user behavior tracking
            self._track_user_behavior(
                context, resource, action, decision == AccessDecision.ALLOW
            )

            # Update device fingerprint
            self._update_device_fingerprint(context)

            return decision, context, policy_name

        except Exception as e:
            self.logger.error(f"Request evaluation failed: {str(e)}")
            return AccessDecision.DENY, None, "evaluation_error"

    def _log_security_event(
        self,
        context: SecurityContext,
        resource: str,
        action: str,
        decision: AccessDecision,
        policy_name: str,
    ):
        """Log security event"""
        try:
            event = SecurityEvent(
                event_id=str(uuid.uuid4()),
                event_type="access_request",
                severity="info" if decision == AccessDecision.ALLOW else "warning",
                user_id=context.user_id,
                session_id=context.session_id,
                ip_address=context.ip_address,
                user_agent=context.user_agent,
                resource=resource,
                action=action,
                decision=decision.value,
                trust_score=context.trust_score,
                risk_score=context.risk_score,
                details=json.dumps(
                    {
                        "policy_name": policy_name,
                        "location": context.location,
                        "device_id": context.device_id,
                        "authentication_factors": context.authentication_factors,
                    }
                ),
            )

            self.db_session.add(event)
            self.db_session.commit()

        except Exception as e:
            self.logger.error(f"Security event logging failed: {str(e)}")

    def _track_user_behavior(
        self, context: SecurityContext, resource: str, action: str, success: bool
    ):
        """Track user behavior"""
        try:
            behavior = UserBehavior(
                user_id=context.user_id,
                session_id=context.session_id,
                action_type=action,
                resource=resource,
                ip_address=context.ip_address,
                location=json.dumps(context.location),
                device_id=context.device_id,
                success=success,
                anomaly_score=1.0 - context.behavioral_score,
                metadata=json.dumps(
                    {
                        "trust_score": context.trust_score,
                        "risk_score": context.risk_score,
                    }
                ),
            )

            self.db_session.add(behavior)
            self.db_session.commit()

        except Exception as e:
            self.logger.error(f"Behavior tracking failed: {str(e)}")

    def _update_device_fingerprint(self, context: SecurityContext):
        """Update device fingerprint information"""
        try:
            device = (
                self.db_session.query(DeviceFingerprint)
                .filter_by(device_id=context.device_id)
                .first()
            )

            if device:
                device.last_seen = datetime.utcnow()
                device.user_id = context.user_id
            else:
                device = DeviceFingerprint(
                    device_id=context.device_id,
                    user_id=context.user_id,
                    fingerprint_hash=hashlib.sha256(
                        context.device_fingerprint.encode()
                    ).hexdigest(),
                    device_info=json.dumps(
                        {
                            "user_agent": context.user_agent,
                            "first_ip": context.ip_address,
                        }
                    ),
                    trust_level=TrustLevel.UNTRUSTED.name,
                )
                self.db_session.add(device)

            self.db_session.commit()

        except Exception as e:
            self.logger.error(f"Device fingerprint update failed: {str(e)}")

    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics"""
        try:
            # Get recent events
            recent_events = (
                self.db_session.query(SecurityEvent)
                .filter(
                    SecurityEvent.timestamp >= datetime.utcnow() - timedelta(hours=24)
                )
                .all()
            )

            total_requests = len(recent_events)
            allowed_requests = len([e for e in recent_events if e.decision == "allow"])
            denied_requests = len([e for e in recent_events if e.decision == "deny"])
            challenged_requests = len(
                [e for e in recent_events if e.decision == "challenge"]
            )

            # Calculate average scores
            trust_scores = [
                e.trust_score for e in recent_events if e.trust_score is not None
            ]
            risk_scores = [
                e.risk_score for e in recent_events if e.risk_score is not None
            ]

            avg_trust_score = (
                sum(trust_scores) / len(trust_scores) if trust_scores else 0
            )
            avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0

            return {
                "total_requests_24h": total_requests,
                "allowed_requests": allowed_requests,
                "denied_requests": denied_requests,
                "challenged_requests": challenged_requests,
                "allow_rate": (
                    allowed_requests / total_requests if total_requests > 0 else 0
                ),
                "deny_rate": (
                    denied_requests / total_requests if total_requests > 0 else 0
                ),
                "challenge_rate": (
                    challenged_requests / total_requests if total_requests > 0 else 0
                ),
                "average_trust_score": avg_trust_score,
                "average_risk_score": avg_risk_score,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Security metrics calculation failed: {str(e)}")
            return {"error": str(e)}


def create_zero_trust_framework(
    database_url: str, redis_url: str, geoip_db_path: str = None
) -> ZeroTrustFramework:
    """Factory function to create zero-trust framework"""

    # Create database session
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    db_session = Session()

    # Create Redis client
    redis_client = redis.from_url(redis_url, decode_responses=True)

    # Create framework
    framework = ZeroTrustFramework(redis_client, db_session, geoip_db_path)

    return framework


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Create zero-trust framework
    framework = create_zero_trust_framework(
        database_url="sqlite:///zero_trust.db", redis_url="redis://localhost:6379/0"
    )

    # Example request evaluation
    request_data = {
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "session_id": "session_123",
        "accept_language": "en-US,en;q=0.9",
        "screen_resolution": "1920x1080",
        "timezone": "America/New_York",
    }

    decision, context, policy = framework.evaluate_request(
        user_id="user_123",
        resource="/api/financial-data",
        action="read",
        request_data=request_data,
    )

    print(f"Access Decision: {decision.value}")
    print(f"Policy: {policy}")
    print(f"Trust Score: {context.trust_score}")
    print(f"Risk Score: {context.risk_score}")

    # Get security metrics
    metrics = framework.get_security_metrics()
    print(f"Security Metrics: {json.dumps(metrics, indent=2)}")
