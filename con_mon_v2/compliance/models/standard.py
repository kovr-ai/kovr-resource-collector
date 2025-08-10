"""
Standard model - 1:1 mapping with database schema.
"""

from typing import Optional, ClassVar, List, Any
from datetime import datetime
from pydantic import Field

from .base import BaseModel


class Standard(BaseModel):
    """
    Standard model matching database schema exactly.
    
    Database table: standard
    Fields: id, name, short_description, long_description, path, labels,
            created_at, updated_at, active, framework_id, index
    """
    
    # Table configuration
    _table_name: ClassVar[str] = "standard"
    
    # Database fields (exact 1:1 mapping)
    id: Optional[int] = Field(None, description="Auto-generated primary key")
    name: str = Field(..., description="Standard name")
    short_description: Optional[str] = Field(None, description="Brief description")
    long_description: Optional[str] = Field(None, description="Detailed description")
    path: Optional[str] = Field(None, description="Standard path")
    labels: Optional[List[str]] = Field(None, description="Labels array")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    active: Optional[bool] = Field(None, description="Active status")
    framework_id: Optional[int] = Field(None, description="Foreign key to Framework table")
    index: Optional[int] = Field(None, description="Index value") 