import hashlib
import json
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from functools import wraps

from flask import Blueprint, jsonify, request
from src.models.user import (
    ExchangeRate,
    PaymentMethod,
    PaymentProcessor,
    RecurringPayment,
    Transaction,
    Wallet,
    WalletBalanceHistory,
    db,
)

user_bp = Blueprint("payment", __name__)


def require_user_id(f):
    """Decorator to extract user_id from request headers"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.headers.get("X-User-ID")
        if not user_id:
            return jsonify({"error": "User ID is required in headers"}), 401
        request.user_id = user_id
        return f(*args, **kwargs)

    return decorated_function


def calculate_fees(amount, payment_method_type, processor_name="default"):
    """Calculate transaction fees based on payment method and processor"""
    # Default fee structure (can be made configurable)
    fee_structures = {
        "card": {
            "percentage": Decimal("0.029"),
            "fixed": Decimal("0.30"),
        },  # 2.9% + $0.30
        "bank_account": {
            "percentage": Decimal("0.008"),
            "fixed": Decimal("0.00"),
        },  # 0.8%
        "digital_wallet": {
            "percentage": Decimal("0.025"),
            "fixed": Decimal("0.00"),
        },  # 2.5%
    }

    fee_structure = fee_structures.get(payment_method_type, fee_structures["card"])
    percentage_fee = amount * fee_structure["percentage"]
    total_fee = percentage_fee + fee_structure["fixed"]

    return total_fee


def create_or_update_wallet(user_id, currency="USD"):
    """Create or get existing wallet for user and currency"""
    wallet = Wallet.query.filter_by(user_id=user_id, currency=currency).first()

    if not wallet:
        wallet = Wallet(
            user_id=user_id,
            currency=currency,
            balance=Decimal("0"),
            available_balance=Decimal("0"),
            pending_balance=Decimal("0"),
            reserved_balance=Decimal("0"),
        )
        db.session.add(wallet)
        db.session.flush()

    return wallet


def update_wallet_balance(
    wallet, amount, change_type, description, transaction_id=None
):
    """Update wallet balance and create history record"""
    balance_before = wallet.balance

    if change_type == "credit":
        wallet.balance += amount
        wallet.available_balance += amount
    elif change_type == "debit":
        wallet.balance -= amount
        wallet.available_balance -= amount
    elif change_type == "hold":
        wallet.available_balance -= amount
        wallet.reserved_balance += amount
    elif change_type == "release":
        wallet.available_balance += amount
        wallet.reserved_balance -= amount

    wallet.updated_at = datetime.utcnow()

    # Create balance history record
    history = WalletBalanceHistory(
        wallet_id=wallet.id,
        transaction_id=transaction_id,
        change_type=change_type,
        amount=amount,
        balance_before=balance_before,
        balance_after=wallet.balance,
        description=description,
    )

    db.session.add(history)


# Payment Method Routes
@user_bp.route("/payment-methods", methods=["GET"])
@require_user_id
def get_payment_methods():
    """Get all payment methods for user"""
    try:
        payment_methods = (
            PaymentMethod.query.filter_by(user_id=request.user_id, is_active=True)
            .order_by(PaymentMethod.is_default.desc(), PaymentMethod.created_at.desc())
            .all()
        )

        return (
            jsonify(
                {
                    "payment_methods": [method.to_dict() for method in payment_methods],
                    "total": len(payment_methods),
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify({"error": "Failed to get payment methods", "details": str(e)}),
            500,
        )


@user_bp.route("/payment-methods", methods=["POST"])
@require_user_id
def create_payment_method():
    """Create new payment method"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["type", "provider", "details"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400

        # Validate payment method type
        valid_types = ["card", "bank_account", "digital_wallet"]
        if data["type"] not in valid_types:
            return (
                jsonify(
                    {
                        "error": f"Invalid payment method type. Must be one of: {valid_types}"
                    }
                ),
                400,
            )

        # Create payment method
        payment_method = PaymentMethod(
            user_id=request.user_id,
            type=data["type"],
            provider=data["provider"],
            external_id=data.get("external_id"),
            details=data["details"],
            is_default=data.get("is_default", False),
            expires_at=(
                datetime.strptime(data["expires_at"], "%Y-%m-%d")
                if data.get("expires_at")
                else None
            ),
        )

        # If this is set as default, unset other defaults
        if payment_method.is_default:
            PaymentMethod.query.filter_by(
                user_id=request.user_id, is_default=True
            ).update({"is_default": False})

        db.session.add(payment_method)
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Payment method created successfully",
                    "payment_method": payment_method.to_dict(),
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return (
            jsonify({"error": "Failed to create payment method", "details": str(e)}),
            500,
        )


