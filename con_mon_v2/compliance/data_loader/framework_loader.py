"""
Framework data loader - loads Framework records from database.
"""

from .base import BaseLoader
from con_mon_v2.compliance.models import Framework


class FrameworkLoader(BaseLoader):
    """
    Database loader for Framework records.
    Handles the framework table with exact 1:1 field mapping.
    """

    def __init__(self):
        """Initialize the FrameworkLoader with the Framework model."""
        super().__init__(Framework) 