import json
import uuid
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class CreditScoreModel(db.Model):
    __tablename__ = "credit_score_models"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    version = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)

    # Model configuration
    model_type = db.Column(
        db.String(50), default="xgboost"
    )  # xgboost, random_forest, neural_network
    features = db.Column(db.Text)  # JSON array of feature names
    weights = db.Column(db.Text)  # JSON feature weights
    thresholds = db.Column(db.Text)  # JSON score thresholds

    # Model performance
    accuracy = db.Column(db.Float)
    precision = db.Column(db.Float)
    recall = db.Column(db.Float)
    f1_score = db.Column(db.Float)

    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    scores = db.relationship(
        "CreditScore", backref="model", cascade="all, delete-orphan"
    )

    def get_features(self):
        return json.loads(self.features) if self.features else []

    def set_features(self, features_list):
        self.features = json.dumps(features_list)

    def get_weights(self):
        return json.loads(self.weights) if self.weights else {}

    def set_weights(self, weights_dict):
        self.weights = json.dumps(weights_dict)

    def get_thresholds(self):
        return json.loads(self.thresholds) if self.thresholds else {}

    def set_thresholds(self, thresholds_dict):
        self.thresholds = json.dumps(thresholds_dict)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "model_type": self.model_type,
            "features": self.get_features(),
            "weights": self.get_weights(),
            "thresholds": self.get_thresholds(),
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class CreditScore(db.Model):
    __tablename__ = "credit_scores"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)
    model_id = db.Column(
        db.String(36), db.ForeignKey("credit_score_models.id"), nullable=False
    )

    # Score details
    score = db.Column(db.Integer, nullable=False)  # 300-850 range
    grade = db.Column(db.String(10))  # A+, A, B+, B, C+, C, D, F
    risk_level = db.Column(db.String(20))  # very_low, low, medium, high, very_high

    # Score components
    payment_history_score = db.Column(db.Float)
    credit_utilization_score = db.Column(db.Float)
    length_of_history_score = db.Column(db.Float)
    credit_mix_score = db.Column(db.Float)
    new_credit_score = db.Column(db.Float)

    # Financial factors
    debt_to_income_ratio = db.Column(db.Float)
    annual_income = db.Column(db.Float)
    total_debt = db.Column(db.Float)
    available_credit = db.Column(db.Float)

    # Business factors (if applicable)
    business_revenue = db.Column(db.Float)
    business_age_months = db.Column(db.Integer)
    industry_risk_factor = db.Column(db.Float)

    # Calculation metadata
    input_features = db.Column(db.Text)  # JSON input data used
    calculation_details = db.Column(db.Text)  # JSON detailed breakdown
    confidence_score = db.Column(db.Float)  # Model confidence 0-1

    # Validity
    expires_at = db.Column(db.DateTime)
    is_current = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_input_features(self):
        return json.loads(self.input_features) if self.input_features else {}

    def set_input_features(self, features):
        self.input_features = json.dumps(features)

    def get_calculation_details(self):
        return json.loads(self.calculation_details) if self.calculation_details else {}

    def set_calculation_details(self, details):
        self.calculation_details = json.dumps(details)

    def is_expired(self):
        return self.expires_at and datetime.utcnow() > self.expires_at

    def calculate_grade(self):
        """Calculate letter grade based on score"""
        if self.score >= 800:
            return "A+"
        elif self.score >= 750:
            return "A"
        elif self.score >= 700:
            return "B+"
        elif self.score >= 650:
            return "B"
        elif self.score >= 600:
            return "C+"
        elif self.score >= 550:
            return "C"
        elif self.score >= 500:
            return "D"
        else:
            return "F"

    def calculate_risk_level(self):
        """Calculate risk level based on score"""
        if self.score >= 750:
            return "very_low"
        elif self.score >= 700:
            return "low"
        elif self.score >= 650:
            return "medium"
        elif self.score >= 600:
            return "high"
        else:
            return "very_high"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "model_id": self.model_id,
            "score": self.score,
            "grade": self.grade,
            "risk_level": self.risk_level,
            "payment_history_score": self.payment_history_score,
            "credit_utilization_score": self.credit_utilization_score,
            "length_of_history_score": self.length_of_history_score,
            "credit_mix_score": self.credit_mix_score,
            "new_credit_score": self.new_credit_score,
            "debt_to_income_ratio": self.debt_to_income_ratio,
            "annual_income": self.annual_income,
            "total_debt": self.total_debt,
            "available_credit": self.available_credit,
            "business_revenue": self.business_revenue,
            "business_age_months": self.business_age_months,
            "industry_risk_factor": self.industry_risk_factor,
            "input_features": self.get_input_features(),
            "calculation_details": self.get_calculation_details(),
            "confidence_score": self.confidence_score,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_current": self.is_current,
            "is_expired": self.is_expired(),
            "created_at": self.created_at.isoformat(),
        }


