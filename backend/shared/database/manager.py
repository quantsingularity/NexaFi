"""
Database utilities and connection management for NexaFi
Implements connection pooling, transaction management, and database migrations
"""

import os
import sqlite3
import threading
from contextlib import contextmanager
from typing import Any, Dict, List, Tuple

from core.logging import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """Database connection and transaction manager"""

    def __init__(self, db_path: str, pool_size: int = 10):
        self.db_path = db_path
        self.pool_size = pool_size
        self.connections = []
        self.lock = threading.Lock()

        # Ensure database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Initialize connection pool
        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize connection pool"""
        for _ in range(self.pool_size):
            conn = self._create_connection()
            self.connections.append(conn)

    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)

        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")

        # Set WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode = WAL")

        # Set row factory for dict-like access
        conn.row_factory = sqlite3.Row

        return conn

    @contextmanager
    def get_connection(self):
        """Get connection from pool"""
        conn = None
        try:
            with self.lock:
                if self.connections:
                    conn = self.connections.pop()
                else:
                    conn = self._create_connection()

            yield conn

        finally:
            if conn:
                with self.lock:
                    if len(self.connections) < self.pool_size:
                        self.connections.append(conn)
                    else:
                        conn.close()

    @contextmanager
    def transaction(self):
        """Database transaction context manager"""
        with self.get_connection() as conn:
            try:
                conn.execute("BEGIN")
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def execute_query(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """Execute SELECT query"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()

    def execute_update(self, query: str, params: Tuple = ()) -> int:
        """Execute INSERT/UPDATE/DELETE query"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount

    def execute_insert(self, query: str, params: Tuple = ()) -> int:
        """Execute INSERT query and return last row ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.lastrowid

    def close_all_connections(self):
        """Close all connections in pool"""
        with self.lock:
            for conn in self.connections:
                conn.close()
            self.connections.clear()


class MigrationManager:
    """Database migration management"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.migrations_table = "schema_migrations"
        self._ensure_migrations_table()

    def _ensure_migrations_table(self):
        """Create migrations tracking table"""
        query = f"""
        CREATE TABLE IF NOT EXISTS {self.migrations_table} (
            version TEXT PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        )
        """
        self.db_manager.execute_update(query)

    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions"""
        query = f"SELECT version FROM {self.migrations_table} ORDER BY version"
        rows = self.db_manager.execute_query(query)
        return [row["version"] for row in rows]

    def apply_migration(self, version: str, description: str, sql: str):
        """Apply a database migration"""
        applied_migrations = self.get_applied_migrations()

        if version in applied_migrations:
            logger.info(f"Migration {version} already applied")
            return

        logger.info(f"Applying migration {version}: {description}")
        with self.db_manager.transaction() as conn:
            # Execute migration SQL
            for statement in sql.split(";"):
                statement = statement.strip()
                if statement:
                    conn.execute(statement)

            # Record migration
            conn.execute(
                f"INSERT INTO {self.migrations_table} (version, description) VALUES (?, ?)",
                (version, description),
            )

        logger.info(f"Migration {version} applied successfully")

    def rollback_migration(self, version: str, rollback_sql: str):
        """Rollback a database migration"""
        applied_migrations = self.get_applied_migrations()

        if version not in applied_migrations:
            logger.info(f"Migration {version} not applied")
            return

        logger.info(f"Rolling back migration {version}")
        with self.db_manager.transaction() as conn:
            # Execute rollback SQL
            for statement in rollback_sql.split(";"):
                statement = statement.strip()
                if statement:
                    conn.execute(statement)

            # Remove migration record
            conn.execute(
                f"DELETE FROM {self.migrations_table} WHERE version = ?", (version,)
            )

        logger.info(f"Migration {version} rolled back successfully")


class BaseModel:
    """Base model class with common database operations"""

    table_name = None
    db_manager = None

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def set_db_manager(cls, db_manager: DatabaseManager):
        """Set database manager for all models"""
        cls.db_manager = db_manager

    @classmethod
    def find_by_id(cls, id_value: Any):
        """Find record by ID"""
        query = f"SELECT * FROM {cls.table_name} WHERE id = ?"
        rows = cls.db_manager.execute_query(query, (id_value,))
        if rows:
            return cls(**dict(rows[0]))
        return None

    @classmethod
    def find_all(cls, where_clause: str = "", params: Tuple = ()):
        """Find all records matching criteria"""
        query = f"SELECT * FROM {cls.table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"

        rows = cls.db_manager.execute_query(query, params)
        return [cls(**dict(row)) for row in rows]

    @classmethod
    def find_one(cls, where_clause: str, params: Tuple = ()):
        """Find one record matching criteria"""
        query = f"SELECT * FROM {cls.table_name} WHERE {where_clause} LIMIT 1"
        rows = cls.db_manager.execute_query(query, params)
        if rows:
            return cls(**dict(rows[0]))
        return None

    def save(self):
        """Save record to database"""
        if hasattr(self, "id") and self.id:
            return self._update()
        else:
            return self._insert()

    def _insert(self):
        """Insert new record"""
        fields = [k for k in self.__dict__.keys() if k != "id"]
        values = [getattr(self, k) for k in fields]

        placeholders = ", ".join(["?" for _ in fields])
        field_names = ", ".join(fields)

        query = f"INSERT INTO {self.table_name} ({field_names}) VALUES ({placeholders})"

        self.id = self.db_manager.execute_insert(query, tuple(values))
        return self

    def _update(self):
        """Update existing record"""
        fields = [k for k in self.__dict__.keys() if k != "id"]
        values = [getattr(self, k) for k in fields]

        set_clause = ", ".join([f"{field} = ?" for field in fields])
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?"

        values.append(self.id)
        self.db_manager.execute_update(query, tuple(values))
        return self

    def delete(self):
        """Delete record from database"""
        if hasattr(self, "id") and self.id:
            query = f"DELETE FROM {self.table_name} WHERE id = ?"
            self.db_manager.execute_update(query, (self.id,))

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}


# Database initialization migrations
INITIAL_MIGRATIONS = {
    "001_create_users_table": {
        "description": "Create users table with enhanced security",
        "sql": """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone TEXT,
            company_name TEXT,
            is_active BOOLEAN DEFAULT 1,
            email_verified BOOLEAN DEFAULT 0,
            failed_login_attempts INTEGER DEFAULT 0,
            locked_until TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
        """,
    },
    "002_create_user_roles_table": {
        "description": "Create user roles and permissions",
        "sql": """
        CREATE TABLE IF NOT EXISTS user_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role_name TEXT NOT NULL,
            granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            granted_by INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (granted_by) REFERENCES users(id)
        );

        CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role_name);
        """,
    },
    "003_create_audit_log_table": {
        "description": "Create audit log table",
        "sql": """
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            event_type TEXT NOT NULL,
            user_id TEXT,
            resource_type TEXT,
            resource_id TEXT,
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            user_agent TEXT,
            success BOOLEAN NOT NULL,
            error_message TEXT,
            event_hash TEXT NOT NULL,
            chain_hash TEXT NOT NULL,
            previous_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_audit_log_event_type ON audit_log(event_type);
        CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);
        """,
    },
}


def initialize_database(db_path: str) -> Tuple[DatabaseManager, MigrationManager]:
    """Initialize database with migrations"""
    db_manager = DatabaseManager(db_path)
    migration_manager = MigrationManager(db_manager)

    # Apply initial migrations
    for version, migration in INITIAL_MIGRATIONS.items():
        migration_manager.apply_migration(
            version, migration["description"], migration["sql"]
        )

    return db_manager, migration_manager
