"""
Models for resources module - represents individual data items and collections.
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class FieldType(Enum):
    """Types of fields in a resource."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    LIST = "list"
    DICT = "dict"
    OBJECT = "object"


class ResourceField(BaseModel):
    """Represents a single field within a resource."""
    name: str
    field_type: FieldType
    value: Any
    is_required: bool = False
    description: Optional[str] = None
    validation_rules: Optional[Dict[str, Any]] = None
    
    def validate(self) -> bool:
        """Validate the field value against its type and rules."""
        if self.is_required and self.value is None:
            return False
        
        # Basic type validation
        if self.value is not None:
            if self.field_type == FieldType.STRING and not isinstance(self.value, str):
                return False
            elif self.field_type == FieldType.INTEGER and not isinstance(self.value, int):
                return False
            elif self.field_type == FieldType.FLOAT and not isinstance(self.value, (int, float)):
                return False
            elif self.field_type == FieldType.BOOLEAN and not isinstance(self.value, bool):
                return False
            elif self.field_type == FieldType.LIST and not isinstance(self.value, list):
                return False
            elif self.field_type == FieldType.DICT and not isinstance(self.value, dict):
                return False
        
        return True


class Resource(BaseModel):
    """
    Represents a single resource item that checks will evaluate.
    This is the fundamental unit that connectors fetch and checks operate on.
    """
    id: str
    source_connector: str
    data: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    fields: List[ResourceField] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    
    def get_field_value(self, field_path: str) -> Any:
        """
        Get a field value using dot notation (e.g., 'user.name', 'config.settings.timeout').
        
        Args:
            field_path: Dot-separated path to the field
            
        Returns:
            The field value or None if not found
        """
        keys = field_path.split('.')
        value = self.data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        
        return value
    
    def set_field_value(self, field_path: str, value: Any) -> None:
        """
        Set a field value using dot notation.
        
        Args:
            field_path: Dot-separated path to the field
            value: Value to set
        """
        keys = field_path.split('.')
        current = self.data
        
        # Navigate to the parent of the target field
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
        self.updated_at = datetime.now()
    
    def has_field(self, field_path: str) -> bool:
        """Check if a field exists in the resource data."""
        return self.get_field_value(field_path) is not None
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the resource."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the resource."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()
    
    def validate_fields(self) -> bool:
        """Validate all defined fields in the resource."""
        return all(field.validate() for field in self.fields)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert resource to dictionary representation."""
        return {
            "id": self.id,
            "source_connector": self.source_connector,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "tags": self.tags
        }


class ResourceCollection(BaseModel):
    """
    Represents a collection of resources, typically the result of a connector's fetch operation.
    """
    resources: List[Resource]
    source_connector: str
    total_count: int
    fetched_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def __len__(self) -> int:
        """Return the number of resources in the collection."""
        return len(self.resources)
    
    def __iter__(self):
        """Make the collection iterable."""
        return iter(self.resources)
    
    def __getitem__(self, index: Union[int, slice]) -> Union[Resource, List[Resource]]:
        """Allow indexing and slicing of the collection."""
        return self.resources[index]
    
    def add_resource(self, resource: Resource) -> None:
        """Add a resource to the collection."""
        self.resources.append(resource)
    
    def filter_by_tag(self, tag: str) -> List[Resource]:
        """Filter resources that have a specific tag."""
        return [r for r in self.resources if tag in r.tags]
    
    def get_by_id(self, resource_id: str) -> Optional[Resource]:
        """Get a resource by its ID."""
        for resource in self.resources:
            if resource.id == resource_id:
                return resource
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert collection to dictionary representation."""
        return {
            "resources": [r.to_dict() for r in self.resources],
            "source_connector": self.source_connector,
            "total_count": self.total_count,
            "fetched_at": self.fetched_at.isoformat(),
            "metadata": self.metadata
        } 