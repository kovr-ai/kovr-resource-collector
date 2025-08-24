"""
Check Guidance Service - Section 2 System Compatibility Implementation

This module implements system compatibility enrichment workflow:
1. Expand to Resource Types and Field Paths
2. Coverage on System Compatibility

Provides check_guidance_service instance for external usage.
"""

import json
import logging
from typing import Dict, Any, List
from datetime import datetime

# Local imports - prompts
from .prompts import (
    get_system_enrichment_prompt,
    get_resource_selection_prompt,
    generate_system_enriched_id,
)
from .models import (
    SystemEnrichedCheck,
    ResourceSchema,
    SystemCompatibilityCoverage
)

# System imports
from con_mon.utils.llm.client import get_llm_client
from con_mon.resources.models import get_all_resource_types

logger = logging.getLogger(__name__)


class CheckGuidanceService:
    """
    Core service for system compatibility enrichment implementing Section 2 workflow.

    Methods align with the 2-step process:
    - enrich_checks_with_system_resources(): Step 1 - Expand to Resource Types and Field Paths
    - generate_system_compatibility_coverage(): Step 2 - Coverage on System Compatibility
    """

    def __init__(self):
        self.llm_client = get_llm_client()
        self._resource_schemas_cache = None

    def enrich_checks_with_system_resources(
            self,
            enriched_checks: List,  # List of Check objects from Section 1
    ) -> List[SystemEnrichedCheck]:
        """
        Step 1: Expand checks to include resource types and field paths.

        Args:
            enriched_checks: List of enriched Check objects from Section 1

        Returns:
            List of SystemEnrichedCheck objects with system compatibility info
        """
        logger.info(f"Starting Step 1: Enriching {len(enriched_checks)} checks with system resources")

        # Load available resource schemas
        resource_schemas = self._load_resource_schemas()
        logger.info(f"Loaded {len(resource_schemas)} resource schemas")

        system_enriched_checks = []
        
        for i, check in enumerate(enriched_checks):
            logger.info(f"Enriching check {i + 1}/{len(enriched_checks)}: {check.unique_id}")

            try:
                # Step 1: Generate system-enriched check using LLM
                check_data = self._check_to_dict(check)
                resource_schemas_data = [self._resource_schema_to_dict(rs) for rs in resource_schemas]
                
                enrichment_prompt = get_system_enrichment_prompt(check_data, resource_schemas_data)
                enrichment_response = self.llm_client.generate_text(enrichment_prompt)

                # Parse system-enriched check from LLM
                enriched_check_data = self._parse_json_response(enrichment_response)

                # Validate field paths against available schemas
                validated_field_paths = self._validate_field_paths(
                    enriched_check_data.get('field_paths_used', []),
                    enriched_check_data.get('resource_type', ''),
                    resource_schemas
                )

                # Create SystemEnrichedCheck object
                system_enriched_check = SystemEnrichedCheck(
                    unique_id=enriched_check_data.get('unique_id', check.unique_id),
                    name=enriched_check_data.get('name', check.name),
                    literature=enriched_check_data.get('literature', check.literature),
                    controls=check.controls or [],
                    frameworks=check.frameworks or [],
                    benchmark_mapping=check.benchmark_mapping or [],
                    mapping_confidence=check.mapping_confidence or 0.0,
                    category=check.category or '',
                    severity=check.severity or 'medium',
                    tags=check.tags or [],
                    extracted_at=check.extracted_at,
                    mapped_at=check.mapped_at,
                    resource_type=enriched_check_data.get('resource_type', ''),
                    field_paths_used=validated_field_paths,
                    targeted_guidance=enriched_check_data.get('targeted_guidance', ''),
                    system_enriched_at=datetime.now()
                )

                system_enriched_checks.append(system_enriched_check)
                
            except Exception as e:
                logger.error(f"Failed to enrich check {check.unique_id}: {e}")
                # Create a basic system enriched check with no system compatibility
                system_enriched_check = SystemEnrichedCheck(
                    unique_id=check.unique_id,
                    name=check.name,
                    literature=check.literature,
                    controls=check.controls or [],
                    frameworks=check.frameworks or [],
                    benchmark_mapping=check.benchmark_mapping or [],
                    mapping_confidence=check.mapping_confidence or 0.0,
                    category=check.category or '',
                    severity=check.severity or 'medium',
                    tags=check.tags or [],
                    extracted_at=check.extracted_at,
                    mapped_at=check.mapped_at,
                    resource_type='No Compatible Resource',
                    field_paths_used=[],
                    targeted_guidance='System compatibility could not be determined.',
                    system_enriched_at=datetime.now()
                )
                system_enriched_checks.append(system_enriched_check)

        logger.info(f"Successfully enriched {len(system_enriched_checks)} checks with system resources")
        return system_enriched_checks

    def generate_system_compatibility_coverage(
            self, 
            system_enriched_checks: List[SystemEnrichedCheck]
    ) -> SystemCompatibilityCoverage:
        """
        Step 2: Generate coverage metrics for system compatibility.

        Args:
            system_enriched_checks: List of SystemEnrichedCheck objects from Step 1

        Returns:
            SystemCompatibilityCoverage object containing coverage statistics
        """
        total_checks = len(system_enriched_checks)
        
        checks_with_resource_types = sum(
            1 for check in system_enriched_checks 
            if check.resource_type and check.resource_type != 'No Compatible Resource'
        )
        
        checks_with_field_paths = sum(
            1 for check in system_enriched_checks 
            if check.field_paths_used
        )
        
        checks_with_targeted_guidance = sum(
            1 for check in system_enriched_checks 
            if check.targeted_guidance and len(check.targeted_guidance.strip()) > 50
        )

        # Provider breakdown
        github_checks = sum(1 for check in system_enriched_checks if 'GitHub' in (check.resource_type or ''))
        aws_checks = sum(1 for check in system_enriched_checks if 'AWS' in (check.resource_type or ''))
        google_checks = sum(1 for check in system_enriched_checks if 'Google' in (check.resource_type or ''))
        
        # Quality metrics
        total_field_paths = sum(len(check.field_paths_used or []) for check in system_enriched_checks)
        avg_field_paths = (total_field_paths / total_checks) if total_checks > 0 else 0
        
        total_guidance_length = sum(len(check.targeted_guidance or '') for check in system_enriched_checks)
        avg_guidance_length = (total_guidance_length / total_checks) if total_checks > 0 else 0
        
        checks_with_multiple_resources = sum(
            1 for check in system_enriched_checks 
            if (check.field_paths_used and len(check.field_paths_used) > 1)
        )

        return SystemCompatibilityCoverage(
            total_checks=total_checks,
            checks_with_resource_types=checks_with_resource_types,
            checks_with_field_paths=checks_with_field_paths,
            checks_with_targeted_guidance=checks_with_targeted_guidance,
            coverage_percentages={
                'resource_types': (checks_with_resource_types / total_checks * 100) if total_checks > 0 else 0,
                'field_paths': (checks_with_field_paths / total_checks * 100) if total_checks > 0 else 0,
                'targeted_guidance': (checks_with_targeted_guidance / total_checks * 100) if total_checks > 0 else 0
            },
            provider_coverage={
                'github_checks': github_checks,
                'aws_checks': aws_checks, 
                'google_checks': google_checks,
                'multi_provider_checks': checks_with_multiple_resources
            },
            quality_metrics={
                'avg_field_paths_per_check': avg_field_paths,
                'avg_guidance_length': avg_guidance_length,
                'checks_with_multiple_resources': checks_with_multiple_resources
            }
        )

    # Helper methods
    def _load_resource_schemas(self) -> List[ResourceSchema]:
        """Load available resource schemas for system compatibility."""
        if self._resource_schemas_cache is None:
            try:
                # Load from system resource models
                resource_types = get_all_resource_types()
                
                schemas = []
                for resource_type_name, resource_config in resource_types.items():
                    # Extract field paths from resource model
                    field_paths = self._extract_field_paths_from_model(resource_config)
                    
                    schema = ResourceSchema(
                        resource_type=resource_type_name,
                        display_name=resource_config.get('display_name', resource_type_name),
                        field_paths=field_paths,
                        provider=self._extract_provider_from_resource_type(resource_type_name),
                        description=resource_config.get('description', f'Resource type: {resource_type_name}')
                    )
                    schemas.append(schema)
                
                self._resource_schemas_cache = schemas
                logger.info(f"Loaded {len(schemas)} resource schemas")
                
            except Exception as e:
                logger.warning(f"Failed to load resource schemas: {e}, using fallback")
                self._resource_schemas_cache = self._get_fallback_resource_schemas()
                
        return self._resource_schemas_cache

    def _extract_field_paths_from_model(self, resource_config: Dict) -> List[str]:
        """Extract field paths from resource model configuration."""
        # This is a simplified implementation
        # In a real implementation, you'd introspect the Pydantic models to get field paths
        field_paths = []
        
        if 'model' in resource_config:
            # Extract from Pydantic model fields
            model = resource_config['model']
            if hasattr(model, '__fields__'):
                for field_name, field_info in model.__fields__.items():
                    field_paths.append(f"{resource_config.get('base_path', 'resource')}.{field_name}")
        
        # Fallback to some common field paths
        if not field_paths:
            field_paths = [
                f"{resource_config.get('base_path', 'resource')}.id",
                f"{resource_config.get('base_path', 'resource')}.name",
                f"{resource_config.get('base_path', 'resource')}.status"
            ]
            
        return field_paths

    def _extract_provider_from_resource_type(self, resource_type: str) -> str:
        """Extract provider name from resource type."""
        if '::' in resource_type:
            return resource_type.split('::')[0].lower()
        elif resource_type.startswith(('GitHub', 'github')):
            return 'github'
        elif resource_type.startswith(('AWS', 'aws')):
            return 'aws'
        elif resource_type.startswith(('Google', 'google', 'GCP')):
            return 'google'
        else:
            return 'unknown'

    def _get_fallback_resource_schemas(self) -> List[ResourceSchema]:
        """Provide fallback resource schemas if loading fails."""
        return [
            ResourceSchema(
                resource_type="GitHub::Repo",
                display_name="GitHub Repository",
                field_paths=[
                    "repo.basic_info.name",
                    "repo.basic_info.branches[].name", 
                    "repo.basic_info.branches[].protected",
                    "repo.security.branch_protection.enforce_admins",
                    "repo.security.branch_protection.required_reviews"
                ],
                provider="github",
                description="GitHub repository with branch protection and security settings"
            ),
            ResourceSchema(
                resource_type="AWS::EC2::Instance",
                display_name="AWS EC2 Instance", 
                field_paths=[
                    "instance.instance_id",
                    "instance.state",
                    "instance.security_groups[].group_id",
                    "instance.vpc_id",
                    "instance.tags[]"
                ],
                provider="aws",
                description="AWS EC2 compute instance"
            ),
            ResourceSchema(
                resource_type="Google::Compute::Instance",
                display_name="Google Compute Instance",
                field_paths=[
                    "instance.name",
                    "instance.status", 
                    "instance.machine_type",
                    "instance.network_interfaces[].access_configs",
                    "instance.service_accounts[].scopes"
                ],
                provider="google",
                description="Google Cloud compute instance"
            )
        ]

    def _validate_field_paths(self, field_paths: List[str], resource_type: str, resource_schemas: List[ResourceSchema]) -> List[str]:
        """Validate that field paths actually exist in the resource schema."""
        if not field_paths or not resource_type:
            return []
            
        # Find matching resource schema
        matching_schema = next((rs for rs in resource_schemas if rs.resource_type == resource_type), None)
        if not matching_schema:
            return []
            
        # Filter field paths to only include valid ones
        valid_paths = [fp for fp in field_paths if fp in matching_schema.field_paths]
        
        if len(valid_paths) < len(field_paths):
            invalid_paths = set(field_paths) - set(valid_paths)
            logger.warning(f"Filtered out invalid field paths for {resource_type}: {invalid_paths}")
            
        return valid_paths

    def _check_to_dict(self, check) -> Dict[str, Any]:
        """Convert Check object to dictionary for LLM processing."""
        return {
            'unique_id': check.unique_id,
            'name': check.name,
            'literature': check.literature,
            'controls': check.controls or [],
            'frameworks': check.frameworks or [],
            'benchmark_mapping': check.benchmark_mapping or [],
            'mapping_confidence': check.mapping_confidence or 0.0,
            'category': check.category or '',
            'severity': check.severity or 'medium',
            'tags': check.tags or [],
            'extracted_at': check.extracted_at.isoformat() if hasattr(check.extracted_at, 'isoformat') else str(check.extracted_at),
            'mapped_at': check.mapped_at.isoformat() if hasattr(check.mapped_at, 'isoformat') else str(check.mapped_at)
        }

    def _resource_schema_to_dict(self, resource_schema: ResourceSchema) -> Dict[str, Any]:
        """Convert ResourceSchema object to dictionary for LLM processing."""
        return {
            'resource_type': resource_schema.resource_type,
            'display_name': resource_schema.display_name,
            'field_paths': resource_schema.field_paths,
            'provider': resource_schema.provider,
            'description': resource_schema.description
        }

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM with enhanced error handling."""
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            logger.info(f"LLM Response (first 500 chars): {response[:500]}")

            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                logger.info("Found JSON in markdown code block, attempting to parse...")
                return json.loads(json_match.group(1))

            raise e


# Global service instance for external usage
check_guidance_service = CheckGuidanceService()

# Export the key methods
enrich_checks_with_system_resources = check_guidance_service.enrich_checks_with_system_resources
generate_system_compatibility_coverage = check_guidance_service.generate_system_compatibility_coverage
