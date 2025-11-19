from datetime import date, datetime
from decimal import Decimal
from functools import wraps

from flask import Blueprint, jsonify, request
from src.models.user import Account, JournalEntry, JournalEntryLine, db

user_bp = Blueprint("ledger", __name__)


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


def generate_entry_number(user_id):
    """Generate unique journal entry number"""
    today = datetime.now()
    prefix = f"JE{today.strftime('%Y%m%d')}"

    # Find the last entry number for today
    last_entry = (
        JournalEntry.query.filter(
            JournalEntry.user_id == user_id,
            JournalEntry.entry_number.like(f"{prefix}%"),
        )
        .order_by(JournalEntry.entry_number.desc())
        .first()
    )

    if last_entry:
        # Extract sequence number and increment
        seq = int(last_entry.entry_number[-4:]) + 1
    else:
        seq = 1

    return f"{prefix}{seq:04d}"


def create_default_chart_of_accounts(user_id):
    """Create default chart of accounts for new user"""
    default_accounts = [
        # Assets
        {
            "code": "1000",
            "name": "Cash and Cash Equivalents",
            "type": "asset",
            "subtype": "current_asset",
            "normal_balance": "debit",
        },
        {
            "code": "1100",
            "name": "Accounts Receivable",
            "type": "asset",
            "subtype": "current_asset",
            "normal_balance": "debit",
        },
        {
            "code": "1200",
            "name": "Inventory",
            "type": "asset",
            "subtype": "current_asset",
            "normal_balance": "debit",
        },
        {
            "code": "1300",
            "name": "Prepaid Expenses",
            "type": "asset",
            "subtype": "current_asset",
            "normal_balance": "debit",
        },
        {
            "code": "1500",
            "name": "Property, Plant & Equipment",
            "type": "asset",
            "subtype": "fixed_asset",
            "normal_balance": "debit",
        },
        {
            "code": "1600",
            "name": "Accumulated Depreciation",
            "type": "asset",
            "subtype": "fixed_asset",
            "normal_balance": "credit",
        },
        # Liabilities
        {
            "code": "2000",
            "name": "Accounts Payable",
            "type": "liability",
            "subtype": "current_liability",
            "normal_balance": "credit",
        },
        {
            "code": "2100",
            "name": "Accrued Expenses",
            "type": "liability",
            "subtype": "current_liability",
            "normal_balance": "credit",
        },
        {
            "code": "2200",
            "name": "Short-term Debt",
            "type": "liability",
            "subtype": "current_liability",
            "normal_balance": "credit",
        },
        {
            "code": "2500",
            "name": "Long-term Debt",
            "type": "liability",
            "subtype": "long_term_liability",
            "normal_balance": "credit",
        },
        # Equity
        {
            "code": "3000",
            "name": "Owner's Equity",
            "type": "equity",
            "subtype": "capital",
            "normal_balance": "credit",
        },
        {
            "code": "3100",
            "name": "Retained Earnings",
            "type": "equity",
            "subtype": "retained_earnings",
            "normal_balance": "credit",
        },
        # Revenue
        {
            "code": "4000",
            "name": "Sales Revenue",
            "type": "revenue",
            "subtype": "operating_revenue",
            "normal_balance": "credit",
        },
        {
            "code": "4100",
            "name": "Service Revenue",
            "type": "revenue",
            "subtype": "operating_revenue",
            "normal_balance": "credit",
        },
        {
            "code": "4900",
            "name": "Other Income",
            "type": "revenue",
            "subtype": "non_operating_revenue",
            "normal_balance": "credit",
        },
        # Expenses
        {
            "code": "5000",
            "name": "Cost of Goods Sold",
            "type": "expense",
            "subtype": "cost_of_sales",
            "normal_balance": "debit",
        },
        {
            "code": "6000",
            "name": "Salaries and Wages",
            "type": "expense",
            "subtype": "operating_expense",
            "normal_balance": "debit",
        },
        {
            "code": "6100",
            "name": "Rent Expense",
            "type": "expense",
            "subtype": "operating_expense",
            "normal_balance": "debit",
        },
        {
            "code": "6200",
            "name": "Utilities Expense",
            "type": "expense",
            "subtype": "operating_expense",
            "normal_balance": "debit",
        },
        {
            "code": "6300",
            "name": "Marketing Expense",
            "type": "expense",
            "subtype": "operating_expense",
            "normal_balance": "debit",
        },
        {
            "code": "6400",
            "name": "Office Supplies",
            "type": "expense",
            "subtype": "operating_expense",
            "normal_balance": "debit",
        },
        {
            "code": "6500",
            "name": "Professional Services",
            "type": "expense",
            "subtype": "operating_expense",
            "normal_balance": "debit",
        },
        {
            "code": "6600",
            "name": "Insurance Expense",
            "type": "expense",
            "subtype": "operating_expense",
            "normal_balance": "debit",
        },
        {
            "code": "6700",
            "name": "Depreciation Expense",
            "type": "expense",
            "subtype": "operating_expense",
            "normal_balance": "debit",
        },
        {
            "code": "6800",
            "name": "Interest Expense",
            "type": "expense",
            "subtype": "non_operating_expense",
            "normal_balance": "debit",
        },
    ]

    for account_data in default_accounts:
        account = Account(
            user_id=user_id,
            account_code=account_data["code"],
            account_name=account_data["name"],
            account_type=account_data["type"],
            account_subtype=account_data["subtype"],
            normal_balance=account_data["normal_balance"],
            description=f"Default {account_data['name']} account",
        )
        db.session.add(account)

    db.session.commit()


