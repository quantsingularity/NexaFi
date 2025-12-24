# Fix all _initialize methods

with open("enhanced_security.py", "r") as f:
    lines = f.readlines()

methods_to_fix = ["_initialize_mfa_tables", "_initialize_session_tables"]

for method_name in methods_to_fix:
    method_start = -1
    for i, line in enumerate(lines):
        if f"def {method_name}(self)" in line:
            method_start = i
            break

    if method_start != -1:
        # Find the end
        indent_level = len(lines[method_start]) - len(lines[method_start].lstrip())
        method_end = method_start + 1

        for i in range(method_start + 1, len(lines)):
            if (
                lines[i].strip()
                and not lines[i].startswith(" " * (indent_level + 4))
                and not lines[i].strip().startswith('"')
            ):
                if lines[i].startswith(" " * indent_level) and (
                    lines[i].strip().startswith("def ")
                    or lines[i].strip().startswith("class ")
                ):
                    method_end = i
                    break
            if i == len(lines) - 1:
                method_end = i + 1

        # Get the old method
        old_method = "".join(lines[method_start:method_end])

        # Create appropriate replacement
        if method_name == "_initialize_mfa_tables":
            new_method = '''    def _initialize_mfa_tables(self) -> Any:
        """Initialize MFA tables"""
        # Execute each statement separately
        statements = [
            """
            CREATE TABLE IF NOT EXISTS mfa_secrets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                secret TEXT NOT NULL,
                method TEXT NOT NULL,
                enabled BOOLEAN DEFAULT FALSE,
                backup_codes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS mfa_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                method TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_mfa_secrets_user_id ON mfa_secrets(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_mfa_attempts_user_id ON mfa_attempts(user_id)",
        ]
        for statement in statements:
            self.db_manager.execute_query(statement)

'''
        elif method_name == "_initialize_session_tables":
            new_method = '''    def _initialize_session_tables(self) -> Any:
        """Initialize session management tables"""
        # Execute each statement separately
        statements = [
            """
            CREATE TABLE IF NOT EXISTS secure_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                user_agent TEXT,
                device_fingerprint TEXT,
                security_level TEXT NOT NULL,
                mfa_verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT TRUE
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON secure_sessions(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON secure_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON secure_sessions(expires_at)",
        ]
        for statement in statements:
            self.db_manager.execute_query(statement)

'''
        else:
            continue

        # Replace
        lines = lines[:method_start] + [new_method] + lines[method_end:]
        print(f"Fixed {method_name}")

with open("enhanced_security.py", "w") as f:
    f.writelines(lines)

print("Done!")
