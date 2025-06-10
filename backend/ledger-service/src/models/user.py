from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from decimal import Decimal
import uuid

db = SQLAlchemy()

class Account(db.Model):
    __tablename__ = 'accounts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)
    account_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    account_name = db.Column(db.String(255), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)  # asset, liability, equity, revenue, expense
    account_subtype = db.Column(db.String(50))  # current_asset, fixed_asset, current_liability, etc.
    parent_account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'))
    normal_balance = db.Column(db.String(10), nullable=False)  # debit or credit
    is_active = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parent = db.relationship('Account', remote_side=[id], backref='children')
    journal_lines = db.relationship('JournalEntryLine', backref='account', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Account {self.account_code}: {self.account_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'account_code': self.account_code,
            'account_name': self.account_name,
            'account_type': self.account_type,
            'account_subtype': self.account_subtype,
            'parent_account_id': self.parent_account_id,
            'normal_balance': self.normal_balance,
            'is_active': self.is_active,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def get_balance(self, as_of_date=None):
        """Calculate account balance as of a specific date"""
        query = db.session.query(
            db.func.sum(JournalEntryLine.debit_amount).label('total_debits'),
            db.func.sum(JournalEntryLine.credit_amount).label('total_credits')
        ).join(JournalEntry).filter(
            JournalEntryLine.account_id == self.id,
            JournalEntry.status == 'posted'
        )
        
        if as_of_date:
            query = query.filter(JournalEntry.entry_date <= as_of_date)
        
        result = query.first()
        total_debits = result.total_debits or Decimal('0')
        total_credits = result.total_credits or Decimal('0')
        
        if self.normal_balance == 'debit':
            return total_debits - total_credits
        else:
            return total_credits - total_debits

class JournalEntry(db.Model):
    __tablename__ = 'journal_entries'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)
    entry_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    reference = db.Column(db.String(100))
    entry_date = db.Column(db.Date, nullable=False, index=True)
    total_amount = db.Column(db.Numeric(15, 2), nullable=False)
    status = db.Column(db.String(20), default='draft')  # draft, posted, reversed
    source_type = db.Column(db.String(50))  # manual, payment, invoice, etc.
    source_id = db.Column(db.String(36))
    created_by = db.Column(db.String(36))
    posted_by = db.Column(db.String(36))
    posted_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lines = db.relationship('JournalEntryLine', backref='journal_entry', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<JournalEntry {self.entry_number}: {self.description}>'

    def to_dict(self, include_lines=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'entry_number': self.entry_number,
            'description': self.description,
            'reference': self.reference,
            'entry_date': self.entry_date.isoformat() if self.entry_date else None,
            'total_amount': float(self.total_amount) if self.total_amount else 0,
            'status': self.status,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'created_by': self.created_by,
            'posted_by': self.posted_by,
            'posted_at': self.posted_at.isoformat() if self.posted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_lines:
            data['lines'] = [line.to_dict() for line in self.lines]
            
        return data

    def validate_entry(self):
        """Validate that debits equal credits"""
        total_debits = sum(line.debit_amount or Decimal('0') for line in self.lines)
        total_credits = sum(line.credit_amount or Decimal('0') for line in self.lines)
        
        return total_debits == total_credits and total_debits > 0

class JournalEntryLine(db.Model):
    __tablename__ = 'journal_entry_lines'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    journal_entry_id = db.Column(db.String(36), db.ForeignKey('journal_entries.id'), nullable=False)
    account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'), nullable=False)
    description = db.Column(db.Text)
    debit_amount = db.Column(db.Numeric(15, 2), default=Decimal('0'))
    credit_amount = db.Column(db.Numeric(15, 2), default=Decimal('0'))
    line_number = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<JournalEntryLine {self.line_number}: Dr {self.debit_amount} Cr {self.credit_amount}>'

    def to_dict(self):
        return {
            'id': self.id,
            'journal_entry_id': self.journal_entry_id,
            'account_id': self.account_id,
            'account_code': self.account.account_code if self.account else None,
            'account_name': self.account.account_name if self.account else None,
            'description': self.description,
            'debit_amount': float(self.debit_amount) if self.debit_amount else 0,
            'credit_amount': float(self.credit_amount) if self.credit_amount else 0,
            'line_number': self.line_number,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class FinancialPeriod(db.Model):
    __tablename__ = 'financial_periods'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)
    period_name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    period_type = db.Column(db.String(20), nullable=False)  # monthly, quarterly, yearly
    status = db.Column(db.String(20), default='open')  # open, closed
    fiscal_year = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<FinancialPeriod {self.period_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'period_name': self.period_name,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'period_type': self.period_type,
            'status': self.status,
            'fiscal_year': self.fiscal_year,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Budget(db.Model):
    __tablename__ = 'budgets'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)
    account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'), nullable=False)
    period_id = db.Column(db.String(36), db.ForeignKey('financial_periods.id'), nullable=False)
    budgeted_amount = db.Column(db.Numeric(15, 2), nullable=False)
    actual_amount = db.Column(db.Numeric(15, 2), default=Decimal('0'))
    variance = db.Column(db.Numeric(15, 2), default=Decimal('0'))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    account = db.relationship('Account', backref='budgets')
    period = db.relationship('FinancialPeriod', backref='budgets')

    def __repr__(self):
        return f'<Budget {self.account.account_name}: {self.budgeted_amount}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'account_id': self.account_id,
            'account_code': self.account.account_code if self.account else None,
            'account_name': self.account.account_name if self.account else None,
            'period_id': self.period_id,
            'period_name': self.period.period_name if self.period else None,
            'budgeted_amount': float(self.budgeted_amount) if self.budgeted_amount else 0,
            'actual_amount': float(self.actual_amount) if self.actual_amount else 0,
            'variance': float(self.variance) if self.variance else 0,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

