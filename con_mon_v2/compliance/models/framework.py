"""
Framework model - 1:1 mapping with database schema.
"""

from typing import Optional, ClassVar
from datetime import datetime
from pydantic import Field

from .base import BaseModel


class Framework(BaseModel):
    """
    Framework model matching database schema exactly.
    
    Database table: framework
    Fields: id, name, description, path, version, created_at, updated_at, active
    """
    
    # Table configuration
    _table_name: ClassVar[str] = "framework"
    
    # Database fields (exact 1:1 mapping)
    id: Optional[int] = Field(None, description="Auto-generated primary key")
    name: str = Field(..., description="Framework name")
    description: Optional[str] = Field(None, description="Framework description") 
    path: Optional[str] = Field(None, description="Framework path")
    version: Optional[int] = Field(None, description="Framework version (integer)")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    active: Optional[bool] = Field(None, description="Active status") 