# Account Management Routes
@user_bp.route("/accounts", methods=["GET"])
@require_user_id
def get_accounts():
    """Get all accounts for user"""
    try:
        account_type = request.args.get("type")
        is_active = request.args.get("active", "true").lower() == "true"

        query = Account.query.filter_by(user_id=request.user_id, is_active=is_active)

        if account_type:
            query = query.filter_by(account_type=account_type)

        accounts = query.order_by(Account.account_code).all()

        return (
            jsonify(
                {
                    "accounts": [account.to_dict() for account in accounts],
                    "total": len(accounts),
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": "Failed to get accounts", "details": str(e)}), 500


@user_bp.route("/accounts", methods=["POST"])
@require_user_id
def create_account():
    """Create new account"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = [
            "account_code",
            "account_name",
            "account_type",
            "normal_balance",
        ]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400

        # Check if account code already exists
        existing_account = Account.query.filter_by(
            user_id=request.user_id, account_code=data["account_code"]
        ).first()

        if existing_account:
            return jsonify({"error": "Account code already exists"}), 409

        # Create account
        account = Account(
            user_id=request.user_id,
            account_code=data["account_code"],
            account_name=data["account_name"],
            account_type=data["account_type"],
            account_subtype=data.get("account_subtype"),
            parent_account_id=data.get("parent_account_id"),
            normal_balance=data["normal_balance"],
            description=data.get("description"),
        )

        db.session.add(account)
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Account created successfully",
                    "account": account.to_dict(),
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create account", "details": str(e)}), 500


@user_bp.route("/accounts/<account_id>", methods=["GET"])
@require_user_id
def get_account(account_id):
    """Get specific account"""
    try:
        account = Account.query.filter_by(
            id=account_id, user_id=request.user_id
        ).first()

        if not account:
            return jsonify({"error": "Account not found"}), 404

        # Get account balance
        balance = account.get_balance()

        account_data = account.to_dict()
        account_data["balance"] = float(balance)

        return jsonify({"account": account_data}), 200

    except Exception as e:
        return jsonify({"error": "Failed to get account", "details": str(e)}), 500


@user_bp.route("/accounts/<account_id>", methods=["PUT"])
@require_user_id
def update_account(account_id):
    """Update account"""
    try:
        account = Account.query.filter_by(
            id=account_id, user_id=request.user_id
        ).first()

        if not account:
            return jsonify({"error": "Account not found"}), 404

        data = request.get_json()

        # Update fields
        updatable_fields = [
            "account_name",
            "account_type",
            "account_subtype",
            "description",
            "is_active",
        ]
        for field in updatable_fields:
            if field in data:
                setattr(account, field, data[field])

        account.updated_at = datetime.utcnow()
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Account updated successfully",
                    "account": account.to_dict(),
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update account", "details": str(e)}), 500


# Journal Entry Routes
@user_bp.route("/journal-entries", methods=["GET"])
@require_user_id
def get_journal_entries():
    """Get journal entries for user"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        status = request.args.get("status")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        query = JournalEntry.query.filter_by(user_id=request.user_id)

        if status:
            query = query.filter_by(status=status)

        if start_date:
            query = query.filter(
                JournalEntry.entry_date
                >= datetime.strptime(start_date, "%Y-%m-%d").date()
            )

        if end_date:
            query = query.filter(
                JournalEntry.entry_date
                <= datetime.strptime(end_date, "%Y-%m-%d").date()
            )

        entries = query.order_by(
            JournalEntry.entry_date.desc(), JournalEntry.entry_number.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

        return (
            jsonify(
                {
                    "journal_entries": [
                        entry.to_dict(include_lines=True) for entry in entries.items
                    ],
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": entries.total,
                        "pages": entries.pages,
                        "has_next": entries.has_next,
                        "has_prev": entries.has_prev,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify({"error": "Failed to get journal entries", "details": str(e)}),
            500,
        )


@user_bp.route("/journal-entries", methods=["POST"])
@require_user_id
def create_journal_entry():
    """Create new journal entry"""
    try:
        data = request.get_json()

        # Validate required fields
        if not data.get("description") or not data.get("lines"):
            return jsonify({"error": "Description and lines are required"}), 400

        if len(data["lines"]) < 2:
            return jsonify({"error": "At least two lines are required"}), 400

        # Create journal entry
        entry = JournalEntry(
            user_id=request.user_id,
            entry_number=generate_entry_number(request.user_id),
            description=data["description"],
            reference=data.get("reference"),
            entry_date=datetime.strptime(
                data.get("entry_date", datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d"
            ).date(),
            source_type=data.get("source_type", "manual"),
            source_id=data.get("source_id"),
            created_by=request.user_id,
        )

        db.session.add(entry)
        db.session.flush()  # Get the ID

        # Create journal entry lines
        total_debits = Decimal("0")
        total_credits = Decimal("0")

        for i, line_data in enumerate(data["lines"]):
            if not line_data.get("account_id"):
                return jsonify({"error": f"Account ID is required for line {i+1}"}), 400

            # Verify account exists and belongs to user
            account = Account.query.filter_by(
                id=line_data["account_id"], user_id=request.user_id
            ).first()

            if not account:
                return jsonify({"error": f"Invalid account ID for line {i+1}"}), 400

            debit_amount = Decimal(str(line_data.get("debit_amount", 0)))
            credit_amount = Decimal(str(line_data.get("credit_amount", 0)))

            if debit_amount == 0 and credit_amount == 0:
                return (
                    jsonify(
                        {
                            "error": f"Either debit or credit amount is required for line {i+1}"
                        }
                    ),
                    400,
                )

            if debit_amount > 0 and credit_amount > 0:
                return (
                    jsonify(
                        {
                            "error": f"Line {i+1} cannot have both debit and credit amounts"
                        }
                    ),
                    400,
                )

            line = JournalEntryLine(
                journal_entry_id=entry.id,
                account_id=line_data["account_id"],
                description=line_data.get("description"),
                debit_amount=debit_amount,
                credit_amount=credit_amount,
                line_number=i + 1,
            )

            db.session.add(line)
            total_debits += debit_amount
            total_credits += credit_amount

        # Validate that debits equal credits
        if total_debits != total_credits:
            return jsonify({"error": "Total debits must equal total credits"}), 400

        entry.total_amount = total_debits

        # Auto-post if requested
        if data.get("auto_post", False):
            entry.status = "posted"
            entry.posted_by = request.user_id
            entry.posted_at = datetime.utcnow()

        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Journal entry created successfully",
                    "journal_entry": entry.to_dict(include_lines=True),
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return (
            jsonify({"error": "Failed to create journal entry", "details": str(e)}),
            500,
        )


@user_bp.route("/journal-entries/<entry_id>/post", methods=["POST"])
@require_user_id
def post_journal_entry(entry_id):
    """Post a journal entry"""
    try:
        entry = JournalEntry.query.filter_by(
            id=entry_id, user_id=request.user_id
        ).first()

        if not entry:
            return jsonify({"error": "Journal entry not found"}), 404

        if entry.status != "draft":
            return jsonify({"error": "Only draft entries can be posted"}), 400

        # Validate entry
        if not entry.validate_entry():
            return (
                jsonify(
                    {"error": "Entry validation failed - debits must equal credits"}
                ),
                400,
            )

        # Post entry
        entry.status = "posted"
        entry.posted_by = request.user_id
        entry.posted_at = datetime.utcnow()

        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Journal entry posted successfully",
                    "journal_entry": entry.to_dict(include_lines=True),
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return (
            jsonify({"error": "Failed to post journal entry", "details": str(e)}),
            500,
        )


# Financial Reports
@user_bp.route("/reports/trial-balance", methods=["GET"])
@require_user_id
def get_trial_balance():
    """Generate trial balance report"""
    try:
        as_of_date = request.args.get("as_of_date")
        if as_of_date:
            as_of_date = datetime.strptime(as_of_date, "%Y-%m-%d").date()
        else:
            as_of_date = date.today()

        accounts = (
            Account.query.filter_by(user_id=request.user_id, is_active=True)
            .order_by(Account.account_code)
            .all()
        )

        trial_balance = []
        total_debits = Decimal("0")
        total_credits = Decimal("0")

        for account in accounts:
            balance = account.get_balance(as_of_date)

            if balance != 0:
                if account.normal_balance == "debit":
                    debit_balance = balance if balance > 0 else Decimal("0")
                    credit_balance = abs(balance) if balance < 0 else Decimal("0")
                else:
                    credit_balance = balance if balance > 0 else Decimal("0")
                    debit_balance = abs(balance) if balance < 0 else Decimal("0")

                trial_balance.append(
                    {
                        "account_code": account.account_code,
                        "account_name": account.account_name,
                        "account_type": account.account_type,
                        "debit_balance": float(debit_balance),
                        "credit_balance": float(credit_balance),
                    }
                )

                total_debits += debit_balance
                total_credits += credit_balance

        return (
            jsonify(
                {
                    "trial_balance": trial_balance,
                    "as_of_date": as_of_date.isoformat(),
                    "total_debits": float(total_debits),
                    "total_credits": float(total_credits),
                    "is_balanced": total_debits == total_credits,
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify({"error": "Failed to generate trial balance", "details": str(e)}),
            500,
        )


@user_bp.route("/reports/balance-sheet", methods=["GET"])
@require_user_id
def get_balance_sheet():
    """Generate balance sheet report"""
    try:
        as_of_date = request.args.get("as_of_date")
        if as_of_date:
            as_of_date = datetime.strptime(as_of_date, "%Y-%m-%d").date()
        else:
            as_of_date = date.today()

        # Get accounts by type
        assets = (
            Account.query.filter_by(
                user_id=request.user_id, account_type="asset", is_active=True
            )
            .order_by(Account.account_code)
            .all()
        )
        liabilities = (
            Account.query.filter_by(
                user_id=request.user_id, account_type="liability", is_active=True
            )
            .order_by(Account.account_code)
            .all()
        )
        equity = (
            Account.query.filter_by(
                user_id=request.user_id, account_type="equity", is_active=True
            )
            .order_by(Account.account_code)
            .all()
        )

        # Calculate balances
        asset_items = []
        total_assets = Decimal("0")

        for account in assets:
            balance = account.get_balance(as_of_date)
            if balance != 0:
                asset_items.append(
                    {
                        "account_code": account.account_code,
                        "account_name": account.account_name,
                        "account_subtype": account.account_subtype,
                        "balance": float(balance),
                    }
                )
                total_assets += balance

        liability_items = []
        total_liabilities = Decimal("0")

        for account in liabilities:
            balance = account.get_balance(as_of_date)
            if balance != 0:
                liability_items.append(
                    {
                        "account_code": account.account_code,
                        "account_name": account.account_name,
                        "account_subtype": account.account_subtype,
                        "balance": float(balance),
                    }
                )
                total_liabilities += balance

        equity_items = []
        total_equity = Decimal("0")

        for account in equity:
            balance = account.get_balance(as_of_date)
            if balance != 0:
                equity_items.append(
                    {
                        "account_code": account.account_code,
                        "account_name": account.account_name,
                        "account_subtype": account.account_subtype,
                        "balance": float(balance),
                    }
                )
                total_equity += balance

        return (
            jsonify(
                {
                    "balance_sheet": {
                        "assets": asset_items,
                        "liabilities": liability_items,
                        "equity": equity_items,
                    },
                    "totals": {
                        "total_assets": float(total_assets),
                        "total_liabilities": float(total_liabilities),
                        "total_equity": float(total_equity),
                        "total_liabilities_and_equity": float(
                            total_liabilities + total_equity
                        ),
                    },
                    "as_of_date": as_of_date.isoformat(),
                    "is_balanced": total_assets == (total_liabilities + total_equity),
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify({"error": "Failed to generate balance sheet", "details": str(e)}),
            500,
        )


@user_bp.route("/reports/income-statement", methods=["GET"])
@require_user_id
def get_income_statement():
    """Generate income statement report"""
    try:
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        if not start_date or not end_date:
            return jsonify({"error": "Start date and end date are required"}), 400

        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        # Get revenue and expense accounts
        revenue_accounts = (
            Account.query.filter_by(
                user_id=request.user_id, account_type="revenue", is_active=True
            )
            .order_by(Account.account_code)
            .all()
        )
        expense_accounts = (
            Account.query.filter_by(
                user_id=request.user_id, account_type="expense", is_active=True
            )
            .order_by(Account.account_code)
            .all()
        )

        # Calculate revenue
        revenue_items = []
        total_revenue = Decimal("0")

        for account in revenue_accounts:
            # Get balance for the period
            query = (
                db.session.query(
                    db.func.sum(
                        JournalEntryLine.credit_amount - JournalEntryLine.debit_amount
                    ).label("balance")
                )
                .join(JournalEntry)
                .filter(
                    JournalEntryLine.account_id == account.id,
                    JournalEntry.status == "posted",
                    JournalEntry.entry_date >= start_date,
                    JournalEntry.entry_date <= end_date,
                )
            )

            result = query.first()
            balance = result.balance or Decimal("0")

            if balance != 0:
                revenue_items.append(
                    {
                        "account_code": account.account_code,
                        "account_name": account.account_name,
                        "account_subtype": account.account_subtype,
                        "balance": float(balance),
                    }
                )
                total_revenue += balance

        # Calculate expenses
        expense_items = []
        total_expenses = Decimal("0")

        for account in expense_accounts:
            # Get balance for the period
            query = (
                db.session.query(
                    db.func.sum(
                        JournalEntryLine.debit_amount - JournalEntryLine.credit_amount
                    ).label("balance")
                )
                .join(JournalEntry)
                .filter(
                    JournalEntryLine.account_id == account.id,
                    JournalEntry.status == "posted",
                    JournalEntry.entry_date >= start_date,
                    JournalEntry.entry_date <= end_date,
                )
            )

            result = query.first()
            balance = result.balance or Decimal("0")

            if balance != 0:
                expense_items.append(
                    {
                        "account_code": account.account_code,
                        "account_name": account.account_name,
                        "account_subtype": account.account_subtype,
                        "balance": float(balance),
                    }
                )
                total_expenses += balance

        net_income = total_revenue - total_expenses

        return (
            jsonify(
                {
                    "income_statement": {
                        "revenue": revenue_items,
                        "expenses": expense_items,
                    },
                    "totals": {
                        "total_revenue": float(total_revenue),
                        "total_expenses": float(total_expenses),
                        "net_income": float(net_income),
                    },
                    "period": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify(
                {"error": "Failed to generate income statement", "details": str(e)}
            ),
            500,
        )


# Initialize default accounts
@user_bp.route("/accounts/initialize", methods=["POST"])
@require_user_id
def initialize_accounts():
    """Initialize default chart of accounts for user"""
    try:
        # Check if user already has accounts
        existing_accounts = Account.query.filter_by(user_id=request.user_id).count()

        if existing_accounts > 0:
            return jsonify({"error": "User already has accounts initialized"}), 409

        create_default_chart_of_accounts(request.user_id)

        return (
            jsonify({"message": "Default chart of accounts created successfully"}),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return (
            jsonify({"error": "Failed to initialize accounts", "details": str(e)}),
            500,
        )


# Health check
@user_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "ledger-service",
                "timestamp": datetime.utcnow().isoformat(),
            }
        ),
        200,
    )
