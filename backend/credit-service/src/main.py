import os
import sys

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from database.manager import BaseModel, initialize_database
from .routes.user import credit_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), "static"))
app.config["SECRET_KEY"] = "asdf#FGSgvasgf$5$WGT"

app.register_blueprint(credit_bp, url_prefix="/api/v1/credit")

# Initialize database
db_path = os.path.join(os.path.dirname(__file__), "database", "app.db")
os.makedirs(os.path.dirname(db_path), exist_ok=True)
db_manager, migration_manager = initialize_database(db_path)

# Set database manager for models
BaseModel.set_db_manager(db_manager)

# Apply Credit-specific migrations
from .migrations import CREDIT_MIGRATIONS

for version, migration in CREDIT_MIGRATIONS.items():
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
            return "index.html not found", 404


if __name__ == "__main__":
    # Ensure data directory exists
    os.makedirs(
        "/home/ubuntu/NexaFi/backend/credit-service/src/database", exist_ok=True
    )

    # Development server
    app.run(host="0.0.0.0", port=5005, debug=True)
