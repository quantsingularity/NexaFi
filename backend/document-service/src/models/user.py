import uuid
import json
from datetime import datetime
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

    def delete(self):
        # Placeholder for actual implementation
        pass

    def to_dict(self) -> Dict[str, Any]:
        # Placeholder for actual implementation
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}


class Document(BaseModel):
    table_name = "documents"

    def get_metadata(self):
        return json.loads(self.metadata) if self.metadata else {}

    def set_metadata(self, metadata):
        self.metadata = json.dumps(metadata)

    def get_extracted_data(self):
        return json.loads(self.extracted_data) if self.extracted_data else {}

    def set_extracted_data(self, data):
        self.extracted_data = json.dumps(data)

    def to_dict(self):
        data = super().to_dict()
        data["metadata"] = self.get_metadata()
        data["extracted_data"] = self.get_extracted_data()
        return data


class DocumentTemplate(BaseModel):
    table_name = "document_templates"

    def get_fields(self):
        return json.loads(self.fields) if self.fields else []

    def set_fields(self, fields):
        self.fields = json.dumps(fields)

    def get_metadata(self):
        return json.loads(self.metadata) if self.metadata else {}

    def set_metadata(self, metadata):
        self.metadata = json.dumps(metadata)

    def to_dict(self):
        data = super().to_dict()
        data["fields"] = self.get_fields()
        data["metadata"] = self.get_metadata()
        return data


class DocumentShare(BaseModel):
    table_name = "document_shares"

    def to_dict(self):
        return super().to_dict()


class DocumentVersion(BaseModel):
    table_name = "document_versions"

    def to_dict(self):
        return super().to_dict()