@user_bp.route("/payment-methods/<method_id>", methods=["GET"])
@require_user_id
def get_payment_method(method_id):
    """Get specific payment method"""
    try:
        payment_method = PaymentMethod.query.filter_by(
            id=method_id, user_id=request.user_id
        ).first()

        if not payment_method:
            return jsonify({"error": "Payment method not found"}), 404

        return jsonify({"payment_method": payment_method.to_dict()}), 200

    except Exception as e:
        return (
            jsonify({"error": "Failed to get payment method", "details": str(e)}),
            500,
        )


@user_bp.route("/payment-methods/<method_id>", methods=["PUT"])
@require_user_id
def update_payment_method(method_id):
    """Update payment method"""
    try:
        payment_method = PaymentMethod.query.filter_by(
            id=method_id, user_id=request.user_id
        ).first()

        if not payment_method:
            return jsonify({"error": "Payment method not found"}), 404

        data = request.get_json()

        # Update fields
        updatable_fields = ["details", "is_default", "is_active", "expires_at"]
        for field in updatable_fields:
            if field in data:
                if field == "expires_at" and data[field]:
                    setattr(
                        payment_method,
                        field,
                        datetime.strptime(data[field], "%Y-%m-%d"),
                    )
                else:
                    setattr(payment_method, field, data[field])

        # If this is set as default, unset other defaults
        if data.get("is_default"):
            PaymentMethod.query.filter_by(
                user_id=request.user_id, is_default=True
            ).filter(PaymentMethod.id != method_id).update({"is_default": False})

        payment_method.updated_at = datetime.utcnow()
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Payment method updated successfully",
                    "payment_method": payment_method.to_dict(),
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return (
            jsonify({"error": "Failed to update payment method", "details": str(e)}),
            500,
        )


