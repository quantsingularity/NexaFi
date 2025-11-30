import os
import sys

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from database.manager import BaseModel, initialize_database
from .routes.user import payment_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), "static"))
app.config["SECRET_KEY"] = "nexafi-payment-service-secret-key-2024"

# Enable CORS for all routes
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization", "X-User-ID"])

app.register_blueprint(payment_bp, url_prefix="/api/v1/payment")

# Initialize database
db_path = os.path.join(os.path.dirname(__file__), "database", "app.db")
os.makedirs(os.path.dirname(db_path), exist_ok=True)
db_manager, migration_manager = initialize_database(db_path)

# Set database manager for models
BaseModel.set_db_manager(db_manager)

# Apply Payment-specific migrations
PAYMENT_MIGRATIONS = {
    "001_create_payment_tables": {
        "description": "Create payment_methods, transactions, wallets, and recurring_payments tables",
        "sql": """
        CREATE TABLE IF NOT EXISTS payment_methods (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            type TEXT NOT NULL,
            provider TEXT NOT NULL,
            external_id TEXT,
            details TEXT,
            is_default INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            is_verified INTEGER DEFAULT 0,
            verification_status TEXT DEFAULT 'pending',
            last_used_at TEXT,
            expires_at TEXT,
            created_at TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            payment_method_id TEXT,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'USD',
            description TEXT,
            reference TEXT,
            status TEXT NOT NULL,
            external_transaction_id TEXT,
            provider_response TEXT,
            fees REAL DEFAULT 0.0,
            net_amount REAL NOT NULL,
            failure_reason TEXT,
            metadata TEXT,
            processed_at TEXT,
            settled_at TEXT,
            created_at TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS wallets (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            currency TEXT NOT NULL,
            balance REAL DEFAULT 0.0,
            available_balance REAL DEFAULT 0.0,
            pending_balance REAL DEFAULT 0.0,
            reserved_balance REAL DEFAULT 0.0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS wallet_balance_history (
            id TEXT PRIMARY KEY,
            wallet_id TEXT NOT NULL,
            transaction_id TEXT,
            change_type TEXT NOT NULL,
            amount REAL NOT NULL,
            balance_before REAL NOT NULL,
            balance_after REAL NOT NULL,
            description TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS recurring_payments (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            payment_method_id TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'USD',
            frequency TEXT NOT NULL,
            description TEXT,
            start_date TEXT NOT NULL,
            end_date TEXT,
            next_payment_date TEXT NOT NULL,
            total_payments INTEGER,
            payments_made INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            metadata TEXT,
            created_at TEXT,
            updated_at TEXT
        );
        """,
    },
}

for version, migration in PAYMENT_MIGRATIONS.items():
    migration_manager.apply_migration(
        version, migration["description"], migration["sql"]
    )


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, "index.html")
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, "index.html")
        else:
            return "Payment Service API - NexaFi Platform", 200


@app.errorhandler(404)
def not_found(error):
    return {"error": "Endpoint not found"}, 404


@app.errorhandler(500)
def internal_error(error):
    return {"error": "Internal server error"}, 500


if __name__ == "__main__":
    # Ensure data directory exists
    os.makedirs(os.path.join(os.path.dirname(__file__), "database"), exist_ok=True)

    # Development server
    app.run(host="0.0.0.0", port=5008, debug=True)
