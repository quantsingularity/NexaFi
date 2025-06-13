
import locust
from locust import HttpUser, task, between
import random

class WebsiteUser(HttpUser):
    wait_time = between(1, 2)  # Users wait between 1 and 2 seconds between tasks

    host = "http://localhost:5000" # Default host for API Gateway

    # On start, each user will try to log in to get a token
    def on_start(self):
        self.client.post("/auth/login", json={
            "email": "test@example.com", # Use a pre-registered test user
            "password": "password123"
        })
        # Assuming successful login, the token would be stored in the client session
        # For simplicity, we're not explicitly handling token refresh here, but in a real scenario, it would be needed.

    @task
    def index_page(self):
        self.client.get("/", name="01_Homepage")

    @task(3)  # This task has a higher weight (3 times more likely to be executed)
    def login(self):
        self.client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        }, name="02_Login")

    @task
    def get_user_profile(self):
        self.client.get("/users/profile", name="03_UserProfile")

    @task
    def update_user_profile(self):
        # Simulate updating a user profile
        self.client.put("/users/profile", json={
            "first_name": f"TestUser{random.randint(1, 1000)}",
            "last_name": "Locust",
            "email": "test@example.com"
        }, name="04_UpdateUserProfile")

    @task
    def get_accounts(self):
        self.client.get("/accounts", name="05_GetAccounts")

    @task
    def create_account(self):
        self.client.post("/accounts", json={
            "account_name": f"Locust Account {random.randint(1, 10000)}",
            "account_code": str(random.randint(1000, 9999)),
            "account_type": random.choice(["asset", "liability", "equity", "revenue", "expense"]),
            "description": "Account created by Locust"
        }, name="06_CreateAccount")

    @task
    def get_journal_entries(self):
        self.client.get("/journal-entries", name="07_GetJournalEntries")

    @task
    def create_journal_entry(self):
        self.client.post("/journal-entries", json={
            "entry_date": "2024-06-15",
            "description": f"Locust Test Entry {random.randint(1, 10000)}",
            "line_items": [
                {"account_id": "1", "debit": random.uniform(10, 1000), "credit": 0},
                {"account_id": "2", "debit": 0, "credit": random.uniform(10, 1000)}
            ]
        }, name="08_CreateJournalEntry")

    @task
    def get_financial_summary(self):
        self.client.get("/dashboard/financial-summary", name="09_FinancialSummary")

    @task
    def get_transactions(self):
        self.client.get("/transactions", name="10_GetTransactions")

    @task
    def create_transaction(self):
        self.client.post("/transactions", json={
            "amount": random.uniform(10, 500),
            "type": random.choice(["income", "expense"]),
            "description": f"Locust Transaction {random.randint(1, 10000)}",
            "payment_method_id": "some_method_id" # Placeholder
        }, name="11_CreateTransaction")

    @task
    def predict_cash_flow(self):
        self.client.post("/predictions/cash-flow", json={
            "data": [random.uniform(100, 1000) for _ in range(12)] # Example data
        }, name="12_PredictCashFlow")

    @task
    def get_insights(self):
        self.client.get("/insights", name="13_GetInsights")

    @task
    def health_check(self):
        self.client.get("/health", name="14_HealthCheck")

# To run this Locust test:
# 1. Make sure you have Locust installed: pip install locust
# 2. Save this code as, e.g., `locustfile.py`
# 3. Run from your terminal: locust -f locustfile.py --host=http://localhost:5000
# 4. Open your browser to http://localhost:8089 (Locust web UI)
# 5. Start the test with desired number of users and spawn rate.


