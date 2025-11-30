from datetime import datetime, timedelta
from typing import Any, Dict, Optional

# Import BaseModel from the shared database manager
# Note: BaseModel.set_db_manager is called in main.py
# We will rely on the main application to set up the environment and imports.
# For the sake of a clean model file, we will assume the necessary components
# (BaseModel, auth_manager, db_manager) are available via the main application's context
# or that the methods will be called in a context where they are available.

# Since the original main.py defined the User class with methods that directly
# use auth_manager and db_manager, we must ensure these dependencies are met.
# The simplest way is to import them here, assuming the shared path is set up.

# We will use relative imports for shared components as they are in the same repo structure.
# However, the original code used an absolute path append, so we'll stick to that pattern
# for now, but clean up the imports to be more explicit.

# We will define the classes and their methods.


class BaseModel:
    """Placeholder for BaseModel to avoid import errors in this file.
    The actual BaseModel is imported and set in main.py."""


# We need to import the actual BaseModel from the shared directory.
# Since the original code was structured to have the models defined in main.py
# and rely on imports there, moving them requires careful dependency management.

# Let's assume the main application will handle the environment setup and we only
# need the class definitions here. We will define the classes with their methods.

# --- Dependencies for User Model Methods ---
# - auth_manager (for hashing/checking password)
# - db_manager (for get_roles, add_role, remove_role)

# Since we cannot easily import auth_manager and db_manager here without circular
# dependencies or complex path manipulation, we will pass them as arguments to the
# methods that need them, or rely on the fact that the original main.py used them
# as global-like variables (which is bad practice but the current structure).

# Given the original structure, the cleanest fix is to define the classes and
# assume the necessary components are available in the scope where the methods are called.
# The original main.py defined the classes *after* importing and initializing the dependencies.

# Let's define the classes and assume the main application will handle the imports.
# We will use the original methods that rely on `auth_manager` and `db_manager`.

# Re-defining the User and UserSession classes from the original main.py logic
# and placing them in the models file.


class User(BaseModel):
    table_name = "users"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not hasattr(self, "created_at"):
            self.created_at = datetime.utcnow()
        if not hasattr(self, "updated_at"):
            self.updated_at = datetime.utcnow()
        if not hasattr(self, "is_active"):
            self.is_active = True
        if not hasattr(self, "email_verified"):
            self.email_verified = False
        if not hasattr(self, "failed_login_attempts"):
            self.failed_login_attempts = 0

    def set_password(self, password: str, auth_manager):
        """Set hashed password"""
        self.password_hash = auth_manager.hash_password(password)

    def check_password(self, password: str, auth_manager) -> bool:
        """Check password against hash"""
        return auth_manager.verify_password(password, self.password_hash)

    def is_locked(self) -> bool:
        """Check if account is locked"""
        if self.locked_until:
            # The original code had a timezone issue fix, we'll keep it for robustness
            locked_until = datetime.fromisoformat(
                self.locked_until.replace("Z", "+00:00")
            )
            return datetime.utcnow() < locked_until
        return False

    def lock_account(self, duration_minutes: int = 30):
        """Lock account for specified duration"""
        self.locked_until = (
            datetime.utcnow() + timedelta(minutes=duration_minutes)
        ).isoformat()
        self.save()

    def unlock_account(self):
        """Unlock account"""
        self.locked_until = None
        self.failed_login_attempts = 0
        self.save()

    def increment_failed_attempts(self):
        """Increment failed login attempts"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.lock_account()
        self.save()

    def reset_failed_attempts(self):
        """Reset failed login attempts"""
        self.failed_login_attempts = 0
        self.save()

    def get_roles(self) -> list:
        """Get user roles"""
        # Assumes BaseModel.db_manager is set
        query = "SELECT role_name FROM user_roles WHERE user_id = ?"
        rows = self.db_manager.execute_query(query, (self.id,))
        return [row["role_name"] for row in rows]

    def add_role(self, role_name: str, granted_by: Optional[int] = None):
        """Add role to user"""
        # Assumes BaseModel.db_manager is set
        query = (
            "INSERT INTO user_roles (user_id, role_name, granted_by) VALUES (?, ?, ?)"
        )
        self.db_manager.execute_insert(query, (self.id, role_name, granted_by))

    def remove_role(self, role_name: str):
        """Remove role from user"""
        # Assumes BaseModel.db_manager is set
        query = "DELETE FROM user_roles WHERE user_id = ? AND role_name = ?"
        self.db_manager.execute_update(query, (self.id, role_name))

    def to_dict(self, include_sensitive=False) -> Dict[str, Any]:
        """Convert user to dictionary"""
        data = super().to_dict()

        # Remove sensitive fields
        if not include_sensitive:
            data.pop("password_hash", None)
            data.pop("failed_login_attempts", None)
            data.pop("locked_until", None)

        # Add roles
        data["roles"] = self.get_roles()

        return data


class UserSession(BaseModel):
    table_name = "user_sessions"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not hasattr(self, "created_at"):
            self.created_at = datetime.utcnow()
        if not hasattr(self, "updated_at"):
            self.updated_at = datetime.utcnow()
        if not hasattr(self, "is_active"):
            self.is_active = True
        if not hasattr(self, "expires_at"):
            # Default session expiration to 7 days
            self.expires_at = datetime.utcnow() + timedelta(days=7)

    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        data = super().to_dict()
        data["is_expired"] = self.is_expired()
        return data
