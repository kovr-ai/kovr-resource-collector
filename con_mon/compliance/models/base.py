"""
Base model class for all database models.
"""

import json
from typing import Optional, ClassVar, Any, Dict, Union
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class TableModel(BaseModel):
    """
    Base model class for all database models.
    Provides common functionality and configuration.
    """

    @staticmethod
    def _parse_datetime(date_string: Union[str, datetime, None]) -> Optional[datetime]:
        """Parse ISO datetime string, return None if invalid."""
        if not date_string or date_string == 'None' or date_string == '':
            return None
        if isinstance(date_string, datetime):
            return date_string
        try:
            # Handle various datetime formats
            if isinstance(date_string, str):
                # Remove quotes if present
                date_string = date_string.strip('"\'')
                return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
        return None

    @staticmethod
    def _parse_bool(value: Union[str, bool, None]) -> bool:
        """Parse boolean string value."""
        if isinstance(value, bool):
            return value
        if value is None or value == '' or value == 'None':
            return False
        return str(value).lower() in ('true', '1', 'yes', 'on', 't')

    @staticmethod
    def _parse_int(value: Union[str, int, None]) -> Optional[int]:
        """Parse integer value."""
        if value is None or value == '' or value == 'None':
            return None
        if isinstance(value, int):
            return value
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_json(value: Union[str, dict, list, None]) -> Optional[Union[dict, list]]:
        """Parse JSON string to dict/list."""
        if value is None or value == '' or value == 'None':
            return None
        if isinstance(value, (dict, list)):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    @staticmethod
    def _parse_array(value: Union[str, list, None]) -> Optional[list]:
        """Parse array value from various formats."""
        if value is None or value == '' or value == 'None':
            return None
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            # Handle PostgreSQL array format: {item1,item2,item3}
            if value.startswith('{') and value.endswith('}'):
                # Remove braces and split by comma
                items = value[1:-1].split(',') if value != '{}' else []
                return [item.strip() for item in items if item.strip()]
            # Handle JSON array format
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else None
            except json.JSONDecodeError:
                return None
        return None

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
    def from_row(cls, row: Dict[str, Any]) -> 'BaseModel':
        """
        Convert a row dictionary to a model instance.
        
        The row should already be in the correct format for the model fields.
        Any transformations (CSV flattening, JSONB parsing, etc.) should be 
        handled by the loaders before calling this method.
        
        Args:
            row: Dictionary containing row data with keys matching model fields
            
        Returns:
            Model instance
        """
        # Get model fields and their types
        model_fields = cls.model_fields
        processed_data = {}
        
        for field_name, field_info in model_fields.items():
            raw_value = row.get(field_name)
            field_type = field_info.annotation
            
            # Handle different field types with basic parsing
            if raw_value is None or raw_value == '' or raw_value == 'None':
                processed_data[field_name] = None
            elif field_type == Optional[datetime] or field_type == datetime:
                processed_data[field_name] = cls._parse_datetime(raw_value)
            elif field_type == Optional[bool] or field_type == bool:
                processed_data[field_name] = cls._parse_bool(raw_value)
            elif field_type == Optional[int] or field_type == int:
                processed_data[field_name] = cls._parse_int(raw_value)
            elif hasattr(field_type, '__origin__') and field_type.__origin__ is list:
                processed_data[field_name] = cls._parse_array(raw_value)
            elif isinstance(raw_value, str) and raw_value.strip().startswith(('{', '[')):
                # Handle JSON strings (from database JSONB fields)
                processed_data[field_name] = cls._parse_json(raw_value)
            else:
                # Default: use raw value as-is
                processed_data[field_name] = raw_value
        
        return cls(**processed_data)

    def get_field_value(self, field_name: str, default=None):
        """Get field value with default fallback."""
        return getattr(self, field_name, default)

    def to_row(self) -> Dict[str, Any]:
        """Convert model to dictionary of row"""
        data = self.model_dump()
        # Convert datetime objects to ISO strings for database compatibility
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data
