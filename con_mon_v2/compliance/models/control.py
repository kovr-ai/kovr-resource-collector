"""
Control model - 1:1 mapping with database schema.
"""

from typing import Optional, ClassVar, Any
from datetime import datetime
from pydantic import Field

from .base import TableModel


class Control(TableModel):
    """
    Control model matching database schema exactly.
    
    Database table: control
    Fields: id, framework_id, control_parent_id, control_name, family_name, 
            control_long_name, control_text, control_discussion, control_summary,
            source_control_mapping_emb, control_eval_criteria, created_at, 
            updated_at, active, source_control_mapping, order_index, control_short_summary
    """
    
    # Table configuration
    table_name: ClassVar[str] = "control"
    
    # Database fields (exact 1:1 mapping)
    id: int = Field(..., description="Primary key")
    framework_id: Optional[int] = Field(None, description="Foreign key to Framework table")
    control_parent_id: Optional[int] = Field(None, description="Parent control ID")
    control_name: str = Field(..., description="Control identifier (e.g., 'AC-1', 'GV.OC-01')")
    family_name: Optional[str] = Field(None, description="Control family name")
    control_long_name: Optional[str] = Field(None, description="Full control name/title")
    control_text: Optional[str] = Field(None, description="Control description/requirement text")
    control_discussion: Optional[str] = Field(None, description="Control discussion")
    control_summary: Optional[str] = Field(None, description="Control summary")
    source_control_mapping_emb: Optional[Any] = Field(None, description="Source control mapping embedding (USER-DEFINED type)")
    control_eval_criteria: Optional[str] = Field(None, description="Control evaluation criteria")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    active: Optional[bool] = Field(None, description="Active status")
    source_control_mapping: Optional[str] = Field(None, description="Source control mapping")
    order_index: Optional[int] = Field(None, description="Order index")
    control_short_summary: Optional[str] = Field(None, description="Short summary of control") 