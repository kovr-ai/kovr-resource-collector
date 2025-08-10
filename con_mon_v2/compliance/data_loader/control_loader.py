"""
Control data loader - loads Control records from database.
"""

from typing import List, Type
from .base import BaseLoader
from con_mon_v2.compliance.models import Control


class ControlLoader(BaseLoader):
    """
    Database loader for Control records.
    Handles the control table with exact 1:1 field mapping.
    """

    def get_model_class(self) -> Type[Control]:
        """Return the Control model class."""
        return Control

    def get_table_name(self) -> str:
        """Return the database table name."""
        return "control"

    def get_select_fields(self) -> List[str]:
        """Return the list of database fields to select."""
        return [
            "id",
            "framework_id",
            "control_parent_id", 
            "control_name",
            "family_name",
            "control_long_name",
            "control_text",
            "control_discussion",
            "control_summary",
            "source_control_mapping_emb",
            "control_eval_criteria",
            "created_at",
            "updated_at",
            "active",
            "source_control_mapping",
            "order_index",
            "control_short_summary"
        ] 