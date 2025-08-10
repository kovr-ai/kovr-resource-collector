"""
Base model class for all database models.
"""

from typing import Optional, ClassVar, Any, Dict
from pydantic import BaseModel as PydanticBaseModel, ConfigDict
from datetime import datetime


class BaseModel(PydanticBaseModel):
    """
    Base model class for all database models.
    Provides common functionality and configuration.
    """

    @staticmethod
    def _parse_datetime(date_string: str) -> Optional[datetime]:
        """Parse ISO datetime string, return None if invalid."""
        if not date_string or date_string == 'None':
            return None
        try:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _parse_bool(value: str) -> bool:
        """Parse boolean string value."""
        if isinstance(value, bool):
            return value
        return str(value).lower() in ('true', '1', 'yes', 'on')

    model_config = ConfigDict(
        # Allow arbitrary field types for datetime and other complex types
        arbitrary_types_allowed=True,
        # Enable field validation
        validate_assignment=True,
        # Use enum values instead of names
        use_enum_values=True,
        # Allow extra fields (for flexibility)
        extra='forbid',
        # Validate default values
        validate_default=True
    )
    
    # Table metadata - override in subclasses
    _table_name: ClassVar[Optional[str]] = None
    _primary_key: ClassVar[str] = "id"
    
    @classmethod
    def get_table_name(cls) -> str:
        """Get the database table name for this model."""
        if cls._table_name:
            return cls._table_name
        # Default: lowercase class name
        return cls.__name__.lower()
    
    @classmethod
    def get_primary_key(cls) -> str:
        """Get the primary key field name for this model."""
        return cls._primary_key

    @classmethod
    def from_db_to_object(cls, row) -> PydanticBaseModel:
        pass

    def get_field_value(self, field_name: str, default=None):
        """Get field value with default fallback."""
        return getattr(self, field_name, default)
    
    def to_dict_for_db(self) -> Dict[str, Any]:
        """Convert model to dictionary suitable for database operations."""
        data = self.model_dump()
        # Convert datetime objects to ISO strings for database compatibility
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data
    
    def to_csv_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary suitable for CSV export."""
        return self.model_dump()
