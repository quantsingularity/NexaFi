with open("enhanced_security.py", "r") as f:
    lines = f.readlines()

# Find _initialize_fraud_tables method
method_start = -1
for i, line in enumerate(lines):
    if "def _initialize_fraud_tables(self)" in line:
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

    new_method = '''    def _initialize_fraud_tables(self) -> Any:
        """Initialize fraud detection tables"""
        # Execute each statement separately
        statements = [
            """
            CREATE TABLE IF NOT EXISTS fraud_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                alert_type TEXT NOT NULL,
                risk_score REAL NOT NULL,
                details TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS transaction_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                pattern_type TEXT NOT NULL,
                pattern_data TEXT NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_fraud_alerts_user_id ON fraud_alerts(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_fraud_alerts_status ON fraud_alerts(status)",
            "CREATE INDEX IF NOT EXISTS idx_transaction_patterns_user_id ON transaction_patterns(user_id)",
        ]
        for statement in statements:
            self.db_manager.execute_query(statement)

'''

    new_lines = lines[:method_start] + [new_method] + lines[method_end:]

    with open("enhanced_security.py", "w") as f:
        f.writelines(new_lines)

    print(f"Fixed FraudDetectionEngine! Replaced lines {method_start} to {method_end}")
else:
    print("Method not found")
