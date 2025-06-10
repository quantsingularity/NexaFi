from flask import Blueprint, jsonify, request, current_app
from src.models.user import User, UserProfile, UserSession, UserActivity, db
from werkzeug.security import generate_password_hash
import jwt
from datetime import datetime, timedelta
import uuid
import re
from functools import wraps

user_bp = Blueprint('user', __name__)

# JWT Configuration
JWT_SECRET_KEY = 'nexafi-secret-key-2024'
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    return True, "Password is valid"

def create_access_token(user_id):
    """Create JWT access token"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id):
    """Create JWT refresh token"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        'iat': datetime.utcnow(),
        'type': 'refresh'
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid authorization header format'}), 401
        
        if not token:
            return jsonify({'error': 'Authentication token is missing'}), 401
        
        payload = verify_token(token)
        if not payload or payload.get('type') != 'access':
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Get user from database
        user = User.query.get(payload['user_id'])
        if not user or user.status != 'active':
            return jsonify({'error': 'User not found or inactive'}), 401
        
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function

def log_user_activity(user_id, activity_type, description, metadata=None):
    """Log user activity"""
    activity = UserActivity(
        user_id=user_id,
        activity_type=activity_type,
        description=description,
        metadata=metadata,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(activity)
    db.session.commit()

# Authentication Routes
@user_bp.route('/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate email format
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password strength
        is_valid, message = validate_password(data['password'])
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({'error': 'User with this email already exists'}), 409
        
        # Create new user
        user = User(
            email=data['email'].lower().strip(),
            first_name=data['first_name'].strip(),
            last_name=data['last_name'].strip(),
            phone=data.get('phone', '').strip() if data.get('phone') else None,
            role=data.get('role', 'business_owner')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Create user profile
        profile = UserProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
        
        # Log activity
        log_user_activity(user.id, 'user_registered', 'User account created')
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed', 'details': str(e)}), 500

@user_bp.route('/auth/login', methods=['POST'])
def login():
    """Authenticate user and return tokens"""
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user by email
        user = User.query.filter_by(email=data['email'].lower().strip()).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        if user.status != 'active':
            return jsonify({'error': 'Account is not active'}), 401
        
        # Create tokens
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        
        # Create session record
        session = UserSession(
            user_id=user.id,
            token_hash=generate_password_hash(access_token),
            refresh_token_hash=generate_password_hash(refresh_token),
            expires_at=datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            refresh_expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            user_agent=request.headers.get('User-Agent'),
            ip_address=request.remote_addr
        )
        
        db.session.add(session)
        db.session.commit()
        
        # Log activity
        log_user_activity(user.id, 'user_login', 'User logged in successfully')
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Login failed', 'details': str(e)}), 500

@user_bp.route('/auth/refresh', methods=['POST'])
def refresh_token():
    """Refresh access token using refresh token"""
    try:
        data = request.get_json()
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({'error': 'Refresh token is required'}), 400
        
        # Verify refresh token
        payload = verify_token(refresh_token)
        if not payload or payload.get('type') != 'refresh':
            return jsonify({'error': 'Invalid or expired refresh token'}), 401
        
        # Get user
        user = User.query.get(payload['user_id'])
        if not user or user.status != 'active':
            return jsonify({'error': 'User not found or inactive'}), 401
        
        # Create new access token
        new_access_token = create_access_token(user.id)
        
        return jsonify({
            'access_token': new_access_token,
            'token_type': 'Bearer',
            'expires_in': ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Token refresh failed', 'details': str(e)}), 500

@user_bp.route('/auth/logout', methods=['POST'])
@require_auth
def logout():
    """Logout user and invalidate session"""
    try:
        user = request.current_user
        
        # Invalidate all user sessions
        UserSession.query.filter_by(user_id=user.id, is_active=True).update({'is_active': False})
        db.session.commit()
        
        # Log activity
        log_user_activity(user.id, 'user_logout', 'User logged out')
        
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Logout failed', 'details': str(e)}), 500

# User Management Routes
@user_bp.route('/users/profile', methods=['GET'])
@require_auth
def get_user_profile():
    """Get current user profile"""
    try:
        user = request.current_user
        profile = UserProfile.query.filter_by(user_id=user.id).first()
        
        return jsonify({
            'user': user.to_dict(),
            'profile': profile.to_dict() if profile else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get profile', 'details': str(e)}), 500

@user_bp.route('/users/profile', methods=['PUT'])
@require_auth
def update_user_profile():
    """Update current user profile"""
    try:
        user = request.current_user
        data = request.get_json()
        
        # Update user basic info
        if 'first_name' in data:
            user.first_name = data['first_name'].strip()
        if 'last_name' in data:
            user.last_name = data['last_name'].strip()
        if 'phone' in data:
            user.phone = data['phone'].strip() if data['phone'] else None
        
        user.updated_at = datetime.utcnow()
        
        # Update or create profile
        profile = UserProfile.query.filter_by(user_id=user.id).first()
        if not profile:
            profile = UserProfile(user_id=user.id)
            db.session.add(profile)
        
        # Update profile fields
        profile_fields = [
            'business_name', 'business_type', 'industry', 'tax_id',
            'address', 'preferences', 'annual_revenue', 'employee_count',
            'business_description', 'website'
        ]
        
        for field in profile_fields:
            if field in data:
                setattr(profile, field, data[field])
        
        profile.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Log activity
        log_user_activity(user.id, 'profile_updated', 'User profile updated')
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict(),
            'profile': profile.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update profile', 'details': str(e)}), 500

@user_bp.route('/users/change-password', methods=['POST'])
@require_auth
def change_password():
    """Change user password"""
    try:
        user = request.current_user
        data = request.get_json()
        
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        # Verify current password
        if not user.check_password(data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Validate new password
        is_valid, message = validate_password(data['new_password'])
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Update password
        user.set_password(data['new_password'])
        user.updated_at = datetime.utcnow()
        
        # Invalidate all sessions except current
        UserSession.query.filter_by(user_id=user.id, is_active=True).update({'is_active': False})
        
        db.session.commit()
        
        # Log activity
        log_user_activity(user.id, 'password_changed', 'User password changed')
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to change password', 'details': str(e)}), 500

@user_bp.route('/users/activity', methods=['GET'])
@require_auth
def get_user_activity():
    """Get user activity log"""
    try:
        user = request.current_user
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        activities = UserActivity.query.filter_by(user_id=user.id)\
            .order_by(UserActivity.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'activities': [activity.to_dict() for activity in activities.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': activities.total,
                'pages': activities.pages,
                'has_next': activities.has_next,
                'has_prev': activities.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get activity', 'details': str(e)}), 500

# Admin Routes (for testing and management)
@user_bp.route('/users', methods=['GET'])
def get_users():
    """Get all users (admin only)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        users = User.query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': users.total,
                'pages': users.pages,
                'has_next': users.has_next,
                'has_prev': users.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get users', 'details': str(e)}), 500

@user_bp.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get specific user by ID"""
    try:
        user = User.query.get_or_404(user_id)
        profile = UserProfile.query.filter_by(user_id=user.id).first()
        
        return jsonify({
            'user': user.to_dict(),
            'profile': profile.to_dict() if profile else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get user', 'details': str(e)}), 500

# Health check
@user_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'user-service',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

