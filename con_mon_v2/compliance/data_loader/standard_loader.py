"""
Standard data loader - loads Standard records from database.
"""

from .base import BaseLoader
from con_mon_v2.compliance.models import Standard


class StandardLoader(BaseLoader):
    """
    Database loader for Standard records.
    Handles the standard table with exact 1:1 field mapping.
    """

    def __init__(self):
        """Initialize the StandardLoader with the Standard model."""
        super().__init__(Standard) 