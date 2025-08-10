"""
Check model - 1:1 mapping with database schema including JSONB nested fields.
"""

from typing import Optional, ClassVar, List, Any, Dict
from datetime import datetime
from pydantic import Field, BaseModel as PydanticBaseModel

from .base import TableModel


class CheckOperation(PydanticBaseModel):
    """
    Nested model for check operation within metadata JSONB field.
    """
    name: str = Field(..., description="Operation name (e.g., 'custom', 'equals')")
    logic: Optional[str] = Field(None, description="Custom logic code for operation")


class CheckMetadata(PydanticBaseModel):
    """
    Nested model for metadata JSONB field.
    
    Represents the full nested structure:
    {
        "tags": ["compliance", "nist"],
        "category": "configuration", 
        "severity": "medium",
        "operation": {"name": "custom", "logic": "..."},
        "field_path": "repository_data.basic_info.description",
        "connection_id": 1,
        "resource_type": "con_mon_v2.mappings.github.GithubResource",
        "expected_value": null
    }
    """
    tags: Optional[List[str]] = Field(None, description="Tags array")
    category: Optional[str] = Field(None, description="Check category")
    severity: Optional[str] = Field(None, description="Severity level")
    operation: CheckOperation = Field(..., description="Operation configuration")
    field_path: str = Field(..., description="Resource field path")
    connection_id: Optional[int] = Field(None, description="Connection ID")
    resource_type: Optional[str] = Field(None, description="Resource type class path")
    expected_value: Optional[Any] = Field(None, description="Expected value for comparison")


class OutputStatements(PydanticBaseModel):
    """
    Nested model for output_statements JSONB field.
    
    Represents the nested structure:
    {
        "failure": "Check failed: ...",
        "partial": "Check partially passed",
        "success": "Check passed: ..."
    }
    """
    failure: Optional[str] = Field(None, description="Failure message")
    partial: Optional[str] = Field(None, description="Partial success message")
    success: Optional[str] = Field(None, description="Success message")


class FixDetails(PydanticBaseModel):
    """
    Nested model for fix_details JSONB field.
    
    Represents the nested structure:
    {
        "description": "Update the repository description...",
        "instructions": ["Go to settings", "Edit description"],
        "estimated_date": "2023-06-30",
        "automation_available": false
    }
    """
    description: Optional[str] = Field(None, description="Fix description")
    instructions: Optional[List[str]] = Field(None, description="Step-by-step instructions")
    estimated_date: Optional[str] = Field(None, description="Estimated completion date")
    automation_available: bool = Field(False, description="Whether automation is available")


class Check(TableModel):
    """
    Check model matching database schema exactly.
    
    Database table: checks
    Fields: id, name, description, output_statements (JSONB), fix_details (JSONB),
            created_by, category, metadata (JSONB), updated_by, created_at, 
            updated_at, is_deleted
    """
    
    # Table configuration
    table_name: ClassVar[str] = "checks"
    
    # Database fields (exact 1:1 mapping)
    id: str = Field(..., description="Check ID (string primary key)")
    name: str = Field(..., description="Check name")
    description: str = Field(..., description="Check description")
    
    # JSONB fields with full nested structure
    output_statements: OutputStatements = Field(..., description="Output statements JSONB field")
    fix_details: FixDetails = Field(..., description="Fix details JSONB field") 
    metadata: CheckMetadata = Field(..., description="Metadata JSONB field")
    
    # Regular fields
    created_by: str = Field(..., description="User who created the check")
    category: str = Field(..., description="Check category")
    updated_by: str = Field(..., description="User who last updated the check")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    is_deleted: bool = Field(False, description="Soft delete flag") 