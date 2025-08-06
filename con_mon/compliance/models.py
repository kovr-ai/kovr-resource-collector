"""
Pydantic models for cybersecurity frameworks, controls, and standards.
"""

from typing import Optional, List, ClassVar
from pydantic import BaseModel as PydanticBaseModel, Field
from datetime import datetime


class BaseModel(PydanticBaseModel):
    """
    Base model class for all compliance data models.
    Provides common functionality and configuration.
    """
    
    # Table configuration - can be overridden in subclasses
    class Config:
        # Allow arbitrary field types for datetime
        arbitrary_types_allowed = True
        # Enable field validation
        validate_assignment = True
        # Use enum values instead of names
        use_enum_values = True
        
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
    
    def get_field_value(self, field_name: str, default=None):
        """Get field value with default fallback."""
        return getattr(self, field_name, default)
    
    def to_dict_for_db(self) -> dict:
        """Convert model to dictionary suitable for database operations."""
        data = self.dict()
        # Convert datetime objects to ISO strings for database compatibility
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data


class Framework(BaseModel):
    """
    Represents a cybersecurity framework (e.g., NIST 800-171, NIST 800-53).
    """
    
    # Table configuration
    _table_name: ClassVar[str] = "framework"
    
    id: Optional[int] = None  # Auto-generated primary key
    name: str = Field(..., description="Framework name (e.g., 'NIST 800-171 Rev 2')")
    version: Optional[str] = Field(None, description="Framework version (e.g., 'Rev 2')")
    description: Optional[str] = Field(None, description="Framework description")
    issuing_organization: Optional[str] = Field(None, description="Organization that issued the framework")
    publication_date: Optional[datetime] = Field(None, description="Framework publication date")
    status: str = Field(default="active", description="Framework status (active, deprecated, draft)")
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)


class Control(BaseModel):
    """
    Represents a control within a cybersecurity framework.
    """
    
    # Table configuration
    _table_name: ClassVar[str] = "control"
    
    id: Optional[int] = None  # Auto-generated primary key
    framework_id: int = Field(..., description="Foreign key to Framework table")
    control_id: str = Field(..., description="Control identifier (e.g., '3.1.1', 'AC-2')")
    name: str = Field(..., description="Control name/title")
    description: str = Field(..., description="Control description/requirement")
    control_family: Optional[str] = Field(None, description="Control family (e.g., 'Access Control', 'Audit')")
    priority: Optional[str] = Field(None, description="Control priority (high, medium, low)")
    implementation_guidance: Optional[str] = Field(None, description="Implementation guidance for the control")
    github_check_required: Optional[str] = Field(None, description="GitHub-specific implementation requirement")
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)


class Standard(BaseModel):
    """
    Represents an industry standard or compliance requirement.
    """
    
    # Table configuration
    _table_name: ClassVar[str] = "standard"
    
    id: Optional[int] = None  # Auto-generated primary key
    name: str = Field(..., description="Standard name (e.g., 'SOC 2', 'ISO 27001')")
    version: Optional[str] = Field(None, description="Standard version")
    description: Optional[str] = Field(None, description="Standard description")
    issuing_organization: Optional[str] = Field(None, description="Organization that issued the standard")
    scope: Optional[str] = Field(None, description="Standard scope (e.g., 'Information Security')")
    status: str = Field(default="active", description="Standard status (active, deprecated, draft)")
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)


class StandardControlMapping(BaseModel):
    """
    Maps standards to framework controls (many-to-many relationship).
    """
    
    # Table configuration
    _table_name: ClassVar[str] = "standard_control_mapping"
    
    id: Optional[int] = None  # Auto-generated primary key
    standard_id: int = Field(..., description="Foreign key to Standard table")
    control_id: int = Field(..., description="Foreign key to Control table")
    mapping_type: str = Field(default="direct", description="Type of mapping (direct, partial, conceptual)")
    compliance_level: Optional[str] = Field(None, description="Compliance level required (mandatory, recommended, optional)")
    notes: Optional[str] = Field(None, description="Additional mapping notes")
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)


# Helper models for displaying framework data with relationships
class FrameworkWithControls(Framework):
    """Framework with its associated controls."""
    controls: List[Control] = Field(default_factory=list)


class StandardWithControls(Standard):
    """Standard with its control mappings."""
    controls: List[Control] = Field(default_factory=list)


class ControlWithStandards(Control):
    """Control with its mapped standards."""
    standards: List[Standard] = Field(default_factory=list) 