"""
Control data loader - loads Control records from database.
"""

from .base import BaseLoader
from con_mon.compliance.models import Control


class ControlLoader(BaseLoader):
    """
    Database loader for Control records.
    Handles the control table with exact 1:1 field mapping.
    """

    def __init__(self):
        """Initialize the ControlLoader with the Control model."""
        super().__init__(Control) 