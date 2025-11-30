from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional


# Placeholder for BaseModel. The actual BaseModel is set in main.py
class BaseModel:
    table_name = None
    db_manager = None

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def find_by_id(cls, id_value: Any):
        # Placeholder for actual implementation
        pass

    @classmethod
    def find_all(cls, where_clause: str = "", params: tuple = ()):
        # Placeholder for actual implementation
        pass

    @classmethod
    def find_one(cls, where_clause: str, params: tuple = ()):
        # Placeholder for actual implementation
        pass

    def save(self):
        # Placeholder for actual implementation
        pass

    def delete(self):
        # Placeholder for actual implementation
        pass

    def to_dict(self) -> Dict[str, Any]:
        # Placeholder for actual implementation
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}


class Account(BaseModel):
    table_name = "accounts"

    def get_balance(self, as_of_date: Optional[datetime] = None) -> Decimal:
        """Calculate account balance as of a specific date"""
        if as_of_date is None:
            return Decimal(str(self.current_balance))

        # Calculate balance from journal entries up to the date
        query = """
        SELECT
            COALESCE(SUM(debit_amount), 0) as total_debits,
            COALESCE(SUM(credit_amount), 0) as total_credits
        FROM journal_entry_lines jel
        JOIN journal_entries je ON jel.journal_entry_id = je.id
        WHERE jel.account_id = ? AND je.posting_date <= ? AND je.status = 'posted'
        """

        # Note: The main.py file already contains a full implementation of Account.get_balance
        # that uses the custom db_manager. We will rely on that implementation being present
        # in the final main.py, and keep this model file clean.
        # For now, we'll return the current balance as a placeholder.
        return Decimal(str(self.current_balance))

    def to_dict(self):
        data = super().to_dict()
        # Convert Decimal/float to string for JSON serialization
        data["opening_balance"] = str(data.get("opening_balance", 0))
        data["current_balance"] = str(data.get("current_balance", 0))
        return data


class JournalEntry(BaseModel):
    table_name = "journal_entries"

    def to_dict(self, include_lines=False):
        data = super().to_dict()
        # Convert Decimal/float to string for JSON serialization
        data["total_debit"] = str(data.get("total_debit", 0))
        data["total_credit"] = str(data.get("total_credit", 0))

        if include_lines:
            # In a real scenario, we'd fetch lines here, but for now, we rely on the main.py logic
            data["lines"] = []

        return data


class JournalEntryLine(BaseModel):
    table_name = "journal_entry_lines"

    def to_dict(self):
        data = super().to_dict()
        # Convert Decimal/float to string for JSON serialization
        data["debit_amount"] = str(data.get("debit_amount", 0))
        data["credit_amount"] = str(data.get("credit_amount", 0))
        return data


class ExchangeRate(BaseModel):
    table_name = "exchange_rates"

    def to_dict(self):
        data = super().to_dict()
        data["rate"] = str(data.get("rate", 1.0))
        return data


class Reconciliation(BaseModel):
    table_name = "reconciliations"

    def to_dict(self):
        data = super().to_dict()
        data["statement_balance"] = str(data.get("statement_balance", 0))
        data["book_balance"] = str(data.get("book_balance", 0))
        data["difference"] = str(data.get("difference", 0))
        return data


class FinancialPeriod(BaseModel):
    table_name = "financial_periods"

    def to_dict(self):
        return super().to_dict()


class Budget(BaseModel):
    table_name = "budgets"

    def to_dict(self):
        data = super().to_dict()
        data["budgeted_amount"] = str(data.get("budgeted_amount", 0))
        data["actual_amount"] = str(data.get("actual_amount", 0))
        data["variance"] = str(data.get("variance", 0))
        return data
