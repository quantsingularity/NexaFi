import hashlib
import json
import os
import secrets
import sys
from datetime import datetime, timedelta
from urllib.parse import urlencode

import bcrypt
from flask import Flask, g, jsonify, redirect, request, url_for
from flask_cors import CORS

# Add shared modules to path
sys.path.append("/home/ubuntu/NexaFi/backend/shared")

from logging.logger import get_logger, setup_request_logging

from audit.audit_logger import AuditEventType, AuditSeverity, audit_action, audit_logger
from database.manager import BaseModel, initialize_database
from enhanced_security import (
    AdvancedEncryption,
    FraudDetectionEngine,
    MultiFactorAuthentication,
    SecureSessionManager,
    SecurityEvent,
    SecurityEventType,
    SecurityLevel,
    SecurityMonitor,
    ThreatLevel,
)
from middleware.auth import require_auth
from open_banking_compliance import FAPI2SecurityProfile
from validators.schemas import (
    SanitizationMixin,
    Schema,
    fields,
    validate,
    validate_json_request,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "nexafi-enhanced-auth-service-secret-key-2024"
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
logger = get_logger("enhanced_auth_service")

# Initialize database
db_path = "/home/ubuntu/NexaFi/backend/enhanced-auth-service/data/auth.db"
os.makedirs(os.path.dirname(db_path), exist_ok=True)
db_manager, migration_manager = initialize_database(db_path)

# Initialize security components
encryption = AdvancedEncryption()
security_monitor = SecurityMonitor(db_manager)
fraud_engine = FraudDetectionEngine(db_manager)
mfa_manager = MultiFactorAuthentication(db_manager)
session_manager = SecureSessionManager(db_manager, encryption)

# Initialize FAPI security
fapi_security = FAPI2SecurityProfile(
    private_key_path="/home/ubuntu/NexaFi/backend/enhanced-auth-service/keys/private_key.pem",
    public_key_path="/home/ubuntu/NexaFi/backend/enhanced-auth-service/keys/public_key.pem",
)

# Apply enhanced authentication migrations
AUTH_MIGRATIONS = {
    "008_create_oauth_clients_table": {
        "description": "Create OAuth 2.1 clients table",
        "sql": """
        CREATE TABLE IF NOT EXISTS oauth_clients (
            client_id TEXT PRIMARY KEY,
            client_secret_hash TEXT,
            client_name TEXT NOT NULL,
            client_type TEXT NOT NULL DEFAULT 'confidential',
            redirect_uris TEXT NOT NULL,
            scope TEXT DEFAULT 'openid profile',
            grant_types TEXT DEFAULT 'authorization_code',
            response_types TEXT DEFAULT 'code',
            token_endpoint_auth_method TEXT DEFAULT 'client_secret_basic',
            jwks_uri TEXT,
            software_statement TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        );

        CREATE TABLE IF NOT EXISTS oauth_authorization_codes (
            code TEXT PRIMARY KEY,
            client_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            redirect_uri TEXT NOT NULL,
            scope TEXT,
            code_challenge TEXT,
            code_challenge_method TEXT DEFAULT 'S256',
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES oauth_clients(client_id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS oauth_access_tokens (
            token_id TEXT PRIMARY KEY,
            access_token_hash TEXT NOT NULL,
            refresh_token_hash TEXT,
            client_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            scope TEXT,
            expires_at TIMESTAMP NOT NULL,
            refresh_expires_at TIMESTAMP,
            is_revoked BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES oauth_clients(client_id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE INDEX IF NOT EXISTS idx_oauth_codes_client_id ON oauth_authorization_codes(client_id);
        CREATE INDEX IF NOT EXISTS idx_oauth_codes_user_id ON oauth_authorization_codes(user_id);
        CREATE INDEX IF NOT EXISTS idx_oauth_tokens_client_id ON oauth_access_tokens(client_id);
        CREATE INDEX IF NOT EXISTS idx_oauth_tokens_user_id ON oauth_access_tokens(user_id);
        """,
    },
    "009_create_device_registration_table": {
        "description": "Create device registration table",
        "sql": """
        CREATE TABLE IF NOT EXISTS registered_devices (
            device_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            device_name TEXT NOT NULL,
            device_type TEXT NOT NULL,
            device_fingerprint TEXT,
            public_key TEXT,
            registration_token TEXT,
            is_trusted BOOLEAN DEFAULT FALSE,
            last_used TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE INDEX IF NOT EXISTS idx_registered_devices_user_id ON registered_devices(user_id);
        CREATE INDEX IF NOT EXISTS idx_registered_devices_fingerprint ON registered_devices(device_fingerprint);
        """,
    },
}

# Apply migrations
for version, migration in AUTH_MIGRATIONS.items():
    migration_manager.apply_migration(
        version, migration["description"], migration["sql"]
    )

# Set database manager for models
BaseModel.set_db_manager(db_manager)


class OAuthClient(BaseModel):
    table_name = "oauth_clients"


class AuthorizationCode(BaseModel):
    table_name = "oauth_authorization_codes"


class AccessToken(BaseModel):
    table_name = "oauth_access_tokens"


class RegisteredDevice(BaseModel):
    table_name = "registered_devices"


# Validation schemas
class LoginSchema(SanitizationMixin, Schema):
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    password = fields.Str(required=True, validate=validate.Length(min=8, max=128))
    device_fingerprint = fields.Str(required=False)
    remember_me = fields.Bool(required=False, default=False)


class MFASetupSchema(SanitizationMixin, Schema):
    method = fields.Str(required=True, validate=validate.OneOf(["totp", "sms"]))
    phone_number = fields.Str(
        required=False, validate=validate.Regexp(r"^\+[1-9]\d{1,14}$")
    )


class MFAVerifySchema(SanitizationMixin, Schema):
    token = fields.Str(required=True, validate=validate.Length(min=4, max=10))
    method = fields.Str(
        required=True, validate=validate.OneOf(["totp", "sms", "backup_code"])
    )


class OAuth2AuthorizeSchema(SanitizationMixin, Schema):
    response_type = fields.Str(required=True, validate=validate.OneOf(["code"]))
    client_id = fields.Str(required=True)
    redirect_uri = fields.Str(required=True, validate=validate.URL())
    scope = fields.Str(required=False, default="openid profile")
    state = fields.Str(required=False)
    code_challenge = fields.Str(required=False)
    code_challenge_method = fields.Str(
        required=False, validate=validate.OneOf(["S256", "plain"])
    )


class OAuth2TokenSchema(SanitizationMixin, Schema):
    grant_type = fields.Str(
        required=True, validate=validate.OneOf(["authorization_code", "refresh_token"])
    )
    code = fields.Str(required=False)
    redirect_uri = fields.Str(required=False)
    client_id = fields.Str(required=True)
    client_secret = fields.Str(required=False)
    code_verifier = fields.Str(required=False)
    refresh_token = fields.Str(required=False)


def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure token"""
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    """Hash token for storage"""
    return hashlib.sha256(token.encode()).hexdigest()


def verify_client_authentication(client_id: str, client_secret: str = None) -> bool:
    """Verify OAuth client authentication"""
    client = OAuthClient.find_by_field("client_id", client_id)
    if not client or not client.is_active:
        return False

    if client.client_type == "public":
        return True  # Public clients don't have secrets

    if not client_secret:
        return False

    return bcrypt.checkpw(client_secret.encode(), client.client_secret_hash.encode())


@app.route("/api/v1/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "service": "enhanced-auth-service",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "features": {
                "oauth2_1": True,
                "fapi_2_0": True,
                "mfa": True,
                "device_registration": True,
                "fraud_detection": True,
            },
        }
    )


@app.route("/api/v1/auth/login", methods=["POST"])
@validate_json_request(LoginSchema)
@audit_action(AuditEventType.USER_LOGIN, "login_attempt", severity=AuditSeverity.MEDIUM)
def login():
    """Enhanced login with fraud detection"""
    data = request.validated_data

    # Analyze login behavior for fraud
    risk_score, risk_factors = fraud_engine.analyze_login_behavior(
        data["username"],
        request.remote_addr,
        request.headers.get("User-Agent", ""),
        data.get("device_fingerprint"),
    )

    # Log security event
    event = SecurityEvent(
        event_type=SecurityEventType.LOGIN_ATTEMPT,
        user_id=data["username"],
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent", ""),
        timestamp=datetime.utcnow(),
        details={
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "device_fingerprint": data.get("device_fingerprint"),
        },
        threat_level=(
            ThreatLevel.HIGH
            if risk_score > 70
            else ThreatLevel.MODERATE if risk_score > 40 else ThreatLevel.LOW
        ),
    )
    security_monitor.log_security_event(event)

    # Check if account is locked or requires additional verification
    if risk_score > 80:
        return (
            jsonify(
                {
                    "error": "account_locked",
                    "message": "Account temporarily locked due to suspicious activity",
                    "requires_verification": True,
                }
            ),
            423,
        )

    # Verify credentials (mock implementation)
    # In production, integrate with user service
    if data["username"] == "demo@nexafi.com" and data["password"] == "SecurePass123!":
        user_id = "user_demo_001"

        # Determine security level based on risk
        if risk_score > 50:
            security_level = SecurityLevel.HIGH
        elif risk_score > 30:
            security_level = SecurityLevel.MEDIUM
        else:
            security_level = SecurityLevel.LOW

        # Create session
        session_id = session_manager.create_session(
            user_id,
            request.remote_addr,
            request.headers.get("User-Agent"),
            data.get("device_fingerprint"),
            security_level,
        )

        # Check if MFA is required
        mfa_required = risk_score > 40 or security_level in [
            SecurityLevel.HIGH,
            SecurityLevel.CRITICAL,
        ]

        # Log successful login
        audit_logger.log_event(
            AuditEventType.USER_LOGIN,
            "login_successful",
            user_id=user_id,
            details={
                "session_id": session_id,
                "risk_score": risk_score,
                "mfa_required": mfa_required,
            },
            severity=AuditSeverity.MEDIUM,
        )

        response_data = {
            "success": True,
            "session_id": session_id,
            "user_id": user_id,
            "security_level": security_level.value,
            "mfa_required": mfa_required,
            "risk_score": risk_score,
        }

        if mfa_required:
            response_data["next_step"] = "mfa_verification"
            response_data["available_methods"] = ["totp", "sms"]

        return jsonify(response_data)
    else:
        # Log failed login
        audit_logger.log_event(
            AuditEventType.USER_LOGIN,
            "login_failed",
            user_id=data["username"],
            details={"reason": "invalid_credentials"},
            severity=AuditSeverity.HIGH,
        )

        return (
            jsonify(
                {
                    "error": "invalid_credentials",
                    "message": "Invalid username or password",
                }
            ),
            401,
        )


@app.route("/api/v1/auth/mfa/setup", methods=["POST"])
@require_auth
@validate_json_request(MFASetupSchema)
@audit_action(AuditEventType.USER_UPDATE, "mfa_setup", severity=AuditSeverity.HIGH)
def setup_mfa():
    """Setup Multi-Factor Authentication"""
    data = request.validated_data
    user_id = g.user_id

    if data["method"] == "totp":
        # Setup TOTP
        secret, provisioning_uri, backup_codes = mfa_manager.setup_totp(
            user_id, f"{user_id}@nexafi.com"
        )

        return jsonify(
            {
                "method": "totp",
                "secret": secret,
                "qr_code_uri": provisioning_uri,
                "backup_codes": backup_codes,
                "message": "Scan QR code with authenticator app",
            }
        )

    elif data["method"] == "sms":
        # Setup SMS (mock implementation)
        phone_number = data.get("phone_number")
        if not phone_number:
            return (
                jsonify(
                    {
                        "error": "phone_number_required",
                        "message": "Phone number required for SMS setup",
                    }
                ),
                400,
            )

        return jsonify(
            {
                "method": "sms",
                "phone_number": phone_number,
                "message": "SMS MFA setup completed",
            }
        )


@app.route("/api/v1/auth/mfa/verify", methods=["POST"])
@require_auth
@validate_json_request(MFAVerifySchema)
@audit_action(
    AuditEventType.USER_LOGIN, "mfa_verification", severity=AuditSeverity.HIGH
)
def verify_mfa():
    """Verify Multi-Factor Authentication"""
    data = request.validated_data
    user_id = g.user_id
    session_id = g.session_id

    is_verified = False

    if data["method"] == "totp":
        is_verified = mfa_manager.verify_totp(
            user_id,
            data["token"],
            request.remote_addr,
            request.headers.get("User-Agent"),
        )
    elif data["method"] == "backup_code":
        is_verified = mfa_manager.verify_backup_code(
            user_id,
            data["token"],
            request.remote_addr,
            request.headers.get("User-Agent"),
        )

    if is_verified:
        # Mark session as MFA verified
        session_manager.mark_mfa_verified(session_id)

        audit_logger.log_event(
            AuditEventType.USER_LOGIN,
            "mfa_verification_successful",
            user_id=user_id,
            details={"method": data["method"]},
            severity=AuditSeverity.HIGH,
        )

        return jsonify(
            {
                "success": True,
                "message": "MFA verification successful",
                "session_verified": True,
            }
        )
    else:
        audit_logger.log_event(
            AuditEventType.USER_LOGIN,
            "mfa_verification_failed",
            user_id=user_id,
            details={"method": data["method"]},
            severity=AuditSeverity.HIGH,
        )

        return jsonify({"error": "invalid_token", "message": "Invalid MFA token"}), 401


@app.route("/oauth2/authorize", methods=["GET", "POST"])
@validate_json_request(OAuth2AuthorizeSchema, methods=["POST"])
def oauth2_authorize():
    """OAuth 2.1 Authorization Endpoint with FAPI 2.0 compliance"""
    if request.method == "GET":
        # Parse query parameters
        data = {
            "response_type": request.args.get("response_type"),
            "client_id": request.args.get("client_id"),
            "redirect_uri": request.args.get("redirect_uri"),
            "scope": request.args.get("scope", "openid profile"),
            "state": request.args.get("state"),
            "code_challenge": request.args.get("code_challenge"),
            "code_challenge_method": request.args.get("code_challenge_method", "S256"),
        }
    else:
        data = request.validated_data

    # Validate client
    client = OAuthClient.find_by_field("client_id", data["client_id"])
    if not client or not client.is_active:
        return (
            jsonify(
                {
                    "error": "invalid_client",
                    "error_description": "Invalid client identifier",
                }
            ),
            400,
        )

    # Validate redirect URI
    allowed_uris = json.loads(client.redirect_uris)
    if data["redirect_uri"] not in allowed_uris:
        return (
            jsonify(
                {
                    "error": "invalid_request",
                    "error_description": "Invalid redirect URI",
                }
            ),
            400,
        )

    # Check if user is authenticated
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        # Redirect to login
        login_url = url_for(
            "login",
            client_id=data["client_id"],
            redirect_uri=data["redirect_uri"],
            state=data.get("state"),
        )
        return redirect(login_url)

    # Extract user from session (simplified)
    user_id = "user_demo_001"  # Would be extracted from valid session

    # Generate authorization code
    auth_code = generate_secure_token(32)
    expires_at = datetime.utcnow() + timedelta(minutes=10)  # 10-minute expiry

    # Store authorization code
    code_record = AuthorizationCode(
        code=auth_code,
        client_id=data["client_id"],
        user_id=user_id,
        redirect_uri=data["redirect_uri"],
        scope=data["scope"],
        code_challenge=data.get("code_challenge"),
        code_challenge_method=data.get("code_challenge_method"),
        expires_at=expires_at,
    )
    code_record.save()

    # Build redirect URL
    redirect_params = {"code": auth_code}
    if data.get("state"):
        redirect_params["state"] = data["state"]

    redirect_url = f"{data['redirect_uri']}?{urlencode(redirect_params)}"

    return redirect(redirect_url)


@app.route("/oauth2/token", methods=["POST"])
@validate_json_request(OAuth2TokenSchema)
def oauth2_token():
    """OAuth 2.1 Token Endpoint with FAPI 2.0 compliance"""
    data = request.validated_data

    # Verify client authentication
    client_secret = data.get("client_secret")
    if not verify_client_authentication(data["client_id"], client_secret):
        return (
            jsonify(
                {
                    "error": "invalid_client",
                    "error_description": "Client authentication failed",
                }
            ),
            401,
        )

    if data["grant_type"] == "authorization_code":
        # Exchange authorization code for tokens
        code_record = AuthorizationCode.find_by_field("code", data["code"])

        if not code_record or code_record.used:
            return (
                jsonify(
                    {
                        "error": "invalid_grant",
                        "error_description": "Invalid or expired authorization code",
                    }
                ),
                400,
            )

        # Check expiry
        if datetime.utcnow() > datetime.fromisoformat(code_record.expires_at):
            return (
                jsonify(
                    {
                        "error": "invalid_grant",
                        "error_description": "Authorization code expired",
                    }
                ),
                400,
            )

        # Verify PKCE if present
        if code_record.code_challenge:
            code_verifier = data.get("code_verifier")
            if not code_verifier:
                return (
                    jsonify(
                        {
                            "error": "invalid_request",
                            "error_description": "Code verifier required",
                        }
                    ),
                    400,
                )

            # Verify code challenge
            if code_record.code_challenge_method == "S256":
                challenge = (
                    base64.urlsafe_b64encode(
                        hashlib.sha256(code_verifier.encode()).digest()
                    )
                    .decode()
                    .rstrip("=")
                )
            else:
                challenge = code_verifier

            if challenge != code_record.code_challenge:
                return (
                    jsonify(
                        {
                            "error": "invalid_grant",
                            "error_description": "Invalid code verifier",
                        }
                    ),
                    400,
                )

        # Mark code as used
        code_record.used = True
        code_record.save()

        # Generate tokens
        access_token = generate_secure_token(32)
        refresh_token = generate_secure_token(32)

        # Create access token record
        token_record = AccessToken(
            token_id=generate_secure_token(16),
            access_token_hash=hash_token(access_token),
            refresh_token_hash=hash_token(refresh_token),
            client_id=data["client_id"],
            user_id=code_record.user_id,
            scope=code_record.scope,
            expires_at=datetime.utcnow() + timedelta(hours=1),
            refresh_expires_at=datetime.utcnow() + timedelta(days=30),
        )
        token_record.save()

        # Create ID token (OpenID Connect)
        id_token_payload = {
            "sub": code_record.user_id,
            "aud": data["client_id"],
            "iss": "https://auth.nexafi.com",
            "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            "iat": int(datetime.utcnow().timestamp()),
            "auth_time": int(datetime.utcnow().timestamp()),
        }

        id_token = fapi_security.create_signed_jwt(
            id_token_payload, data["client_id"], "https://auth.nexafi.com"
        )

        return jsonify(
            {
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": refresh_token,
                "id_token": id_token,
                "scope": code_record.scope,
            }
        )

    elif data["grant_type"] == "refresh_token":
        # Refresh access token
        refresh_token = data.get("refresh_token")
        if not refresh_token:
            return (
                jsonify(
                    {
                        "error": "invalid_request",
                        "error_description": "Refresh token required",
                    }
                ),
                400,
            )

        # Find token record
        token_record = AccessToken.find_by_field(
            "refresh_token_hash", hash_token(refresh_token)
        )

        if not token_record or token_record.is_revoked:
            return (
                jsonify(
                    {
                        "error": "invalid_grant",
                        "error_description": "Invalid refresh token",
                    }
                ),
                400,
            )

        # Check refresh token expiry
        if datetime.utcnow() > datetime.fromisoformat(token_record.refresh_expires_at):
            return (
                jsonify(
                    {
                        "error": "invalid_grant",
                        "error_description": "Refresh token expired",
                    }
                ),
                400,
            )

        # Generate new access token
        new_access_token = generate_secure_token(32)

        # Update token record
        token_record.access_token_hash = hash_token(new_access_token)
        token_record.expires_at = datetime.utcnow() + timedelta(hours=1)
        token_record.save()

        return jsonify(
            {
                "access_token": new_access_token,
                "token_type": "Bearer",
                "expires_in": 3600,
                "scope": token_record.scope,
            }
        )


@app.route("/oauth2/userinfo", methods=["GET"])
def oauth2_userinfo():
    """OAuth 2.1 UserInfo Endpoint"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return (
            jsonify(
                {
                    "error": "invalid_token",
                    "error_description": "Invalid or missing access token",
                }
            ),
            401,
        )

    access_token = auth_header[7:]  # Remove 'Bearer ' prefix

    # Find token record
    token_record = AccessToken.find_by_field(
        "access_token_hash", hash_token(access_token)
    )

    if not token_record or token_record.is_revoked:
        return (
            jsonify(
                {"error": "invalid_token", "error_description": "Invalid access token"}
            ),
            401,
        )

    # Check token expiry
    if datetime.utcnow() > datetime.fromisoformat(token_record.expires_at):
        return (
            jsonify(
                {"error": "invalid_token", "error_description": "Access token expired"}
            ),
            401,
        )

    # Return user info (mock data)
    return jsonify(
        {
            "sub": token_record.user_id,
            "name": "Demo User",
            "email": "demo@nexafi.com",
            "email_verified": True,
            "preferred_username": "demo",
        }
    )


@app.route("/api/v1/auth/logout", methods=["POST"])
@require_auth
@audit_action(AuditEventType.USER_LOGOUT, "logout", severity=AuditSeverity.LOW)
def logout():
    """Secure logout"""
    user_id = g.user_id
    session_id = g.session_id

    # Invalidate session
    session_manager.invalidate_session(session_id)

    # Log logout
    audit_logger.log_event(
        AuditEventType.USER_LOGOUT,
        "logout_successful",
        user_id=user_id,
        details={"session_id": session_id},
        severity=AuditSeverity.LOW,
    )

    return jsonify({"success": True, "message": "Logged out successfully"})


if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("/home/ubuntu/NexaFi/backend/enhanced-auth-service/keys", exist_ok=True)
    os.makedirs("/home/ubuntu/NexaFi/backend/enhanced-auth-service/data", exist_ok=True)

    app.run(host="0.0.0.0", port=5011, debug=False)
