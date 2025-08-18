"""
Check results models for con_mon_results and con_mon_results_history tables.
"""

from typing import Optional, ClassVar, List, Dict, Any
from datetime import datetime
from pydantic import Field

from .base import TableModel


class ConMonResult(TableModel):
    """
    con_mon_results database schema.
    
    Database table: con_mon_results
    Stores the current/latest check results for each customer, connection, and check combination.
    """
    
    # Table configuration
    table_name: ClassVar[str] = "con_mon_results"
    
    # Database fields (exact 1:1 mapping)
    # id: Optional[int] = Field(None, description="Auto-generated primary key")
    customer_id: str = Field(..., description="Customer/organization identifier")
    connection_id: int = Field(..., description="Connection ID")
    check_id: str = Field(..., description="Check identifier")
    result: str = Field(..., description="Overall result (PASS/FAIL)")
    result_message: str = Field(..., description="Result message/description")
    
    # Count fields
    success_count: int = Field(..., description="Number of resources that passed")
    failure_count: int = Field(..., description="Number of resources that failed")
    success_percentage: float = Field(..., description="Success percentage (0-100)")
    
    # JSONB fields for detailed data
    success_resources: List[Dict[str, Any]] = Field(default_factory=list, description="Resources that passed (JSONB)")
    failed_resources: List[Dict[str, Any]] = Field(default_factory=list, description="Resources that failed (JSONB)")
    exclusions: List[Dict[str, Any]] = Field(default_factory=list, description="Excluded resources (JSONB)")
    resource_json: Dict[str, Any] = Field(default_factory=dict, description="Full resource collection data (JSONB)")
    
    # Audit fields
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class ConMonResultHistory(ConMonResult):
    """
    Check results history model matching con_mon_results_history database schema exactly.
    
    Database table: con_mon_results_history
    Stores historical check results for audit trail and trend analysis.
    """
    
    # Table configuration
    table_name: ClassVar[str] = "con_mon_results_history"