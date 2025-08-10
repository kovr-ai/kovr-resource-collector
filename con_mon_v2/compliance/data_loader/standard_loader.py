"""
Standard data loader - loads Standard records from database.
"""

from typing import List, Type
from .base import BaseLoader
from con_mon_v2.compliance.models import Standard


class StandardLoader(BaseLoader):
    """
    Database loader for Standard records.
    Handles the standard table with exact 1:1 field mapping.
    """

    def get_model_class(self) -> Type[Standard]:
        """Return the Standard model class."""
        return Standard

    def get_table_name(self) -> str:
        """Return the database table name."""
        return "standard"

    def get_select_fields(self) -> List[str]:
        """Return the list of database fields to select."""
        return [
            "id",
            "name",
            "short_description",
            "long_description",
            "path",
            "labels",
            "created_at",
            "updated_at", 
            "active",
            "framework_id",
            "index"
        ] 