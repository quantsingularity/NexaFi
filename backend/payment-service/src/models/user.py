import uuid
from datetime import datetime
from decimal import Decimal

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class PaymentMethod(db.Model):
    __tablename__ = "payment_methods"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)
    type = db.Column(
        db.String(50), nullable=False
    )  # card, bank_account, digital_wallet
    provider = db.Column(db.String(100), nullable=False)  # stripe, plaid, paypal, etc.
    external_id = db.Column(db.String(255))  # External provider ID
    details = db.Column(db.JSON, nullable=False)  # Encrypted payment details
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    verification_status = db.Column(db.String(50), default="pending")
    last_used_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)  # For cards
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    transactions = db.relationship(
        "Transaction", backref="payment_method", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<PaymentMethod {self.type}: {self.provider}>"

    def to_dict(self, include_sensitive=False):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "provider": self.provider,
            "external_id": self.external_id,
            "is_default": self.is_default,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "verification_status": self.verification_status,
            "last_used_at": (
                self.last_used_at.isoformat() if self.last_used_at else None
            ),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        # Add masked details for security
        if self.details:
            if self.type == "card":
                data["masked_details"] = {
                    "last_four": self.details.get("last_four"),
                    "brand": self.details.get("brand"),
                    "exp_month": self.details.get("exp_month"),
                    "exp_year": self.details.get("exp_year"),
                }
            elif self.type == "bank_account":
                data["masked_details"] = {
                    "last_four": self.details.get("last_four"),
                    "bank_name": self.details.get("bank_name"),
                    "account_type": self.details.get("account_type"),
                }
            elif self.type == "digital_wallet":
                data["masked_details"] = {
                    "email": self.details.get("email"),
                    "wallet_type": self.details.get("wallet_type"),
                }

        if include_sensitive:
            data["details"] = self.details

        return data


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)
    payment_method_id = db.Column(db.String(36), db.ForeignKey("payment_methods.id"))
    transaction_type = db.Column(
        db.String(50), nullable=False
    )  # payment, refund, transfer, withdrawal
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(3), default="USD")
    description = db.Column(db.Text)
    reference = db.Column(db.String(100))
    status = db.Column(
        db.String(50), nullable=False
    )  # pending, processing, completed, failed, cancelled
    external_transaction_id = db.Column(db.String(255))
    provider_response = db.Column(db.JSON)
    fees = db.Column(db.Numeric(15, 2), default=Decimal("0"))
    net_amount = db.Column(db.Numeric(15, 2), nullable=False)
    failure_reason = db.Column(db.String(255))
    metadata = db.Column(db.JSON)
    processed_at = db.Column(db.DateTime)
    settled_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<Transaction {self.transaction_type}: {self.amount} {self.currency}>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "payment_method_id": self.payment_method_id,
            "transaction_type": self.transaction_type,
            "amount": float(self.amount) if self.amount else 0,
            "currency": self.currency,
            "description": self.description,
            "reference": self.reference,
            "status": self.status,
            "external_transaction_id": self.external_transaction_id,
            "provider_response": self.provider_response,
            "fees": float(self.fees) if self.fees else 0,
            "net_amount": float(self.net_amount) if self.net_amount else 0,
            "failure_reason": self.failure_reason,
            "metadata": self.metadata,
            "processed_at": (
                self.processed_at.isoformat() if self.processed_at else None
            ),
            "settled_at": self.settled_at.isoformat() if self.settled_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Wallet(db.Model):
    __tablename__ = "wallets"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)
    currency = db.Column(db.String(3), nullable=False)
    balance = db.Column(db.Numeric(15, 2), default=Decimal("0"))
    available_balance = db.Column(db.Numeric(15, 2), default=Decimal("0"))
    pending_balance = db.Column(db.Numeric(15, 2), default=Decimal("0"))
    reserved_balance = db.Column(db.Numeric(15, 2), default=Decimal("0"))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    balance_history = db.relationship(
        "WalletBalanceHistory", backref="wallet", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Wallet {self.currency}: {self.balance}>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "currency": self.currency,
            "balance": float(self.balance) if self.balance else 0,
            "available_balance": (
                float(self.available_balance) if self.available_balance else 0
            ),
            "pending_balance": (
                float(self.pending_balance) if self.pending_balance else 0
            ),
            "reserved_balance": (
                float(self.reserved_balance) if self.reserved_balance else 0
            ),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class WalletBalanceHistory(db.Model):
    __tablename__ = "wallet_balance_history"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    wallet_id = db.Column(db.String(36), db.ForeignKey("wallets.id"), nullable=False)
    transaction_id = db.Column(db.String(36), db.ForeignKey("transactions.id"))
    change_type = db.Column(
        db.String(50), nullable=False
    )  # credit, debit, hold, release
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    balance_before = db.Column(db.Numeric(15, 2), nullable=False)
    balance_after = db.Column(db.Numeric(15, 2), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<WalletBalanceHistory {self.change_type}: {self.amount}>"

    def to_dict(self):
        return {
            "id": self.id,
            "wallet_id": self.wallet_id,
            "transaction_id": self.transaction_id,
            "change_type": self.change_type,
            "amount": float(self.amount) if self.amount else 0,
            "balance_before": float(self.balance_before) if self.balance_before else 0,
            "balance_after": float(self.balance_after) if self.balance_after else 0,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PaymentProcessor(db.Model):
    __tablename__ = "payment_processors"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), unique=True, nullable=False)
    provider_type = db.Column(
        db.String(50), nullable=False
    )  # stripe, paypal, square, etc.
    supported_methods = db.Column(
        db.JSON, nullable=False
    )  # List of supported payment methods
    supported_currencies = db.Column(
        db.JSON, nullable=False
    )  # List of supported currencies
    fee_structure = db.Column(db.JSON)  # Fee structure configuration
    api_config = db.Column(db.JSON)  # API configuration (encrypted)
    is_active = db.Column(db.Boolean, default=True)
    is_sandbox = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<PaymentProcessor {self.name}>"

    def to_dict(self, include_sensitive=False):
        data = {
            "id": self.id,
            "name": self.name,
            "provider_type": self.provider_type,
            "supported_methods": self.supported_methods,
            "supported_currencies": self.supported_currencies,
            "fee_structure": self.fee_structure,
            "is_active": self.is_active,
            "is_sandbox": self.is_sandbox,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_sensitive:
            data["api_config"] = self.api_config

        return data


class RecurringPayment(db.Model):
    __tablename__ = "recurring_payments"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)
    payment_method_id = db.Column(
        db.String(36), db.ForeignKey("payment_methods.id"), nullable=False
    )
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(3), default="USD")
    frequency = db.Column(
        db.String(20), nullable=False
    )  # daily, weekly, monthly, quarterly, yearly
    interval = db.Column(db.Integer, default=1)  # Every X frequency periods
    description = db.Column(db.Text)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    next_payment_date = db.Column(db.Date, nullable=False)
    total_payments = db.Column(db.Integer)  # Total number of payments (optional)
    payments_made = db.Column(db.Integer, default=0)
    status = db.Column(
        db.String(20), default="active"
    )  # active, paused, cancelled, completed
    metadata = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<RecurringPayment {self.frequency}: {self.amount} {self.currency}>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "payment_method_id": self.payment_method_id,
            "amount": float(self.amount) if self.amount else 0,
            "currency": self.currency,
            "frequency": self.frequency,
            "interval": self.interval,
            "description": self.description,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "next_payment_date": (
                self.next_payment_date.isoformat() if self.next_payment_date else None
            ),
            "total_payments": self.total_payments,
            "payments_made": self.payments_made,
            "status": self.status,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ExchangeRate(db.Model):
    __tablename__ = "exchange_rates"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    base_currency = db.Column(db.String(3), nullable=False)
    target_currency = db.Column(db.String(3), nullable=False)
    rate = db.Column(db.Numeric(15, 8), nullable=False)
    source = db.Column(db.String(50), nullable=False)  # API source
    valid_from = db.Column(db.DateTime, nullable=False)
    valid_until = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return (
            f"<ExchangeRate {self.base_currency}/{self.target_currency}: {self.rate}>"
        )

    def to_dict(self):
        return {
            "id": self.id,
            "base_currency": self.base_currency,
            "target_currency": self.target_currency,
            "rate": float(self.rate) if self.rate else 0,
            "source": self.source,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
