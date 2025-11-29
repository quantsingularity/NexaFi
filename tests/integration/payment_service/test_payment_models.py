from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

# Assuming the file structure allows these imports to resolve correctly
from NexaFi.backend.payment_service.src.main import app
from NexaFi.backend.payment_service.src.models.user import (
    ExchangeRate,
    PaymentMethod,
    RecurringPayment,
    Transaction,
    Wallet,
    WalletBalanceHistory,
    db,
)


@pytest.fixture(scope="module")
def client():
    """Configures the Flask app for testing and sets up an in-memory database."""
    # Ensure the database URI is set to in-memory SQLite for speed and isolation
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.test_client() as client:
        with app.app_context():
            # Create all tables before the tests run
            db.create_all()
        yield client
        with app.app_context():
            # Drop all tables after the tests run
            db.drop_all()


@pytest.fixture(autouse=True)
def run_around_tests(client):
    """Cleans up the database between each test."""
    with app.app_context():
        # Clean data from all tables
        PaymentMethod.query.delete()
        Transaction.query.delete()
        Wallet.query.delete()
        WalletBalanceHistory.query.delete()
        RecurringPayment.query.delete()
        ExchangeRate.query.delete()
        db.session.commit()
    yield


class TestPaymentMethodModel:

    def test_payment_method_creation(self):
        # Test creation and retrieval
        pm = PaymentMethod(
            user_id="user123",
            type="card",
            provider="Stripe",
            details={"last4": "1234", "brand": "Visa"},
        )
        db.session.add(pm)
        db.session.commit()

        retrieved_pm = PaymentMethod.query.filter_by(user_id="user123").first()
        assert retrieved_pm is not None
        assert retrieved_pm.type == "card"
        assert retrieved_pm.provider == "Stripe"
        assert retrieved_pm.details["last4"] == "1234"

    def test_payment_method_to_dict(self):
        # Test serialization to dictionary format
        pm = PaymentMethod(
            user_id="user123",
            type="card",
            provider="Stripe",
            details={"last4": "1234", "brand": "Visa"},
        )
        db.session.add(pm)
        db.session.commit()

        pm_dict = pm.to_dict()
        assert pm_dict["type"] == "card"
        # The to_dict method masks details and uses 'last_four' key
        assert pm_dict["masked_details"]["last_four"] == "1234"
        assert "details" not in pm_dict  # Ensure raw details are not exposed


class TestTransactionModel:

    def test_transaction_creation(self):
        # Test creation and retrieval
        transaction = Transaction(
            user_id="user456",
            transaction_type="payment",
            amount=Decimal("100.00"),
            currency="USD",
            status="pending",
            net_amount=Decimal("95.00"),
        )
        db.session.add(transaction)
        db.session.commit()

        retrieved_transaction = Transaction.query.filter_by(user_id="user456").first()
        assert retrieved_transaction is not None
        assert retrieved_transaction.amount == Decimal("100.00")
        assert retrieved_transaction.net_amount == Decimal("95.00")

    def test_transaction_to_dict(self):
        # Test serialization to dictionary format
        transaction = Transaction(
            user_id="user456",
            transaction_type="payment",
            amount=Decimal("100.00"),
            currency="USD",
            status="pending",
            net_amount=Decimal("95.00"),
        )
        db.session.add(transaction)
        db.session.commit()

        transaction_dict = transaction.to_dict()
        # Decimals should be converted to float for JSON compatibility
        assert transaction_dict["amount"] == 100.00
        assert transaction_dict["status"] == "pending"
        assert transaction_dict["net_amount"] == 95.00


class TestWalletModel:

    def test_wallet_creation(self):
        # Test creation and retrieval
        wallet = Wallet(user_id="user789", currency="EUR", balance=Decimal("500.00"))
        db.session.add(wallet)
        db.session.commit()

        retrieved_wallet = Wallet.query.filter_by(user_id="user789").first()
        assert retrieved_wallet is not None
        assert retrieved_wallet.currency == "EUR"
        assert retrieved_wallet.balance == Decimal("500.00")

    def test_wallet_to_dict(self):
        # Test serialization to dictionary format
        wallet = Wallet(user_id="user789", currency="EUR", balance=Decimal("500.00"))
        db.session.add(wallet)
        db.session.commit()

        wallet_dict = wallet.to_dict()
        assert wallet_dict["currency"] == "EUR"
        # Decimals should be converted to float
        assert wallet_dict["balance"] == 500.00


class TestWalletBalanceHistoryModel:

    def test_wallet_balance_history_creation(self):
        # Setup prerequisite wallet
        wallet = Wallet(user_id="user101", currency="GBP", balance=Decimal("100.00"))
        db.session.add(wallet)
        db.session.commit()

        # Test creation and retrieval of history record
        history = WalletBalanceHistory(
            wallet_id=wallet.id,
            change_type="credit",
            amount=Decimal("50.00"),
            balance_before=Decimal("100.00"),
            balance_after=Decimal("150.00"),
            description="Deposit",
        )
        db.session.add(history)
        db.session.commit()

        retrieved_history = WalletBalanceHistory.query.filter_by(
            wallet_id=wallet.id
        ).first()
        assert retrieved_history is not None
        assert retrieved_history.change_type == "credit"
        assert retrieved_history.amount == Decimal("50.00")
        assert retrieved_history.balance_after == Decimal("150.00")


class TestRecurringPaymentModel:

    def test_recurring_payment_creation(self):
        # Setup prerequisite payment method
        pm = PaymentMethod(
            user_id="user111", type="card", provider="Visa", details={"last4": "9999"}
        )
        db.session.add(pm)
        db.session.commit()

        # Calculate next payment date
        next_date = date.today() + timedelta(days=30)

        # Test creation and retrieval of recurring payment
        rp = RecurringPayment(
            user_id="user111",
            payment_method_id=pm.id,
            amount=Decimal("10.00"),
            currency="USD",
            frequency="monthly",
            start_date=date.today(),
            next_payment_date=next_date,
        )
        db.session.add(rp)
        db.session.commit()

        retrieved_rp = RecurringPayment.query.filter_by(user_id="user111").first()
        assert retrieved_rp is not None
        assert retrieved_rp.amount == Decimal("10.00")
        assert retrieved_rp.frequency == "monthly"
        assert retrieved_rp.next_payment_date == next_date


class TestExchangeRateModel:

    def test_exchange_rate_creation(self):
        # Define the valid_from timestamp for testing
        test_valid_from = datetime.utcnow().replace(microsecond=0)

        # Test creation and retrieval of exchange rate
        er = ExchangeRate(
            base_currency="USD",
            target_currency="JPY",
            rate=Decimal("150.00"),
            source="API",
            valid_from=test_valid_from,
        )
        db.session.add(er)
        db.session.commit()

        retrieved_er = ExchangeRate.query.filter_by(
            base_currency="USD", target_currency="JPY"
        ).first()
        assert retrieved_er is not None
        assert retrieved_er.rate == Decimal("150.00")
        # Use a tolerance for datetime comparison or ensure minimal precision
        assert retrieved_er.valid_from.replace(microsecond=0) == test_valid_from
