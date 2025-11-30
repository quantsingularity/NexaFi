import uuid
import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List


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

    def to_dict(self) -> Dict[str, Any]:
        # Placeholder for actual implementation
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}


class AIModel(BaseModel):
    table_name = "ai_models"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        # Convert JSON strings back to dicts if they exist
        for key in ["model_config", "training_data_info", "performance_metrics"]:
            if key in data and isinstance(data[key], str):
                try:
                    data[key] = json.loads(data[key])
                except json.JSONDecodeError:
                    pass  # Keep as string if decoding fails
        return data


class AIPrediction(BaseModel):
    table_name = "ai_predictions"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        # Convert JSON strings back to dicts if they exist
        for key in ["input_data", "prediction_result", "explanation"]:
            if key in data and isinstance(data[key], str):
                try:
                    data[key] = json.loads(data[key])
                except json.JSONDecodeError:
                    pass
        # Convert Decimal to float for JSON serialization
        if "confidence_score" in data and data["confidence_score"] is not None:
            data["confidence_score"] = float(data["confidence_score"])
        return data


class FinancialInsight(BaseModel):
    table_name = "financial_insights"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        # Convert JSON strings back to dicts if they exist
        for key in ["data_points", "recommendations"]:
            if key in data and isinstance(data[key], str):
                try:
                    data[key] = json.loads(data[key])
                except json.JSONDecodeError:
                    pass
        return data


class ConversationSession(BaseModel):
    table_name = "conversation_sessions"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        if "context" in data and isinstance(data["context"], str):
            try:
                data["context"] = json.loads(data["context"])
            except json.JSONDecodeError:
                pass
        # Note: Relationships like 'messages' are not handled by the simple BaseModel
        # We will need to fetch messages separately in the route or enhance BaseModel.
        # For now, we'll remove the relationship handling from the to_dict method.
        data.pop("messages", None)
        return data


class ConversationMessage(BaseModel):
    table_name = "conversation_messages"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        if "metadata" in data and isinstance(data["metadata"], str):
            try:
                data["metadata"] = json.loads(data["metadata"])
            except json.JSONDecodeError:
                pass
        return data


class FeatureStore(BaseModel):
    table_name = "feature_store"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        if "feature_value" in data and isinstance(data["feature_value"], str):
            try:
                data["feature_value"] = json.loads(data["feature_value"])
            except json.JSONDecodeError:
                pass
        if "data_sources" in data and isinstance(data["data_sources"], str):
            try:
                data["data_sources"] = json.loads(data["data_sources"])
            except json.JSONDecodeError:
                pass
        return data


class ModelTrainingJob(BaseModel):
    table_name = "model_training_jobs"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        for key in ["training_config", "dataset_info", "metrics"]:
            if key in data and isinstance(data[key], str):
                try:
                    data[key] = json.loads(data[key])
                except json.JSONDecodeError:
                    pass
        return data
