"""
Service implementation for consolidate_resource_wise_checks.
This is a NON-LLM service that consolidates multiple resource analyses for the same security check.
"""

import logging
from pydantic import BaseModel
from llm_generator_v2.services import Service as BaseService

logger = logging.getLogger(__name__)


class ConsolidateResourceWiseChecksService(BaseService):
    """
    NON-LLM service that consolidates multiple resource analyses for a single security check.
    Groups valid and invalid resources together with their literature and field paths.
    """

    def _get_input_filename(self, input_: BaseModel) -> str:
        """Generate unique filename for input based on check unique_id."""
        return f"{input_.check.unique_id}.yaml"

    def _get_output_filename(self, output_: BaseModel) -> str:
        """Generate unique filename for output based on check unique_id and resource name."""
        return f"{output_.check.unique_id}.yaml"

    def _process_input(self, input_):
        """
        Consolidate multiple resource analyses into a single check result.
        
        Args:
            input_data: Pydantic model containing check with list of resources and analyses
            
        Returns:
            Dictionary with consolidated check containing valid and invalid resources
        """
        valid_resources = []
        invalid_resources = []
        for resource in input_.check.resources:
            # is_valid should always be boolean now, but add safety check
            is_valid = resource.is_valid

            # Ensure boolean type (safety measure)
            if not isinstance(is_valid, bool):
                logger.warning(f"is_valid should be boolean, got {type(is_valid)}: {is_valid}")
                is_valid = bool(is_valid) if is_valid else False

            if is_valid:
                valid_resources.append(resource.model_dump())
            else:
                invalid_resources.append(resource.model_dump())

        return self.Output(
            check=dict(
                unique_id=input_.check.unique_id,
                valid_resources=valid_resources,
                invalid_resources=invalid_resources,
            )
        )
