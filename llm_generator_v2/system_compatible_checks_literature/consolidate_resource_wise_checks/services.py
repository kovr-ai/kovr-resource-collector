"""
Service implementation for consolidate_resource_wise_checks.
This is a NON-LLM service that consolidates multiple resource analyses for the same security check.
"""

import logging
from typing import Dict, Any, List
from collections import defaultdict
from llm_generator_v2.services import Service

logger = logging.getLogger(__name__)


class ConsolidateResourceWiseChecksService(Service):
    """
    NON-LLM service that consolidates multiple resource analyses for a single security check.
    Groups valid and invalid resources together with their literature and field paths.
    """

    def _process_input(self, input_data) -> Dict[str, Any]:
        """
        Consolidate multiple resource analyses into a single check result.
        
        Args:
            input_data: Pydantic model containing array of checks with resource analyses
            
        Returns:
            Dictionary with consolidated check containing valid and invalid resources
        """
        # Convert to dict if it's a Pydantic model
        if hasattr(input_data, 'model_dump'):
            input_dict = input_data.model_dump()
        else:
            input_dict = input_data
            
        checks = input_dict['check']
        
        if not checks:
            logger.warning("No checks provided for consolidation")
            return self._create_empty_consolidated_check()
        
        # Group checks by unique_id (should all be the same, but handle edge cases)
        checks_by_id = defaultdict(list)
        for check in checks:
            checks_by_id[check['unique_id']].append(check)
        
        # For now, consolidate the first group (assuming all checks have same unique_id)
        primary_check_id = list(checks_by_id.keys())[0]
        checks_to_consolidate = checks_by_id[primary_check_id]
        
        return self._consolidate_checks(checks_to_consolidate)
    
    def _consolidate_checks(self, checks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Consolidate multiple checks into a single result.
        
        Args:
            checks: List of check dictionaries to consolidate
            
        Returns:
            Consolidated check dictionary
        """
        if not checks:
            return self._create_empty_consolidated_check()
        
        # Use first check as the base
        base_check = checks[0]
        unique_id = base_check['unique_id']
        
        # Separate valid and invalid resources
        valid_resources = []
        invalid_resources = []
        
        for check in checks:
            resource = check['resource']
            # is_valid should always be boolean now, but add safety check
            is_valid = resource.get('is_valid', False)
            
            # Ensure boolean type (safety measure)
            if not isinstance(is_valid, bool):
                logger.warning(f"is_valid should be boolean, got {type(is_valid)}: {is_valid}")
                is_valid = bool(is_valid) if is_valid else False
            
            resource_info = {
                'name': resource.get('name', 'unknown_resource'),
                'literature': resource.get('literature', ''),
                'field_paths': resource.get('field_paths', []),
                'reason': resource.get('reason', 'No reason provided')
            }
            
            if is_valid:
                valid_resources.append(resource_info)
            else:
                invalid_resources.append(resource_info)
        
        logger.info(f"Consolidated check {unique_id}: {len(valid_resources)} valid, {len(invalid_resources)} invalid resources")
        
        return {
            'check': {
                'unique_id': unique_id,
                'valid_resources': valid_resources,
                'invalid_resources': invalid_resources
            }
        }
    
    def _create_empty_consolidated_check(self) -> Dict[str, Any]:
        """Create an empty consolidated check result."""
        return {
            'check': {
                'unique_id': 'unknown',
                'valid_resources': [],
                'invalid_resources': []
            }
        }
    
    def _process_input_list(self, input_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Override parent method to handle the input properly since this service
        expects input.check[] but processes them together into a single output.
        """
        # For this service, we want to process all inputs together, not individually
        combined_input = {'check': input_list}
        result = self._process_input(combined_input)
        return [result]  # Return as list for consistency with array output
