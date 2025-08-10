"""
StandardControlMapping data loader - loads mapping records from database.
"""

from typing import List, Type
from .base import BaseLoader
from con_mon_v2.compliance.models import StandardControlMapping


class StandardControlMappingLoader(BaseLoader):
    """
    Database loader for StandardControlMapping records.
    Handles the standard_control_mapping table with exact 1:1 field mapping.
    """

    def get_model_class(self) -> Type[StandardControlMapping]:
        """Return the StandardControlMapping model class."""
        return StandardControlMapping

    def get_table_name(self) -> str:
        """Return the database table name."""
        return "standard_control_mapping"

    def get_select_fields(self) -> List[str]:
        """Return the list of database fields to select."""
        return [
            "id",
            "standard_id",
            "control_id",
            "additional_selection_parameters",
            "additional_guidance", 
            "created_at",
            "updated_at"
        ] 