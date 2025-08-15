"""
StandardControlMapping data loader - loads mapping records from database.
"""

from .base import BaseLoader
from con_mon_v2.compliance.models import StandardControlMapping


class StandardControlMappingLoader(BaseLoader):
    """
    Database loader for StandardControlMapping records.
    Handles the standard_control_mapping table with exact 1:1 field mapping.
    """

    def __init__(self):
        """Initialize the StandardControlMappingLoader with the StandardControlMapping model."""
        super().__init__(StandardControlMapping) 