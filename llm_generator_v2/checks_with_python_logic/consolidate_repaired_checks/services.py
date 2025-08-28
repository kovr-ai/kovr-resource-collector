"""
Consolidate Repaired Checks Service Implementation
"""

import logging
from typing import Dict, Any, List
from collections import defaultdict
from pydantic import BaseModel
from llm_generator_v2.services import Service

logger = logging.getLogger(__name__)


class ConsolidateRepairedChecksService(Service):
    """
    NON-LLM service that consolidates repaired Python logic into final check format.
    """

    def _get_input_filename(self, input_: BaseModel) -> str:
        """Generate unique filename for input based on check unique_id."""
        return f"{input_.check.unique_id}.yaml"

    def _get_output_filename(self, output_: BaseModel) -> str:
        """Generate unique filename for output based on check unique_id."""
        return f"{output_.checks.unique_id}.yaml"

    def _process_input(self, input_data) -> Dict[str, Any]:
        """
        Consolidate repaired Python logic into final check format.

        Args:
            input_data: Pydantic model containing check and resource information

        Returns:
            Dictionary with consolidated check containing final format
        """
        # Convert to dict if it's a Pydantic model
        if hasattr(input_data, 'model_dump'):
            input_dict = input_data.model_dump()
        else:
            input_dict = input_data

        check = input_dict['check']
        resource = input_dict['resource']

        # Create consolidated check structure
        consolidated_check = {
            'checks': {
                'unique_id': check['unique_id'],
                'name': f"Repaired_{check['unique_id']}",
                'literature': f"Repaired check for {check['unique_id']} with improved logic",
                'category': 'repaired_compliance',
                'output_statements': {
                    'success': f'Repaired check {check["unique_id"]} passed',
                    'failure': f'Repaired check {check["unique_id"]} failed',
                    'partial': f'Repaired check {check["unique_id"]} partially passed'
                },
                'fix_details': {
                    'description': f'Repaired logic for {check["unique_id"]} based on error analysis',
                    'instructions': [
                        'Logic was repaired based on validation errors',
                        'Field path and validation criteria were improved',
                        'Edge cases are now properly handled'
                    ],
                    'estimated_time': '1 hour',
                    'automation_available': True
                },
                'resource': {
                    'name': resource['name'],
                    'field_path': resource['field_path'],
                    'logic': resource['logic']
                },
                'tags': ['repaired', 'improved', 'compliance'],
                'severity': 'medium'
            }
        }

        logger.info(f"Consolidated repaired check: {check['unique_id']}")

        return consolidated_check
