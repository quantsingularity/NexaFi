with open("enhanced_security.py", "r") as f:
    lines = f.readlines()

# Find and replace the method
in_method = False
method_start = -1
for i, line in enumerate(lines):
    if "def _initialize_monitoring_tables(self)" in line:
        method_start = i
        in_method = True
        break

if method_start != -1:
    # Find the end of the method
    indent_level = len(lines[method_start]) - len(lines[method_start].lstrip())
    method_end = method_start + 1

    for i in range(method_start + 1, len(lines)):
        # Check if we've hit a new method or class definition
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

    # Replace the method
    new_method = '''    def _initialize_monitoring_tables(self) -> Any:
        """Initialize security monitoring tables"""
        # Execute each statement separately to avoid SQLite's single statement limitation
        statements = [
            """
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
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS threat_indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                indicator_type TEXT NOT NULL,
                indicator_value TEXT NOT NULL,
                threat_level TEXT NOT NULL,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                occurrence_count INTEGER DEFAULT 1,
                status TEXT DEFAULT 'active'
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_security_events_user_id ON security_events(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_security_events_ip_address ON security_events(ip_address)",
            "CREATE INDEX IF NOT EXISTS idx_security_events_created_at ON security_events(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_threat_indicators_value ON threat_indicators(indicator_value)",
        ]
        for statement in statements:
            self.db_manager.execute_query(statement)

'''

    # Rebuild the file
    new_lines = lines[:method_start] + [new_method] + lines[method_end:]

    with open("enhanced_security.py", "w") as f:
        f.writelines(new_lines)

    print(f"Fixed! Replaced lines {method_start} to {method_end}")
else:
    print("Method not found")
