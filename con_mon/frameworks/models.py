"""
Pydantic models for cybersecurity frameworks, controls, and standards.
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class Framework(BaseModel):
    """
    Represents a cybersecurity framework (e.g., NIST 800-171, NIST 800-53).
    """
    id: Optional[int] = None  # Auto-generated primary key
    name: str = Field(..., description="Framework name (e.g., 'NIST 800-171 Rev 2')")
    version: Optional[str] = Field(None, description="Framework version (e.g., 'Rev 2')")
    description: Optional[str] = Field(None, description="Framework description")
    issuing_organization: Optional[str] = Field(None, description="Organization that issued the framework")
    publication_date: Optional[datetime] = Field(None, description="Framework publication date")
    status: str = Field(default="active", description="Framework status (active, deprecated, draft)")
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)
    
    class Config:
        # Allow arbitrary field types for datetime
        arbitrary_types_allowed = True


class Control(BaseModel):
    """
    Represents a control within a cybersecurity framework.
    """
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
    
    class Config:
        arbitrary_types_allowed = True


class Standard(BaseModel):
    """
    Represents an industry standard or compliance requirement.
    """
    id: Optional[int] = None  # Auto-generated primary key
    name: str = Field(..., description="Standard name (e.g., 'SOC 2', 'ISO 27001')")
    version: Optional[str] = Field(None, description="Standard version")
    description: Optional[str] = Field(None, description="Standard description")
    issuing_organization: Optional[str] = Field(None, description="Organization that issued the standard")
    scope: Optional[str] = Field(None, description="Standard scope (e.g., 'Information Security')")
    status: str = Field(default="active", description="Standard status (active, deprecated, draft)")
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True


class StandardControlMapping(BaseModel):
    """
    Maps standards to framework controls (many-to-many relationship).
    """
    id: Optional[int] = None  # Auto-generated primary key
    standard_id: int = Field(..., description="Foreign key to Standard table")
    control_id: int = Field(..., description="Foreign key to Control table")
    mapping_type: str = Field(default="direct", description="Type of mapping (direct, partial, conceptual)")
    compliance_level: Optional[str] = Field(None, description="Compliance level required (mandatory, recommended, optional)")
    notes: Optional[str] = Field(None, description="Additional mapping notes")
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True


# Helper models for displaying framework data with relationships
class FrameworkWithControls(Framework):
    """Framework with its associated controls."""
    controls: List[Control] = Field(default_factory=list)


class ControlWithMappings(Control):
    """Control with its standard mappings."""
    framework: Optional[Framework] = None
    standard_mappings: List[StandardControlMapping] = Field(default_factory=list)


class StandardWithMappings(Standard):
    """Standard with its control mappings."""
    control_mappings: List[StandardControlMapping] = Field(default_factory=list) 