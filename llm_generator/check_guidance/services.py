"""
Check Guidance Service - Resource Selection (Step 1)

Simple service focused on determining which resource types are valid for a given check.
"""

import json
import logging
from typing import Dict, Any, Type, List

# Local imports
from .prompts import get_resource_selection_prompt
from .models import SystemEnrichedCheck
from llm_generator.benchmark.models import Check

# System imports
from con_mon.utils.llm.client import get_llm_client
from con_mon.utils.llm.prompt import ProviderConfig
from con_mon.connectors.models import ConnectorType

logger = logging.getLogger(__name__)


class ResourceSelectionService:
    """
    Service for determining which resource types are valid for compliance checks.

    This implements Step 1: Identify compatible resource types for a given check
    without the complexity of field path mapping or guidance generation.
    """

    def __init__(self):
        self.llm_client = get_llm_client()
        self.provider_wise_configs: Dict[ConnectorType, ProviderConfig] = dict()
        self._load_resource_schemas()

    def select_valid_resources(
            self,
            check: Check,
    ) -> SystemEnrichedCheck:
        """
        Determine which resource types are valid for a given check.

        Args:
            check: Check object from benchmark processing

        Returns:
            SystemEnrichedCheck object with valid and invalid resources populated
        """
        logger.info(f"Selecting valid resources for check: {check.unique_id}")

        # Generate the resource selection prompt
        valid_resources = []
        invalid_resources = []
        for provider, provider_config in self.provider_wise_configs.items():
            for resource_name, field_paths in provider_config.resource_wise_field_paths.items():
                prompt = get_resource_selection_prompt(
                    check,
                    provider,
                    resource_name,
                    field_paths
                )

                # Get LLM response
                response = self.llm_client.generate_text(prompt)

                # Parse the JSON response and map to ResourceSchema objects
                try:
                    llm_result = self._parse_json_response(response)
                except Exception as e:
                    logger.error(f"Failed to parse response: {e}")
                    llm_result = dict(
                        is_valid=None,
                        field_paths=[],
                        literature=response,
                        reason="LLM Response Failed to parse",
                    )
                resource_dict = dict(
                    resource_name=resource_name,
                    provider=provider,
                    **llm_result
                )
                if resource_dict['is_valid']:
                    valid_resources.append(resource_dict)
                else:
                    invalid_resources.append(resource_dict)

        # Create SystemEnrichedCheck with resource analysis
        enriched_check = SystemEnrichedCheck(
            # Base check fields
            unique_id=check.unique_id,
            name=check.name,
            literature=check.literature,
            controls=check.controls or [],
            frameworks=check.frameworks or [],
            benchmark_mapping=check.benchmark_mapping or [],
            mapping_confidence=check.mapping_confidence or 0.0,
            category=check.category,
            severity=check.severity,
            tags=check.tags or [],
            extracted_at=check.extracted_at,
            mapped_at=check.mapped_at,

            # Resource selection results
            valid_resources=valid_resources,
            invalid_resources=invalid_resources
        )
        
        logger.info(f"✅ Resource selection completed for {check.unique_id}: {len(valid_resources)} valid, {len(invalid_resources)} invalid")
        return enriched_check

    def _load_resource_schemas(self):
        """Load available resource schemas for analysis."""
        # Determine which providers to load
        providers = [ConnectorType.GITHUB, ConnectorType.AWS, ConnectorType.GOOGLE]

        # Load schemas from each provider
        for provider in providers:
            provider_config = ProviderConfig(provider)
            self.provider_wise_configs.update({
                provider: provider_config
            })

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM with error handling."""
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"LLM Response: {response[:500]}")

            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                logger.info("Found JSON in markdown code block, attempting to parse...")
                json_content = json_match.group(1).strip()
                return json.loads(json_content)

            # If all else fails, raise the original error
            raise e


# Global service instance
resource_selection_service = ResourceSelectionService()


# Export the main function
def select_valid_resources_for_check(check):
    """
    Main function to determine valid resource types for a check.
    
    Args:
        check: Check object from benchmark processing
        
    Returns:
        SystemEnrichedCheck object with valid and invalid resources populated
    """
    return resource_selection_service.select_valid_resources(check)
