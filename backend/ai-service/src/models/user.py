import uuid
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class AIModel(db.Model):
    __tablename__ = "ai_models"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), unique=True, nullable=False)
    model_type = db.Column(
        db.String(50), nullable=False
    )  # cash_flow_forecast, credit_scoring, document_processing, etc.
    version = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)
    model_config = db.Column(db.JSON)  # Model configuration and hyperparameters
    training_data_info = db.Column(db.JSON)  # Information about training data
    performance_metrics = db.Column(db.JSON)  # Model performance metrics
    is_active = db.Column(db.Boolean, default=True)
    is_production = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    predictions = db.relationship(
        "AIPrediction", backref="model", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<AIModel {self.name} v{self.version}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "model_type": self.model_type,
            "version": self.version,
            "description": self.description,
            "model_config": self.model_config,
            "training_data_info": self.training_data_info,
            "performance_metrics": self.performance_metrics,
            "is_active": self.is_active,
            "is_production": self.is_production,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AIPrediction(db.Model):
    __tablename__ = "ai_predictions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)
    model_id = db.Column(db.String(36), db.ForeignKey("ai_models.id"), nullable=False)
    prediction_type = db.Column(db.String(50), nullable=False)
    input_data = db.Column(
        db.JSON, nullable=False
    )  # Input features used for prediction
    prediction_result = db.Column(db.JSON, nullable=False)  # Prediction output
    confidence_score = db.Column(db.Numeric(5, 4))  # Confidence score (0-1)
    explanation = db.Column(db.JSON)  # Feature importance and explanation
    status = db.Column(db.String(20), default="completed")  # pending, completed, failed
    execution_time_ms = db.Column(
        db.Integer
    )  # Prediction execution time in milliseconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AIPrediction {self.prediction_type}: {self.confidence_score}>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "model_id": self.model_id,
            "model_name": self.model.name if self.model else None,
            "prediction_type": self.prediction_type,
            "input_data": self.input_data,
            "prediction_result": self.prediction_result,
            "confidence_score": (
                float(self.confidence_score) if self.confidence_score else None
            ),
            "explanation": self.explanation,
            "status": self.status,
            "execution_time_ms": self.execution_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class FinancialInsight(db.Model):
    __tablename__ = "financial_insights"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)
    insight_type = db.Column(
        db.String(50), nullable=False
    )  # cash_flow_alert, expense_anomaly, revenue_trend, etc.
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), default="info")  # info, warning, critical
    category = db.Column(
        db.String(50)
    )  # cash_flow, expenses, revenue, risk, opportunity
    data_points = db.Column(db.JSON)  # Supporting data for the insight
    recommendations = db.Column(db.JSON)  # AI-generated recommendations
    is_read = db.Column(db.Boolean, default=False)
    is_dismissed = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime)  # When the insight becomes irrelevant
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<FinancialInsight {self.insight_type}: {self.title}>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "insight_type": self.insight_type,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "category": self.category,
            "data_points": self.data_points,
            "recommendations": self.recommendations,
            "is_read": self.is_read,
            "is_dismissed": self.is_dismissed,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ConversationSession(db.Model):
    __tablename__ = "conversation_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)
    session_name = db.Column(db.String(255))
    context = db.Column(db.JSON)  # Conversation context and history
    is_active = db.Column(db.Boolean, default=True)
    last_activity_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    messages = db.relationship(
        "ConversationMessage", backref="session", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ConversationSession {self.session_name}>"

    def to_dict(self, include_messages=False):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "session_name": self.session_name,
            "context": self.context,
            "is_active": self.is_active,
            "last_activity_at": (
                self.last_activity_at.isoformat() if self.last_activity_at else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_messages:
            data["messages"] = [msg.to_dict() for msg in self.messages]

        return data


class ConversationMessage(db.Model):
    __tablename__ = "conversation_messages"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(
        db.String(36), db.ForeignKey("conversation_sessions.id"), nullable=False
    )
    message_type = db.Column(db.String(20), nullable=False)  # user, assistant, system
    content = db.Column(db.Text, nullable=False)
    metadata = db.Column(db.JSON)  # Additional message metadata
    tokens_used = db.Column(db.Integer)  # Number of tokens used for AI processing
    processing_time_ms = db.Column(db.Integer)  # Processing time in milliseconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ConversationMessage {self.message_type}: {self.content[:50]}...>"

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "message_type": self.message_type,
            "content": self.content,
            "metadata": self.metadata,
            "tokens_used": self.tokens_used,
            "processing_time_ms": self.processing_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class FeatureStore(db.Model):
    __tablename__ = "feature_store"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)
    feature_name = db.Column(db.String(100), nullable=False)
    feature_group = db.Column(
        db.String(50), nullable=False
    )  # financial, behavioral, demographic, etc.
    feature_value = db.Column(db.JSON, nullable=False)  # The actual feature value
    feature_type = db.Column(
        db.String(20), nullable=False
    )  # numeric, categorical, boolean, array
    calculation_method = db.Column(db.Text)  # How the feature was calculated
    data_sources = db.Column(db.JSON)  # Sources used to calculate the feature
    valid_from = db.Column(db.DateTime, nullable=False)
    valid_until = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<FeatureStore {self.feature_name}: {self.feature_value}>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "feature_name": self.feature_name,
            "feature_group": self.feature_group,
            "feature_value": self.feature_value,
            "feature_type": self.feature_type,
            "calculation_method": self.calculation_method,
            "data_sources": self.data_sources,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ModelTrainingJob(db.Model):
    __tablename__ = "model_training_jobs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id = db.Column(db.String(36), db.ForeignKey("ai_models.id"), nullable=False)
    job_type = db.Column(
        db.String(50), nullable=False
    )  # training, retraining, validation
    status = db.Column(
        db.String(20), default="pending"
    )  # pending, running, completed, failed
    training_config = db.Column(db.JSON)  # Training configuration
    dataset_info = db.Column(db.JSON)  # Information about training dataset
    metrics = db.Column(db.JSON)  # Training metrics and results
    logs = db.Column(db.Text)  # Training logs
    error_message = db.Column(db.Text)  # Error message if failed
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ModelTrainingJob {self.job_type}: {self.status}>"

    def to_dict(self):
        return {
            "id": self.id,
            "model_id": self.model_id,
            "model_name": self.model.name if self.model else None,
            "job_type": self.job_type,
            "status": self.status,
            "training_config": self.training_config,
            "dataset_info": self.dataset_info,
            "metrics": self.metrics,
            "logs": self.logs,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
