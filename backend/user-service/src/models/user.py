from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import json
import secrets
import pyotp

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    email_verified_at = db.Column(db.DateTime)
    last_login = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    
    # MFA fields
    mfa_enabled = db.Column(db.Boolean, default=False)
    mfa_secret = db.Column(db.String(32))  # TOTP secret
    backup_codes = db.Column(db.Text)  # JSON array of backup codes
    
    # Subscription and business info
    subscription_tier = db.Column(db.String(50), default='free')  # free, basic, premium, enterprise
    business_type = db.Column(db.String(100))
    company_size = db.Column(db.String(50))
    industry = db.Column(db.String(100))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    roles = db.relationship('UserRole', backref='user', cascade='all, delete-orphan')
    sessions = db.relationship('UserSession', backref='user', cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='user', cascade='all, delete-orphan')
    custom_fields = db.relationship('UserCustomField', backref='user', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_locked(self):
        return self.locked_until and self.locked_until > datetime.utcnow()
    
    def lock_account(self, duration_minutes=30):
        self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self.failed_login_attempts = 0
    
    def unlock_account(self):
        self.locked_until = None
        self.failed_login_attempts = 0
    
    def increment_failed_login(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.lock_account()
    
    def setup_mfa(self):
        """Generate MFA secret and backup codes"""
        self.mfa_secret = pyotp.random_base32()
        backup_codes = [secrets.token_hex(4) for _ in range(10)]
        self.backup_codes = json.dumps(backup_codes)
        return self.mfa_secret, backup_codes
    
    def verify_mfa_token(self, token):
        """Verify TOTP token or backup code"""
        if not self.mfa_enabled or not self.mfa_secret:
            return False
        
        # Check TOTP token
        totp = pyotp.TOTP(self.mfa_secret)
        if totp.verify(token, valid_window=1):
            return True
        
        # Check backup codes
        if self.backup_codes:
            backup_codes = json.loads(self.backup_codes)
            if token in backup_codes:
                backup_codes.remove(token)
                self.backup_codes = json.dumps(backup_codes)
                return True
        
        return False
    
    def get_mfa_qr_code_url(self, issuer_name="NexaFi"):
        """Get QR code URL for MFA setup"""
        if not self.mfa_secret:
            return None
        
        totp = pyotp.TOTP(self.mfa_secret)
        return totp.provisioning_uri(
            name=self.email,
            issuer_name=issuer_name
        )
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        for role in self.roles:
            if role.role.has_permission(permission):
                return True
        return False
    
    def get_permissions(self):
        """Get all permissions for user"""
        permissions = set()
        for user_role in self.roles:
            permissions.update(user_role.role.get_permissions())
        return list(permissions)
    
    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'email_verified_at': self.email_verified_at.isoformat() if self.email_verified_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'subscription_tier': self.subscription_tier,
            'business_type': self.business_type,
            'company_size': self.company_size,
            'industry': self.industry,
            'mfa_enabled': self.mfa_enabled,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_sensitive:
            data.update({
                'failed_login_attempts': self.failed_login_attempts,
                'is_locked': self.is_locked(),
                'locked_until': self.locked_until.isoformat() if self.locked_until else None
            })
        
        return data

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Extended profile information
    avatar_url = db.Column(db.String(500))
    bio = db.Column(db.Text)
    timezone = db.Column(db.String(50), default='UTC')
    language = db.Column(db.String(10), default='en')
    currency_preference = db.Column(db.String(3), default='USD')
    date_format = db.Column(db.String(20), default='YYYY-MM-DD')
    
    # Business information
    company_name = db.Column(db.String(200))
    company_address = db.Column(db.Text)
    company_website = db.Column(db.String(200))
    tax_id = db.Column(db.String(50))
    business_registration_number = db.Column(db.String(50))
    
    # Financial preferences
    fiscal_year_start = db.Column(db.String(5), default='01-01')  # MM-DD format
    accounting_method = db.Column(db.String(20), default='accrual')  # accrual, cash
    default_payment_terms = db.Column(db.Integer, default=30)  # days
    
    # Notification preferences
    email_notifications = db.Column(db.Boolean, default=True)
    sms_notifications = db.Column(db.Boolean, default=False)
    push_notifications = db.Column(db.Boolean, default=True)
    marketing_emails = db.Column(db.Boolean, default=False)
    
    # Security preferences
    session_timeout = db.Column(db.Integer, default=480)  # minutes
    require_mfa_for_sensitive_actions = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'avatar_url': self.avatar_url,
            'bio': self.bio,
            'timezone': self.timezone,
            'language': self.language,
            'currency_preference': self.currency_preference,
            'date_format': self.date_format,
            'company_name': self.company_name,
            'company_address': self.company_address,
            'company_website': self.company_website,
            'tax_id': self.tax_id,
            'business_registration_number': self.business_registration_number,
            'fiscal_year_start': self.fiscal_year_start,
            'accounting_method': self.accounting_method,
            'default_payment_terms': self.default_payment_terms,
            'email_notifications': self.email_notifications,
            'sms_notifications': self.sms_notifications,
            'push_notifications': self.push_notifications,
            'marketing_emails': self.marketing_emails,
            'session_timeout': self.session_timeout,
            'require_mfa_for_sensitive_actions': self.require_mfa_for_sensitive_actions,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_system_role = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    permissions = db.relationship('RolePermission', backref='role', cascade='all, delete-orphan')
    users = db.relationship('UserRole', backref='role', cascade='all, delete-orphan')
    
    def has_permission(self, permission_name):
        """Check if role has specific permission"""
        for role_perm in self.permissions:
            if role_perm.permission.name == permission_name:
                return True
        return False
    
    def get_permissions(self):
        """Get all permission names for this role"""
        return [rp.permission.name for rp in self.permissions]
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'is_system_role': self.is_system_role,
            'is_active': self.is_active,
            'permissions': self.get_permissions(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Permission(db.Model):
    __tablename__ = 'permissions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    resource = db.Column(db.String(50))  # e.g., 'users', 'accounts', 'transactions'
    action = db.Column(db.String(50))    # e.g., 'create', 'read', 'update', 'delete'
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    roles = db.relationship('RolePermission', backref='permission', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'resource': self.resource,
            'action': self.action,
            'created_at': self.created_at.isoformat()
        }

class UserRole(db.Model):
    __tablename__ = 'user_roles'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    role_id = db.Column(db.String(36), db.ForeignKey('roles.id'), nullable=False)
    granted_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)  # Optional expiration
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    granted_by_user = db.relationship('User', foreign_keys=[granted_by])
    
    def is_expired(self):
        return self.expires_at and self.expires_at < datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'role_id': self.role_id,
            'role_name': self.role.name,
            'role_display_name': self.role.display_name,
            'granted_by': self.granted_by,
            'granted_at': self.granted_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'is_expired': self.is_expired()
        }

class RolePermission(db.Model):
    __tablename__ = 'role_permissions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    role_id = db.Column(db.String(36), db.ForeignKey('roles.id'), nullable=False)
    permission_id = db.Column(db.String(36), db.ForeignKey('permissions.id'), nullable=False)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('role_id', 'permission_id'),)

