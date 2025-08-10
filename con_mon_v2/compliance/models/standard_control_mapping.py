"""
StandardControlMapping model - 1:1 mapping with database schema.
"""

from typing import Optional, ClassVar
from datetime import datetime
from pydantic import Field

from .base import BaseModel


class StandardControlMapping(BaseModel):
    """
    StandardControlMapping model matching database schema exactly.
    
    Database table: standard_control_mapping
    Fields: id, standard_id, control_id, additional_selection_parameters, 
            additional_guidance, created_at, updated_at
    """
    
    # Table configuration
    _table_name: ClassVar[str] = "standard_control_mapping"
    
    # Database fields (exact 1:1 mapping)
    id: Optional[int] = Field(None, description="Auto-generated primary key")
    standard_id: int = Field(..., description="Foreign key to Standard table")
    control_id: Optional[int] = Field(None, description="Foreign key to Control table")
    additional_selection_parameters: Optional[str] = Field(None, description="Additional selection parameters")
    additional_guidance: Optional[str] = Field(None, description="Additional guidance")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp") 