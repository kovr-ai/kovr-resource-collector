"""
Framework data loader - loads Framework records from database.
"""

from typing import List, Type
from .base import BaseLoader
from con_mon_v2.compliance.models import Framework


class FrameworkLoader(BaseLoader):
    """
    Database loader for Framework records.
    Handles the framework table with exact 1:1 field mapping.
    """

    def get_model_class(self) -> Type[Framework]:
        """Return the Framework model class."""
        return Framework

    def get_table_name(self) -> str:
        """Return the database table name."""
        return "framework"

    def get_select_fields(self) -> List[str]:
        """Return the list of database fields to select."""
        return [
            "id",
            "name", 
            "description",
            "path",
            "version",
            "created_at",
            "updated_at",
            "active"
        ] 