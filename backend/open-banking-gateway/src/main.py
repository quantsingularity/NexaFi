"""
Open Banking API Gateway
Implements PSD2 compliant API gateway with FAPI 2.0 security
"""

import os
import sys
import time
from datetime import datetime
from functools import wraps

from flask import Flask, g, jsonify, request
from flask_cors import CORS

# Add shared modules to path
sys.path.append("/home/ubuntu/NexaFi/backend/shared")

from logging.logger import get_logger, setup_request_logging

from audit.audit_logger import AuditEventType, AuditSeverity, audit_action, audit_logger
from database.manager import initialize_database
from enhanced_security import (
    AdvancedEncryption,
    FraudDetectionEngine,
    MultiFactorAuthentication,
    SecurityEvent,
    SecurityEventType,
    SecurityMonitor,
    ThreatLevel,
)
from middleware.auth import require_auth, require_permission
from open_banking_compliance import (
    AuthenticationMethod,
    ConsentStatus,
    FAPI2SecurityProfile,
    OpenBankingAPIValidator,
    PSD2ConsentManager,
    SCAManager,
    TransactionRiskAnalysis,
)
from validators.schemas import (
    SanitizationMixin,
    Schema,
    fields,
    validate,
    validate_json_request,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "nexafi-open-banking-gateway-secret-key-2024"
)

# Enable CORS
CORS(
    app,
    origins="*",
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-User-ID",
        "X-FAPI-Auth-Date",
        "X-FAPI-Customer-IP-Address",
        "X-FAPI-Interaction-ID",
        "DPoP",
    ],
)

# Setup logging
setup_request_logging(app)
logger = get_logger("open_banking_gateway")

# Initialize database
db_path = "/home/ubuntu/NexaFi/backend/open-banking-gateway/data/open_banking.db"
os.makedirs(os.path.dirname(db_path), exist_ok=True)
db_manager, migration_manager = initialize_database(db_path)

# Initialize security components
encryption = AdvancedEncryption()
security_monitor = SecurityMonitor(db_manager)
fraud_engine = FraudDetectionEngine(db_manager)
mfa_manager = MultiFactorAuthentication(db_manager)

# Initialize Open Banking components
fapi_security = FAPI2SecurityProfile(
    private_key_path="/home/ubuntu/NexaFi/backend/open-banking-gateway/keys/private_key.pem",
    public_key_path="/home/ubuntu/NexaFi/backend/open-banking-gateway/keys/public_key.pem",
)
consent_manager = PSD2ConsentManager(db_manager)
sca_manager = SCAManager(db_manager)

# TPP Registry (in production, this would be from official sources)
REGISTERED_TPPS = {
    "PSDGB-FCA-123456": {
        "organization_name": "Example TPP Ltd",
        "roles": ["PSP_PI", "PSP_AI"],
        "public_key_path": "/path/to/tpp/public/key.pem",
        "status": "active",
    }
}


# Validation schemas
class ConsentRequestSchema(SanitizationMixin, Schema):
    access = fields.Dict(required=True)
    recurringIndicator = fields.Bool(required=False, default=False)
    validUntil = fields.DateTime(required=False)
    frequencyPerDay = fields.Int(
        required=False, default=4, validate=validate.Range(min=1, max=10)
    )
    combinedServiceIndicator = fields.Bool(required=False, default=False)


class PaymentInitiationSchema(SanitizationMixin, Schema):
    instructedAmount = fields.Dict(required=True)
    debtorAccount = fields.Dict(required=True)
    creditorAccount = fields.Dict(required=True)
    creditorName = fields.Str(required=True, validate=validate.Length(min=1, max=70))
    remittanceInformationUnstructured = fields.Str(
        required=False, validate=validate.Length(max=140)
    )


class SCAInitiationSchema(SanitizationMixin, Schema):
    scaMethod = fields.Str(
        required=True,
        validate=validate.OneOf(
            [
                "sms_otp",
                "push_notification",
                "biometric",
                "hardware_token",
                "mobile_app",
            ]
        ),
    )
    psuMessage = fields.Str(required=False, validate=validate.Length(max=500))