@user_bp.route("/payment-methods/<method_id>", methods=["DELETE"])
@require_user_id
def delete_payment_method(method_id):
    """Delete payment method"""
    try:
        payment_method = PaymentMethod.query.filter_by(
            id=method_id, user_id=request.user_id
        ).first()

        if not payment_method:
            return jsonify({"error": "Payment method not found"}), 404

        # Soft delete by setting is_active to False
        payment_method.is_active = False
        payment_method.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({"message": "Payment method deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return (
            jsonify({"error": "Failed to delete payment method", "details": str(e)}),
            500,
        )


# Transaction Routes
@user_bp.route("/transactions", methods=["GET"])
@require_user_id
def get_transactions():
    """Get transactions for user"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        status = request.args.get("status")
        transaction_type = request.args.get("type")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        query = Transaction.query.filter_by(user_id=request.user_id)

        if status:
            query = query.filter_by(status=status)

        if transaction_type:
            query = query.filter_by(transaction_type=transaction_type)

        if start_date:
            query = query.filter(
                Transaction.created_at >= datetime.strptime(start_date, "%Y-%m-%d")
            )

        if end_date:
            query = query.filter(
                Transaction.created_at <= datetime.strptime(end_date, "%Y-%m-%d")
            )

        transactions = query.order_by(Transaction.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return (
            jsonify(
                {
                    "transactions": [
                        transaction.to_dict() for transaction in transactions.items
                    ],
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": transactions.total,
                        "pages": transactions.pages,
                        "has_next": transactions.has_next,
                        "has_prev": transactions.has_prev,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": "Failed to get transactions", "details": str(e)}), 500


@user_bp.route("/transactions", methods=["POST"])
@require_user_id
def create_transaction():
    """Create new transaction"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["amount", "transaction_type"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400

        amount = Decimal(str(data["amount"]))
        if amount <= 0:
            return jsonify({"error": "Amount must be greater than 0"}), 400

        # Get payment method if provided
        payment_method = None
        if data.get("payment_method_id"):
            payment_method = PaymentMethod.query.filter_by(
                id=data["payment_method_id"], user_id=request.user_id, is_active=True
            ).first()

            if not payment_method:
                return jsonify({"error": "Invalid payment method"}), 400

        # Calculate fees
        fees = Decimal("0")
        if payment_method:
            fees = calculate_fees(amount, payment_method.type, payment_method.provider)

        net_amount = amount - fees

        # Create transaction
        transaction = Transaction(
            user_id=request.user_id,
            payment_method_id=data.get("payment_method_id"),
            transaction_type=data["transaction_type"],
            amount=amount,
            currency=data.get("currency", "USD"),
            description=data.get("description"),
            reference=data.get("reference"),
            status="pending",
            fees=fees,
            net_amount=net_amount,
            metadata=data.get("metadata"),
        )

        db.session.add(transaction)
        db.session.flush()

        # Process transaction based on type
        if data["transaction_type"] == "payment":
            # For demo purposes, simulate payment processing
            transaction.status = "processing"
            transaction.external_transaction_id = f"ext_{uuid.uuid4().hex[:12]}"

            # Simulate processing delay and success
            transaction.status = "completed"
            transaction.processed_at = datetime.utcnow()
            transaction.settled_at = datetime.utcnow()

            # Update wallet balance
            wallet = create_or_update_wallet(request.user_id, transaction.currency)
            update_wallet_balance(
                wallet,
                net_amount,
                "credit",
                f"Payment received: {transaction.description}",
                transaction.id,
            )

        elif data["transaction_type"] == "withdrawal":
            # Check wallet balance
            wallet = create_or_update_wallet(request.user_id, transaction.currency)
            if wallet.available_balance < amount:
                return jsonify({"error": "Insufficient balance"}), 400

            transaction.status = "processing"
            transaction.external_transaction_id = f"ext_{uuid.uuid4().hex[:12]}"

            # Update wallet balance
            update_wallet_balance(
                wallet,
                amount,
                "debit",
                f"Withdrawal: {transaction.description}",
                transaction.id,
            )

            transaction.status = "completed"
            transaction.processed_at = datetime.utcnow()
            transaction.settled_at = datetime.utcnow()

        # Update payment method last used
        if payment_method:
            payment_method.last_used_at = datetime.utcnow()

        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Transaction created successfully",
                    "transaction": transaction.to_dict(),
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return (
            jsonify({"error": "Failed to create transaction", "details": str(e)}),
            500,
        )


@user_bp.route("/transactions/<transaction_id>", methods=["GET"])
@require_user_id
def get_transaction(transaction_id):
    """Get specific transaction"""
    try:
        transaction = Transaction.query.filter_by(
            id=transaction_id, user_id=request.user_id
        ).first()

        if not transaction:
            return jsonify({"error": "Transaction not found"}), 404

        return jsonify({"transaction": transaction.to_dict()}), 200

    except Exception as e:
        return jsonify({"error": "Failed to get transaction", "details": str(e)}), 500


# Wallet Routes
@user_bp.route("/wallets", methods=["GET"])
@require_user_id
def get_wallets():
    """Get all wallets for user"""
    try:
        wallets = Wallet.query.filter_by(user_id=request.user_id, is_active=True).all()

        return (
            jsonify(
                {
                    "wallets": [wallet.to_dict() for wallet in wallets],
                    "total": len(wallets),
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": "Failed to get wallets", "details": str(e)}), 500


@user_bp.route("/wallets/<currency>", methods=["GET"])
@require_user_id
def get_wallet_by_currency(currency):
    """Get wallet for specific currency"""
    try:
        wallet = Wallet.query.filter_by(
            user_id=request.user_id, currency=currency.upper(), is_active=True
        ).first()

        if not wallet:
            # Create wallet if it doesn't exist
            wallet = create_or_update_wallet(request.user_id, currency.upper())
            db.session.commit()

        return jsonify({"wallet": wallet.to_dict()}), 200

    except Exception as e:
        return jsonify({"error": "Failed to get wallet", "details": str(e)}), 500


@user_bp.route("/wallets/<currency>/history", methods=["GET"])
@require_user_id
def get_wallet_history(currency):
    """Get wallet balance history"""
    try:
        wallet = Wallet.query.filter_by(
            user_id=request.user_id, currency=currency.upper(), is_active=True
        ).first()

        if not wallet:
            return jsonify({"error": "Wallet not found"}), 404

        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)

        history = (
            WalletBalanceHistory.query.filter_by(wallet_id=wallet.id)
            .order_by(WalletBalanceHistory.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

        return (
            jsonify(
                {
                    "wallet": wallet.to_dict(),
                    "history": [record.to_dict() for record in history.items],
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": history.total,
                        "pages": history.pages,
                        "has_next": history.has_next,
                        "has_prev": history.has_prev,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify({"error": "Failed to get wallet history", "details": str(e)}),
            500,
        )


# Recurring Payment Routes
@user_bp.route("/recurring-payments", methods=["GET"])
@require_user_id
def get_recurring_payments():
    """Get recurring payments for user"""
    try:
        recurring_payments = (
            RecurringPayment.query.filter_by(user_id=request.user_id)
            .order_by(RecurringPayment.next_payment_date)
            .all()
        )

        return (
            jsonify(
                {
                    "recurring_payments": [
                        payment.to_dict() for payment in recurring_payments
                    ],
                    "total": len(recurring_payments),
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify({"error": "Failed to get recurring payments", "details": str(e)}),
            500,
        )


@user_bp.route("/recurring-payments", methods=["POST"])
@require_user_id
def create_recurring_payment():
    """Create new recurring payment"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["payment_method_id", "amount", "frequency", "start_date"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400

        # Validate payment method
        payment_method = PaymentMethod.query.filter_by(
            id=data["payment_method_id"], user_id=request.user_id, is_active=True
        ).first()

        if not payment_method:
            return jsonify({"error": "Invalid payment method"}), 400

        # Calculate next payment date
        start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
        next_payment_date = start_date

        # Create recurring payment
        recurring_payment = RecurringPayment(
            user_id=request.user_id,
            payment_method_id=data["payment_method_id"],
            amount=Decimal(str(data["amount"])),
            currency=data.get("currency", "USD"),
            frequency=data["frequency"],
            interval=data.get("interval", 1),
            description=data.get("description"),
            start_date=start_date,
            end_date=(
                datetime.strptime(data["end_date"], "%Y-%m-%d").date()
                if data.get("end_date")
                else None
            ),
            next_payment_date=next_payment_date,
            total_payments=data.get("total_payments"),
            metadata=data.get("metadata"),
        )

        db.session.add(recurring_payment)
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Recurring payment created successfully",
                    "recurring_payment": recurring_payment.to_dict(),
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return (
            jsonify({"error": "Failed to create recurring payment", "details": str(e)}),
            500,
        )


# Exchange Rate Routes
@user_bp.route("/exchange-rates", methods=["GET"])
def get_exchange_rates():
    """Get current exchange rates"""
    try:
        base_currency = request.args.get("base", "USD")
        target_currency = request.args.get("target")

        query = ExchangeRate.query.filter_by(base_currency=base_currency)

        if target_currency:
            query = query.filter_by(target_currency=target_currency)

        # Get latest rates
        rates = (
            query.filter(ExchangeRate.valid_from <= datetime.utcnow())
            .order_by(ExchangeRate.valid_from.desc())
            .all()
        )

        # Remove duplicates, keeping only the latest for each currency pair
        unique_rates = {}
        for rate in rates:
            key = f"{rate.base_currency}_{rate.target_currency}"
            if key not in unique_rates:
                unique_rates[key] = rate

        return (
            jsonify(
                {
                    "exchange_rates": [
                        rate.to_dict() for rate in unique_rates.values()
                    ],
                    "base_currency": base_currency,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify({"error": "Failed to get exchange rates", "details": str(e)}),
            500,
        )


@user_bp.route("/exchange-rates/convert", methods=["POST"])
def convert_currency():
    """Convert amount between currencies"""
    try:
        data = request.get_json()

        required_fields = ["amount", "from_currency", "to_currency"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400

        amount = Decimal(str(data["amount"]))
        from_currency = data["from_currency"].upper()
        to_currency = data["to_currency"].upper()

        if from_currency == to_currency:
            return (
                jsonify(
                    {
                        "original_amount": float(amount),
                        "converted_amount": float(amount),
                        "from_currency": from_currency,
                        "to_currency": to_currency,
                        "exchange_rate": 1.0,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ),
                200,
            )

        # Get exchange rate
        exchange_rate = (
            ExchangeRate.query.filter_by(
                base_currency=from_currency, target_currency=to_currency
            )
            .filter(ExchangeRate.valid_from <= datetime.utcnow())
            .order_by(ExchangeRate.valid_from.desc())
            .first()
        )

        if not exchange_rate:
            # Try reverse rate
            reverse_rate = (
                ExchangeRate.query.filter_by(
                    base_currency=to_currency, target_currency=from_currency
                )
                .filter(ExchangeRate.valid_from <= datetime.utcnow())
                .order_by(ExchangeRate.valid_from.desc())
                .first()
            )

            if reverse_rate:
                rate = Decimal("1") / reverse_rate.rate
            else:
                return jsonify({"error": "Exchange rate not available"}), 404
        else:
            rate = exchange_rate.rate

        converted_amount = amount * rate

        return (
            jsonify(
                {
                    "original_amount": float(amount),
                    "converted_amount": float(converted_amount),
                    "from_currency": from_currency,
                    "to_currency": to_currency,
                    "exchange_rate": float(rate),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": "Failed to convert currency", "details": str(e)}), 500


# Analytics Routes
@user_bp.route("/analytics/summary", methods=["GET"])
@require_user_id
def get_payment_analytics():
    """Get payment analytics summary"""
    try:
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        if not start_date or not end_date:
            # Default to last 30 days
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        # Get transaction summary
        transactions = Transaction.query.filter(
            Transaction.user_id == request.user_id,
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date,
            Transaction.status == "completed",
        ).all()

        total_volume = sum(t.amount for t in transactions)
        total_fees = sum(t.fees for t in transactions)
        transaction_count = len(transactions)

        # Group by transaction type
        by_type = {}
        for transaction in transactions:
            if transaction.transaction_type not in by_type:
                by_type[transaction.transaction_type] = {
                    "count": 0,
                    "volume": Decimal("0"),
                    "fees": Decimal("0"),
                }
            by_type[transaction.transaction_type]["count"] += 1
            by_type[transaction.transaction_type]["volume"] += transaction.amount
            by_type[transaction.transaction_type]["fees"] += transaction.fees

        # Convert to serializable format
        for type_name in by_type:
            by_type[type_name]["volume"] = float(by_type[type_name]["volume"])
            by_type[type_name]["fees"] = float(by_type[type_name]["fees"])

        return (
            jsonify(
                {
                    "summary": {
                        "total_volume": float(total_volume),
                        "total_fees": float(total_fees),
                        "transaction_count": transaction_count,
                        "average_transaction": (
                            float(total_volume / transaction_count)
                            if transaction_count > 0
                            else 0
                        ),
                    },
                    "by_type": by_type,
                    "period": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": "Failed to get analytics", "details": str(e)}), 500


# Health check
@user_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "payment-service",
                "timestamp": datetime.utcnow().isoformat(),
            }
        ),
        200,
    )
