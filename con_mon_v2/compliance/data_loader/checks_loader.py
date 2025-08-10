"""
Checks data loader - loads Check records from database.
Handles JSONB fields properly.
"""

from typing import Dict, Any
from .base import BaseLoader
from con_mon_v2.compliance.models import Check


class ChecksLoader(BaseLoader):
    """
    Database loader for Check records.
    Handles the checks table with JSONB fields (output_statements, fix_details, metadata).
    """

    def __init__(self):
        """Initialize the ChecksLoader with the Check model."""
        super().__init__(Check)

    def process_row(self, raw_row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a raw database row before converting to model.

        The JSONB fields (output_statements, fix_details, metadata) come from the database
        as either:
        1. Already parsed dict/objects (from psycopg2)
        2. JSON strings that need parsing

        The base model's from_row method will handle the JSON string parsing,
        so we just pass the row through as-is.

        Args:
            raw_row: Raw row from database

        Returns:
            Processed row ready for model creation
        """
        # For checks, we don't need special processing since the base model
        # handles JSONB fields (JSON strings) automatically in from_row
        return raw_row