class LoanApplication(db.Model):
    __tablename__ = "loan_applications"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)

    # Application details
    loan_type = db.Column(
        db.String(50), nullable=False
    )  # personal, business, mortgage, auto
    requested_amount = db.Column(db.Float, nullable=False)
    purpose = db.Column(db.String(200))
    term_months = db.Column(db.Integer)

    # Applicant information
    applicant_data = db.Column(db.Text)  # JSON applicant details
    financial_data = db.Column(db.Text)  # JSON financial information
    business_data = db.Column(db.Text)  # JSON business information (if applicable)

    # Application status
    status = db.Column(
        db.String(20), default="pending"
    )  # pending, approved, rejected, withdrawn
    decision_date = db.Column(db.DateTime)
    decision_reason = db.Column(db.Text)

    # Risk assessment
    credit_score_id = db.Column(db.String(36))
    risk_assessment = db.Column(db.Text)  # JSON risk analysis
    approval_probability = db.Column(db.Float)

    # Loan terms (if approved)
    approved_amount = db.Column(db.Float)
    interest_rate = db.Column(db.Float)
    monthly_payment = db.Column(db.Float)
    total_interest = db.Column(db.Float)

    # Processing
    assigned_to = db.Column(db.String(36))  # User ID of loan officer
    priority = db.Column(db.String(20), default="normal")  # low, normal, high, urgent

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    documents = db.relationship(
        "LoanDocument", backref="application", cascade="all, delete-orphan"
    )
    history = db.relationship(
        "LoanApplicationHistory", backref="application", cascade="all, delete-orphan"
    )

    def get_applicant_data(self):
        return json.loads(self.applicant_data) if self.applicant_data else {}

    def set_applicant_data(self, data):
        self.applicant_data = json.dumps(data)

    def get_financial_data(self):
        return json.loads(self.financial_data) if self.financial_data else {}

    def set_financial_data(self, data):
        self.financial_data = json.dumps(data)

    def get_business_data(self):
        return json.loads(self.business_data) if self.business_data else {}

    def set_business_data(self, data):
        self.business_data = json.dumps(data)

    def get_risk_assessment(self):
        return json.loads(self.risk_assessment) if self.risk_assessment else {}

    def set_risk_assessment(self, assessment):
        self.risk_assessment = json.dumps(assessment)

    def calculate_monthly_payment(self):
        """Calculate monthly payment based on approved terms"""
        if self.approved_amount and self.interest_rate and self.term_months:
            monthly_rate = self.interest_rate / 100 / 12
            if monthly_rate == 0:
                return self.approved_amount / self.term_months

            payment = (
                self.approved_amount
                * (monthly_rate * (1 + monthly_rate) ** self.term_months)
                / ((1 + monthly_rate) ** self.term_months - 1)
            )
            return round(payment, 2)
        return None

    def calculate_total_interest(self):
        """Calculate total interest over loan term"""
        if self.monthly_payment and self.term_months and self.approved_amount:
            total_payments = self.monthly_payment * self.term_months
            return round(total_payments - self.approved_amount, 2)
        return None

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "loan_type": self.loan_type,
            "requested_amount": self.requested_amount,
            "purpose": self.purpose,
            "term_months": self.term_months,
            "applicant_data": self.get_applicant_data(),
            "financial_data": self.get_financial_data(),
            "business_data": self.get_business_data(),
            "status": self.status,
            "decision_date": (
                self.decision_date.isoformat() if self.decision_date else None
            ),
            "decision_reason": self.decision_reason,
            "credit_score_id": self.credit_score_id,
            "risk_assessment": self.get_risk_assessment(),
            "approval_probability": self.approval_probability,
            "approved_amount": self.approved_amount,
            "interest_rate": self.interest_rate,
            "monthly_payment": self.monthly_payment,
            "total_interest": self.total_interest,
            "assigned_to": self.assigned_to,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class Loan(db.Model):
    __tablename__ = "loans"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = db.Column(db.String(36), nullable=False, index=True)
    user_id = db.Column(db.String(36), nullable=False, index=True)

    # Loan details
    loan_number = db.Column(db.String(50), unique=True, nullable=False)
    loan_type = db.Column(db.String(50), nullable=False)
    principal_amount = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, nullable=False)
    term_months = db.Column(db.Integer, nullable=False)
    monthly_payment = db.Column(db.Float, nullable=False)

    # Loan status
    status = db.Column(
        db.String(20), default="active"
    )  # active, paid_off, defaulted, closed
    disbursement_date = db.Column(db.DateTime)
    first_payment_date = db.Column(db.DateTime)
    maturity_date = db.Column(db.DateTime)

    # Current balances
    current_balance = db.Column(db.Float)
    principal_balance = db.Column(db.Float)
    interest_balance = db.Column(db.Float)
    fees_balance = db.Column(db.Float)

    # Payment tracking
    total_payments_made = db.Column(db.Float, default=0)
    payments_count = db.Column(db.Integer, default=0)
    last_payment_date = db.Column(db.DateTime)
    next_payment_date = db.Column(db.DateTime)

    # Delinquency tracking
    days_past_due = db.Column(db.Integer, default=0)
    late_fees = db.Column(db.Float, default=0)
    is_delinquent = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    payments = db.relationship(
        "LoanPayment", backref="loan", cascade="all, delete-orphan"
    )

    def calculate_remaining_balance(self):
        """Calculate remaining loan balance"""
        return self.principal_balance + self.interest_balance + self.fees_balance

    def calculate_payoff_amount(self):
        """Calculate amount needed to pay off loan"""
        # This would include any prepayment penalties, accrued interest, etc.
        return self.calculate_remaining_balance()

    def update_delinquency_status(self):
        """Update delinquency status based on payment history"""
        if self.next_payment_date and datetime.utcnow() > self.next_payment_date:
            self.days_past_due = (datetime.utcnow() - self.next_payment_date).days
            self.is_delinquent = self.days_past_due > 0
        else:
            self.days_past_due = 0
            self.is_delinquent = False

    def to_dict(self):
        return {
            "id": self.id,
            "application_id": self.application_id,
            "user_id": self.user_id,
            "loan_number": self.loan_number,
            "loan_type": self.loan_type,
            "principal_amount": self.principal_amount,
            "interest_rate": self.interest_rate,
            "term_months": self.term_months,
            "monthly_payment": self.monthly_payment,
            "status": self.status,
            "disbursement_date": (
                self.disbursement_date.isoformat() if self.disbursement_date else None
            ),
            "first_payment_date": (
                self.first_payment_date.isoformat() if self.first_payment_date else None
            ),
            "maturity_date": (
                self.maturity_date.isoformat() if self.maturity_date else None
            ),
            "current_balance": self.current_balance,
            "principal_balance": self.principal_balance,
            "interest_balance": self.interest_balance,
            "fees_balance": self.fees_balance,
            "remaining_balance": self.calculate_remaining_balance(),
            "payoff_amount": self.calculate_payoff_amount(),
            "total_payments_made": self.total_payments_made,
            "payments_count": self.payments_count,
            "last_payment_date": (
                self.last_payment_date.isoformat() if self.last_payment_date else None
            ),
            "next_payment_date": (
                self.next_payment_date.isoformat() if self.next_payment_date else None
            ),
            "days_past_due": self.days_past_due,
            "late_fees": self.late_fees,
            "is_delinquent": self.is_delinquent,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class LoanPayment(db.Model):
    __tablename__ = "loan_payments"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    loan_id = db.Column(db.String(36), db.ForeignKey("loans.id"), nullable=False)

    # Payment details
    payment_number = db.Column(db.Integer, nullable=False)
    payment_date = db.Column(db.DateTime, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)

    # Payment amounts
    total_amount = db.Column(db.Float, nullable=False)
    principal_amount = db.Column(db.Float, nullable=False)
    interest_amount = db.Column(db.Float, nullable=False)
    fees_amount = db.Column(db.Float, default=0)
    late_fee_amount = db.Column(db.Float, default=0)

    # Payment method and status
    payment_method = db.Column(db.String(50))  # ach, check, wire, online
    payment_status = db.Column(
        db.String(20), default="completed"
    )  # pending, completed, failed, reversed
    transaction_id = db.Column(db.String(100))

    # Balances after payment
    remaining_balance = db.Column(db.Float)
    principal_balance_after = db.Column(db.Float)
    interest_balance_after = db.Column(db.Float)

    # Metadata
    is_extra_payment = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_late(self):
        return self.payment_date > self.due_date

    def days_late(self):
        if self.is_late():
            return (self.payment_date - self.due_date).days
        return 0

    def to_dict(self):
        return {
            "id": self.id,
            "loan_id": self.loan_id,
            "payment_number": self.payment_number,
            "payment_date": self.payment_date.isoformat(),
            "due_date": self.due_date.isoformat(),
            "total_amount": self.total_amount,
            "principal_amount": self.principal_amount,
            "interest_amount": self.interest_amount,
            "fees_amount": self.fees_amount,
            "late_fee_amount": self.late_fee_amount,
            "payment_method": self.payment_method,
            "payment_status": self.payment_status,
            "transaction_id": self.transaction_id,
            "remaining_balance": self.remaining_balance,
            "principal_balance_after": self.principal_balance_after,
            "interest_balance_after": self.interest_balance_after,
            "is_extra_payment": self.is_extra_payment,
            "is_late": self.is_late(),
            "days_late": self.days_late(),
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }


class RiskAssessment(db.Model):
    __tablename__ = "risk_assessments"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)
    assessment_type = db.Column(
        db.String(50), nullable=False
    )  # credit, operational, market, liquidity

    # Assessment details
    risk_factors = db.Column(db.Text)  # JSON risk factors analyzed
    risk_scores = db.Column(db.Text)  # JSON individual risk scores
    overall_risk_score = db.Column(db.Float, nullable=False)
    risk_level = db.Column(
        db.String(20), nullable=False
    )  # very_low, low, medium, high, very_high

    # Recommendations
    recommendations = db.Column(db.Text)  # JSON recommendations
    mitigation_strategies = db.Column(db.Text)  # JSON mitigation strategies

    # Validity and metadata
    valid_until = db.Column(db.DateTime)
    confidence_level = db.Column(db.Float)
    data_sources = db.Column(db.Text)  # JSON data sources used

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_risk_factors(self):
        return json.loads(self.risk_factors) if self.risk_factors else {}

    def set_risk_factors(self, factors):
        self.risk_factors = json.dumps(factors)

    def get_risk_scores(self):
        return json.loads(self.risk_scores) if self.risk_scores else {}

    def set_risk_scores(self, scores):
        self.risk_scores = json.dumps(scores)

    def get_recommendations(self):
        return json.loads(self.recommendations) if self.recommendations else []

    def set_recommendations(self, recommendations):
        self.recommendations = json.dumps(recommendations)

    def get_mitigation_strategies(self):
        return (
            json.loads(self.mitigation_strategies) if self.mitigation_strategies else []
        )

    def set_mitigation_strategies(self, strategies):
        self.mitigation_strategies = json.dumps(strategies)

    def get_data_sources(self):
        return json.loads(self.data_sources) if self.data_sources else []

    def set_data_sources(self, sources):
        self.data_sources = json.dumps(sources)

    def is_expired(self):
        return self.valid_until and datetime.utcnow() > self.valid_until

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "assessment_type": self.assessment_type,
            "risk_factors": self.get_risk_factors(),
            "risk_scores": self.get_risk_scores(),
            "overall_risk_score": self.overall_risk_score,
            "risk_level": self.risk_level,
            "recommendations": self.get_recommendations(),
            "mitigation_strategies": self.get_mitigation_strategies(),
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "confidence_level": self.confidence_level,
            "data_sources": self.get_data_sources(),
            "is_expired": self.is_expired(),
            "created_at": self.created_at.isoformat(),
        }


