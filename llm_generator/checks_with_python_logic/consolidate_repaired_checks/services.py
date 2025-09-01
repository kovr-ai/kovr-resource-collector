"""
Consolidate Repaired Checks Service Implementation
"""

import yaml
import logging
from typing import Dict, Any
from pydantic import BaseModel
from llm_generator.services import Service

logger = logging.getLogger(__name__)


class ConsolidateRepairedChecksService(Service):
    """
    NON-LLM service that consolidates repaired Python logic into final check format.
    """

    def _get_input_filename(self, input_: BaseModel) -> str:
        """Generate unique filename for input based on check unique_id."""
        return f"{input_.check.unique_id}-{input_.resource.name}.yaml"

    def _get_output_filename(self, output_: BaseModel) -> str:
        """Generate unique filename for output based on check unique_id and resource name."""
        # This is with Input
        if hasattr(output_, "resource") and output_.resource.name:
            return f"{output_.check.unique_id}-{output_.resource.name}.yaml"
        # This is with Output
        elif hasattr(output_, "check") and output_.check.resource.name:
            return f"{output_.check.unique_id}-{output_.check.resource.name}.yaml"
        raise self.GenerateUniqueFilepath()

    def _process_input(self, input_: BaseModel) -> Dict[str, Any]:
        """
        Consolidate repaired Python logic into final check format.

        Args:
            input_data: Pydantic model containing check and resource information

        Returns:
            Dictionary with consolidated check containing final format
        """
        targeted_literature_folder = 'llm_generator/data/debugging/sec2_system_compatible_checks_literature/step1_add_targeted_literature/output'
        check_resource_yaml_filepath = f'{targeted_literature_folder}/{input_.check.unique_id}-{input_.resource.name}.yaml'
        with open(check_resource_yaml_filepath, 'r') as check_resource_yaml_file:
            yaml_data = yaml.safe_load(check_resource_yaml_file)
            yaml_resource = yaml_data.pop('resource')
            _ = yaml_resource.pop('check')
        input_check = input_.check
        input_resource = input_.resource

        # Create consolidated check structure
        consolidated_check = {
            'check': {
                'unique_id': input_check.unique_id,
                'name': input_check.unique_id,
                'resource': input_resource.model_dump(),
                # 'tags': ['repaired', 'improved', 'compliance'],
                # 'severity': 'medium'
            }
        }
        consolidated_check['check']['resource'].update(yaml_resource)
        return consolidated_check
