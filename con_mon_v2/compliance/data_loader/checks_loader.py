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