def validate_tpp_certificate(f):
    """Decorator to validate TPP certificate"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get TPP certificate from headers
        tpp_cert = request.headers.get("TPP-Signature-Certificate")
        if not tpp_cert:
            return (
                jsonify(
                    {
                        "error": "invalid_request",
                        "error_description": "TPP certificate required",
                    }
                ),
                400,
            )

        # Validate certificate
        is_valid, cert_info = OpenBankingAPIValidator.validate_tpp_certificate(tpp_cert)
        if not is_valid:
            return (
                jsonify(
                    {
                        "error": "invalid_client",
                        "error_description": "Invalid TPP certificate",
                    }
                ),
                401,
            )

        # Store TPP info in request context
        g.tpp_id = cert_info["organization_id"]
        g.tpp_name = cert_info["organization_name"]
        g.tpp_roles = cert_info["roles"]

        return f(*args, **kwargs)

    return decorated_function


def validate_fapi_headers(f):
    """Decorator to validate FAPI required headers"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        is_valid, errors = OpenBankingAPIValidator.validate_fapi_headers(
            dict(request.headers)
        )
        if not is_valid:
            return (
                jsonify(
                    {
                        "error": "invalid_request",
                        "error_description": f'FAPI header validation failed: {", ".join(errors)}',
                    }
                ),
                400,
            )

        return f(*args, **kwargs)

    return decorated_function