class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    session_token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    refresh_token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    # Session metadata
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    device_fingerprint = db.Column(db.String(255))
    location = db.Column(db.String(100))
    
    # Session status
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    def extend_session(self, hours=24):
        """Extend session expiration"""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self.last_activity = datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'location': self.location,
            'is_active': self.is_active,
            'expires_at': self.expires_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'created_at': self.created_at.isoformat(),
            'is_expired': self.is_expired()
        }

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    
    # Action details
    action = db.Column(db.String(100), nullable=False)  # e.g., 'login', 'create_account', 'update_profile'
    resource_type = db.Column(db.String(50))  # e.g., 'user', 'account', 'transaction'
    resource_id = db.Column(db.String(36))
    
    # Request details
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    request_method = db.Column(db.String(10))
    request_path = db.Column(db.String(500))
    
    # Change details
    old_values = db.Column(db.Text)  # JSON
    new_values = db.Column(db.Text)  # JSON
    
    # Status and metadata
    status = db.Column(db.String(20), default='success')  # success, failure, error
    error_message = db.Column(db.Text)
    severity = db.Column(db.String(20), default='info')  # info, warning, error, critical
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'request_method': self.request_method,
            'request_path': self.request_path,
            'old_values': json.loads(self.old_values) if self.old_values else None,
            'new_values': json.loads(self.new_values) if self.new_values else None,
            'status': self.status,
            'error_message': self.error_message,
            'severity': self.severity,
            'created_at': self.created_at.isoformat()
        }

class UserCustomField(db.Model):
    __tablename__ = 'user_custom_fields'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    field_name = db.Column(db.String(100), nullable=False)
    field_value = db.Column(db.Text)
    field_type = db.Column(db.String(20), default='text')  # text, number, boolean, date, json
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'field_name'),)
    
    def get_typed_value(self):
        """Return value in appropriate type"""
        if self.field_type == 'number':
            try:
                return float(self.field_value)
            except (ValueError, TypeError):
                return None
        elif self.field_type == 'boolean':
            return self.field_value.lower() in ('true', '1', 'yes', 'on')
        elif self.field_type == 'json':
            try:
                return json.loads(self.field_value)
            except (ValueError, TypeError):
                return None
        elif self.field_type == 'date':
            try:
                return datetime.fromisoformat(self.field_value)
            except (ValueError, TypeError):
                return None
        else:
            return self.field_value
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'field_name': self.field_name,
            'field_value': self.get_typed_value(),
            'field_type': self.field_type,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class PasswordReset(db.Model):
    __tablename__ = 'password_resets'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime)
    ip_address = db.Column(db.String(45))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='password_resets')
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    def is_used(self):
        return self.used_at is not None
    
    def is_valid(self):
        return not self.is_expired() and not self.is_used()
    
    def mark_as_used(self):
        self.used_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'expires_at': self.expires_at.isoformat(),
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat(),
            'is_expired': self.is_expired(),
            'is_used': self.is_used(),
            'is_valid': self.is_valid()
        }

class EmailVerification(db.Model):
    __tablename__ = 'email_verifications'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    verified_at = db.Column(db.DateTime)
    ip_address = db.Column(db.String(45))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='email_verifications')
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    def is_verified(self):
        return self.verified_at is not None
    
    def is_valid(self):
        return not self.is_expired() and not self.is_verified()
    
    def mark_as_verified(self):
        self.verified_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email': self.email,
            'expires_at': self.expires_at.isoformat(),
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat(),
            'is_expired': self.is_expired(),
            'is_verified': self.is_verified(),
            'is_valid': self.is_valid()
        }