class LoanDocument(db.Model):
    __tablename__ = "loan_documents"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = db.Column(
        db.String(36), db.ForeignKey("loan_applications.id"), nullable=False
    )

    # Document details
    document_type = db.Column(
        db.String(50), nullable=False
    )  # income_statement, bank_statement, tax_return, etc.
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))

    # Document status
    status = db.Column(db.String(20), default="pending")  # pending, verified, rejected
    verification_notes = db.Column(db.Text)
    verified_by = db.Column(db.String(36))  # User ID
    verified_at = db.Column(db.DateTime)

    # Extracted data (if applicable)
    extracted_data = db.Column(db.Text)  # JSON extracted information

    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_extracted_data(self):
        return json.loads(self.extracted_data) if self.extracted_data else {}

    def set_extracted_data(self, data):
        self.extracted_data = json.dumps(data)

    def to_dict(self):
        return {
            "id": self.id,
            "application_id": self.application_id,
            "document_type": self.document_type,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "status": self.status,
            "verification_notes": self.verification_notes,
            "verified_by": self.verified_by,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "extracted_data": self.get_extracted_data(),
            "uploaded_at": self.uploaded_at.isoformat(),
        }


class LoanApplicationHistory(db.Model):
    __tablename__ = "loan_application_history"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = db.Column(
        db.String(36), db.ForeignKey("loan_applications.id"), nullable=False
    )

    # Change details
    action = db.Column(db.String(100), nullable=False)
    old_status = db.Column(db.String(20))
    new_status = db.Column(db.String(20))
    notes = db.Column(db.Text)

    # User who made the change
    changed_by = db.Column(db.String(36))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "application_id": self.application_id,
            "action": self.action,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "notes": self.notes,
            "changed_by": self.changed_by,
            "created_at": self.created_at.isoformat(),
        }
