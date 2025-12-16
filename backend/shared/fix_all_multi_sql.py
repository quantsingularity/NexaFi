import re

with open("enhanced_security.py", "r") as f:
    content = f.read()

# Find all methods that execute multi-statement SQL
method_pattern = r'(    def (_initialize_\w+_tables)\(self\).*?:.*?\n.*?""".*?""".*?\n)(.*?self\.db_manager\.execute_query\([^)]+\))'


def fix_method(match):
    method_def = match.group(1)
    match.group(2)
    rest = match.group(3)

    # Extract the SQL string
    sql_match = re.search(r'(\w+_sql)\s*=\s*"([^"]*)"', rest, re.DOTALL)
    if not sql_match:
        sql_match = re.search(r"(\w+_sql)\s*=\s*\'([^\']*)\'", rest, re.DOTALL)

    if sql_match:
        sql_match.group(1)
        sql_content = sql_match.group(2)

        # Split by semicolons to get individual statements
        statements = [
            s.strip()
            for s in re.split(r";(?=\s*(?:CREATE|INSERT))", sql_content)
            if s.strip()
        ]

        # Build the new method
        new_code = method_def
        new_code += "        # Execute each statement separately to avoid SQLite's single statement limitation\n"
        new_code += "        statements = [\n"

        for stmt in statements:
            # Clean up the statement
            stmt = stmt.strip()
            if stmt:
                # Remove trailing semicolons
                stmt = stmt.rstrip(";").strip()
                # Escape the triple quotes properly
                new_code += f'            """\n            {stmt}\n            """,\n'

        new_code += "        ]\n"
        new_code += "        for statement in statements:\n"
        new_code += "            self.db_manager.execute_query(statement)\n"

        return new_code

    return match.group(0)


# Apply the fix
fixed_content = re.sub(method_pattern, fix_method, content, flags=re.DOTALL)

with open("enhanced_security.py", "w") as f:
    f.write(fixed_content)

print("Fixed all multi-statement SQL methods")
