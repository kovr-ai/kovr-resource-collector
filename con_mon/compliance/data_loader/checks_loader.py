"""
Checks data loader - loads Check records from database.
Handles JSONB fields properly.
"""

from typing import List, Type
from .base import BaseLoader
from con_mon.compliance.models import Check
from con_mon.resources import Resource


class ChecksLoader(BaseLoader):
    """
    Database loader for Check records.
    Handles the checks table with JSONB fields (output_statements, fix_details, metadata).
    """

    @staticmethod
    def filter_by_resource_model(
        checks: List[Check],
        resource_models: List[Type[Resource]],
    ) -> List[Check]:
        # Filter checks by connector type based on resource_type in metadata
        filtered_checks = []
        for check in checks:
            if check.resource_model in resource_models:
                filtered_checks.append(check)

        print(f"✅ Loaded {len(checks)} total checks from database")
        print(f"🔍 Filtered to {len(filtered_checks)} checks")

        return filtered_checks

    def __init__(self):
        """Initialize the ChecksLoader with the Check model."""
        super().__init__(Check)
