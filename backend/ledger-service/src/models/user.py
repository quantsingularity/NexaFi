from datetime import datetime
from typing import Any, Dict, Optional

from decimal import Decimal


class BaseModel:
    table_name = None
    db_manager = None

    def __init__(self, **kwargs) -> Any:
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def find_by_id(cls: Any, id_value: Any) -> Any:
        pass

    @classmethod
    def find_all(cls: Any, where_clause: str = "", params: tuple = ()) -> Any:
        pass

    @classmethod
    def find_one(cls: Any, where_clause: str, params: tuple = ()) -> Any:
        pass

    def save(self) -> Any:
        pass

    def delete(self) -> Any:
        pass

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}


class Account(BaseModel):
    table_name = "accounts"

    def get_balance(self, as_of_date: Optional[datetime] = None) -> Decimal:
        """Calculate account balance as of a specific date"""
        if as_of_date is None:
            return Decimal(str(self.current_balance))
        query = "\n        SELECT\n            COALESCE(SUM(debit_amount), 0) as total_debits,\n            COALESCE(SUM(credit_amount), 0) as total_credits\n        FROM journal_entry_lines jel\n        JOIN journal_entries je ON jel.journal_entry_id = je.id\n        WHERE jel.account_id = ? AND je.posting_date <= ? AND je.status = 'posted'\n        "
        return Decimal(str(self.current_balance))

    def to_dict(self) -> Any:
        data = super().to_dict()
        data["opening_balance"] = str(data.get("opening_balance", 0))
        data["current_balance"] = str(data.get("current_balance", 0))
        return data


class JournalEntry(BaseModel):
    table_name = "journal_entries"

    def to_dict(self, include_lines: Any = False) -> Any:
        data = super().to_dict()
        data["total_debit"] = str(data.get("total_debit", 0))
        data["total_credit"] = str(data.get("total_credit", 0))
        if include_lines:
            data["lines"] = []
        return data


class JournalEntryLine(BaseModel):
    table_name = "journal_entry_lines"

    def to_dict(self) -> Any:
        data = super().to_dict()
        data["debit_amount"] = str(data.get("debit_amount", 0))
        data["credit_amount"] = str(data.get("credit_amount", 0))
        return data


class ExchangeRate(BaseModel):
    table_name = "exchange_rates"

    def to_dict(self) -> Any:
        data = super().to_dict()
        data["rate"] = str(data.get("rate", 1.0))
        return data


class Reconciliation(BaseModel):
    table_name = "reconciliations"

    def to_dict(self) -> Any:
        data = super().to_dict()
        data["statement_balance"] = str(data.get("statement_balance", 0))
        data["book_balance"] = str(data.get("book_balance", 0))
        data["difference"] = str(data.get("difference", 0))
        return data


class FinancialPeriod(BaseModel):
    table_name = "financial_periods"

    def to_dict(self) -> Any:
        return super().to_dict()


class Budget(BaseModel):
    table_name = "budgets"

    def to_dict(self) -> Any:
        data = super().to_dict()
        data["budgeted_amount"] = str(data.get("budgeted_amount", 0))
        data["actual_amount"] = str(data.get("actual_amount", 0))
        data["variance"] = str(data.get("variance", 0))
        return data