def log_security_event(
    event_type: SecurityEventType, threat_level: ThreatLevel = ThreatLevel.LOW
):
    """Decorator to log security events"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()

            try:
                result = f(*args, **kwargs)

                # Log successful event
                event = SecurityEvent(
                    event_type=event_type,
                    user_id=getattr(g, "user_id", None),
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get("User-Agent", ""),
                    timestamp=datetime.utcnow(),
                    details={
                        "endpoint": request.endpoint,
                        "method": request.method,
                        "tpp_id": getattr(g, "tpp_id", None),
                        "response_time": time.time() - start_time,
                    },
                    threat_level=threat_level,
                    session_id=getattr(g, "session_id", None),
                )
                security_monitor.log_security_event(event)

                return result

            except Exception as e:
                # Log failed event
                event = SecurityEvent(
                    event_type=SecurityEventType.SECURITY_VIOLATION,
                    user_id=getattr(g, "user_id", None),
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get("User-Agent", ""),
                    timestamp=datetime.utcnow(),
                    details={
                        "endpoint": request.endpoint,
                        "method": request.method,
                        "error": str(e),
                        "tpp_id": getattr(g, "tpp_id", None),
                    },
                    threat_level=ThreatLevel.HIGH,
                    session_id=getattr(g, "session_id", None),
                )
                security_monitor.log_security_event(event)
                raise

        return decorated_function

    return decorator


@app.route("/api/v1/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "service": "open-banking-gateway",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "compliance": {"psd2": True, "fapi_2_0": True, "sca_ready": True},
        }
    )


@app.route("/api/v1/consents", methods=["POST"])
@validate_tpp_certificate
@validate_fapi_headers
@validate_json_request(ConsentRequestSchema)
@log_security_event(SecurityEventType.DATA_ACCESS, ThreatLevel.MODERATE)
@audit_action(
    AuditEventType.USER_UPDATE,
    "consent_creation_requested",
    severity=AuditSeverity.HIGH,
)
def create_consent():
    """Create PSD2 consent (Account Information Service)"""
    data = request.validated_data

    # Check TPP authorization for AIS
    if "PSP_AI" not in g.tpp_roles:
        return (
            jsonify(
                {
                    "error": "unauthorized_client",
                    "error_description": "TPP not authorized for Account Information Services",
                }
            ),
            403,
        )

    # Extract PSU identification (would come from OAuth flow in production)
    psu_id = request.headers.get("PSU-ID")
    if not psu_id:
        return (
            jsonify(
                {
                    "error": "invalid_request",
                    "error_description": "PSU identification required",
                }
            ),
            400,
        )

    # Create consent
    valid_until = data.get("validUntil")
    if valid_until:
        valid_until = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))

    consent = consent_manager.create_consent(
        psu_id=psu_id,
        tpp_id=g.tpp_id,
        access_data=data["access"],
        valid_until=valid_until,
        frequency_per_day=data.get("frequencyPerDay", 4),
    )

    # Log consent creation
    audit_logger.log_event(
        AuditEventType.USER_UPDATE,
        "consent_created",
        user_id=psu_id,
        resource_type="psd2_consent",
        resource_id=consent.consent_id,
        details={
            "tpp_id": g.tpp_id,
            "access_scope": data["access"],
            "valid_until": consent.valid_until.isoformat(),
        },
        severity=AuditSeverity.HIGH,
    )

    logger.info(
        f"Consent created: {consent.consent_id} for PSU {psu_id} by TPP {g.tpp_id}"
    )

    return (
        jsonify(
            {
                "consentId": consent.consent_id,
                "consentStatus": consent.status.value,
                "validUntil": consent.valid_until.isoformat(),
                "_links": {
                    "scaRedirect": f"/api/v1/consents/{consent.consent_id}/authorisations",
                    "self": f"/api/v1/consents/{consent.consent_id}",
                    "status": f"/api/v1/consents/{consent.consent_id}/status",
                },
            }
        ),
        201,
    )


@app.route("/api/v1/consents/<consent_id>", methods=["GET"])
@validate_tpp_certificate
@validate_fapi_headers
@log_security_event(SecurityEventType.DATA_ACCESS)
def get_consent(consent_id):
    """Get consent details"""
    consent = consent_manager.get_consent(consent_id)

    if not consent:
        return (
            jsonify({"error": "not_found", "error_description": "Consent not found"}),
            404,
        )

    # Verify TPP authorization
    if consent.tpp_id != g.tpp_id:
        return (
            jsonify(
                {
                    "error": "forbidden",
                    "error_description": "TPP not authorized for this consent",
                }
            ),
            403,
        )

    return jsonify(
        {
            "consentId": consent.consent_id,
            "consentStatus": consent.status.value,
            "validUntil": consent.valid_until.isoformat(),
            "frequencyPerDay": consent.frequency_per_day,
            "recurringIndicator": consent.recurring_indicator,
            "access": consent.access,
            "lastActionDate": consent.status_change_date_time.isoformat(),
        }
    )


@app.route("/api/v1/consents/<consent_id>/authorisations", methods=["POST"])
@validate_tpp_certificate
@validate_fapi_headers
@validate_json_request(SCAInitiationSchema)
@log_security_event(SecurityEventType.LOGIN_ATTEMPT, ThreatLevel.MODERATE)
def initiate_consent_authorisation(consent_id):
    """Initiate Strong Customer Authentication for consent"""
    data = request.validated_data

    # Validate consent
    is_valid, message = consent_manager.validate_consent(consent_id, g.tpp_id)
    if not is_valid:
        return jsonify({"error": "invalid_consent", "error_description": message}), 400

    consent = consent_manager.get_consent(consent_id)

    # Initiate SCA
    sca_method = AuthenticationMethod(data["scaMethod"])
    sca_data = sca_manager.initiate_sca(
        psu_id=consent.psu_id, sca_method=sca_method, consent_id=consent_id
    )

    logger.info(f"SCA initiated for consent {consent_id}: {sca_data.authentication_id}")

    return (
        jsonify(
            {
                "scaStatus": sca_data.status.value,
                "authorisationId": sca_data.authentication_id,
                "scaMethod": sca_data.sca_method.value,
                "psuMessage": data.get(
                    "psuMessage", "Please authenticate to authorize consent"
                ),
                "_links": {
                    "scaStatus": f"/api/v1/consents/{consent_id}/authorisations/{sca_data.authentication_id}",
                    "scaOAuth": f"/oauth2/authorize?consent_id={consent_id}&auth_id={sca_data.authentication_id}",
                },
            }
        ),
        201,
    )


@app.route(
    "/api/v1/consents/<consent_id>/authorisations/<authorisation_id>", methods=["PUT"]
)
@validate_tpp_certificate
@validate_fapi_headers
@log_security_event(SecurityEventType.LOGIN_ATTEMPT, ThreatLevel.HIGH)
def update_consent_authorisation(consent_id, authorisation_id):
    """Update SCA authorisation with authentication data"""
    data = request.get_json() or {}

    # Get authentication response
    auth_response = data.get("scaAuthenticationData")
    if not auth_response:
        return (
            jsonify(
                {
                    "error": "invalid_request",
                    "error_description": "SCA authentication data required",
                }
            ),
            400,
        )

    # Verify SCA
    is_verified, sca_status = sca_manager.verify_sca(authorisation_id, auth_response)

    if is_verified:
        # Update consent status to valid
        consent_manager.update_consent_status(consent_id, ConsentStatus.VALID)

        logger.info(f"Consent {consent_id} authorized successfully")

        return jsonify(
            {"scaStatus": sca_status.value, "consentStatus": ConsentStatus.VALID.value}
        )
    else:
        logger.warning(f"SCA verification failed for consent {consent_id}")

        return (
            jsonify(
                {
                    "scaStatus": sca_status.value,
                    "error": "authentication_failed",
                    "error_description": "Strong Customer Authentication failed",
                }
            ),
            401,
        )


@app.route("/api/v1/payments/sepa-credit-transfers", methods=["POST"])
@validate_tpp_certificate
@validate_fapi_headers
@validate_json_request(PaymentInitiationSchema)
@log_security_event(SecurityEventType.FRAUD_DETECTION, ThreatLevel.HIGH)
@audit_action(
    AuditEventType.TRANSACTION_CREATE,
    "payment_initiation_requested",
    severity=AuditSeverity.CRITICAL,
)
def initiate_payment():
    """Initiate SEPA Credit Transfer (Payment Initiation Service)"""
    data = request.validated_data

    # Check TPP authorization for PIS
    if "PSP_PI" not in g.tpp_roles:
        return (
            jsonify(
                {
                    "error": "unauthorized_client",
                    "error_description": "TPP not authorized for Payment Initiation Services",
                }
            ),
            403,
        )

    # Extract PSU identification
    psu_id = request.headers.get("PSU-ID")
    if not psu_id:
        return (
            jsonify(
                {
                    "error": "invalid_request",
                    "error_description": "PSU identification required",
                }
            ),
            400,
        )

    # Perform fraud detection
    transaction_data = {
        "amount": float(data["instructedAmount"]["amount"]),
        "currency": data["instructedAmount"]["currency"],
        "merchant_category": "bank_transfer",
        "country": "DE",  # Would be determined from creditor account
        "timestamp": datetime.utcnow().isoformat(),
    }

    user_data = {
        "risk_score": 20,
        "country": "DE",
    }  # Would be fetched from user profile

    risk_score, risk_factors = fraud_engine.analyze_transaction_behavior(
        psu_id,
        transaction_data["amount"],
        transaction_data["currency"],
        transaction_data["merchant_category"],
        request.remote_addr,
    )

    # Check if SCA exemption is possible
    exemption_eligible = TransactionRiskAnalysis.is_eligible_for_exemption(
        risk_score, transaction_data["amount"], "low_risk"
    )

    # Create payment object
    payment_id = f"payment_{int(time.time())}_{psu_id[:8]}"

    # Determine if SCA is required
    sca_required = not exemption_eligible or risk_score > 30

    if sca_required:
        # Initiate SCA for payment
        sca_data = sca_manager.initiate_sca(
            psu_id=psu_id,
            sca_method=AuthenticationMethod.SMS_OTP,  # Default method
            transaction_id=payment_id,
        )

        response_data = {
            "paymentId": payment_id,
            "transactionStatus": "RCVD",  # Received
            "scaRequired": True,
            "scaStatus": sca_data.status.value,
            "authorisationId": sca_data.authentication_id,
            "_links": {
                "scaRedirect": f"/api/v1/payments/sepa-credit-transfers/{payment_id}/authorisations/{sca_data.authentication_id}",
                "self": f"/api/v1/payments/sepa-credit-transfers/{payment_id}",
                "status": f"/api/v1/payments/sepa-credit-transfers/{payment_id}/status",
            },
        }

        if risk_score > 50:
            # Create fraud alert
            fraud_engine.create_fraud_alert(
                psu_id,
                "high_risk_payment",
                risk_score,
                {"payment_id": payment_id, "risk_factors": risk_factors},
            )
    else:
        # Process payment without SCA (exemption applied)
        response_data = {
            "paymentId": payment_id,
            "transactionStatus": "ACCP",  # Accepted
            "scaRequired": False,
            "scaExemption": "lowRisk",
            "_links": {
                "self": f"/api/v1/payments/sepa-credit-transfers/{payment_id}",
                "status": f"/api/v1/payments/sepa-credit-transfers/{payment_id}/status",
            },
        }

    # Log payment initiation
    audit_logger.log_financial_transaction(
        AuditEventType.TRANSACTION_CREATE,
        psu_id,
        payment_id,
        str(transaction_data["amount"]),
        transaction_data["currency"],
        details={
            "tpp_id": g.tpp_id,
            "creditor_name": data["creditorName"],
            "risk_score": risk_score,
            "sca_required": sca_required,
        },
    )

    logger.info(f"Payment initiated: {payment_id} for PSU {psu_id} by TPP {g.tpp_id}")

    return jsonify(response_data), 201


@app.route("/api/v1/accounts", methods=["GET"])
@validate_tpp_certificate
@validate_fapi_headers
@log_security_event(SecurityEventType.DATA_ACCESS)
def get_accounts():
    """Get account list (Account Information Service)"""
    # Get consent ID from request
    consent_id = request.headers.get("Consent-ID")
    if not consent_id:
        return (
            jsonify(
                {
                    "error": "invalid_request",
                    "error_description": "Consent-ID header required",
                }
            ),
            400,
        )

    # Validate consent
    is_valid, message = consent_manager.validate_consent(consent_id, g.tpp_id)
    if not is_valid:
        return jsonify({"error": "invalid_consent", "error_description": message}), 403

    consent = consent_manager.get_consent(consent_id)

    # Check if accounts access is granted
    if "accounts" not in consent.access:
        return (
            jsonify(
                {
                    "error": "insufficient_scope",
                    "error_description": "Consent does not include accounts access",
                }
            ),
            403,
        )

    # Mock account data (in production, fetch from core banking system)
    accounts = [
        {
            "resourceId": "account_001",
            "iban": "DE89370400440532013000",
            "currency": "EUR",
            "accountType": "Girokonto",
            "cashAccountType": "CACC",
            "name": "Main Account",
            "_links": {
                "balances": f"/api/v1/accounts/account_001/balances",
                "transactions": f"/api/v1/accounts/account_001/transactions",
            },
        }
    ]

    return jsonify({"accounts": accounts})


@app.route("/api/v1/accounts/<account_id>/balances", methods=["GET"])
@validate_tpp_certificate
@validate_fapi_headers
@log_security_event(SecurityEventType.DATA_ACCESS)
def get_account_balances(account_id):
    """Get account balances"""
    # Validate consent (similar to get_accounts)
    consent_id = request.headers.get("Consent-ID")
    if not consent_id:
        return (
            jsonify(
                {
                    "error": "invalid_request",
                    "error_description": "Consent-ID header required",
                }
            ),
            400,
        )

    is_valid, message = consent_manager.validate_consent(consent_id, g.tpp_id)
    if not is_valid:
        return jsonify({"error": "invalid_consent", "error_description": message}), 403

    # Mock balance data
    balances = [
        {
            "balanceType": "closingBooked",
            "balanceAmount": {"amount": "1500.00", "currency": "EUR"},
            "referenceDate": datetime.utcnow().date().isoformat(),
        },
        {
            "balanceType": "expected",
            "balanceAmount": {"amount": "1500.00", "currency": "EUR"},
        },
    ]

    return jsonify(
        {"account": {"iban": "DE89370400440532013000"}, "balances": balances}
    )


@app.route("/api/v1/security/threat-summary", methods=["GET"])
@require_auth
@require_permission("security:read")
def get_threat_summary():
    """Get security threat summary"""
    hours = request.args.get("hours", 24, type=int)
    summary = security_monitor.get_threat_summary(hours)

    return jsonify(summary)


@app.errorhandler(400)
def bad_request(error):
    """Handle bad request errors"""
    return (
        jsonify(
            {
                "error": "invalid_request",
                "error_description": "The request is malformed or invalid",
            }
        ),
        400,
    )


@app.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized errors"""
    return (
        jsonify(
            {
                "error": "unauthorized",
                "error_description": "Authentication required or invalid",
            }
        ),
        401,
    )


@app.errorhandler(403)
def forbidden(error):
    """Handle forbidden errors"""
    return (
        jsonify(
            {"error": "forbidden", "error_description": "Insufficient permissions"}
        ),
        403,
    )


@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {str(error)}")
    return (
        jsonify(
            {
                "error": "server_error",
                "error_description": "An internal server error occurred",
            }
        ),
        500,
    )


if __name__ == "__main__":
    # Create keys directory
    os.makedirs("/home/ubuntu/NexaFi/backend/open-banking-gateway/keys", exist_ok=True)
    os.makedirs("/home/ubuntu/NexaFi/backend/open-banking-gateway/data", exist_ok=True)

    app.run(host="0.0.0.0", port=5010, debug=False)
